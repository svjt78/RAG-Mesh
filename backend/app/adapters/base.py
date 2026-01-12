"""
Base adapter interfaces for RAGMesh
Defines abstract base classes for all external dependencies
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path


class DocStoreAdapter(ABC):
    """Abstract interface for document storage"""

    @abstractmethod
    async def save_document(self, doc_id: str, document: Dict[str, Any]) -> None:
        """
        Save a complete document with pages

        Args:
            doc_id: Unique document identifier
            document: Document data including metadata and pages
        """
        pass

    @abstractmethod
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by ID

        Args:
            doc_id: Unique document identifier

        Returns:
            Document data or None if not found
        """
        pass

    @abstractmethod
    async def save_chunks(self, doc_id: str, chunks: List[Dict[str, Any]]) -> None:
        """
        Save chunks for a document

        Args:
            doc_id: Unique document identifier
            chunks: List of chunk data
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document and its chunks

        Args:
            doc_id: Unique document identifier

        Returns:
            True if deleted, False if not found
        """
        pass


class VectorStoreAdapter(ABC):
    """Abstract interface for vector storage and search"""

    @abstractmethod
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
        pass

    @abstractmethod
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
            threshold: Optional similarity threshold
            filters: Optional metadata filters

        Returns:
            List of results with chunk_id, score, and metadata
        """
        pass

    @abstractmethod
    async def save_index(self, path: Path) -> None:
        """
        Persist the index to disk

        Args:
            path: Path to save the index
        """
        pass

    @abstractmethod
    async def load_index(self, path: Path) -> None:
        """
        Load the index from disk

        Args:
            path: Path to load the index from
        """
        pass

    @abstractmethod
    async def get_index_size(self) -> int:
        """
        Get the number of vectors in the index

        Returns:
            Number of vectors
        """
        pass


class GraphStoreAdapter(ABC):
    """Abstract interface for graph storage and traversal"""

    @abstractmethod
    async def add_nodes(self, nodes: List[Dict[str, Any]]) -> None:
        """
        Add nodes to the graph

        Args:
            nodes: List of node data with id, type, label, properties, chunk_ids
        """
        pass

    @abstractmethod
    async def add_edges(self, edges: List[Dict[str, Any]]) -> None:
        """
        Add edges to the graph

        Args:
            edges: List of edge data with source, target, type, properties, evidence_chunk_ids
        """
        pass

    @abstractmethod
    async def query_subgraph(
        self,
        entity_ids: List[str],
        max_hops: int = 2
    ) -> Dict[str, Any]:
        """
        Extract a subgraph around entities

        Args:
            entity_ids: List of entity IDs to start from
            max_hops: Maximum number of hops from seed entities

        Returns:
            Subgraph with nodes and edges
        """
        pass

    @abstractmethod
    async def get_supporting_chunks(self, entity_ids: List[str]) -> List[str]:
        """
        Get chunk IDs that support entities

        Args:
            entity_ids: List of entity IDs

        Returns:
            List of unique chunk IDs
        """
        pass

    @abstractmethod
    async def find_entities(
        self,
        labels: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find entities by labels or types

        Args:
            labels: Optional list of entity labels
            entity_types: Optional list of entity types

        Returns:
            List of matching entities
        """
        pass

    @abstractmethod
    async def save_graph(self, path: Path) -> None:
        """
        Persist the graph to disk

        Args:
            path: Path to save the graph
        """
        pass

    @abstractmethod
    async def load_graph(self, path: Path) -> None:
        """
        Load the graph from disk

        Args:
            path: Path to load the graph from
        """
        pass


class LLMAdapter(ABC):
    """Abstract interface for LLM operations"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate text completion

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            json_mode: Whether to enforce JSON output
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Dict with 'content', 'tokens_used', 'cost'
        """
        pass

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    async def extract_entities(
        self,
        text: str,
        entity_types: List[str]
    ) -> Dict[str, Any]:
        """
        Extract structured entities from text

        Args:
            text: Input text
            entity_types: Expected entity types

        Returns:
            Extracted entities and relationships
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text

        Args:
            text: Input text

        Returns:
            Number of tokens
        """
        pass


class JudgeAdapter(ABC):
    """Abstract interface for validation checks"""

    @abstractmethod
    async def evaluate(
        self,
        query: str,
        context: str,
        answer: str,
        citations: List[Dict[str, Any]],
        check_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate answer quality

        Args:
            query: Original query
            context: Context used for generation
            answer: Generated answer
            citations: List of citations
            check_config: Configuration for checks

        Returns:
            JudgeReport with scores, violations, and decision
        """
        pass


class RerankAdapter(ABC):
    """Abstract interface for reranking (optional)"""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Rerank chunks by relevance

        Args:
            query: Query text
            chunks: List of chunks with metadata
            top_k: Number of top results to return

        Returns:
            Reranked chunks
        """
        pass
