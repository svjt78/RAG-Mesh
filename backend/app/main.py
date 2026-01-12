"""
RAGMesh - Production-Grade Insurance RAG Framework
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting RAGMesh API...")

    # Initialize data directories
    from pathlib import Path
    data_dirs = [
        Path("data/docs"),
        Path("data/chunks"),
        Path("data/vectors"),
        Path("data/graph"),
        Path("data/runs"),
        Path("data/temp")
    ]
    for directory in data_dirs:
        directory.mkdir(parents=True, exist_ok=True)
    logger.info("Data directories initialized")

    # Load configurations
    from app.core.config_loader import get_config_loader
    config_loader = get_config_loader()
    logger.info(f"Configurations loaded: {len(config_loader.list_profiles())} profile types")

    # Initialize vector store index (if exists)
    try:
        from app.adapters.faiss_vector_store import FAISSVectorStoreAdapter
        vector_store = FAISSVectorStoreAdapter(Path("data/vectors"))
        await vector_store.load_index(Path("data/vectors"))
        logger.info(f"Vector index loaded: {await vector_store.get_index_size()} vectors")
    except Exception as e:
        logger.info(f"No existing vector index found: {e}")

    # Initialize graph store (if exists)
    try:
        from app.adapters.networkx_graph_store import NetworkXGraphStoreAdapter
        graph_store = NetworkXGraphStoreAdapter(Path("data/graph"))
        await graph_store.load_graph(Path("data/graph"))
        stats = await graph_store.get_stats()
        logger.info(f"Graph loaded: {stats['node_count']} nodes, {stats['edge_count']} edges")
    except Exception as e:
        logger.info(f"No existing graph found: {e}")

    logger.info("RAGMesh API ready!")

    yield

    logger.info("Shutting down RAGMesh API...")


# Initialize FastAPI application
app = FastAPI(
    title="RAGMesh API",
    description="Production-Grade Insurance RAG Framework with Tri-Modal Retrieval",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3017", "http://frontend:3017"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RAGMesh API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ragmesh-api"
    }


# Register API routes
from app.api import ingest, run, config, docs

app.include_router(ingest.router, prefix="/api", tags=["Ingestion"])
app.include_router(run.router, prefix="/api", tags=["Execution"])
app.include_router(config.router, prefix="/api", tags=["Configuration"])
app.include_router(docs.router, prefix="/api", tags=["Documents"])
