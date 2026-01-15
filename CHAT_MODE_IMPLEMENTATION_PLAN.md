# Chat Mode Implementation Plan for RAGMesh

## Executive Summary

This document outlines the complete implementation plan for adding **Chat Mode** to RAGMesh, enabling stateful multi-turn conversations while maintaining full backward compatibility with the existing stateless Query Mode.

### Key Features
- **Mode Selection**: Toggle between Query mode (default, stateless) and Chat mode (stateful, multi-turn)
- **Session Management**: In-memory chat sessions with automatic session lifecycle
- **History Compaction**: LLM-based summarization when conversation exceeds token threshold
- **Full Pipeline Execution**: Each chat turn executes complete RAG pipeline (retrieval → fusion → context → generation → judge)
- **UI Integration**: Dedicated chat history panel in Query tab with scrollable Q&A thread
- **Configuration-Driven**: New `chat_profiles.json` for compaction settings

---

## Requirements Summary

### User Requirements (from clarification)
1. **Storage**: In-memory sessions (lost on refresh)
2. **Compaction Strategy**: LLM Summarization when tokens exceed threshold
3. **Pipeline**: Full RAG pipeline every turn
4. **Display**: Dedicated chat history panel in Query tab
5. **Tabs**: Show only latest turn's data in other tabs
6. **Configuration**: Create `chat_profiles.json`
7. **Exit**: Type "Quit" to end session

### Technical Requirements
- Backward compatibility with Query mode (no breaking changes)
- Session identified by `session_id` (UUID)
- Chat history integrated into context compilation
- Token budget management (history + retrieval context)
- Configuration-driven behavior

---

## Architecture Overview

### Data Flow in Chat Mode

```
1. User submits question in Chat mode
   ↓
2. Frontend sends POST /api/run with mode="chat", session_id (if exists)
   ↓
3. Backend checks "Quit" command → delete session if matched
   ↓
4. Get or create chat session (in-memory)
   ↓
5. Check if compaction needed (tokens > threshold)
   ↓
6. If yes: LLM summarizes older turns, keep recent N turns
   ↓
7. Execute full RAG pipeline:
   - Retrieval (tri-modal: vector, document, graph)
   - Fusion (weighted RRF)
   - Context compilation (history + retrieval, token budget managed)
   - Generation (chat-aware prompt with history)
   - Judge validation
   ↓
8. Add turn to chat session
   ↓
9. Return response with session_id, turn_number, answer
   ↓
10. Frontend appends Q&A to chat history panel
    Updates latest turn data in other tabs
```

---

## Backend Implementation

### 1. Data Models (Pydantic)

**File**: `backend/app/core/models.py`

#### New Models

```python
class ChatTurn(BaseModel):
    """Single turn in a chat conversation"""
    turn_number: int = Field(..., ge=1)
    query: str = Field(..., description="User query")
    answer: Answer = Field(..., description="Generated answer")
    run_id: str = Field(..., description="Associated run ID")
    timestamp: datetime = Field(default_factory=datetime.now)
    tokens: int = Field(..., ge=0, description="Total tokens used in this turn")

class ChatHistory(BaseModel):
    """Chat conversation history"""
    turns: List[ChatTurn] = Field(default_factory=list)
    summary: Optional[str] = Field(None, description="LLM-generated summary of older turns")
    summary_covers_turns: List[int] = Field(default_factory=list)
    total_turns: int = Field(default=0, ge=0)

class ChatSession(BaseModel):
    """Complete chat session state"""
    session_id: str = Field(..., description="Unique session identifier")
    history: ChatHistory = Field(default_factory=ChatHistory)
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    total_tokens: int = Field(default=0, ge=0)
    workflow_id: str = Field(default="default_workflow")
    chat_profile_id: str = Field(default="default")

class ChatProfile(BaseModel):
    """Chat mode configuration"""
    description: str = Field(default="Chat configuration")
    compaction_threshold_tokens: int = Field(default=2000, ge=500)
    max_history_turns: int = Field(default=10, ge=1)
    summarization_model: str = Field(default="gpt-3.5-turbo")
    summarization_max_tokens: int = Field(default=500, ge=100)
    include_summary_in_context: bool = Field(default=True)
    summary_position: str = Field(default="before_retrieval")
    reserve_tokens_for_history: int = Field(default=800, ge=0)
```

