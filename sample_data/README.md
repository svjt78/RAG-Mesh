# Sample Insurance PDFs for RAGMesh

This directory contains sample insurance policy documents for testing the RAGMesh system.

## Generated PDFs

Three realistic insurance documents have been generated:

### 1. Homeowners Policy HO-3 (California)
**File:** `pdfs/homeowners_policy_HO3_california.pdf`
- **Form Number:** HO-3
- **Type:** Policy
- **State:** California
- **Effective Date:** 2024-01-01
- **Content:**
  - Policy declarations
  - Property coverages (Dwelling, Other Structures, Personal Property, Loss of Use)
  - Perils insured against (16 named perils)
  - Exclusions (Ordinance/Law, Earth Movement, Water Damage, Neglect, War)
  - Liability coverages
  - Policy conditions

### 2. Water Damage Exclusion Endorsement
**File:** `pdfs/water_damage_exclusion_endorsement.pdf`
- **Form Number:** WD-EXCL-01
- **Type:** Endorsement
- **State:** California
- **Effective Date:** 2024-01-01
- **Content:**
  - Water damage exclusions (flood, sewer backup, surface water)
  - Exceptions to exclusions
  - Definitions (flood, surface water, sewer backup)
  - Claims procedure
  - California-specific notices

### 3. Earthquake Insurance Disclosure (California)
**File:** `pdfs/earthquake_coverage_info.pdf`
- **Form Number:** EQ-INFO-CA
- **Type:** Disclosure
- **State:** California
- **Effective Date:** 2024-01-01
- **Content:**
  - California earthquake insurance requirements
  - Coverage options (CEA vs Private Market)
  - Cost estimates by deductible level
  - Important considerations
  - How to obtain coverage
  - Policyholder acknowledgment form

## How to Use

### 1. Upload to RAGMesh

1. Start the RAGMesh application:
   ```bash
   docker-compose up
   ```

2. Open the frontend: http://localhost:3017

3. Navigate to the **Documents** tab

4. Upload each PDF file:
   - Click "Choose File" and select a PDF
   - Click "Upload"
   - Click "Index" to process the document

### 2. Test Queries

Once the documents are indexed, try these sample queries in the **Query** tab:

**Coverage Questions:**
- "What are the coverage limits for dwelling and personal property?"
- "What perils are covered for personal property?"
- "What is the medical payments coverage limit?"

**Exclusion Questions:**
- "What types of water damage are excluded?"
- "Is earthquake damage covered in the standard policy?"
- "What is the earth movement exclusion?"

**Endorsement Questions:**
- "Can sewer backup coverage be added?"
- "What are the exceptions to the water damage exclusion?"
- "How do I file a water damage claim?"

**California-Specific Questions:**
- "Is earthquake insurance required in California?"
- "How much does earthquake insurance cost?"
- "What deductible options are available for earthquake coverage?"
- "What is the California Earthquake Authority?"

**Cross-Document Questions:**
- "What types of damage are excluded but can be added with endorsements?"
- "Which exclusions apply to my California homeowners policy?"
- "What additional coverages should I consider for comprehensive protection?"

## Regenerating PDFs

To regenerate the sample PDFs (e.g., after modifying content):

```bash
cd sample_data
python generate_sample_pdfs.py
```

The script will create fresh PDFs in the `pdfs/` directory.

## PDF Content Features

The generated PDFs include:

- **Realistic Content:** Based on actual insurance policy language
- **Proper Formatting:** Headers, sections, and paragraph spacing
- **Metadata:** Form numbers, doc types, states, effective dates
- **Insurance-Specific Terms:** Coverage types, exclusions, definitions
- **Multi-Page Documents:** Full policy documents with multiple sections
- **Cross-References:** Documents reference each other (policy → endorsements)

## Testing the RAG Pipeline

These documents are designed to test:

1. **PDF Ingestion:** Text extraction from formatted PDFs
2. **Chunking:** Proper segmentation of policy sections
3. **Vector Retrieval:** Semantic search for coverage information
4. **Document Retrieval:** Keyword matching for specific terms (form numbers, exclusions)
5. **Graph Extraction:** Entity linking (Coverage types, Exclusions, Conditions, States)
6. **Fusion:** Combining results from multiple retrieval modalities
7. **Context Compilation:** Assembling relevant chunks within token budget
8. **Generation:** Creating accurate answers with proper citations
9. **Judge Validation:** All 9 checks (citation coverage, groundedness, hallucination, etc.)

## Expected Results

After indexing these documents, RAGMesh should be able to:

- Answer questions about coverage limits, perils, and exclusions
- Cite specific sections from the correct documents
- Link entities across documents (e.g., water damage mentioned in policy and endorsement)
- Identify California-specific requirements and disclosures
- Provide accurate information about earthquake insurance options
- Handle multi-document queries that require information from multiple sources

## Troubleshooting

If documents fail to index:
1. Check that PDFs are in the `pdfs/` directory
2. Verify the backend is running: http://localhost:8017/health
3. Check backend logs for errors: `docker-compose logs ragmesh-api`
4. Ensure OpenAI API key is configured in `.env`

If queries return poor results:
1. Verify all documents are indexed (check Documents tab)
2. Try different query phrasings
3. Check retrieval results in Retrieval tab
4. Review judge report in Judge tab for any failures

## Adding More Documents

To add your own insurance PDFs:

1. Place PDF files in the `pdfs/` directory
2. Upload via the Documents tab in the frontend
3. Index each document
4. Test with relevant queries

Or modify `generate_sample_pdfs.py` to create additional documents:
- Add new document definitions to the `SAMPLE_DOCUMENTS` list
- Include form numbers, doc types, states, and content sections
- Run the script to generate new PDFs
