# RAGMesh

**Production-Grade Retrieval-Augmented Generation Framework for Insurance Documents**

RAGMesh is a comprehensive, configuration-driven RAG system designed specifically for processing insurance policies, endorsements, and disclosures. It features tri-modal retrieval (Vector + Document + Graph), 9-check validation system, and complete observability.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

### Core Capabilities
- **Tri-Modal Retrieval**: Vector (FAISS) + Document (BM25/TF-IDF) + Graph (NetworkX)
- **9-Check Validation**: Citation coverage, groundedness, hallucination detection, and 6 more
- **Configuration-Driven**: 100% JSON-configurable with 8 profile types
- **Real-Time Streaming**: SSE for live pipeline updates
- **Complete Observability**: Event sourcing with full audit trail
- **Production-Ready**: Docker, comprehensive testing, error handling

### System Architecture
- **Backend**: FastAPI + Python 3.11+ with async/await
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **Storage**: File-based (documents, vectors, graph, runs)
- **LLM**: OpenAI GPT-3.5-turbo + text-embedding-3-small
- **Deployment**: Docker Compose with hot reload

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key
- 4GB+ RAM, 2+ CPU cores

### 1. Clone and Configure

```bash
git clone <repository-url>
cd RAGMesh

# Set up environment
cp .env.example .env
# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=sk-your-key-here
```

### 2. Start the Application

```bash
docker-compose up
```

This starts:
- **Backend API**: http://localhost:8017
- **Frontend UI**: http://localhost:3017
- **Health Check**: http://localhost:8017/health

### 3. Upload Sample Documents

1. Open http://localhost:3017
2. Navigate to **Documents** tab
3. Upload PDFs from `sample_data/pdfs/`:
   - `homeowners_policy_HO3_california.pdf`
   - `water_damage_exclusion_endorsement.pdf`
   - `earthquake_coverage_info.pdf`
4. Click **Index** for each document

### 4. Run Sample Queries

Go to the **Query** tab and try:

- "What are the coverage limits for dwelling and personal property?"
- "What types of water damage are excluded?"
- "Is earthquake insurance required in California?"
- "What additional coverages can be added with endorsements?"

