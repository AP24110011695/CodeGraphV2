"""PostgreSQL-backed semantic-search API integration test with mocked embeddings."""

import uuid
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.config import EnvironmentType, Settings
from app.dependencies import get_db
from app.main import create_app
from app.models.code_chunk import ChunkType, CodeChunk
from app.models.code_file import CodeFile
from app.models.repository import Repository, RepositorySource, RepositoryStatus


async def test_semantic_search_returns_matching_chunk(
    db_session: AsyncSession, integration_engine: AsyncEngine
) -> None:
    """Search queries pgvector data and returns a source-backed matching result."""
    repository = Repository(
        id=uuid.uuid4(), name="search", slug="search", source=RepositorySource.UPLOAD,
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
    db_session.add_all([repository, code_file, chunk])
    await db_session.commit()

    settings = Settings(
        DATABASE_URL=str(integration_engine.url), SECRET_KEY="test", LLM_API_KEY="test",
        ENVIRONMENT=EnvironmentType.PRODUCTION,
    )
    application = create_app(settings=settings)

    async def override_db():
        yield db_session

    application.dependency_overrides[get_db] = override_db
    provider = AsyncMock()
    provider.embed.return_value = [[1.0] + [0.0] * 1535]
    with patch("app.api.v1.search.get_embedding_provider", return_value=provider):
        async with AsyncClient(
            transport=ASGITransport(app=application), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/repositories/{repository.id}/search",
                json={"query": "authentication", "limit": 3},
            )

    assert response.status_code == 200
    assert response.json()[0]["path"] == "auth.py"
    assert response.json()[0]["score"] == 1.0
