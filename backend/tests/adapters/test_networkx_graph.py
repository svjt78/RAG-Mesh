"""
Unit tests for NetworkXGraph adapter
"""

import os

import pytest

from app.adapters.networkx_graph import NetworkXGraph
from app.core.models import (
    Edge,
    EntityType,
    GraphResult,
    Node,
    RelationType,
)


@pytest.mark.unit
class TestNetworkXGraph:
    """Test cases for NetworkXGraph adapter."""

    @pytest.fixture
    def graph_store(self, test_data_dir: str) -> NetworkXGraph:
        """Create a NetworkXGraph instance for testing."""
        return NetworkXGraph(data_dir=test_data_dir)

    @pytest.mark.asyncio
    async def test_add_and_get_node(
        self, graph_store: NetworkXGraph, sample_nodes: list[Node]
    ):
        """Test adding and retrieving nodes."""
        # Add nodes
        await graph_store.add_nodes(sample_nodes)

        # Retrieve a node
        node = await graph_store.get_node(sample_nodes[0].node_id)
        assert node is not None
        assert node.node_id == sample_nodes[0].node_id
        assert node.entity_name == sample_nodes[0].entity_name
        assert node.entity_type == sample_nodes[0].entity_type

    @pytest.mark.asyncio
    async def test_get_nonexistent_node(self, graph_store: NetworkXGraph):
        """Test retrieving a node that doesn't exist."""
        node = await graph_store.get_node("nonexistent")
        assert node is None

    @pytest.mark.asyncio
    async def test_add_edges(
        self,
        graph_store: NetworkXGraph,
        sample_nodes: list[Node],
        sample_edges: list[Edge],
    ):
        """Test adding edges between nodes."""
        # Add nodes first
        await graph_store.add_nodes(sample_nodes)

        # Add edges
        await graph_store.add_edges(sample_edges)

        # Verify edges exist in graph
        assert graph_store.graph.number_of_edges() == len(sample_edges)

        # Verify edge data
        edge_data = graph_store.graph.get_edge_data(
            sample_edges[0].source_id, sample_edges[0].target_id
        )
        assert edge_data is not None
        assert edge_data["relation_type"] == sample_edges[0].relation_type.value

    @pytest.mark.asyncio
    async def test_search_by_entity(
        self, graph_store: NetworkXGraph, sample_nodes: list[Node]
    ):
        """Test searching for entities by name."""
        await graph_store.add_nodes(sample_nodes)

        # Search for exact match
        result = await graph_store.search_by_entity(
            entity_name="Water Damage", top_k=1
        )
        assert isinstance(result, GraphResult)
        assert len(result.nodes) > 0
        assert result.nodes[0].entity_name == "Water Damage"

    @pytest.mark.asyncio
    async def test_search_by_entity_partial_match(
        self, graph_store: NetworkXGraph, sample_nodes: list[Node]
    ):
        """Test searching with partial entity name."""
        await graph_store.add_nodes(sample_nodes)

        # Search with partial name
        result = await graph_store.search_by_entity(
            entity_name="Coverage", top_k=5
        )
        assert len(result.nodes) > 0
        assert any("Coverage" in node.entity_name for node in result.nodes)

    @pytest.mark.asyncio
    async def test_search_by_entity_type(
        self, graph_store: NetworkXGraph, sample_nodes: list[Node]
    ):
        """Test searching by entity type."""
        await graph_store.add_nodes(sample_nodes)

        # Search for all COVERAGE entities
        result = await graph_store.search_by_entity(
            entity_name="Coverage", entity_type=EntityType.COVERAGE, top_k=5
        )
        assert all(
            node.entity_type == EntityType.COVERAGE for node in result.nodes
        )

    @pytest.mark.asyncio
    async def test_traverse_from_node(
        self,
        graph_store: NetworkXGraph,
        sample_nodes: list[Node],
        sample_edges: list[Edge],
    ):
        """Test graph traversal from a starting node."""
        await graph_store.add_nodes(sample_nodes)
        await graph_store.add_edges(sample_edges)

        # Traverse from Coverage A node
        result = await graph_store.traverse(
            start_node_ids=["node1"], max_depth=1, max_nodes=10
        )

        assert isinstance(result, GraphResult)
        assert len(result.nodes) > 0
        assert len(result.edges) > 0
        # Should include the California node (connected via edge)
        assert any(node.entity_name == "California" for node in result.nodes)

    @pytest.mark.asyncio
    async def test_traverse_max_depth(
        self,
        graph_store: NetworkXGraph,
        sample_nodes: list[Node],
        sample_edges: list[Edge],
    ):
        """Test that traversal respects max_depth parameter."""
        await graph_store.add_nodes(sample_nodes)
        await graph_store.add_edges(sample_edges)

        # Traverse with depth 0 (only start node)
        result = await graph_store.traverse(
            start_node_ids=["node1"], max_depth=0, max_nodes=10
        )
        assert len(result.nodes) == 1
        assert result.nodes[0].node_id == "node1"

    @pytest.mark.asyncio
    async def test_save_and_load_graph(
        self,
        graph_store: NetworkXGraph,
        sample_nodes: list[Node],
        sample_edges: list[Edge],
    ):
        """Test persisting and loading the graph."""
        # Add data and save
        await graph_store.add_nodes(sample_nodes)
        await graph_store.add_edges(sample_edges)
        await graph_store.save_graph()

        # Verify file was created
        graph_path = os.path.join(graph_store.graph_dir, "graph.json")
        assert os.path.exists(graph_path)

        # Create new instance and load
        new_store = NetworkXGraph(
            data_dir=graph_store.graph_dir.replace("/graph", "")
        )
        await new_store.load_graph()

        # Verify loaded graph has same data
        assert new_store.graph.number_of_nodes() == len(sample_nodes)
        assert new_store.graph.number_of_edges() == len(sample_edges)

    @pytest.mark.asyncio
    async def test_delete_graph_data(
        self,
        graph_store: NetworkXGraph,
        sample_nodes: list[Node],
        sample_edges: list[Edge],
    ):
        """Test clearing graph data."""
        # Add data
        await graph_store.add_nodes(sample_nodes)
        await graph_store.add_edges(sample_edges)
        assert graph_store.graph.number_of_nodes() > 0

        # Clear graph
        await graph_store.delete_graph_data(doc_id="doc123")

        # Graph should be empty
        assert graph_store.graph.number_of_nodes() == 0
        assert graph_store.graph.number_of_edges() == 0

    @pytest.mark.asyncio
    async def test_chunk_id_collection(
        self,
        graph_store: NetworkXGraph,
        sample_nodes: list[Node],
        sample_edges: list[Edge],
    ):
        """Test that search results include chunk IDs from traversed nodes."""
        await graph_store.add_nodes(sample_nodes)
        await graph_store.add_edges(sample_edges)

        # Search for an entity
        result = await graph_store.search_by_entity(
            entity_name="Coverage A", top_k=1
        )

        # Should include chunk IDs from the node
        assert len(result.chunk_ids) > 0
        assert "chunk1" in result.chunk_ids

    @pytest.mark.asyncio
    async def test_add_duplicate_nodes(
        self, graph_store: NetworkXGraph, sample_nodes: list[Node]
    ):
        """Test adding nodes with duplicate IDs."""
        await graph_store.add_nodes(sample_nodes)
        initial_count = graph_store.graph.number_of_nodes()

        # Add same nodes again (should update, not duplicate)
        await graph_store.add_nodes(sample_nodes)
        assert graph_store.graph.number_of_nodes() == initial_count

    @pytest.mark.asyncio
    async def test_add_edges_without_nodes(
        self, graph_store: NetworkXGraph, sample_edges: list[Edge]
    ):
        """Test adding edges when nodes don't exist."""
        # This should not raise an error, but edges won't be added
        # NetworkX allows adding edges even if nodes don't exist (it creates them)
        await graph_store.add_edges(sample_edges)

        # Edges should be created (NetworkX auto-creates nodes)
        assert graph_store.graph.number_of_edges() == len(sample_edges)

    @pytest.mark.asyncio
    async def test_search_empty_graph(self, graph_store: NetworkXGraph):
        """Test searching an empty graph."""
        result = await graph_store.search_by_entity(
            entity_name="Coverage", top_k=5
        )
        assert len(result.nodes) == 0
        assert len(result.chunk_ids) == 0

    @pytest.mark.asyncio
    async def test_traverse_from_nonexistent_node(
        self, graph_store: NetworkXGraph, sample_nodes: list[Node]
    ):
        """Test traversing from a node that doesn't exist."""
        await graph_store.add_nodes(sample_nodes)

        result = await graph_store.traverse(
            start_node_ids=["nonexistent"], max_depth=1, max_nodes=10
        )
        # Should return empty result
        assert len(result.nodes) == 0

    @pytest.mark.asyncio
    async def test_complex_graph_structure(self, graph_store: NetworkXGraph):
        """Test building and querying a complex graph."""
        # Create a more complex graph structure
        nodes = [
            Node(
                node_id=f"node{i}",
                entity_name=f"Entity {i}",
                entity_type=EntityType.COVERAGE if i % 2 == 0 else EntityType.EXCLUSION,
                chunk_ids=[f"chunk{i}"],
                doc_ids=["doc123"],
                metadata={},
            )
            for i in range(10)
        ]

        edges = [
            Edge(
                edge_id=f"edge{i}",
                source_id=f"node{i}",
                target_id=f"node{i+1}",
                relation_type=RelationType.RELATED_TO,
                metadata={},
            )
            for i in range(9)
        ]

        await graph_store.add_nodes(nodes)
        await graph_store.add_edges(edges)

        # Verify graph structure
        assert graph_store.graph.number_of_nodes() == 10
        assert graph_store.graph.number_of_edges() == 9

        # Traverse from start
        result = await graph_store.traverse(
            start_node_ids=["node0"], max_depth=3, max_nodes=5
        )
        # Should find multiple nodes within 3 hops
        assert len(result.nodes) <= 5
        assert len(result.nodes) > 1

    @pytest.mark.asyncio
    async def test_metadata_preservation(
        self, graph_store: NetworkXGraph, sample_nodes: list[Node]
    ):
        """Test that node metadata is preserved."""
        # Add metadata to nodes
        sample_nodes[0].metadata["custom_field"] = "test_value"
        await graph_store.add_nodes(sample_nodes)

        # Retrieve and verify
        node = await graph_store.get_node(sample_nodes[0].node_id)
        assert node is not None
        assert node.metadata.get("custom_field") == "test_value"

    @pytest.mark.asyncio
    async def test_top_k_limit_in_search(
        self, graph_store: NetworkXGraph
    ):
        """Test that search respects top_k parameter."""
        # Create many similar nodes
        nodes = [
            Node(
                node_id=f"coverage_{i}",
                entity_name=f"Coverage Type {i}",
                entity_type=EntityType.COVERAGE,
                chunk_ids=[f"chunk{i}"],
                doc_ids=["doc123"],
                metadata={},
            )
            for i in range(20)
        ]
        await graph_store.add_nodes(nodes)

        # Search with small top_k
        result = await graph_store.search_by_entity(
            entity_name="Coverage", top_k=5
        )
        assert len(result.nodes) <= 5