#### Extend Existing Models

```python
class RunRequest(BaseModel):
    # ... existing fields ...
    mode: Literal["query", "chat"] = Field(default="query")
    session_id: Optional[str] = Field(None)
    chat_profile_id: Optional[str] = Field(default="default")

class RunResponse(BaseModel):
    # ... existing fields ...
    session_id: Optional[str] = Field(None)
    turn_number: Optional[int] = Field(None)
    history_compacted: bool = Field(default=False)

class EventType(str, Enum):
    # ... existing events ...
    CHAT_SESSION_CREATED = "chat_session_created"
    CHAT_COMPACTED = "chat_compacted"
    CHAT_TURN_ADDED = "chat_turn_added"
    CHAT_SESSION_TERMINATED = "chat_session_terminated"
```

---

### 2. Configuration File

**File**: `config/chat_profiles.json` (NEW)

```json
{
  "description": "Chat mode configurations",
  "profiles": {
    "default": {
      "description": "Standard chat configuration",
      "compaction_threshold_tokens": 2000,
      "max_history_turns": 10,
      "summarization_model": "gpt-3.5-turbo",
      "summarization_max_tokens": 500,
      "include_summary_in_context": true,
      "summary_position": "before_retrieval",
      "reserve_tokens_for_history": 800
    },
    "long_context": {
      "description": "Extended chat history support",
      "compaction_threshold_tokens": 4000,
      "max_history_turns": 20,
      "summarization_model": "gpt-3.5-turbo",
      "summarization_max_tokens": 800,
      "include_summary_in_context": true,
      "summary_position": "before_retrieval",
      "reserve_tokens_for_history": 1500
    },
    "compact": {
      "description": "Minimal chat history",
      "compaction_threshold_tokens": 1000,
      "max_history_turns": 5,
      "summarization_model": "gpt-3.5-turbo",
      "summarization_max_tokens": 300,
      "include_summary_in_context": true,
      "summary_position": "before_retrieval",
      "reserve_tokens_for_history": 500
    }
  },
  "default_profile": "default"
}
```

---

### 3. Chat Session Manager

**File**: `backend/app/core/chat_manager.py` (NEW)

**Key Responsibilities**:
- In-memory session storage (`Dict[session_id, ChatSession]`)
- Session lifecycle (create, get, delete)
- Turn management (add turn to session)
- Compaction logic (check threshold, trigger summarization)
- History formatting for context

**Key Methods**:
```python
class ChatSessionManager:
    def __init__(self, llm_adapter: LLMAdapter)
    def create_session(workflow_id, chat_profile_id) -> session_id
    def get_session(session_id) -> ChatSession
    def add_turn(session_id, query, answer, run_id, tokens) -> turn_number
    async def check_and_compact(session_id, profile) -> bool
    async def _compact_history(session, profile)
    def get_formatted_history(session_id, profile, encoding) -> (text, tokens)
    def delete_session(session_id)
    def check_quit_command(query) -> bool
```

**Compaction Algorithm**:
1. Calculate total history tokens
2. Check if exceeds `compaction_threshold_tokens` OR exceeds `max_history_turns`
3. Keep last N/2 turns in full detail
4. Summarize older turns using LLM
5. Update session with summary and reduced turn list

---

### 4. Config Loader Changes

**File**: `backend/app/core/config_loader.py`

**Changes**:
1. Load `chat_profiles.json` in `_load_all_configs()`
2. Add method: `get_chat_profile(profile_id: str) -> ChatProfile`
3. Update `list_profiles()` to include chat profiles

---

### 5. Context Compiler Modifications

**File**: `backend/app/modules/context_compiler.py`

**New Method**: `compile_context_with_chat()`

