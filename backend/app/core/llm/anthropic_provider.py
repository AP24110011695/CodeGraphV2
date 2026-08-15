"""Anthropic LLM Provider implementation."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

import anthropic

from app.core.llm.base import BaseLLMProvider, Message

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic LLM provider using official AsyncAnthropic SDK."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022") -> None:
        self._api_key = api_key
        self._model = model
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def max_context_tokens(self) -> int:
        return 200_000

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return len(text) // 4

    async def _stream_chat(
        self, system_text: str | None, payload: list[dict[str, str]]
    ) -> AsyncIterator[str]:
        kwargs: dict[str, str | list[dict[str, str]] | int] = {
            "model": self._model,
            "max_tokens": 4096,
            "messages": payload,
        }
        if system_text:
            kwargs["system"] = system_text

        async with self._client.messages.stream(**kwargs) as stream:  # type: ignore[arg-type]
            async for text in stream.text_stream:
                if text:
                    yield text

    async def chat(
        self,
        messages: list[Message],
        stream: bool = False,
    ) -> AsyncIterator[str] | str:
        system_parts = [m.content for m in messages if m.role == "system"]
        system_text = "\n\n".join(system_parts) if system_parts else None

        payload = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in ("user", "assistant")
        ]

        if stream:
            return self._stream_chat(system_text, payload)

        kwargs: dict[str, str | list[dict[str, str]] | int] = {
            "model": self._model,
            "max_tokens": 4096,
            "messages": payload,
        }
        if system_text:
            kwargs["system"] = system_text

        response = await self._client.messages.create(**kwargs)  # type: ignore[arg-type]
        if response.content and len(response.content) > 0:
            first_block = response.content[0]
            if hasattr(first_block, "text"):
                return first_block.text
        return ""
