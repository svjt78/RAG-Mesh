"""
Run Execution API routes
Handles query execution with SSE streaming
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, AsyncGenerator
import logging
import json
import asyncio

from app.core.models import RunRequest, RunResponse
from app.core.orchestrator import RunOrchestrator
from app.core.config_loader import get_config_loader

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize orchestrator
orchestrator = RunOrchestrator()
config_loader = get_config_loader()

# Store active SSE connections (run_id -> queue)
active_streams = {}


@router.post("/run", response_model=RunResponse)
async def execute_run(request: RunRequest):
    """
    Execute a RAG query run (Query or Chat mode)

    Args:
        request: Run request with query and configuration

    Returns:
        Run response with run_id and status
    """
    logger.info(f"Executing run with query: {request.query[:100]}... (mode: {request.mode})")

    try:
        # Validate workflow exists
        workflow = config_loader.get_workflow_profile(request.workflow_id)

        # Execute run with chat mode support
        result = await orchestrator.execute_run(
            query=request.query,
            workflow_id=request.workflow_id,
            chunking_profile_id=request.chunking_profile_id,
            retrieval_profile_id=request.retrieval_profile_id,
            fusion_profile_id=request.fusion_profile_id,
            context_profile_id=request.context_profile_id,
            judge_profile_id=request.judge_profile_id,
            doc_filter=request.doc_filter,
            mode=request.mode,
            session_id=request.session_id,
            chat_profile_id=request.chat_profile_id or "default"
        )

        return RunResponse(
            run_id=result["run_id"],
            status=result["status"],
            sse_endpoint=f"/api/run/{result['run_id']}/stream",
            answer=result.get("answer"),
            judge_report=result.get("judge_report"),
            metadata=result.get("metadata", {}),
            session_id=result.get("session_id"),
            turn_number=result.get("turn_number"),
            history_compacted=result.get("history_compacted", False)
        )

    except Exception as e:
        logger.error(f"Error executing run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}")
async def get_run_status(run_id: str):
    """
    Get run status and results

    Args:
        run_id: Run ID to query

    Returns:
        Run status and artifacts
    """
    logger.info(f"Getting run status: {run_id}")

    try:
        # Load run metadata
        from pathlib import Path
        run_dir = Path("data/runs") / run_id

        if not run_dir.exists():
            raise HTTPException(status_code=404, detail="Run not found")

        # Load artifacts
        artifacts = {}
        artifacts_dir = run_dir / "artifacts"
        if artifacts_dir.exists():
            for artifact_file in artifacts_dir.glob("*.json"):
                with open(artifact_file) as f:
                    artifacts[artifact_file.stem] = json.load(f)

        # Load events
        events = []
        events_file = run_dir / "events.jsonl"
        if events_file.exists():
            with open(events_file) as f:
                for line in f:
                    events.append(json.loads(line))

        status = "unknown"
        session_id = None
        turn_number = None
        history_compacted = False

        # Parse events to extract status and chat metadata
        for event in reversed(events):
            event_type = event.get("event_type")
            if event_type == "run_failed":
                status = "failed"
                break
            if event_type == "run_blocked":
                status = "blocked"
                break
            if event_type == "run_completed":
                status = "completed"
                break

        # Extract chat metadata from events (forward order to get latest)
        for event in events:
            event_type = event.get("event_type")
            event_data = event.get("data", {})

            # Session ID can be in run_started or chat_session_created events
            if event_type == "run_started" and event_data.get("session_id"):
                session_id = event_data.get("session_id")
            elif event_type == "chat_session_created":
                session_id = event_data.get("session_id")
            elif event_type == "chat_turn_added":
                turn_number = event_data.get("turn_number")
            elif event_type == "chat_compacted":
                history_compacted = True

        return {
            "run_id": run_id,
            "artifacts": artifacts,
            "events": events,
            "status": status,
            "session_id": session_id,
            "turn_number": turn_number,
            "history_compacted": history_compacted
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting run status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/run/{run_id}/stream")
async def stream_run_events(run_id: str, request: Request):
    """
    Stream run events via Server-Sent Events (SSE)

    Args:
        run_id: Run ID to stream
        request: FastAPI request object

    Returns:
        SSE stream of events
    """
    logger.info(f"Starting SSE stream for run: {run_id}")

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events"""
        try:
            # Create event queue for this stream
            event_queue = asyncio.Queue()
            active_streams[run_id] = event_queue

            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'run_id': run_id})}\n\n"

            # Check if run already completed (race condition fix)
            try:
                run_data = await orchestrator.get_run(run_id)
                if run_data and run_data.get("status") in ["completed", "failed", "blocked", "terminated"]:
                    logger.info(f"Run {run_id} already completed, sending run_complete event")
                    yield f"data: {json.dumps({'type': 'run_complete', 'run_id': run_id})}\n\n"
                    return
            except Exception as e:
                logger.warning(f"Could not check run status: {e}")

            # Stream events from queue
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from stream: {run_id}")
                    break

                try:
                    # Wait for event with timeout
                    event = await asyncio.wait_for(event_queue.get(), timeout=1.0)

                    # Send event
                    yield f"data: {json.dumps(event)}\n\n"

                    # Check if this is the final event
                    if event.get("type") == "run_complete":
                        break

                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f": heartbeat\n\n"

        except Exception as e:
            logger.error(f"Error in SSE stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        finally:
            # Clean up
            if run_id in active_streams:
                del active_streams[run_id]
            logger.info(f"SSE stream closed: {run_id}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.post("/run/{run_id}/events")
async def emit_event(run_id: str, event: dict):
    """
    Emit an event to active SSE streams (internal use)

    Args:
        run_id: Run ID
        event: Event data
    """
    if run_id in active_streams:
        await active_streams[run_id].put(event)
    return {"status": "emitted"}


@router.get("/runs")
async def list_runs(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None
):
    """
    List recent runs

    Args:
        limit: Maximum number of runs to return
        offset: Number of runs to skip
        status: Filter by status (optional)

    Returns:
        List of runs with metadata
    """
    logger.info(f"Listing runs: limit={limit}, offset={offset}")

    try:
        from pathlib import Path
        runs_dir = Path("data/runs")

        if not runs_dir.exists():
            return {"runs": [], "total": 0}

        # Get all run directories
        run_dirs = sorted(runs_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)

        runs = []
        for run_dir in run_dirs[offset:offset + limit]:
            if not run_dir.is_dir():
                continue

            try:
                events_file = run_dir / "events.jsonl"
                run_status = "unknown"
                if events_file.exists():
                    events = []
                    with open(events_file) as f:
                        for line in f:
                            if line.strip():
                                events.append(json.loads(line))
                    for event in reversed(events):
                        event_type = event.get("event_type")
                        if event_type == "run_failed":
                            run_status = "failed"
                            break
                        if event_type == "run_blocked":
                            run_status = "blocked"
                            break
                        if event_type == "run_completed":
                            run_status = "completed"
                            break

                # Apply status filter
                if status and run_status != status:
                    continue

                runs.append({
                    "run_id": run_dir.name,
                    "status": run_status,
                    "created_at": run_dir.stat().st_mtime,
                })

            except Exception as e:
                logger.warning(f"Error loading run {run_dir.name}: {e}")
                continue

        return {
            "runs": runs,
            "total": len(run_dirs),
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        logger.error(f"Error listing runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/run/{run_id}")
async def delete_run(run_id: str):
    """
    Delete a run and its artifacts

    Args:
        run_id: Run ID to delete

    Returns:
        Deletion confirmation
    """
    logger.info(f"Deleting run: {run_id}")

    try:
        from pathlib import Path
        import shutil

        run_dir = Path("data/runs") / run_id

        if not run_dir.exists():
            raise HTTPException(status_code=404, detail="Run not found")

        # Delete run directory
        shutil.rmtree(run_dir)

        return {"status": "deleted", "run_id": run_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Chat Session Management Endpoints
# ============================================================================

@router.get("/chat/session/{session_id}")
async def get_chat_session(session_id: str):
    """
    Get chat session details

    Args:
        session_id: Session identifier

    Returns:
        Session details including history
    """
    try:
        session = orchestrator.chat_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/session/{session_id}")
async def delete_chat_session(session_id: str):
    """
    Delete chat session

    Args:
        session_id: Session identifier

    Returns:
        Deletion confirmation
    """
    try:
        orchestrator.chat_manager.delete_session(session_id)
        return {"status": "deleted", "session_id": session_id}
    except Exception as e:
        logger.error(f"Error deleting chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/sessions")
async def list_chat_sessions():
    """
    List all active chat sessions

    Returns:
        List of session summaries
    """
    try:
        sessions = [
            {
                "session_id": sid,
                "total_turns": session.history.total_turns,
                "total_tokens": session.total_tokens,
                "created_at": session.created_at.isoformat(),
                "last_updated": session.last_updated.isoformat(),
                "workflow_id": session.workflow_id,
                "chat_profile_id": session.chat_profile_id
            }
            for sid, session in orchestrator.chat_manager.sessions.items()
        ]
        return {"sessions": sessions, "total": len(sessions)}
    except Exception as e:
        logger.error(f"Error listing chat sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
