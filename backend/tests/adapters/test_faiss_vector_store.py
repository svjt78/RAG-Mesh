"""
Unit tests for FAISSVectorStore adapter
"""

import os

import numpy as np
import pytest

from app.adapters.faiss_vector_store import FAISSVectorStore


@pytest.mark.unit
class TestFAISSVectorStore:
    """Test cases for FAISSVectorStore adapter."""

    @pytest.fixture
    def vector_store(self, test_data_dir: str) -> FAISSVectorStore:
        """Create a FAISSVectorStore instance for testing."""
        return FAISSVectorStore(data_dir=test_data_dir, dimension=384)

    @pytest.fixture
    def sample_vectors(self) -> list[dict]:
        """Create sample vectors for testing."""
        return [
            {
                "chunk_id": "chunk1",
                "vector": np.random.rand(384).tolist(),
                "metadata": {"doc_id": "doc123", "page_num": 1},
            },
            {
                "chunk_id": "chunk2",
                "vector": np.random.rand(384).tolist(),
                "metadata": {"doc_id": "doc123", "page_num": 1},
            },
            {
                "chunk_id": "chunk3",
                "vector": np.random.rand(384).tolist(),
                "metadata": {"doc_id": "doc123", "page_num": 2},
            },
        ]

    @pytest.mark.asyncio
    async def test_add_and_search_vectors(
        self, vector_store: FAISSVectorStore, sample_vectors: list[dict]
    ):
        """Test adding vectors and performing search."""
        # Add vectors
        await vector_store.add_vectors(sample_vectors)

        # Verify index is not empty
        assert vector_store.index.ntotal == len(sample_vectors)

        # Search with the first vector (should return itself as top result)
        query_vector = sample_vectors[0]["vector"]
        results = await vector_store.search(
            query_vector=query_vector, top_k=3, doc_id=None
        )

        assert len(results) > 0
        assert results[0]["chunk_id"] == "chunk1"
        assert results[0]["score"] >= 0.99  # Very high similarity to itself

    @pytest.mark.asyncio
    async def test_search_empty_index(self, vector_store: FAISSVectorStore):
        """Test searching an empty index."""
        query_vector = np.random.rand(384).tolist()
        results = await vector_store.search(
            query_vector=query_vector, top_k=5, doc_id=None
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_search_with_doc_filter(
        self, vector_store: FAISSVectorStore, sample_vectors: list[dict]
    ):
        """Test searching with document ID filter."""
        # Add vectors from different documents
        vectors = sample_vectors + [
            {
                "chunk_id": "chunk4",
                "vector": np.random.rand(384).tolist(),
                "metadata": {"doc_id": "doc456", "page_num": 1},
            }
        ]
        await vector_store.add_vectors(vectors)

        # Search with doc filter
        query_vector = np.random.rand(384).tolist()
        results = await vector_store.search(
            query_vector=query_vector, top_k=10, doc_id="doc123"
        )

        # All results should be from doc123
        assert all(r["chunk_id"].startswith("chunk") for r in results)
        assert all(
            r["chunk_id"] in ["chunk1", "chunk2", "chunk3"] for r in results
        )

    @pytest.mark.asyncio
    async def test_delete_vectors(
        self, vector_store: FAISSVectorStore, sample_vectors: list[dict]
    ):
        """Test deleting vectors by document ID."""
        # Add vectors
        await vector_store.add_vectors(sample_vectors)
        initial_count = vector_store.index.ntotal

        # Delete vectors for doc123
        await vector_store.delete_vectors(doc_id="doc123")

        # Index should be empty or recreated
        assert vector_store.index.ntotal == 0

    @pytest.mark.asyncio
    async def test_save_and_load_index(
        self, vector_store: FAISSVectorStore, sample_vectors: list[dict]
    ):
        """Test persisting and loading the FAISS index."""
        # Add vectors and save
        await vector_store.add_vectors(sample_vectors)
        await vector_store.save_index()

        # Verify index file was created
        index_path = os.path.join(vector_store.index_dir, "faiss.index")
        metadata_path = os.path.join(vector_store.index_dir, "metadata.json")
        assert os.path.exists(index_path)
        assert os.path.exists(metadata_path)

        # Create new instance and load
        new_store = FAISSVectorStore(
            data_dir=vector_store.index_dir.replace("/vectors", ""),
            dimension=384,
        )
        await new_store.load_index()

        # Verify loaded index has same data
        assert new_store.index.ntotal == len(sample_vectors)

        # Search should work on loaded index
        query_vector = sample_vectors[0]["vector"]
        results = await new_store.search(
            query_vector=query_vector, top_k=1, doc_id=None
        )
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_add_vectors_incrementally(
        self, vector_store: FAISSVectorStore
    ):
        """Test adding vectors in multiple batches."""
        # Add first batch
        batch1 = [
            {
                "chunk_id": f"chunk{i}",
                "vector": np.random.rand(384).tolist(),
                "metadata": {"doc_id": "doc1"},
            }
            for i in range(5)
        ]
        await vector_store.add_vectors(batch1)
        assert vector_store.index.ntotal == 5

        # Add second batch
        batch2 = [
            {
                "chunk_id": f"chunk{i}",
                "vector": np.random.rand(384).tolist(),
                "metadata": {"doc_id": "doc2"},
            }
            for i in range(5, 10)
        ]
        await vector_store.add_vectors(batch2)
        assert vector_store.index.ntotal == 10

    @pytest.mark.asyncio
    async def test_vector_dimension_mismatch(
        self, vector_store: FAISSVectorStore
    ):
        """Test handling vectors with wrong dimension."""
        wrong_dim_vectors = [
            {
                "chunk_id": "chunk1",
                "vector": np.random.rand(256).tolist(),  # Wrong dimension
                "metadata": {},
            }
        ]

        with pytest.raises(Exception):
            await vector_store.add_vectors(wrong_dim_vectors)

    @pytest.mark.asyncio
    async def test_search_top_k_limit(
        self, vector_store: FAISSVectorStore, sample_vectors: list[dict]
    ):
        """Test that search respects top_k parameter."""
        await vector_store.add_vectors(sample_vectors)

        query_vector = np.random.rand(384).tolist()

        # Search with top_k=1
        results = await vector_store.search(
            query_vector=query_vector, top_k=1, doc_id=None
        )
        assert len(results) <= 1

        # Search with top_k=2
        results = await vector_store.search(
            query_vector=query_vector, top_k=2, doc_id=None
        )
        assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_similarity_scores(
        self, vector_store: FAISSVectorStore
    ):
        """Test that similarity scores are normalized between 0 and 1."""
        # Create vectors with known similarity
        base_vector = np.random.rand(384)
        similar_vector = base_vector + np.random.rand(384) * 0.1  # Very similar
        dissimilar_vector = np.random.rand(384)  # Random

        vectors = [
            {
                "chunk_id": "chunk1",
                "vector": base_vector.tolist(),
                "metadata": {},
            },
            {
                "chunk_id": "chunk2",
                "vector": similar_vector.tolist(),
                "metadata": {},
            },
            {
                "chunk_id": "chunk3",
                "vector": dissimilar_vector.tolist(),
                "metadata": {},
            },
        ]

        await vector_store.add_vectors(vectors)

        # Search with base vector
        results = await vector_store.search(
            query_vector=base_vector.tolist(), top_k=3, doc_id=None
        )

        # All scores should be between 0 and 1
        assert all(0 <= r["score"] <= 1 for r in results)

        # First result (exact match) should have highest score
        assert results[0]["chunk_id"] == "chunk1"
        assert results[0]["score"] >= 0.99

    @pytest.mark.asyncio
    async def test_empty_vectors_list(self, vector_store: FAISSVectorStore):
        """Test adding an empty list of vectors."""
        await vector_store.add_vectors([])
        assert vector_store.index.ntotal == 0

    @pytest.mark.asyncio
    async def test_load_nonexistent_index(
        self, vector_store: FAISSVectorStore
    ):
        """Test loading an index that doesn't exist."""
        # Should not raise an error, just create new index
        await vector_store.load_index()
        assert vector_store.index.ntotal == 0

    @pytest.mark.asyncio
    async def test_metadata_preservation(
        self, vector_store: FAISSVectorStore, sample_vectors: list[dict]
    ):
        """Test that metadata is preserved through save/load cycle."""
        await vector_store.add_vectors(sample_vectors)
        await vector_store.save_index()

        # Load in new instance
        new_store = FAISSVectorStore(
            data_dir=vector_store.index_dir.replace("/vectors", ""),
            dimension=384,
        )
        await new_store.load_index()

        # Search and verify metadata
        query_vector = sample_vectors[0]["vector"]
        results = await new_store.search(
            query_vector=query_vector, top_k=1, doc_id=None
        )

        assert len(results) > 0
        assert "metadata" in results[0]
        assert results[0]["metadata"]["doc_id"] == "doc123"
