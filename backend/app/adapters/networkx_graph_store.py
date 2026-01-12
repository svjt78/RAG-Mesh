"""
NetworkX-based graph store adapter
Implements graph storage and traversal using NetworkX
"""

import networkx as nx
import json
import aiofiles
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from collections import deque
import logging

from app.adapters.base import GraphStoreAdapter

logger = logging.getLogger(__name__)


class NetworkXGraphStoreAdapter(GraphStoreAdapter):
    """NetworkX-based implementation of graph storage"""

    def __init__(self, data_dir: Path = Path("data/graph")):
        """
        Initialize NetworkX graph store

        Args:
            data_dir: Directory for graph storage
        """
        self.data_dir = data_dir
        self.nodes_path = data_dir / "nodes.jsonl"
        self.edges_path = data_dir / "edges.jsonl"

        # Create directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize MultiDiGraph for typed edges
        self.graph = nx.MultiDiGraph()

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

        # Load existing graph if available
        asyncio.create_task(self._initialize())

    async def _initialize(self) -> None:
        """Initialize or load existing graph"""
        if self.nodes_path.exists() and self.edges_path.exists():
            await self.load_graph(self.data_dir)
        else:
            logger.info("Created new NetworkX graph")

    async def add_nodes(self, nodes: List[Dict[str, Any]]) -> None:
        """
        Add nodes to the graph

        Args:
            nodes: List of node data with id, type, label, properties, chunk_ids
        """
        async with self._lock:
            for node in nodes:
                node_id = node["node_id"]
                self.graph.add_node(
                    node_id,
                    label=node.get("label", ""),
                    node_type=node.get("node_type", ""),
                    properties=node.get("properties", {}),
                    chunk_ids=node.get("chunk_ids", [])
                )

            logger.info(f"Added {len(nodes)} nodes to graph (total: {self.graph.number_of_nodes()})")

    async def add_edges(self, edges: List[Dict[str, Any]]) -> None:
        """
        Add edges to the graph

        Args:
            edges: List of edge data with source, target, type, properties, evidence_chunk_ids
        """
        async with self._lock:
            for edge in edges:
                self.graph.add_edge(
                    edge["source"],
                    edge["target"],
                    edge_type=edge.get("edge_type", ""),
                    properties=edge.get("properties", {}),
                    evidence_chunk_ids=edge.get("evidence_chunk_ids", [])
                )

            logger.info(f"Added {len(edges)} edges to graph (total: {self.graph.number_of_edges()})")

    async def query_subgraph(
        self,
        entity_ids: List[str],
        max_hops: int = 2
    ) -> Dict[str, Any]:
        """
        Extract a subgraph around entities using BFS

        Args:
            entity_ids: List of entity IDs to start from
            max_hops: Maximum number of hops from seed entities

        Returns:
            Subgraph with nodes and edges
        """
        async with self._lock:
            # BFS to find all nodes within max_hops
            visited_nodes: Set[str] = set()
            queue = deque()

            # Initialize with seed entities
            for entity_id in entity_ids:
                if entity_id in self.graph:
                    queue.append((entity_id, 0))
                    visited_nodes.add(entity_id)

            # BFS traversal
            while queue:
                node_id, depth = queue.popleft()

                if depth >= max_hops:
                    continue

                # Explore neighbors (both incoming and outgoing edges)
                for neighbor in self.graph.successors(node_id):
                    if neighbor not in visited_nodes:
                        visited_nodes.add(neighbor)
                        queue.append((neighbor, depth + 1))

                for neighbor in self.graph.predecessors(node_id):
                    if neighbor not in visited_nodes:
                        visited_nodes.add(neighbor)
                        queue.append((neighbor, depth + 1))

            # Extract subgraph
            subgraph = self.graph.subgraph(visited_nodes)

            # Build node list
            nodes = []
            for node_id in subgraph.nodes():
                node_data = subgraph.nodes[node_id]
                nodes.append({
                    "node_id": node_id,
                    "label": node_data.get("label", ""),
                    "node_type": node_data.get("node_type", ""),
                    "properties": node_data.get("properties", {}),
                    "chunk_ids": node_data.get("chunk_ids", [])
                })

            # Build edge list
            edges = []
            for source, target, key, edge_data in subgraph.edges(keys=True, data=True):
                edges.append({
                    "source": source,
                    "target": target,
                    "edge_type": edge_data.get("edge_type", ""),
                    "properties": edge_data.get("properties", {}),
                    "evidence_chunk_ids": edge_data.get("evidence_chunk_ids", [])
                })

            logger.info(f"Extracted subgraph with {len(nodes)} nodes and {len(edges)} edges")

            return {
                "nodes": nodes,
                "edges": edges,
                "metadata": {
                    "seed_entities": entity_ids,
                    "max_hops": max_hops,
                    "total_nodes": len(nodes),
                    "total_edges": len(edges)
                }
            }

    async def get_supporting_chunks(self, entity_ids: List[str]) -> List[str]:
        """
        Get chunk IDs that support entities

        Args:
            entity_ids: List of entity IDs

        Returns:
            List of unique chunk IDs
        """
        async with self._lock:
            chunk_ids: Set[str] = set()

            for entity_id in entity_ids:
                if entity_id not in self.graph:
                    continue

                # Get chunks from node
                node_data = self.graph.nodes[entity_id]
                node_chunks = node_data.get("chunk_ids", [])
                chunk_ids.update(node_chunks)

                # Get chunks from outgoing edges
                for _, _, edge_data in self.graph.out_edges(entity_id, data=True):
                    edge_chunks = edge_data.get("evidence_chunk_ids", [])
                    chunk_ids.update(edge_chunks)

                # Get chunks from incoming edges
                for _, _, edge_data in self.graph.in_edges(entity_id, data=True):
                    edge_chunks = edge_data.get("evidence_chunk_ids", [])
                    chunk_ids.update(edge_chunks)

            logger.info(f"Found {len(chunk_ids)} supporting chunks for {len(entity_ids)} entities")
            return list(chunk_ids)

    async def find_entities(
        self,
        labels: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find entities by labels or types

        Args:
            labels: Optional list of entity labels (partial match)
            entity_types: Optional list of entity types

        Returns:
            List of matching entities
        """
        async with self._lock:
            matching_entities = []

            for node_id, node_data in self.graph.nodes(data=True):
                match = True

                # Filter by labels (case-insensitive partial match)
                if labels:
                    node_label = node_data.get("label", "").lower()
                    label_match = any(label.lower() in node_label for label in labels)
                    if not label_match:
                        match = False

                # Filter by entity types
                if entity_types:
                    node_type = node_data.get("node_type", "")
                    if node_type not in entity_types:
                        match = False

                if match:
                    matching_entities.append({
                        "node_id": node_id,
                        "label": node_data.get("label", ""),
                        "node_type": node_data.get("node_type", ""),
                        "properties": node_data.get("properties", {}),
                        "chunk_ids": node_data.get("chunk_ids", [])
                    })

            logger.info(f"Found {len(matching_entities)} matching entities")
            return matching_entities

    async def save_graph(self, path: Path) -> None:
        """
        Persist the graph to disk

        Args:
            path: Path to save the graph
        """
        async with self._lock:
            # Save nodes as JSONL
            nodes_file = path / "nodes.jsonl"
            async with aiofiles.open(nodes_file, 'w') as f:
                for node_id, node_data in self.graph.nodes(data=True):
                    node_entry = {
                        "node_id": node_id,
                        "label": node_data.get("label", ""),
                        "node_type": node_data.get("node_type", ""),
                        "properties": node_data.get("properties", {}),
                        "chunk_ids": node_data.get("chunk_ids", [])
                    }
                    await f.write(json.dumps(node_entry) + '\n')

            # Save edges as JSONL
            edges_file = path / "edges.jsonl"
            async with aiofiles.open(edges_file, 'w') as f:
                for source, target, key, edge_data in self.graph.edges(keys=True, data=True):
                    edge_entry = {
                        "source": source,
                        "target": target,
                        "edge_type": edge_data.get("edge_type", ""),
                        "properties": edge_data.get("properties", {}),
                        "evidence_chunk_ids": edge_data.get("evidence_chunk_ids", [])
                    }
                    await f.write(json.dumps(edge_entry) + '\n')

            logger.info(f"Saved graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")

    async def load_graph(self, path: Path) -> None:
        """
        Load the graph from disk

        Args:
            path: Path to load the graph from
        """
        async with self._lock:
            # Clear existing graph
            self.graph.clear()

            nodes_file = path / "nodes.jsonl"
            edges_file = path / "edges.jsonl"

            # Load nodes
            if nodes_file.exists():
                async with aiofiles.open(nodes_file, 'r') as f:
                    async for line in f:
                        if line.strip():
                            node = json.loads(line)
                            node_id = node["node_id"]
                            self.graph.add_node(
                                node_id,
                                label=node.get("label", ""),
                                node_type=node.get("node_type", ""),
                                properties=node.get("properties", {}),
                                chunk_ids=node.get("chunk_ids", [])
                            )

            # Load edges
            if edges_file.exists():
                async with aiofiles.open(edges_file, 'r') as f:
                    async for line in f:
                        if line.strip():
                            edge = json.loads(line)
                            self.graph.add_edge(
                                edge["source"],
                                edge["target"],
                                edge_type=edge.get("edge_type", ""),
                                properties=edge.get("properties", {}),
                                evidence_chunk_ids=edge.get("evidence_chunk_ids", [])
                            )

            logger.info(f"Loaded graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get graph statistics

        Returns:
            Statistics dictionary
        """
        async with self._lock:
            # Count nodes by type
            node_types: Dict[str, int] = {}
            for _, node_data in self.graph.nodes(data=True):
                node_type = node_data.get("node_type", "unknown")
                node_types[node_type] = node_types.get(node_type, 0) + 1

            # Count edges by type
            edge_types: Dict[str, int] = {}
            for _, _, edge_data in self.graph.edges(data=True):
                edge_type = edge_data.get("edge_type", "unknown")
                edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

            return {
                "total_nodes": self.graph.number_of_nodes(),
                "total_edges": self.graph.number_of_edges(),
                "node_types": node_types,
                "edge_types": edge_types,
                "is_connected": nx.is_weakly_connected(self.graph) if self.graph.number_of_nodes() > 0 else False
            }

    async def clear_graph(self) -> None:
        """Clear the entire graph"""
        async with self._lock:
            self.graph.clear()
            logger.info("Cleared graph")
