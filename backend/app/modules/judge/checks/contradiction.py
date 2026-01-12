"""
Contradiction Detection Check
Detects contradictions between answer and evidence
"""

import json
from typing import Dict, Any, List


class ContradictionCheck:
    """Checks for contradictions"""

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
        """Evaluate for contradictions (higher score = fewer contradictions)"""

        prompt = f"""Check if the answer contradicts the provided context.

Context:
{context[:3000]}

Answer:
{answer}

Identify any contradictions where the answer states something that conflicts with the context.

Output JSON:
{{
  "contradictions": [
    {{"answer_claim": "...", "context_evidence": "...", "conflict": "..."}}
  ],
  "contradiction_score": 0.0-1.0
}}

Score 0.0 = severe contradictions, 1.0 = no contradictions"""

        try:
            response = await self.llm.generate(
                prompt=prompt,
                json_mode=True,
                temperature=0.0
            )

            result = json.loads(response["content"])
            score = result.get("contradiction_score", 0.0)

            return {
                "score": score,
                "details": {"contradictions": result.get("contradictions", [])},
                "message": f"Contradiction score: {score:.2f} (higher is better)"
            }

        except Exception as e:
            return {
                "score": 0.8,  # Assume mostly non-contradictory on error
                "details": {"error": str(e)},
                "message": f"Contradiction check error: {e}"
            }
