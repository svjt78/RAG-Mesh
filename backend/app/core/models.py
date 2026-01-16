"""
Pydantic domain models for RAGMesh
Strict data validation for all entities in the system
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


# ============================================================================
# Document Models
# ============================================================================

class Page(BaseModel):
    """Single page in a document"""
    page_no: int = Field(..., ge=1, description="Page number (1-indexed)")
    text: str = Field(..., description="Extracted text content")
    char_count: int = Field(..., ge=0, description="Character count")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Page-specific metadata")


class Document(BaseModel):
    """Complete document with metadata and pages"""
    doc_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    doc_type: Optional[str] = Field(None, description="Document type (e.g., policy, endorsement)")
    form_number: Optional[str] = Field(None, description="Insurance form number")
    effective_date: Optional[str] = Field(None, description="Effective date")
    state: Optional[str] = Field(None, description="State jurisdiction")
    pages: List[Page] = Field(..., description="List of pages")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    created_at: datetime = Field(default_factory=datetime.now)
    indexed_at: Optional[datetime] = None


class Chunk(BaseModel):
    """Text chunk with provenance"""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    doc_id: str = Field(..., description="Parent document ID")
    text: str = Field(..., description="Chunk text content")
    page_no: int = Field(..., ge=1, description="Source page number")
    char_start: int = Field(..., ge=0, description="Character start position in page")
    char_end: int = Field(..., ge=0, description="Character end position in page")
    tokens: int = Field(..., ge=0, description="Estimated token count")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")


# ============================================================================
# Graph Models
# ============================================================================

class EntityType(str, Enum):
    """Insurance-specific entity types"""
    COVERAGE = "Coverage"
    EXCLUSION = "Exclusion"
    CONDITION = "Condition"
    ENDORSEMENT = "Endorsement"
    FORM = "Form"
    DEFINITION = "Definition"
    STATE = "State"
    TERM = "Term"
    OTHER = "Other"


class RelationType(str, Enum):
    """Relationship types between entities"""
    AMENDS = "AMENDS"
    EXCLUDES = "EXCLUDES"
    SUBJECT_TO = "SUBJECT_TO"
    APPLIES_IN = "APPLIES_IN"
    REFERENCES = "REFERENCES"
    DEFINES = "DEFINES"
    OTHER = "OTHER"


class Node(BaseModel):
    """Graph node representing an entity"""
    node_id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Entity label/name")
    node_type: EntityType = Field(..., description="Entity type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node properties")
    chunk_ids: List[str] = Field(default_factory=list, description="Supporting chunk IDs")


class Edge(BaseModel):
    """Graph edge representing a relationship"""
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    edge_type: RelationType = Field(..., description="Relationship type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Edge properties")
    evidence_chunk_ids: List[str] = Field(default_factory=list, description="Evidence chunk IDs")


class Subgraph(BaseModel):
    """Subgraph with nodes and edges"""
    nodes: List[Node] = Field(..., description="Nodes in subgraph")
    edges: List[Edge] = Field(..., description="Edges in subgraph")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Subgraph metadata")


# ============================================================================
# Retrieval Models
# ============================================================================

class VectorResult(BaseModel):
    """Single vector search result"""
    chunk_id: str = Field(..., description="Chunk identifier")
    score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    rank: int = Field(..., ge=1, description="Rank in results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")


class DocumentResult(BaseModel):
    """Single document retrieval result"""
    chunk_id: str = Field(..., description="Chunk identifier")
    score: float = Field(..., ge=0.0, description="Relevance score")
    rank: int = Field(..., ge=1, description="Rank in results")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")


class GraphResult(BaseModel):
    """Graph retrieval result"""
    chunk_id: str = Field(..., description="Chunk identifier")
    score: float = Field(..., ge=0.0, description="Relevance score")
    rank: int = Field(..., ge=1, description="Rank in results")
    entity_ids: List[str] = Field(..., description="Related entity IDs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")


class RetrievalBundle(BaseModel):
    """Complete retrieval results from all modalities"""
    query: str = Field(..., description="Original query")
    vector_results: List[VectorResult] = Field(default_factory=list)
    document_results: List[DocumentResult] = Field(default_factory=list)
    graph_results: List[GraphResult] = Field(default_factory=list)
    fused_results: List[Dict[str, Any]] = Field(default_factory=list, description="Fused and ranked results")
    subgraph: Optional[Subgraph] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Context and Generation Models
# ============================================================================

class Citation(BaseModel):
    """Citation with provenance"""
    chunk_id: str = Field(..., description="Chunk identifier")
    doc_id: str = Field(..., description="Document identifier")
    page_no: int = Field(..., ge=1, description="Page number")
    quote: str = Field(..., description="Quoted text from chunk")
    reason: str = Field(..., description="Why this citation supports the claim")


class ContextPack(BaseModel):
    """Compiled context for generation"""
    context_text: str = Field(..., description="Exact context string for generation")
    chunks: List[Dict[str, Any]] = Field(..., description="Chunks with tokens per chunk")
    token_budget: int = Field(..., ge=0, description="Maximum tokens allowed")
    tokens_used: int = Field(..., ge=0, description="Actual tokens used")
    coverage: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Query facets to evidence mapping"
    )
    redactions_applied: List[str] = Field(default_factory=list, description="PII redaction log")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConfidenceLevel(str, Enum):
    """Confidence levels for answers"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Answer(BaseModel):
    """Generated answer with citations"""
    answer: str = Field(..., description="Generated answer text")
    citations: List[Citation] = Field(..., description="Citations supporting the answer")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made")
    limitations: List[str] = Field(default_factory=list, description="Limitations of the answer")
    confidence: ConfidenceLevel = Field(..., description="Confidence level")
    tokens_used: int = Field(..., ge=0, description="Tokens used for generation")
    cost: float = Field(..., ge=0.0, description="Cost in USD")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Judge Models
