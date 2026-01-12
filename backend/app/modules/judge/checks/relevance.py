"""
Context Relevance Check
Checks if answer addresses the query
"""

import json
from typing import Dict, Any, List


class RelevanceCheck:
    """Checks query-answer relevance"""

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
        """Evaluate answer relevance to query"""

        prompt = f"""Evaluate if the answer directly addresses the query.

Query: {query}

Answer: {answer}

Rate relevance 0.0-1.0 where:
- 1.0 = Directly and completely addresses query
- 0.5 = Partially addresses query
- 0.0 = Does not address query

Output JSON:
{{
  "relevance_score": 0.0-1.0,
  "explanation": "brief explanation"
}}"""

        try:
            response = await self.llm.generate(
                prompt=prompt,
                json_mode=True,
                temperature=0.0
            )

            result = json.loads(response["content"])
            score = result.get("relevance_score", 0.5)

            return {
                "score": score,
                "details": {"explanation": result.get("explanation", "")},
                "message": f"Relevance score: {score:.2f}"
            }

        except Exception as e:
            return {
                "score": 0.5,
                "details": {"error": str(e)},
                "message": f"Relevance check error: {e}"
            }
