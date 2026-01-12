# RAGMesh Verification Checklist

This document provides a comprehensive checklist to verify that RAGMesh is properly installed, configured, and functioning correctly.

## Pre-Deployment Verification

### 1. Environment Setup

- [ ] Docker and Docker Compose installed
  ```bash
  docker --version
  docker-compose --version
  ```

- [ ] OpenAI API key obtained and valid
  - Visit: https://platform.openai.com/api-keys
  - Check quota: https://platform.openai.com/usage

- [ ] `.env` file created with valid API key
  ```bash
  cat .env | grep OPENAI_API_KEY
  ```

- [ ] System requirements met
  - [ ] 4GB+ RAM available
  - [ ] 2+ CPU cores
  - [ ] 2GB+ disk space free

### 2. File Structure Verification

- [ ] All required directories exist:
  ```bash
  ls -la backend/app/adapters
  ls -la backend/app/modules
  ls -la backend/app/core
  ls -la frontend/components
  ls -la frontend/lib
  ls -la config
  ls -la sample_data/pdfs
  ```

- [ ] Configuration files present:
  ```bash
  ls config/*.json
  # Should show 8 JSON files
  ```

- [ ] Sample PDFs generated:
  ```bash
  ls sample_data/pdfs/*.pdf
  # Should show 3 PDF files
  ```

## Deployment Verification

### 3. Docker Container Startup

- [ ] Build containers successfully:
  ```bash
  docker-compose build
  # Should complete without errors
  ```

- [ ] Start containers:
  ```bash
  docker-compose up -d
  ```

- [ ] Verify containers are running:
  ```bash
  docker-compose ps
  # Should show ragmesh-api and ragmesh-ui as "Up"
  ```

- [ ] Check container logs for errors:
  ```bash
  docker-compose logs ragmesh-api | grep -i error
  docker-compose logs ragmesh-ui | grep -i error
  # Should show no critical errors
  ```

### 4. Backend API Verification

- [ ] Health check returns 200 OK:
  ```bash
  curl http://localhost:8017/health
  # Should return: {"status":"healthy"}
  ```

- [ ] API documentation accessible:
  - Visit: http://localhost:8017/docs
  - [ ] OpenAPI/Swagger UI loads
  - [ ] All 15+ endpoints visible

- [ ] Configuration profiles load:
  ```bash
  curl http://localhost:8017/profiles
  # Should return all 8 profile types
  ```

- [ ] Data directories created:
  ```bash
  docker exec ragmesh-api ls data/
  # Should show: docs, chunks, vectors, graph, runs
  ```

### 5. Frontend UI Verification

- [ ] Frontend loads successfully:
  - Visit: http://localhost:3017
  - [ ] Page loads without errors
  - [ ] All 9 tabs visible

- [ ] Tab navigation works:
  - [ ] Query tab
  - [ ] Retrieval tab
  - [ ] Fusion tab
  - [ ] Context tab
  - [ ] Answer tab
  - [ ] Judge tab
  - [ ] Events tab
  - [ ] Config tab
  - [ ] Documents tab

- [ ] No console errors:
  - Open browser DevTools → Console
  - [ ] No red errors shown

## Functional Verification

### 6. Document Upload & Indexing

- [ ] Upload sample PDF (Documents tab):
  1. Navigate to Documents tab
  2. Click "Upload Document"
  3. Select `sample_data/pdfs/homeowners_policy_HO3_california.pdf`
  4. Add metadata:
     - form_number: HO-3
     - doc_type: policy
     - state: CA
  5. Click Upload
  6. [ ] Document appears in document list

- [ ] Index document:
  1. Click "Index" button for uploaded document
  2. Select "default" chunking profile
  3. Click "Start Indexing"
  4. [ ] Indexing completes successfully
  5. [ ] Status shows "Indexed"

- [ ] Verify backend storage:
  ```bash
  # Check document was saved
  docker exec ragmesh-api ls data/docs/

  # Check chunks were created
  docker exec ragmesh-api ls data/chunks/

  # Check vectors were indexed
  docker exec ragmesh-api ls data/vectors/
  ```

### 7. Query Execution

- [ ] Execute test query (Query tab):
  1. Enter query: "What are the coverage limits for dwelling?"
  2. Select "default" workflow
  3. Click "Execute Query"
  4. [ ] Query starts executing
  5. [ ] Events tab shows real-time updates

