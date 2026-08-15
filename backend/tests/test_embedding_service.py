"""Tests for app.services.embedding_service — Phase 12.

All tests use mocked embedding APIs; no real network calls are made.

Covers:
- Factory selects the correct provider based on EMBEDDING_PROVIDER alone
  (independent of LLM_PROVIDER).
- OpenAIEmbeddingProvider.embed() calls the API in batches of EMBED_BATCH_SIZE.
- Retry-on-429 (RateLimitError) with exponential backoff.
- Anthropic and Groq stubs raise NotImplementedError.
- Custom provider raises ValueError.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import EmbeddingProvider as EmbeddingProviderEnum
from app.config import LLMProvider, Settings
from app.services.embedding_service import (
    EMBED_BATCH_SIZE,
    MAX_RETRIES,
    AnthropicEmbeddingProvider,
    EmbeddingProvider,
    GroqEmbeddingProvider,
    OpenAIEmbeddingProvider,
    get_embedding_provider,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _settings(**kwargs: Any) -> Settings:
    """Build a Settings instance with sensible test defaults."""
    defaults = dict(
        DATABASE_URL="postgresql+asyncpg://localhost/test",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret",
        LLM_API_KEY="sk-test-key",
        LLM_PROVIDER=LLMProvider.OPENAI,
        EMBEDDING_PROVIDER=EmbeddingProviderEnum.OPENAI,
        EMBEDDING_MODEL="text-embedding-3-small",
        EMBEDDING_DIM=1536,
    )
    defaults.update(kwargs)
    return Settings(**defaults)  # type: ignore[arg-type]


def _fake_embedding(dim: int = 3) -> list[float]:
    return [0.1] * dim


def _make_openai_response(n: int, dim: int = 3) -> MagicMock:
    """Fake openai embeddings.create() response for n texts."""
    response = MagicMock()
    response.data = [MagicMock(embedding=_fake_embedding(dim)) for _ in range(n)]
    return response


# ---------------------------------------------------------------------------
# Factory tests
# ---------------------------------------------------------------------------


class TestGetEmbeddingProvider:
    def test_openai_provider_selected_when_embedding_provider_is_openai(self) -> None:
        settings = _settings(EMBEDDING_PROVIDER=EmbeddingProviderEnum.OPENAI)
        with patch("app.services.embedding_service.OpenAIEmbeddingProvider") as MockCls:
            MockCls.return_value = MagicMock(spec=EmbeddingProvider)
            provider = get_embedding_provider(settings)
        MockCls.assert_called_once()
        assert provider is MockCls.return_value

    def test_anthropic_provider_selected_independently_of_llm_provider(self) -> None:
        """EMBEDDING_PROVIDER=anthropic should select Anthropic regardless of LLM_PROVIDER."""
        settings = _settings(
            LLM_PROVIDER=LLMProvider.OPENAI,  # different from embedding
            EMBEDDING_PROVIDER=EmbeddingProviderEnum.ANTHROPIC,
        )
        provider = get_embedding_provider(settings)
        assert isinstance(provider, AnthropicEmbeddingProvider)

    def test_groq_provider_selected_independently_of_llm_provider(self) -> None:
        settings = _settings(
            LLM_PROVIDER=LLMProvider.ANTHROPIC,
            EMBEDDING_PROVIDER=EmbeddingProviderEnum.GROQ,
        )
        provider = get_embedding_provider(settings)
        assert isinstance(provider, GroqEmbeddingProvider)

    def test_openai_embedding_with_anthropic_llm_provider(self) -> None:
        """Classic case: LLM_PROVIDER=anthropic + EMBEDDING_PROVIDER=openai."""
        settings = _settings(
            LLM_PROVIDER=LLMProvider.ANTHROPIC,
            EMBEDDING_PROVIDER=EmbeddingProviderEnum.OPENAI,
        )
        with patch("app.services.embedding_service.OpenAIEmbeddingProvider") as MockCls:
            MockCls.return_value = MagicMock(spec=EmbeddingProvider)
            provider = get_embedding_provider(settings)
        MockCls.assert_called_once()

    def test_custom_provider_raises_value_error(self) -> None:
        settings = _settings(EMBEDDING_PROVIDER=EmbeddingProviderEnum.CUSTOM)
        with pytest.raises(ValueError, match="custom"):
            get_embedding_provider(settings)


# ---------------------------------------------------------------------------
# Stub tests
# ---------------------------------------------------------------------------


class TestStubs:
    @pytest.mark.asyncio
    async def test_anthropic_stub_raises_not_implemented(self) -> None:
        provider = AnthropicEmbeddingProvider()
        with pytest.raises(NotImplementedError, match="Anthropic"):
            await provider.embed(["hello"])

    @pytest.mark.asyncio
    async def test_groq_stub_raises_not_implemented(self) -> None:
        provider = GroqEmbeddingProvider()
        with pytest.raises(NotImplementedError, match="Groq"):
            await provider.embed(["hello"])


# ---------------------------------------------------------------------------
# OpenAI provider — basic functionality
# ---------------------------------------------------------------------------


class TestOpenAIEmbeddingProvider:
    def _make_provider(self) -> tuple[OpenAIEmbeddingProvider, MagicMock]:
        """Return (provider, mock_create_fn)."""
        mock_create = AsyncMock()
        with patch("openai.AsyncOpenAI") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.embeddings.create = mock_create
            mock_client_cls.return_value = mock_client
            provider = OpenAIEmbeddingProvider(api_key="sk-test", model="text-embedding-3-small")
        return provider, mock_create

    @pytest.mark.asyncio
    async def test_embed_empty_list_returns_empty(self) -> None:
        provider, mock_create = self._make_provider()
        result = await provider.embed([])
        assert result == []
        mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_embed_single_batch(self) -> None:
        provider, mock_create = self._make_provider()
        n = 5
        mock_create.return_value = _make_openai_response(n)

        texts = [f"text {i}" for i in range(n)]
        result = await provider.embed(texts)

        assert len(result) == n
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        assert len(call_args.kwargs["input"]) == n

    @pytest.mark.asyncio
    async def test_embed_multiple_batches(self) -> None:
        provider, mock_create = self._make_provider()
        n = EMBED_BATCH_SIZE + 10  # force 2 batches

        def side_effect(**kwargs: Any) -> MagicMock:
            batch_size = len(kwargs["input"])
            return _make_openai_response(batch_size)

        mock_create.side_effect = side_effect

        texts = [f"text {i}" for i in range(n)]
        result = await provider.embed(texts)

        assert len(result) == n
        assert mock_create.call_count == 2
        # First call has EMBED_BATCH_SIZE texts, second has remainder
        first_batch_size = len(mock_create.call_args_list[0].kwargs["input"])
        second_batch_size = len(mock_create.call_args_list[1].kwargs["input"])
        assert first_batch_size == EMBED_BATCH_SIZE
        assert second_batch_size == 10

    @pytest.mark.asyncio
    async def test_embed_returns_vectors_in_order(self) -> None:
        provider, mock_create = self._make_provider()
        # Return distinct embeddings per call to verify ordering
        n = EMBED_BATCH_SIZE + 5
        call_count = [0]

        def side_effect(**kwargs: Any) -> MagicMock:
            batch = kwargs["input"]
            resp = MagicMock()
            resp.data = [MagicMock(embedding=[float(call_count[0]) + float(j) / 100]) for j in range(len(batch))]
            call_count[0] += 1
            return resp

        mock_create.side_effect = side_effect

        texts = [str(i) for i in range(n)]
        result = await provider.embed(texts)

        assert len(result) == n


# ---------------------------------------------------------------------------
# Retry on rate-limit
# ---------------------------------------------------------------------------


class TestRetryOnRateLimit:
    @pytest.mark.asyncio
    async def test_retries_on_rate_limit_error(self) -> None:
        """embed() should retry after a 429 and eventually succeed."""
        import openai

        provider, mock_create = TestOpenAIEmbeddingProvider()._make_provider()

        n_texts = 3
        attempts = [0]

        async def flaky(**kwargs: Any) -> MagicMock:
            attempts[0] += 1
            if attempts[0] < 3:
                raise openai.RateLimitError(
                    message="rate limit", response=MagicMock(), body={}
                )
            return _make_openai_response(n_texts)

        mock_create.side_effect = flaky

        with patch("asyncio.sleep", new=AsyncMock()):
            result = await provider.embed(["a", "b", "c"])

        assert len(result) == n_texts
        assert attempts[0] == 3  # 2 failures + 1 success

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self) -> None:
        """embed() should re-raise RateLimitError after MAX_RETRIES attempts."""
        import openai

        provider, mock_create = TestOpenAIEmbeddingProvider()._make_provider()

        async def always_limit(**kwargs: Any) -> None:
            raise openai.RateLimitError(
                message="rate limit", response=MagicMock(), body={}
            )

        mock_create.side_effect = always_limit

        with patch("asyncio.sleep", new=AsyncMock()):
            with pytest.raises(openai.RateLimitError):
                await provider.embed(["text"])

        assert mock_create.call_count == MAX_RETRIES

    @pytest.mark.asyncio
    async def test_backoff_doubles_on_each_retry(self) -> None:
        """asyncio.sleep() should be called with doubling delays."""
        import openai

        provider, mock_create = TestOpenAIEmbeddingProvider()._make_provider()
        sleep_calls: list[float] = []

        async def mock_sleep(seconds: float) -> None:
            sleep_calls.append(seconds)

        fail_count = [0]

        async def flaky(**kwargs: Any) -> MagicMock:
            fail_count[0] += 1
            if fail_count[0] < 3:
                raise openai.RateLimitError(
                    message="rl", response=MagicMock(), body={}
                )
            return _make_openai_response(1)

        mock_create.side_effect = flaky

        with patch("asyncio.sleep", side_effect=mock_sleep):
            await provider.embed(["x"])

        assert len(sleep_calls) == 2
        assert sleep_calls[1] == sleep_calls[0] * 2  # exponential doubling
