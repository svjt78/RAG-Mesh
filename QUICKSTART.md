# RAGMesh Quick Start Guide

Get up and running with RAGMesh in minutes.

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API key
- 8GB+ RAM recommended
- Ports 8017 (API) and 3017 (UI) available

## Step 1: Configure OpenAI API Key

Edit the `.env` file and add your OpenAI API key:

```bash
OPENAI_API_KEY=sk-your-actual-openai-key-here
```

## Step 2: Start the Application

```bash
docker-compose up --build
```

Wait for both services to start:
- Backend API will be available at http://localhost:8017
- Frontend UI will be available at http://localhost:3017

## Step 3: Upload Sample Documents

1. Open http://localhost:3017 in your browser

2. Navigate to the **Documents** tab

3. Upload the three sample PDFs:
   - `sample_data/pdfs/homeowners_policy_HO3_california.pdf`
   - `sample_data/pdfs/water_damage_exclusion_endorsement.pdf`
   - `sample_data/pdfs/earthquake_coverage_info.pdf`

4. For each uploaded document, click the **Index** button
   - This creates chunks, embeddings, and extracts graph entities
   - Wait for "indexed" status before proceeding

## Step 4: Run Your First Query

1. Navigate to the **Query** tab

2. Try this sample query:
   ```
   What types of water damage are excluded from coverage?
   ```

3. Select workflow: **Default Insurance (Balanced)**

4. Click **Execute Query**

5. Watch the real-time progress in the **Events** tab

## Step 5: Explore the Results

### Retrieval Tab
- See results from all three modalities:
  - Vector (semantic similarity)
  - Document (keyword matching)
  - Graph (entity linking)

### Fusion Tab
- View the RRF-fused results
- See how scores from different modalities are combined
- Notice the ranking by final score

### Context Tab
- See the compiled context sent to the LLM
- Check token count (should be under budget)
- View which chunks were included

### Answer Tab
- Read the generated answer
- See confidence level (high/medium/low)
- Review citations linking to source documents
- Check assumptions and limitations

### Judge Tab
- Review all 9 validation checks:
  - Citation Coverage
  - Groundedness
  - Hallucination Detection
  - Relevance
  - Consistency
  - Toxicity
  - PII Leakage
  - Bias Detection
  - Contradiction Detection
- See overall decision (PASS/FAIL)
- Check individual check scores

## Sample Queries to Try

### Coverage Questions
```
What are the coverage limits for dwelling and personal property?
What perils are covered under Coverage C?
What is included in Coverage E - Personal Liability?
```

### Exclusion Questions
```
What types of water damage are excluded?
Is earthquake damage covered?
What is the earth movement exclusion?
```

### California-Specific Questions
```
Is earthquake insurance required in California?
How much does earthquake insurance cost in California?
What is the California Earthquake Authority?
```

### Cross-Document Questions
```
Can I add sewer backup coverage to my policy?
What exclusions can be added back with endorsements?
What additional coverages should I consider?
```

## Configuration Profiles

RAGMesh comes with pre-configured profiles for different use cases:

### Workflows
- **default_insurance_workflow**: Balanced tri-modal retrieval
- **fast_workflow**: Vector-only for speed
- **comprehensive_workflow**: With reranking for accuracy

### Chunking
- **default**: 500 chars, 100 overlap
- **large_chunks**: 1000 chars for context
- **small_chunks**: 300 chars for precision

### Judge Validation
- **strict_insurance**: Production-grade (all 9 checks)
- **balanced**: Development/testing
- **lenient**: Experimentation

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs ragmesh-api

# Common issues:
# - Port 8017 already in use
# - OpenAI API key not set or invalid
```

### Frontend won't connect
```bash
# Check logs
docker-compose logs ragmesh-ui

# Common issues:
# - Port 3017 already in use
# - Backend not running
```

### Document indexing fails
```bash
# Check backend logs
docker-compose logs ragmesh-api

# Common issues:
# - OpenAI API key invalid
# - OpenAI API rate limits
# - PDF file corrupted
```

### Queries return no results
```bash
# Verify documents are indexed
# Check Documents tab for "indexed" status

# Try:
# 1. Re-index documents
# 2. Try different query phrasings
# 3. Check retrieval results in Retrieval tab
```

## API Documentation

Once the backend is running, explore the auto-generated API docs:

- **Swagger UI**: http://localhost:8017/docs
- **ReDoc**: http://localhost:8017/redoc

## Next Steps

- **Add More Documents**: Upload your own insurance PDFs
- **Experiment with Profiles**: Try different chunking, retrieval, and fusion strategies
- **Tune Judge Checks**: Adjust thresholds in `config/judge_profiles.json`
- **Monitor Performance**: Check Events tab for timing and token usage
- **Review Artifacts**: Inspect saved runs in `data/runs/`

## System Architecture

```
┌─────────────┐
│  Frontend   │  Next.js 14 + TypeScript
│  (Port 3017)│  9-Tab Interface + SSE
└──────┬──────┘
       │ HTTP + SSE
┌──────▼──────┐
│   FastAPI   │  Python 3.11+
│  (Port 8017)│  30+ REST Endpoints
└──────┬──────┘
       │
  ┌────┴────┬─────────┬──────────┐
  │         │         │          │
┌─▼──┐  ┌──▼──┐  ┌───▼───┐  ┌──▼───┐
│File│  │FAISS│  │NetworkX│ │OpenAI│
│Store│ │Vector│ │ Graph  │ │ API  │
└────┘  └─────┘  └────────┘ └──────┘
```

## Features at a Glance

✅ **Tri-Modal Retrieval**: Vector + Document + Graph
✅ **RRF Fusion**: Weighted rank fusion across modalities
✅ **9-Check Judge**: Production-grade validation gate
✅ **Real-Time Streaming**: SSE for live updates
✅ **Configuration-Driven**: 100% JSON-configurable
✅ **Complete Observability**: Event logs and artifacts
✅ **Type-Safe**: Pydantic backend, TypeScript frontend
✅ **Containerized**: Docker Compose for easy deployment

## Support

For issues, questions, or contributions:
- Review logs: `docker-compose logs`
- Check `PROGRESS.md` for implementation status
- Review `sample_data/README.md` for testing guidance
- Inspect `config/` for configuration options

## Performance Tips

1. **For Speed**: Use `fast_workflow` (vector-only)
2. **For Accuracy**: Use `comprehensive_workflow` (with reranking)
3. **For Cost**: Use smaller chunking and lower k values
4. **For Quality**: Use `strict_insurance` judge profile
5. **For Testing**: Use `lenient` judge profile
