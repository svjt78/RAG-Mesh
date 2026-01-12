"""
Pytest configuration and shared fixtures
"""

import asyncio
import os
import shutil
import tempfile
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.models import (
    Chunk,
    Citation,
    Document,
    Edge,
    EntityType,
    GraphResult,
    Node,
    Page,
    RelationType,
)


# === Pytest Configuration ===

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# === Temporary Directories ===

@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_data_dir(temp_dir: str) -> str:
    """Create test data directory structure."""
    data_dir = os.path.join(temp_dir, "data")
    os.makedirs(os.path.join(data_dir, "docs"), exist_ok=True)
    os.makedirs(os.path.join(data_dir, "chunks"), exist_ok=True)
    os.makedirs(os.path.join(data_dir, "vectors"), exist_ok=True)
    os.makedirs(os.path.join(data_dir, "graph"), exist_ok=True)
    os.makedirs(os.path.join(data_dir, "runs"), exist_ok=True)
    return data_dir


# === Sample Data Fixtures ===

@pytest.fixture
def sample_document() -> Document:
    """Create a sample document for testing."""
    return Document(
        doc_id="doc123",
        filename="sample.pdf",
        metadata={
            "form_number": "HO-3",
            "doc_type": "policy",
            "state": "CA",
            "upload_date": "2024-01-01T00:00:00Z",
        },
        pages=[
            Page(
                page_num=1,
                text="This is a homeowners insurance policy. Coverage A: Dwelling - $500,000. Coverage B: Other Structures - $50,000.",
                bbox={"x0": 0, "y0": 0, "x1": 100, "y1": 100},
            ),
            Page(
                page_num=2,
                text="Section I - Exclusions. We do not cover water damage caused by flood or surface water.",
                bbox={"x0": 0, "y0": 0, "x1": 100, "y1": 100},
            ),
        ],
    )


@pytest.fixture
def sample_chunks() -> list[Chunk]:
    """Create sample chunks for testing."""
    return [
        Chunk(
            chunk_id="chunk1",
            doc_id="doc123",
            text="This is a homeowners insurance policy. Coverage A: Dwelling - $500,000.",
            metadata={
                "page_num": 1,
                "form_number": "HO-3",
                "doc_type": "policy",
                "state": "CA",
            },
            start_char=0,
            end_char=75,
        ),
        Chunk(
            chunk_id="chunk2",
            doc_id="doc123",
            text="Coverage B: Other Structures - $50,000. This provides coverage for detached structures.",
            metadata={
                "page_num": 1,
                "form_number": "HO-3",
                "doc_type": "policy",
                "state": "CA",
            },
            start_char=76,
            end_char=165,
        ),
        Chunk(
            chunk_id="chunk3",
            doc_id="doc123",
            text="Section I - Exclusions. We do not cover water damage caused by flood or surface water.",
            metadata={
                "page_num": 2,
                "form_number": "HO-3",
                "doc_type": "policy",
                "state": "CA",
            },
            start_char=0,
            end_char=88,
        ),
    ]


@pytest.fixture
def sample_nodes() -> list[Node]:
    """Create sample graph nodes for testing."""
    return [
        Node(
            node_id="node1",
            entity_name="Coverage A: Dwelling",
            entity_type=EntityType.COVERAGE,
            chunk_ids=["chunk1"],
            doc_ids=["doc123"],
            metadata={"limit": "$500,000"},
        ),
        Node(
            node_id="node2",
            entity_name="Water Damage",
            entity_type=EntityType.EXCLUSION,
            chunk_ids=["chunk3"],
            doc_ids=["doc123"],
            metadata={},
        ),
        Node(
            node_id="node3",
            entity_name="California",
            entity_type=EntityType.STATE,
            chunk_ids=["chunk1", "chunk2", "chunk3"],
            doc_ids=["doc123"],
            metadata={},
        ),
    ]


@pytest.fixture
def sample_edges() -> list[Edge]:
    """Create sample graph edges for testing."""
    return [
        Edge(
            edge_id="edge1",
            source_id="node1",
            target_id="node3",
            relation_type=RelationType.APPLIES_TO,
            metadata={},
        ),
        Edge(
            edge_id="edge2",
            source_id="node2",
            target_id="node3",
            relation_type=RelationType.APPLIES_TO,
            metadata={},
        ),
    ]


