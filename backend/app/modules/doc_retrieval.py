"""
Document retrieval module
Keyword-based retrieval using TF-IDF and BM25
"""

import logging
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from rank_bm25 import BM25Okapi
import numpy as np

from app.adapters.base import DocStoreAdapter
from app.core.models import DocumentResult, RetrievalProfile

logger = logging.getLogger(__name__)


class DocumentRetrievalModule:
    """Handles keyword-based document retrieval"""

    def __init__(self, doc_store: DocStoreAdapter):
        """
        Initialize document retrieval module

        Args:
            doc_store: Document store adapter
        """
        self.doc_store = doc_store
        self.bm25: Optional[BM25Okapi] = None
        self.tfidf: Optional[TfidfVectorizer] = None
        self.chunks_cache: List[Dict[str, Any]] = []

    async def index_chunks(
        self,
        chunks: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Index chunks for retrieval

        Args:
            chunks: Optional list of chunks (if None, loads all from store)
        """
        logger.info("Indexing chunks for document retrieval")

        # Load chunks if not provided
        if chunks is None:
            chunks = await self.doc_store.get_chunks()

        if not chunks:
            logger.warning("No chunks to index")
            return

        self.chunks_cache = chunks

        # Prepare texts
        texts = [chunk.get("text", "") for chunk in chunks]

        # Tokenize for BM25
        tokenized_texts = [text.lower().split() for text in texts]
        self.bm25 = BM25Okapi(tokenized_texts)

        # Build TF-IDF vectorizer
        self.tfidf = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.tfidf.fit(texts)

        logger.info(f"Indexed {len(chunks)} chunks")

    async def retrieve(
        self,
        query: str,
        profile: RetrievalProfile,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[DocumentResult]:
        """
        Retrieve chunks using BM25 and TF-IDF

        Args:
            query: Search query
            profile: Retrieval profile
            filters: Optional metadata filters

        Returns:
            List of DocumentResult objects
        """
        logger.info(f"Document retrieval for query: '{query[:50]}...'")

        if not self.chunks_cache:
            logger.warning("No chunks indexed, returning empty results")
            return []

        try:
            # Get BM25 scores
            bm25_scores = self._get_bm25_scores(query)

            # Get TF-IDF scores
            tfidf_scores = self._get_tfidf_scores(query)

            # Combine scores (weighted average)
            combined_scores = 0.6 * bm25_scores + 0.4 * tfidf_scores

            # Apply exact match boosting
            combined_scores = self._apply_boost(
                query=query,
                scores=combined_scores,
                profile=profile
            )

            # Get top-k indices
            top_k_indices = np.argsort(combined_scores)[::-1][:profile.doc_k]

            # Build results
            results = []
            for rank, idx in enumerate(top_k_indices, start=1):
                chunk = self.chunks_cache[idx]
                score = float(combined_scores[idx])

                # Apply filters
                if filters and not self._matches_filters(chunk, filters):
                    continue

                result = DocumentResult(
                    chunk_id=chunk.get("chunk_id", ""),
                    score=score,
                    rank=rank,
                    metadata=chunk.get("metadata", {})
                )
                results.append(result)

            logger.info(f"Document retrieval returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error in document retrieval: {e}")
            return []

    def _get_bm25_scores(self, query: str) -> np.ndarray:
        """Get BM25 scores for query"""
        if self.bm25 is None:
            return np.zeros(len(self.chunks_cache))

        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        # Normalize to 0-1 range
        if scores.max() > 0:
            scores = scores / scores.max()

        return scores

    def _get_tfidf_scores(self, query: str) -> np.ndarray:
        """Get TF-IDF scores for query"""
        if self.tfidf is None:
            return np.zeros(len(self.chunks_cache))

        # Transform query
        query_vector = self.tfidf.transform([query])

        # Transform all documents
        doc_vectors = self.tfidf.transform([
            chunk.get("text", "") for chunk in self.chunks_cache
        ])

        # Calculate cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        scores = cosine_similarity(query_vector, doc_vectors)[0]

        return scores

    def _apply_boost(
        self,
        query: str,
        scores: np.ndarray,
        profile: RetrievalProfile
    ) -> np.ndarray:
        """
        Apply boost factors for exact matches

        Args:
            query: Search query
            scores: Current scores
            profile: Retrieval profile with boost factors

        Returns:
            Boosted scores
        """
        query_lower = query.lower()
        boosted_scores = scores.copy()

        for idx, chunk in enumerate(self.chunks_cache):
            chunk_text = chunk.get("text", "").lower()
            metadata = chunk.get("metadata", {})

            # Boost for exact keyword match
            if query_lower in chunk_text:
                boosted_scores[idx] *= profile.doc_boost_exact_match

            # Boost for form number match
            form_number = metadata.get("form_number")
            if form_number and form_number.lower() in query_lower:
                boosted_scores[idx] *= profile.doc_boost_form_number

            # Boost for defined term match (if configured)
            if hasattr(profile, 'doc_boost_defined_term'):
                # Check if query contains defined terms (simple heuristic)
                if '"' in query and query.strip('"').lower() in chunk_text:
                    boosted_scores[idx] *= profile.doc_boost_defined_term

        return boosted_scores

    def _matches_filters(
        self,
        chunk: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> bool:
        """Check if chunk matches filters"""
        metadata = chunk.get("metadata", {})

        for key, value in filters.items():
            if key in metadata and metadata[key] != value:
                return False

        return True