**Key Logic**:
```python
async def compile_context_with_chat(
    fused_results,
    query,
    profile,
    chat_history_text,
    chat_history_tokens,
    chat_profile
) -> ContextPack:
    # Calculate retrieval budget = total budget - history tokens - reserved
    retrieval_budget = profile.max_context_tokens - chat_history_tokens
    retrieval_budget -= (reserve_for_query + reserve_for_instructions)

    # Pack retrieval chunks within reduced budget
    packed_chunks, retrieval_context, retrieval_tokens = await _pack_chunks(
        chunks, retrieval_budget, profile
    )

    # Combine history + retrieval based on position
    if chat_profile.summary_position == "before_retrieval":
        combined = f"{chat_history_text}\n\n[Current Query Context]\n{retrieval_context}"
    else:
        combined = f"{retrieval_context}\n\n[Conversation History]\n{chat_history_text}"

    # Return ContextPack with combined context
```

---

### 6. Generation Module Modifications

**File**: `backend/app/modules/generation.py`

**Changes**:
1. Modify `_build_system_prompt()` to accept `is_chat_mode` flag
2. Add chat-specific instructions when in chat mode
3. Add method: `generate_answer_chat()` (uses chat-aware prompt)

**Chat Mode System Prompt Addition**:
```
CHAT MODE INSTRUCTIONS:
- You are in a multi-turn conversation with the user
- Previous conversation history is provided for context
- Reference previous exchanges when relevant
- Maintain consistency with previous answers
- If user refers to "earlier" topics, use conversation history
```

---

### 7. Orchestrator Modifications

**File**: `backend/app/core/orchestrator.py`

**Key Changes**:

1. **Initialize ChatSessionManager** in `__init__()`
```python
from app.core.chat_manager import ChatSessionManager
self.chat_manager = ChatSessionManager(self.llm)
```

2. **Extend `execute_run()` signature**:
```python
async def execute_run(
    # ... existing params ...
    mode: str = "query",
    session_id: Optional[str] = None,
    chat_profile_id: str = "default"
)
```

3. **Add chat mode handling**:
```python
# Check for quit command
if mode == "chat" and self.chat_manager.check_quit_command(query):
    if session_id:
        self.chat_manager.delete_session(session_id)
    return {"status": "terminated", "session_id": session_id}

# Get or create session
if mode == "chat":
    if not session_id:
        session_id = self.chat_manager.create_session(workflow_id, chat_profile_id)
    chat_session = self.chat_manager.get_session(session_id)
    chat_profile = config_loader.get_chat_profile(chat_profile_id)

    # Check and compact if needed
    history_compacted = await self.chat_manager.check_and_compact(
        session_id, chat_profile
    )
```

4. **Modify context compilation**:
```python
if mode == "chat":
    history_text, history_tokens = self.chat_manager.get_formatted_history(
        session_id, chat_profile, self.context_compiler.encoding
    )
    context_pack = await self.context_compiler.compile_context_with_chat(
        fused_results, query, context_profile,
        history_text, history_tokens, chat_profile
    )
else:
    context_pack = await self.context_compiler.compile_context(
        fused_results, query, context_profile
    )
```

5. **Modify generation**:
```python
if mode == "chat":
    answer = await self.generation.generate_answer_chat(query, context_pack)
else:
    answer = await self.generation.generate_answer(query, context_pack)
```

6. **Add turn to session**:
```python
if mode == "chat" and not blocked_by_judge:
    turn_number = self.chat_manager.add_turn(
        session_id, query, answer, run_id,
        tokens=answer.tokens_used + context_pack.tokens_used
    )
```

---

### 8. API Route Changes

**File**: `backend/app/api/run.py`

**Modify `execute_run` endpoint**:
```python
@router.post("/run", response_model=RunResponse)
async def execute_run(request: RunRequest):
    result = await orchestrator.execute_run(
        query=request.query,
        workflow_id=request.workflow_id,
        # ... existing params ...
        mode=request.mode,
        session_id=request.session_id,
        chat_profile_id=request.chat_profile_id or "default"
    )

    return RunResponse(
        # ... existing fields ...
        session_id=result.get("session_id"),
        turn_number=result.get("turn_number"),
        history_compacted=result.get("history_compacted", False)
    )
```

