# RAGMesh Test Suite

Comprehensive test suite for the RAGMesh insurance RAG system.

## Test Coverage

### Unit Tests

#### Adapters (tests/adapters/)
- **test_file_doc_store.py** - File-based document storage
  - Document CRUD operations
  - Chunk storage and retrieval
  - Metadata handling
  - Concurrent operations

- **test_faiss_vector_store.py** - FAISS vector search
  - Vector indexing and search
  - Similarity scoring
  - Index persistence
  - Document filtering

- **test_networkx_graph.py** - Graph storage and traversal
  - Node and edge management
  - Entity search
  - Graph traversal
  - Persistence

- **test_openai_adapter.py** - OpenAI API integration
  - Text generation
  - Embeddings
  - Entity extraction
  - Token counting
  - Retry logic

#### Modules (tests/modules/)
- **test_ingestion.py** - PDF ingestion
  - Text extraction
  - Metadata propagation
  - Error handling
  - Special characters

- **test_indexing.py** - Document indexing
  - Chunking strategies
  - Vector embedding
  - Entity extraction
  - Metadata preservation

#### Judge Checks (tests/modules/judge/checks/)
- **test_citation_coverage.py** - Citation validation
  - Missing citation detection
  - Coverage scoring
  - Format handling

- **test_groundedness.py** - Claim verification
  - LLM-based validation
  - Score parsing
  - Threshold configuration

- **test_hallucination.py** - Fabrication detection
  - Hallucination scoring
  - Numeric accuracy
  - Attribution verification

### Integration Tests

#### API (tests/api/)
- **test_endpoints.py** - REST API endpoints
  - Health checks
  - Document management
  - Query execution
  - Configuration
  - Error handling
  - CORS
  - Concurrent requests

### End-to-End Tests

- **test_e2e_pipeline.py** - Full pipeline execution
  - Complete RAG workflow
  - Multi-document queries
  - Error recovery
  - Caching behavior

## Running Tests

### Run All Tests
```bash
cd backend
pytest
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Slow tests (excluded by default)
pytest -m slow

# Tests requiring OpenAI API
pytest -m requires_openai
```

### Run Specific Test Files
```bash
# Adapter tests
pytest tests/adapters/

# Module tests
pytest tests/modules/

# Judge tests
pytest tests/modules/judge/

# API tests
pytest tests/api/

# E2E tests
pytest tests/test_e2e_pipeline.py
```

### Run Specific Test Functions
```bash
pytest tests/adapters/test_file_doc_store.py::TestFileDocStore::test_save_and_get_document
```

## Test Configuration

### pytest.ini
- Test discovery patterns
- Markers for categorization
- Coverage settings
- Warning filters

### conftest.py
Common fixtures:
- `temp_dir` - Temporary directory
- `test_data_dir` - Test data structure
- `sample_document` - Sample document with pages
- `sample_chunks` - Sample text chunks
- `sample_nodes` - Sample graph nodes
- `sample_edges` - Sample graph edges
- `sample_citations` - Sample citations
- Mock adapters (doc_store, vector_store, graph_store, llm_adapter)
- Configuration fixtures
- OpenAI API key

## Test Best Practices

### Unit Tests
- Test one component in isolation
- Mock external dependencies
- Cover edge cases and error conditions
- Test configuration variations

### Integration Tests
- Test component interactions
- Use real implementations where possible
- Test realistic scenarios
- Verify API contracts

### E2E Tests
- Test complete workflows
- Use realistic data
- Test error recovery
- Verify business requirements

## CI/CD Integration

The test suite is designed to run in CI/CD pipelines:

```bash
# Quick feedback (unit tests only)
pytest -m unit --tb=short

# Full test suite with coverage
pytest --cov=app --cov-report=xml --cov-fail-under=80

# Integration tests (may require external services)
pytest -m integration
```

## Coverage Goals

- **Overall**: 80%+ coverage
- **Adapters**: 90%+ coverage
- **Core modules**: 85%+ coverage
- **Judge checks**: 90%+ coverage
- **API endpoints**: 75%+ coverage

## Mocking Strategy

### When to Mock
- External APIs (OpenAI)
- File I/O for some tests
- Network requests
- Time-dependent operations

### When to Use Real Implementations
- Internal adapters (in integration tests)
- Data models
- Business logic
- Validation logic

## Test Data

Sample test data is located in:
- `tests/conftest.py` - Fixture definitions
- `sample_data/pdfs/` - Sample insurance PDFs

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure backend is in PYTHONPATH
export PYTHONPATH=/path/to/backend:$PYTHONPATH
```

**OpenAI API Errors**
```bash
# Skip tests requiring OpenAI
pytest -m "not requires_openai"
```

**Slow Tests**
```bash
# Skip slow tests
pytest -m "not slow"
```

**Coverage Not Working**
```bash
# Install coverage extras
pip install pytest-cov
```

## Contributing

When adding new tests:

1. Follow existing patterns
2. Use appropriate markers (`@pytest.mark.unit`, etc.)
3. Add docstrings
4. Mock external dependencies
5. Test both success and failure cases
6. Update this README if adding new test categories

## Test Metrics

Run pytest with verbose output to see test metrics:

```bash
pytest -v --durations=10
```

This shows:
- Total tests run
- Pass/fail counts
- 10 slowest tests
- Coverage percentage
