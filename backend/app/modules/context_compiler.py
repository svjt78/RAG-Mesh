"""
Context compilation module
Compiles retrieved chunks into context with token budget enforcement
"""

import logging
from typing import List, Dict, Any
import tiktoken

from app.core.models import ContextProfile, ContextPack
from app.adapters.base import DocStoreAdapter

logger = logging.getLogger(__name__)


class ContextCompilerModule:
    """Handles context compilation with token budget management"""

    def __init__(self, doc_store: DocStoreAdapter, encoding_name: str = "cl100k_base"):
        """
        Initialize context compiler

        Args:
            doc_store: Document store for loading chunk texts
            encoding_name: Tiktoken encoding name
        """
        self.doc_store = doc_store
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning(f"Failed to load encoding {encoding_name}: {e}")
            self.encoding = tiktoken.get_encoding("cl100k_base")

    async def compile_context(
        self,
        fused_results: List[Dict[str, Any]],
        query: str,
        profile: ContextProfile
    ) -> ContextPack:
        """
        Compile context from fused results with token budget

        Args:
            fused_results: Fused retrieval results
            query: Original query
            profile: Context profile with token budget

        Returns:
            ContextPack with compiled context
        """
        logger.info(f"Compiling context with budget of {profile.max_context_tokens} tokens")

        # Calculate available budget (reserve for query and instructions)
        available_tokens = profile.max_context_tokens
        if hasattr(profile, 'reserve_tokens_for_query'):
            available_tokens -= profile.reserve_tokens_for_query
        if hasattr(profile, 'reserve_tokens_for_instructions'):
            available_tokens -= profile.reserve_tokens_for_instructions

        # Load chunk texts
        chunks_with_text = await self._load_chunk_texts(fused_results)

        # Pack chunks within budget
        packed_chunks, context_text, tokens_used = await self._pack_chunks(
            chunks=chunks_with_text,
            budget=available_tokens,
            profile=profile
        )

        # Generate coverage report
        coverage = self._generate_coverage(query, packed_chunks)

        # Apply PII redaction if enabled
        redactions = []
        if profile.redact_pii:
            context_text, redactions = self._redact_pii(context_text)

        # Create ContextPack
        context_pack = ContextPack(
            context_text=context_text,
            chunks=packed_chunks,
            token_budget=profile.max_context_tokens,
            tokens_used=tokens_used,
            coverage=coverage,
            redactions_applied=redactions,
            metadata={
                "num_chunks": len(packed_chunks),
                "citation_format": profile.citation_format,
                "query": query
            }
        )

        logger.info(
            f"Context compiled: {len(packed_chunks)} chunks, "
            f"{tokens_used}/{profile.max_context_tokens} tokens"
        )

        return context_pack

    async def _load_chunk_texts(
        self,
        fused_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Load chunk texts from storage

        Args:
            fused_results: Fused results with chunk IDs

        Returns:
            Results with chunk texts loaded
        """
        # Get all chunk IDs
        chunk_ids = [result["chunk_id"] for result in fused_results]

        # Load chunks from store
        all_chunks = await self.doc_store.get_chunks()
        chunk_map = {chunk["chunk_id"]: chunk for chunk in all_chunks}

        # Add chunk text to results
        enriched_results = []
        for result in fused_results:
            chunk_id = result["chunk_id"]
            chunk = chunk_map.get(chunk_id, {})

            enriched_result = result.copy()
            enriched_result["text"] = chunk.get("text", "")
            enriched_result["doc_id"] = chunk.get("doc_id", "")
            enriched_result["page_no"] = chunk.get("page_no", 1)
            enriched_results.append(enriched_result)

        return enriched_results

    async def _pack_chunks(
        self,
        chunks: List[Dict[str, Any]],
        budget: int,
        profile: ContextProfile
    ) -> tuple[List[Dict[str, Any]], str, int]:
        """
        Pack chunks within token budget

        Args:
            chunks: Chunks to pack
            budget: Token budget
            profile: Context profile

        Returns:
            Tuple of (packed_chunks, context_text, tokens_used)
        """
        packed_chunks = []
        context_parts = []
        total_tokens = 0

        for rank, chunk in enumerate(chunks, start=1):
            chunk_text = chunk.get("text", "")
            if not chunk_text:
                continue

            # Build chunk with citation
            if profile.citation_format == "inline":
                chunk_with_citation = self._format_inline_citation(chunk, rank, profile)
            elif profile.citation_format == "detailed":
                chunk_with_citation = self._format_detailed_citation(chunk, rank, profile)
            else:
                chunk_with_citation = chunk_text

            # Count tokens
            chunk_tokens = self._count_tokens(chunk_with_citation)

            # Check if adding this chunk exceeds budget
            if total_tokens + chunk_tokens > budget:
                logger.info(f"Token budget reached at chunk {rank}")
                break

            # Add chunk
            packed_chunks.append({
                "chunk_id": chunk["chunk_id"],
                "doc_id": chunk.get("doc_id", ""),
                "page_no": chunk.get("page_no", 1),
                "rank": rank,
                "tokens": chunk_tokens,
                "text": chunk_text,
                "rrf_score": chunk.get("rrf_score", 0.0)
            })
            context_parts.append(chunk_with_citation)
            total_tokens += chunk_tokens

        # Combine context
        context_text = "\n\n".join(context_parts)

        return packed_chunks, context_text, total_tokens

    def _format_inline_citation(
        self,
        chunk: Dict[str, Any],
        rank: int,
        profile: ContextProfile
    ) -> str:
        """Format chunk with inline citation"""
        text = chunk.get("text", "")

        citation_parts = [f"[{rank}]"]
        if profile.include_page_numbers:
            page_no = chunk.get("page_no", 1)
            citation_parts.append(f"(Page {page_no})")

        if profile.include_doc_metadata:
            doc_id = chunk.get("doc_id", "")
            if doc_id:
                citation_parts.append(f"(Doc: {doc_id[:8]})")

        citation = " ".join(citation_parts)
        return f"{citation} {text}"

    def _format_detailed_citation(
        self,
        chunk: Dict[str, Any],
        rank: int,
        profile: ContextProfile
    ) -> str:
        """Format chunk with detailed citation"""
        text = chunk.get("text", "")
        doc_id = chunk.get("doc_id", "")
        page_no = chunk.get("page_no", 1)

        metadata = chunk.get("metadata", {})
        form_number = metadata.get("form_number", "N/A")

        citation = f"[Citation {rank}]\n"
        citation += f"Document: {doc_id}\n"
        citation += f"Page: {page_no}\n"
        citation += f"Form: {form_number}\n"
        citation += f"Content: {text}"

        return citation

    def _generate_coverage(
        self,
        query: str,
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        Generate coverage report mapping query facets to evidence

        Args:
            query: Original query
            chunks: Packed chunks

        Returns:
            Coverage mapping
        """
        # Simple coverage: map query terms to chunks that contain them
        coverage = {}

        # Extract key terms from query (simple approach)
        query_terms = [term.lower() for term in query.split() if len(term) > 3]

        for term in query_terms:
            supporting_chunks = []
            for chunk in chunks:
                chunk_text = chunk.get("text", "").lower()
                if term in chunk_text:
                    supporting_chunks.append(chunk["chunk_id"])

            if supporting_chunks:
                coverage[term] = supporting_chunks

        return coverage

    def _redact_pii(self, text: str) -> tuple[str, List[str]]:
        """
        Redact PII from text

        Args:
            text: Input text

        Returns:
            Tuple of (redacted_text, redaction_log)
        """
        import re

        redactions = []
        redacted_text = text

        # SSN pattern
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        if re.search(ssn_pattern, redacted_text):
            redacted_text = re.sub(ssn_pattern, '[SSN-REDACTED]', redacted_text)
            redactions.append("SSN")

        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, redacted_text):
            redacted_text = re.sub(email_pattern, '[EMAIL-REDACTED]', redacted_text)
            redactions.append("Email")

        # Phone pattern
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        if re.search(phone_pattern, redacted_text):
            redacted_text = re.sub(phone_pattern, '[PHONE-REDACTED]', redacted_text)
            redactions.append("Phone")

        return redacted_text, redactions

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            return len(text) // 4  # Fallback estimate