**Add new endpoints**:
```python
@router.get("/chat/session/{session_id}")
async def get_chat_session(session_id: str):
    """Get chat session details"""
    session = orchestrator.chat_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.model_dump()

@router.delete("/chat/session/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete chat session"""
    orchestrator.chat_manager.delete_session(session_id)
    return {"status": "deleted", "session_id": session_id}

@router.get("/chat/sessions")
async def list_chat_sessions():
    """List all active chat sessions"""
    sessions = [
        {
            "session_id": sid,
            "total_turns": session.history.total_turns,
            "created_at": session.created_at,
            "last_updated": session.last_updated
        }
        for sid, session in orchestrator.chat_manager.sessions.items()
    ]
    return {"sessions": sessions, "total": len(sessions)}
```

---

## Frontend Implementation

### 1. TypeScript Type Definitions

**File**: `frontend/lib/types.ts`

```typescript
export interface ChatTurn {
  turn_number: number;
  query: string;
  answer: Answer;
  run_id: string;
  timestamp: string;
  tokens: number;
}

export interface ChatHistory {
  turns: ChatTurn[];
  summary: string | null;
  summary_covers_turns: number[];
  total_turns: number;
}

export interface ChatSession {
  session_id: string;
  history: ChatHistory;
  created_at: string;
  last_updated: string;
  total_tokens: number;
  workflow_id: string;
  chat_profile_id: string;
}

// Extend RunData
export interface RunData {
  // ... existing fields ...
  session_id?: string;
  turn_number?: number;
  history_compacted?: boolean;
}
```

---

### 2. API Client Extensions

**File**: `frontend/lib/api.ts`

```typescript
export interface RunRequest {
  // ... existing fields ...
  mode?: 'query' | 'chat';
  session_id?: string;
  chat_profile_id?: string;
}

// New methods
async getChatSession(sessionId: string): Promise<ChatSession>
async deleteChatSession(sessionId: string): Promise<any>
async listChatSessions(): Promise<{ sessions: any[]; total: number }>
async listChatProfiles(): Promise<any>
async getChatProfile(profileId: string): Promise<any>
```

---

### 3. Query Tab UI Modifications

**File**: `frontend/components/QueryTab.tsx`

**Major UI Changes**:

1. **Add mode toggle switch** (above query textarea):
```tsx
<div className="mb-4">
  <label className="block text-sm font-medium text-gray-700 mb-2">
    Execution Mode
  </label>
  <div className="flex items-center gap-4">
    <button
      onClick={() => setMode('query')}
      className={mode === 'query' ? 'bg-blue-600 text-white' : 'bg-gray-200'}
    >
      Query Mode
    </button>
    <button
      onClick={() => setMode('chat')}
      className={mode === 'chat' ? 'bg-blue-600 text-white' : 'bg-gray-200'}
    >
      Chat Mode
    </button>
  </div>
</div>
```

2. **Add chat history panel** (shown when mode === 'chat'):
```tsx
{mode === 'chat' && (
  <div className="border rounded-lg bg-white">
    <div className="px-4 py-3 border-b">
      <div className="font-semibold">
        Chat History (Session: {sessionId?.slice(0, 8)}...)
      </div>
      <button onClick={endSession}>End Session</button>
    </div>
    <div className="p-4 max-h-96 overflow-y-auto">
      {chatHistory.map(turn => (
        <div key={turn.turn_number}>
          <div className="bg-blue-50 p-3">User: {turn.query}</div>
          <div className="bg-gray-50 p-3">Assistant: {turn.answer.answer}</div>
        </div>
      ))}
    </div>
  </div>
)}
```

3. **Update placeholder** for query input:
```tsx
placeholder={
  mode === 'query'
    ? "e.g., What are the exclusions for flood damage..."
    : "Ask a follow-up question or type 'Quit' to end the session..."
}
```

