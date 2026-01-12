# RAGMesh Architecture

**Comprehensive Technical Documentation**

This document provides an in-depth explanation of RAGMesh's architecture, design decisions, and implementation details.

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Layer-by-Layer Breakdown](#layer-by-layer-breakdown)
4. [Data Flow](#data-flow)
5. [Module Deep Dive](#module-deep-dive)
6. [Configuration System](#configuration-system)
7. [Validation Framework](#validation-framework)
8. [Observability & Telemetry](#observability--telemetry)
9. [Storage Strategy](#storage-strategy)
10. [Scaling Considerations](#scaling-considerations)

---

## System Overview

RAGMesh is a production-grade Retrieval-Augmented Generation (RAG) framework designed for insurance document processing. It implements a multi-stage pipeline with tri-modal retrieval and comprehensive validation.

### Key Components

```
┌─────────────────────────────────────────────────────────────┐
│                      RAGMesh System                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend (Next.js 14 + TypeScript)                          │
│  ├── 9-Tab Interface                                          │
│  ├── Real-Time SSE Streaming                                 │
│  └── REST API Client                                          │
│                                                               │
│  Backend (FastAPI + Python 3.11+)                            │
│  ├── Orchestration Layer (Workflow Coordinator)             │
│  ├── Module Layer (7 Pipeline Modules)                       │
│  ├── Adapter Layer (Swappable Implementations)              │
│  └── Storage Layer (File-Based)                              │
│                                                               │
│  Configuration (JSON)                                         │
│  └── 8 Profile Types (100% Configurable)                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture Principles

### 1. **Configuration-Driven Design**

**Principle**: All system behavior is controlled via JSON configuration files.

**Benefits**:
- No code changes required for tuning
- Easy A/B testing of strategies
- Version-controlled configurations
- Environment-specific settings

**Implementation**:
```python
# Example: Loading retrieval profile
profile = config_loader.get_profile("retrieval", "balanced")
results = retrieval.retrieve(query, profile=profile)
```

### 2. **Adapter Pattern for Swappability**

**Principle**: All external dependencies use adapters implementing common interfaces.

**Benefits**:
- Easy to swap implementations (e.g., FAISS → Pinecone)
- Simplified testing with mocks
- Isolation of vendor-specific code

**Implementation**:
```python
# Base adapter interface
class VectorStoreAdapter(ABC):
    @abstractmethod
    async def add_vectors(self, vectors: list) -> None: ...
    @abstractmethod
    async def search(self, query_vector: list, top_k: int) -> list: ...

# Concrete implementation
class FAISSVectorStore(VectorStoreAdapter):
    # FAISS-specific implementation
    ...
```

### 3. **Event Sourcing for Observability**

**Principle**: Every pipeline step emits events that are stored and can be replayed.

**Benefits**:
- Complete audit trail
- Debugging and troubleshooting
- Performance analysis
- Real-time monitoring via SSE

**Implementation**:
```python
# Emit event at each step
await telemetry.emit_event(
    run_id=run_id,
    step="retrieval",
    status="completed",
    details={"results_count": len(results)},
)
```

### 4. **Fail-Fast Validation**

**Principle**: Validate outputs at critical checkpoints with 9 judge checks.

**Benefits**:
- Prevent hallucinations
- Ensure citation accuracy
- Early error detection
- Quality assurance

---

## Layer-by-Layer Breakdown

### 1. Frontend Layer (Next.js 14)

**Responsibilities**:
- User interface (9 tabs)
- API communication
- Real-time updates via SSE
- State management

**Architecture**:
```
frontend/
├── app/
│   ├── layout.tsx              # Root layout with metadata
│   └── page.tsx                # Main app with state management
├── components/
│   ├── QueryTab.tsx            # Query input + workflow selection
│   ├── RetrievalTab.tsx        # Tri-modal results viewer
│   ├── FusionTab.tsx           # Fused results display
│   ├── ContextTab.tsx          # Context pack viewer
│   ├── AnswerTab.tsx           # Generated answer with citations
│   ├── JudgeTab.tsx            # 9 validation checks
│   ├── EventsTab.tsx           # Real-time event stream
│   ├── ConfigTab.tsx           # Configuration browser
│   └── DocumentsTab.tsx        # Document management
└── lib/
    ├── api.ts                  # Complete API client (25+ methods)
    └── types.ts                # TypeScript type definitions
```

**State Management**:
```typescript
// Main application state
const [currentRunId, setCurrentRunId] = useState<string | null>(null);
const [runData, setRunData] = useState<RunData | null>(null);
const [events, setEvents] = useState<Event[]>([]);
const [isStreaming, setIsStreaming] = useState(false);

// Real-time updates via SSE
const eventSource = apiClient.createEventSource(runId);
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  setEvents(prev => [...prev, data]);
  updateArtifacts(data);
};
```

### 2. API Layer (FastAPI)

**Responsibilities**:
- REST endpoints
- SSE streaming
- Request validation
- Error handling

**Key Endpoints**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/ingest` | POST | Upload and ingest PDF |
| `/index` | POST | Index document (chunk + embed) |
| `/run` | POST | Execute RAG pipeline |
| `/run/{id}/stream` | GET | SSE event stream |
| `/run/{id}/status` | GET | Get run status |
| `/run/{id}/artifacts` | GET | Get pipeline artifacts |
| `/profiles` | GET | List all profiles |
| `/profiles/{type}/{id}` | GET | Get specific profile |
| `/documents` | GET | List documents |
| `/documents/{id}` | GET | Get document |
| `/reload-config` | POST | Reload configurations |

**Error Handling**:
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": str(exc),
            "request_id": request.state.request_id,
        },
    )
```

### 3. Orchestration Layer

**Responsibilities**:
- Workflow coordination
- Step sequencing
- Timeout management
- Error recovery

**Workflow Execution**:
```python
async def execute_workflow(
    run_id: str,
    query: str,
    workflow_profile: dict,
) -> RunResult:
    steps = workflow_profile["steps"]

    for step in steps:
        try:
            await telemetry.emit_event(run_id, step, "started")

            if step == "retrieval":
                result = await retrieval.retrieve(query, ...)
            elif step == "fusion":
                result = await fusion.fuse(retrieval_results, ...)
            # ... other steps

            await telemetry.emit_event(run_id, step, "completed")

        except Exception as e:
            await telemetry.emit_event(run_id, step, "failed", error=str(e))
            if workflow_profile.get("fail_on_error"):
                raise
```

### 4. Module Layer

**Responsibilities**:
- Core RAG logic
- Pipeline transformations
- Business logic

#### Module 1: Ingestion

**Purpose**: Convert PDF to structured document

```python
class Ingestion:
    async def ingest_pdf(
        self,
        file_path: str,
        filename: str,
        metadata: dict,
    ) -> Document:
        # Extract text from PDF using pdfplumber
        # Create Document with Pages
        # Preserve bounding boxes
        # Store in doc_store
```

**Output**:
```python
Document(
    doc_id="doc_abc123",
    filename="policy.pdf",
    metadata={"form_number": "HO-3", ...},
    pages=[
        Page(page_num=1, text="...", bbox={...}),
        Page(page_num=2, text="...", bbox={...}),
    ]
)
```

#### Module 2: Indexing

**Purpose**: Chunk document, generate embeddings, extract entities

```python
class Indexing:
    async def index_document(
        self,
        doc_id: str,
        chunking_profile: dict,
    ) -> IndexResult:
        # 1. Chunk text using configured strategy
        chunks = self._chunk_document(doc, chunking_profile)

        # 2. Generate embeddings for each chunk
        vectors = []
        for chunk in chunks:
            embedding = await llm_adapter.embed(chunk.text)
            vectors.append({
                "chunk_id": chunk.chunk_id,
                "vector": embedding,
                "metadata": chunk.metadata,
            })

        # 3. Extract entities for graph
        entities = await llm_adapter.extract_entities(doc.text)

        # 4. Store everything
        await doc_store.save_chunks(doc_id, chunks)
        await vector_store.add_vectors(vectors)
        await graph_store.add_nodes(entities["nodes"])
        await graph_store.add_edges(entities["edges"])
```

**Chunking Strategies**:
- **sentence_aware**: Split on sentence boundaries
- **fixed_size**: Fixed character count
- **page_based**: One chunk per page
- **semantic**: (future) Semantic segmentation

#### Module 3: Retrieval (Tri-Modal)

**Purpose**: Retrieve relevant chunks using three modalities

```python
class Retrieval:
    async def retrieve(
        self,
        query: str,
        profile: dict,
    ) -> RetrievalResults:
        # Modality 1: Vector search (semantic similarity)
        query_embedding = await llm_adapter.embed(query)
        vector_results = await vector_store.search(
            query_vector=query_embedding,
            top_k=profile["vector_top_k"],
        )

        # Modality 2: Document search (BM25 + TF-IDF)
        document_results = await self._document_search(
            query=query,
            top_k=profile["document_top_k"],
        )

        # Modality 3: Graph search (entity-based)
        graph_results = await self._graph_search(
            query=query,
            strategy=profile["graph_strategy"],
            top_k=profile["graph_top_k"],
        )

        return {
            "vector": vector_results,
            "document": document_results,
            "graph": graph_results,
        }
```

**Graph Search Strategies**:
- **entity_search**: Find entities matching query
- **traversal**: Start from entities, traverse graph
- **hybrid**: Combination of both

#### Module 4: Fusion

**Purpose**: Combine results from multiple modalities using Weighted RRF

```python
class Fusion:
    async def fuse(
        self,
        retrieval_results: dict,
        profile: dict,
    ) -> list[FusedResult]:
        # Reciprocal Rank Fusion (RRF)
        # Score = Σ (weight_i / (k + rank_i))

        scores = defaultdict(float)

        for modality, weight in weights.items():
            results = retrieval_results[modality]
            for rank, result in enumerate(results):
                chunk_id = result["chunk_id"]
                scores[chunk_id] += weight / (profile["rrf_k"] + rank + 1)

        # Sort by combined score
        fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Deduplicate similar chunks
        return self._deduplicate(fused, profile["dedup_threshold"])
```

**Why RRF?**
- Simple and effective
- No training required
- Handles different score ranges
- Proven in IR research

#### Module 5: Context Compilation

**Purpose**: Pack chunks into context within token budget

```python
class ContextCompiler:
    async def compile_context(
        self,
        chunk_ids: list[str],
        profile: dict,
    ) -> ContextPack:
        citations = []
        context_parts = []
        token_count = 0

        for i, chunk_id in enumerate(chunk_ids):
            chunk = await doc_store.get_chunk_by_id(chunk_id)

            # Check token budget
            chunk_tokens = llm_adapter.count_tokens(chunk.text)
            if token_count + chunk_tokens > profile["max_tokens"]:
                break

            # Add to context
            citation_num = i + 1
            context_parts.append(f"[{citation_num}] {chunk.text}")
            citations.append(Citation(
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                text=chunk.text,
                metadata=chunk.metadata,
            ))
            token_count += chunk_tokens

        # PII redaction if enabled
        context_text = "\n\n".join(context_parts)
        if profile["redact_pii"]:
            context_text = self._redact_pii(context_text)

        return ContextPack(
            context_text=context_text,
            citations=citations,
            total_tokens=token_count,
        )
```

**PII Redaction**:
- SSN: `\d{3}-\d{2}-\d{4}` → `[SSN]`
- Email: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` → `[EMAIL]`
- Phone: `\(\d{3}\) \d{3}-\d{4}` → `[PHONE]`
- Credit Card: `\d{4}-\d{4}-\d{4}-\d{4}` → `[CC]`

#### Module 6: Generation

**Purpose**: Generate answer using LLM with context

```python
class Generation:
    async def generate_answer(
        self,
        query: str,
        context_pack: ContextPack,
    ) -> Answer:
        prompt = f"""You are an insurance policy expert. Answer the user's question using ONLY the provided context.

Context:
{context_pack.context_text}

Question: {query}

Instructions:
1. Use ONLY information from the context
2. Cite sources using [1], [2], etc.
3. If context doesn't contain answer, say so
4. List any assumptions made
5. List any limitations

Answer:"""

        response = await llm_adapter.generate(
            prompt=prompt,
            system_prompt="You are a helpful insurance assistant.",
        )

        # Parse response into structured Answer
        return self._parse_answer(response, context_pack.citations)
```

**Structured Output**:
```python
Answer(
    answer_text="The policy provides...[1]",
    citations=[Citation(...)],
    confidence="high",  # Based on citation count and clarity
    assumptions=["Assuming standard policy form"],
    limitations=["Information from pages 1-3 only"],
)
```

#### Module 7: Judge (9 Validation Checks)

**Purpose**: Validate answer quality and safety

```python
class JudgeOrchestrator:
    async def validate(
        self,
        query: str,
        answer: Answer,
        profile: dict,
    ) -> JudgeReport:
        checks = []
        violations = []

        for check_name in profile["checks"]:
            check = self.checks[check_name]
            result = await check.validate(query, answer)
            checks.append(result)

            if not result.passed:
                violations.append(Violation(
                    check=check_name,
                    severity="hard" if check_name in profile["fail_on_violation"] else "soft",
                    message=result.message,
                ))

        # Determine overall decision
        hard_failures = [v for v in violations if v.severity == "hard"]
        if hard_failures:
            decision = "FAIL_BLOCKED"
        elif violations:
            decision = "FAIL_RETRYABLE"
        else:
            decision = "PASS"

        return JudgeReport(
            decision=decision,
            checks=checks,
            violations=violations,
            overall_score=self._compute_overall_score(checks),
        )
```

**9 Validation Checks**:

| Check | Type | Purpose |
|-------|------|---------|
| citation_coverage | Deterministic | All [N] references exist |
| groundedness | LLM | Claims supported by citations |
| hallucination | LLM | No fabricated information |
| relevance | LLM | Answer addresses query |
| consistency | LLM | No internal contradictions |
| toxicity | LLM | No offensive language |
| pii | Regex | No personal information |
| bias | LLM | No biased language |
| contradiction | LLM | No contradictions with citations |

### 5. Adapter Layer

**Swappable Implementations**:

#### FileDocStore
```python
class FileDocStore(DocStoreAdapter):
    def __init__(self, data_dir: str):
        self.docs_dir = f"{data_dir}/docs"
        self.chunks_dir = f"{data_dir}/chunks"

    async def save_document(self, doc: Document):
        path = f"{self.docs_dir}/{doc.doc_id}.json"
        async with aiofiles.open(path, 'w') as f:
            await f.write(doc.model_dump_json())
```

#### FAISSVectorStore
```python
class FAISSVectorStore(VectorStoreAdapter):
    def __init__(self, data_dir: str, dimension: int = 1536):
        self.index = faiss.IndexFlatIP(dimension)
        self.metadata = []

    async def add_vectors(self, vectors: list):
        vectors_array = np.array([v["vector"] for v in vectors])
        self.index.add(vectors_array)
        self.metadata.extend(vectors)
```

#### NetworkXGraph
```python
class NetworkXGraph(GraphStoreAdapter):
    def __init__(self, data_dir: str):
        self.graph = nx.DiGraph()

    async def add_nodes(self, nodes: list[Node]):
        for node in nodes:
            self.graph.add_node(
                node.node_id,
                entity_name=node.entity_name,
                entity_type=node.entity_type.value,
                **node.metadata,
            )
```

#### OpenAIAdapter
```python
class OpenAIAdapter(LLMAdapter):
    def __init__(self, config: dict):
        self.client = AsyncOpenAI(api_key=config["api_key"])
        self.model = config["model"]

    async def generate(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
```

---

## Data Flow

### Complete Pipeline Flow

```
1. Ingestion
   PDF File → pdfplumber → Document(pages[]) → FileDocStore

2. Indexing
   Document → Chunker → Chunks[]
           ↓
   Chunks → OpenAI embed → Vectors[] → FAISS
   Chunks → OpenAI extract → Entities → NetworkX Graph

3. Query Execution
   Query → OpenAI embed → query_vector
        ↓
   [Vector Search] query_vector → FAISS → Results[]
   [Doc Search]    query → BM25/TF-IDF → Results[]
   [Graph Search]  query → Entity Match → NetworkX → Results[]

4. Fusion
   [Vector Results, Doc Results, Graph Results] → Weighted RRF → Fused Results[]

5. Context Compilation
   Fused Results[] → Fetch Chunks → Pack within Token Budget → Context Pack

6. Generation
   (Query + Context Pack) → OpenAI generate → Answer

7. Validation
   (Query + Answer) → 9 Judge Checks → Judge Report → PASS/FAIL
```

---

## Configuration System

### Configuration Loader

```python
class ConfigLoader:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.cache = {}

    def get_profile(self, profile_type: str, profile_id: str) -> dict:
        cache_key = f"{profile_type}:{profile_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        path = f"{self.config_dir}/{profile_type}_profiles.json"
        with open(path) as f:
            profiles = json.load(f)

        if profile_id not in profiles:
            raise ValueError(f"Profile {profile_id} not found")

        profile = profiles[profile_id]
        self.cache[cache_key] = profile
        return profile

    def reload(self):
        self.cache.clear()
```

### Profile Examples

**Workflow Profile**:
```json
{
  "default": {
    "steps": [
      "retrieval",
      "fusion",
      "context_compilation",
      "generation",
      "validation"
    ],
    "timeout_seconds": 120,
    "retry_on_failure": false
  }
}
```

**Retrieval Profile**:
```json
{
  "balanced": {
    "vector_weight": 0.5,
    "document_weight": 0.3,
    "graph_weight": 0.2,
    "vector_top_k": 10,
    "document_top_k": 10,
    "graph_top_k": 5,
    "graph_strategy": "entity_search"
  }
}
```

---

## Validation Framework

### Check Interface

```python
class BaseCheck(ABC):
    def __init__(self, config: dict, llm_adapter: Optional[LLMAdapter] = None):
        self.config = config
        self.llm_adapter = llm_adapter

    @abstractmethod
    async def validate(self, query: str, answer: Answer) -> CheckResult:
        pass
```

### Example: Citation Coverage Check

```python
class CitationCoverageCheck(BaseCheck):
    async def validate(self, query: str, answer: Answer) -> CheckResult:
        # Extract citation references from answer text
        referenced = set(re.findall(r'\[(\d+)\]', answer.answer_text))

        # Check if all references have corresponding citations
        available = set(range(1, len(answer.citations) + 1))
        missing = referenced - {int(x) for x in available}

        # Calculate coverage score
        if not referenced:
            score = 1.0  # No citations referenced
        else:
            score = 1.0 - (len(missing) / len(referenced))

        passed = score >= self.config["threshold"]

        return CheckResult(
            check_name="citation_coverage",
            passed=passed,
            score=score,
            details={"missing_citations": list(missing)},
        )
```

---

## Observability & Telemetry

### Event Structure

```python
@dataclass
class Event:
    run_id: str
    timestamp: datetime
    step: str
    status: str  # started, completed, failed
    details: dict
    duration_ms: Optional[int] = None
```

### Event Emission

```python
class TelemetryService:
    async def emit_event(
        self,
        run_id: str,
        step: str,
        status: str,
        details: dict = None,
    ):
        event = Event(
            run_id=run_id,
            timestamp=datetime.now(),
            step=step,
            status=status,
            details=details or {},
        )

        # Save to file
        await self._save_event(event)

        # Stream via SSE
        await self._stream_event(event)

        # Log
        logger.info(f"[{run_id}] {step}: {status}")
```

---

## Storage Strategy

### File-Based Storage

```
data/
├── docs/               # Raw documents (JSON)
│   └── doc_abc123.json
├── chunks/             # Chunked text (JSON)
│   └── doc_abc123.json
├── vectors/            # FAISS index + metadata
│   ├── faiss.index
│   └── metadata.json
├── graph/              # NetworkX graph (JSON)
│   └── graph.json
└── runs/               # Pipeline execution logs
    └── run_xyz789.json
```

### Why File-Based?

**Pros**:
- Simple, no external dependencies
- Easy backup/restore
- Version control friendly
- Good for moderate scale

**Cons**:
- Not scalable to millions of documents
- No ACID transactions
- Limited concurrent access

**Production Alternative**:
- Documents: PostgreSQL
- Vectors: Pinecone, Weaviate, Qdrant
- Graph: Neo4j
- Runs: PostgreSQL or MongoDB

---

## Scaling Considerations

### Current Limits
- **Documents**: ~10,000 PDFs
- **Vectors**: ~1M embeddings
- **Graph**: ~100K nodes
- **Concurrent Queries**: ~10 req/s

### Horizontal Scaling

```
┌──────────────────────────────────────────────┐
│           Load Balancer (nginx)              │
└──────────────────────────────────────────────┘
         │             │             │
         ▼             ▼             ▼
    ┌─────────┐  ┌─────────┐  ┌─────────┐
    │ API #1  │  │ API #2  │  │ API #3  │
    └─────────┘  └─────────┘  └─────────┘
         │             │             │
         └──────────┬──────────┘
                    ▼
         ┌──────────────────────┐
         │  Shared Storage      │
         │  (S3, PostgreSQL)    │
         └──────────────────────┘
```

### Performance Optimizations

1. **Caching**: Redis for frequently accessed data
2. **Batching**: Batch embedding requests
3. **Async**: Full async/await throughout
4. **Connection Pooling**: DB connection pools
5. **CDN**: Static assets via CDN
6. **Compression**: Gzip responses

---

## Design Decisions

### Why FastAPI?
- Modern Python async framework
- Auto-generated OpenAPI docs
- Pydantic integration
- High performance
- SSE support

### Why Next.js?
- React Server Components
- File-based routing
- TypeScript support
- Built-in optimization
- API routes (not used here, but available)

### Why FAISS over Pinecone?
- No external dependencies
- Free and open-source
- Sufficient for prototype
- Easy to swap later

### Why File Storage over Database?
- Simplicity for demo
- No external dependencies
- Easy to inspect/debug
- Sufficient for prototype

### Why 9 Judge Checks?
- Comprehensive validation
- Inspired by research (Anthropic, OpenAI)
- Configurable (can disable checks)
- Safety-first approach

---

## Future Enhancements

### Planned
- Multi-modal support (images, tables)
- Streaming generation (token-by-token)
- Query rewriting
- Hybrid search tuning
- Fine-tuned embeddings
- Multi-tenancy

### Under Consideration
- Graph neural networks for graph retrieval
- Reinforcement learning for fusion weights
- Active learning for relevance feedback
- Multi-language support

---

## References

- **FAISS**: Facebook AI Similarity Search
- **RRF**: Reciprocal Rank Fusion (Cormack et al.)
- **RAG**: Retrieval-Augmented Generation (Lewis et al.)
- **Constitutional AI**: Anthropic research on safety
- **BM25**: Best Match 25 ranking function

---

**Questions? See [README.md](README.md) or open an issue.**
