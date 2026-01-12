"""
Groundedness Check
LLM-based verification that claims are entailed by evidence
"""

import json
from typing import Dict, Any, List


class GroundednessCheck:
    """Checks if answer claims are grounded in context"""

    def __init__(self, llm_adapter):
        self.llm = llm_adapter

    async def evaluate(
        self,
        query: str,
        context: str,
        answer: str,
        citations: List[Any],
        threshold: float
    ) -> Dict[str, Any]:
        """Evaluate groundedness of answer"""

        prompt = f"""Analyze if the answer's claims are grounded in (entailed by) the provided context.

Context:
{context[:3000]}

Answer:
{answer}

For each major claim in the answer, determine if it is:
1. Directly supported by the context (grounded)
2. Not supported by the context (ungrounded)

Output JSON:
{{
  "grounded_claims": ["claim 1", "claim 2"],
  "ungrounded_claims": ["claim 3"],
  "overall_score": 0.0-1.0
}}"""

        try:
            response = await self.llm.generate(
                prompt=prompt,
                json_mode=True,
                temperature=0.0
            )

            result = json.loads(response["content"])
            score = result.get("overall_score", 0.5)

            return {
                "score": score,
                "details": {
                    "grounded_claims": result.get("grounded_claims", []),
                    "ungrounded_claims": result.get("ungrounded_claims", [])
                },
                "message": f"Groundedness score: {score:.2f}"
            }

        except Exception as e:
            return {
                "score": 0.5,
                "details": {"error": str(e)},
                "message": f"Groundedness check error: {e}"
            }
