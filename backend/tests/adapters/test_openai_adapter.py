"""
Unit tests for OpenAIAdapter
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.adapters.openai_adapter import OpenAIAdapter
from app.core.models import EntityType, RelationType


@pytest.mark.unit
class TestOpenAIAdapter:
    """Test cases for OpenAIAdapter."""

    @pytest.fixture
    def openai_adapter(self, openai_api_key: str) -> OpenAIAdapter:
        """Create an OpenAIAdapter instance for testing."""
        config = {
            "api_key": openai_api_key,
            "model": "gpt-3.5-turbo",
            "embedding_model": "text-embedding-3-small",
            "temperature": 0.0,
            "max_tokens": 1000,
            "timeout": 30,
        }
        return OpenAIAdapter(config)

    @pytest.mark.asyncio
    @patch("app.adapters.openai_adapter.AsyncOpenAI")
    async def test_generate(
        self, mock_openai_class: MagicMock, openai_adapter: OpenAIAdapter
    ):
        """Test text generation."""
        # Mock the OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Generated answer text"))
        ]
        mock_response.usage = MagicMock(
            prompt_tokens=50, completion_tokens=20, total_tokens=70
        )

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        mock_openai_class.return_value = mock_client

        # Create new adapter to use mocked client
        adapter = OpenAIAdapter(
            {
                "api_key": "test-key",
                "model": "gpt-3.5-turbo",
                "embedding_model": "text-embedding-3-small",
            }
        )

        # Test generation
        prompt = "What is covered under the policy?"
        result = await adapter.generate(prompt)

        assert result == "Generated answer text"
        mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.adapters.openai_adapter.AsyncOpenAI")
    async def test_generate_with_system_prompt(
        self, mock_openai_class: MagicMock, openai_adapter: OpenAIAdapter
    ):
        """Test generation with system prompt."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Answer"))
        ]
        mock_response.usage = MagicMock(
            prompt_tokens=50, completion_tokens=20, total_tokens=70
        )

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        mock_openai_class.return_value = mock_client

        adapter = OpenAIAdapter(
            {
                "api_key": "test-key",
                "model": "gpt-3.5-turbo",
                "embedding_model": "text-embedding-3-small",
            }
        )

        result = await adapter.generate(
            prompt="Question?", system_prompt="You are an insurance expert."
        )

        assert result == "Answer"
        # Verify system message was included
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are an insurance expert."

    @pytest.mark.asyncio
    @patch("app.adapters.openai_adapter.AsyncOpenAI")
    async def test_embed(
        self, mock_openai_class: MagicMock, openai_adapter: OpenAIAdapter
    ):
        """Test text embedding."""
        # Mock embedding response
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_response.usage = MagicMock(prompt_tokens=10, total_tokens=10)

        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client

        adapter = OpenAIAdapter(
            {
                "api_key": "test-key",
                "model": "gpt-3.5-turbo",
                "embedding_model": "text-embedding-3-small",
            }
        )

        # Test embedding
        text = "Sample text for embedding"
        embedding = await adapter.embed(text)

        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
        mock_client.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.adapters.openai_adapter.AsyncOpenAI")
    async def test_extract_entities(
        self, mock_openai_class: MagicMock, openai_adapter: OpenAIAdapter
    ):
        """Test entity extraction."""
        # Mock LLM response with entities
        entity_json = """{
            "nodes": [
                {
                    "entity_name": "Coverage A: Dwelling",
                    "entity_type": "COVERAGE",
                    "metadata": {"limit": "$500,000"}
                },
                {
                    "entity_name": "Water Damage",
                    "entity_type": "EXCLUSION",
                    "metadata": {}
                }
            ],
            "edges": [
                {
                    "source_name": "Coverage A: Dwelling",
                    "target_name": "California",
                    "relation_type": "APPLIES_TO",
                    "metadata": {}
                }
            ]
        }"""

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=entity_json))]
        mock_response.usage = MagicMock(
            prompt_tokens=100, completion_tokens=50, total_tokens=150
        )

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        mock_openai_class.return_value = mock_client

        adapter = OpenAIAdapter(
            {
                "api_key": "test-key",
                "model": "gpt-3.5-turbo",
                "embedding_model": "text-embedding-3-small",
            }
        )

        # Test entity extraction
        text = "Policy text with entities"
        result = await adapter.extract_entities(text)

        assert "nodes" in result
        assert "edges" in result
        assert len(result["nodes"]) == 2
        assert len(result["edges"]) == 1
        assert result["nodes"][0]["entity_type"] == "COVERAGE"

    @pytest.mark.asyncio
    @patch("app.adapters.openai_adapter.AsyncOpenAI")
    async def test_extract_entities_invalid_json(
        self, mock_openai_class: MagicMock, openai_adapter: OpenAIAdapter
    ):
        """Test handling of invalid JSON in entity extraction."""
        # Mock response with invalid JSON
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Invalid JSON response"))
        ]
        mock_response.usage = MagicMock(
            prompt_tokens=100, completion_tokens=50, total_tokens=150
        )

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        mock_openai_class.return_value = mock_client

        adapter = OpenAIAdapter(
            {
                "api_key": "test-key",
                "model": "gpt-3.5-turbo",
                "embedding_model": "text-embedding-3-small",
            }
        )

        # Should return empty structure on invalid JSON
        result = await adapter.extract_entities("text")
        assert result["nodes"] == []
        assert result["edges"] == []

    @pytest.mark.asyncio
    def test_count_tokens(self, openai_adapter: OpenAIAdapter):
        """Test token counting."""
        text = "This is a sample text for token counting."
        count = openai_adapter.count_tokens(text)

        assert isinstance(count, int)
        assert count > 0
        # Should be roughly 8-10 tokens for this text
        assert 5 <= count <= 15

    @pytest.mark.asyncio
    def test_count_tokens_empty(self, openai_adapter: OpenAIAdapter):
        """Test token counting with empty text."""
        count = openai_adapter.count_tokens("")
        assert count == 0

    @pytest.mark.asyncio
    def test_count_tokens_long_text(self, openai_adapter: OpenAIAdapter):
        """Test token counting with long text."""
        # Create a long text (~1000 words)
        text = " ".join(["word"] * 1000)
        count = openai_adapter.count_tokens(text)

        assert count > 900  # Should be around 1000 tokens

    @pytest.mark.asyncio
    @patch("app.adapters.openai_adapter.AsyncOpenAI")
    async def test_generate_with_max_tokens(
        self, mock_openai_class: MagicMock
    ):
        """Test that max_tokens is respected in generation."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="Short answer"))
        ]
        mock_response.usage = MagicMock(
            prompt_tokens=50, completion_tokens=5, total_tokens=55
        )

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        mock_openai_class.return_value = mock_client

        adapter = OpenAIAdapter(
            {
                "api_key": "test-key",
                "model": "gpt-3.5-turbo",
                "embedding_model": "text-embedding-3-small",
                "max_tokens": 100,
            }
        )

        await adapter.generate("Question?")

        # Verify max_tokens was passed
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["max_tokens"] == 100

    @pytest.mark.asyncio
    @patch("app.adapters.openai_adapter.AsyncOpenAI")
    async def test_generate_with_temperature(
        self, mock_openai_class: MagicMock
    ):
        """Test that temperature is configurable."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Answer"))]
        mock_response.usage = MagicMock(
            prompt_tokens=50, completion_tokens=10, total_tokens=60
        )

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        mock_openai_class.return_value = mock_client

        adapter = OpenAIAdapter(
            {
                "api_key": "test-key",
                "model": "gpt-3.5-turbo",
                "embedding_model": "text-embedding-3-small",
                "temperature": 0.7,
            }
        )

        await adapter.generate("Question?")

        # Verify temperature was passed
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["temperature"] == 0.7

    @pytest.mark.asyncio
    @patch("app.adapters.openai_adapter.AsyncOpenAI")
    async def test_retry_on_api_error(
        self, mock_openai_class: MagicMock
    ):
        """Test retry logic on API errors."""
        mock_client = AsyncMock()
        # First call fails, second succeeds
        mock_success_response = MagicMock()
        mock_success_response.choices = [
            MagicMock(message=MagicMock(content="Success"))
        ]
        mock_success_response.usage = MagicMock(
            prompt_tokens=50, completion_tokens=10, total_tokens=60
        )

        mock_client.chat.completions.create = AsyncMock(
            side_effect=[
                Exception("API Error"),
                mock_success_response,
            ]
        )
        mock_openai_class.return_value = mock_client

        adapter = OpenAIAdapter(
            {
                "api_key": "test-key",
                "model": "gpt-3.5-turbo",
                "embedding_model": "text-embedding-3-small",
                "max_retries": 3,
            }
        )

        # Should succeed on retry
        result = await adapter.generate("Question?")
        assert result == "Success"
        assert mock_client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    @patch("app.adapters.openai_adapter.AsyncOpenAI")
    async def test_embed_batch(
        self, mock_openai_class: MagicMock
    ):
        """Test batched embedding."""
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1] * 1536),
            MagicMock(embedding=[0.2] * 1536),
            MagicMock(embedding=[0.3] * 1536),
        ]
        mock_response.usage = MagicMock(prompt_tokens=30, total_tokens=30)

        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client

        adapter = OpenAIAdapter(
            {
                "api_key": "test-key",
                "model": "gpt-3.5-turbo",
                "embedding_model": "text-embedding-3-small",
            }
        )

        # Embed multiple texts (using single embed multiple times)
        texts = ["text1", "text2", "text3"]
        embeddings = []
        for text in texts:
            emb = await adapter.embed(text)
            embeddings.append(emb)

        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)