Explore the results across all 9 tabs to see the complete pipeline execution!

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        RAGMesh System                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌─────────────────────────────────┐  │
│  │   Frontend   │      │           Backend API            │  │
│  │  (Next.js)   │◄────►│         (FastAPI)                │  │
│  │              │ HTTP │                                   │  │
│  │  9-Tab UI    │ SSE  │  ┌─────────────────────────────┐ │  │
│  └──────────────┘      │  │    Orchestration Layer      │ │  │
│                         │  │  (Workflow Coordinator)     │ │  │
│                         │  └─────────────────────────────┘ │  │
│                         │            │                     │  │
│                         │            ▼                     │  │
│                         │  ┌─────────────────────────────┐ │  │
│                         │  │      Module Pipeline        │ │  │
│                         │  ├─────────────────────────────┤ │  │
│                         │  │ 1. Ingestion (PDF → Text)   │ │  │
│                         │  │ 2. Indexing (Chunk+Embed)   │ │  │
│                         │  │ 3. Retrieval (Tri-Modal)    │ │  │
│                         │  │ 4. Fusion (Weighted RRF)    │ │  │
│                         │  │ 5. Context (Pack+Redact)    │ │  │
│                         │  │ 6. Generation (Answer)      │ │  │
│                         │  │ 7. Judge (9 Checks)         │ │  │
│                         │  └─────────────────────────────┘ │  │
│                         │            │                     │  │
│                         │            ▼                     │  │
│                         │  ┌─────────────────────────────┐ │  │
│                         │  │      Adapter Layer          │ │  │
│                         │  ├─────────────────────────────┤ │  │
│                         │  │ • FileDocStore              │ │  │
│                         │  │ • FAISSVectorStore          │ │  │
│                         │  │ • NetworkXGraph             │ │  │
│                         │  │ • OpenAIAdapter             │ │  │
│                         │  └─────────────────────────────┘ │  │
│                         └─────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Storage (File-Based)                        │ │
│  ├─────────────────────────────────────────────────────────┤ │
│  │  data/docs/  data/chunks/  data/vectors/  data/graph/   │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
RAGMesh/
├── backend/                      # Python FastAPI backend
│   ├── app/
│   │   ├── adapters/             # Swappable implementations
│   │   │   ├── base.py           # Adapter interfaces
│   │   │   ├── file_doc_store.py
│   │   │   ├── faiss_vector_store.py
│   │   │   ├── networkx_graph.py
│   │   │   └── openai_adapter.py
│   │   ├── core/                 # Core domain models
│   │   │   └── models.py         # Pydantic models
│   │   ├── modules/              # Pipeline modules
│   │   │   ├── ingestion.py
│   │   │   ├── indexing.py
│   │   │   ├── retrieval.py
│   │   │   ├── fusion.py
│   │   │   ├── context_compiler.py
│   │   │   ├── generation.py
│   │   │   └── judge/            # 9 validation checks
│   │   │       ├── orchestrator.py
│   │   │       └── checks/
│   │   ├── api.py                # REST API endpoints
│   │   └── main.py               # FastAPI app
│   ├── tests/                    # Comprehensive test suite
│   │   ├── adapters/             # Adapter unit tests
│   │   ├── modules/              # Module unit tests
│   │   ├── api/                  # API integration tests
│   │   └── test_e2e_pipeline.py  # End-to-end tests
│   ├── requirements.txt
│   ├── pytest.ini
│   └── Dockerfile
│
├── frontend/                     # Next.js frontend
│   ├── app/
│   │   ├── layout.tsx
│   │   └── page.tsx              # Main application
│   ├── components/               # 9 tab components
│   │   ├── QueryTab.tsx
│   │   ├── RetrievalTab.tsx
│   │   ├── FusionTab.tsx
│   │   ├── ContextTab.tsx
│   │   ├── AnswerTab.tsx
│   │   ├── JudgeTab.tsx
│   │   ├── EventsTab.tsx
│   │   ├── ConfigTab.tsx
│   │   └── DocumentsTab.tsx
│   ├── lib/
│   │   ├── api.ts                # API client
│   │   └── types.ts              # TypeScript types
│   ├── package.json
│   └── Dockerfile
│
├── config/                       # JSON configuration files
│   ├── models.json               # LLM and embedding models
│   ├── workflows.json            # 3 workflow profiles
│   ├── chunking_profiles.json    # 4 chunking strategies
│   ├── retrieval_profiles.json   # 4 retrieval profiles
│   ├── fusion_profiles.json      # 5 fusion strategies
│   ├── context_profiles.json     # 4 context packing strategies
│   ├── judge_profiles.json       # 4 validation profiles
│   └── telemetry.json            # 3 telemetry profiles
│
├── sample_data/                  # Sample insurance PDFs
│   ├── pdfs/                     # 3 realistic insurance documents
│   ├── generate_sample_pdfs.py   # PDF generation script
│   └── README.md                 # Sample data guide
│
├── data/                         # Runtime data (created on first run)
│   ├── docs/                     # Ingested documents
│   ├── chunks/                   # Chunked text
│   ├── vectors/                  # FAISS index
│   ├── graph/                    # Graph data
│   └── runs/                     # Pipeline execution logs
│
├── docker-compose.yml            # Docker orchestration
├── .env.example                  # Environment template
├── QUICKSTART.md                 # Quick start guide
├── ARCHITECTURE.md               # Architecture documentation
├── PROGRESS.md                   # Implementation progress
└── README.md                     # This file
```

## Configuration Profiles

RAGMesh is 100% configuration-driven with 8 profile types:

### 1. Workflows (3 profiles)
- `default` - Balanced pipeline
- `fast` - Quick responses, lower quality
- `comprehensive` - Maximum accuracy

### 2. Chunking (4 profiles)
- `default` - Sentence-aware, 500 chars
- `large` - 1000 char chunks
- `small` - 300 char chunks
- `page-based` - One chunk per page

### 3. Retrieval (4 profiles)
- `balanced` - Equal weights across modalities
- `vector-focused` - Emphasize semantic search
- `graph-heavy` - Emphasize entity relationships
- `precise` - Higher relevance threshold

### 4. Fusion (5 profiles)
- `balanced` - Weighted RRF with equal weights
- `vector-heavy` - Favor vector results
- `graph-heavy` - Favor graph results
- `keyword-heavy` - Favor document search
- `diverse` - Maximize result diversity

### 5. Context (4 profiles)
- `default` - 3000 token budget
- `large` - 6000 token budget
- `compact` - 1500 token budget
- `citation-heavy` - More metadata per citation

### 6. Judge (4 profiles)
- `strict` - High thresholds, all 9 checks
- `balanced` - Moderate thresholds (default)
- `lenient` - Lower thresholds
- `critical-only` - Only hard-fail checks

### 7. Telemetry (3 profiles)
- `minimal` - Critical events only
- `standard` - Key milestones + errors
- `detailed` - Full event stream

### 8. Models
- Generation: GPT-3.5-turbo
- Embeddings: text-embedding-3-small
- Configurable temperature, max_tokens, timeouts

## API Documentation

### Core Endpoints

#### Health Check
```bash
GET /health
```

#### Ingest PDF
```bash
POST /ingest
Content-Type: multipart/form-data

file: <PDF file>
metadata: {"form_number": "HO-3", "doc_type": "policy", "state": "CA"}
```

#### Index Document
```bash
POST /index
Content-Type: application/json

{
  "doc_id": "doc_123",
  "chunking_profile_id": "default"
}
```

#### Execute Query
```bash
POST /run
Content-Type: application/json

