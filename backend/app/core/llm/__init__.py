"""LLM module exports and factory."""

from __future__ import annotations

from app.config import LLMProvider, Settings
from app.core.llm.anthropic_provider import AnthropicProvider
from app.core.llm.base import BaseLLMProvider, Message
from app.core.llm.groq_provider import GroqProvider
from app.core.llm.openai_provider import OpenAIProvider


def get_llm_provider(settings: Settings) -> BaseLLMProvider:
    """Instantiate the configured LLM provider based on settings.LLM_PROVIDER.

    Args:
        settings: Application Settings instance.

    Returns:
        Concrete BaseLLMProvider instance.

    Raises:
        ValueError: If LLM_PROVIDER is unsupported.
    """
    provider = settings.LLM_PROVIDER

    if provider == LLMProvider.OPENAI:
        return OpenAIProvider(
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL,
        )
    if provider == LLMProvider.ANTHROPIC:
        model = settings.LLM_MODEL if settings.LLM_MODEL != "gpt-4o" else "claude-3-5-sonnet-20241022"
        return AnthropicProvider(
            api_key=settings.LLM_API_KEY,
            model=model,
        )
    if provider == LLMProvider.GROQ:
        model = settings.LLM_MODEL if settings.LLM_MODEL != "gpt-4o" else "llama-3.3-70b-versatile"
        return GroqProvider(
            api_key=settings.LLM_API_KEY,
            model=model,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider!r}")


__all__ = [
    "AnthropicProvider",
    "BaseLLMProvider",
    "GroqProvider",
    "Message",
    "OpenAIProvider",
    "get_llm_provider",
]