4. **Modify handleSubmit**:
```typescript
const handleSubmit = async (e: React.FormEvent) => {
  const request: RunRequest = {
    query: query.trim(),
    workflow_id: workflowId,
    mode: mode,
    ...(mode === 'chat' && {
      session_id: sessionId,
      chat_profile_id: 'default'
    })
  };

  const response = await apiClient.executeRun(request);

  if (mode === 'chat' && response.session_id) {
    setSessionId(response.session_id);
  }

  setQuery(''); // Clear for next turn
};
```

5. **Add useEffect to update chat history**:
```typescript
useEffect(() => {
  if (mode === 'chat' && runData?.session_id && runData?.artifacts?.answer) {
    const latestTurn: ChatTurn = {
      turn_number: runData.turn_number || chatHistory.length + 1,
      query: currentQuery,
      answer: runData.artifacts.answer,
      run_id: runData.run_id,
      timestamp: new Date().toISOString(),
      tokens: 0
    };
    setChatHistory(prev => [...prev, latestTurn]);
  }
}, [runData]);
```

---

### 4. Page State Management

**File**: `frontend/app/page.tsx`

**Changes**:
1. Add state: `currentMode`, `currentSessionId`
2. Update `handleRunStart` to accept mode and sessionId
3. Pass mode to QueryTab
4. In chat mode, don't clear runData (maintain history in tabs)

---

## Testing Strategy

### Unit Tests

**New Test Files**:
- `backend/tests/test_chat_manager.py`
  - test_create_session
  - test_add_turn
  - test_compaction_trigger
  - test_compaction_summary_generation
  - test_quit_command

**Modified Test Files**:
- `backend/tests/modules/test_context_compiler.py`
  - test_compile_context_with_chat_history

### Integration Tests

**File**: `backend/tests/api/test_run.py`

**New Tests**:
- test_execute_run_chat_mode_new_session
- test_execute_run_chat_mode_existing_session
- test_execute_run_chat_mode_quit_command
- test_execute_run_chat_mode_compaction

### End-to-End Tests

**New File**: `backend/tests/test_e2e_chat.py`

**Test Scenarios**:
- Full 3-turn chat session with context awareness
- Compaction trigger with 15 turns
- Quit command and session termination
- Token budget verification

### Regression Tests

**Verification**:
- Run existing test suite: `pytest -m unit`
- Ensure all query mode tests pass unchanged
- Verify `mode="query"` produces identical results

---

## Implementation Sequence

### Phase 1: Foundation (Backend Models & Config)
1. ✅ Add Pydantic models to `models.py`
2. ✅ Create `chat_profiles.json`
3. ✅ Update `config_loader.py`
4. ✅ Write unit tests for models

### Phase 2: Core Chat Logic
5. ✅ Implement `chat_manager.py`
6. ✅ Write unit tests for ChatSessionManager
7. ✅ Test compaction logic in isolation

### Phase 3: Pipeline Integration
8. ✅ Modify `context_compiler.py`
9. ✅ Modify `generation.py`
10. ✅ Modify `orchestrator.py`
11. ✅ Write integration tests

### Phase 4: API Layer
12. ✅ Update `run.py` API endpoints
13. ✅ Add chat session management endpoints
14. ✅ Test with curl/Postman

### Phase 5: Frontend
15. ✅ Update TypeScript types
16. ✅ Extend API client
17. ✅ Modify QueryTab.tsx
18. ✅ Update page.tsx state management
19. ✅ Manual UI testing

### Phase 6: End-to-End Testing
20. ✅ Write E2E chat tests
21. ✅ Run full regression suite
22. ✅ Manual testing of both modes

### Phase 7: Polish
23. ✅ Add loading states and error handling
24. ✅ Add compaction notifications
25. ✅ Documentation updates

---

## Critical Files Summary

### Top 5 Most Critical Files

1. **`backend/app/core/chat_manager.py`** (NEW) - ~300 lines
   - Core session management, compaction algorithm

