"""
Document Management API routes
Handles document listing, retrieval, and deletion
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any, List
import logging

from app.adapters.file_doc_store import FileDocStoreAdapter
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize doc store
data_dir = Path("data")
doc_store = FileDocStoreAdapter(data_dir)


@router.get("/docs")
async def list_documents(
    limit: int = 50,
    offset: int = 0,
    doc_type: Optional[str] = None,
    state: Optional[str] = None,
    form_number: Optional[str] = None
):
    """
    List documents with optional filtering

    Args:
        limit: Maximum number of documents to return
        offset: Number of documents to skip
        doc_type: Filter by document type
        state: Filter by state
        form_number: Filter by form number

    Returns:
        List of documents with metadata
    """
    logger.info(f"Listing documents: limit={limit}, offset={offset}")

    try:
        # Build metadata filter
        metadata_filter = {}
        if doc_type:
            metadata_filter["doc_type"] = doc_type
        if state:
            metadata_filter["state"] = state
        if form_number:
            metadata_filter["form_number"] = form_number

        # List documents
        documents = await doc_store.list_documents(metadata_filter or None)

        # Apply pagination
        paginated_docs = documents[offset:offset + limit]

        # Return summary (not full content)
        doc_summaries = []
        for doc in paginated_docs:
            pages_value = doc.get("pages", [])
            pages = pages_value if isinstance(pages_value, int) else len(pages_value)
            doc_summaries.append(
                {
                    "doc_id": doc["doc_id"],
                    "filename": doc["filename"],
                    "doc_type": doc.get("doc_type"),
                    "form_number": doc.get("form_number"),
                    "state": doc.get("state"),
                    "effective_date": doc.get("effective_date"),
                    "pages": pages,
                    "ingested_at": doc.get("ingested_at"),
                    "indexed_at": doc.get("indexed_at")
                }
            )

        return {
            "documents": doc_summaries,
            "total": len(documents),
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/docs/{doc_id}")
async def get_document(doc_id: str):
    """
    Get a specific document with full content

    Args:
        doc_id: Document ID

    Returns:
        Complete document with all pages
    """
    logger.info(f"Getting document: {doc_id}")

    try:
        document = await doc_store.get_document(doc_id)

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return {"document": document}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/docs/{doc_id}/chunks")
async def get_document_chunks(
    doc_id: str,
    page_number: Optional[int] = None
):
    """
    Get chunks for a document

    Args:
        doc_id: Document ID
        page_number: Filter by page number (optional)

    Returns:
        List of chunks
    """
    logger.info(f"Getting chunks for document: {doc_id}")

    try:
        # Build filter
        metadata_filter = {"doc_id": doc_id}
        if page_number is not None:
            metadata_filter["page_number"] = page_number

        # Get chunks
        chunks = await doc_store.get_chunks(metadata_filter)

        return {
            "doc_id": doc_id,
            "chunks": chunks,
            "total": len(chunks)
        }

    except Exception as e:
        logger.error(f"Error getting chunks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/docs/{doc_id}")
async def delete_document(doc_id: str):
    """
    Delete a document and its chunks

    Args:
        doc_id: Document ID to delete

    Returns:
        Deletion confirmation
    """
    logger.info(f"Deleting document: {doc_id}")

    try:
        # Check if document exists
        document = await doc_store.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete document
        await doc_store.delete_document(doc_id)

        return {
            "status": "deleted",
            "doc_id": doc_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/docs/{doc_id}/metadata")
async def get_document_metadata(doc_id: str):
    """
    Get document metadata only (no content)

    Args:
        doc_id: Document ID

    Returns:
        Document metadata
    """
    logger.info(f"Getting metadata for document: {doc_id}")

    try:
        document = await doc_store.get_document(doc_id)

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Return only metadata (no page content)
        pages_value = document.get("pages", [])
        pages = pages_value if isinstance(pages_value, int) else len(pages_value)
        metadata = {
            "doc_id": document["doc_id"],
            "filename": document["filename"],
            "doc_type": document.get("doc_type"),
            "form_number": document.get("form_number"),
            "state": document.get("state"),
            "effective_date": document.get("effective_date"),
            "pages": pages,
            "ingested_at": document.get("ingested_at"),
            "indexed_at": document.get("indexed_at")
        }

        return {"metadata": metadata}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_storage_stats():
    """
    Get storage statistics

    Returns:
        Storage stats for all stores
    """
    logger.info("Getting storage statistics")

    try:
        # Doc store stats
        doc_stats = await doc_store.get_stats()

        # Vector store stats
        from app.adapters.faiss_vector_store import FAISSVectorStoreAdapter
        vector_store = FAISSVectorStoreAdapter(data_dir / "vectors")
        await vector_store.load_index(data_dir / "vectors")
        vector_stats = await vector_store.get_stats()

        # Graph store stats
        from app.adapters.networkx_graph_store import NetworkXGraphStoreAdapter
        graph_store = NetworkXGraphStoreAdapter(data_dir / "graph")
        await graph_store.load_graph(data_dir / "graph")
        graph_stats = await graph_store.get_stats()

        return {
            "documents": doc_stats,
            "vectors": vector_stats,
            "graph": graph_stats
        }

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/chunks")
async def search_chunks(
    query: str,
    limit: int = 10,
    doc_id: Optional[str] = None,
    page_number: Optional[int] = None
):
    """
    Search chunks by text (simple text search, not semantic)

    Args:
        query: Search query
        limit: Maximum results
        doc_id: Filter by document ID (optional)
        page_number: Filter by page number (optional)

    Returns:
        Matching chunks
    """
    logger.info(f"Searching chunks: {query[:50]}")

    try:
        # Build filter
        metadata_filter = {}
        if doc_id:
            metadata_filter["doc_id"] = doc_id
        if page_number is not None:
            metadata_filter["page_number"] = page_number

        # Get all chunks
        all_chunks = await doc_store.get_chunks(metadata_filter or None)

        # Simple text search (case-insensitive)
        query_lower = query.lower()
        matching_chunks = [
            chunk for chunk in all_chunks
            if query_lower in chunk.get("text", "").lower()
        ]

        # Limit results
        matching_chunks = matching_chunks[:limit]

        return {
            "query": query,
            "chunks": matching_chunks,
            "total": len(matching_chunks)
        }

    except Exception as e:
        logger.error(f"Error searching chunks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph")
async def get_graph():
    """
    Get the complete knowledge graph for visualization

    Returns:
        Graph data with nodes and edges
    """
    logger.info("Getting graph data for visualization")

    try:
        from app.adapters.networkx_graph_store import NetworkXGraphStoreAdapter

        graph_store = NetworkXGraphStoreAdapter(data_dir / "graph")
        await graph_store.load_graph(data_dir / "graph")

        # Get all nodes
        nodes = []
        for node_id in graph_store.graph.nodes():
            node_data = graph_store.graph.nodes[node_id]
            nodes.append({
                "id": node_id,
                "label": node_data.get("label", node_id),
                "type": node_data.get("node_type", "Other"),
                "properties": node_data.get("properties", {})
            })

        # Get all edges
        edges = []
        for source, target, edge_data in graph_store.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "type": edge_data.get("edge_type", "RELATED"),
                "properties": edge_data.get("properties", {})
            })

        # Get stats
        stats = await graph_store.get_stats()

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Error getting graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/graph")
async def clear_graph():
    """
    Clear the entire knowledge graph

    Returns:
        Confirmation of graph deletion
    """
    logger.info("Clearing knowledge graph")

    try:
        from app.adapters.networkx_graph_store import NetworkXGraphStoreAdapter

        graph_store = NetworkXGraphStoreAdapter(data_dir / "graph")
        await graph_store.load_graph(data_dir / "graph")

        # Clear the graph
        await graph_store.clear_graph()
        await graph_store.save_graph(data_dir / "graph")

        return {
            "status": "success",
            "message": "Knowledge graph cleared successfully"
        }

    except Exception as e:
        logger.error(f"Error clearing graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rebuild-graph")
async def rebuild_graph(
    graph_extraction_profile_id: str = "generic"
):
    """
    Rebuild the knowledge graph from all indexed documents

    Args:
        graph_extraction_profile_id: Graph extraction profile to use

    Returns:
        Rebuild statistics
    """
    logger.info(f"Rebuilding knowledge graph with profile: {graph_extraction_profile_id}")

    try:
        from app.adapters.networkx_graph_store import NetworkXGraphStoreAdapter
        from app.adapters.openai_adapter import OpenAIAdapter
        from app.modules.graph_extraction import GraphExtractionModule
        from app.core.config_loader import get_config_loader

        # Initialize components
        graph_store = NetworkXGraphStoreAdapter(data_dir / "graph")
        llm = OpenAIAdapter()
        config_loader = get_config_loader()

        # Load profile
        graph_extraction_profile = config_loader.get_graph_extraction_profile(graph_extraction_profile_id)
        graph_extractor = GraphExtractionModule(llm, profile=graph_extraction_profile)

        # Clear existing graph
        await graph_store.clear_graph()

        # Get all indexed documents (those with chunks)
        all_documents = await doc_store.list_documents()
        indexed_docs = []

        for doc in all_documents:
            doc_id = doc["doc_id"]
            chunks = await doc_store.get_chunks(doc_id=doc_id)
            if chunks:
                indexed_docs.append({"doc_id": doc_id, "chunks": chunks})

        logger.info(f"Found {len(indexed_docs)} indexed documents to rebuild graph from")

        total_entities = 0
        total_relationships = 0

        # Extract graph from each document's chunks
        for doc_info in indexed_docs:
            doc_id = doc_info["doc_id"]
            chunks = doc_info["chunks"]

            logger.info(f"Extracting graph from document: {doc_id} ({len(chunks)} chunks)")

            graph_data = await graph_extractor.extract_from_chunks(chunks)

            if graph_data["nodes"]:
                await graph_store.add_nodes(graph_data["nodes"])
                total_entities += len(graph_data["nodes"])

            if graph_data["edges"]:
                await graph_store.add_edges(graph_data["edges"])
                total_relationships += len(graph_data["edges"])

        # Save the rebuilt graph
        await graph_store.save_graph(data_dir / "graph")

        return {
            "status": "success",
            "documents_processed": len(indexed_docs),
            "total_entities": total_entities,
            "total_relationships": total_relationships
        }

    except Exception as e:
        logger.error(f"Error rebuilding graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))
