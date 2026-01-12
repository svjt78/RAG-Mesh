# RAG Production Scaling Framework Prototype (Insurance) — **RAGMesh** Spec

> **Objective:** Build a fully working, fully dockerized app/prototype that demonstrates how to **productionize and scale Insurance RAG (Retrieval Augmented Generation)** with **high-quality retrieval (vector + graph + document)**, **end-to-end observability**, and **mandatory validation/judging gates** (hallucination, groundedness, bias, relevance, consistency, toxicity, PII leakage, citation coverage, contradiction detection).  
>
> **Key constraints (v1):**
> - **PDF-only** document support
> - **No database required** for the default prototype (JSON/file-based storage)
> - **OpenAI GPT-3.5-turbo** for:
>   - answer generation
>   - embeddings
>   - graph extraction
>   - judge/critique
> - **100% configurable** behavior via registries (JSON/YAML)
> - Multi-tenant isolation is **not required** (can be added later)

---

## 1) Product Summary

### What this prototype proves
1. **RAG platform agnostic productionization**: A modular framework that can be wired to any RAG stack, but ships with **file-based adapters** (no DB).
2. **Retrieval beyond semantic-only**: Combines:
   - **Vector retrieval** (semantic similarity)
   - **Graph retrieval** (entity/relationship-aware)
   - **Document retrieval** (keyword/BM25-style + metadata filters)
3. **Hard quality gates**: Answers are **blocked** unless they pass a comprehensive judge policy covering:
   - groundedness
   - hallucination
   - bias
   - context relevance
   - consistency
   - toxicity
   - PII leakage
   - citation coverage
   - contradiction detection
4. **Executive-grade transparency**: UI shows:
   - timeline replay
   - token/cost analytics
   - retrieval explainability
   - context pack (exact prompt context)
   - judge report (scores, failures, claim→evidence mapping)

---

## 2) Architectural Principles

1. **Registry-first configuration**
   - All runtime behavior is driven by config files under `/config/`
   - No code changes required to alter retrieval, fusion, context building, judge thresholds, etc.

2. **Loosely coupled modules via interfaces**
   - Each major capability is behind an adapter interface:
     - `DocStoreAdapter`
     - `VectorStoreAdapter`
     - `GraphStoreAdapter`
     - `RerankAdapter`
     - `LLMAdapter`
     - `JudgeAdapter`

3. **Artifact-first execution**
   - Every run writes a complete auditable bundle:
     - retrieval bundle (vector/graph/doc + fused ranking)
     - context pack (exact compiled context + tokens)
     - answer (structured + citations)
     - judge report (scores, violations, decision)
     - event stream (timeline replay)

4. **Bounded execution controls**
   - Strict caps per run:
     - max chunks per modality
     - graph hop limit
     - max context tokens
     - max judge tokens
     - timeouts per step
     - cost/token budgets

5. **Fail-closed safety**
   - If judge fails any “hard-fail” check, response is not released.
   - UI displays a blocked response card + remediation hints.

---

## 3) System Overview (Dockerized)

### Services
1. **`ragmesh-api` (FastAPI)**
   - Orchestrates ingestion, indexing, retrieval, fusion, context compile, generation, judge, persistence
   - Emits **SSE** events for live timeline
   - Exposes run artifacts for UI

2. **`ragmesh-ui` (Next.js + Tailwind)**
   - Multi-tab interface: Run Console, Timeline, Retrieval, Graph, Context Pack, Answer, Judge, Observability, Runs Library/Replay

3. **Optional Observability Profile**
   - `otel-collector` + `prometheus` + `grafana`
   - Not required for correctness (JSONL artifacts remain the source of truth), but strongly recommended for demos.

### Docker Compose Requirements
- Full hot-reload for frontend and backend
- A **single root `.env`** file used by both services
- Mounted persistent volume `./data:/app/data`
- Mounted configuration volume `./config:/app/config`

