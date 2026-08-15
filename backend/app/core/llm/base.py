"""Base LLM provider abstract interface and data structures."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal

RoleType = Literal["system", "user", "assistant"]


@dataclass(slots=True)
class Message:
    """A single chat message."""

    role: RoleType
    content: str


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the underlying LLM model."""
        ...

    @property
    @abstractmethod
    def max_context_tokens(self) -> int:
        """Maximum context window token limit for this model."""
        ...

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Estimate or compute token count for a text string."""
        ...

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        stream: bool = False,
    ) -> AsyncIterator[str] | str:
        """Send chat messages to the provider.

        Args:
            messages: List of chat messages.
            stream: If True, returns an AsyncIterator of text deltas.
                    If False, returns full response string.

        Returns:
            AsyncIterator of token deltas if stream=True, or complete response string if stream=False.
        """
        ...
