"""
FAISS-based vector store adapter
Implements vector storage and similarity search using FAISS
"""

import faiss
import numpy as np
import json
import aiofiles
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from app.adapters.base import VectorStoreAdapter

logger = logging.getLogger(__name__)


class FAISSVectorStoreAdapter(VectorStoreAdapter):
    """FAISS-based implementation of vector storage"""

    def __init__(self, data_dir: Path = Path("data/vectors"), dimension: int = 1536):
        """
        Initialize FAISS vector store

        Args:
            data_dir: Directory for vector storage
            dimension: Embedding dimension (1536 for text-embedding-3-small)
        """
        self.data_dir = data_dir
        self.dimension = dimension
        self.index_path = data_dir / "index.faiss"
        self.metadata_path = data_dir / "chunk_meta.jsonl"

        # Create directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize FAISS index (L2 distance)
        self.index: Optional[faiss.IndexFlatL2] = None
        self.chunk_ids: List[str] = []
        self.metadata: Dict[str, Dict[str, Any]] = {}

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

        # Load existing index if available
        asyncio.create_task(self._initialize())

    async def _initialize(self) -> None:
        """Initialize or load existing index"""
        if self.index_path.exists():
            await self.load_index(self.data_dir)
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info(f"Created new FAISS index with dimension {self.dimension}")

    async def add_embeddings(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        metadata: List[Dict[str, Any]]
    ) -> None:
        """
        Add embeddings to the index

        Args:
            chunk_ids: List of chunk identifiers
            embeddings: List of embedding vectors
            metadata: List of metadata for each chunk
        """
        if len(chunk_ids) != len(embeddings) != len(metadata):
            raise ValueError("chunk_ids, embeddings, and metadata must have same length")

        async with self._lock:
            # Ensure index is initialized
            if self.index is None:
                self.index = faiss.IndexFlatL2(self.dimension)

            # Convert embeddings to numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)

            # Validate dimensions
            if embeddings_array.shape[1] != self.dimension:
                raise ValueError(f"Embedding dimension {embeddings_array.shape[1]} doesn't match index dimension {self.dimension}")

            # Add to FAISS index
            start_idx = self.index.ntotal
            self.index.add(embeddings_array)

            # Store chunk IDs and metadata
            for i, (chunk_id, meta) in enumerate(zip(chunk_ids, metadata)):
                idx = start_idx + i
                self.chunk_ids.append(chunk_id)
                self.metadata[chunk_id] = meta

            logger.info(f"Added {len(chunk_ids)} embeddings to index (total: {self.index.ntotal})")

    async def search(
        self,
        query_embedding: List[float],
        k: int = 10,
        threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors

        Args:
            query_embedding: Query vector
            k: Number of results to return
            threshold: Optional similarity threshold (L2 distance)
            filters: Optional metadata filters

        Returns:
            List of results with chunk_id, score, and metadata
        """
        async with self._lock:
            if self.index is None or self.index.ntotal == 0:
                logger.warning("Index is empty, returning no results")
                return []

            # Convert query to numpy array
            query_array = np.array([query_embedding], dtype=np.float32)

            # Validate dimensions
            if query_array.shape[1] != self.dimension:
                raise ValueError(f"Query dimension {query_array.shape[1]} doesn't match index dimension {self.dimension}")

            # Perform search
            # Note: k might be larger than index size
            actual_k = min(k, self.index.ntotal)
            distances, indices = self.index.search(query_array, actual_k)

            # Build results
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                # FAISS returns -1 for not found
                if idx == -1:
                    continue

                chunk_id = self.chunk_ids[idx]
                meta = self.metadata.get(chunk_id, {})

                # Convert L2 distance to similarity score (0-1 range)
                # Lower distance = higher similarity
                # Using a simple inverse transformation
                similarity = 1.0 / (1.0 + float(dist))

                # Apply threshold if provided
                if threshold is not None and similarity < threshold:
                    continue

                # Apply filters if provided
                if filters:
                    match = True
                    for key, value in filters.items():
                        if key in meta and meta[key] != value:
                            match = False
                            break
                    if not match:
                        continue

                results.append({
                    "chunk_id": chunk_id,
                    "score": similarity,
                    "distance": float(dist),
                    "metadata": meta
                })

            logger.info(f"Vector search returned {len(results)} results (k={k})")
            return results

    async def save_index(self, path: Path) -> None:
        """
        Persist the index to disk

        Args:
            path: Path to save the index
        """
        async with self._lock:
            if self.index is None:
                logger.warning("No index to save")
                return

            # Save FAISS index
            index_file = path / "index.faiss"
            faiss.write_index(self.index, str(index_file))

            # Save metadata as JSONL
            metadata_file = path / "chunk_meta.jsonl"
            async with aiofiles.open(metadata_file, 'w') as f:
                for chunk_id in self.chunk_ids:
                    meta_entry = {
                        "chunk_id": chunk_id,
                        "metadata": self.metadata.get(chunk_id, {})
                    }
                    await f.write(json.dumps(meta_entry) + '\n')

            logger.info(f"Saved FAISS index with {self.index.ntotal} vectors to {path}")

    async def load_index(self, path: Path) -> None:
        """
        Load the index from disk

        Args:
            path: Path to load the index from
        """
        async with self._lock:
            index_file = path / "index.faiss"
            metadata_file = path / "chunk_meta.jsonl"

            if not index_file.exists():
                logger.warning(f"Index file not found: {index_file}")
                self.index = faiss.IndexFlatL2(self.dimension)
                return

            # Load FAISS index
            self.index = faiss.read_index(str(index_file))

            # Load metadata
            self.chunk_ids = []
            self.metadata = {}

            if metadata_file.exists():
                async with aiofiles.open(metadata_file, 'r') as f:
                    async for line in f:
                        if line.strip():
                            entry = json.loads(line)
                            chunk_id = entry["chunk_id"]
                            self.chunk_ids.append(chunk_id)
                            self.metadata[chunk_id] = entry.get("metadata", {})

            logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors from {path}")

    async def get_index_size(self) -> int:
        """
        Get the number of vectors in the index

        Returns:
            Number of vectors
        """
        async with self._lock:
            if self.index is None:
                return 0
            return self.index.ntotal

    async def clear_index(self) -> None:
        """Clear the entire index"""
        async with self._lock:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.chunk_ids = []
            self.metadata = {}
            logger.info("Cleared FAISS index")

    async def get_embedding(self, chunk_id: str) -> Optional[List[float]]:
        """
        Get embedding for a specific chunk ID

        Args:
            chunk_id: Chunk identifier

        Returns:
            Embedding vector or None if not found
        """
        async with self._lock:
            if chunk_id not in self.chunk_ids:
                return None

            idx = self.chunk_ids.index(chunk_id)
            if idx >= self.index.ntotal:
                return None

            # Reconstruct vector from index
            vector = self.index.reconstruct(idx)
            return vector.tolist()

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get index statistics

        Returns:
            Statistics dictionary
        """
        async with self._lock:
            return {
                "total_vectors": self.index.ntotal if self.index else 0,
                "dimension": self.dimension,
                "index_type": "IndexFlatL2",
                "unique_chunks": len(self.chunk_ids),
            }