# ============================================================================

class CheckStatus(str, Enum):
    """Status of a validation check"""
    PASS = "pass"
    FAIL = "fail"
    SKIPPED = "skipped"
    ERROR = "error"


class CheckResult(BaseModel):
    """Result of a single validation check"""
    check_name: str = Field(..., description="Name of the check")
    status: CheckStatus = Field(..., description="Check status")
    score: float = Field(..., ge=0.0, le=1.0, description="Check score")
    threshold: float = Field(..., ge=0.0, le=1.0, description="Threshold for passing")
    hard_fail: bool = Field(..., description="Whether this is a hard fail check")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed results")
    message: str = Field(default="", description="Human-readable message")


class Violation(BaseModel):
    """A validation violation"""
    check_name: str = Field(..., description="Name of the check")
    severity: Literal["low", "medium", "high"] = Field(..., description="Violation severity")
    message: str = Field(..., description="Violation description")
    remediation: str = Field(..., description="Suggested remediation")


class JudgeDecision(str, Enum):
    """Final judge decision"""
    PASS = "PASS"
    FAIL_BLOCKED = "FAIL_BLOCKED"
    FAIL_RETRYABLE = "FAIL_RETRYABLE"


class JudgeReport(BaseModel):
    """Complete validation report"""
    decision: JudgeDecision = Field(..., description="Final decision")
    checks: List[CheckResult] = Field(..., description="Individual check results")
    violations: List[Violation] = Field(default_factory=list, description="All violations")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Aggregate score")
    passed: bool = Field(..., description="Whether all checks passed")
    claim_evidence_mapping: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Claims mapped to supporting evidence"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Chat Models
# ============================================================================

class ChatTurn(BaseModel):
    """Single turn in a chat conversation"""
    turn_number: int = Field(..., ge=1, description="Turn number in conversation")
    query: str = Field(..., description="User query")
    answer: Answer = Field(..., description="Generated answer")
    run_id: str = Field(..., description="Associated run ID")
    timestamp: datetime = Field(default_factory=datetime.now)
    tokens: int = Field(..., ge=0, description="Total tokens used in this turn")


class ChatHistory(BaseModel):
    """Chat conversation history"""
    turns: List[ChatTurn] = Field(default_factory=list, description="List of conversation turns")
    summary: Optional[str] = Field(None, description="LLM-generated summary of older turns")
    summary_covers_turns: List[int] = Field(default_factory=list, description="Turn numbers included in summary")
    total_turns: int = Field(default=0, ge=0, description="Total number of turns")


class ChatSession(BaseModel):
    """Complete chat session state"""
    session_id: str = Field(..., description="Unique session identifier")
    history: ChatHistory = Field(default_factory=ChatHistory, description="Conversation history")
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    total_tokens: int = Field(default=0, ge=0, description="Cumulative tokens across all turns")
    workflow_id: str = Field(default="default_workflow")
    chat_profile_id: str = Field(default="default")


