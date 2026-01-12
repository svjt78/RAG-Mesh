"""
Answer generation module
Generates structured answers with citations using LLM
"""

import logging
import json
from typing import Dict, Any, List

from app.adapters.base import LLMAdapter
from app.core.models import Answer, Citation, ContextPack, ConfidenceLevel
from app.core.config_loader import get_config_loader

logger = logging.getLogger(__name__)


class GenerationModule:
    """Handles answer generation with structured output"""

    def __init__(self, llm_adapter: LLMAdapter):
        """
        Initialize generation module

        Args:
            llm_adapter: LLM adapter for generation
        """
        self.llm = llm_adapter
        self.config_loader = get_config_loader()

    async def generate_answer(
        self,
        query: str,
        context_pack: ContextPack
    ) -> Answer:
        """
        Generate answer from query and context

        Args:
            query: User query
            context_pack: Compiled context pack

        Returns:
            Answer object with citations
        """
        logger.info(f"Generating answer for query: '{query[:50]}...'")

        try:
            # Build generation prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(query, context_pack)

            # Generate with structured output
            response = await self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                json_mode=True,
                temperature=0.0,
                max_tokens=2000
            )

            # Parse JSON response
            answer_data = json.loads(response["content"])

            # Validate and create Answer object
            answer = self._create_answer(
                answer_data=answer_data,
                context_pack=context_pack,
                tokens_used=response["tokens_used"],
                cost=response["cost"]
            )

            logger.info(f"Answer generated with {len(answer.citations)} citations")
            return answer

        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            # Return fallback answer
            return self._create_fallback_answer(str(e))

    def _build_system_prompt(self) -> str:
        """Build system prompt for generation"""
        default_prompt = """You are an expert insurance analyst. Your task is to answer questions about insurance policies based strictly on the provided context.

CRITICAL RULES:
1. Answer ONLY based on the provided context
2. Include citations for ALL factual claims using [N] format where N is the citation number
3. If information is not in the context, explicitly state "This information is not available in the provided documents"
4. Clearly state any assumptions you make
5. Note any limitations or uncertainties in your answer
6. Be precise and concise
7. Use professional insurance terminology

OUTPUT FORMAT (JSON):
{
  "answer": "Your detailed answer with inline citations [1], [2], etc.",
  "citations": [
    {
      "chunk_id": "chunk_id_from_context",
      "doc_id": "document_id",
      "page_no": page_number,
      "quote": "Exact quote from context that supports the claim",
      "reason": "Why this citation supports the claim"
    }
  ],
  "assumptions": ["Any assumptions made in the answer"],
  "limitations": ["Any limitations or uncertainties"],
  "confidence": "low|medium|high"
}"""
        configured_prompt = self.config_loader.get_generation_system_prompt()
        return configured_prompt or default_prompt

    def _build_user_prompt(self, query: str, context_pack: ContextPack) -> str:
        """Build user prompt with query and context"""
        # Build citation reference guide
        citation_guide = "AVAILABLE CONTEXT:\n\n"
        for chunk in context_pack.chunks:
            citation_guide += f"[{chunk['rank']}] (Page {chunk['page_no']}, Doc: {chunk['doc_id'][:12]})\n"
            citation_guide += f"{chunk['text']}\n\n"

        prompt = f"""{citation_guide}

QUERY: {query}

Please provide a comprehensive answer using the context above. Remember to cite every factual claim using [N] format."""

        return prompt

    def _create_answer(
        self,
        answer_data: Dict[str, Any],
        context_pack: ContextPack,
        tokens_used: int,
        cost: float
    ) -> Answer:
        """
        Create Answer object from generated data

        Args:
            answer_data: Parsed JSON answer
            context_pack: Context pack for validation
            tokens_used: Tokens used
            cost: Generation cost

        Returns:
            Answer object
        """
        # Parse citations
        citations = []
        for cit_data in answer_data.get("citations", []):
            # Validate citation exists in context
            chunk_id = cit_data.get("chunk_id", "")
            if self._validate_citation(chunk_id, context_pack):
                citation = Citation(
                    chunk_id=chunk_id,
                    doc_id=cit_data.get("doc_id", ""),
                    page_no=cit_data.get("page_no", 1),
                    quote=cit_data.get("quote", ""),
                    reason=cit_data.get("reason", "")
                )
                citations.append(citation)
            else:
                logger.warning(f"Invalid citation: {chunk_id} not in context")

        # Parse confidence
        confidence_str = answer_data.get("confidence", "medium").lower()
        try:
            confidence = ConfidenceLevel(confidence_str)
        except ValueError:
            logger.warning(f"Invalid confidence: {confidence_str}, using medium")
            confidence = ConfidenceLevel.MEDIUM

        # Create Answer
        answer = Answer(
            answer=answer_data.get("answer", ""),
            citations=citations,
            assumptions=answer_data.get("assumptions", []),
            limitations=answer_data.get("limitations", []),
            confidence=confidence,
            tokens_used=tokens_used,
            cost=cost,
            metadata={
                "context_chunks": len(context_pack.chunks),
                "context_tokens": context_pack.tokens_used
            }
        )

        return answer

    def _validate_citation(self, chunk_id: str, context_pack: ContextPack) -> bool:
        """
        Validate that citation exists in context

        Args:
            chunk_id: Chunk ID to validate
            context_pack: Context pack

        Returns:
            True if valid
        """
        chunk_ids = [chunk["chunk_id"] for chunk in context_pack.chunks]
        return chunk_id in chunk_ids

    def _create_fallback_answer(self, error_msg: str) -> Answer:
        """Create fallback answer on error"""
        return Answer(
            answer="I apologize, but I encountered an error generating the answer. Please try again.",
            citations=[],
            assumptions=[],
            limitations=[f"Error occurred: {error_msg}"],
            confidence=ConfidenceLevel.LOW,
            tokens_used=0,
            cost=0.0,
            metadata={"error": error_msg}
        )

    async def retry_with_feedback(
        self,
        query: str,
        context_pack: ContextPack,
        feedback: str,
        previous_answer: Answer
    ) -> Answer:
        """
        Retry generation with feedback from judge

        Args:
            query: Original query
            context_pack: Context pack
            feedback: Feedback from judge
            previous_answer: Previous answer that failed

        Returns:
            New Answer
        """
        logger.info("Retrying answer generation with feedback")

        system_prompt = self._build_system_prompt()
        system_prompt += f"\n\nFEEDBACK ON PREVIOUS ATTEMPT:\n{feedback}\n\nPlease address this feedback in your new answer."

        user_prompt = self._build_user_prompt(query, context_pack)

        try:
            response = await self.llm.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                json_mode=True,
                temperature=0.1,  # Slightly higher for variation
                max_tokens=2000
            )

            answer_data = json.loads(response["content"])
            answer = self._create_answer(
                answer_data=answer_data,
                context_pack=context_pack,
                tokens_used=response["tokens_used"],
                cost=response["cost"]
            )

            return answer

        except Exception as e:
            logger.error(f"Retry generation failed: {e}")
            return previous_answer  # Return previous attempt if retry fails
