"""
OpenAI adapter with retry logic and cost tracking
Implements LLM operations using OpenAI API
"""

import os
import json
import logging
from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
import tiktoken
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.adapters.base import LLMAdapter

logger = logging.getLogger(__name__)


class OpenAIAdapter(LLMAdapter):
    """OpenAI-based implementation of LLM operations"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        Initialize OpenAI adapter

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name for generation
            embedding_model: Model name for embeddings
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        self.model = model
        self.embedding_model = embedding_model
        self.client = AsyncOpenAI(api_key=self.api_key)

        # Initialize tokenizer
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            logger.warning(f"Model {model} not found, using cl100k_base encoding")
            self.encoding = tiktoken.get_encoding("cl100k_base")

        # Cost tracking (in USD per 1K tokens)
        self.cost_per_1k_input = 0.0005  # GPT-3.5-turbo input
        self.cost_per_1k_output = 0.0015  # GPT-3.5-turbo output
        self.embedding_cost_per_1k = 0.00002  # text-embedding-3-small

        logger.info(f"Initialized OpenAI adapter with model: {model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate text completion with retry logic

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            json_mode: Whether to enforce JSON output
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Dict with 'content', 'tokens_used', 'cost'
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            # Prepare request parameters
            request_params: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                request_params["max_tokens"] = max_tokens

            if json_mode:
                request_params["response_format"] = {"type": "json_object"}

            # Make API call
            response = await self.client.chat.completions.create(**request_params)

            # Extract response
            content = response.choices[0].message.content or ""
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            total_tokens = response.usage.total_tokens if response.usage else 0

            # Calculate cost
            input_cost = (input_tokens / 1000) * self.cost_per_1k_input
            output_cost = (output_tokens / 1000) * self.cost_per_1k_output
            total_cost = input_cost + output_cost

            logger.info(f"Generated completion: {total_tokens} tokens, ${total_cost:.6f}")

            return {
                "content": content,
                "tokens_used": total_tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": total_cost,
                "model": self.model,
            }

        except Exception as e:
            logger.error(f"Error in generation: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts with retry logic

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        try:
            # OpenAI API has a limit on batch size, chunk if necessary
            batch_size = 100
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]

                response = await self.client.embeddings.create(
                    model=self.embedding_model,
                    input=batch
                )

                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                # Calculate cost
                total_tokens = response.usage.total_tokens if response.usage else 0
                cost = (total_tokens / 1000) * self.embedding_cost_per_1k

                logger.info(f"Generated {len(batch)} embeddings: {total_tokens} tokens, ${cost:.6f}")

            return all_embeddings

        except Exception as e:
            logger.error(f"Error in embedding: {e}")
            raise

    async def extract_entities(
        self,
        text: str,
        entity_types: List[str]
    ) -> Dict[str, Any]:
        """
        Extract structured entities from text

        Args:
            text: Input text
            entity_types: Expected entity types

        Returns:
            Extracted entities and relationships
        """
        system_prompt = """You are an expert at extracting structured information from insurance documents.
Extract entities and relationships from the provided text according to the specified entity types.

Return your response as a JSON object with this structure:
{
  "entities": [
    {
      "id": "unique_id",
      "label": "entity_label",
      "type": "entity_type",
      "properties": {}
    }
  ],
  "relationships": [
    {
      "source": "source_entity_id",
      "target": "target_entity_id",
      "type": "relationship_type",
      "properties": {}
    }
  ]
}
"""

        user_prompt = f"""Entity types to extract: {', '.join(entity_types)}

Text to analyze:
{text}

Extract all relevant entities and their relationships."""

        response = await self.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            json_mode=True,
            temperature=0.0
        )

        try:
            # Parse JSON response
            extracted_data = json.loads(response["content"])
            return {
                "entities": extracted_data.get("entities", []),
                "relationships": extracted_data.get("relationships", []),
                "tokens_used": response["tokens_used"],
                "cost": response["cost"]
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse entity extraction response: {e}")
            return {
                "entities": [],
                "relationships": [],
                "tokens_used": response["tokens_used"],
                "cost": response["cost"],
                "error": str(e)
            }

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text

        Args:
            text: Input text

        Returns:
            Number of tokens
        """
        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int = 0,
        is_embedding: bool = False
    ) -> float:
        """
        Estimate cost for token usage

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            is_embedding: Whether this is for embeddings

        Returns:
            Estimated cost in USD
        """
        if is_embedding:
            return (input_tokens / 1000) * self.embedding_cost_per_1k
        else:
            input_cost = (input_tokens / 1000) * self.cost_per_1k_input
            output_cost = (output_tokens / 1000) * self.cost_per_1k_output
            return input_cost + output_cost
