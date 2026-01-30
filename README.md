# RAGMesh

**Production-Grade Retrieval-Augmented Generation Framework for Insurance Documents**

RAGMesh is a comprehensive, configuration-driven RAG system designed specifically for processing insurance policies, endorsements, and disclosures. It features tri-modal retrieval (Vector + Document + Graph), 9-check validation system, and complete observability.

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## What's New 🎉

### Latest Updates (January 2026)

- **📊 Fusion Logic Documentation**: Comprehensive documentation of tri-modal retrieval scoring
  - Detailed explanation of V (Vector), D (Document), G (Graph) score calculations
  - Weighted Reciprocal Rank Fusion (RRF) formula with worked examples
  - Configuration options for fusion weights and retrieval profiles
  - See [FUSION_LOGIC.md](FUSION_LOGIC.md) for complete details

- **🔗 Graph Retrieval Enhancements**: Improved entity linking and scoring
  - LLM-based entity extraction from queries using GPT-3.5-turbo
  - Fuzzy matching with SequenceMatcher (0.8 threshold) for entity linking
  - Seed entity boosting (1.5x) for chunks supporting query-linked entities
  - Normalized scoring with entity mention counting
  - See [GRAPH_SEARCH.md](GRAPH_SEARCH.md) for implementation details

- **🗨️ Chat Mode**: Added stateful multi-turn conversations with intelligent history management
  - In-memory session management with automatic compaction
  - LLM-based conversation summarization
  - Token budget balancing between history and retrieval context
  - Three configurable chat profiles (default, long_context, compact)

- **🎨 Enhanced UI**:
  - Mode toggle for switching between Query and Chat modes
  - Dedicated chat history panel showing full conversation thread
  - Real-time session status indicators
  - Chat profile configuration editor

- **⚙️ Configuration Improvements**:
  - New `chat_profiles.json` with 3 profile types
  - Enhanced judge profiles with improved validation thresholds
  - Better event tracking for chat sessions
  - Graph extraction profiles are now viewable/editable in the Config tab with dedicated API endpoints

- **🔧 Backend Enhancements**:
  - New `ChatSessionManager` for session lifecycle management
  - Enhanced context compiler with chat-aware token management
  - Improved generation module with chat-specific prompting
  - Robust judge checks with better edge case handling

See [CHAT_MODE_IMPLEMENTATION_PLAN.md](CHAT_MODE_IMPLEMENTATION_PLAN.md) for complete design details.

## Features

### Core Capabilities
- **Dual Execution Modes**: Query mode (stateless) and Chat mode (multi-turn conversations)
- **Tri-Modal Retrieval**: Vector (FAISS) + Document (BM25/TF-IDF) + Graph (NetworkX)
- **Retrieval Docs**: [Document Search](DOCUMENT_SEARCH.md), [Graph Search](GRAPH_SEARCH.md), and [Fusion Logic](FUSION_LOGIC.md)
- **9-Check Validation**: Citation coverage, groundedness, hallucination detection, and 6 more
- **Configuration-Driven**: 100% JSON-configurable with 9 profile types
- **Intelligent Chat Sessions**: In-memory sessions with LLM-based history compaction
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

### 5. Try Chat Mode (NEW!)

Switch to **Chat Mode** in the Query tab for multi-turn conversations:

1. Toggle to **Chat Mode** using the mode selector
2. Ask: "What does the homeowners policy cover?"
3. Follow up: "What about water damage specifically?"
4. Continue: "Are there any endorsements that expand this coverage?"
5. Type "Quit" to end the session

Chat mode maintains conversation history and allows contextual follow-up questions!

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

## Tri-Modal Retrieval System

RAGMesh uses three complementary retrieval modalities that are fused using Weighted Reciprocal Rank Fusion (RRF):

### Vector Search (V Score)
- **Method**: Semantic similarity using embeddings
- **Implementation**: FAISS index with cosine similarity
- **Score Range**: 0.0 to 1.0
- **Best For**: Finding conceptually related content even with different wording

