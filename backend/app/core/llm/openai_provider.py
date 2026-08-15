"""OpenAI LLM Provider implementation."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator

import openai

from app.core.llm.base import BaseLLMProvider, Message

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider using official AsyncOpenAI SDK."""

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        self._api_key = api_key
        self._model = model
        self._client = openai.AsyncOpenAI(api_key=api_key)

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def max_context_tokens(self) -> int:
        if "gpt-4o" in self._model:
            return 128_000
        if "gpt-4" in self._model:
            return 8_192
        if "gpt-3.5" in self._model:
            return 16_385
        return 128_000

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        try:
            import tiktoken

            try:
                encoding = tiktoken.encoding_for_model(self._model)
            except KeyError:
                encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
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
