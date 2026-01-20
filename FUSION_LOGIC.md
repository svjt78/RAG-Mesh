# Fusion Logic Documentation

This document explains how RAGMesh calculates and combines scores from three retrieval modalities (Vector, Document, Graph) using Weighted Reciprocal Rank Fusion (RRF).

## Overview

RAGMesh uses **tri-modal retrieval** to find relevant chunks:

```
Query → [Vector Search] → V scores
      → [Document Search] → D scores  → [Fusion (RRF)] → Final Ranked Results
      → [Graph Search] → G scores
```

Each modality produces its own relevance scores, which are then combined using rank-based fusion.

---

## Modality Score Calculations

### Vector Score (V)

**Source:** `backend/app/modules/vector_retrieval.py`

Vector search uses semantic similarity via embeddings.

#### Calculation

```python
# 1. Generate query embedding using LLM
query_embeddings = await self.llm.embed([query])
query_embedding = query_embeddings[0]

# 2. Search FAISS index - returns cosine similarity
results = await self.vector_store.search(
    query_embedding=query_embedding,
    k=profile.vector_k,
    threshold=profile.vector_threshold
)

# 3. Score is the raw cosine similarity
score = result["score"]  # Range: 0.0 to 1.0
```

#### Formula

```
V = cosine_similarity(query_embedding, chunk_embedding)
```

#### Characteristics

| Property | Value |
|----------|-------|
| Range | 0.0 to 1.0 |
| Source | FAISS vector store |
| Embedding Model | Configured in `config/models.json` (default: `text-embedding-3-small`) |

---

### Document Score (D)

**Source:** `backend/app/modules/doc_retrieval.py`

Document search uses keyword matching with BM25 and TF-IDF, plus boosting factors.

#### Step 1: BM25 Scores (lines 140-152)

```python
def _get_bm25_scores(self, query: str) -> np.ndarray:
    tokenized_query = query.lower().split()
    scores = self.bm25.get_scores(tokenized_query)

    # Normalize to 0-1 range
    if scores.max() > 0:
        scores = scores / scores.max()
    return scores
```

BM25 (Best Matching 25) is a probabilistic ranking function that scores documents based on term frequency and inverse document frequency.

#### Step 2: TF-IDF Scores (lines 154-171)

```python
def _get_tfidf_scores(self, query: str) -> np.ndarray:
    query_vector = self.tfidf.transform([query])
    doc_vectors = self.tfidf.transform([
        chunk.get("text", "") for chunk in self.chunks_cache
    ])

    # Cosine similarity between query and document vectors
    scores = cosine_similarity(query_vector, doc_vectors)[0]
    return scores
```

TF-IDF uses n-grams (1-2) with English stop words removed.

#### Step 3: Weighted Combination (line 103)

```python
combined_scores = 0.6 * bm25_scores + 0.4 * tfidf_scores
```

#### Step 4: Boost Factors (lines 173-212)

```python
# Exact keyword match boost
if query_lower in chunk_text:
    boosted_scores[idx] *= profile.doc_boost_exact_match  # default: 1.5

# Form number match boost (insurance-specific)
if form_number and form_number.lower() in query_lower:
    boosted_scores[idx] *= profile.doc_boost_form_number  # default: 2.0

# Defined term match boost (quoted terms in query)
if '"' in query and query.strip('"').lower() in chunk_text:
    boosted_scores[idx] *= profile.doc_boost_defined_term  # default: 1.8
```

#### Formula

```
D = (0.6 × BM25_normalized + 0.4 × TF-IDF_cosine) × boost_multipliers
```

Where boost_multipliers can stack:
- `doc_boost_exact_match`: 1.5x (query text found in chunk)
- `doc_boost_form_number`: 2.0x (form number matches)
- `doc_boost_defined_term`: 1.8x (quoted terms match)

#### Characteristics

| Property | Value |
|----------|-------|
| Range | 0.0 to ~5.4 (with all boosts stacked) |
| BM25 Weight | 60% |
| TF-IDF Weight | 40% |
| TF-IDF Features | max 5000, unigrams + bigrams |

---

### Graph Score (G)

**Source:** `backend/app/modules/graph_retrieval.py`

Graph search uses entity relationships from the knowledge graph.

#### Step 1: Entity Linking (lines 133-201)