{
  "query": "What does the policy cover?",
  "workflow_profile_id": "default"
}
```

#### Stream Events (SSE)
```bash
GET /run/{run_id}/stream
Accept: text/event-stream
```

#### Get Run Status
```bash
GET /run/{run_id}/status
```

See full API documentation at http://localhost:8017/docs (when running).

## Testing

### Run All Tests
```bash
cd backend
pytest
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Test Categories
```bash
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests
pytest -m slow          # Slow tests (E2E)
```

### Test Coverage
- **Adapters**: 90%+
- **Modules**: 85%+
- **Judge Checks**: 90%+
- **API**: 75%+
- **Overall**: 80%+

See [backend/tests/README.md](backend/tests/README.md) for details.

## Development

### Local Development (without Docker)

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8017
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Adding New Adapters

1. Extend base adapter interface in `backend/app/adapters/base.py`
2. Implement adapter in `backend/app/adapters/your_adapter.py`
3. Add configuration in `config/models.json` or relevant file
4. Update factory/dependency injection in `app/main.py`
5. Write unit tests in `tests/adapters/test_your_adapter.py`

### Adding New Judge Checks

1. Create check in `backend/app/modules/judge/checks/your_check.py`
2. Implement `BaseCheck` interface
3. Register in `JudgeOrchestrator`
4. Add configuration in `config/judge_profiles.json`
5. Write unit tests in `tests/modules/judge/checks/test_your_check.py`

## Performance

### Benchmarks (3 insurance PDFs, ~20 pages total)

- **Ingestion**: ~2 seconds per PDF
- **Indexing**: ~5-8 seconds per document (including embeddings)
- **Retrieval**: ~1-2 seconds
- **Full Pipeline**: ~8-12 seconds (including generation and validation)

### Optimization Tips

1. **Use Smaller Chunks**: Reduces embedding costs and latency
2. **Adjust Top-K**: Lower values for faster retrieval
3. **Fast Workflow**: Use `fast` workflow profile for quick responses
4. **Batch Processing**: Index multiple documents before querying
5. **Cache Embeddings**: Embeddings are cached in vector store

## Security

### Current Measures
- PII redaction in context compilation
- Toxicity check in judge validation
- Input validation with Pydantic
- CORS configuration for frontend
- Environment-based secrets

### Production Recommendations
- Enable HTTPS/TLS
- Add authentication/authorization
- Rate limiting on API endpoints
- Input sanitization for user queries
- Secrets management (AWS Secrets Manager, HashiCorp Vault)
- Regular security audits

## Deployment

### Docker Production Build
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables
```bash
OPENAI_API_KEY=<your-key>
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
API_PORT=8017
FRONTEND_PORT=3017
ENVIRONMENT=production
```

### Scaling Considerations
- **Horizontal**: Add load balancer for multiple API instances
- **Vertical**: Increase container memory/CPU for large documents
- **Storage**: Consider S3/GCS for document storage
- **Database**: Migrate to PostgreSQL for metadata
- **Vector DB**: Consider Pinecone/Weaviate for large-scale vector search
- **Caching**: Add Redis for frequently accessed data

## Troubleshooting

### Common Issues

**Docker containers won't start**
```bash
docker-compose down
docker-compose up --build
```

**OpenAI API errors**
- Verify API key in `.env`
- Check API quota: https://platform.openai.com/usage
- Ensure `OPENAI_API_KEY` starts with `sk-`

**Documents fail to index**
- Check PDF is valid (not password-protected)
- Verify sufficient disk space
- Check backend logs: `docker-compose logs ragmesh-api`

**Query returns no results**
- Ensure documents are indexed (check Documents tab)
- Try different query phrasings
- Review retrieval results in Retrieval tab

**Frontend can't connect to backend**
- Verify both containers are running: `docker ps`
- Check `NEXT_PUBLIC_API_URL` in `.env`
- Verify backend health: http://localhost:8017/health

## Roadmap

### Planned Features
- [ ] Support for more document types (DOCX, TXT, HTML)
- [ ] Multi-language support
- [ ] Fine-tuned embedding models
- [ ] Advanced graph queries (SPARQL-like)
- [ ] Query history and analytics
- [ ] User management and authentication
- [ ] Batch processing API
- [ ] Export/import configurations
- [ ] Custom judge check plugins
- [ ] Real-time collaboration

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- Python: Black formatter, isort, flake8
- TypeScript: ESLint, Prettier
- Write tests for new features
- Update documentation

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- OpenAI for GPT-3.5 and embeddings
- FAISS for fast vector search
- NetworkX for graph operations
- FastAPI and Next.js communities

## Support

- **Documentation**: See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design
- **Quick Start**: See [QUICKSTART.md](QUICKSTART.md)
- **Issues**: Open an issue on GitHub
- **Email**: support@ragmesh.example.com (if applicable)

## Citation

If you use RAGMesh in your research, please cite:

```bibtex
@software{ragmesh2024,
  title={RAGMesh: Production-Grade RAG Framework for Insurance Documents},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/ragmesh}
}
```

---

**Built with ❤️ for the insurance industry**
