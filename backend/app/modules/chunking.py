"""
Chunking module
Creates chunks from documents with page-aware and sentence-aware strategies
"""

import logging
import re
from typing import List, Dict, Any
import tiktoken
import uuid

from app.core.models import Document, Chunk, ChunkingProfile

logger = logging.getLogger(__name__)


class ChunkingModule:
    """Handles document chunking with various strategies"""

    def __init__(self, encoding_name: str = "cl100k_base"):
        """
        Initialize chunking module

        Args:
            encoding_name: Tiktoken encoding name for token counting
        """
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning(f"Failed to load encoding {encoding_name}: {e}")
            self.encoding = tiktoken.get_encoding("cl100k_base")

    async def chunk_document(
        self,
        document: Document,
        profile: ChunkingProfile
    ) -> List[Chunk]:
        """
        Chunk a document according to the profile

        Args:
            document: Document to chunk
            profile: Chunking profile with strategy

        Returns:
            List of chunks
        """
        logger.info(f"Chunking document {document.doc_id} with profile")

        chunks = []

        if profile.page_aware:
            # Process each page separately
            for page in document.pages:
                page_chunks = await self._chunk_text(
                    text=page.text,
                    page_no=page.page_no,
                    doc_id=document.doc_id,
                    chunk_size=profile.chunk_size,
                    chunk_overlap=profile.chunk_overlap,
                    sentence_aware=profile.sentence_aware,
                    metadata=document.metadata
                )
                chunks.extend(page_chunks)
        else:
            # Combine all pages and chunk
            combined_text = " ".join([page.text for page in document.pages])
            chunks = await self._chunk_text(
                text=combined_text,
                page_no=1,  # Default to page 1 if not page-aware
                doc_id=document.doc_id,
                chunk_size=profile.chunk_size,
                chunk_overlap=profile.chunk_overlap,
                sentence_aware=profile.sentence_aware,
                metadata=document.metadata
            )

        # Apply max chunks limit if specified
        if profile.max_chunks_per_doc and len(chunks) > profile.max_chunks_per_doc:
            logger.warning(
                f"Document has {len(chunks)} chunks, limiting to {profile.max_chunks_per_doc}"
            )
            chunks = chunks[:profile.max_chunks_per_doc]

        logger.info(f"Created {len(chunks)} chunks for document {document.doc_id}")
        return chunks

    async def _chunk_text(
        self,
        text: str,
        page_no: int,
        doc_id: str,
        chunk_size: int,
        chunk_overlap: int,
        sentence_aware: bool,
        metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """
        Chunk text with specified parameters

        Args:
            text: Text to chunk
            page_no: Page number
            doc_id: Document ID
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap size in characters
            sentence_aware: Whether to respect sentence boundaries
            metadata: Document metadata to propagate

        Returns:
            List of chunks
        """
        if not text.strip():
            return []

        chunks = []

        if sentence_aware:
            # Split by sentences first
            sentences = self._split_sentences(text)
            chunks = self._chunk_by_sentences(
                sentences=sentences,
                page_no=page_no,
                doc_id=doc_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                metadata=metadata
            )
        else:
            # Simple character-based chunking
            chunks = self._chunk_by_characters(
                text=text,
                page_no=page_no,
                doc_id=doc_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                metadata=metadata
            )

        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Simple sentence splitter (can be enhanced with spaCy/NLTK)
        # Split on period, exclamation, question mark followed by space or newline
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(sentence_pattern, text)

        # Clean up sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def _chunk_by_sentences(
        self,
        sentences: List[str],
        page_no: int,
        doc_id: str,
        chunk_size: int,
        chunk_overlap: int,
        metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """
        Create chunks by grouping sentences

        Args:
            sentences: List of sentences
            page_no: Page number
            doc_id: Document ID
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap size in characters
            metadata: Document metadata

        Returns:
            List of chunks
        """
        chunks = []
        current_chunk_text = ""
        char_start = 0

        for sentence in sentences:
            # Check if adding this sentence exceeds chunk size
            if current_chunk_text and len(current_chunk_text) + len(sentence) > chunk_size:
                # Create chunk
                chunk = self._create_chunk(
                    text=current_chunk_text,
                    char_start=char_start,
                    page_no=page_no,
                    doc_id=doc_id,
                    metadata=metadata
                )
                chunks.append(chunk)

                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk_text, chunk_overlap)
                char_start = char_start + len(current_chunk_text) - len(overlap_text)
                current_chunk_text = overlap_text + " " + sentence
            else:
                # Add sentence to current chunk
                if current_chunk_text:
                    current_chunk_text += " " + sentence
                else:
                    current_chunk_text = sentence

        # Add final chunk if any text remains
        if current_chunk_text.strip():
            chunk = self._create_chunk(
                text=current_chunk_text,
                char_start=char_start,
                page_no=page_no,
                doc_id=doc_id,
                metadata=metadata
            )
            chunks.append(chunk)

        return chunks

    def _chunk_by_characters(
        self,
        text: str,
        page_no: int,
        doc_id: str,
        chunk_size: int,
        chunk_overlap: int,
        metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """
        Create chunks by character count

        Args:
            text: Text to chunk
            page_no: Page number
            doc_id: Document ID
            chunk_size: Chunk size in characters
            chunk_overlap: Overlap size in characters
            metadata: Document metadata

        Returns:
            List of chunks
        """
        chunks = []
        text_length = len(text)
        start = 0

        while start < text_length:
            # Calculate end position
            end = start + chunk_size

            # Extract chunk text
            chunk_text = text[start:end]

            # Create chunk
            chunk = self._create_chunk(
                text=chunk_text,
                char_start=start,
                page_no=page_no,
                doc_id=doc_id,
                metadata=metadata
            )
            chunks.append(chunk)

            # Move start position with overlap
            start = end - chunk_overlap

        return chunks

    def _create_chunk(
        self,
        text: str,
        char_start: int,
        page_no: int,
        doc_id: str,
        metadata: Dict[str, Any]
    ) -> Chunk:
        """
        Create a Chunk object

        Args:
            text: Chunk text
            char_start: Character start position in page
            page_no: Page number
            doc_id: Document ID
            metadata: Document metadata

        Returns:
            Chunk object
        """
        chunk_id = f"{doc_id}_p{page_no}_c{uuid.uuid4().hex[:8]}"

        # Count tokens
        tokens = self._count_tokens(text)

        # Create chunk metadata
        chunk_metadata = {
            "doc_type": metadata.get("doc_type"),
            "form_number": metadata.get("form_number"),
            "state": metadata.get("state"),
        }

        chunk = Chunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            text=text,
            page_no=page_no,
            char_start=char_start,
            char_end=char_start + len(text),
            tokens=tokens,
            metadata=chunk_metadata
        )

        return chunk

    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """
        Get overlap text from end of current chunk

        Args:
            text: Current chunk text
            overlap_size: Desired overlap size

        Returns:
            Overlap text
        """
        if len(text) <= overlap_size:
            return text

        return text[-overlap_size:]

    def _count_tokens(self, text: str) -> int:
        """
        Count tokens in text

        Args:
            text: Input text

        Returns:
            Number of tokens
        """
        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4
