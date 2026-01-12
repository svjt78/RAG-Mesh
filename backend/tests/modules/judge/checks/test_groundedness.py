"""
Unit tests for Groundedness check
"""

from unittest.mock import AsyncMock

import pytest

from app.core.models import Answer, Citation
from app.modules.judge.checks.groundedness import GroundednessCheck


@pytest.mark.unit
class TestGroundednessCheck:
    """Test cases for Groundedness check."""

    @pytest.fixture
    def check(self, mock_llm_adapter: AsyncMock) -> GroundednessCheck:
        """Create a GroundednessCheck instance."""
        config = {"threshold": 0.8, "use_llm": True}
        return GroundednessCheck(config=config, llm_adapter=mock_llm_adapter)

    @pytest.mark.asyncio
    async def test_grounded_answer(
        self,
        check: GroundednessCheck,
        mock_llm_adapter: AsyncMock,
        sample_citations: list[Citation],
    ):
        """Test an answer that is grounded in the citations."""
        answer = Answer(
            answer_text="The policy provides Coverage A for dwelling with a limit of $500,000 [1].",
            citations=sample_citations,
            confidence="high",
            assumptions=[],
            limitations=[],
        )

        # Mock LLM to return high groundedness score
        mock_llm_adapter.generate.return_value = (
            "GROUNDED\nScore: 0.95\nThe answer accurately reflects the citation content."
        )

        result = await check.validate(
            query="What is the dwelling coverage?",
            answer=answer,
        )

        assert result.passed is True
        assert result.score >= 0.8

    @pytest.mark.asyncio
    async def test_ungrounded_answer(
        self,
        check: GroundednessCheck,
        mock_llm_adapter: AsyncMock,
        sample_citations: list[Citation],
    ):
        """Test an answer that makes unsupported claims."""
        answer = Answer(
            answer_text="The policy covers flood damage and earthquake damage [1].",
            citations=sample_citations,  # Citations don't mention flood or earthquake
            confidence="medium",
            assumptions=[],
            limitations=[],
        )

        # Mock LLM to return low groundedness score
        mock_llm_adapter.generate.return_value = (
            "NOT_GROUNDED\nScore: 0.3\nThe answer makes claims not supported by citations."
        )

        result = await check.validate(
            query="What does the policy cover?",
            answer=answer,
        )

        assert result.passed is False
        assert result.score < 0.8

    @pytest.mark.asyncio
    async def test_no_citations_provided(
        self,
        check: GroundednessCheck,
        mock_llm_adapter: AsyncMock,
    ):
        """Test answer with no citations."""
        answer = Answer(
            answer_text="The policy covers dwelling and personal property.",
            citations=[],
            confidence="low",
            assumptions=[],
            limitations=[],
        )

        result = await check.validate(
            query="What is covered?",
            answer=answer,
        )

        # Cannot verify groundedness without citations
        assert result.passed is False
        assert result.score == 0.0

    @pytest.mark.asyncio
    async def test_partial_groundedness(
        self,
        check: GroundednessCheck,
        mock_llm_adapter: AsyncMock,
        sample_citations: list[Citation],
    ):
        """Test answer that is partially grounded."""
        answer = Answer(
            answer_text="The policy covers dwelling [1] and also covers nuclear incidents.",
            citations=sample_citations,
            confidence="medium",
            assumptions=[],
            limitations=[],
        )

        # Mock LLM to return moderate groundedness score
        mock_llm_adapter.generate.return_value = (
            "PARTIALLY_GROUNDED\nScore: 0.5\nDwelling coverage is supported, but nuclear incidents claim is not."
        )

        result = await check.validate(
            query="What is covered?",
            answer=answer,
        )

        assert result.score == pytest.approx(0.5, abs=0.1)
        assert result.passed is False  # Below 0.8 threshold

    @pytest.mark.asyncio
    async def test_llm_response_parsing(
        self,
        check: GroundednessCheck,
        mock_llm_adapter: AsyncMock,
        sample_citations: list[Citation],
    ):
        """Test parsing of various LLM response formats."""
        answer = Answer(
            answer_text="Test answer [1]",
            citations=sample_citations,
            confidence="high",
            assumptions=[],
            limitations=[],
        )

        # Test different response formats
        test_cases = [
            ("Score: 0.9\nGrounded", 0.9),
            ("GROUNDED (Score: 0.85)", 0.85),
            ("The score is 0.75 out of 1.0", 0.75),
            ("Not grounded - Score: 0.2", 0.2),
        ]

        for llm_response, expected_score in test_cases:
            mock_llm_adapter.generate.return_value = llm_response
            result = await check.validate(
                query="Test",
                answer=answer,
            )
            assert result.score == pytest.approx(expected_score, abs=0.05)

    @pytest.mark.asyncio
    async def test_llm_response_no_score(
        self,
        check: GroundednessCheck,
        mock_llm_adapter: AsyncMock,
        sample_citations: list[Citation],
    ):
        """Test handling of LLM response with no parseable score."""
        answer = Answer(
            answer_text="Test answer [1]",
            citations=sample_citations,
            confidence="high",
            assumptions=[],
            limitations=[],
        )

        # LLM returns response without clear score
        mock_llm_adapter.generate.return_value = "The answer seems reasonable."

        result = await check.validate(
            query="Test",
            answer=answer,
        )

        # Should default to a low score when unparseable
        assert result.score < 0.8
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_threshold_configuration(
        self,
        mock_llm_adapter: AsyncMock,
        sample_citations: list[Citation],
    ):
        """Test that threshold affects pass/fail decision."""
        answer = Answer(
            answer_text="Test answer [1]",
            citations=sample_citations,
            confidence="high",
            assumptions=[],
            limitations=[],
        )

        mock_llm_adapter.generate.return_value = "Score: 0.75"

        # Strict threshold (0.9)
        strict_check = GroundednessCheck(
            config={"threshold": 0.9, "use_llm": True},
            llm_adapter=mock_llm_adapter,
        )
        result = await strict_check.validate(query="Test", answer=answer)
        assert result.passed is False  # 0.75 < 0.9

        # Lenient threshold (0.6)
        lenient_check = GroundednessCheck(
            config={"threshold": 0.6, "use_llm": True},
            llm_adapter=mock_llm_adapter,
        )
        result = await lenient_check.validate(query="Test", answer=answer)
        assert result.passed is True  # 0.75 > 0.6

    @pytest.mark.asyncio
    async def test_multiple_citations(
        self,
        check: GroundednessCheck,
        mock_llm_adapter: AsyncMock,
    ):
        """Test groundedness with multiple citations."""
        citations = [
            Citation(
                chunk_id="chunk1",
                doc_id="doc123",
                text="Coverage A provides dwelling protection.",
                score=0.9,
                metadata={},
            ),
            Citation(
                chunk_id="chunk2",
                doc_id="doc123",
                text="Coverage B provides other structures protection.",
                score=0.85,
                metadata={},
            ),
            Citation(
                chunk_id="chunk3",
                doc_id="doc123",
                text="Coverage C provides personal property protection.",
                score=0.8,
                metadata={},
            ),
        ]

        answer = Answer(
            answer_text="The policy provides dwelling [1], other structures [2], and personal property [3] protection.",
            citations=citations,
            confidence="high",
            assumptions=[],
            limitations=[],
        )

        mock_llm_adapter.generate.return_value = "Score: 0.95\nAll claims are well-supported."

        result = await check.validate(
            query="What coverages are included?",
            answer=answer,
        )

        assert result.passed is True
        assert result.score >= 0.8

    @pytest.mark.asyncio
    async def test_conflicting_citations(
        self,
        check: GroundednessCheck,
        mock_llm_adapter: AsyncMock,
    ):
        """Test groundedness when citations seem contradictory."""
        citations = [
            Citation(
                chunk_id="chunk1",
                doc_id="doc123",
                text="Water damage is covered.",
                score=0.9,
                metadata={},
            ),
            Citation(
                chunk_id="chunk2",
                doc_id="doc123",
                text="Water damage is excluded.",
                score=0.85,
                metadata={},
            ),
        ]

        answer = Answer(
            answer_text="Water damage coverage depends on the type [1][2].",
            citations=citations,
            confidence="medium",
            assumptions=["Answer attempts to reconcile conflicting citations"],
            limitations=[],
        )

        mock_llm_adapter.generate.return_value = (
            "Score: 0.7\nCitations conflict, answer tries to explain."
        )

        result = await check.validate(
            query="Is water damage covered?",
            answer=answer,
        )

        # Should reflect the moderate groundedness
        assert 0.6 <= result.score <= 0.8