- [ ] Verify pipeline stages complete:
  - [ ] Retrieval completes (Retrieval tab shows results)
  - [ ] Fusion completes (Fusion tab shows combined results)
  - [ ] Context completes (Context tab shows context pack)
  - [ ] Generation completes (Answer tab shows answer)
  - [ ] Judge validation completes (Judge tab shows checks)

- [ ] Check answer quality:
  - [ ] Answer contains relevant information
  - [ ] Citations are numbered [1], [2], etc.
  - [ ] Citations match context pack

- [ ] Verify judge checks:
  - [ ] All 9 checks executed
  - [ ] Scores displayed
  - [ ] Overall decision shown (PASS/FAIL)

### 8. Advanced Queries

Test with multiple query types:

- [ ] **Coverage Query:**
  - Query: "What types of property damage are covered?"
  - [ ] Returns relevant coverage information
  - [ ] Cites specific policy sections

- [ ] **Exclusion Query:**
  - Query: "What water damage is excluded?"
  - [ ] Returns exclusion information
  - [ ] References exclusion endorsement

- [ ] **Requirement Query:**
  - Query: "Is earthquake insurance required in California?"
  - [ ] Returns accurate information
  - [ ] Cites earthquake disclosure document

- [ ] **Limit Query:**
  - Query: "What is the coverage limit for personal property?"
  - [ ] Returns specific dollar amounts
  - [ ] Correctly extracts Coverage C limit

### 9. SSE Streaming Verification

- [ ] Real-time events display:
  1. Execute a query
  2. Switch to Events tab
  3. [ ] Events appear in real-time
  4. [ ] Events include timestamps
  5. [ ] Events show all pipeline steps

- [ ] Event details complete:
  - [ ] Each event has step name
  - [ ] Each event has status (started/completed/failed)
  - [ ] Events include details object
  - [ ] Duration shown for completed events

### 10. Configuration Management

- [ ] View configurations (Config tab):
  - [ ] All 8 profile types listed
  - [ ] Can expand each profile type
  - [ ] Profile details shown correctly

- [ ] Configuration reload:
  ```bash
  curl -X POST http://localhost:8017/reload-config
  # Should return success message
  ```

### 11. Multi-Document Testing

- [ ] Upload all 3 sample PDFs:
  - [ ] homeowners_policy_HO3_california.pdf
  - [ ] water_damage_exclusion_endorsement.pdf
  - [ ] earthquake_coverage_info.pdf

- [ ] Index all documents

- [ ] Query across documents:
  - Query: "What additional coverages can I add to my policy?"
  - [ ] Retrieves from multiple documents
  - [ ] Combines information correctly
  - [ ] Cites all relevant documents

## Testing Verification

### 12. Run Test Suite

- [ ] Unit tests pass:
  ```bash
  cd backend
  pytest -m unit -v
  # All unit tests should pass
  ```

- [ ] Integration tests pass:
  ```bash
  pytest -m integration -v
  # All integration tests should pass
  ```

- [ ] Coverage meets threshold:
  ```bash
  pytest --cov=app --cov-report=term-missing
  # Coverage should be 80%+
  ```

- [ ] No test failures:
  ```bash
  pytest
  # 147+ tests should pass, 0 failures
  ```

## Performance Verification

### 13. Performance Benchmarks

- [ ] Ingestion performance:
  - Upload a PDF
  - [ ] Completes in <5 seconds

- [ ] Indexing performance:
  - Index a document
  - [ ] Completes in <15 seconds (depends on document size)

- [ ] Query performance:
  - Execute a query
  - [ ] Retrieval completes in <3 seconds
  - [ ] Full pipeline completes in <15 seconds

- [ ] Memory usage acceptable:
  ```bash
  docker stats --no-stream
  # Both containers should use <1GB RAM each
  ```

### 14. Concurrent Request Handling

- [ ] Multiple simultaneous queries:
  - Open 2-3 browser tabs
  - Execute queries simultaneously
  - [ ] All queries complete successfully
  - [ ] No errors in logs
  - [ ] No timeout errors

## Error Handling Verification

### 15. Error Scenarios

