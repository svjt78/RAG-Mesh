"""
Vector retrieval module
Semantic search using vector embeddings
"""

import logging
from typing import List, Dict, Any, Optional

from app.adapters.base import VectorStoreAdapter, LLMAdapter
from app.core.models import VectorResult, RetrievalProfile

logger = logging.getLogger(__name__)


class VectorRetrievalModule:
    """Handles vector-based semantic retrieval"""

    def __init__(
        self,
        vector_store: VectorStoreAdapter,
        llm_adapter: LLMAdapter
    ):
        """
        Initialize vector retrieval module

        Args:
            vector_store: Vector store adapter
            llm_adapter: LLM adapter for embeddings
        """
        self.vector_store = vector_store
        self.llm = llm_adapter

    async def retrieve(
        self,
        query: str,
        profile: RetrievalProfile,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[VectorResult]:
        """
        Retrieve chunks using vector similarity search

        Args:
            query: Search query
            profile: Retrieval profile with parameters
            filters: Optional metadata filters

        Returns:
            List of VectorResult objects
        """
        logger.info(f"Vector retrieval for query: '{query[:50]}...'")

        try:
            # Generate query embedding
            query_embeddings = await self.llm.embed([query])
            query_embedding = query_embeddings[0]

            # Search vector store
            results = await self.vector_store.search(
                query_embedding=query_embedding,
                k=profile.vector_k,
                threshold=profile.vector_threshold,
                filters=filters
            )

            # Convert to VectorResult objects
            vector_results = []
            for rank, result in enumerate(results, start=1):
                vector_result = VectorResult(
                    chunk_id=result["chunk_id"],
                    score=result["score"],
                    rank=rank,
                    metadata=result.get("metadata", {})
                )
                vector_results.append(vector_result)

            logger.info(f"Vector retrieval returned {len(vector_results)} results")
            return vector_results

        except Exception as e:
            logger.error(f"Error in vector retrieval: {e}")
            return []

    async def retrieve_with_diversity(
        self,
        query: str,
        profile: RetrievalProfile,
        max_per_doc: int = 3,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[VectorResult]:
        """
        Retrieve with diversity constraints

        Args:
            query: Search query
            profile: Retrieval profile
            max_per_doc: Maximum chunks per document
            filters: Optional metadata filters

        Returns:
            List of diverse VectorResult objects
        """
        # Get initial results
        results = await self.retrieve(query, profile, filters)

        # Apply diversity constraints
        doc_counts: Dict[str, int] = {}
        diverse_results = []

        for result in results:
            doc_id = result.metadata.get("doc_id")
            if not doc_id:
                diverse_results.append(result)
                continue

            # Check document count
            if doc_counts.get(doc_id, 0) < max_per_doc:
                diverse_results.append(result)
                doc_counts[doc_id] = doc_counts.get(doc_id, 0) + 1

        logger.info(
            f"Applied diversity: {len(results)} → {len(diverse_results)} results"
        )
        return diverse_results
