"""Tests for Phase 14 — LLM Provider Abstraction & Prompt Management.

Covers:
- get_llm_provider factory selection for OpenAI, Anthropic, and Groq.
- OpenAIProvider: non-streaming chat, streaming chat, token counting via tiktoken.
- AnthropicProvider: non-streaming chat, streaming chat, system prompt extraction.
- GroqProvider: non-streaming chat, streaming chat.
- Prompt management: system prompt directives, context block formatting, RAG user prompt rendering.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import LLMProvider, Settings
from app.core.llm import (
    AnthropicProvider,
    GroqProvider,
    Message,
    OpenAIProvider,
    get_llm_provider,
)
from app.core.llm.prompts import (
    SYSTEM_PROMPT,
    build_rag_prompt,
    format_context_block,
)


def _settings(**kwargs: Any) -> Settings:
    defaults = dict(
        DATABASE_URL="postgresql+asyncpg://localhost/test",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret",
        LLM_API_KEY="sk-fake-key",
        LLM_PROVIDER=LLMProvider.OPENAI,
        LLM_MODEL="gpt-4o",
    )
    defaults.update(kwargs)
    return Settings(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Factory Tests
# ---------------------------------------------------------------------------


class TestLLMFactory:
    def test_factory_selects_openai(self) -> None:
        settings = _settings(LLM_PROVIDER=LLMProvider.OPENAI, LLM_MODEL="gpt-4o")
        with patch("app.core.llm.openai_provider.openai.AsyncOpenAI"):
            provider = get_llm_provider(settings)
        assert isinstance(provider, OpenAIProvider)
        assert provider.model_name == "gpt-4o"

    def test_factory_selects_anthropic(self) -> None:
        settings = _settings(LLM_PROVIDER=LLMProvider.ANTHROPIC, LLM_MODEL="claude-3-5-sonnet-20241022")
        with patch("app.core.llm.anthropic_provider.anthropic.AsyncAnthropic"):
            provider = get_llm_provider(settings)
        assert isinstance(provider, AnthropicProvider)
        assert provider.model_name == "claude-3-5-sonnet-20241022"

    def test_factory_selects_groq(self) -> None:
        settings = _settings(LLM_PROVIDER=LLMProvider.GROQ, LLM_MODEL="llama-3.3-70b-versatile")
        with patch("app.core.llm.groq_provider.groq.AsyncGroq"):
            provider = get_llm_provider(settings)
        assert isinstance(provider, GroqProvider)
        assert provider.model_name == "llama-3.3-70b-versatile"

    def test_factory_raises_on_invalid_provider(self) -> None:
        settings = _settings()
        settings.LLM_PROVIDER = "invalid_provider"  # type: ignore[assignment]
        with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
            get_llm_provider(settings)


# ---------------------------------------------------------------------------
# OpenAI Provider Tests
# ---------------------------------------------------------------------------


class TestOpenAIProvider:
    @pytest.mark.asyncio
    async def test_openai_non_streaming_chat(self) -> None:
        with patch("app.core.llm.openai_provider.openai.AsyncOpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_resp = MagicMock()
            mock_resp.choices = [MagicMock(message=MagicMock(content="Hello from OpenAI"))]
            mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client

            provider = OpenAIProvider(api_key="sk-key", model="gpt-4o")
            messages = [Message(role="user", content="Hi")]
            result = await provider.chat(messages, stream=False)

            assert result == "Hello from OpenAI"
            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_openai_streaming_chat(self) -> None:
        with patch("app.core.llm.openai_provider.openai.AsyncOpenAI") as mock_cls:
            mock_client = MagicMock()

            # Fake async iterator for stream chunks
            async def fake_stream():
                for token in ["Hello", " ", "world"]:
                    chunk = MagicMock()
                    chunk.choices = [MagicMock(delta=MagicMock(content=token))]
                    yield chunk

            mock_client.chat.completions.create = AsyncMock(return_value=fake_stream())
            mock_cls.return_value = mock_client

            provider = OpenAIProvider(api_key="sk-key", model="gpt-4o")
            messages = [Message(role="user", content="Hi")]
            stream_gen = await provider.chat(messages, stream=True)

            tokens = []
            async for token in stream_gen:
                tokens.append(token)

            assert "".join(tokens) == "Hello world"

    def test_token_counting(self) -> None:
        with patch("app.core.llm.openai_provider.openai.AsyncOpenAI"):
            provider = OpenAIProvider(api_key="sk-key", model="gpt-4o")
            with patch("tiktoken.encoding_for_model") as mock_enc:
                mock_enc.return_value.encode.return_value = [101, 102, 103, 104, 105]
                count = provider.count_tokens("def foo(): return 42")
                assert count == 5


# ---------------------------------------------------------------------------
# Anthropic Provider Tests
# ---------------------------------------------------------------------------


class TestAnthropicProvider:
    @pytest.mark.asyncio
    async def test_anthropic_non_streaming_chat(self) -> None:
        with patch("app.core.llm.anthropic_provider.anthropic.AsyncAnthropic") as mock_cls:
            mock_client = MagicMock()
            mock_resp = MagicMock()
            mock_block = MagicMock()
            mock_block.text = "Hello from Claude"
            mock_resp.content = [mock_block]
            mock_client.messages.create = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client

            provider = AnthropicProvider(api_key="sk-key", model="claude-3-5-sonnet-20241022")
            messages = [
                Message(role="system", content="You are a helper."),
                Message(role="user", content="Hi"),
            ]
            result = await provider.chat(messages, stream=False)

            assert result == "Hello from Claude"
            mock_client.messages.create.assert_called_once()
            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert call_kwargs["system"] == "You are a helper."
            assert call_kwargs["messages"] == [{"role": "user", "content": "Hi"}]

    @pytest.mark.asyncio
    async def test_anthropic_streaming_chat(self) -> None:
        with patch("app.core.llm.anthropic_provider.anthropic.AsyncAnthropic") as mock_cls:
            mock_client = MagicMock()

            class FakeStream:
                def __init__(self):
                    self.text_stream = self._stream()

                async def _stream(self):
                    for word in ["Claude", " ", "response"]:
                        yield word

                async def __aenter__(self):
                    return self

                async def __aexit__(self, *args):
                    pass

            mock_client.messages.stream.return_value = FakeStream()
            mock_cls.return_value = mock_client

            provider = AnthropicProvider(api_key="sk-key")
            messages = [Message(role="user", content="Hi")]
            stream_gen = await provider.chat(messages, stream=True)

            tokens = []
            async for token in stream_gen:
                tokens.append(token)

            assert "".join(tokens) == "Claude response"


# ---------------------------------------------------------------------------
# Groq Provider Tests
# ---------------------------------------------------------------------------


class TestGroqProvider:
    @pytest.mark.asyncio
    async def test_groq_non_streaming_chat(self) -> None:
        with patch("app.core.llm.groq_provider.groq.AsyncGroq") as mock_cls:
            mock_client = MagicMock()
            mock_resp = MagicMock()
            mock_resp.choices = [MagicMock(message=MagicMock(content="Hello from Groq"))]
            mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client

            provider = GroqProvider(api_key="gsk-key", model="llama-3.3-70b-versatile")
            messages = [Message(role="user", content="Hi")]
            result = await provider.chat(messages, stream=False)

            assert result == "Hello from Groq"
            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_groq_streaming_chat(self) -> None:
        with patch("app.core.llm.groq_provider.groq.AsyncGroq") as mock_cls:
            mock_client = MagicMock()

            async def fake_stream():
                for token in ["Groq", " ", "stream"]:
                    chunk = MagicMock()
                    chunk.choices = [MagicMock(delta=MagicMock(content=token))]
                    yield chunk

            mock_client.chat.completions.create = AsyncMock(return_value=fake_stream())
            mock_cls.return_value = mock_client

            provider = GroqProvider(api_key="gsk-key")
            messages = [Message(role="user", content="Hi")]
            stream_gen = await provider.chat(messages, stream=True)

            tokens = []
            async for token in stream_gen:
                tokens.append(token)

            assert "".join(tokens) == "Groq stream"


# ---------------------------------------------------------------------------
# Prompt Management Tests
# ---------------------------------------------------------------------------


class TestPrompts:
    def test_system_prompt_directives(self) -> None:
        assert "CodeGraph AI" in SYSTEM_PROMPT
        assert "STRICTLY" in SYSTEM_PROMPT
        assert "I don't know based on the provided codebase context." in SYSTEM_PROMPT

    def test_format_context_block(self) -> None:
        block = format_context_block(
            index=1,
            file_path="src/auth.py",
            start_line=10,
            end_line=25,
            content="def login(): pass",
            symbol_name="login",
        )
        assert "[Context Item #1]" in block
        assert "File: src/auth.py (Lines 10-25)" in block
        assert "Symbol: login" in block
        assert "def login(): pass" in block

    def test_build_rag_prompt(self) -> None:
        context_items = [
            {
                "file_path": "src/main.py",
                "start_line": 1,
                "end_line": 10,
                "content": "print('hello')",
                "symbol_name": "main",
            }
        ]
        prompt = build_rag_prompt("How does main work?", context_items)
        assert "User Question: How does main work?" in prompt
        assert "File: src/main.py (Lines 1-10)" in prompt
        assert "Symbol: main" in prompt
        assert "print('hello')" in prompt

    def test_build_rag_prompt_empty_context(self) -> None:
        prompt = build_rag_prompt("Where is login?", [])
        assert "No relevant codebase context found." in prompt
        assert "User Question: Where is login?" in prompt