---

## 4) Storage (No Database Required)

### Default file-based storage layout
All persisted under `./data`:

- **Documents**
  - `data/docs/{doc_id}.json`  
    Contains metadata + extracted PDF text by page + derived annotations.
  - `data/docs/index.json`  
    Catalog for filtering and discovery.

- **Chunks**
  - `data/chunks/{doc_id}.jsonl`  
    Each line is a chunk record with provenance: `{chunk_id, doc_id, page_no, offsets, text, tokens_estimate, metadata}`

- **Vectors**
  - `data/vectors/embeddings.bin` or `data/vectors/embeddings.npy` (implementation choice)
  - `data/vectors/chunk_meta.jsonl` (chunk_id → metadata/provenance)
  - `data/vectors/index.faiss` (optional file-based index, still “no DB container”)

- **Graph**
  - `data/graph/nodes.jsonl`
  - `data/graph/edges.jsonl`
  - `data/graph/adjacency.json`

- **Runs / Artifacts**
  - `data/runs/{run_id}/events.jsonl`
  - `data/runs/{run_id}/artifacts/retrieval_bundle.json`
  - `data/runs/{run_id}/artifacts/context_pack.json`
  - `data/runs/{run_id}/artifacts/answer.json`
  - `data/runs/{run_id}/artifacts/judge_report.json`
  - `data/runs/{run_id}/artifacts/config_snapshot.json`

> **Note:** The design keeps storage behind adapters, so dedicated stores (Milvus/Neo4j/OpenSearch) can be introduced later without changing orchestration logic.

---

## 5) Configuration (100% Configurable)

### Registry files (under `/config`)
- `workflows.json`  
  Defines step ordering, fallback strategies, and gating rules.

- `models.json`  
  Defines OpenAI model profiles:
  - `llm_model`: `gpt-3.5-turbo`
  - `embedding_model`: OpenAI embeddings model (configurable)
  - per-step budgets and timeouts

- `chunking_profiles.json`  
  Chunk size/overlap; page-aware chunking; max chunks per doc.

- `retrieval_profiles.json`  
  Per modality:
  - vector: `k`, filters, similarity threshold
  - doc: keyword weighting, BM25 params, filters
  - graph: hop limit, relation allowlist, entity types

- `fusion_profiles.json`  
  Fusion method (e.g., RRF), weights, diversity rules, dedupe rules.

- `context_profiles.json`  
  Context token budget, compression strategy, citation-first packing policy, redaction rules.

- `judge_profiles.json`  
  Mandatory checks, thresholds, weights, hard-fail list, remediation rules.

- `telemetry.json`  
  Event verbosity, metrics toggles, sampling policies.

### Runtime overrides
- API request body can include an `overrides` object to temporarily override profile parameters (bounded by server policy).

---

## 6) PDF Ingestion & Indexing

### 6.1 PDF extraction
- Extract text **by page** (page anchoring is mandatory for citations).
- Persist page text to `data/docs/{doc_id}.json`.

### 6.2 Chunking (page-aware)
- Chunk per page with overlap.
- Each chunk stores:
  - `chunk_id`
  - `doc_id`
  - `page_no`
  - `char_start`, `char_end`
  - `text`
  - `metadata` (form number, state, effective dates, doc type, etc.)
  - `tokens_estimate`

### 6.3 Embeddings (OpenAI)
- Generate embeddings per chunk using OpenAI embeddings model specified in `models.json`.
- Store embeddings in file-based vector storage.
- Maintain stable mapping `chunk_id → embedding vector`.

### 6.4 Graph extraction (OpenAI)
- For each document (or per page), run a structured extraction prompt to produce:
  - entities (nodes)
  - relationships (edges)
  - evidence pointers (chunk_id/page provenance)
- Output schema is strict JSON, validated server-side.
- Persist to `data/graph/*`.

