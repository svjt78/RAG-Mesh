"""
Unit tests for FileDocStore adapter
"""

import json
import os

import pytest

from app.adapters.file_doc_store import FileDocStore
from app.core.models import Chunk, Document, Page


@pytest.mark.unit
class TestFileDocStore:
    """Test cases for FileDocStore adapter."""

    @pytest.fixture
    def doc_store(self, test_data_dir: str) -> FileDocStore:
        """Create a FileDocStore instance for testing."""
        return FileDocStore(data_dir=test_data_dir)

    @pytest.mark.asyncio
    async def test_save_and_get_document(
        self, doc_store: FileDocStore, sample_document: Document
    ):
        """Test saving and retrieving a document."""
        # Save document
        await doc_store.save_document(sample_document)

        # Verify file was created
        doc_path = os.path.join(
            doc_store.docs_dir, f"{sample_document.doc_id}.json"
        )
        assert os.path.exists(doc_path)

        # Retrieve document
        retrieved = await doc_store.get_document(sample_document.doc_id)
        assert retrieved is not None
        assert retrieved.doc_id == sample_document.doc_id
        assert retrieved.filename == sample_document.filename
        assert len(retrieved.pages) == len(sample_document.pages)
        assert retrieved.metadata == sample_document.metadata

    @pytest.mark.asyncio
    async def test_get_nonexistent_document(self, doc_store: FileDocStore):
        """Test retrieving a document that doesn't exist."""
        result = await doc_store.get_document("nonexistent_doc")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_documents(
        self, doc_store: FileDocStore, sample_document: Document
    ):
        """Test listing all documents."""
        # Initially empty
        docs = await doc_store.list_documents()
        assert len(docs) == 0

        # Save a document
        await doc_store.save_document(sample_document)

        # List should contain the document
        docs = await doc_store.list_documents()
        assert len(docs) == 1
        assert docs[0].doc_id == sample_document.doc_id

    @pytest.mark.asyncio
    async def test_delete_document(
        self, doc_store: FileDocStore, sample_document: Document
    ):
        """Test deleting a document."""
        # Save document first
        await doc_store.save_document(sample_document)
        assert await doc_store.get_document(sample_document.doc_id) is not None

        # Delete document
        await doc_store.delete_document(sample_document.doc_id)

        # Verify it's gone
        assert await doc_store.get_document(sample_document.doc_id) is None

    @pytest.mark.asyncio
    async def test_save_and_get_chunks(
        self, doc_store: FileDocStore, sample_chunks: list[Chunk]
    ):
        """Test saving and retrieving chunks."""
        doc_id = sample_chunks[0].doc_id

        # Save chunks
        await doc_store.save_chunks(doc_id, sample_chunks)

        # Verify file was created
        chunks_path = os.path.join(doc_store.chunks_dir, f"{doc_id}.json")
        assert os.path.exists(chunks_path)

        # Retrieve chunks
        retrieved = await doc_store.get_chunks(doc_id)
        assert len(retrieved) == len(sample_chunks)
        assert all(isinstance(chunk, Chunk) for chunk in retrieved)
        assert retrieved[0].chunk_id == sample_chunks[0].chunk_id
        assert retrieved[0].text == sample_chunks[0].text

    @pytest.mark.asyncio
    async def test_get_chunks_for_nonexistent_doc(self, doc_store: FileDocStore):
        """Test retrieving chunks for a document that doesn't exist."""
        chunks = await doc_store.get_chunks("nonexistent_doc")
        assert chunks == []

    @pytest.mark.asyncio
    async def test_get_chunk_by_id(
        self, doc_store: FileDocStore, sample_chunks: list[Chunk]
    ):
        """Test retrieving a specific chunk by ID."""
        doc_id = sample_chunks[0].doc_id
        chunk_id = sample_chunks[0].chunk_id

        # Save chunks first
        await doc_store.save_chunks(doc_id, sample_chunks)

        # Retrieve specific chunk
        chunk = await doc_store.get_chunk_by_id(chunk_id, doc_id)
        assert chunk is not None
        assert chunk.chunk_id == chunk_id
        assert chunk.text == sample_chunks[0].text

    @pytest.mark.asyncio
    async def test_get_chunk_by_id_not_found(
        self, doc_store: FileDocStore, sample_chunks: list[Chunk]
    ):
        """Test retrieving a chunk that doesn't exist."""
        doc_id = sample_chunks[0].doc_id
        await doc_store.save_chunks(doc_id, sample_chunks)

        # Try to get non-existent chunk
        chunk = await doc_store.get_chunk_by_id("nonexistent_chunk", doc_id)
        assert chunk is None

    @pytest.mark.asyncio
    async def test_update_document_metadata(
        self, doc_store: FileDocStore, sample_document: Document
    ):
        """Test updating document metadata."""
        # Save document
        await doc_store.save_document(sample_document)

        # Update metadata
        new_metadata = {**sample_document.metadata, "indexed": True}
        sample_document.metadata = new_metadata
        await doc_store.save_document(sample_document)

        # Retrieve and verify
        retrieved = await doc_store.get_document(sample_document.doc_id)
        assert retrieved is not None
        assert retrieved.metadata["indexed"] is True

    @pytest.mark.asyncio
    async def test_concurrent_saves(
        self, doc_store: FileDocStore, sample_document: Document
    ):
        """Test concurrent document saves."""
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
                        text=f"Content {i}",
                        bbox={"x0": 0, "y0": 0, "x1": 100, "y1": 100},
                    )
                ],
            )
            for i in range(5)
        ]

        # Save concurrently
        await asyncio.gather(*[doc_store.save_document(doc) for doc in docs])

        # Verify all were saved
        saved_docs = await doc_store.list_documents()
        assert len(saved_docs) == 5
        saved_ids = {doc.doc_id for doc in saved_docs}
        expected_ids = {f"doc{i}" for i in range(5)}
        assert saved_ids == expected_ids

    @pytest.mark.asyncio
    async def test_save_empty_document(self, doc_store: FileDocStore):
        """Test saving a document with no pages."""
        empty_doc = Document(
            doc_id="empty123",
            filename="empty.pdf",
            metadata={},
            pages=[],
        )

        await doc_store.save_document(empty_doc)
        retrieved = await doc_store.get_document("empty123")
        assert retrieved is not None
        assert len(retrieved.pages) == 0

    @pytest.mark.asyncio
    async def test_large_document(self, doc_store: FileDocStore):
        """Test handling a document with many pages."""
        large_doc = Document(
            doc_id="large123",
            filename="large.pdf",
            metadata={},
            pages=[
                Page(
                    page_num=i,
                    text=f"Page {i} content " * 100,  # Longer text
                    bbox={"x0": 0, "y0": 0, "x1": 100, "y1": 100},
                )
                for i in range(1, 101)  # 100 pages
            ],
        )

        await doc_store.save_document(large_doc)
        retrieved = await doc_store.get_document("large123")
        assert retrieved is not None
        assert len(retrieved.pages) == 100

    @pytest.mark.asyncio
    async def test_special_characters_in_metadata(self, doc_store: FileDocStore):
        """Test handling special characters in metadata."""
        doc = Document(
            doc_id="special123",
            filename="special.pdf",
            metadata={
                "description": "Policy with 'quotes' and \"double quotes\"",
                "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
                "unicode": "Policy für Deutschland 保险单",
            },
            pages=[
                Page(
                    page_num=1,
                    text="Content",
                    bbox={"x0": 0, "y0": 0, "x1": 100, "y1": 100},
                )
            ],
        )

        await doc_store.save_document(doc)
        retrieved = await doc_store.get_document("special123")
        assert retrieved is not None
        assert retrieved.metadata["description"] == doc.metadata["description"]
        assert retrieved.metadata["unicode"] == doc.metadata["unicode"]
