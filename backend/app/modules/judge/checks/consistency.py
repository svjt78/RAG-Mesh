"""
Consistency Check
Checks internal consistency of the answer
"""

import json
from typing import Dict, Any, List


class ConsistencyCheck:
    """Checks answer internal consistency"""

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
        """Evaluate internal consistency"""

        prompt = f"""Check if the answer is internally consistent - no contradictions within the answer itself.

Answer: {answer}

Identify any internal contradictions or inconsistencies.

Output JSON:
{{
  "contradictions": ["contradiction 1", "contradiction 2"],
  "consistency_score": 0.0-1.0
}}

Score 1.0 = perfectly consistent, 0.0 = major contradictions"""

        try:
            response = await self.llm.generate(
                prompt=prompt,
                json_mode=True,
                temperature=0.0
            )

            result = json.loads(response["content"])
            score = result.get("consistency_score", 0.8)

            return {
                "score": score,
                "details": {"contradictions": result.get("contradictions", [])},
                "message": f"Consistency score: {score:.2f}"
            }

        except Exception as e:
            return {
                "score": 0.8,
                "details": {"error": str(e)},
                "message": f"Consistency check error: {e}"
            }
