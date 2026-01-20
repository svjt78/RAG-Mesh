# Document Search Retrieval (Keyword-Based)

This repository implements a **document search** retrieval mode that is separate from vector (semantic) search and graph search. The document search path is **keyword-based** and uses BM25 + TF-IDF over chunk text.

## Where the logic lives

- Retrieval module: `backend/app/modules/doc_retrieval.py`
- Orchestration entry point: `backend/app/core/orchestrator.py` (`_execute_retrieval`)
- Chunk storage: `backend/app/adapters/file_doc_store.py` (reads from `data/chunks/*.jsonl`)

## High-level flow

1. **Load chunks**
   - The orchestrator loads chunks from the doc store:
     - `doc_store.get_chunks(filters=...)`
2. **Index for keyword search**
   - `DocumentRetrievalModule.index_chunks()` caches chunk text in memory and builds:
     - **BM25** index with tokenized chunk text
     - **TF-IDF** vectorizer over chunk text
3. **Score a query**
   - `DocumentRetrievalModule.retrieve()` computes:
     - BM25 scores
     - TF-IDF cosine similarity scores
   - Scores are combined as:
     - `combined = 0.6 * bm25 + 0.4 * tfidf`
4. **Apply boosts**
   - Exact substring match: `doc_boost_exact_match`
   - Form number match (metadata): `doc_boost_form_number`
   - Quoted term match (heuristic): `doc_boost_defined_term`
5. **Return top-k**
   - Top results are selected by `profile.doc_k` and returned as `DocumentResult` objects.

## Is it keyword search?

Yes. The module explicitly uses BM25 and TF-IDF and does **not** use embeddings.

## What keywords are identified?

There is no explicit keyword extraction step. “Keywords” are implicitly:

- **BM25 tokens**: `text.lower().split()` (simple whitespace tokenization)
- **TF-IDF terms**: unigrams and bigrams from `TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)`

## Where are the keywords stored?

They are **not persisted**. They are in-memory structures inside `DocumentRetrievalModule`:

- BM25 corpus tokens stored in `self.bm25`
- TF-IDF vocabulary stored in `self.tfidf.vocabulary_`

These are rebuilt each time `index_chunks()` runs.

## Are keywords converted to vector embeddings?

No. BM25 uses token scores, and TF-IDF uses sparse term vectors (not dense embeddings).

## Is retrieval done against the vector store?

No. Document search scores chunks loaded from the doc store (`data/chunks/*.jsonl`).
Vector search runs independently through the vector store (`FAISS`), using embeddings.

## Related configuration

The document search uses fields in `RetrievalProfile` (`backend/app/core/models.py`):

- `doc_k`
- `doc_boost_exact_match`
- `doc_boost_form_number`
- `doc_boost_defined_term`

These are applied during scoring and boosting in `DocumentRetrievalModule`.