**Graph schema (example)**
- Node types:
  - `Coverage`, `Exclusion`, `Condition`, `Endorsement`, `Form`, `Definition`, `State`, `Term`, `Entity`
- Edge types:
  - `AMENDS`, `EXCLUDES`, `SUBJECT_TO`, `APPLIES_IN`, `REFERENCES`, `DEFINES`, `EXCEPTION_TO`

---

## 7) Retrieval (Vector + Graph + Document)

### 7.1 Vector retrieval
Inputs:
- `query_text`
- `filters` (metadata)
- `k`
- `similarity_threshold`

Outputs:
- ranked chunks with similarity scores and provenance

### 7.2 Document retrieval (keyword/BM25-style)
Inputs:
- `query_text`
- `filters`
- `k`

Outputs:
- ranked chunks/pages with keyword match scores
- boosts for exact matches: form numbers, clause IDs, defined terms

### 7.3 Graph retrieval (hop-limited)
Steps:
1. Identify query entities (LLM-based entity linker, bounded)
2. Expand neighborhood with hop limit `H`
3. Retrieve supporting chunks linked to relevant nodes/edges
4. Return:
   - subgraph (nodes/edges used)
   - supporting chunk list with provenance

### 7.4 Fusion & reranking
Config-driven:
- Fusion method: **Weighted RRF** (default)
- Diversity constraints:
  - max N chunks per doc
  - enforce ≥M distinct docs where available
- Dedup rules:
  - near-duplicate chunk removal
- Optional LLM rerank (bounded by budget)

---

## 8) Context Compiler (Token-Aware, Citation-First)

### Inputs
- fused candidate chunks (+ provenance)
- context profile:
  - max tokens
  - compression strategy
  - citation policy

### Responsibilities
- Build final context within strict token budget
- Ensure each included snippet has provenance:
  - `doc_id`, `page_no`, `chunk_id`
- Maintain a **Context Pack** artifact:
  - ordered list of included chunks
  - token estimates per chunk
  - dedupe notes
  - coverage summary (question facets → evidence coverage)
  - redactions applied (if any)

### Output
- `context_text` (exact string used for generation)
- `context_pack.json` artifact persisted per run

---

## 9) Answer Generation (OpenAI GPT-3.5-turbo)

### Output contract (strict JSON)
The generator must return:

```json
{
  "answer": "string",
  "citations": [
    {"chunk_id":"...", "doc_id":"...", "page_no": 3, "quote":"...", "reason":"..."}
  ],
  "assumptions": ["..."],
  "limitations": ["..."],
  "confidence": "low|medium|high"
}
```

Rules:
- Every major claim must be backed by ≥1 citation.
- If evidence is insufficient, the model must say so and provide “what is missing”.
- No hidden chain-of-thought is stored; only structured outputs and evidence mappings.

---

## 10) Judge / Validation Gate (All Checks Mandatory)

### 10.1 Judge model
- Uses **OpenAI GPT-3.5-turbo** to evaluate outputs against evidence.
- Combines:
  - LLM rubric scoring
  - deterministic detectors (PII regex, citation coverage calculation, etc.)
- Produces a single **Judge Report** with:
  - per-check score
  - violations
  - claim→evidence mapping
  - pass/fail decision
  - remediation recommendations

### 10.2 Required checks

1. **Citation Coverage**
   - Metric: % of sentences/claims with citations
   - Hard fail if below threshold.

2. **Groundedness**
   - For each claim: does cited evidence entail/support the claim?
   - Output: mapping `{claim: [supporting_citations], grounded: true/false}`

3. **Hallucination Detection**
   - Flags claims not present in evidence
   - Flags fabricated numbers/entities

4. **Context Relevance**
   - Do retrieved snippets address the question facets?
   - Detect retrieval drift.

5. **Consistency**
   - Generate 2–3 bounded samples and judge agreement; or judge internal coherence.
   - Flag contradictory statements in the answer.