```python
# Extract entities from query using LLM
llm_result = await self.llm.extract_entities(
    text=query,
    entity_types=profile.graph_entity_types
)

# Fuzzy match against graph entities
for graph_entity in all_entities:
    entity_label = graph_entity.get("label", "").lower()

    # Exact match
    if entity_label in query_lower:
        entity_ids.append(entity_id)

    # Fuzzy match (>80% similarity)
    similarity = SequenceMatcher(None, query_entity, entity_label).ratio()
    if similarity > 0.8:
        entity_ids.append(entity_id)
```

#### Step 2: Subgraph Extraction

```python
subgraph_data = await self.graph_store.query_subgraph(
    entity_ids=entity_ids,
    max_hops=profile.graph_max_hops  # default: 2
)
```

#### Step 3: Count Entity Mentions (lines 236-244)

```python
chunk_entity_counts: Dict[str, int] = {}

# Count from nodes
for node in subgraph_data.get("nodes", []):
    for chunk_id in node.get("chunk_ids", []):
        chunk_entity_counts[chunk_id] = chunk_entity_counts.get(chunk_id, 0) + 1

# Count from edge evidence
for edge in subgraph_data.get("edges", []):
    for chunk_id in edge.get("evidence_chunk_ids", []):
        chunk_entity_counts[chunk_id] = chunk_entity_counts.get(chunk_id, 0) + 1
```

#### Step 4: Normalize and Boost (lines 246-264)

```python
max_count = max(chunk_entity_counts.values()) if chunk_entity_counts else 1

for chunk_id in chunk_ids:
    entity_count = chunk_entity_counts.get(chunk_id, 0)
    score = entity_count / max_count if max_count > 0 else 0.0

    # Boost 1.5x if chunk supports seed entities (query-linked)
    for node in subgraph_data.get("nodes", []):
        if chunk_id in node.get("chunk_ids", []):
            if node.get("node_id") in entity_ids:
                score *= 1.5

    score = min(score, 1.0)  # Cap at 1.0
```

#### Formula

```
G = min((entity_mentions / max_mentions) × seed_boost, 1.0)
```

Where:
- `entity_mentions`: Count of graph entities mentioned in chunk
- `max_mentions`: Maximum count across all chunks
- `seed_boost`: 1.5 if chunk mentions a query-linked entity, else 1.0

#### Characteristics

| Property | Value |
|----------|-------|
| Range | 0.0 to 1.0 (capped) |
| Seed Entity Boost | 1.5x |
| Max Hops | Configurable (default: 2) |
| Fuzzy Match Threshold | 0.8 |

---

## Fusion: Weighted Reciprocal Rank Fusion (RRF)

**Source:** `backend/app/modules/fusion.py`

The individual V, D, G scores are **displayed in the UI** but are **not directly used** for final ranking. Instead, **rank-based fusion** is applied.

### Why RRF Instead of Score Averaging?

1. **Incompatible score ranges**: BM25 scores are unbounded, while cosine similarity is 0-1
2. **Ranks are comparable**: Position 1 means "best" regardless of modality
3. **No training required**: Works out of the box
4. **Proven effectiveness**: Well-established in information retrieval research

### RRF Formula

For each chunk that appears in retrieval results:

```
Final_Score = Σ (Weight_i / (K + Rank_i))
```

Where:
- `Weight_i`: Modality weight from fusion profile
- `K`: RRF constant (default: 60)
- `Rank_i`: Position in that modality's results (1-indexed)

### Implementation (lines 48-82)

```python
# Initialize chunk scores
chunk_scores: Dict[str, Dict] = {}

# Add vector RRF contributions
for result in vector_results:
    chunk_id = result.chunk_id
    rrf_score = profile.vector_weight / (profile.rrf_k + result.rank)

    if chunk_id not in chunk_scores:
        chunk_scores[chunk_id] = {"rrf_score": 0, "vector_score": 0, ...}

    chunk_scores[chunk_id]["rrf_score"] += rrf_score
    chunk_scores[chunk_id]["vector_score"] = result.score

# Add document RRF contributions
for result in document_results:
    chunk_id = result.chunk_id
    rrf_score = profile.document_weight / (profile.rrf_k + result.rank)

    chunk_scores[chunk_id]["rrf_score"] += rrf_score
    chunk_scores[chunk_id]["document_score"] = result.score

# Add graph RRF contributions
for result in graph_results:
    chunk_id = result.chunk_id
    rrf_score = profile.graph_weight / (profile.rrf_k + result.rank)

    chunk_scores[chunk_id]["rrf_score"] += rrf_score
    chunk_scores[chunk_id]["graph_score"] = result.score
```

### Calculation Example

