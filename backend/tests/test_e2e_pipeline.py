"""
End-to-end pipeline tests
Tests the complete RAG pipeline from ingestion to answer generation
"""

import tempfile
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.adapters.file_doc_store import FileDocStore
from app.adapters.networkx_graph import NetworkXGraph
from app.core.models import Document
from app.modules.context_compiler import ContextCompiler
from app.modules.fusion import Fusion
from app.modules.generation import Generation
from app.modules.indexing import Indexing
from app.modules.ingestion import Ingestion
from app.modules.judge.orchestrator import JudgeOrchestrator
from app.modules.retrieval import Retrieval


@pytest.mark.integration
class TestE2EPipeline:
    """End-to-end pipeline tests."""

    @pytest.fixture
    def sample_pdf_path(self) -> str:
        """Create a temporary sample PDF file."""
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)

        # Page 1
        pdf.drawString(100, 750, "HOMEOWNERS INSURANCE POLICY - FORM HO-3")
        pdf.drawString(100, 720, "Policy Number: HO-123456")
        pdf.drawString(100, 690, "")
        pdf.drawString(100, 660, "COVERAGE A - DWELLING: $500,000")
        pdf.drawString(100, 640, "COVERAGE B - OTHER STRUCTURES: $50,000")
        pdf.drawString(100, 620, "COVERAGE C - PERSONAL PROPERTY: $350,000")
        pdf.showPage()

        # Page 2
        pdf.drawString(100, 750, "SECTION I - EXCLUSIONS")
        pdf.drawString(100, 720, "")
        pdf.drawString(100, 690, "We do not cover:")
        pdf.drawString(100, 670, "1. Water Damage from flood or surface water")
        pdf.drawString(100, 650, "2. Earth Movement including earthquake")
        pdf.drawString(100, 630, "3. War and nuclear hazard")
        pdf.showPage()

        pdf.save()
        buffer.seek(0)

        # Write to temp file
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        )
        temp_file.write(buffer.read())
        temp_file.close()

        return temp_file.name

    @pytest.fixture
    async def setup_pipeline(
        self,
        test_data_dir: str,
        mock_llm_adapter: AsyncMock,
    ):
        """Set up the complete pipeline with real adapters."""
        # Use real adapters for this E2E test
        doc_store = FileDocStore(data_dir=test_data_dir)

        # Mock vector store for simplicity
        vector_store = AsyncMock()
        vector_store.add_vectors.return_value = None
        vector_store.search.return_value = [
            {"chunk_id": "chunk1", "score": 0.95, "metadata": {}},
            {"chunk_id": "chunk2", "score": 0.87, "metadata": {}},
        ]

        # Use real graph store
        graph_store = NetworkXGraph(data_dir=test_data_dir)

        # Create modules
        ingestion = Ingestion(doc_store=doc_store)
        indexing = Indexing(
            doc_store=doc_store,
            vector_store=vector_store,
            graph_store=graph_store,
            llm_adapter=mock_llm_adapter,
        )
        retrieval = Retrieval(
            doc_store=doc_store,
            vector_store=vector_store,
            graph_store=graph_store,
            llm_adapter=mock_llm_adapter,
        )
        fusion = Fusion()
        context_compiler = ContextCompiler(doc_store=doc_store)
        generation = Generation(llm_adapter=mock_llm_adapter)
        judge = JudgeOrchestrator(llm_adapter=mock_llm_adapter)

        return {
            "ingestion": ingestion,
            "indexing": indexing,
            "retrieval": retrieval,
            "fusion": fusion,
            "context_compiler": context_compiler,
            "generation": generation,
            "judge": judge,
            "doc_store": doc_store,
        }

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_full_pipeline_execution(
        self,
        setup_pipeline: dict,
        sample_pdf_path: str,
        mock_llm_adapter: AsyncMock,
    ):
        """Test executing the full RAG pipeline."""
        pipeline = setup_pipeline

        # Mock LLM responses
        mock_llm_adapter.embed.return_value = [0.1] * 1536
        mock_llm_adapter.extract_entities.return_value = {
            "nodes": [
                {
                    "entity_name": "Coverage A",
                    "entity_type": "COVERAGE",
                    "metadata": {"limit": "$500,000"},
                }
            ],
            "edges": [],
        }
        mock_llm_adapter.generate.return_value = (
            "The policy provides Coverage A for dwelling with a limit of $500,000 [1]. "
            "Water damage from flood is excluded [2]."
        )

        # Step 1: Ingest PDF
        document = await pipeline["ingestion"].ingest_pdf(
            file_path=sample_pdf_path,
            filename="test_policy.pdf",
            metadata={
                "form_number": "HO-3",
                "doc_type": "policy",
                "state": "CA",
            },
        )

        assert document is not None
        assert len(document.pages) == 2
        assert document.metadata["form_number"] == "HO-3"

        # Step 2: Index document
        chunking_config = {
            "method": "sentence_aware",
            "chunk_size": 500,
            "chunk_overlap": 50,
            "sentence_min_length": 10,
        }

        index_result = await pipeline["indexing"].index_document(
            doc_id=document.doc_id,
            chunking_profile=chunking_config,
        )

        assert index_result["chunks_created"] > 0

        # Step 3: Retrieve relevant chunks
        retrieval_config = {
            "vector_weight": 0.5,
            "document_weight": 0.3,
            "graph_weight": 0.2,
            "vector_top_k": 5,
            "document_top_k": 5,
            "graph_top_k": 3,
            "graph_strategy": "entity_search",
        }

        # Get chunks for mocking
        chunks = await pipeline["doc_store"].get_chunks(document.doc_id)
        mock_llm_adapter.embed.return_value = [0.1] * 1536

        retrieval_results = await pipeline["retrieval"].retrieve(
            query="What does the policy cover and what is excluded?",
            profile=retrieval_config,
        )

        assert retrieval_results is not None
        # Should have results from at least one modality
        assert (
            len(retrieval_results.get("vector", [])) > 0 or
            len(retrieval_results.get("document", [])) > 0 or
            len(retrieval_results.get("graph", [])) > 0
        )

        # Step 4: Fuse results
        fusion_config = {
            "method": "weighted_rrf",
            "rrf_k": 60,
            "dedup_threshold": 0.9,
            "max_results": 10,
        }

        fused_results = await pipeline["fusion"].fuse(
            retrieval_results=retrieval_results,
            profile=fusion_config,
        )

        assert len(fused_results) > 0

        # Step 5: Compile context
        context_config = {
            "max_tokens": 3000,
            "citation_format": "numbered",
            "include_metadata": True,
            "redact_pii": False,
        }

        context_pack = await pipeline["context_compiler"].compile_context(
            chunk_ids=[r["chunk_id"] for r in fused_results[:5]],
            profile=context_config,
        )

        assert context_pack is not None
        assert len(context_pack.citations) > 0
        assert context_pack.total_tokens > 0

        # Step 6: Generate answer
        answer = await pipeline["generation"].generate_answer(
            query="What does the policy cover and what is excluded?",
            context_pack=context_pack,
        )

        assert answer is not None
        assert len(answer.answer_text) > 0
        assert len(answer.citations) > 0

        # Step 7: Validate with judge
        judge_config = {
            "checks": [
                "citation_coverage",
                "groundedness",
                "hallucination",
                "relevance",
            ],
            "citation_coverage_threshold": 0.9,
            "groundedness_threshold": 0.8,
            "hallucination_threshold": 0.1,
            "relevance_threshold": 0.7,
            "fail_on_violation": ["hallucination"],
        }

        # Mock judge checks
        mock_llm_adapter.generate.return_value = "Score: 0.9\nAll checks passed"

        judge_report = await pipeline["judge"].validate(
            query="What does the policy cover and what is excluded?",
            answer=answer,
            profile=judge_config,
        )

        assert judge_report is not None
        assert len(judge_report.checks) > 0

        # Pipeline should complete successfully
        print(f"✓ Full pipeline executed successfully")
        print(f"  - Document: {document.doc_id}")
        print(f"  - Chunks created: {index_result['chunks_created']}")
        print(f"  - Fused results: {len(fused_results)}")
        print(f"  - Answer length: {len(answer.answer_text)} chars")
        print(f"  - Judge decision: {judge_report.decision}")

    @pytest.mark.asyncio
    async def test_pipeline_with_no_results(
        self,
        setup_pipeline: dict,
        mock_llm_adapter: AsyncMock,
    ):
        """Test pipeline behavior when retrieval returns no results."""
        pipeline = setup_pipeline

        # Mock empty retrieval results
        retrieval_results = {
            "vector": [],
            "document": [],
            "graph": [],
        }

        fusion_config = {
            "method": "weighted_rrf",
            "rrf_k": 60,
            "dedup_threshold": 0.9,
            "max_results": 10,
        }

        fused_results = await pipeline["fusion"].fuse(
            retrieval_results=retrieval_results,
            profile=fusion_config,
        )

        # Should handle empty results gracefully
        assert fused_results == []

    @pytest.mark.asyncio
    async def test_pipeline_error_recovery(
        self,
        setup_pipeline: dict,
        sample_pdf_path: str,
        mock_llm_adapter: AsyncMock,
    ):
        """Test pipeline error handling and recovery."""
        pipeline = setup_pipeline

        # Simulate LLM error
        mock_llm_adapter.generate.side_effect = Exception("API Error")

        # Generation should handle the error
        with pytest.raises(Exception):
            answer = await pipeline["generation"].generate_answer(
                query="Test query",
                context_pack=MagicMock(
                    context_text="Test context",
                    citations=[],
                    total_tokens=100,
                ),
            )

    @pytest.mark.asyncio
    async def test_pipeline_caching(
        self,
        setup_pipeline: dict,
        sample_pdf_path: str,
        mock_llm_adapter: AsyncMock,
    ):
        """Test that pipeline components cache appropriately."""
        pipeline = setup_pipeline

        # Ingest document
        doc1 = await pipeline["ingestion"].ingest_pdf(
            file_path=sample_pdf_path,
            filename="test1.pdf",
            metadata={},
        )

        # Retrieve document (should be cached in doc store)
        doc2 = await pipeline["doc_store"].get_document(doc1.doc_id)

        assert doc2 is not None
        assert doc1.doc_id == doc2.doc_id
        assert len(doc1.pages) == len(doc2.pages)

    @pytest.mark.asyncio
    async def test_multi_document_query(
        self,
        setup_pipeline: dict,
        sample_pdf_path: str,
        mock_llm_adapter: AsyncMock,
    ):
        """Test querying across multiple documents."""
        pipeline = setup_pipeline

        mock_llm_adapter.embed.return_value = [0.1] * 1536
        mock_llm_adapter.extract_entities.return_value = {
            "nodes": [],
            "edges": [],
        }

        # Ingest two documents
        doc1 = await pipeline["ingestion"].ingest_pdf(
            file_path=sample_pdf_path,
            filename="policy1.pdf",
            metadata={"doc_type": "policy"},
        )

        doc2 = await pipeline["ingestion"].ingest_pdf(
            file_path=sample_pdf_path,
            filename="policy2.pdf",
            metadata={"doc_type": "endorsement"},
        )

        # Index both
        chunking_config = {
            "method": "fixed_size",
            "chunk_size": 500,
            "chunk_overlap": 50,
        }

        await pipeline["indexing"].index_document(
            doc_id=doc1.doc_id,
            chunking_profile=chunking_config,
        )

        await pipeline["indexing"].index_document(
            doc_id=doc2.doc_id,
            chunking_profile=chunking_config,
        )

        # Query should find results from both documents
        retrieval_config = {
            "vector_weight": 0.5,
            "document_weight": 0.5,
            "graph_weight": 0.0,
            "vector_top_k": 10,
            "document_top_k": 10,
            "graph_top_k": 0,
            "graph_strategy": "entity_search",
        }

        retrieval_results = await pipeline["retrieval"].retrieve(
            query="What is covered?",
            profile=retrieval_config,
        )

        # Should have results (potentially from both docs)
        total_results = (
            len(retrieval_results.get("vector", [])) +
            len(retrieval_results.get("document", []))
        )
        assert total_results > 0
