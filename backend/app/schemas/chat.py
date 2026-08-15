"""Pydantic schemas for Chat and RAG API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateSessionRequest(BaseModel):
    """Request body to create a new chat session."""

    title: str | None = Field(default=None, description="Optional title for the chat session.")


class CreateSessionResponse(BaseModel):
    """Response containing created session ID."""

    session_id: uuid.UUID = Field(description="UUID of the created chat session.")


class ChatSessionResponse(BaseModel):
    """Schema for chat session detail."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repository_id: uuid.UUID
    title: str | None = None
    created_at: datetime
    updated_at: datetime


class SendMessageRequest(BaseModel):
    """Request body to send a question in a chat session."""

    question: str = Field(
        ...,
        min_length=1,
        description="User question to send to the grounded RAG assistant.",
        examples=["How does the authentication flow work?"],
    )


class SourceItem(BaseModel):
    """A cited source code reference."""

    path: str = Field(description="Repository-relative file path.")
    start_line: int = Field(description="1-indexed start line.")
    end_line: int = Field(description="1-indexed end line.")
    symbol_name: str | None = Field(default=None, description="Symbol name if applicable.")


class ChatMessageResponse(BaseModel):
    """Schema for a single chat message item in history."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    sources: list[SourceItem] | None = Field(
        default_factory=list, description="Cited file sources."
    )
    created_at: datetime