# ============================================================================
# Event Models
# ============================================================================

class EventType(str, Enum):
    """Event types in the pipeline"""
    RUN_STARTED = "run_started"
    RETRIEVAL_STARTED = "retrieval_started"
    VECTOR_SEARCH_COMPLETED = "vector_search_completed"
    DOCUMENT_SEARCH_COMPLETED = "document_search_completed"
    GRAPH_SEARCH_COMPLETED = "graph_search_completed"
    FUSION_COMPLETED = "fusion_completed"
    CONTEXT_COMPILED = "context_compiled"
    GENERATION_COMPLETED = "generation_completed"
    JUDGE_STARTED = "judge_started"
    JUDGE_CHECK_COMPLETED = "judge_check_completed"
    JUDGE_COMPLETED = "judge_completed"
    RUN_COMPLETED = "run_completed"
    RUN_BLOCKED = "run_blocked"
    RUN_FAILED = "run_failed"
    CHAT_SESSION_CREATED = "chat_session_created"
    CHAT_COMPACTED = "chat_compacted"
    CHAT_TURN_ADDED = "chat_turn_added"
    CHAT_SESSION_TERMINATED = "chat_session_terminated"


class Event(BaseModel):
    """Pipeline event for observability"""
    run_id: str = Field(..., description="Run identifier")
    event_type: EventType = Field(..., description="Type of event")
    step: str = Field(..., description="Pipeline step name")
    timestamp: datetime = Field(default_factory=datetime.now)
    duration_ms: Optional[int] = Field(None, ge=0, description="Step duration in milliseconds")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Configuration Models
# ============================================================================

class ModelConfig(BaseModel):
    """LLM model configuration"""
    model_name: str = Field(..., description="Model name")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)
    timeout: int = Field(default=60, ge=1, description="Timeout in seconds")
    max_retries: int = Field(default=3, ge=0)


class ChunkingProfile(BaseModel):
    """Chunking configuration"""
    chunk_size: int = Field(default=500, ge=100, le=5000)
    chunk_overlap: int = Field(default=100, ge=0, le=1000)
    page_aware: bool = Field(default=True)
    max_chunks_per_doc: Optional[int] = Field(None, ge=1)
    sentence_aware: bool = Field(default=True)
    min_chunk_size: int = Field(default=100, ge=10, le=1000)
    preserve_paragraph_boundaries: bool = Field(default=True)


class GraphExtractionProfile(BaseModel):
    """Graph extraction configuration for entity and relationship extraction"""
    description: str = Field(default="Graph extraction profile")
    entity_types: List[str] = Field(
        default_factory=lambda: [
            "Person", "Organization", "Location", "Date", "Event",
            "Concept", "Product", "Document", "Term", "Metric"
        ]
    )
    relationship_types: List[str] = Field(
        default_factory=lambda: [
            "RELATES_TO", "PART_OF", "LOCATED_IN", "OCCURS_AT", "CREATED_BY",
            "REFERENCES", "DEFINES", "SUPPORTS", "CONTRADICTS", "PRECEDES"
        ]
    )


class RetrievalProfile(BaseModel):
    """Retrieval configuration for all modalities"""
    description: str = Field(default="Retrieval profile")
    vector_k: int = Field(default=10, ge=1, le=100)
    vector_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    doc_k: int = Field(default=10, ge=1, le=100)
    doc_boost_exact_match: float = Field(default=1.5, ge=1.0, le=5.0)
    doc_boost_form_number: float = Field(default=1.5, ge=1.0, le=5.0)
    doc_boost_defined_term: float = Field(default=1.5, ge=1.0, le=5.0)
    graph_max_hops: int = Field(default=2, ge=0, le=5)
    graph_entity_types: List[str] = Field(default_factory=list)


class FusionProfile(BaseModel):
    """Fusion configuration"""
    vector_weight: float = Field(default=1.0, ge=0.0, le=10.0)
    document_weight: float = Field(default=1.0, ge=0.0, le=10.0)
    graph_weight: float = Field(default=1.0, ge=0.0, le=10.0)
    rrf_k: int = Field(default=60, ge=1)
    max_chunks_per_doc: int = Field(default=3, ge=1, le=10)
    min_distinct_docs: int = Field(default=2, ge=1, le=10)
    dedup_threshold: float = Field(default=0.95, ge=0.0, le=1.0)
    apply_diversity_constraints: bool = Field(default=True)
    final_top_k: int = Field(default=20, ge=1, le=1000)


