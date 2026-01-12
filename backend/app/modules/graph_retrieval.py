"""
Graph retrieval module
Entity-based retrieval using knowledge graph
"""

import logging
from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher

from app.adapters.base import GraphStoreAdapter, LLMAdapter
from app.core.models import GraphResult, RetrievalProfile, Subgraph, RelationType

logger = logging.getLogger(__name__)


class GraphRetrievalModule:
    """Handles graph-based retrieval"""

    def __init__(
        self,
        graph_store: GraphStoreAdapter,
        llm_adapter: LLMAdapter
    ):
        """
        Initialize graph retrieval module

        Args:
            graph_store: Graph store adapter
            llm_adapter: LLM adapter for entity linking
        """
        self.graph_store = graph_store
        self.llm = llm_adapter

    @staticmethod
    def _normalize_edge_type(edge_type: str) -> str:
        """
        Normalize edge type to valid RelationType

        Args:
            edge_type: Raw edge type from graph

        Returns:
            Valid RelationType value
        """
        # Map common variations to valid RelationType values
        edge_type_upper = edge_type.upper().replace(" ", "_")

        mapping = {
            "APPLIES_IN": "APPLIES_IN",
            "AMENDS": "AMENDS",
            "EXCLUDES": "EXCLUDES",
            "SUBJECT_TO": "SUBJECT_TO",
            "REFERENCES": "REFERENCES",
            "DEFINES": "DEFINES",
            "IS_DEFINED_IN": "DEFINES",
            "ORIGINATING_STATE": "APPLIES_IN",
            "RECIPIENT_STATE": "APPLIES_IN",
            "HASFORM": "REFERENCES",
            "LOCATEDIN": "APPLIES_IN",
            "BELONGSTOSTATE": "APPLIES_IN",
        }

        normalized = mapping.get(edge_type_upper, "OTHER")
        return normalized

    async def retrieve(
        self,
        query: str,
        profile: RetrievalProfile
    ) -> tuple[List[GraphResult], Optional[Subgraph]]:
        """
        Retrieve chunks using graph relationships

        Args:
            query: Search query
            profile: Retrieval profile

        Returns:
            Tuple of (GraphResult list, Subgraph)
        """
        logger.info(f"Graph retrieval for query: '{query[:50]}...'")

        try:
            # Step 1: Link query to entities
            entity_ids = await self._link_entities(query, profile)

            if not entity_ids:
                logger.warning("No entities found for query")
                return [], None

            logger.info(f"Found {len(entity_ids)} entities: {entity_ids}")

            # Step 2: Extract subgraph
            subgraph_data = await self.graph_store.query_subgraph(
                entity_ids=entity_ids,
                max_hops=profile.graph_max_hops
            )

            # Convert to Subgraph model
            from app.core.models import Node, Edge
            nodes = [Node(**node) for node in subgraph_data.get("nodes", [])]

            # Normalize edge types before creating Edge objects
            edges = []
            for edge_data in subgraph_data.get("edges", []):
                normalized_edge = edge_data.copy()
                normalized_edge["edge_type"] = self._normalize_edge_type(edge_data.get("edge_type", "OTHER"))
                edges.append(Edge(**normalized_edge))

            subgraph = Subgraph(
                nodes=nodes,
                edges=edges,
                metadata=subgraph_data.get("metadata", {})
            )

            # Step 3: Get supporting chunks
            chunk_ids = await self.graph_store.get_supporting_chunks(entity_ids)

            # Step 4: Score and rank chunks
            results = await self._score_chunks(
                chunk_ids=chunk_ids,
                entity_ids=entity_ids,
                subgraph_data=subgraph_data
            )

            logger.info(f"Graph retrieval returned {len(results)} results")
            return results, subgraph

        except Exception as e:
            logger.error(f"Error in graph retrieval: {e}")
            return [], None

    async def _link_entities(
        self,
        query: str,
        profile: RetrievalProfile
    ) -> List[str]:
        """
        Link query to graph entities

        Args:
            query: Search query
            profile: Retrieval profile

        Returns:
            List of entity IDs
        """
        # Step 1: Get all entities from graph
        all_entities = await self.graph_store.find_entities(
            entity_types=profile.graph_entity_types if profile.graph_entity_types else None
        )

        if not all_entities:
            return []

        # Step 2: LLM-based entity extraction from query
        try:
            llm_result = await self.llm.extract_entities(
                text=query,
                entity_types=profile.graph_entity_types if profile.graph_entity_types else []
            )
            query_entities = [e.get("label", "").lower() for e in llm_result.get("entities", [])]
        except Exception as e:
            logger.warning(f"LLM entity extraction failed: {e}")
            query_entities = []

        # Step 3: Fuzzy matching with graph entities
        entity_ids = []
        query_lower = query.lower()

        for graph_entity in all_entities:
            entity_label = graph_entity.get("label", "").lower()
            entity_id = graph_entity.get("node_id", "")

            # Exact match
            if entity_label in query_lower:
                entity_ids.append(entity_id)
                continue

            # Check against extracted entities
            for query_entity in query_entities:
                similarity = self._fuzzy_match(query_entity, entity_label)
                if similarity > 0.8:  # High similarity threshold
                    entity_ids.append(entity_id)
                    break

        # Limit number of entities
        if entity_ids:
            return entity_ids[:10]  # Avoid graph explosion

        # Fallback: use any entities of the allowed types
        if profile.graph_entity_types:
            fallback_entities = await self.graph_store.find_entities(
                entity_types=profile.graph_entity_types
            )
            fallback_ids = [entity.get("node_id", "") for entity in fallback_entities if entity.get("node_id")]
            if fallback_ids:
                logger.info("No entity label matches; falling back to entity types")
                return fallback_ids[:10]

        return []

    def _fuzzy_match(self, str1: str, str2: str) -> float:
        """
        Calculate fuzzy string similarity

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score (0-1)
        """
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    async def _score_chunks(
        self,
        chunk_ids: List[str],
        entity_ids: List[str],
        subgraph_data: Dict[str, Any]
    ) -> List[GraphResult]:
        """
        Score and rank chunks based on graph relevance

        Args:
            chunk_ids: List of chunk IDs
            entity_ids: Seed entity IDs
            subgraph_data: Subgraph data

        Returns:
            List of GraphResult objects
        """
        results = []

        # Count entity mentions per chunk
        chunk_entity_counts: Dict[str, int] = {}
        for node in subgraph_data.get("nodes", []):
            for chunk_id in node.get("chunk_ids", []):
                chunk_entity_counts[chunk_id] = chunk_entity_counts.get(chunk_id, 0) + 1

        # Also count edge evidence
        for edge in subgraph_data.get("edges", []):
            for chunk_id in edge.get("evidence_chunk_ids", []):
                chunk_entity_counts[chunk_id] = chunk_entity_counts.get(chunk_id, 0) + 1

        # Score chunks
        max_count = max(chunk_entity_counts.values()) if chunk_entity_counts else 1

        for rank, chunk_id in enumerate(chunk_ids, start=1):
            # Score based on entity mentions
            entity_count = chunk_entity_counts.get(chunk_id, 0)
            score = entity_count / max_count if max_count > 0 else 0.0

            # Boost if chunk supports seed entities
            supporting_entities = []
            for node in subgraph_data.get("nodes", []):
                if chunk_id in node.get("chunk_ids", []):
                    if node.get("node_id") in entity_ids:
                        score *= 1.5  # Boost for seed entities
                    supporting_entities.append(node.get("node_id"))

            result = GraphResult(
                chunk_id=chunk_id,
                score=min(score, 1.0),  # Cap at 1.0
                rank=rank,
                entity_ids=supporting_entities,
                metadata={}
            )
            results.append(result)

        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)

        # Rerank
        for rank, result in enumerate(results, start=1):
            result.rank = rank

        return results