### Document Search (D Score)
- **Method**: Keyword matching with BM25 + TF-IDF
- **Implementation**: 60% BM25 + 40% TF-IDF with boost factors
- **Score Range**: 0.0 to ~5.4 (with all boosts)
- **Boosts**:
  - Exact match: 1.5x
  - Form number: 2.0x
  - Defined terms: 1.8x
- **Best For**: Finding exact keyword matches and specific terms

### Graph Search (G Score)
- **Method**: Entity-based knowledge graph traversal
- **Implementation**: NetworkX with LLM entity extraction
- **Score Range**: 0.0 to 1.0 (capped)
- **Process**:
  1. Extract entities from query using LLM (GPT-3.5-turbo)
  2. Link to graph nodes via exact match or fuzzy matching (>0.8 similarity)
  3. Traverse relationships up to `graph_max_hops`
  4. Score by entity mention count, boost 1.5x for seed entities
- **Best For**: Finding structurally related content through entity relationships

### Fusion (Final Score)
All three modalities are combined using **rank-based fusion**, not score averaging:

```
Final_Score = Σ (Weight_i / (K + Rank_i))
```

This approach handles incompatible score ranges and produces robust rankings. See [FUSION_LOGIC.md](FUSION_LOGIC.md) for detailed calculations.

## Chat Mode (NEW Feature!)

RAGMesh now supports **stateful multi-turn conversations** alongside traditional stateless queries.

### Key Features

- **In-Memory Sessions**: Conversation state maintained during session (lost on refresh)
- **Contextual Awareness**: Each turn has access to full conversation history
- **Intelligent Compaction**: LLM-based summarization when history exceeds token threshold
- **Full Pipeline Execution**: Each turn executes complete RAG pipeline with retrieval
- **Token Budget Management**: Balances history tokens with retrieval context
- **Configuration-Driven**: Three chat profiles (default, long_context, compact)

### How It Works

1. **Toggle to Chat Mode** in the Query tab
2. **Ask your first question** - A new session is created automatically
3. **Follow-up questions** reference previous conversation context
4. **View chat history** in the dedicated panel showing all Q&A turns
5. **Type "Quit"** or click "End Session" to terminate

### Chat vs Query Mode

| Feature | Query Mode | Chat Mode |
|---------|------------|-----------|
| State | Stateless | Stateful |
| History | None | Full conversation |
| Use Case | One-off questions | Exploratory conversations |
| Context | Retrieval only | History + Retrieval |
| Sessions | No | Yes (in-memory) |

### Configuration

Chat profiles control history management:

- **compaction_threshold_tokens**: When to trigger summarization (default: 2000)
- **max_history_turns**: Maximum turns before compaction (default: 10)
- **summarization_model**: LLM for history summarization
- **reserve_tokens_for_history**: Token budget reserved for conversation history

