"""
Judge orchestrator
Coordinates all 9 validation checks and generates comprehensive report
"""

import logging
from typing import Dict, Any
import asyncio

from app.adapters.base import LLMAdapter
from app.core.models import (
    JudgeProfile, JudgeReport, CheckResult, Violation,
    JudgeDecision, CheckStatus, Answer, ContextPack
)

# Import individual check modules
from app.modules.judge.checks.citation_coverage import CitationCoverageCheck
from app.modules.judge.checks.groundedness import GroundednessCheck
from app.modules.judge.checks.hallucination import HallucinationCheck
from app.modules.judge.checks.relevance import RelevanceCheck
from app.modules.judge.checks.consistency import ConsistencyCheck
from app.modules.judge.checks.toxicity import ToxicityCheck
from app.modules.judge.checks.pii import PIILeakageCheck
from app.modules.judge.checks.bias import BiasCheck
from app.modules.judge.checks.contradiction import ContradictionCheck

logger = logging.getLogger(__name__)


class JudgeOrchestrator:
    """Orchestrates all judge validation checks"""

    def __init__(self, llm_adapter: LLMAdapter):
        """
        Initialize judge orchestrator

        Args:
            llm_adapter: LLM adapter for judge checks
        """
        self.llm = llm_adapter

        # Initialize all checks
        self.checks = {
            "citation_coverage": CitationCoverageCheck(),
            "groundedness": GroundednessCheck(llm_adapter),
            "hallucination": HallucinationCheck(llm_adapter),
            "relevance": RelevanceCheck(llm_adapter),
            "consistency": ConsistencyCheck(llm_adapter),
            "toxicity": ToxicityCheck(llm_adapter),
            "pii_leakage": PIILeakageCheck(),
            "bias": BiasCheck(llm_adapter),
            "contradiction": ContradictionCheck(llm_adapter)
        }

    async def evaluate(
        self,
        query: str,
        context_pack: ContextPack,
        answer: Answer,
        profile: JudgeProfile
    ) -> JudgeReport:
        """
        Run all enabled validation checks

        Args:
            query: Original query
            context_pack: Context used for generation
            answer: Generated answer
            profile: Judge profile with check configurations

        Returns:
            Complete JudgeReport
        """
        logger.info("Starting judge validation")

        # Run all checks in parallel where possible
        check_results = []

        # Group checks by dependency
        independent_checks = []
        dependent_checks = []

        # Independent checks (can run in parallel)
        if profile.citation_coverage.enabled:
            independent_checks.append(self._run_check(
                "citation_coverage", query, context_pack, answer, profile.citation_coverage
            ))

        if profile.relevance.enabled:
            independent_checks.append(self._run_check(
                "relevance", query, context_pack, answer, profile.relevance
            ))

        if profile.toxicity.enabled:
            independent_checks.append(self._run_check(
                "toxicity", query, context_pack, answer, profile.toxicity
            ))

        if profile.pii_leakage.enabled:
            independent_checks.append(self._run_check(
                "pii_leakage", query, context_pack, answer, profile.pii_leakage
            ))

        if profile.bias.enabled:
            independent_checks.append(self._run_check(
                "bias", query, context_pack, answer, profile.bias
            ))

        # Run independent checks in parallel
        if independent_checks:
            results = await asyncio.gather(*independent_checks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Check failed: {result}")
                else:
                    check_results.append(result)

        # Dependent checks (require independent checks to complete)
        if profile.groundedness.enabled:
            result = await self._run_check(
                "groundedness", query, context_pack, answer, profile.groundedness
            )
            check_results.append(result)

        if profile.hallucination.enabled:
            result = await self._run_check(
                "hallucination", query, context_pack, answer, profile.hallucination
            )
            check_results.append(result)

        if profile.consistency.enabled:
            result = await self._run_check(
                "consistency", query, context_pack, answer, profile.consistency
            )
            check_results.append(result)

        if profile.contradiction.enabled:
            result = await self._run_check(
                "contradiction", query, context_pack, answer, profile.contradiction
            )
            check_results.append(result)

        # Compile report
        report = self._compile_report(check_results, answer)

        logger.info(f"Judge validation complete: {report.decision}")
        return report

    async def _run_check(
        self,
        check_name: str,
        query: str,
        context_pack: ContextPack,
        answer: Answer,
        config: Any
    ) -> CheckResult:
        """Run a single validation check"""
        try:
            logger.info(f"Running check: {check_name}")
            check = self.checks[check_name]

            result = await check.evaluate(
                query=query,
                context=context_pack.context_text,
                answer=answer.answer,
                citations=answer.citations,
                threshold=config.threshold
            )

            # Determine status
            if result["score"] >= config.threshold:
                status = CheckStatus.PASS
            else:
                status = CheckStatus.FAIL

            check_result = CheckResult(
                check_name=check_name,
                status=status,
                score=result["score"],
                threshold=config.threshold,
                hard_fail=config.hard_fail,
                details=result.get("details", {}),
                message=result.get("message", "")
            )

            return check_result

        except Exception as e:
            logger.error(f"Error running check {check_name}: {e}")
            return CheckResult(
                check_name=check_name,
                status=CheckStatus.ERROR,
                score=0.0,
                threshold=config.threshold,
                hard_fail=config.hard_fail,
                details={"error": str(e)},
                message=f"Check failed with error: {e}"
            )

    def _compile_report(
        self,
        check_results: list[CheckResult],
        answer: Answer
    ) -> JudgeReport:
        """
        Compile final judge report

        Args:
            check_results: Results from all checks
            answer: Generated answer

        Returns:
            JudgeReport
        """
        violations = []
        passed = True
        blocked = False

        # Analyze check results
        for result in check_results:
            if result.status == CheckStatus.FAIL:
                passed = False

                # Determine severity
                if result.hard_fail:
                    severity = "high"
                    blocked = True
                elif result.score < result.threshold * 0.7:
                    severity = "medium"
                else:
                    severity = "low"

                # Create violation
                violation = Violation(
                    check_name=result.check_name,
                    severity=severity,
                    message=result.message or f"{result.check_name} failed (score: {result.score:.2f}, threshold: {result.threshold:.2f})",
                    remediation=self._get_remediation(result.check_name, result)
                )
                violations.append(violation)

        # Calculate overall score (average of all check scores)
        overall_score = sum(r.score for r in check_results) / len(check_results) if check_results else 0.0

        # Determine decision
        if blocked:
            decision = JudgeDecision.FAIL_BLOCKED
        elif not passed:
            decision = JudgeDecision.FAIL_RETRYABLE
        else:
            decision = JudgeDecision.PASS

        # Build claim-evidence mapping
        claim_evidence_mapping = self._build_claim_evidence_mapping(answer, check_results)

        report = JudgeReport(
            decision=decision,
            checks=check_results,
            violations=violations,
            overall_score=overall_score,
            passed=passed,
            claim_evidence_mapping=claim_evidence_mapping,
            metadata={
                "total_checks": len(check_results),
                "passed_checks": sum(1 for r in check_results if r.status == CheckStatus.PASS),
                "failed_checks": sum(1 for r in check_results if r.status == CheckStatus.FAIL),
                "blocked": blocked
            }
        )

        return report

    def _get_remediation(self, check_name: str, result: CheckResult) -> str:
        """Get remediation recommendation for failed check"""
        remediation_map = {
            "citation_coverage": "Add more citations to support factual claims. Ensure every claim has a corresponding citation.",
            "groundedness": "Ensure all claims are directly supported by the provided context. Remove or rephrase unsupported claims.",
            "hallucination": "Remove fabricated information. Only include facts present in the source documents.",
            "relevance": "Focus the answer more directly on addressing the specific query. Remove tangential information.",
            "consistency": "Review the answer for internal contradictions. Ensure all statements align with each other.",
            "toxicity": "Remove any toxic, offensive, or inappropriate language from the answer.",
            "pii_leakage": "Redact any personally identifiable information (SSN, email, phone, etc.) from the answer.",
            "bias": "Remove biased or discriminatory language. Ensure fair and neutral treatment of all groups.",
            "contradiction": "Ensure the answer does not contradict the source context. Align claims with evidence."
        }

        return remediation_map.get(check_name, "Review and improve this aspect of the answer.")

    def _build_claim_evidence_mapping(
        self,
        answer: Answer,
        check_results: list[CheckResult]
    ) -> Dict[str, list[str]]:
        """Build mapping of claims to supporting evidence"""
        mapping = {}

        # Extract claims from answer (simple sentence splitting)
        claims = [s.strip() for s in answer.answer.split('.') if s.strip()]

        # Map claims to citations
        for i, claim in enumerate(claims[:10]):  # Limit to 10 claims
            claim_key = f"claim_{i+1}"
            supporting_citations = []

            # Find citations in claim
            import re
            citation_refs = re.findall(r'\[(\d+)\]', claim)
            for ref in citation_refs:
                try:
                    citation_idx = int(ref) - 1
                    if 0 <= citation_idx < len(answer.citations):
                        citation = answer.citations[citation_idx]
                        supporting_citations.append(citation.chunk_id)
                except ValueError:
                    continue

            if supporting_citations:
                mapping[claim] = supporting_citations

        return mapping