@pytest.fixture
def sample_citations() -> list[Citation]:
    """Create sample citations for testing."""
    return [
        Citation(
            chunk_id="chunk1",
            doc_id="doc123",
            text="This is a homeowners insurance policy. Coverage A: Dwelling - $500,000.",
            score=0.95,
            metadata={"page_num": 1, "form_number": "HO-3"},
        ),
        Citation(
            chunk_id="chunk3",
            doc_id="doc123",
            text="Section I - Exclusions. We do not cover water damage caused by flood or surface water.",
            score=0.87,
            metadata={"page_num": 2, "form_number": "HO-3"},
        ),
    ]


# === Mock Adapter Fixtures ===

@pytest.fixture
def mock_llm_adapter() -> AsyncMock:
    """Create a mock LLM adapter."""
    mock = AsyncMock()
    mock.generate.return_value = "This is a generated answer with [1] citations."
    mock.embed.return_value = [0.1] * 1536  # Mock embedding vector
    mock.extract_entities.return_value = {
        "nodes": [
            {
                "entity_name": "Coverage A: Dwelling",
                "entity_type": "COVERAGE",
                "metadata": {"limit": "$500,000"},
            }
        ],
        "edges": [],
    }
    mock.count_tokens.return_value = 100
    return mock


@pytest.fixture
def mock_doc_store() -> AsyncMock:
    """Create a mock document store."""
    mock = AsyncMock()
    mock.save_document.return_value = None
    mock.get_document.return_value = None
    mock.list_documents.return_value = []
    mock.save_chunks.return_value = None
    mock.get_chunks.return_value = []
    mock.get_chunk_by_id.return_value = None
    return mock


@pytest.fixture
def mock_vector_store() -> AsyncMock:
    """Create a mock vector store."""
    mock = AsyncMock()
    mock.add_vectors.return_value = None
    mock.search.return_value = [
        {"chunk_id": "chunk1", "score": 0.95},
        {"chunk_id": "chunk2", "score": 0.87},
    ]
    mock.delete_vectors.return_value = None
    return mock


@pytest.fixture
def mock_graph_store() -> AsyncMock:
    """Create a mock graph store."""
    mock = AsyncMock()
    mock.add_nodes.return_value = None
    mock.add_edges.return_value = None
    mock.get_node.return_value = None
    mock.search_by_entity.return_value = GraphResult(
        nodes=[],
        edges=[],
        chunk_ids=[],
        score=0.8,
    )
    mock.traverse.return_value = GraphResult(
        nodes=[],
        edges=[],
        chunk_ids=[],
        score=0.75,
    )
    return mock


# === Configuration Fixtures ===

@pytest.fixture
def sample_chunking_config() -> dict:
    """Sample chunking configuration."""
    return {
        "method": "sentence_aware",
        "chunk_size": 500,
        "chunk_overlap": 50,
        "sentence_min_length": 10,
    }


@pytest.fixture
def sample_retrieval_config() -> dict:
    """Sample retrieval configuration."""
    return {
        "vector_weight": 0.5,
        "document_weight": 0.3,
        "graph_weight": 0.2,
        "vector_top_k": 10,
        "document_top_k": 10,
        "graph_top_k": 5,
        "graph_strategy": "entity_search",
    }


@pytest.fixture
def sample_fusion_config() -> dict:
    """Sample fusion configuration."""
    return {
        "method": "weighted_rrf",
        "rrf_k": 60,
        "dedup_threshold": 0.9,
        "max_results": 20,
    }


@pytest.fixture
def sample_context_config() -> dict:
    """Sample context configuration."""
    return {
        "max_tokens": 3000,
        "citation_format": "numbered",
        "include_metadata": True,
        "redact_pii": True,
    }


@pytest.fixture
def sample_judge_config() -> dict:
    """Sample judge configuration."""
    return {
        "checks": [
            "citation_coverage",
            "groundedness",
            "hallucination",
            "relevance",
            "consistency",
            "toxicity",
            "pii",
            "bias",
            "contradiction",
        ],
        "citation_coverage_threshold": 0.9,
        "groundedness_threshold": 0.8,
        "hallucination_threshold": 0.1,
        "relevance_threshold": 0.7,
        "fail_on_violation": ["hallucination", "toxicity", "pii"],
    }


@pytest.fixture
def openai_api_key() -> str:
    """Get OpenAI API key from environment or return dummy key."""
    return os.getenv("OPENAI_API_KEY", "sk-test-dummy-key")


# === FastAPI Test Client ===

@pytest.fixture
def test_client() -> TestClient:
    """Create a FastAPI test client."""
    from app.main import app
    return TestClient(app)
