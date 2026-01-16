"""
Synchronous API endpoints for Query and Chat modes
Provides simplified request-response pattern without SSE streaming
"""

from fastapi import APIRouter, HTTPException
import logging
import asyncio
from typing import Dict, Any

from app.core.models import (
    QueryRequest, QueryResponse,
    ChatRequest, ChatResponse
)
from app.core.orchestrator import RunOrchestrator
from app.core.config_loader import get_config_loader

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize orchestrator and config loader
orchestrator = RunOrchestrator()
config_loader = get_config_loader()


def _transform_to_query_response(
    result: Dict[str, Any],
    include_metadata: bool
) -> QueryResponse:
    """
    Transform orchestrator result to simplified QueryResponse

    Args:
        result: Orchestrator execution result
        include_metadata: Whether to include debug metadata

    Returns:
        QueryResponse with simplified structure

    Raises:
        HTTPException: If answer is blocked by judge
    """
    answer = result.get("answer")
    judge_report = result.get("judge_report")
    status = result.get("status")

    # Handle blocked answers
    if status == "blocked" and answer is None:
        violations = []
        if judge_report and judge_report.violations:
            violations = [
                {
                    "check": v.check,
                    "severity": v.severity,
                    "message": v.message
                }
                for v in judge_report.violations
            ]

        raise HTTPException(
            status_code=403,
            detail={
                "error": "Answer blocked by judge validation",
                "violations": violations
            }
        )

    # Handle failed execution
    if status == "failed":
        error_msg = result.get("error", "Pipeline execution failed")
        raise HTTPException(
            status_code=500,
            detail={
                "error": error_msg,
                "run_id": result.get("run_id") if include_metadata else None
            }
        )

    # Extract judge decision
    judge_passed = judge_report.passed if judge_report else True
    judge_decision = "SKIPPED"
    if judge_report:
        if judge_report.passed:
            judge_decision = "PASS"
        elif judge_report.decision in ["FAIL_BLOCKED", "FAIL_RETRYABLE"]:
            judge_decision = judge_report.decision
        else:
            judge_decision = "FAIL_BLOCKED" if not judge_report.passed else "PASS"

    # Build metadata if requested
    metadata = None
    if include_metadata and answer:
        metadata = {
            "run_id": result.get("run_id"),
            "tokens_used": answer.tokens_used,
            "cost": answer.cost,
            "status": status
        }

    # Return simplified response
    return QueryResponse(
        answer=answer.answer,
        citations=answer.citations,
        confidence=answer.confidence.value if answer.confidence else "medium",
        judge_passed=judge_passed,
        judge_decision=judge_decision,
        assumptions=answer.assumptions,
        limitations=answer.limitations,
        metadata=metadata
    )


def _transform_to_chat_response(
    result: Dict[str, Any],
    session_created: bool,
    include_metadata: bool
) -> ChatResponse:
    """
    Transform orchestrator result to simplified ChatResponse

    Args:
        result: Orchestrator execution result
        session_created: Whether a new session was created
        include_metadata: Whether to include debug metadata

    Returns:
        ChatResponse with simplified structure and session info

    Raises:
        HTTPException: If answer is blocked by judge or execution fails
    """
    answer = result.get("answer")
    judge_report = result.get("judge_report")
    status = result.get("status")
    session_id = result.get("session_id")
    turn_number = result.get("turn_number", 0)
    history_compacted = result.get("history_compacted", False)

    # Handle session termination (Quit command)
    if status == "terminated":
        return ChatResponse(
            answer="",
            citations=[],
            confidence="high",
            session_id=session_id,
            turn_number=0,
            session_created=False,
            session_terminated=True,
            history_compacted=False,
            judge_passed=True,
            judge_decision="SKIPPED",
            assumptions=[],
            limitations=[],
            metadata=None
        )

    # Handle blocked answers
    if status == "blocked" and answer is None:
        violations = []
        if judge_report and judge_report.violations:
            violations = [
                {
                    "check": v.check,
                    "severity": v.severity,
                    "message": v.message
                }
                for v in judge_report.violations
            ]

        raise HTTPException(
            status_code=403,
            detail={
                "error": "Answer blocked by judge validation",
                "violations": violations,
                "session_id": session_id
            }
        )

    # Handle failed execution
    if status == "failed":
        error_msg = result.get("error", "Pipeline execution failed")
        raise HTTPException(
            status_code=500,
            detail={
                "error": error_msg,
                "session_id": session_id,
                "run_id": result.get("run_id") if include_metadata else None
            }
        )

    # Extract judge decision
    judge_passed = judge_report.passed if judge_report else True
    judge_decision = "SKIPPED"
    if judge_report:
        if judge_report.passed:
            judge_decision = "PASS"
        elif judge_report.decision in ["FAIL_BLOCKED", "FAIL_RETRYABLE"]:
            judge_decision = judge_report.decision
        else:
            judge_decision = "FAIL_BLOCKED" if not judge_report.passed else "PASS"

    # Build metadata if requested
    metadata = None
    if include_metadata and answer:
        metadata = {
            "run_id": result.get("run_id"),
            "tokens_used": answer.tokens_used,
            "cost": answer.cost,
            "status": status
        }

    # Return simplified response
    return ChatResponse(
        answer=answer.answer,
        citations=answer.citations,
        confidence=answer.confidence.value if answer.confidence else "medium",
        session_id=session_id,
        turn_number=turn_number,
        session_created=session_created,
        session_terminated=False,
        history_compacted=history_compacted,
        judge_passed=judge_passed,
        judge_decision=judge_decision,
        assumptions=answer.assumptions,
        limitations=answer.limitations,
        metadata=metadata
    )


