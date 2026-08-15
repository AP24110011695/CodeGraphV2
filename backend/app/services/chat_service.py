"""Chat session and message management service."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession

logger = logging.getLogger(__name__)


async def create_session(
    repo_id: uuid.UUID,
    db: AsyncSession,
    title: str | None = None,
) -> ChatSession:
    """Create and persist a new ChatSession for a repository.

    Args:
        repo_id: Repository UUID.
        db: Async database session.
        title: Optional title.

    Returns:
        Created ChatSession instance.
    """
    session = ChatSession(
        id=uuid.uuid4(),
        repository_id=repo_id,
        title=title or "New Chat Session",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(
    session_id: uuid.UUID,
    repo_id: uuid.UUID,
    db: AsyncSession,
) -> ChatSession:
    """Fetch a ChatSession by ID, scoped to a repository.

    Args:
        session_id: Session UUID.
        repo_id: Repository UUID.
        db: Async database session.

    Returns:
        ChatSession ORM instance.

    Raises:
        NotFoundError: If no matching session is found.
    """
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.repository_id == repo_id,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise NotFoundError(
            message=f"ChatSession '{session_id}' not found for repository '{repo_id}'.",
            code="SESSION_NOT_FOUND",
        )
    return session


async def list_messages(
    session_id: uuid.UUID,
    repo_id: uuid.UUID,
    db: AsyncSession,
) -> list[ChatMessage]:
    """Retrieve all ChatMessage records for a session ordered by creation time.

    Args:
        session_id: Session UUID.
        repo_id: Repository UUID.
        db: Async database session.

    Returns:
        List of ChatMessage ORM instances.
    """
    # Verify session existence
    await get_session(session_id, repo_id, db)

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return list(result.scalars().all())


async def save_message(
    session_id: uuid.UUID,
    role: str,
    content: str,
    db: AsyncSession,
    sources: list[dict[str, Any]] | None = None,
) -> ChatMessage:
    """Insert and persist a new ChatMessage in a session.

    Args:
        session_id: Session UUID.
        role: Message role ('user', 'assistant', 'system').
        content: Text content of the message.
        db: Async database session.
        sources: Optional list of source citation dicts.

    Returns:
        Persisted ChatMessage instance.
    """
    message = ChatMessage(
        id=uuid.uuid4(),
        session_id=session_id,
        role=role,
        content=content,
        sources=sources or [],
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message