Consider a chunk appearing in all three modalities:

| Modality | Rank | Weight | K | RRF Contribution |
|----------|------|--------|---|------------------|
| Vector | 5 | 1.0 | 60 | 1.0 / (60 + 5) = 0.0154 |
| Document | 3 | 1.0 | 60 | 1.0 / (60 + 3) = 0.0159 |
| Graph | 1 | 1.0 | 60 | 1.0 / (60 + 1) = 0.0164 |

**Final Score = 0.0154 + 0.0159 + 0.0164 = 0.0477**

### Why Scores Are Small (~0.03)

The RRF formula produces small scores by design:
- With K=60, even rank 1 yields only `weight / 61 ≈ 0.016`
- This is intentional - it makes the formula robust to outliers
- What matters is the **relative ordering**, not absolute values

---

## Post-Fusion Processing

After RRF calculation, additional processing is applied:

### 1. Sort by RRF Score

```python
sorted_chunks = sorted(chunk_scores.items(), key=lambda x: x[1]["rrf_score"], reverse=True)
```

### 2. Diversity Constraints (if enabled)

```python
if profile.apply_diversity_constraints:
    # Maximum chunks per document
    max_per_doc = profile.max_chunks_per_doc  # default: 3

    # Minimum distinct documents
    min_docs = profile.min_distinct_docs  # default: 2
```

### 3. Deduplication

```python
# Remove near-duplicate chunks
dedup_threshold = profile.dedup_threshold  # default: 0.95
```

### 4. Final Top-K Selection

```python
final_results = sorted_chunks[:profile.final_top_k]  # default: 20
```

---

## Configuration

### Fusion Profiles

**File:** `config/fusion_profiles.json`

```json
{
  "balanced": {
    "vector_weight": 1.0,
    "document_weight": 1.0,
    "graph_weight": 1.0,
    "rrf_k": 60,
    "max_chunks_per_doc": 3,
    "min_distinct_docs": 2,
    "dedup_threshold": 0.95,
    "apply_diversity_constraints": true,
    "final_top_k": 20
  },
  "vector_heavy": {
    "vector_weight": 2.0,
    "document_weight": 1.0,
    "graph_weight": 0.8,
    "rrf_k": 60,
    ...
  },
  "keyword_focused": {
    "vector_weight": 0.8,
    "document_weight": 2.0,
    "graph_weight": 1.0,
    "rrf_k": 60,
    ...
  }
}
```

### Retrieval Profiles

**File:** `config/retrieval_profiles.json`

Controls per-modality retrieval parameters:

```json
{
  "balanced_insurance": {
    "vector_k": 20,
    "vector_threshold": 0.5,
    "doc_k": 20,
    "doc_boost_exact_match": 1.5,
    "doc_boost_form_number": 2.0,
    "doc_boost_defined_term": 1.8,
    "graph_max_hops": 2,
    "graph_entity_types": ["Coverage", "Exclusion", "Definition", "Condition"]
  }
}
```

---

## UI Display

### Fusion Tab

The frontend displays both:
- **Final Score**: The RRF-calculated score used for ranking
- **V, D, G Badges**: Original modality scores for transparency

Badges only appear if the chunk was retrieved by that modality (score > 0).

**Source:** `frontend/components/FusionTab.tsx`

---

## Summary Table

| Component | Formula | Range | Purpose |
|-----------|---------|-------|---------|
| **V Score** | `cosine_similarity(query, chunk)` | 0-1 | Semantic relevance |
| **D Score** | `(0.6×BM25 + 0.4×TF-IDF) × boosts` | 0-5.4 | Keyword relevance |
| **G Score** | `min((mentions/max) × 1.5, 1.0)` | 0-1 | Entity relevance |
| **Final Score** | `Σ(weight / (K + rank))` | ~0.01-0.05 | Combined ranking |

---

## Code References

| File | Purpose |
|------|---------|
| `backend/app/modules/vector_retrieval.py` | Vector (V) score calculation |
| `backend/app/modules/doc_retrieval.py` | Document (D) score calculation |
| `backend/app/modules/graph_retrieval.py` | Graph (G) score calculation |
| `backend/app/modules/fusion.py` | RRF fusion logic |
| `backend/app/core/models.py` | FusionProfile, RetrievalProfile models |
| `config/fusion_profiles.json` | Fusion weight configuration |
| `config/retrieval_profiles.json` | Per-modality retrieval configuration |
| `frontend/components/FusionTab.tsx` | UI display logic |
