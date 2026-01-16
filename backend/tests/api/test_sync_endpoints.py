"""
Integration tests for synchronous API endpoints (/api/query and /api/chat)
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.models import (
    Answer, Citation, ConfidenceLevel, JudgeReport, CheckResult,
    CheckSeverity, JudgeViolation
)


@pytest.mark.integration
class TestSyncQueryEndpoint:
    """Integration tests for POST /api/query endpoint."""

    @pytest.fixture
    def mock_orchestrator_success(self):
        """Mock successful orchestrator execution."""
        with patch("app.api.sync.orchestrator") as mock_orch:
            # Mock answer
            mock_answer = Answer(
                answer="Dwelling protection (Coverage A) covers the structure of your home up to $500,000.",
                citations=[
                    Citation(
                        chunk_id="chunk1",
                        doc_id="doc123",
                        page_no=1,
                        quote="Coverage A: Dwelling - $500,000",
                        reason="Directly addresses dwelling protection coverage"
                    )
                ],
                confidence=ConfidenceLevel.HIGH,
                assumptions=["Based on standard HO-3 policy"],
                limitations=["Specific exclusions may apply"],
                tokens_used=450,
                cost=0.002
            )

            # Mock judge report
            mock_judge = JudgeReport(
                passed=True,
                decision="PASS",
                violations=[],
                checks=[]
            )

            # Mock orchestrator response
            mock_orch.execute_run = AsyncMock(return_value={
                "run_id": "test-run-123",
                "status": "completed",
                "answer": mock_answer,
                "judge_report": mock_judge
            })

            yield mock_orch

    def test_sync_query_basic(
        self, test_client: TestClient, mock_orchestrator_success
    ):
        """Test basic synchronous query with defaults."""
        response = test_client.post("/api/query", json={
            "query": "What is covered under dwelling protection?"
        })

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "answer" in data
        assert "citations" in data
        assert "confidence" in data
        assert "judge_passed" in data
        assert "judge_decision" in data
        assert "assumptions" in data
        assert "limitations" in data

        # Validate values
        assert data["answer"] == "Dwelling protection (Coverage A) covers the structure of your home up to $500,000."
        assert len(data["citations"]) == 1
        assert data["confidence"] == "high"
        assert data["judge_passed"] is True
        assert data["judge_decision"] == "PASS"
        assert len(data["assumptions"]) == 1
        assert len(data["limitations"]) == 1

        # Metadata should not be present by default
        assert data.get("metadata") is None

    def test_sync_query_with_metadata(
        self, test_client: TestClient, mock_orchestrator_success
    ):
        """Test query with include_metadata=True."""
        response = test_client.post("/api/query", json={
            "query": "What is covered under dwelling protection?",
            "include_metadata": True
        })

        assert response.status_code == 200
        data = response.json()

        # Metadata should be present
        assert "metadata" in data
        assert data["metadata"] is not None
        assert "run_id" in data["metadata"]
        assert "tokens_used" in data["metadata"]
        assert "cost" in data["metadata"]
        assert "status" in data["metadata"]

        assert data["metadata"]["run_id"] == "test-run-123"
        assert data["metadata"]["tokens_used"] == 450
        assert data["metadata"]["cost"] == 0.002
        assert data["metadata"]["status"] == "completed"

    def test_sync_query_with_custom_profiles(
        self, test_client: TestClient, mock_orchestrator_success
    ):
        """Test query with custom profile configurations."""
        response = test_client.post("/api/query", json={
            "query": "What are the exclusions?",
            "workflow_id": "default_workflow",
            "retrieval_profile_id": "balanced_insurance",
            "fusion_profile_id": "balanced",
            "context_profile_id": "default",
            "judge_profile_id": "strict_insurance"
        })

        assert response.status_code == 200
        data = response.json()

        # Verify orchestrator was called with correct profiles
        mock_orchestrator_success.execute_run.assert_called_once()
        call_kwargs = mock_orchestrator_success.execute_run.call_args.kwargs
        assert call_kwargs["workflow_id"] == "default_workflow"
        assert call_kwargs["retrieval_profile_id"] == "balanced_insurance"
        assert call_kwargs["fusion_profile_id"] == "balanced"
        assert call_kwargs["mode"] == "query"

    def test_sync_query_with_doc_filter(
        self, test_client: TestClient, mock_orchestrator_success
    ):
        """Test query with document filter."""
        response = test_client.post("/api/query", json={
            "query": "Coverage details",
            "doc_filter": {"state": "CA", "form_number": "HO-3"}
        })

        assert response.status_code == 200

        # Verify doc_filter was passed to orchestrator
        call_kwargs = mock_orchestrator_success.execute_run.call_args.kwargs
        assert call_kwargs["doc_filter"] == {"state": "CA", "form_number": "HO-3"}

    def test_sync_query_judge_blocking(self, test_client: TestClient):
        """Test query when judge blocks the answer."""
        with patch("app.api.sync.orchestrator") as mock_orch:
            # Mock blocked judge report
            mock_judge = JudgeReport(
                passed=False,
                decision="FAIL_BLOCKED",
                violations=[
                    JudgeViolation(
                        check="hallucination",
                        severity=CheckSeverity.CRITICAL,
                        message="Response contains hallucinated content"
                    )
                ],
                checks=[]
            )

            mock_orch.execute_run = AsyncMock(return_value={
                "run_id": "test-run-456",
                "status": "blocked",
                "answer": None,
                "judge_report": mock_judge
            })

            response = test_client.post("/api/query", json={
                "query": "Test query"
            })

            # Should return 403 Forbidden
            assert response.status_code == 403
            data = response.json()
            assert "error" in data["detail"]
            assert "violations" in data["detail"]
            assert len(data["detail"]["violations"]) == 1
            assert data["detail"]["violations"][0]["check"] == "hallucination"

    def test_sync_query_judge_warning(self, test_client: TestClient):
        """Test query when judge fails but doesn't block (fail_on_judge_block=False)."""
        with patch("app.api.sync.orchestrator") as mock_orch:
            # Mock answer despite judge failure
            mock_answer = Answer(
                answer="Test answer with warnings",
                citations=[],
                confidence=ConfidenceLevel.LOW,
                assumptions=[],
                limitations=["May contain bias"],
                tokens_used=200,
                cost=0.001
            )

            mock_judge = JudgeReport(
                passed=False,
                decision="FAIL_RETRYABLE",
                violations=[
                    JudgeViolation(
                        check="bias",
                        severity=CheckSeverity.WARNING,
                        message="Potential bias detected"
                    )
                ],
                checks=[]
            )

            mock_orch.execute_run = AsyncMock(return_value={
                "run_id": "test-run-789",
                "status": "completed",  # Not blocked, just warning
                "answer": mock_answer,
                "judge_report": mock_judge
            })

            response = test_client.post("/api/query", json={
                "query": "Test query"
            })

            # Should return 200 with answer but judge_passed=False
            assert response.status_code == 200
            data = response.json()
            assert data["judge_passed"] is False
            assert data["judge_decision"] == "FAIL_RETRYABLE"
            assert data["answer"] == "Test answer with warnings"

    def test_sync_query_execution_failure(self, test_client: TestClient):
        """Test query when pipeline execution fails."""
        with patch("app.api.sync.orchestrator") as mock_orch:
            mock_orch.execute_run = AsyncMock(return_value={
                "run_id": "test-run-error",
                "status": "failed",
                "error": "Vector store not initialized",
                "answer": None,
                "judge_report": None
            })

            response = test_client.post("/api/query", json={
                "query": "Test query"
            })

            # Should return 500 Internal Server Error
            assert response.status_code == 500
            data = response.json()
            assert "error" in data["detail"]

    def test_sync_query_invalid_profile(self, test_client: TestClient):
        """Test query with invalid workflow profile."""
        with patch("app.api.sync.config_loader") as mock_loader:
            mock_loader.get_workflow_profile.side_effect = Exception("Profile not found")

            response = test_client.post("/api/query", json={
                "query": "Test query",
                "workflow_id": "nonexistent_workflow"
            })

            # Should return 400 Bad Request
            assert response.status_code == 400
            assert "Invalid workflow_id" in response.json()["detail"]

    def test_sync_query_empty_query(self, test_client: TestClient):
        """Test query with empty string."""
        response = test_client.post("/api/query", json={
            "query": ""
        })

        # Should return 422 Unprocessable Entity (Pydantic validation)
        assert response.status_code == 422


