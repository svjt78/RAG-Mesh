"""
File-based document store adapter
Implements document and chunk storage using JSON/JSONL files
"""

import json
import aiofiles
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.adapters.base import DocStoreAdapter

logger = logging.getLogger(__name__)


class FileDocStoreAdapter(DocStoreAdapter):
    """File-based implementation of document storage"""

    def __init__(self, data_dir: Path = Path("data")):
        """
        Initialize file-based document store

        Args:
            data_dir: Root data directory
        """
        self.data_dir = data_dir
        self.docs_dir = data_dir / "docs"
        self.chunks_dir = data_dir / "chunks"
        self.index_file = self.docs_dir / "index.json"

        # Create directories if they don't exist
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_dir.mkdir(parents=True, exist_ok=True)

        # File locks for atomic writes
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create a lock for a specific key"""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def _load_index(self) -> Dict[str, Any]:
        """
        Load the document index

        Returns:
            Document index dictionary
        """
        if not self.index_file.exists():
            return {"documents": {}, "updated_at": datetime.now().isoformat()}

        try:
            async with aiofiles.open(self.index_file, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning("Index file corrupted or missing, creating new")
            return {"documents": {}, "updated_at": datetime.now().isoformat()}

    async def _save_index(self, index: Dict[str, Any]) -> None:
        """
        Save the document index

        Args:
            index: Document index to save
        """
        async with self._get_lock("index"):
            index["updated_at"] = datetime.now().isoformat()
            async with aiofiles.open(self.index_file, 'w') as f:
                await f.write(json.dumps(index, indent=2, default=str))

    async def save_document(self, doc_id: str, document: Dict[str, Any]) -> None:
        """
        Save a complete document with pages

        Args:
            doc_id: Unique document identifier
            document: Document data including metadata and pages
        """
        logger.info(f"Saving document: {doc_id}")

        async with self._get_lock(f"doc_{doc_id}"):
            # Add timestamp
            document["saved_at"] = datetime.now().isoformat()

            # Save document file
            doc_path = self.docs_dir / f"{doc_id}.json"
            async with aiofiles.open(doc_path, 'w') as f:
                await f.write(json.dumps(document, indent=2, default=str))

            # Update index
            index = await self._load_index()
            index["documents"][doc_id] = {
                "doc_id": doc_id,
                "filename": document.get("filename", ""),
                "doc_type": document.get("doc_type"),
                "form_number": document.get("form_number"),
                "pages": len(document.get("pages", [])),
                "created_at": document.get("created_at"),
                "indexed_at": document.get("indexed_at"),
                "saved_at": document["saved_at"],
            }
            await self._save_index(index)

        logger.info(f"Document saved: {doc_id}")

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by ID

        Args:
            doc_id: Unique document identifier

        Returns:
            Document data or None if not found
        """
        doc_path = self.docs_dir / f"{doc_id}.json"

        if not doc_path.exists():
            logger.warning(f"Document not found: {doc_id}")
            return None

        try:
            async with aiofiles.open(doc_path, 'r') as f:
                content = await f.read()
                document = json.loads(content)
                logger.info(f"Document retrieved: {doc_id}")
                return document
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error loading document {doc_id}: {e}")
            return None

    async def save_chunks(self, doc_id: str, chunks: List[Dict[str, Any]]) -> None:
        """
        Save chunks for a document

        Args:
            doc_id: Unique document identifier
            chunks: List of chunk data
        """
        logger.info(f"Saving {len(chunks)} chunks for document: {doc_id}")

        async with self._get_lock(f"chunks_{doc_id}"):
            chunks_path = self.chunks_dir / f"{doc_id}.jsonl"

            # Write chunks as JSONL (one JSON object per line)
            async with aiofiles.open(chunks_path, 'w') as f:
                for chunk in chunks:
                    chunk["saved_at"] = datetime.now().isoformat()
                    await f.write(json.dumps(chunk, default=str) + '\n')

        logger.info(f"Chunks saved: {doc_id}")

    async def get_chunks(
        self,
        doc_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks by document ID or filters

        Args:
            doc_id: Optional document identifier
            filters: Optional metadata filters

        Returns:
            List of chunks matching criteria
        """
        chunks = []

        if doc_id:
            # Load chunks for specific document
            chunks_path = self.chunks_dir / f"{doc_id}.jsonl"
            if chunks_path.exists():
                async with aiofiles.open(chunks_path, 'r') as f:
                    async for line in f:
                        if line.strip():
                            chunk = json.loads(line)
                            chunks.append(chunk)
        else:
            # Load all chunks
            for chunks_file in self.chunks_dir.glob("*.jsonl"):
                async with aiofiles.open(chunks_file, 'r') as f:
                    async for line in f:
                        if line.strip():
                            chunk = json.loads(line)
                            chunks.append(chunk)

        # Apply filters if provided
        if filters:
            filtered_chunks = []
            for chunk in chunks:
                match = True
                for key, value in filters.items():
                    if key in chunk.get("metadata", {}):
                        if chunk["metadata"][key] != value:
                            match = False
                            break
                    elif key in chunk:
                        if chunk[key] != value:
                            match = False
                            break
                if match:
                    filtered_chunks.append(chunk)
            chunks = filtered_chunks

        logger.info(f"Retrieved {len(chunks)} chunks")
        return chunks

    async def list_documents(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        List all documents with optional filters

        Args:
            filters: Optional metadata filters

        Returns:
            List of document metadata
        """
        index = await self._load_index()
        documents = list(index["documents"].values())

        # Apply filters if provided
        if filters:
            filtered_docs = []
            for doc in documents:
                match = True
                for key, value in filters.items():
                    if key in doc:
                        if doc[key] != value:
                            match = False
                            break
                if match:
                    filtered_docs.append(doc)
            documents = filtered_docs

        logger.info(f"Listed {len(documents)} documents")
        return documents

    async def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document and its chunks

        Args:
            doc_id: Unique document identifier

        Returns:
            True if deleted, False if not found
        """
        logger.info(f"Deleting document: {doc_id}")

        doc_path = self.docs_dir / f"{doc_id}.json"
        chunks_path = self.chunks_dir / f"{doc_id}.jsonl"

        if not doc_path.exists():
            logger.warning(f"Document not found for deletion: {doc_id}")
            return False

        async with self._get_lock(f"doc_{doc_id}"):
            # Delete document file
            doc_path.unlink(missing_ok=True)

            # Delete chunks file
            chunks_path.unlink(missing_ok=True)

            # Update index
            index = await self._load_index()
            if doc_id in index["documents"]:
                del index["documents"][doc_id]
                await self._save_index(index)

        logger.info(f"Document deleted: {doc_id}")
        return True

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics

        Returns:
            Statistics dictionary
        """
        index = await self._load_index()
        total_docs = len(index["documents"])

        # Count total chunks
        total_chunks = 0
        for chunks_file in self.chunks_dir.glob("*.jsonl"):
            async with aiofiles.open(chunks_file, 'r') as f:
                async for line in f:
                    if line.strip():
                        total_chunks += 1

        return {
            "total_documents": total_docs,
            "total_chunks": total_chunks,
            "index_updated_at": index.get("updated_at"),
        }