@router.post("/query", response_model=QueryResponse)
async def sync_query(request: QueryRequest):
    """
    Execute a synchronous RAG query

    This endpoint provides a simplified, Postman-friendly interface for RAG queries.
    It executes the full pipeline and returns the answer with citations in a single
    synchronous request-response (no SSE streaming required).

    Args:
        request: QueryRequest with query text and configuration

    Returns:
        QueryResponse with answer, citations, and judge validation

    Raises:
        HTTPException: 400 for invalid input, 403 for blocked answer,
                      500 for execution failure, 504 for timeout
    """
    logger.info(f"Synchronous query: {request.query[:100]}...")

    try:
        # Validate workflow exists
        try:
            workflow = config_loader.get_workflow_profile(request.workflow_id)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid workflow_id: {request.workflow_id}"
            )

        # Execute query with timeout
        result = await asyncio.wait_for(
            orchestrator.execute_run(
                query=request.query,
                workflow_id=request.workflow_id,
                retrieval_profile_id=request.retrieval_profile_id,
                fusion_profile_id=request.fusion_profile_id,
                context_profile_id=request.context_profile_id,
                judge_profile_id=request.judge_profile_id,
                doc_filter=request.doc_filter,
                mode="query"
            ),
            timeout=300.0  # 5 minutes max
        )

        # Transform to simplified response
        return _transform_to_query_response(result, request.include_metadata)

    except asyncio.TimeoutError:
        logger.error("Query execution timeout (5 minutes)")
        raise HTTPException(
            status_code=504,
            detail="Query execution timeout (5 minutes). Try a simpler query or check system load."
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error executing synchronous query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
async def sync_chat(request: ChatRequest):
    """
    Execute a synchronous chat turn

    This endpoint provides session-based conversational RAG with automatic session
    management. The first message creates a session, subsequent messages continue it,
    and "Quit" terminates the session.

    Args:
        request: ChatRequest with message and optional session_id

    Returns:
        ChatResponse with answer, citations, and session info

    Raises:
        HTTPException: 400 for invalid input/quit without session, 403 for blocked answer,
                      500 for execution failure, 504 for timeout
    """
    logger.info(f"Synchronous chat: {request.message[:100]}... (session: {request.session_id})")

    try:
        # Check for quit command
        if orchestrator.chat_manager.check_quit_command(request.message):
            if request.session_id:
                # Terminate existing session
                orchestrator.chat_manager.delete_session(request.session_id)
                logger.info(f"Session terminated: {request.session_id}")

                return ChatResponse(
                    answer="",
                    citations=[],
                    confidence="high",
                    session_id=request.session_id,
                    turn_number=0,
                    session_created=False,
                    session_terminated=True,
                    history_compacted=False,
                    judge_passed=True,
                    judge_decision="SKIPPED",
                    assumptions=[],
                    limitations=[],
                    metadata=None
                )
            else:
                # Quit without active session
                raise HTTPException(
                    status_code=400,
                    detail="No active session to terminate. Start a conversation first."
                )

        # Track if we're creating a new session
        session_created = False
        session_id = request.session_id

        if not session_id:
            # First message - session will be auto-created by orchestrator
            session_created = True
            logger.info("Creating new chat session")
        elif not orchestrator.chat_manager.get_session(session_id):
            # Invalid session - will be recreated
            logger.warning(f"Session {session_id} not found, creating new session")
            session_created = True
            session_id = None  # Let orchestrator create new one

        # Validate workflow exists
        try:
            workflow = config_loader.get_workflow_profile(request.workflow_id)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid workflow_id: {request.workflow_id}"
            )

        # Execute chat with timeout
        result = await asyncio.wait_for(
            orchestrator.execute_run(
                query=request.message,
                workflow_id=request.workflow_id,
                retrieval_profile_id=request.retrieval_profile_id,
                fusion_profile_id=request.fusion_profile_id,
                context_profile_id=request.context_profile_id,
                judge_profile_id=request.judge_profile_id,
                doc_filter=request.doc_filter,
                mode="chat",
                session_id=session_id,
                chat_profile_id=request.chat_profile_id
            ),
            timeout=300.0  # 5 minutes max
        )

        # Transform to simplified response
        return _transform_to_chat_response(result, session_created, request.include_metadata)

    except asyncio.TimeoutError:
        logger.error("Chat execution timeout (5 minutes)")
        raise HTTPException(
            status_code=504,
            detail="Chat execution timeout (5 minutes). Try a simpler question or check system load."
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error executing synchronous chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