- [ ] Invalid API key:
  1. Set invalid OPENAI_API_KEY in .env
  2. Restart containers
  3. Try to index a document
  4. [ ] Error message is clear and helpful
  5. [ ] No crash or 500 errors

- [ ] Corrupted PDF upload:
  1. Try to upload a non-PDF file
  2. [ ] Error is caught and reported
  3. [ ] System remains stable

- [ ] Missing configuration:
  1. Request non-existent profile
  2. [ ] 404 error returned with clear message

- [ ] Query with no indexed documents:
  1. Delete all documents
  2. Execute a query
  3. [ ] Returns empty results or clear message
  4. [ ] No crash

## Security Verification

### 16. Security Checks

- [ ] PII redaction works:
  1. Upload document with SSN (123-45-6789)
  2. Index and query
  3. [ ] SSN is redacted in context as [SSN]

- [ ] CORS configured correctly:
  ```bash
  curl -H "Origin: http://localhost:3017" \
       -H "Access-Control-Request-Method: POST" \
       -X OPTIONS http://localhost:8017/health
  # Should return CORS headers
  ```

- [ ] Input validation works:
  ```bash
  curl -X POST http://localhost:8017/run \
       -H "Content-Type: application/json" \
       -d '{}'
  # Should return 422 validation error
  ```

- [ ] No sensitive data in logs:
  ```bash
  docker-compose logs | grep -i "sk-"
  # Should not show API keys
  ```

## Documentation Verification

### 17. Documentation Completeness

- [ ] README.md is comprehensive
  - [ ] Quick start instructions work
  - [ ] All commands are accurate
  - [ ] Links are valid

- [ ] ARCHITECTURE.md explains design
  - [ ] All 7 modules documented
  - [ ] Data flow is clear
  - [ ] Design decisions explained

- [ ] CLAUDE.md helps developers
  - [ ] Development commands work
  - [ ] Architecture principles clear
  - [ ] Common patterns documented

- [ ] API documentation accurate:
  - Visit http://localhost:8017/docs
  - [ ] All endpoints documented
  - [ ] Request/response schemas shown
  - [ ] Try out feature works

## Production Readiness

### 18. Production Checklist

- [ ] Environment variables externalized
- [ ] Secrets not in code or commits
- [ ] Error handling comprehensive
- [ ] Logging configured appropriately
- [ ] Health checks implemented
- [ ] Graceful shutdown configured
- [ ] Resource limits set (Docker)
- [ ] Monitoring endpoints available
- [ ] Documentation complete
- [ ] License file present

## Final Verification

### 19. End-to-End Demo Scenario

Complete this scenario without errors:

1. [ ] Start fresh containers: `docker-compose down && docker-compose up --build -d`
2. [ ] Wait for startup (30 seconds)
3. [ ] Check health: `curl http://localhost:8017/health`
4. [ ] Open UI: http://localhost:3017
5. [ ] Upload homeowners policy PDF
6. [ ] Index with default profile
7. [ ] Upload water damage exclusion PDF
8. [ ] Index with default profile
9. [ ] Execute query: "What water damage is excluded?"
10. [ ] Verify answer includes both documents
11. [ ] Check all 9 judge checks pass
12. [ ] Verify events tab shows complete flow
13. [ ] Execute second query: "What is the dwelling coverage limit?"
14. [ ] Verify answer includes $500,000
15. [ ] All steps complete without errors

## Sign-Off

**Verification Date:** _______________

**Verified By:** _______________

**Overall Status:** [ ] PASS  [ ] FAIL

**Notes:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

**Critical Issues Found:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

**Recommendations:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

## Quick Verification Script

For automated verification, run:

```bash
#!/bin/bash
echo "=== RAGMesh Verification Script ==="

echo "1. Checking Docker..."
docker --version || exit 1

echo "2. Starting containers..."
docker-compose up -d

echo "3. Waiting for startup..."
sleep 30

echo "4. Checking API health..."
curl -f http://localhost:8017/health || exit 1

echo "5. Checking frontend..."
curl -f http://localhost:3017 || exit 1

echo "6. Checking profiles..."
curl -f http://localhost:8017/profiles || exit 1

echo "7. Running tests..."
docker exec ragmesh-api pytest -m unit --tb=short || exit 1

echo "✅ All checks passed!"
```

Save as `verify.sh` and run with `chmod +x verify.sh && ./verify.sh`