@pytest.mark.integration
class TestSyncChatEndpoint:
    """Integration tests for POST /api/chat endpoint."""

    @pytest.fixture
    def mock_chat_orchestrator(self):
        """Mock orchestrator for chat mode."""
        with patch("app.api.sync.orchestrator") as mock_orch:
            # Mock chat manager
            mock_orch.chat_manager = MagicMock()
            mock_orch.chat_manager.check_quit_command.return_value = False
            mock_orch.chat_manager.get_session.return_value = None  # No existing session
            mock_orch.chat_manager.delete_session = MagicMock()

            # Mock answer
            mock_answer = Answer(
                answer="There are several coverages available including dwelling, personal property, and liability.",
                citations=[
                    Citation(
                        chunk_id="chunk2",
                        doc_id="doc123",
                        page_no=1,
                        quote="Coverage A: Dwelling, Coverage B: Other Structures",
                        reason="Lists available coverages"
                    )
                ],
                confidence=ConfidenceLevel.HIGH,
                assumptions=[],
                limitations=[],
                tokens_used=350,
                cost=0.0015
            )

            mock_judge = JudgeReport(
                passed=True,
                decision="PASS",
                violations=[],
                checks=[]
            )

            mock_orch.execute_run = AsyncMock(return_value={
                "run_id": "chat-run-123",
                "status": "completed",
                "answer": mock_answer,
                "judge_report": mock_judge,
                "session_id": "session-abc-123",
                "turn_number": 1,
                "history_compacted": False
            })

            yield mock_orch

    def test_chat_first_message(
        self, test_client: TestClient, mock_chat_orchestrator
    ):
        """Test first message creates new session."""
        response = test_client.post("/api/chat", json={
            "message": "What coverages are available?"
        })

        assert response.status_code == 200
        data = response.json()

        # Validate chat-specific fields
        assert "session_id" in data
        assert "turn_number" in data
        assert "session_created" in data
        assert "session_terminated" in data
        assert "history_compacted" in data

        assert data["session_id"] == "session-abc-123"
        assert data["turn_number"] == 1
        assert data["session_created"] is True  # First message
        assert data["session_terminated"] is False
        assert data["history_compacted"] is False

        # Verify orchestrator called with mode="chat"
        call_kwargs = mock_chat_orchestrator.execute_run.call_args.kwargs
        assert call_kwargs["mode"] == "chat"
        assert call_kwargs["session_id"] is None  # First message

    def test_chat_continuation(
        self, test_client: TestClient, mock_chat_orchestrator
    ):
        """Test continuing conversation with session_id."""
        # Mock existing session
        mock_chat_orchestrator.chat_manager.get_session.return_value = MagicMock()

        # Update mock to return turn 2
        mock_answer = Answer(
            answer="The limits for dwelling coverage are $500,000.",
            citations=[],
            confidence=ConfidenceLevel.HIGH,
            assumptions=[],
            limitations=[],
            tokens_used=250,
            cost=0.001
        )

        mock_chat_orchestrator.execute_run.return_value = {
            "run_id": "chat-run-124",
            "status": "completed",
            "answer": mock_answer,
            "judge_report": JudgeReport(passed=True, decision="PASS", violations=[], checks=[]),
            "session_id": "session-abc-123",
            "turn_number": 2,
            "history_compacted": False
        }

        response = test_client.post("/api/chat", json={
            "message": "What are the limits for the first one?",
            "session_id": "session-abc-123"
        })

        assert response.status_code == 200
        data = response.json()

        assert data["session_id"] == "session-abc-123"
        assert data["turn_number"] == 2
        assert data["session_created"] is False  # Continuing existing session
        assert data["session_terminated"] is False

        # Verify orchestrator called with session_id
        call_kwargs = mock_chat_orchestrator.execute_run.call_args.kwargs
        assert call_kwargs["session_id"] == "session-abc-123"

    def test_chat_quit_command(
        self, test_client: TestClient, mock_chat_orchestrator
    ):
        """Test 'Quit' command terminates session."""
        # Mock quit detection
        mock_chat_orchestrator.chat_manager.check_quit_command.return_value = True

        response = test_client.post("/api/chat", json={
            "message": "Quit",
            "session_id": "session-abc-123"
        })

        assert response.status_code == 200
        data = response.json()

        # Session should be terminated
        assert data["session_terminated"] is True
        assert data["session_id"] == "session-abc-123"
        assert data["turn_number"] == 0
        assert data["answer"] == ""
        assert data["citations"] == []

        # Verify delete_session was called
        mock_chat_orchestrator.chat_manager.delete_session.assert_called_once_with("session-abc-123")

    def test_chat_quit_without_session(
        self, test_client: TestClient, mock_chat_orchestrator
    ):
        """Test 'Quit' without active session returns error."""
        mock_chat_orchestrator.chat_manager.check_quit_command.return_value = True

        response = test_client.post("/api/chat", json={
            "message": "Quit"
            # No session_id
        })

        # Should return 400 Bad Request
        assert response.status_code == 400
        assert "No active session" in response.json()["detail"]

    def test_chat_invalid_session(
        self, test_client: TestClient, mock_chat_orchestrator
    ):
        """Test invalid session_id creates new session."""
        # Mock no existing session
        mock_chat_orchestrator.chat_manager.get_session.return_value = None

        response = test_client.post("/api/chat", json={
            "message": "Test message",
            "session_id": "invalid-session-999"
        })

        assert response.status_code == 200
        data = response.json()

        # Should create new session
        assert data["session_created"] is True
        assert data["session_id"] == "session-abc-123"  # New session

        # Verify orchestrator called with session_id=None (to create new)
        call_kwargs = mock_chat_orchestrator.execute_run.call_args.kwargs
        assert call_kwargs["session_id"] is None

    def test_chat_history_compaction(
        self, test_client: TestClient, mock_chat_orchestrator
    ):
        """Test history compaction flag is returned."""
        # Mock existing session
        mock_chat_orchestrator.chat_manager.get_session.return_value = MagicMock()

        # Update mock to indicate compaction occurred
        mock_chat_orchestrator.execute_run.return_value["history_compacted"] = True

        response = test_client.post("/api/chat", json={
            "message": "Test message",
            "session_id": "session-abc-123"
        })

        assert response.status_code == 200
        data = response.json()

        # Verify compaction flag
        assert data["history_compacted"] is True

    def test_chat_custom_profiles(
        self, test_client: TestClient, mock_chat_orchestrator
    ):
        """Test chat with custom profile configurations."""
        response = test_client.post("/api/chat", json={
            "message": "Test message",
            "workflow_id": "default_workflow",
            "chat_profile_id": "default",
            "retrieval_profile_id": "balanced_insurance",
            "fusion_profile_id": "balanced",
            "context_profile_id": "default",
            "judge_profile_id": "strict_insurance"
        })

        assert response.status_code == 200

        # Verify all profiles passed to orchestrator
        call_kwargs = mock_chat_orchestrator.execute_run.call_args.kwargs
        assert call_kwargs["workflow_id"] == "default_workflow"
        assert call_kwargs["chat_profile_id"] == "default"
        assert call_kwargs["retrieval_profile_id"] == "balanced_insurance"
        assert call_kwargs["fusion_profile_id"] == "balanced"
        assert call_kwargs["context_profile_id"] == "default"
        assert call_kwargs["judge_profile_id"] == "strict_insurance"

    def test_chat_with_metadata(
        self, test_client: TestClient, mock_chat_orchestrator
    ):
        """Test chat with include_metadata=True."""
        response = test_client.post("/api/chat", json={
            "message": "Test message",
            "include_metadata": True
        })

        assert response.status_code == 200
        data = response.json()

        # Metadata should be present
        assert "metadata" in data
        assert data["metadata"] is not None
        assert "run_id" in data["metadata"]
        assert "tokens_used" in data["metadata"]

    def test_chat_judge_blocking(self, test_client: TestClient):
        """Test chat when judge blocks the answer."""
        with patch("app.api.sync.orchestrator") as mock_orch:
            mock_orch.chat_manager = MagicMock()
            mock_orch.chat_manager.check_quit_command.return_value = False
            mock_orch.chat_manager.get_session.return_value = None

            # Mock blocked response
            mock_judge = JudgeReport(
                passed=False,
                decision="FAIL_BLOCKED",
                violations=[
                    JudgeViolation(
                        check="toxicity",
                        severity=CheckSeverity.CRITICAL,
                        message="Response contains toxic content"
                    )
                ],
                checks=[]
            )

            mock_orch.execute_run = AsyncMock(return_value={
                "run_id": "chat-run-error",
                "status": "blocked",
                "answer": None,
                "judge_report": mock_judge,
                "session_id": "session-xyz-789",
                "turn_number": 1,
                "history_compacted": False
            })

            response = test_client.post("/api/chat", json={
                "message": "Test message"
            })

            # Should return 403 Forbidden
            assert response.status_code == 403
            data = response.json()
            assert "error" in data["detail"]
            assert "session_id" in data["detail"]
            assert data["detail"]["session_id"] == "session-xyz-789"

    def test_chat_empty_message(self, test_client: TestClient):
        """Test chat with empty message."""
        response = test_client.post("/api/chat", json={
            "message": ""
        })

        # Should return 422 Unprocessable Entity (Pydantic validation)
        assert response.status_code == 422

    def test_chat_session_metadata(
        self, test_client: TestClient, mock_chat_orchestrator
    ):
        """Test turn_number increments correctly."""
        # Mock existing session
        mock_chat_orchestrator.chat_manager.get_session.return_value = MagicMock()

        # Simulate multiple turns
        for turn in range(1, 4):
            mock_chat_orchestrator.execute_run.return_value["turn_number"] = turn

            response = test_client.post("/api/chat", json={
                "message": f"Message {turn}",
                "session_id": "session-abc-123"
            })

            assert response.status_code == 200
            data = response.json()
            assert data["turn_number"] == turn
            assert data["session_id"] == "session-abc-123"
