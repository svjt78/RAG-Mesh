"""
Hallucination Detection Check
Detects fabricated information not present in context
"""

import json
from typing import Dict, Any, List


class HallucinationCheck:
    """Detects hallucinated content"""

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
        """Evaluate for hallucinations (lower score = more hallucinations)"""

        prompt = f"""Detect hallucinations in the answer - fabricated facts, entities, or numbers NOT present in the context.

Context:
{context[:3000]}

Answer:
{answer}

Identify any hallucinated content. Output JSON:
{{
  "hallucinations": ["hallucination 1", "hallucination 2"],
  "hallucination_score": 0.0-1.0
}}

Score 0.0 = severe hallucinations, 1.0 = no hallucinations"""

        try:
            response = await self.llm.generate(
                prompt=prompt,
                json_mode=True,
                temperature=0.0
            )

            result = json.loads(response["content"])
            # LLM returns score where 1.0 = no hallucinations, 0.0 = severe hallucinations
            score = result.get("hallucination_score", 0.5)

            return {
                "score": score,
                "details": {"hallucinations": result.get("hallucinations", [])},
                "message": f"Hallucination score: {score:.2f} (higher is better)"
            }

        except Exception as e:
            return {
                "score": 0.5,
                "details": {"error": str(e)},
                "message": f"Hallucination check error: {e}"
            }
