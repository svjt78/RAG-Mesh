# Graph Search Retrieval Mechanism

This repository implements **graph-based retrieval** as a separate modality from vector and document search. It uses a knowledge graph stored in NetworkX and retrieves chunks by linking query entities to graph nodes, then traversing relationships to collect supporting evidence.

## Where the logic lives

- Retrieval module: `backend/app/modules/graph_retrieval.py`
- Graph store: `backend/app/adapters/networkx_graph_store.py`
- LLM adapter (entity extraction): `backend/app/adapters/openai_adapter.py`
- Orchestration entry point: `backend/app/core/orchestrator.py` (`_execute_retrieval`)

## High-level flow

1. **Entity linking from the query**
   - Load all entities from the graph store (`find_entities`).
   - Use an LLM to extract candidate entities from the user query.
   - Match candidate entities to graph nodes using exact substring checks and fuzzy string similarity.

2. **Subgraph extraction**
   - Run BFS from matched entity nodes up to `graph_max_hops` (from `RetrievalProfile`).
   - Return a subgraph with nodes and edges.

3. **Supporting chunk retrieval**
   - Collect `chunk_ids` from matched nodes and their connected edges (`evidence_chunk_ids`).

4. **Scoring and ranking**
   - Score chunks by how many entity mentions/evidence links they contain.
   - Boost chunks that support seed entities.

## LLM used for entity extraction

Graph retrieval uses the `OpenAIAdapter`, which defaults to:

- Generation/extraction model: **`gpt-3.5-turbo`**
- Embedding model (not used here): `text-embedding-3-small`

Entity extraction is done via `llm.extract_entities(...)` and returns a structured JSON payload with entity labels and types.

## LLM + fuzzy matching responsibilities

- **LLM responsibility**: Propose candidate entities present in the query text.
- **Fuzzy matching responsibility**: Link those candidates to **existing graph nodes** by comparing labels.

Matching logic in `GraphRetrievalModule._link_entities()`:

- Exact substring match: if a graph entity label appears in the query text, it is selected.
- Fuzzy match: if `SequenceMatcher(...).ratio() > 0.8`, it is selected.

## How `SequenceMatcher` works

`difflib.SequenceMatcher` compares two strings by finding matching subsequences and computing a similarity ratio:

```
ratio = 2.0 * M / T
```

- `M`: total number of matching characters across all matching blocks
- `T`: total length of both strings combined

A ratio of **1.0** is identical; **0.0** is no overlap. The graph retrieval code uses **0.8** as the cutoff for a match.

## Graph storage format (no embeddings)

The graph is stored as JSONL files in `data/graph/`:

- `nodes.jsonl`: node records with `node_id`, `label`, `node_type`, `properties`, `chunk_ids`
- `edges.jsonl`: edge records with `source`, `target`, `edge_type`, `properties`, `evidence_chunk_ids`

The graph is **not** converted to vector embeddings for storage or retrieval.

## Related configuration

Graph retrieval uses fields in `RetrievalProfile` (`backend/app/core/models.py`):

- `graph_max_hops`
- `graph_entity_types`

These control how far the BFS travels and which entity types are considered during linking.
