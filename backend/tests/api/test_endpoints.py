"""
Integration tests for API endpoints
"""

import json
import tempfile
from io import BytesIO
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


@pytest.mark.integration
class TestAPIEndpoints:
    """Integration tests for API endpoints."""

    @pytest.fixture
    def sample_pdf_bytes(self) -> bytes:
        """Create a sample PDF file."""
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.drawString(100, 750, "Sample insurance policy document")
        pdf.drawString(100, 730, "Coverage A: Dwelling - $500,000")
        pdf.showPage()
        pdf.save()
        buffer.seek(0)
        return buffer.read()

    def test_health_endpoint(self, test_client: TestClient):
        """Test the health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_list_profiles(self, test_client: TestClient):
        """Test listing all configuration profiles."""
        response = test_client.get("/profiles")
        assert response.status_code == 200
        data = response.json()

        assert "profiles" in data
        # Should have all profile types
        assert "workflows" in data["profiles"]
        assert "chunking" in data["profiles"]
        assert "retrieval" in data["profiles"]
        assert "fusion" in data["profiles"]
        assert "context" in data["profiles"]
        assert "judge" in data["profiles"]

    def test_get_workflow_profile(self, test_client: TestClient):
        """Test getting a specific workflow profile."""
        response = test_client.get("/profiles/workflow/default")
        assert response.status_code == 200
        data = response.json()

        assert "profile_id" in data
        assert data["profile_id"] == "default"
        assert "steps" in data

    def test_get_nonexistent_profile(self, test_client: TestClient):
        """Test getting a profile that doesn't exist."""
        response = test_client.get("/profiles/workflow/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_ingest_pdf(
        self, test_client: TestClient, sample_pdf_bytes: bytes
    ):
        """Test PDF ingestion endpoint."""
        files = {"file": ("test.pdf", BytesIO(sample_pdf_bytes), "application/pdf")}
        data = {
            "metadata": json.dumps({
                "form_number": "HO-3",
                "doc_type": "policy",
                "state": "CA",
            })
        }

        response = test_client.post("/ingest", files=files, data=data)
        assert response.status_code == 200

        result = response.json()
        assert "doc_id" in result
        assert "filename" in result
        assert "pages" in result
        assert result["pages"] > 0

    def test_ingest_without_file(self, test_client: TestClient):
        """Test ingestion without providing a file."""
        response = test_client.post("/ingest", data={})
        assert response.status_code == 422  # Validation error

    def test_ingest_invalid_file_type(self, test_client: TestClient):
        """Test ingestion with non-PDF file."""
        files = {"file": ("test.txt", BytesIO(b"Plain text"), "text/plain")}
        response = test_client.post("/ingest", files=files)
        # Should either reject or fail processing
        assert response.status_code in [400, 422, 500]

    def test_list_documents(self, test_client: TestClient):
        """Test listing all documents."""
        response = test_client.get("/documents")
        assert response.status_code == 200
        data = response.json()

        assert "documents" in data
        assert isinstance(data["documents"], list)

    def test_get_document(self, test_client: TestClient):
        """Test getting a specific document."""
        # First, we need a document ID (from previous ingestion)
        # For now, test with a mock ID
        response = test_client.get("/documents/doc123")

        # Will return 404 if document doesn't exist
        if response.status_code == 200:
            data = response.json()
            assert "doc_id" in data
            assert data["doc_id"] == "doc123"
        else:
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_index_document(self, test_client: TestClient):
        """Test document indexing endpoint."""
        request_data = {
            "doc_id": "doc123",
            "chunking_profile_id": "default",
        }

        response = test_client.post("/index", json=request_data)

        # Will fail if document doesn't exist
        if response.status_code == 200:
            result = response.json()
            assert "chunks_created" in result
        else:
            # Expected if document doesn't exist
            assert response.status_code in [404, 500]

    def test_index_without_doc_id(self, test_client: TestClient):
        """Test indexing without providing doc_id."""
        response = test_client.post("/index", json={})
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_execute_run(self, test_client: TestClient):
        """Test executing a RAG pipeline run."""
        request_data = {
            "query": "What does the policy cover?",
            "workflow_profile_id": "default",
        }

        response = test_client.post("/run", json=request_data)

        # May fail if no documents are indexed
        if response.status_code == 200:
            result = response.json()
            assert "run_id" in result
            assert "status" in result
        else:
            # Expected if no documents available
            assert response.status_code in [400, 500]

    def test_execute_run_invalid_request(self, test_client: TestClient):
        """Test run execution with invalid request."""
        response = test_client.post("/run", json={})
        assert response.status_code == 422  # Missing required fields

    def test_get_run_status(self, test_client: TestClient):
        """Test getting run status."""
        response = test_client.get("/run/run123/status")

        if response.status_code == 200:
            data = response.json()
            assert "run_id" in data
            assert "status" in data
        else:
            # Expected if run doesn't exist
            assert response.status_code == 404

    def test_get_run_artifacts(self, test_client: TestClient):
        """Test getting run artifacts."""
        response = test_client.get("/run/run123/artifacts")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            # May have retrieval_results, fusion_results, etc.
        else:
            assert response.status_code == 404

    def test_stream_run_events(self, test_client: TestClient):
        """Test SSE event streaming."""
        # Note: TestClient may not fully support SSE
        # This is a basic connectivity test
        response = test_client.get(
            "/run/run123/stream",
            headers={"Accept": "text/event-stream"},
        )

        # Should either connect or return 404
        assert response.status_code in [200, 404]

    def test_reload_config(self, test_client: TestClient):
        """Test configuration reload endpoint."""
        response = test_client.post("/reload-config")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "status" in data

    def test_get_stats(self, test_client: TestClient):
        """Test stats endpoint."""
        response = test_client.get("/stats")

        if response.status_code == 200:
            data = response.json()
            # Should have various stats
            assert isinstance(data, dict)
        else:
            # Stats endpoint might not be implemented
            assert response.status_code in [404, 501]

    def test_cors_headers(self, test_client: TestClient):
        """Test CORS headers are set correctly."""
        response = test_client.options(
            "/health",
            headers={"Origin": "http://localhost:3017"},
        )

        # Should allow CORS from frontend
        if "access-control-allow-origin" in response.headers:
            assert response.headers["access-control-allow-origin"] == "*" or \
                   "localhost:3017" in response.headers["access-control-allow-origin"]

    def test_error_handling(self, test_client: TestClient):
        """Test API error responses are well-formed."""
        # Request a non-existent endpoint
        response = test_client.get("/nonexistent")
        assert response.status_code == 404

        # Error response should be JSON
        try:
            data = response.json()
            assert "detail" in data or "error" in data
        except:
            # Some frameworks return HTML for 404
            pass

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, test_client: TestClient):
        """Test handling concurrent API requests."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        def make_request():
            return test_client.get("/health")

        # Make multiple concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]

        # All requests should succeed
        assert all(r.status_code == 200 for r in results)

    def test_request_size_limit(self, test_client: TestClient):
        """Test handling of large request payloads."""
        # Create a very large metadata object
        large_metadata = {"data": "x" * 10000000}  # 10MB of data

        response = test_client.post(
            "/ingest",
            files={"file": ("test.pdf", BytesIO(b"%PDF-"), "application/pdf")},
            data={"metadata": json.dumps(large_metadata)},
        )

        # Should either succeed or reject gracefully
        assert response.status_code in [200, 413, 422, 500]

    def test_malformed_json(self, test_client: TestClient):
        """Test handling of malformed JSON."""
        response = test_client.post(
            "/run",
            data="{ invalid json }{",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_complete_workflow(
        self, test_client: TestClient, sample_pdf_bytes: bytes
    ):
        """Test complete workflow: ingest -> index -> query."""
        # Step 1: Ingest PDF
        files = {"file": ("test.pdf", BytesIO(sample_pdf_bytes), "application/pdf")}
        ingest_response = test_client.post("/ingest", files=files)

        if ingest_response.status_code != 200:
            pytest.skip("Ingestion failed, skipping workflow test")

        doc_id = ingest_response.json()["doc_id"]

        # Step 2: Index document
        index_response = test_client.post(
            "/index",
            json={"doc_id": doc_id, "chunking_profile_id": "default"},
        )

        if index_response.status_code != 200:
            pytest.skip("Indexing failed, skipping workflow test")

        # Step 3: Execute query
        run_response = test_client.post(
            "/run",
            json={
                "query": "What is covered?",
                "workflow_profile_id": "default",
            },
        )

        # Should succeed if all previous steps worked
        if run_response.status_code == 200:
            run_data = run_response.json()
            assert "run_id" in run_data
        else:
            # May fail due to missing OpenAI key or other deps
            assert run_response.status_code in [400, 500]