See [config/chat_profiles.json](config/chat_profiles.json) for full details.

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
│   │   │   ├── models.py         # Pydantic models
│   │   │   ├── orchestrator.py   # Pipeline orchestration
│   │   │   ├── config_loader.py  # Configuration loader
│   │   │   └── chat_manager.py   # Chat session management (NEW)
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
│   ├── components/               # 9 tab components + chat UI
│   │   ├── QueryTab.tsx          # Query input + Chat mode UI (ENHANCED)
│   │   ├── RetrievalTab.tsx
│   │   ├── FusionTab.tsx
│   │   ├── ContextTab.tsx
│   │   ├── AnswerTab.tsx
│   │   ├── JudgeTab.tsx
│   │   ├── EventsTab.tsx         # Event streaming display (ENHANCED)
│   │   ├── ConfigTab.tsx         # Configuration management (ENHANCED)
│   │   ├── DocumentsTab.tsx
│   │   └── ChatProfileEditor.tsx # Chat profile editor (NEW)
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
│   ├── chat_profiles.json        # 3 chat mode profiles (NEW)
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
├── CHAT_MODE_IMPLEMENTATION_PLAN.md  # Chat mode design doc
├── DOCUMENT_SEARCH.md            # Document (BM25/TF-IDF) retrieval docs
├── GRAPH_SEARCH.md               # Graph-based retrieval docs
├── FUSION_LOGIC.md               # Tri-modal fusion scoring docs (NEW)
└── README.md                     # This file
```

## Configuration Profiles

RAGMesh is 100% configuration-driven with 9 profile types:

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

### 7. Chat (3 profiles) - NEW!
- `default` - Standard chat (2000 token threshold, 10 turn history)
- `long_context` - Extended conversations (4000 tokens, 20 turns)
- `compact` - Minimal history (1000 tokens, 5 turns)

### 8. Telemetry (3 profiles)
- `minimal` - Critical events only
- `standard` - Key milestones + errors
- `detailed` - Full event stream

### 9. Models
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

#### Execute Query (Query Mode)
```bash
POST /run
Content-Type: application/json

{
  "query": "What does the policy cover?",
  "workflow_profile_id": "default",
  "mode": "query"
}
```

#### Execute Query (Chat Mode) - NEW!
```bash
POST /run
Content-Type: application/json

{
  "query": "What about water damage?",
  "workflow_profile_id": "default",
  "mode": "chat",
  "session_id": "abc-123-def",  // Optional for first turn
  "chat_profile_id": "default"
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

#### Chat Session Management - NEW!
```bash
# Get chat session details
GET /chat/session/{session_id}

# List all active chat sessions
GET /chat/sessions

# Delete chat session
DELETE /chat/session/{session_id}
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

### Test Chat Mode
```bash
# Chat-specific tests
pytest tests/test_chat_manager.py           # Chat session management
pytest tests/test_e2e_chat.py               # End-to-end chat tests
pytest tests/modules/test_context_compiler.py -k chat  # Chat context tests
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

**Chat mode issues**
- **Session lost on refresh**: This is expected - sessions are in-memory
- **History not showing**: Check browser console for errors; verify session_id in response
- **"Quit" not working**: Ensure exact spelling (case-insensitive)
- **Token budget exceeded**: Try `compact` chat profile or reduce retrieval top-k
- **Compaction errors**: Check backend logs for LLM API errors

## Roadmap

### Recently Implemented ✅
- [x] **Chat Mode**: Multi-turn conversations with intelligent history compaction
- [x] **Chat Profiles**: Configurable chat behavior and token management
- [x] **Session Management**: In-memory chat session lifecycle
- [x] **Enhanced UI**: Mode toggle and chat history panel

### Planned Features
- [ ] **Persistent Chat Sessions**: Save conversations to disk/database
- [ ] **Chat Export**: Download conversation history as JSON/PDF
- [ ] **Streaming Responses**: Token-by-token generation in chat mode
- [ ] Support for more document types (DOCX, TXT, HTML)
- [ ] Multi-language support
- [ ] Fine-tuned embedding models
- [ ] Advanced graph queries (SPARQL-like)
- [ ] Query history and analytics dashboard
- [ ] User management and authentication
- [ ] Batch processing API
- [ ] Export/import configurations
- [ ] Custom judge check plugins
- [ ] Multi-user real-time collaboration

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
- **Chat Mode Design**: See [CHAT_MODE_IMPLEMENTATION_PLAN.md](CHAT_MODE_IMPLEMENTATION_PLAN.md)
- **Retrieval Documentation**:
  - [DOCUMENT_SEARCH.md](DOCUMENT_SEARCH.md) - BM25/TF-IDF keyword search
  - [GRAPH_SEARCH.md](GRAPH_SEARCH.md) - Entity-based graph retrieval
  - [FUSION_LOGIC.md](FUSION_LOGIC.md) - Tri-modal fusion scoring (V, D, G)
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
