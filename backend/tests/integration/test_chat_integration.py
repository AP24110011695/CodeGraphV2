"""PostgreSQL-backed chat persistence and streaming test with a mocked LLM."""

import uuid
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.config import EnvironmentType, Settings
from app.dependencies import get_db
from app.main import create_app
from app.models.chat_session import ChatSession
from app.models.code_chunk import ChunkType, CodeChunk
from app.models.code_file import CodeFile
from app.models.repository import Repository, RepositorySource, RepositoryStatus


async def _answer() -> AsyncIterator[str]:
    yield "Authentication "
    yield "is checked."


async def test_chat_stream_is_persisted_with_sources(
    db_session: AsyncSession, integration_engine: AsyncEngine
) -> None:
    """A mocked answer streams to the client and persists both chat messages."""
    repository = Repository(
        id=uuid.uuid4(), name="chat", slug="chat", source=RepositorySource.UPLOAD,
        status=RepositoryStatus.READY, size_bytes=1, file_count=1,
    )
    code_file = CodeFile(
        id=uuid.uuid4(), repository_id=repository.id, path="auth.py", language="Python",
        size_bytes=1, content_hash="auth", line_count=2, is_binary=False,
    )
    chunk = CodeChunk(
        id=uuid.uuid4(), repository_id=repository.id, file_id=code_file.id,
        content="def authenticate(user): return True", start_line=1, end_line=1,
        chunk_type=ChunkType.SYMBOL, embedding=[1.0] + [0.0] * 1535,
    )
    session = ChatSession(id=uuid.uuid4(), repository_id=repository.id, title="Auth")
    db_session.add_all([repository, code_file, chunk, session])
    await db_session.commit()

    settings = Settings(
        DATABASE_URL=str(integration_engine.url), SECRET_KEY="test", LLM_API_KEY="test",
        ENVIRONMENT=EnvironmentType.PRODUCTION,
    )
    application = create_app(settings=settings)

    async def override_db():
        yield db_session

    application.dependency_overrides[get_db] = override_db
    embedder = AsyncMock()
    embedder.embed.return_value = [[1.0] + [0.0] * 1535]
    llm = MagicMock(max_context_tokens=1_000, model_name="test")
    llm.count_tokens.return_value = 1
    llm.chat = AsyncMock(return_value=_answer())
    with (
        patch("app.services.rag_service.get_embedding_provider", return_value=embedder),
        patch("app.services.rag_service.get_llm_provider", return_value=llm),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=application), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/repositories/{repository.id}/chat/sessions/{session.id}/messages",
                json={"question": "How does authentication work?"},
            )

    assert response.status_code == 200
    assert "data: Authentication " in response.text
    assert "data: __sources__:" in response.text