2. **`backend/app/core/orchestrator.py`** (MODIFY)
   - Central integration point, mode switching logic

3. **`backend/app/modules/context_compiler.py`** (MODIFY)
   - Chat history integration, token budget management

4. **`frontend/components/QueryTab.tsx`** (MODIFY)
   - All UI changes, user-facing experience

5. **`backend/app/core/models.py`** (MODIFY)
   - All new data structures, type safety foundation

### Additional Important Files

6. `config/chat_profiles.json` (NEW)
7. `backend/app/api/run.py` (MODIFY)
8. `frontend/lib/api.ts` (MODIFY)
9. `backend/app/modules/generation.py` (MODIFY)
10. `backend/app/core/config_loader.py` (MODIFY)

---

## Edge Cases & Considerations

### Edge Cases to Handle

1. **Session expires while user typing** → Create new session gracefully
2. **Very long chat history** → Compaction handles, add max_session_age
3. **Compaction fails (LLM error)** → Fall back to dropping oldest turns
4. **User switches from chat to query mid-session** → Clear session
5. **Browser refresh in chat mode** → Session lost (acceptable)
6. **"Quit" in legitimate query** → Use exact match, case-insensitive
7. **Token budget exhausted by history** → Truncate history aggressively

### Performance Considerations

- In-memory sessions scale to ~1000 concurrent (10KB each = 10MB)
- Compaction adds ~2-3s latency but happens infrequently
- SSE streaming works identically in both modes

### Security Considerations

- Session IDs are UUIDs (secure random)
- Sessions not persisted → no PII storage risk
- PII redaction still applies to chat history

---

## Verification Checklist

### Query Mode (Regression)
- [ ] Single query executes correctly
- [ ] All tabs show data
- [ ] No session_id in response
- [ ] All existing tests pass

### Chat Mode (New)
- [ ] Mode toggle works
- [ ] First question creates session
- [ ] Follow-up questions reference history
- [ ] Chat history panel displays all Q&A
- [ ] Other tabs show only latest turn
- [ ] "Quit" terminates session
- [ ] 15+ turns trigger compaction
- [ ] Compaction notification shown
- [ ] End session button works

---

## Configuration Examples

### Chat Profile: Default
```json
{
  "compaction_threshold_tokens": 2000,
  "max_history_turns": 10,
  "summarization_model": "gpt-3.5-turbo",
  "summarization_max_tokens": 500
}
```

### Chat Profile: Long Context
```json
{
  "compaction_threshold_tokens": 4000,
  "max_history_turns": 20,
  "summarization_model": "gpt-3.5-turbo",
  "summarization_max_tokens": 800
}
```

---

## Appendix: API Examples

### Chat Mode Request
```bash
curl -X POST http://localhost:8017/api/run \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the flood exclusions?",
    "mode": "chat",
    "session_id": null,
    "chat_profile_id": "default",
    "workflow_id": "default_workflow"
  }'
```

### Chat Mode Response
```json
{
  "run_id": "abc123...",
  "status": "completed",
  "session_id": "def456...",
  "turn_number": 1,
  "history_compacted": false,
  "answer": { ... },
  "sse_endpoint": "/api/run/abc123.../stream"
}
```

### Quit Command
```bash
curl -X POST http://localhost:8017/api/run \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quit",
    "mode": "chat",
    "session_id": "def456..."
  }'
```

---

## Conclusion

This implementation plan provides a complete, production-ready design for adding Chat mode to RAGMesh while maintaining 100% backward compatibility with Query mode. The architecture is clean, maintainable, testable, and user-friendly.

**Key Benefits**:
- ✅ Maintains full backward compatibility
- ✅ Configuration-driven behavior
- ✅ Clean separation of concerns
- ✅ Comprehensive testing strategy
- ✅ Scalable in-memory design
- ✅ LLM-based intelligent compaction

**Estimated Implementation Time**: 3-5 days for experienced developer

---

**Document Version**: 1.0
**Last Updated**: 2026-01-13
**Author**: Claude Code Analysis
