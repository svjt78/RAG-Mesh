# Retrieval and Generation Summary

## 1. What databases are used for vector, graph and document based retrieval?

- Vector: FAISS index stored on disk under `data/vectors`, via `FAISSVectorStoreAdapter` in `backend/app/adapters/faiss_vector_store.py`.
- Graph: NetworkX `MultiDiGraph` persisted to JSON in `data/graph`, via `NetworkXGraphStoreAdapter` in `backend/app/adapters/networkx_graph_store.py`.
- Document: file-based JSON/JSONL store in `data/docs` and `data/chunks`, via `FileDocStoreAdapter` in `backend/app/adapters/file_doc_store.py`. Retrieval uses BM25 + TF-IDF over cached chunks in `backend/app/modules/doc_retrieval.py`.

## 2. What embedding model is used?

- Default embedding model is `text-embedding-3-small` (OpenAI), defined in `config/models.json` and used by `OpenAIAdapter` in `backend/app/adapters/openai_adapter.py`.

## 3. What generation model is used?

- Default generation model is `gpt-3.5-turbo`, defined in `config/models.json` and used by `OpenAIAdapter.generate` in `backend/app/adapters/openai_adapter.py`.

## 4. How reranking is done?

- Optional LLM-based reranking in `backend/app/modules/fusion.py`: builds a prompt with chunk excerpts, asks the LLM to return a JSON ranking array, then reorders results accordingly. Enabled/disabled by workflow config (`enable_reranking`) in `config/workflows.json`.

## 5. How fusion is done?

- Weighted Reciprocal Rank Fusion (RRF) across vector, document, and graph results in `backend/app/modules/fusion.py`, with weights and parameters from `config/fusion_profiles.json`. After RRF, it applies diversity constraints (`max_chunks_per_doc`, `min_distinct_docs`), simple text-based dedup, and top-K truncation.

## 6. How judge is working?

- The judge runs 9 checks via `JudgeOrchestrator` in `backend/app/modules/judge/orchestrator.py`: citation_coverage, groundedness, hallucination, relevance, consistency, toxicity, pii_leakage, bias, contradiction.
- Each check returns a score compared against thresholds and hard_fail flags from `config/judge_profiles.json`.
- Independent checks run in parallel; dependent checks run after. The orchestrator compiles a `JudgeReport` with PASS / FAIL_RETRYABLE / FAIL_BLOCKED decisions based on hard-fail violations and overall results.