class RerankProfile(BaseModel):
    """LLM reranking configuration"""
    description: str = Field(default="LLM reranking profile")
    enabled: bool = Field(default=False)
    model: str = Field(default="gpt-3.5-turbo")
    max_chunks: int = Field(default=20, ge=1, le=200)
    chunk_char_limit: int = Field(default=500, ge=100, le=2000)
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    prompt_template: str = Field(
        default="Given the query and the following chunks, rank them by relevance.",
        description="Prompt template for reranking"
    )


class ContextProfile(BaseModel):
    """Context compilation configuration"""
    max_context_tokens: int = Field(default=3000, ge=500, le=100000)
    citation_format: str = Field(default="inline")
    include_page_numbers: bool = Field(default=True)
    include_doc_metadata: bool = Field(default=True)
    redact_pii: bool = Field(default=True)
    pack_strategy: str = Field(default="rank_ordered")
    reserve_tokens_for_query: int = Field(default=0, ge=0)
    reserve_tokens_for_instructions: int = Field(default=0, ge=0)


class CheckConfig(BaseModel):
    """Configuration for a single judge check"""
    enabled: bool = Field(default=True)
    threshold: float = Field(..., ge=0.0, le=1.0)
    hard_fail: bool = Field(default=False)


class JudgeProfile(BaseModel):
    """Judge validation configuration"""
    citation_coverage: CheckConfig
    groundedness: CheckConfig
    hallucination: CheckConfig
    relevance: CheckConfig
    consistency: CheckConfig
    toxicity: CheckConfig
    pii_leakage: CheckConfig
    bias: CheckConfig
    contradiction: CheckConfig


class ChatProfile(BaseModel):
    """Chat mode configuration"""
    description: str = Field(default="Chat configuration")
    compaction_threshold_tokens: int = Field(default=2000, ge=500, description="Trigger compaction when history exceeds this")
    max_history_turns: int = Field(default=10, ge=1, description="Maximum turns to keep uncompacted")
    summarization_model: str = Field(default="gpt-3.5-turbo", description="Model for summarization")
    summarization_max_tokens: int = Field(default=500, ge=100, description="Max tokens for summary")
    include_summary_in_context: bool = Field(default=True, description="Include summary in context")
    summary_position: str = Field(default="before_retrieval", description="Position: before_retrieval or after_retrieval")
    reserve_tokens_for_history: int = Field(default=800, ge=0, description="Token budget reserved for chat history")


class WorkflowProfile(BaseModel):
    """Complete workflow configuration"""
    workflow_id: str = Field(..., description="Workflow identifier")
    description: str = Field(default="", description="Human-readable workflow description")
    steps: List[str] = Field(..., description="Ordered list of pipeline steps")
    enable_graph_retrieval: bool = Field(default=True, description="Enable graph-based retrieval")
    enable_reranking: bool = Field(default=False, description="Enable result reranking")
    fail_on_judge_block: bool = Field(default=True, description="Fail execution if judge blocks the answer")
    timeout_per_step_seconds: int = Field(default=120, description="Maximum time allowed per pipeline step in seconds")
    max_retry_attempts: int = Field(default=1, description="Maximum number of retry attempts on failure")


class TelemetryConfig(BaseModel):
    """Telemetry and observability configuration"""
    event_verbosity: Literal["minimal", "standard", "detailed"] = Field(default="standard")
    track_costs: bool = Field(default=True)
    track_tokens: bool = Field(default=True)
    track_latency: bool = Field(default=True)
    sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)


# ============================================================================
# API Request/Response Models
# ============================================================================

class IngestPDFRequest(BaseModel):
    """Request to ingest a PDF"""
    filename: str = Field(..., description="Original filename")
    doc_type: Optional[str] = None
    form_number: Optional[str] = None
    effective_date: Optional[str] = None
    state: Optional[str] = None


class IngestPDFResponse(BaseModel):
    """Response from PDF ingestion"""
    doc_id: str = Field(..., description="Generated document ID")
    filename: str
    pages: int = Field(..., ge=1)
    success: bool = Field(default=True)


