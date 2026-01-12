"""
Run orchestrator
Coordinates entire RAG pipeline with event emission
"""

import logging
import uuid
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import aiofiles
import asyncio

from app.core.models import (
    Event, EventType, RetrievalBundle, Answer, JudgeReport
)
from app.core.config_loader import get_config_loader
from app.adapters.file_doc_store import FileDocStoreAdapter
from app.adapters.faiss_vector_store import FAISSVectorStoreAdapter
from app.adapters.networkx_graph_store import NetworkXGraphStoreAdapter
from app.adapters.openai_adapter import OpenAIAdapter
from app.modules.vector_retrieval import VectorRetrievalModule
from app.modules.doc_retrieval import DocumentRetrievalModule
from app.modules.graph_retrieval import GraphRetrievalModule
from app.modules.fusion import FusionModule
from app.modules.context_compiler import ContextCompilerModule
from app.modules.generation import GenerationModule
from app.modules.judge.orchestrator import JudgeOrchestrator

logger = logging.getLogger(__name__)


class RunOrchestrator:
    """Orchestrates complete RAG pipeline execution"""

    def __init__(self, data_dir: Path = Path("data")):
        """
        Initialize orchestrator

        Args:
            data_dir: Root data directory
        """
        self.data_dir = data_dir
        self.runs_dir = data_dir / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)

        # Initialize adapters
        self.doc_store = FileDocStoreAdapter(data_dir)
        self.vector_store = FAISSVectorStoreAdapter(data_dir / "vectors")
        self.graph_store = NetworkXGraphStoreAdapter(data_dir / "graph")
        self.llm = OpenAIAdapter()

        # Initialize modules
        self.vector_retrieval = VectorRetrievalModule(self.vector_store, self.llm)
        self.doc_retrieval = DocumentRetrievalModule(self.doc_store)
        self.graph_retrieval = GraphRetrievalModule(self.graph_store, self.llm)
        self.fusion = FusionModule()
        self.context_compiler = ContextCompilerModule(self.doc_store)
        self.generation = GenerationModule(self.llm)
        self.judge = JudgeOrchestrator(self.llm)

        # Config loader
        self.config_loader = get_config_loader()

        # Event queue
        self.events: list[Event] = []

    async def execute_run(
        self,
        query: str,
        workflow_id: str = "default_workflow",
        chunking_profile_id: str = "default",
        retrieval_profile_id: str = "balanced_insurance",
        fusion_profile_id: str = "balanced",
        context_profile_id: str = "default",
        judge_profile_id: str = "strict_insurance",
        doc_filter: Optional[Dict[str, Any]] = None,
        overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute complete RAG pipeline

        Args:
            query: User query
            workflow_id: Workflow profile ID
            retrieval_profile_id: Retrieval profile ID
            context_profile_id: Context profile ID
            judge_profile_id: Judge profile ID
            overrides: Runtime overrides

        Returns:
            Run result with run_id and status
        """
        # Generate run ID
        run_id = str(uuid.uuid4())
        logger.info(f"Starting run: {run_id}")

        # Create run directory
        run_dir = self.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        artifacts_dir = run_dir / "artifacts"
        artifacts_dir.mkdir(exist_ok=True)

        # Clear events
        self.events = []

        # Load configurations
        workflow = self.config_loader.get_workflow_profile(workflow_id)
        retrieval_profile = self.config_loader.get_retrieval_profile(retrieval_profile_id)
        fusion_profile = self.config_loader.get_fusion_profile(fusion_profile_id)
        context_profile = self.config_loader.get_context_profile(context_profile_id)
        judge_profile = self.config_loader.get_judge_profile(judge_profile_id)

        # Save config snapshot
        config_snapshot = self.config_loader.create_config_snapshot(
            workflow_id, retrieval_profile_id, context_profile_id,
            judge_profile_id, overrides
        )
        await self._save_artifact(artifacts_dir, "config_snapshot.json", config_snapshot)

        try:
            # Emit run started
            await self._emit_event(run_id, EventType.RUN_STARTED, "run_started", {
                "query": query,
                "workflow_id": workflow_id
            })

            # Step 1: Retrieval
            await self._emit_event(run_id, EventType.RETRIEVAL_STARTED, "retrieval", {})
            retrieval_bundle = await self._execute_retrieval(
                run_id, query, retrieval_profile, workflow, doc_filter
            )
            await self._save_artifact(artifacts_dir, "retrieval_bundle.json",
                                     retrieval_bundle.model_dump())

            # Step 2: Fusion
            fused_results = await self._execute_fusion(
                run_id, retrieval_bundle, fusion_profile
            )
            await self._save_artifact(artifacts_dir, "fused_results.json", fused_results)
            await self._emit_event(run_id, EventType.FUSION_COMPLETED, "fusion", {
                "fused_chunks": len(fused_results)
            })

            # Step 3: Context Compilation
            context_pack = await self.context_compiler.compile_context(
                fused_results, query, context_profile
            )
            await self._save_artifact(artifacts_dir, "context_pack.json",
                                     context_pack.model_dump())
            await self._emit_event(run_id, EventType.CONTEXT_COMPILED, "context", {
                "chunks": len(context_pack.chunks),
                "tokens": context_pack.tokens_used
            })

            # Step 4: Generation
            answer = await self.generation.generate_answer(query, context_pack)
            await self._save_artifact(artifacts_dir, "answer.json", answer.model_dump())
            await self._emit_event(run_id, EventType.GENERATION_COMPLETED, "generation", {
                "citations": len(answer.citations),
                "tokens": answer.tokens_used,
                "cost": answer.cost
            })

            # Step 5: Judge Validation (optional)
            judge_report = None
            decision = "SKIPPED"
            blocked_by_judge = False

            if "judge_validation" in workflow.steps:
                await self._emit_event(run_id, EventType.JUDGE_STARTED, "judge", {})
                judge_report = await self.judge.evaluate(
                    query, context_pack, answer, judge_profile
                )
                await self._save_artifact(artifacts_dir, "judge_report.json",
                                         judge_report.model_dump())
                await self._emit_event(run_id, EventType.JUDGE_COMPLETED, "judge", {
                    "decision": judge_report.decision,
                    "passed": judge_report.passed,
                    "violations": len(judge_report.violations)
                })
                decision = judge_report.decision
                blocked_by_judge = judge_report.decision == "FAIL_BLOCKED"
            if blocked_by_judge:
                await self._emit_event(run_id, EventType.RUN_BLOCKED, "run_blocked", {
                    "violations": [v.model_dump() for v in judge_report.violations]
                })
                status = "blocked"
            else:
                await self._emit_event(run_id, EventType.RUN_COMPLETED, "run_completed", {})
                status = "completed"

            # Save events
            await self._save_events(run_dir)

            logger.info(f"Run completed: {run_id}, status: {status}")

            allow_blocked_answer = not workflow.fail_on_judge_block
            should_return_answer = (not blocked_by_judge) or allow_blocked_answer
            return {
                "run_id": run_id,
                "status": status,
                "decision": decision,
                "answer": answer if should_return_answer else None,
                "judge_report": judge_report
            }

        except Exception as e:
            logger.error(f"Run failed: {run_id}, error: {e}")
            await self._emit_event(run_id, EventType.RUN_FAILED, "run_failed", {
                "error": str(e)
            })
            await self._save_events(run_dir)

            return {
                "run_id": run_id,
                "status": "failed",
                "error": str(e)
            }

    async def _execute_retrieval(
        self,
        run_id: str,
        query: str,
        profile: Any,
        workflow: Any,
        filters: Optional[Dict[str, Any]] = None
    ) -> RetrievalBundle:
        """Execute tri-modal retrieval"""

        # Vector retrieval
        vector_results = await self.vector_retrieval.retrieve(query, profile, filters)
        await self._emit_event(run_id, EventType.VECTOR_SEARCH_COMPLETED, "vector_search", {
            "results": len(vector_results)
        })

        # Document retrieval
        # Index chunks first if needed
        all_chunks = await self.doc_store.get_chunks(filters=filters)
        await self.doc_retrieval.index_chunks(all_chunks)
        doc_results = await self.doc_retrieval.retrieve(query, profile, filters)
        await self._emit_event(run_id, EventType.DOCUMENT_SEARCH_COMPLETED, "doc_search", {
            "results": len(doc_results)
        })

        # Graph retrieval (if enabled)
        graph_results = []
        subgraph = None
        if workflow.enable_graph_retrieval:
            try:
                await self.graph_store.load_graph(self.data_dir / "graph")
            except Exception as e:
                logger.warning(f"Failed to reload graph before retrieval: {e}")
            graph_results, subgraph = await self.graph_retrieval.retrieve(query, profile)
            await self._emit_event(run_id, EventType.GRAPH_SEARCH_COMPLETED, "graph_search", {
                "results": len(graph_results),
                "subgraph_nodes": len(subgraph.nodes) if subgraph else 0
            })

        # Create retrieval bundle
        bundle = RetrievalBundle(
            query=query,
            vector_results=vector_results,
            document_results=doc_results,
            graph_results=graph_results,
            subgraph=subgraph,
            fused_results=[],
            metadata={
                "total_results": len(vector_results) + len(doc_results) + len(graph_results)
            }
        )

        return bundle

    async def _execute_fusion(
        self,
        run_id: str,
        bundle: RetrievalBundle,
        profile: Any
    ) -> list[Dict[str, Any]]:
        """Execute result fusion"""

        fused_results = await self.fusion.fuse_results(
            vector_results=bundle.vector_results,
            document_results=bundle.document_results,
            graph_results=bundle.graph_results,
            profile=profile
        )

        return fused_results

    async def _emit_event(
        self,
        run_id: str,
        event_type: EventType,
        step: str,
        data: Dict[str, Any]
    ) -> None:
        """Emit pipeline event"""
        event = Event(
            run_id=run_id,
            event_type=event_type,
            step=step,
            timestamp=datetime.now(),
            data=data
        )
        self.events.append(event)
        logger.info(f"Event: {event_type} - {step}")

    async def _save_artifact(
        self,
        artifacts_dir: Path,
        filename: str,
        data: Dict[str, Any]
    ) -> None:
        """Save artifact to disk"""
        file_path = artifacts_dir / filename
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(json.dumps(data, indent=2, default=str))

    async def _save_events(self, run_dir: Path) -> None:
        """Save events to JSONL"""
        events_file = run_dir / "events.jsonl"
        async with aiofiles.open(events_file, 'w') as f:
            for event in self.events:
                await f.write(json.dumps(event.model_dump(), default=str) + '\n')

    async def get_run_events(self, run_id: str) -> list[Event]:
        """Get events for a run"""
        events_file = self.runs_dir / run_id / "events.jsonl"

        if not events_file.exists():
            return []

        events = []
        async with aiofiles.open(events_file, 'r') as f:
            async for line in f:
                if line.strip():
                    event_data = json.loads(line)
                    event = Event(**event_data)
                    events.append(event)

        return events

    async def get_artifact(self, run_id: str, artifact_name: str) -> Optional[Dict[str, Any]]:
        """Get artifact from run"""
        artifact_path = self.runs_dir / run_id / "artifacts" / artifact_name

        if not artifact_path.exists():
            return None

        async with aiofiles.open(artifact_path, 'r') as f:
            content = await f.read()
            return json.loads(content)