6. **Toxicity**
   - LLM rubric + optional classifier hook
   - Hard fail for severe toxicity.

7. **PII Leakage**
   - Regex + LLM rubric for PII exposure (SSN, DOB, phone, address, etc.)
   - If PII present and policy forbids → hard fail (or require redaction + regenerate).

8. **Bias**
   - Rubric for biased or unfair language/inferences.
   - Hard fail thresholds configurable.

9. **Contradiction Detection**
   - Answer vs evidence contradictions
   - Internal contradictions in answer

### 10.3 Gate outcomes
- `PASS`: answer is released
- `FAIL_BLOCKED`: answer is blocked; UI shows judge report and remediation hints
- Optional (configurable): `FAIL_RETRYABLE` to auto-retry with a stricter retrieval/context profile

---

## 11) Observability, Monitoring, and Replay

### 11.1 Event stream (SSE) + JSONL persistence
Each run writes `events.jsonl` and streams live events.

Event examples:
- `run_started`
- `retrieval_vector_completed`
- `retrieval_graph_completed`
- `retrieval_doc_completed`
- `fusion_completed`
- `context_compiled`
- `generation_completed`
- `judge_completed`
- `run_completed`

Each event includes:
- `run_id`, `step`, `timestamp`, `duration_ms`
- token usage (prompt/completion) and cost estimates
- counts (chunks retrieved/selected/deduped)
- config profile IDs + config snapshot hash

### 11.2 Run bundle export
- UI provides “Download run bundle”:
  - retrieval bundle
  - context pack
  - answer
  - judge report
  - events
  - config snapshot

### 11.3 Metrics endpoint
Expose `/metrics` for:
- latency per step
- retrieval KPIs (diversity, hit rates, similarity distributions)
- judge pass rates by policy
- blocked response reasons
- token/cost per run

Optional dashboards (Grafana):
- cost trends
- failure breakdown
- retrieval quality over time

---

## 12) Frontend (Executive Multi-Tab UI)

### 12.1 Must-have UX characteristics
- Live run timeline with step-level expansion
- Drill-down into retrieval decisions
- Exact context view (what the model saw)
- Judge report with claim-level grounding
- Token and cost analytics per step
- Replay past runs deterministically from stored artifacts

### 12.2 Pages & Tabs

1. **Run Console**
   - query input
   - dropdowns: workflow, retrieval profile, context profile, judge profile
   - optional bounded overrides (k, hop limit, token budget)
   - run button triggers `/api/run` and opens SSE stream

2. **Timeline**
   - event list + durations + status badges
   - expandable event payload view

3. **Retrieval Explorer**
   - tabs: Vector / Graph / Document / Fused
   - show topK lists with scores and provenance
   - “Why selected” panel (fusion/rerank rationale)

4. **Graph Viewer**
   - visualize subgraph used for retrieval
   - node/edge click reveals supporting chunks/pages

5. **Context Pack**
   - exact compiled context
   - chunk list with token counts
   - coverage indicators
   - redaction indicators (if applied)

6. **Answer**
   - answer rendering with inline citations
   - click citation → open page text preview

7. **Judge Report**
   - scorecards for each check
   - hard-fail reasons
   - claim→evidence table
   - remediation recommendations
   - blocked response UI state when failed

8. **Observability**
   - token/cost by step
   - latency charts
   - judge failure trends
   - export run bundle

9. **Runs Library**
   - list/search past runs
   - open replay

---

## 13) API (High-Level)

- `POST /api/ingest/pdf`
  - multipart PDF upload
  - returns `{doc_id}`

- `POST /api/index/{doc_id}`
  - runs chunking + embeddings + graph extraction + doc index build
  - returns indexing status

- `POST /api/run`
  - request body:
    - `query`
    - `workflow_id`
    - `retrieval_profile_id`
    - `context_profile_id`
    - `judge_profile_id`
    - `overrides` (optional, bounded)
  - returns `{run_id}`

