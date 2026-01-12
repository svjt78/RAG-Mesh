"""
Graph extraction module
Extracts entities and relationships from text using LLM
"""

import logging
from typing import List, Dict, Any, Optional
import uuid

from app.adapters.base import LLMAdapter
from app.core.models import EntityType, RelationType, GraphExtractionProfile

logger = logging.getLogger(__name__)


class GraphExtractionModule:
    """Handles entity and relationship extraction for graph construction"""

    def __init__(
        self,
        llm_adapter: LLMAdapter,
        profile: Optional[GraphExtractionProfile] = None
    ):
        """
        Initialize graph extraction module

        Args:
            llm_adapter: LLM adapter for entity extraction
            profile: Graph extraction profile with entity and relationship types
        """
        self.llm = llm_adapter

        # Use profile if provided, otherwise use default generic types
        if profile:
            self.entity_types = profile.entity_types
            self.relationship_types = profile.relationship_types
        else:
            self.entity_types = self._default_entity_types()
            self.relationship_types = self._default_relationship_types()

    @staticmethod
    def _default_entity_types() -> List[str]:
        """Return default generic entity types"""
        return [
            "Person", "Organization", "Location", "Date", "Event",
            "Concept", "Product", "Document", "Term", "Metric"
        ]

    @staticmethod
    def _default_relationship_types() -> List[str]:
        """Return default generic relationship types"""
        return [
            "RELATES_TO", "PART_OF", "LOCATED_IN", "OCCURS_AT", "CREATED_BY",
            "REFERENCES", "DEFINES", "SUPPORTS", "CONTRADICTS", "PRECEDES"
        ]

    async def extract_from_chunks(
        self,
        chunks: List[Dict[str, Any]],
        batch_size: int = 5
    ) -> Dict[str, Any]:
        """
        Extract entities and relationships from chunks

        Args:
            chunks: List of chunk dictionaries
            batch_size: Number of chunks to process together

        Returns:
            Dictionary with nodes and edges
        """
        logger.info(f"Extracting entities from {len(chunks)} chunks")

        all_entities = []
        all_relationships = []
        total_cost = 0.0
        total_tokens = 0

        # Process chunks in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            # Combine chunk texts
            combined_text = "\n\n".join([
                f"[Chunk {j+1} - Page {chunk.get('page_no', 'N/A')}]: {chunk.get('text', '')}"
                for j, chunk in enumerate(batch)
            ])

            try:
                # Extract entities and relationships
                result = await self.llm.extract_entities(
                    text=combined_text,
                    entity_types=self.entity_types
                )

                # Process extracted entities
                for entity in result.get("entities", []):
                    # Map chunk IDs to entities
                    entity_chunk_ids = [chunk["chunk_id"] for chunk in batch]

                    # Create entity node
                    node = {
                        "node_id": entity.get("id") or self._generate_entity_id(entity["label"]),
                        "label": entity["label"],
                        "node_type": entity.get("type", "Other"),
                        "properties": entity.get("properties", {}),
                        "chunk_ids": entity_chunk_ids
                    }
                    all_entities.append(node)

                # Process extracted relationships
                for relationship in result.get("relationships", []):
                    edge = {
                        "source": relationship["source"],
                        "target": relationship["target"],
                        "edge_type": relationship.get("type", "OTHER"),
                        "properties": relationship.get("properties", {}),
                        "evidence_chunk_ids": [chunk["chunk_id"] for chunk in batch]
                    }
                    all_relationships.append(edge)

                # Track cost and tokens
                total_cost += result.get("cost", 0.0)
                total_tokens += result.get("tokens_used", 0)

            except Exception as e:
                logger.error(f"Error extracting from batch {i//batch_size + 1}: {e}")
                continue

        # Deduplicate entities
        unique_entities = self._deduplicate_entities(all_entities)

        logger.info(
            f"Extracted {len(unique_entities)} entities and {len(all_relationships)} relationships"
        )
        logger.info(f"Total cost: ${total_cost:.4f}, Total tokens: {total_tokens}")

        return {
            "nodes": unique_entities,
            "edges": all_relationships,
            "metadata": {
                "total_entities": len(unique_entities),
                "total_relationships": len(all_relationships),
                "cost": total_cost,
                "tokens_used": total_tokens
            }
        }

    async def extract_from_text(
        self,
        text: str,
        chunk_id: str
    ) -> Dict[str, Any]:
        """
        Extract entities and relationships from a single text

        Args:
            text: Text to analyze
            chunk_id: Chunk identifier for provenance

        Returns:
            Dictionary with nodes and edges
        """
        try:
            result = await self.llm.extract_entities(
                text=text,
                entity_types=self.entity_types
            )

            # Process entities
            nodes = []
            for entity in result.get("entities", []):
                node = {
                    "node_id": entity.get("id") or self._generate_entity_id(entity["label"]),
                    "label": entity["label"],
                    "node_type": entity.get("type", "Other"),
                    "properties": entity.get("properties", {}),
                    "chunk_ids": [chunk_id]
                }
                nodes.append(node)

            # Process relationships
            edges = []
            for relationship in result.get("relationships", []):
                edge = {
                    "source": relationship["source"],
                    "target": relationship["target"],
                    "edge_type": relationship.get("type", "OTHER"),
                    "properties": relationship.get("properties", {}),
                    "evidence_chunk_ids": [chunk_id]
                }
                edges.append(edge)

            return {
                "nodes": nodes,
                "edges": edges,
                "metadata": {
                    "cost": result.get("cost", 0.0),
                    "tokens_used": result.get("tokens_used", 0)
                }
            }

        except Exception as e:
            logger.error(f"Error extracting from text: {e}")
            return {"nodes": [], "edges": [], "metadata": {}}

    def _generate_entity_id(self, label: str) -> str:
        """
        Generate a unique entity ID from label

        Args:
            label: Entity label

        Returns:
            Unique entity ID
        """
        # Create ID from label (normalized) + short UUID
        normalized_label = label.lower().replace(" ", "_")
        short_uuid = uuid.uuid4().hex[:8]
        return f"{normalized_label}_{short_uuid}"

    def _deduplicate_entities(
        self,
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate entities by label (case-insensitive)

        Args:
            entities: List of entity dictionaries

        Returns:
            Deduplicated list
        """
        seen = {}
        unique_entities = []

        for entity in entities:
            label_lower = entity["label"].lower()

            if label_lower in seen:
                # Merge chunk_ids from duplicate
                existing = seen[label_lower]
                existing["chunk_ids"].extend(entity["chunk_ids"])
                existing["chunk_ids"] = list(set(existing["chunk_ids"]))
            else:
                seen[label_lower] = entity
                unique_entities.append(entity)

        return unique_entities

    def validate_entity_type(self, entity_type: str) -> bool:
        """
        Validate entity type

        Args:
            entity_type: Entity type string

        Returns:
            True if valid
        """
        try:
            EntityType(entity_type)
            return True
        except ValueError:
            return False

    def validate_relationship_type(self, rel_type: str) -> bool:
        """
        Validate relationship type

        Args:
            rel_type: Relationship type string

        Returns:
            True if valid
        """
        try:
            RelationType(rel_type)
            return True
        except ValueError:
            return False