class IndexDocumentResponse(BaseModel):
    """Response from document indexing"""
    doc_id: str
    chunks_created: int = Field(..., ge=0)
    embeddings_created: int = Field(..., ge=0)
    entities_extracted: int = Field(..., ge=0)
    relationships_extracted: int = Field(..., ge=0)
    success: bool = Field(default=True)


class RunRequest(BaseModel):
    """Request to execute RAG pipeline"""
    query: str = Field(..., min_length=1, description="User query")
    workflow_id: str = Field(default="default_workflow")
    chunking_profile_id: Optional[str] = Field(default="default")
    retrieval_profile_id: str = Field(default="balanced_insurance")
    fusion_profile_id: Optional[str] = Field(default="balanced")
    context_profile_id: str = Field(default="default")
    judge_profile_id: str = Field(default="strict_insurance")
    doc_filter: Optional[Dict[str, Any]] = Field(default=None)
    overrides: Dict[str, Any] = Field(default_factory=dict, description="Runtime overrides")
    # Chat mode fields
    mode: Literal["query", "chat"] = Field(default="query", description="Execution mode")
    session_id: Optional[str] = Field(None, description="Chat session ID (required for chat mode)")
    chat_profile_id: Optional[str] = Field(default="default", description="Chat profile ID")


class RunResponse(BaseModel):
    """Response from run execution"""
    run_id: str = Field(..., description="Unique run identifier")
    status: str = Field(..., description="Run status")
    sse_endpoint: str = Field(..., description="SSE endpoint for live updates")
    answer: Optional[Answer] = Field(None, description="Generated answer")
    judge_report: Optional[JudgeReport] = Field(None, description="Judge validation report")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    # Chat mode fields
    session_id: Optional[str] = Field(None, description="Chat session ID (chat mode only)")
    turn_number: Optional[int] = Field(None, description="Turn number in chat session")
    history_compacted: bool = Field(default=False, description="Whether compaction occurred this turn")


# ============================================================================
# Synchronous API Request/Response Models
# ============================================================================

class QueryRequest(BaseModel):
    """Simplified synchronous query request"""
    query: str = Field(..., min_length=1, description="User question")
    workflow_id: str = Field(default="default_workflow")
    retrieval_profile_id: str = Field(default="balanced_insurance")
    fusion_profile_id: str = Field(default="balanced")
    context_profile_id: str = Field(default="default")
    judge_profile_id: str = Field(default="strict_insurance")
    doc_filter: Optional[Dict[str, Any]] = None
    include_metadata: bool = Field(default=False, description="Include run_id and debug info")


class QueryResponse(BaseModel):
    """Simplified synchronous query response"""
    answer: str = Field(..., description="Generated answer text")
    citations: List[Citation] = Field(..., description="Supporting citations")
    confidence: str = Field(..., description="Confidence level: high/medium/low")
    judge_passed: bool = Field(..., description="Whether answer passed validation")
    judge_decision: str = Field(..., description="PASS, FAIL_BLOCKED, or FAIL_RETRYABLE")
    assumptions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Debug metadata (if include_metadata=True)")


class ChatRequest(BaseModel):
    """Simplified synchronous chat request"""
    message: str = Field(..., min_length=1, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for continuing conversation")
    workflow_id: str = Field(default="default_workflow")
    chat_profile_id: str = Field(default="default")
    retrieval_profile_id: str = Field(default="balanced_insurance")
    fusion_profile_id: str = Field(default="balanced")
    context_profile_id: str = Field(default="default")
    judge_profile_id: str = Field(default="strict_insurance")
    doc_filter: Optional[Dict[str, Any]] = None
    include_metadata: bool = Field(default=False)


class ChatResponse(BaseModel):
    """Simplified synchronous chat response"""
    answer: str = Field(..., description="Generated answer text")
    citations: List[Citation] = Field(..., description="Supporting citations")
    confidence: str = Field(..., description="Confidence level")
    session_id: str = Field(..., description="Session ID (use in next request)")
    turn_number: int = Field(..., description="Current turn number")
    session_created: bool = Field(default=False, description="True if this started a new session")
    session_terminated: bool = Field(default=False, description="True if session was ended")
    history_compacted: bool = Field(default=False, description="True if history was compacted")
    judge_passed: bool = Field(..., description="Whether answer passed validation")
    judge_decision: str = Field(..., description="Judge decision")
    assumptions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
