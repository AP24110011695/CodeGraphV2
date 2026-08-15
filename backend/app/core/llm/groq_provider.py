"""Groq LLM Provider implementation."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

import groq

from app.core.llm.base import BaseLLMProvider, Message

logger = logging.getLogger(__name__)


class GroqProvider(BaseLLMProvider):
    """Groq LLM provider using official AsyncGroq SDK (OpenAI-compatible)."""

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile") -> None:
        self._api_key = api_key
        self._model = model
        self._client = groq.AsyncGroq(api_key=api_key)

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def max_context_tokens(self) -> int:
        if "70b" in self._model or "llama-3.3" in self._model:
            return 128_000
        if "mixtral" in self._model:
            return 32_768
        return 32_768

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return len(text) // 4

    async def _stream_chat(self, payload: list[dict[str, str]]) -> AsyncIterator[str]:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=payload,  # type: ignore[arg-type]
            stream=True,
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def chat(
        self,
        messages: list[Message],
        stream: bool = False,
    ) -> AsyncIterator[str] | str:
        payload = [{"role": m.role, "content": m.content} for m in messages]

        if stream:
            return self._stream_chat(payload)

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=payload,  # type: ignore[arg-type]
            stream=False,
        )
        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content
        return ""
