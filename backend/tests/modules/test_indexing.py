"""
Unit tests for Indexing module
"""

from unittest.mock import AsyncMock

import pytest

from app.core.models import Chunk, Document, EntityType, Page
from app.modules.indexing import Indexing


@pytest.mark.unit
class TestIndexing:
    """Test cases for Indexing module."""

    @pytest.fixture
    def indexing(
        self,
        mock_doc_store: AsyncMock,
        mock_vector_store: AsyncMock,
        mock_graph_store: AsyncMock,
        mock_llm_adapter: AsyncMock,
    ) -> Indexing:
        """Create an Indexing instance for testing."""
        return Indexing(
            doc_store=mock_doc_store,
            vector_store=mock_vector_store,
            graph_store=mock_graph_store,
            llm_adapter=mock_llm_adapter,
        )

    @pytest.mark.asyncio
    async def test_index_document_success(
        self,
        indexing: Indexing,
        sample_document: Document,
        sample_chunking_config: dict,
        mock_doc_store: AsyncMock,
        mock_vector_store: AsyncMock,
        mock_graph_store: AsyncMock,
        mock_llm_adapter: AsyncMock,
    ):
        """Test successful document indexing."""
        # Mock document retrieval
        mock_doc_store.get_document.return_value = sample_document

        # Index the document
        result = await indexing.index_document(
            doc_id=sample_document.doc_id,
            chunking_profile=sample_chunking_config,
        )

        # Verify chunks were created
        assert result is not None
        assert "chunks_created" in result
        assert result["chunks_created"] > 0

        # Verify all storage operations were called
        mock_doc_store.save_chunks.assert_called_once()
        mock_vector_store.add_vectors.assert_called_once()
        mock_graph_store.add_nodes.assert_called()

    @pytest.mark.asyncio
    async def test_chunk_creation_sentence_aware(
        self,
        indexing: Indexing,
        sample_document: Document,
        mock_doc_store: AsyncMock,
    ):
        """Test sentence-aware chunking."""
        mock_doc_store.get_document.return_value = sample_document

        config = {
            "method": "sentence_aware",
            "chunk_size": 100,
            "chunk_overlap": 20,
            "sentence_min_length": 10,
        }

        result = await indexing.index_document(
            doc_id=sample_document.doc_id,
            chunking_profile=config,
        )

        # Get the chunks that were saved
        call_args = mock_doc_store.save_chunks.call_args
        chunks = call_args[0][1]  # Second argument is the chunks list

        # Verify chunks were created
        assert len(chunks) > 0

        # Verify chunk properties
        for chunk in chunks:
            assert isinstance(chunk, Chunk)
            assert chunk.doc_id == sample_document.doc_id
            assert len(chunk.text) <= config["chunk_size"] * 1.5  # Allow some flexibility
            assert chunk.chunk_id.startswith(sample_document.doc_id)

    @pytest.mark.asyncio
    async def test_chunk_creation_fixed_size(
        self,
        indexing: Indexing,
        sample_document: Document,
        mock_doc_store: AsyncMock,
    ):
        """Test fixed-size chunking."""
        mock_doc_store.get_document.return_value = sample_document

        config = {
            "method": "fixed_size",
            "chunk_size": 50,
            "chunk_overlap": 10,
        }

        result = await indexing.index_document(
            doc_id=sample_document.doc_id,
            chunking_profile=config,
        )

        call_args = mock_doc_store.save_chunks.call_args
        chunks = call_args[0][1]

        # Each chunk should be around chunk_size
        for chunk in chunks:
            # Allow some flexibility for word boundaries
            assert len(chunk.text) <= config["chunk_size"] * 1.2

    @pytest.mark.asyncio
    async def test_chunk_metadata_propagation(
        self,
        indexing: Indexing,
        sample_document: Document,
        sample_chunking_config: dict,
        mock_doc_store: AsyncMock,
    ):
        """Test that document metadata is propagated to chunks."""
        mock_doc_store.get_document.return_value = sample_document

        await indexing.index_document(
            doc_id=sample_document.doc_id,
            chunking_profile=sample_chunking_config,
        )

        call_args = mock_doc_store.save_chunks.call_args
        chunks = call_args[0][1]

        # All chunks should have document metadata
        for chunk in chunks:
            assert "form_number" in chunk.metadata
            assert chunk.metadata["form_number"] == "HO-3"
            assert "doc_type" in chunk.metadata
            assert "state" in chunk.metadata

    @pytest.mark.asyncio
    async def test_vector_embedding(
        self,
        indexing: Indexing,
        sample_document: Document,
        sample_chunking_config: dict,
        mock_doc_store: AsyncMock,
        mock_llm_adapter: AsyncMock,
        mock_vector_store: AsyncMock,
    ):
        """Test that chunks are embedded and stored."""
        mock_doc_store.get_document.return_value = sample_document

        await indexing.index_document(
            doc_id=sample_document.doc_id,
            chunking_profile=sample_chunking_config,
        )

        # Verify embeddings were created
        # LLM adapter should have been called for each chunk
        assert mock_llm_adapter.embed.call_count > 0

        # Verify vectors were added to vector store
        mock_vector_store.add_vectors.assert_called_once()
        call_args = mock_vector_store.add_vectors.call_args
        vectors = call_args[0][0]

        assert len(vectors) > 0
        assert all("chunk_id" in v for v in vectors)
        assert all("vector" in v for v in vectors)

    @pytest.mark.asyncio
    async def test_entity_extraction(
        self,
        indexing: Indexing,
        sample_document: Document,
        sample_chunking_config: dict,
        mock_doc_store: AsyncMock,
        mock_llm_adapter: AsyncMock,
        mock_graph_store: AsyncMock,
    ):
        """Test entity extraction from chunks."""
        mock_doc_store.get_document.return_value = sample_document

        await indexing.index_document(
            doc_id=sample_document.doc_id,
            chunking_profile=sample_chunking_config,
        )

        # Verify entity extraction was called
        assert mock_llm_adapter.extract_entities.call_count > 0

        # Verify nodes were added to graph
        mock_graph_store.add_nodes.assert_called()

    @pytest.mark.asyncio
    async def test_index_nonexistent_document(
        self,
        indexing: Indexing,
        sample_chunking_config: dict,
        mock_doc_store: AsyncMock,
    ):
        """Test indexing a document that doesn't exist."""
        mock_doc_store.get_document.return_value = None

        with pytest.raises(ValueError, match="Document .* not found"):
            await indexing.index_document(
                doc_id="nonexistent",
                chunking_profile=sample_chunking_config,
            )

    @pytest.mark.asyncio
    async def test_chunk_overlap(
        self,
        indexing: Indexing,
        sample_document: Document,
        mock_doc_store: AsyncMock,
    ):
        """Test that chunk overlap works correctly."""
        mock_doc_store.get_document.return_value = sample_document

        config = {
            "method": "fixed_size",
            "chunk_size": 50,
            "chunk_overlap": 10,
        }

        await indexing.index_document(
            doc_id=sample_document.doc_id,
            chunking_profile=config,
        )

        call_args = mock_doc_store.save_chunks.call_args
        chunks = call_args[0][1]

        # If we have multiple chunks, verify overlap
        if len(chunks) > 1:
            # Some text from end of chunk 1 should appear in start of chunk 2
            # This is approximate due to word boundaries
            chunk1_end = chunks[0].text[-config["chunk_overlap"]:]
            chunk2_start = chunks[1].text[:config["chunk_overlap"]]

            # At least some characters should overlap
            overlap_found = any(
                char in chunk2_start for char in chunk1_end.split()[-2:]
            )
            assert overlap_found or len(chunks[0].text) < config["chunk_size"]

    @pytest.mark.asyncio
    async def test_empty_document(
        self,
        indexing: Indexing,
        sample_chunking_config: dict,
        mock_doc_store: AsyncMock,
    ):
        """Test indexing a document with no content."""
        empty_doc = Document(
            doc_id="empty123",
            filename="empty.pdf",
            metadata={},
            pages=[],
        )
        mock_doc_store.get_document.return_value = empty_doc

        result = await indexing.index_document(
            doc_id="empty123",
            chunking_profile=sample_chunking_config,
        )

        # Should handle gracefully with no chunks created
        assert result["chunks_created"] == 0

    @pytest.mark.asyncio
    async def test_page_aware_chunking(
        self,
        indexing: Indexing,
        sample_document: Document,
        mock_doc_store: AsyncMock,
    ):
        """Test that page information is preserved in chunks."""
        mock_doc_store.get_document.return_value = sample_document

        config = {
            "method": "page_based",
            "chunk_size": 500,
            "chunk_overlap": 0,
        }

        await indexing.index_document(
            doc_id=sample_document.doc_id,
            chunking_profile=config,
        )

        call_args = mock_doc_store.save_chunks.call_args
        chunks = call_args[0][1]

        # All chunks should have page_num in metadata
        for chunk in chunks:
            assert "page_num" in chunk.metadata
            assert isinstance(chunk.metadata["page_num"], int)
            assert chunk.metadata["page_num"] > 0

    @pytest.mark.asyncio
    async def test_concurrent_indexing(
        self,
        indexing: Indexing,
        sample_chunking_config: dict,
        mock_doc_store: AsyncMock,
    ):
        """Test indexing multiple documents concurrently."""
        import asyncio

        # Create multiple documents
        docs = [
            Document(
                doc_id=f"doc{i}",
                filename=f"file{i}.pdf",
                metadata={},
                pages=[
                    Page(
                        page_num=1,
                        text=f"Content for document {i}",
                        bbox={"x0": 0, "y0": 0, "x1": 100, "y1": 100},
                    )
                ],
            )
            for i in range(3)
        ]

        # Mock document retrieval for each
        async def get_doc(doc_id: str):
            for doc in docs:
                if doc.doc_id == doc_id:
                    return doc
            return None

        mock_doc_store.get_document.side_effect = get_doc

        # Index concurrently
        tasks = [
            indexing.index_document(
                doc_id=doc.doc_id,
                chunking_profile=sample_chunking_config,
            )
            for doc in docs
        ]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 3
        assert all(r["chunks_created"] > 0 for r in results)

    @pytest.mark.asyncio
    async def test_chunk_deduplication(
        self,
        indexing: Indexing,
        mock_doc_store: AsyncMock,
    ):
        """Test that very similar chunks are handled appropriately."""
        # Document with repetitive content
        doc = Document(
            doc_id="dup123",
            filename="dup.pdf",
            metadata={},
            pages=[
                Page(
                    page_num=1,
                    text="This is repeated text. " * 100,  # Same text repeated
                    bbox={"x0": 0, "y0": 0, "x1": 100, "y1": 100},
                )
            ],
        )
        mock_doc_store.get_document.return_value = doc

        config = {
            "method": "fixed_size",
            "chunk_size": 100,
            "chunk_overlap": 0,
        }

        result = await indexing.index_document(
            doc_id="dup123",
            chunking_profile=config,
        )

        # Should still create chunks (no deduplication in chunking)
        assert result["chunks_created"] > 0
