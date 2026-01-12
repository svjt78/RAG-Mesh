"""
Fusion and reranking module
Combines retrieval results from multiple modalities using Reciprocal Rank Fusion (RRF)
"""

import logging
from typing import List, Dict, Any, Set
from collections import defaultdict
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.core.models import FusionProfile, VectorResult, DocumentResult, GraphResult

logger = logging.getLogger(__name__)


class FusionModule:
    """Handles multi-modal result fusion and reranking"""

    def __init__(self):
        """Initialize fusion module"""
        pass

    async def fuse_results(
        self,
        vector_results: List[VectorResult],
        document_results: List[DocumentResult],
        graph_results: List[GraphResult],
        profile: FusionProfile
    ) -> List[Dict[str, Any]]:
        """
        Fuse results from all modalities using weighted RRF

        Args:
            vector_results: Vector search results
            document_results: Document search results
            graph_results: Graph search results
            profile: Fusion profile with weights

        Returns:
            List of fused results with scores
        """
        logger.info(
            f"Fusing results: {len(vector_results)} vector, "
            f"{len(document_results)} document, {len(graph_results)} graph"
        )

        # Calculate RRF scores for each modality
        chunk_scores = defaultdict(lambda: {
            "vector_score": 0.0,
            "document_score": 0.0,
            "graph_score": 0.0,
            "rrf_score": 0.0,
            "metadata": {}
        })

        # Vector results
        for result in vector_results:
            chunk_id = result.chunk_id
            rrf_score = profile.vector_weight / (profile.rrf_k + result.rank)
            chunk_scores[chunk_id]["vector_score"] = result.score
            chunk_scores[chunk_id]["rrf_score"] += rrf_score
            chunk_scores[chunk_id]["metadata"] = result.metadata

        # Document results
        for result in document_results:
            chunk_id = result.chunk_id
            rrf_score = profile.document_weight / (profile.rrf_k + result.rank)
            chunk_scores[chunk_id]["document_score"] = result.score
            chunk_scores[chunk_id]["rrf_score"] += rrf_score
            if not chunk_scores[chunk_id]["metadata"]:
                chunk_scores[chunk_id]["metadata"] = result.metadata

        # Graph results
        for result in graph_results:
            chunk_id = result.chunk_id
            rrf_score = profile.graph_weight / (profile.rrf_k + result.rank)
            chunk_scores[chunk_id]["graph_score"] = result.score
            chunk_scores[chunk_id]["rrf_score"] += rrf_score
            chunk_scores[chunk_id]["entity_ids"] = result.entity_ids
            if not chunk_scores[chunk_id]["metadata"]:
                chunk_scores[chunk_id]["metadata"] = result.metadata

        # Convert to list and sort by RRF score
        fused_results = [
            {
                "chunk_id": chunk_id,
                "rrf_score": scores["rrf_score"],
                "vector_score": scores["vector_score"],
                "document_score": scores["document_score"],
                "graph_score": scores["graph_score"],
                "entity_ids": scores.get("entity_ids", []),
                "metadata": scores["metadata"]
            }
            for chunk_id, scores in chunk_scores.items()
        ]

        fused_results.sort(key=lambda x: x["rrf_score"], reverse=True)

        logger.info(f"Fused to {len(fused_results)} unique chunks")

        # Apply diversity constraints if enabled
        if profile.apply_diversity_constraints:
            fused_results = self._apply_diversity(
                results=fused_results,
                max_per_doc=profile.max_chunks_per_doc,
                min_docs=profile.min_distinct_docs
            )

        # Apply deduplication
        fused_results = await self._deduplicate(
            results=fused_results,
            threshold=profile.dedup_threshold
        )

        # Take top K
        fused_results = fused_results[:profile.final_top_k]

        # Add final ranks
        for rank, result in enumerate(fused_results, start=1):
            result["final_rank"] = rank

        logger.info(f"Final fused results: {len(fused_results)} chunks")
        return fused_results

    def _apply_diversity(
        self,
        results: List[Dict[str, Any]],
        max_per_doc: int,
        min_docs: int
    ) -> List[Dict[str, Any]]:
        """
        Apply diversity constraints

        Args:
            results: Fused results
            max_per_doc: Maximum chunks per document
            min_docs: Minimum distinct documents

        Returns:
            Filtered results
        """
        doc_counts: Dict[str, int] = {}
        unique_docs: Set[str] = set()
        diverse_results = []

        for result in results:
            doc_id = result.get("metadata", {}).get("doc_id")

            if not doc_id:
                # Include chunks without doc_id
                diverse_results.append(result)
                continue

            # Check max per doc
            if doc_counts.get(doc_id, 0) < max_per_doc:
                diverse_results.append(result)
                doc_counts[doc_id] = doc_counts.get(doc_id, 0) + 1
                unique_docs.add(doc_id)

        # Check minimum distinct documents
        if len(unique_docs) < min_docs:
            logger.warning(
                f"Only {len(unique_docs)} distinct documents, "
                f"minimum is {min_docs}"
            )

        logger.info(
            f"Diversity applied: {len(results)} → {len(diverse_results)} chunks "
            f"({len(unique_docs)} docs)"
        )

        return diverse_results

    async def _deduplicate(
        self,
        results: List[Dict[str, Any]],
        threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Remove near-duplicate chunks

        Args:
            results: Fused results
            threshold: Similarity threshold for deduplication

        Returns:
            Deduplicated results
        """
        if threshold >= 1.0:
            return results  # No deduplication

        # Simple deduplication based on chunk text similarity
        # In a full implementation, this would use embeddings
        # For now, use exact text matching as approximation

        seen_texts: Set[str] = set()
        deduped_results = []

        for result in results:
            # Get chunk text from metadata (if available)
            chunk_text = result.get("metadata", {}).get("text", "")

            if not chunk_text:
                deduped_results.append(result)
                continue

            # Simple duplicate check (could be enhanced with embeddings)
            if chunk_text not in seen_texts:
                deduped_results.append(result)
                seen_texts.add(chunk_text)

        if len(deduped_results) < len(results):
            logger.info(
                f"Deduplication: {len(results)} → {len(deduped_results)} chunks"
            )

        return deduped_results

    async def rerank(
        self,
        results: List[Dict[str, Any]],
        query: str,
        llm_adapter
    ) -> List[Dict[str, Any]]:
        """
        LLM-based reranking (optional, expensive)

        Args:
            results: Fused results
            query: Original query
            llm_adapter: LLM adapter for reranking

        Returns:
            Reranked results
        """
        logger.info(f"Reranking {len(results)} results")

        try:
            # Build reranking prompt
            chunks_text = "\n\n".join([
                f"[{i+1}] {result.get('metadata', {}).get('text', '')[:500]}"
                for i, result in enumerate(results)
            ])

            prompt = f"""Given the query and the following chunks, rank them by relevance.
Output only the ranking as a JSON array of chunk numbers in order of relevance.

Query: {query}

Chunks:
{chunks_text}

Output format: {{"ranking": [3, 1, 5, 2, 4, ...]}}
"""

            response = await llm_adapter.generate(
                prompt=prompt,
                json_mode=True,
                temperature=0.0
            )

            # Parse ranking
            import json
            ranking_data = json.loads(response["content"])
            ranking = ranking_data.get("ranking", [])

            # Reorder results
            reranked_results = []
            for rank_num in ranking:
                idx = rank_num - 1  # Convert to 0-indexed
                if 0 <= idx < len(results):
                    reranked_results.append(results[idx])

            # Add any remaining results not in ranking
            ranked_indices = set(r - 1 for r in ranking if 0 <= r - 1 < len(results))
            for idx, result in enumerate(results):
                if idx not in ranked_indices:
                    reranked_results.append(result)

            logger.info(f"Reranking complete")
            return reranked_results

        except Exception as e:
            logger.error(f"Reranking failed: {e}, returning original order")
            return results
