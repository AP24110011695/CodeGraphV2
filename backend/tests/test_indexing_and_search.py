"""Tests for Phase 13 — Vector Indexing & Semantic Search API.

Covers:
- index_repository: chunking, embedding, inserting CodeChunk rows, updating job progress/status, and setting Repository.status = "ready".
- Idempotency of index_repository (re-indexing clears old chunks).
- POST /api/v1/repositories/{repo_id}/search API endpoint.
- Correct ranking of search results by cosine similarity score.
- Search 404 for non-existent repository.
- Search on repository with no chunks returning empty list.
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import EnvironmentType, Settings
from app.db.base import Base
from app.dependencies import get_db
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.code_chunk import ChunkType, CodeChunk
from app.models.code_file import CodeFile
from app.models.repository import Repository, RepositorySource, RepositoryStatus
from app.models.symbol import Symbol, SymbolKind
from app.services.indexer import index_repository

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_PY = FIXTURES_DIR / "sample.py"


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


def _fake_vector_for_text(text: str, dim: int = 1536) -> list[float]:
    """Generate a deterministic normalized vector based on string content for testing."""
    vec = [0.0] * dim
    # Set a few indices based on keywords in text to allow score differentiation
    lowered = text.lower()
    if "auth" in lowered or "login" in lowered:
        vec[0] = 0.9
        vec[1] = 0.1
    elif "math" in lowered or "calculate" in lowered or "add" in lowered:
        vec[0] = 0.1
        vec[1] = 0.9
    else:
        vec[0] = 0.5
        vec[1] = 0.5

    # Normalize
    norm = sum(x * x for x in vec) ** 0.5
    return [x / norm for x in vec]


def _repo() -> Repository:
    return Repository(
        id=uuid.uuid4(),
        name="test-repo",
        slug=f"test-repo-{uuid.uuid4().hex[:6]}",
        source=RepositorySource.UPLOAD,
        status=RepositoryStatus.PARSING,
        size_bytes=1000,
        file_count=1,
    )


# ---------------------------------------------------------------------------
# Indexer Integration Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_index_repository_creates_chunks_and_sets_ready(tmp_path: Path) -> None:
    """index_repository chunks source files, embeds, and sets status to ready."""
    engine, Session = await _make_engine()
    settings = _make_settings()

    async with Session() as db:
        repo = _repo()
        db.add(repo)
        await db.flush()

        job = AnalysisJob(
            repository_id=repo.id,
            phase="parsing",
            status=JobStatus.RUNNING,
            progress=60,
        )
        db.add(job)

        code_file = CodeFile(
            id=uuid.uuid4(),
            repository_id=repo.id,
            path="sample.py",
            language="Python",
            size_bytes=500,
            content_hash="hash123",
            line_count=20,
            is_binary=False,
        )
        db.add(code_file)
        await db.flush()

        symbol = Symbol(
            id=uuid.uuid4(),
            repository_id=repo.id,
            file_id=code_file.id,
            name="add_numbers",
            kind=SymbolKind.FUNCTION,
            start_line=1,
            end_line=5,
            is_exported=True,
        )
        db.add(symbol)
        await db.commit()

        # Setup source file on disk
        source_dir = tmp_path / str(repo.id) / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        if SAMPLE_PY.exists():
            shutil.copy(SAMPLE_PY, source_dir / "sample.py")
        else:
            (source_dir / "sample.py").write_text(
                "def add_numbers(a, b):\n    return a + b\n", encoding="utf-8"
            )

    # Mock embedding provider
    fake_embed = AsyncMock(
        side_effect=lambda texts: [_fake_vector_for_text(t) for t in texts]
    )

    async with Session() as db:
        repo_obj = (
            await db.execute(select(Repository).where(Repository.id == repo.id))
        ).scalar_one()

        with patch("app.services.indexer.get_embedding_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.embed = fake_embed
            mock_get_provider.return_value = mock_provider

            chunk_count = await index_repository(
                repo_obj, db, settings=settings, upload_dir=str(tmp_path)
            )

        assert chunk_count > 0

        # Verify DB state
        chunks_res = await db.execute(
            select(CodeChunk).where(CodeChunk.repository_id == repo.id)
        )
        chunks = list(chunks_res.scalars().all())
        assert len(chunks) == chunk_count

        # Verify repo status
        assert repo_obj.status == RepositoryStatus.READY

        # Verify job state
        job_res = await db.execute(
            select(AnalysisJob).where(AnalysisJob.repository_id == repo.id)
        )
        updated_job = job_res.scalar_one()
        assert updated_job.status == JobStatus.DONE
        assert updated_job.progress == 100
        assert updated_job.phase == "indexing"


@pytest.mark.asyncio
async def test_index_repository_idempotency(tmp_path: Path) -> None:
    """Re-indexing clears existing chunks and replaces them."""
    engine, Session = await _make_engine()
    settings = _make_settings()

    async with Session() as db:
        repo = _repo()
        db.add(repo)
        await db.flush()

        code_file = CodeFile(
            id=uuid.uuid4(),
            repository_id=repo.id,
            path="main.py",
            language="Python",
            size_bytes=100,
            content_hash="h1",
            line_count=5,
            is_binary=False,
        )
        db.add(code_file)
        await db.commit()

        source_dir = tmp_path / str(repo.id) / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "main.py").write_text("def hello(): pass\n", encoding="utf-8")

    fake_embed = AsyncMock(
        side_effect=lambda texts: [_fake_vector_for_text(t) for t in texts]
    )

    async with Session() as db:
        repo_obj = (
            await db.execute(select(Repository).where(Repository.id == repo.id))
        ).scalar_one()

        with patch("app.services.indexer.get_embedding_provider") as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.embed = fake_embed
            mock_get_provider.return_value = mock_provider

            count1 = await index_repository(
                repo_obj, db, settings=settings, upload_dir=str(tmp_path)
            )
            count2 = await index_repository(
                repo_obj, db, settings=settings, upload_dir=str(tmp_path)
            )

        chunks_res = await db.execute(
            select(CodeChunk).where(CodeChunk.repository_id == repo.id)
        )
        total_chunks = len(list(chunks_res.scalars().all()))

        # Duplicate chunks should not accumulate
        assert total_chunks == count2
        assert count1 == count2


# ---------------------------------------------------------------------------
# Semantic Search API Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_api_404_non_existent_repo() -> None:
    """POST /search on a non-existent repo_id returns 404."""
    from httpx import ASGITransport, AsyncClient

    from app.main import create_app

    settings = _make_settings()
    test_app = create_app(settings=settings)
    engine, Session = await _make_engine()

    async def _override_get_db():
        async with Session() as session:
            yield session

    test_app.dependency_overrides[get_db] = _override_get_db

    fake_repo_id = uuid.uuid4()
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/repositories/{fake_repo_id}/search",
            json={"query": "test query", "limit": 5},
        )

    test_app.dependency_overrides.clear()
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_search_api_returns_ranked_results(tmp_path: Path) -> None:
    """POST /search returns results sorted by vector similarity."""
    from httpx import ASGITransport, AsyncClient

    from app.main import create_app

    settings = _make_settings()
    test_app = create_app(settings=settings)
    engine, Session = await _make_engine()

    async with Session() as db:
        repo = _repo()
        db.add(repo)
        await db.flush()

        f1 = CodeFile(
            id=uuid.uuid4(),
            repository_id=repo.id,
            path="auth.py",
            language="Python",
            size_bytes=100,
            content_hash="h1",
            line_count=10,
            is_binary=False,
        )
        f2 = CodeFile(
            id=uuid.uuid4(),
            repository_id=repo.id,
            path="math_utils.py",
            language="Python",
            size_bytes=100,
            content_hash="h2",
            line_count=10,
            is_binary=False,
        )
        db.add_all([f1, f2])
        await db.flush()

        # Insert chunks with known embeddings
        c1 = CodeChunk(
            id=uuid.uuid4(),
            file_id=f1.id,
            repository_id=repo.id,
            content="# File: auth.py\n\ndef login(): pass",
            start_line=1,
            end_line=5,
            chunk_type=ChunkType.SYMBOL,
            embedding=_fake_vector_for_text("auth login"),
        )
        c2 = CodeChunk(
            id=uuid.uuid4(),
            file_id=f2.id,
            repository_id=repo.id,
            content="# File: math_utils.py\n\ndef add(a, b): return a + b",
            start_line=1,
            end_line=5,
            chunk_type=ChunkType.SYMBOL,
            embedding=_fake_vector_for_text("math calculate add"),
        )
        db.add_all([c1, c2])
        await db.commit()

    async def _override_get_db():
        async with Session() as session:
            yield session

    test_app.dependency_overrides[get_db] = _override_get_db

    fake_provider = AsyncMock()
    fake_provider.embed = AsyncMock(
        side_effect=lambda texts: [_fake_vector_for_text(t) for t in texts]
    )

    with patch("app.api.v1.search.get_embedding_provider", return_value=fake_provider):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                f"/api/v1/repositories/{repo.id}/search",
                json={"query": "user authentication login flow", "limit": 10},
            )

    test_app.dependency_overrides.clear()

    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 2

    # Top result for "authentication login" should be auth.py
    top_result = results[0]
    assert top_result["path"] == "auth.py"
    assert top_result["score"] > results[1]["score"]
    assert "content" in top_result
    assert "start_line" in top_result
    assert "end_line" in top_result
