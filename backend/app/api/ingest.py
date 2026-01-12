"""
Ingestion API routes
Handles PDF upload and document indexing
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import logging
import uuid
import shutil

from app.core.models import IngestPDFResponse, IndexDocumentResponse
from app.adapters.file_doc_store import FileDocStoreAdapter
from app.adapters.faiss_vector_store import FAISSVectorStoreAdapter
from app.adapters.networkx_graph_store import NetworkXGraphStoreAdapter
from app.adapters.openai_adapter import OpenAIAdapter
from app.modules.pdf_ingestion import PDFIngestionModule
from app.modules.chunking import ChunkingModule
from app.modules.graph_extraction import GraphExtractionModule
from app.core.config_loader import get_config_loader

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize components
config_loader = get_config_loader()
data_dir = Path("data")
doc_store = FileDocStoreAdapter(data_dir)
vector_store = FAISSVectorStoreAdapter(data_dir / "vectors")
graph_store = NetworkXGraphStoreAdapter(data_dir / "graph")
llm = OpenAIAdapter()

pdf_ingestion = PDFIngestionModule()
chunking = ChunkingModule()
graph_extraction = GraphExtractionModule(llm)


@router.post("/ingest/pdf", response_model=IngestPDFResponse)
async def ingest_pdf(
    file: UploadFile = File(...),
    doc_type: str = None,
    form_number: str = None,
    effective_date: str = None,
    state: str = None
):
    """
    Upload and ingest a PDF file

    Args:
        file: PDF file to upload
        doc_type: Document type
        form_number: Form number
        effective_date: Effective date
        state: State jurisdiction

    Returns:
        Ingestion response with doc_id
    """
    logger.info(f"Ingesting PDF: {file.filename}")

    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Save uploaded file
        temp_dir = Path("data/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file_path = temp_dir / f"{uuid.uuid4()}.pdf"

        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Validate PDF
        validation = await pdf_ingestion.validate_pdf(temp_file_path)
        if not validation["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid PDF: {', '.join(validation['errors'])}"
            )

        # Ingest PDF
        document = await pdf_ingestion.ingest_pdf(
            file_path=temp_file_path,
            filename=file.filename,
            doc_type=doc_type,
            form_number=form_number,
            effective_date=effective_date,
            state=state
        )

        # Save document
        await doc_store.save_document(document.doc_id, document.model_dump())

        # Clean up temp file
        temp_file_path.unlink()

        return IngestPDFResponse(
            doc_id=document.doc_id,
            filename=file.filename,
            pages=len(document.pages),
            success=True
        )

    except Exception as e:
        logger.error(f"Error ingesting PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/{doc_id}", response_model=IndexDocumentResponse)
async def index_document(
    doc_id: str,
    chunking_profile_id: str = "default",
    graph_extraction_profile_id: str = "generic"
):
    """
    Index a document (chunking, embeddings, graph extraction)

    Args:
        doc_id: Document ID to index
        chunking_profile_id: Chunking profile to use
        graph_extraction_profile_id: Graph extraction profile to use (domain-specific entity/relationship types)

    Returns:
        Indexing response with statistics
    """
    logger.info(f"Indexing document: {doc_id} with graph profile: {graph_extraction_profile_id}")

    try:
        # Load document
        document_data = await doc_store.get_document(doc_id)
        if not document_data:
            raise HTTPException(status_code=404, detail="Document not found")

        from app.core.models import Document
        document = Document(**document_data)

        # Load profiles
        chunking_profile = config_loader.get_chunking_profile(chunking_profile_id)
        graph_extraction_profile = config_loader.get_graph_extraction_profile(graph_extraction_profile_id)

        # Step 1: Chunk document
        chunks = await chunking.chunk_document(document, chunking_profile)
        chunks_data = [chunk.model_dump() for chunk in chunks]
        await doc_store.save_chunks(doc_id, chunks_data)

        # Step 2: Generate embeddings
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = await llm.embed(chunk_texts)
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        chunk_metadata = [chunk.metadata for chunk in chunks]

        await vector_store.add_embeddings(chunk_ids, embeddings, chunk_metadata)
        await vector_store.save_index(data_dir / "vectors")

        # Step 3: Extract graph entities with domain-specific profile
        graph_extractor = GraphExtractionModule(llm, profile=graph_extraction_profile)
        graph_data = await graph_extractor.extract_from_chunks(chunks_data)
        if graph_data["nodes"]:
            await graph_store.add_nodes(graph_data["nodes"])
        if graph_data["edges"]:
            await graph_store.add_edges(graph_data["edges"])
        await graph_store.save_graph(data_dir / "graph")

        # Update document indexed_at
        document.indexed_at = document_data.get("indexed_at")
        await doc_store.save_document(doc_id, document.model_dump())

        return IndexDocumentResponse(
            doc_id=doc_id,
            chunks_created=len(chunks),
            embeddings_created=len(embeddings),
            entities_extracted=len(graph_data["nodes"]),
            relationships_extracted=len(graph_data["edges"]),
            success=True
        )

    except Exception as e:
        logger.error(f"Error indexing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))
