"""
Citation Coverage Check
Deterministic check for citation density
"""

import re
from typing import Dict, Any, List


class CitationCoverageCheck:
    """Checks percentage of factual claims backed by citations"""

    async def evaluate(
        self,
        query: str,
        context: str,
        answer: str,
        citations: List[Any],
        threshold: float
    ) -> Dict[str, Any]:
        """
        Evaluate citation coverage

        Args:
            query: Original query
            context: Context text
            answer: Generated answer
            citations: List of citations
            threshold: Threshold for passing

        Returns:
            Evaluation result with score
        """
        # Extract sentences (factual claims)
        sentences = [s.strip() for s in re.split(r'[.!?]', answer) if s.strip()]

        # Count citations in answer
        citation_pattern = r'\[(\d+)\]'
        citations_in_answer = set(re.findall(citation_pattern, answer))

        # Count sentences with citations
        sentences_with_citations = 0
        for sentence in sentences:
            if re.search(citation_pattern, sentence):
                sentences_with_citations += 1

        # Calculate coverage
        total_sentences = len(sentences)
        coverage = sentences_with_citations / total_sentences if total_sentences > 0 else 0.0

        return {
            "score": coverage,
            "details": {
                "total_sentences": total_sentences,
                "cited_sentences": sentences_with_citations,
                "unique_citations": len(citations_in_answer)
            },
            "message": f"Citation coverage: {coverage:.1%} ({sentences_with_citations}/{total_sentences} sentences cited)"
        }
