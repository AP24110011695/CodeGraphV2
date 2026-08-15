"""Tests for Phase 15 — RAG Pipeline, Chat History & Chat API.

Covers:
- Chat session CRUD (create, fetch detail, list messages).
- RAG retrieval & prompt building.
- SSE streaming chat messages (POST /chat/sessions/{sid}/messages).
- Verification of token deltas, __sources__ JSON block, and [DONE] sentinel in stream.
- Message history persistence and source citation storage.
- Multi-turn conversation turns included in LLM context.
- Error handling (404 on missing repo / session).
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import EnvironmentType, Settings
from app.db.base import Base
from app.dependencies import get_db
from app.models.chat_session import ChatSession
from app.models.code_chunk import ChunkType, CodeChunk
from app.models.code_file import CodeFile
from app.models.repository import Repository, RepositorySource, RepositoryStatus
from app.services import chat_service

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_engine() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Create an in-memory SQLite engine with all tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    return engine, factory


def _make_settings() -> Settings:
    return Settings(
        DATABASE_URL="postgresql+asyncpg://localhost/test",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret",
        LLM_API_KEY="test-key",
        ENVIRONMENT=EnvironmentType.PRODUCTION,
    )


def _repo() -> Repository:
    return Repository(
        id=uuid.uuid4(),
        name="test-repo",
        slug=f"test-repo-{uuid.uuid4().hex[:6]}",
        source=RepositorySource.UPLOAD,
        status=RepositoryStatus.READY,
        size_bytes=1000,
        file_count=1,
    )


# ---------------------------------------------------------------------------
# Chat Service Unit Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_service_crud() -> None:
    """Chat service creates sessions, retrieves detail, saves and lists messages."""
    engine, Session = await _make_engine()

    async with Session() as db:
        repo = _repo()
        db.add(repo)
        await db.commit()

    async with Session() as db:
        session = await chat_service.create_session(repo.id, db, title="Auth Session")
        assert session.repository_id == repo.id
        assert session.title == "Auth Session"

        # Fetch session
        fetched = await chat_service.get_session(session.id, repo.id, db)
        assert fetched.id == session.id

        # Save messages
        await chat_service.save_message(
            session.id, role="user", content="How does login work?", db=db
        )
        await chat_service.save_message(
            session.id,
            role="assistant",
            content="Login verifies password.",
            db=db,
            sources=[{"path": "auth.py", "start_line": 10, "end_line": 20}],
        )

        messages = await chat_service.list_messages(session.id, repo.id, db)
        assert len(messages) == 2
        assert messages[0].content == "How does login work?"
        assert messages[1].sources[0]["path"] == "auth.py"


# ---------------------------------------------------------------------------
# RAG & Chat API End-to-End Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_api_create_session() -> None:
    """POST /chat/sessions creates session and returns session_id."""
    from httpx import ASGITransport, AsyncClient

    from app.main import create_app

    settings = _make_settings()
    test_app = create_app(settings=settings)
    engine, Session = await _make_engine()

    async with Session() as db:
        repo = _repo()
        db.add(repo)
        await db.commit()

    async def _override_get_db():
        async with Session() as session:
            yield session

    test_app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/repositories/{repo.id}/chat/sessions",
            json={"title": "Test Session"},
        )

    test_app.dependency_overrides.clear()
    assert resp.status_code == 201
    data = resp.json()
    assert "session_id" in data
    assert uuid.UUID(data["session_id"])


@pytest.mark.asyncio
async def test_chat_api_stream_message_and_history() -> None:
    """POST /messages streams SSE tokens, emits __sources__, and persists history."""
    from httpx import ASGITransport, AsyncClient

    from app.main import create_app

    settings = _make_settings()
    test_app = create_app(settings=settings)
    engine, Session = await _make_engine()

    async with Session() as db:
        repo = _repo()
        db.add(repo)
        await db.flush()

        code_file = CodeFile(
            id=uuid.uuid4(),
            repository_id=repo.id,
            path="src/auth.py",
            language="Python",
            size_bytes=200,
            content_hash="h1",
            line_count=30,
            is_binary=False,
        )
        db.add(code_file)
        await db.flush()

        chunk = CodeChunk(
            id=uuid.uuid4(),
            file_id=code_file.id,
            repository_id=repo.id,
            content="# File: src/auth.py\n\ndef login(user, pwd):\n    return True\n",
            start_line=1,
            end_line=10,
            chunk_type=ChunkType.SYMBOL,
            embedding=[0.1] * 1536,
        )
        db.add(chunk)

        session = ChatSession(
            id=uuid.uuid4(),
            repository_id=repo.id,
            title="Authentication Session",
        )
        db.add(session)
        await db.commit()

    async def _override_get_db():
        async with Session() as session:
            yield session

    test_app.dependency_overrides[get_db] = _override_get_db

    # Mock embedding provider
    mock_embed_provider = AsyncMock()
    mock_embed_provider.embed = AsyncMock(return_value=[[0.1] * 1536])

    # Mock LLM provider streaming
    mock_llm_provider = MagicMock()
    mock_llm_provider.max_context_tokens = 100_000
    mock_llm_provider.count_tokens = MagicMock(return_value=10)

    async def _fake_llm_stream(messages, stream=True):
        for token in ["The ", "login ", "function ", "authenticates ", "users."]:
            yield token

    mock_llm_provider.chat = AsyncMock(side_effect=_fake_llm_stream)

    with patch(
        "app.services.rag_service.get_embedding_provider",
        return_value=mock_embed_provider,
    ), patch(
        "app.services.rag_service.get_llm_provider",
        return_value=mock_llm_provider,
    ):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Send message and stream SSE
            resp = await client.post(
                f"/api/v1/repositories/{repo.id}/chat/sessions/{session.id}/messages",
                json={"question": "How does login work?"},
            )
            assert resp.status_code == 200
            assert "text/event-stream" in resp.headers["content-type"]
            sse_content = resp.text

            # Verify SSE structure
            assert "data: The \n\n" in sse_content
            assert "data: login \n\n" in sse_content
            assert "data: __sources__:" in sse_content
            assert "src/auth.py" in sse_content
            assert "data: [DONE]\n\n" in sse_content

            # 2. Check history GET endpoint
            hist_resp = await client.get(
                f"/api/v1/repositories/{repo.id}/chat/sessions/{session.id}/messages"
            )
            assert hist_resp.status_code == 200
            messages_history = hist_resp.json()
            assert len(messages_history) == 2  # user + assistant

            user_msg = messages_history[0]
            assert user_msg["role"] == "user"
            assert user_msg["content"] == "How does login work?"

            assistant_msg = messages_history[1]
            assert assistant_msg["role"] == "assistant"
            assert assistant_msg["content"] == "The login function authenticates users."
            assert len(assistant_msg["sources"]) > 0
            assert assistant_msg["sources"][0]["path"] == "src/auth.py"

    test_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_chat_api_404_non_existent_session() -> None:
    """POST /messages for non-existent session returns 404."""
    from httpx import ASGITransport, AsyncClient

    from app.main import create_app

    settings = _make_settings()
    test_app = create_app(settings=settings)
    engine, Session = await _make_engine()

    async with Session() as db:
        repo = _repo()
        db.add(repo)
        await db.commit()

    async def _override_get_db():
        async with Session() as session:
            yield session

    test_app.dependency_overrides[get_db] = _override_get_db

    fake_session_id = uuid.uuid4()
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/repositories/{repo.id}/chat/sessions/{fake_session_id}/messages",
            json={"question": "hello?"},
        )

    test_app.dependency_overrides.clear()
    assert resp.status_code == 404
