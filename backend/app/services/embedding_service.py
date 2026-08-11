"""Embedding provider abstraction for CodeGraph v2.

Architecture
------------
``EmbeddingProvider`` is an abstract base class with a single async method
``embed(texts)``.  Three concrete implementations are provided:

* ``OpenAIEmbeddingProvider``  — production-ready; uses ``text-embedding-3-small``
  (1 536 dimensions) via the official ``openai`` Python SDK.
* ``AnthropicEmbeddingProvider`` — *stub*: Anthropic has no first-party
  standalone embeddings API.  This class raises ``NotImplementedError`` with a
  descriptive message.  The expected common deployment is
  ``LLM_PROVIDER=anthropic`` + ``EMBEDDING_PROVIDER=openai``.
* ``GroqEmbeddingProvider`` — *stub*: Groq uses third-party embedding models
  and requires a custom ``EMBEDDING_BASE_URL``.  Raises ``NotImplementedError``
  until a concrete model is configured by the operator.

Provider selection
------------------
``get_embedding_provider(settings)`` inspects **only** ``settings.EMBEDDING_PROVIDER``
— it deliberately ignores ``settings.LLM_PROVIDER`` so the two can be
configured independently.

Batching & retry
----------------
``embed()`` calls are processed in batches of ``EMBED_BATCH_SIZE`` (100).
HTTP 429 / ``RateLimitError`` responses are retried with exponential backoff
(up to ``MAX_RETRIES`` attempts, starting at ``INITIAL_BACKOFF_SECONDS``).
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod

from app.config import EmbeddingProvider as EmbeddingProviderEnum
from app.config import Settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EMBED_BATCH_SIZE: int = 100
MAX_RETRIES: int = 5
INITIAL_BACKOFF_SECONDS: float = 1.0


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class EmbeddingProvider(ABC):
    """Abstract embedding provider interface."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts and return their vector representations.

        Args:
            texts: Non-empty list of strings to embed.

        Returns:
            A list of float vectors, one per input text, in the same order.
        """
        ...  # pragma: no cover


# ---------------------------------------------------------------------------
# OpenAI implementation
# ---------------------------------------------------------------------------


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Production embedding provider backed by the OpenAI Embeddings API.

    Uses ``text-embedding-3-small`` (1 536 dimensions) by default.  Processes
    texts in batches of ``EMBED_BATCH_SIZE`` and retries on rate-limit errors
    with exponential backoff.
    """

    def __init__(self, api_key: str, model: str = "text-embedding-3-small") -> None:
        """Initialise the provider.

        Args:
            api_key: OpenAI API key (``OPENAI_API_KEY``).
            model: Embedding model name.  Defaults to ``text-embedding-3-small``.
        """
        import openai  # lazy import so the package is optional at import time

        self._client = openai.AsyncOpenAI(api_key=api_key)
        self._model = model

    async def _embed_batch_with_retry(self, batch: list[str]) -> list[list[float]]:
        """Embed a single batch with exponential-backoff retry on 429s."""
        import openai

        backoff = INITIAL_BACKOFF_SECONDS
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await self._client.embeddings.create(
                    model=self._model,
                    input=batch,
                )
                return [item.embedding for item in response.data]
            except openai.RateLimitError:
                if attempt == MAX_RETRIES:
                    logger.error(
                        "OpenAI rate limit hit; max retries (%d) exhausted", MAX_RETRIES
                    )
                    raise
                logger.warning(
                    "OpenAI rate limit (attempt %d/%d); retrying in %.1fs",
                    attempt, MAX_RETRIES, backoff,
                )
                await asyncio.sleep(backoff)
                backoff *= 2  # exponential backoff
        # Should never reach here
        raise RuntimeError("Unreachable: retry loop exited without result")  # pragma: no cover

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed all texts in batches of EMBED_BATCH_SIZE.

        Args:
            texts: Texts to embed.

        Returns:
            Embedding vectors in the same order as the inputs.
        """
        if not texts:
            return []

        results: list[list[float]] = []
        for i in range(0, len(texts), EMBED_BATCH_SIZE):
            batch = texts[i : i + EMBED_BATCH_SIZE]
            logger.debug("Embedding batch %d/%d (%d texts)", i // EMBED_BATCH_SIZE + 1, -(-len(texts) // EMBED_BATCH_SIZE), len(batch))
            batch_result = await self._embed_batch_with_retry(batch)
            results.extend(batch_result)

        return results


# ---------------------------------------------------------------------------
# Anthropic stub
# ---------------------------------------------------------------------------


class AnthropicEmbeddingProvider(EmbeddingProvider):
    """Stub: Anthropic has no first-party standalone embeddings API.

    As of 2025, Anthropic does not offer a dedicated embeddings endpoint.
    The expected production pattern is::

        LLM_PROVIDER=anthropic
        EMBEDDING_PROVIDER=openai   # <-- use OpenAI for embeddings

    If you need an embeddings provider compatible with Anthropic's ecosystem,
    consider using a third-party provider or OpenAI embeddings directly.

    Raises:
        NotImplementedError: Always — this provider is not implemented.
    """

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError(
            "Anthropic does not provide a standalone embeddings API. "
            "Set EMBEDDING_PROVIDER=openai (or 'custom') in your environment. "
            "See app/services/embedding_service.py for details."
        )


# ---------------------------------------------------------------------------
# Groq stub
# ---------------------------------------------------------------------------


class GroqEmbeddingProvider(EmbeddingProvider):
    """Stub: Groq uses third-party embedding models via a custom base URL.

    To enable Groq embeddings:
    1. Set ``EMBEDDING_PROVIDER=groq`` in your environment.
    2. Set ``EMBEDDING_BASE_URL`` to your Groq-compatible OpenAI-format endpoint.
    3. Set ``EMBEDDING_MODEL`` to the desired model name.

    Until a concrete endpoint is configured this class raises
    ``NotImplementedError``.

    Raises:
        NotImplementedError: Always in the current stub implementation.
    """

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError(
            "Groq embedding support requires a custom EMBEDDING_BASE_URL. "
            "Configure it in your environment and update this provider. "
            "See app/services/embedding_service.py for details."
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    """Instantiate the correct embedding provider based on settings.

    Provider selection uses **only** ``settings.EMBEDDING_PROVIDER`` and is
    completely independent of ``settings.LLM_PROVIDER``.  This allows, for
    example, using Anthropic as the LLM while delegating embeddings to OpenAI.

    Args:
        settings: Application settings instance.

    Returns:
        Configured ``EmbeddingProvider`` concrete instance.

    Raises:
        ValueError: If ``EMBEDDING_PROVIDER`` is set to an unsupported value.
    """
    provider = settings.EMBEDDING_PROVIDER

    if provider == EmbeddingProviderEnum.OPENAI:
        return OpenAIEmbeddingProvider(
            api_key=settings.LLM_API_KEY,
            model=settings.EMBEDDING_MODEL,
        )
    if provider == EmbeddingProviderEnum.ANTHROPIC:
        return AnthropicEmbeddingProvider()
    if provider == EmbeddingProviderEnum.GROQ:
        return GroqEmbeddingProvider()
    if provider == EmbeddingProviderEnum.CUSTOM:
        raise ValueError(
            "EMBEDDING_PROVIDER=custom requires a concrete EmbeddingProvider "
            "subclass to be wired up manually.  See embedding_service.py."
        )

    raise ValueError(
        f"Unsupported EMBEDDING_PROVIDER: {provider!r}.  "
        f"Valid options: openai, anthropic, groq, custom."
    )