- `GET /api/run/{run_id}/events` (SSE)
  - live and replay streaming

- `GET /api/run/{run_id}/artifact/{name}`
  - `retrieval_bundle | context_pack | answer | judge_report | config_snapshot`

- `GET /api/runs`
  - list/search runs

---

## 14) Security & Governance (v1)

- No multi-tenant isolation required.
- Minimal governance included:
  - redaction rules (PII patterns)
  - configurable “allowed document types/tags” enforcement
  - full audit trail via artifacts/events
- Authentication optional for prototype; can be added as a module.

---

## 15) Implementation Constraints & Non-Functional Requirements

- Deterministic storage formats for reproducible demos
- Config snapshot per run to guarantee replay fidelity
- Strict schema validation on all LLM outputs:
  - graph extraction JSON schema
  - generation output schema
  - judge output schema
- Timeouts and budget enforcement are mandatory
- “Fail closed” behavior by default when judge is uncertain or evidence is insufficient

---

## 16) Dockerization Deliverables (Required)

### Required files
- `docker-compose.yml`
  - services: `ragmesh-api`, `ragmesh-ui`
  - optional profiles: `observability` (otel/prom/grafana)

- Root `.env` file (single file shared by backend & frontend)
  - `OPENAI_API_KEY=...`
  - `OPENAI_MODEL=gpt-3.5-turbo`
  - `OPENAI_EMBEDDING_MODEL=...`
  - budgets/timeouts defaults
  - ports

### Required behaviors
- hot reload backend
- hot reload frontend
- `./data` persisted across restarts
- all config files read from `./config`

---

## 17) Example Demo Flow (Insurance)

1. Upload a PDF policy form/endorsement
2. Index it (chunks + embeddings + graph extraction + keyword index)
3. Ask: “Is water backup covered under form X with endorsement Y?”
4. Observe:
   - vector hits vs keyword hits vs graph-driven connections
   - fused ranking selection reasons
   - context pack token budget decisions
5. Answer is generated with citations
6. Judge evaluates all checks; pass releases answer, fail blocks with detailed explanation
7. Replay the run from Runs Library and export the run bundle

---

## 18) Future Extensions (Not required for v1)
- Multi-tenant isolation & per-tenant policy rules
- Dedicated stores via adapters (Milvus/Neo4j/OpenSearch)
- Batch pipelines and scheduled evaluations
- Model evaluation harness across datasets
- Canary deployments and A/B retrieval profile testing

---

# Appendix A — Key Artifacts (Schemas)

## A1) Retrieval Bundle (high level)
```json
{
  "run_id": "...",
  "query": "...",
  "vector_results": [{"chunk_id":"...", "score":0.0, "doc_id":"...", "page_no":1}],
  "doc_results": [{"chunk_id":"...", "score":0.0, "doc_id":"...", "page_no":1}],
  "graph_results": {
    "subgraph": {"nodes":[...], "edges":[...]},
    "supporting_chunks":[{"chunk_id":"...", "doc_id":"...", "page_no":1}]
  },
  "fused_results": [{"chunk_id":"...", "rank":1, "fusion_score":0.0, "reasons":["..."]}]
}
```

## A2) Judge Report (high level)
```json
{
  "decision": "PASS|FAIL_BLOCKED|FAIL_RETRYABLE",
  "scores": {
    "citation_coverage": 0.0,
    "groundedness": 0.0,
    "hallucination": 0.0,
    "relevance": 0.0,
    "consistency": 0.0,
    "toxicity": 0.0,
    "pii_leakage": 0.0,
    "bias": 0.0,
    "contradiction": 0.0
  },
  "violations": [{"type":"...", "severity":"low|med|high", "details":"..."}],
  "claim_evidence_map": [{"claim":"...", "citations":[{"chunk_id":"...", "page_no":1}], "grounded":true}],
  "remediation": ["..."]
}
```
