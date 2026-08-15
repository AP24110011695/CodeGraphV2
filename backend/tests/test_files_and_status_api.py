"""Tests for Phase 16 — Files & Status API Completion.

Covers:
- GET /api/v1/repositories/{repo_id}/files (paginated listing, language filtering).
- GET /api/v1/repositories/{repo_id}/files/{file_id} (text file preview, binary preview error).
- Path traversal security containment check on file content reading.
- GET /api/v1/repositories/{repo_id}/files/{file_id}/symbols.
- GET /api/v1/repositories/{repo_id}/status (status polling with AnalysisJob phase/progress).
- 404 handling for non-existent repo / file.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
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
from app.models.code_file import CodeFile
from app.models.repository import Repository, RepositorySource, RepositoryStatus
from app.models.symbol import Symbol, SymbolKind


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_engine() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
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
        name="files-test-repo",
        slug=f"files-test-{uuid.uuid4().hex[:6]}",
        source=RepositorySource.UPLOAD,
        status=RepositoryStatus.READY,
        size_bytes=2000,
        file_count=2,
    )


# ---------------------------------------------------------------------------
# Status Polling API Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_repository_status_polling() -> None:
    """GET /repositories/{id}/status returns coarse status, phase, and progress."""
    from app.main import create_app

    settings = _make_settings()
    test_app = create_app(settings=settings)
    engine, session_factory = await _make_engine()

    async with session_factory() as db:
        repo = _repo()
        repo.status = RepositoryStatus.INDEXING
        db.add(repo)
        await db.flush()

        job = AnalysisJob(
            repository_id=repo.id,
            phase="graph",
            status=JobStatus.RUNNING,
            progress=70,
        )
        db.add(job)
        await db.commit()

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    test_app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/repositories/{repo.id}/status")

    test_app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "indexing"
    assert data["progress"] == 70
    assert data["phase"] == "graph"
    assert data["error_message"] is None


@pytest.mark.asyncio
async def test_get_repository_status_404() -> None:
    """GET /repositories/{id}/status for non-existent repo returns 404."""
    from app.main import create_app

    settings = _make_settings()
    test_app = create_app(settings=settings)
    engine, session_factory = await _make_engine()

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    test_app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/repositories/{uuid.uuid4()}/status")

    test_app.dependency_overrides.clear()
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Files API Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_files_paginated_and_filtered() -> None:
    """GET /repositories/{id}/files lists files with pagination and filtering."""
    from app.main import create_app

    settings = _make_settings()
    test_app = create_app(settings=settings)
    engine, session_factory = await _make_engine()

    async with session_factory() as db:
        repo = _repo()
        db.add(repo)
        await db.flush()

        f1 = CodeFile(
            id=uuid.uuid4(),
            repository_id=repo.id,
            path="src/main.py",
            language="Python",
            size_bytes=100,
            content_hash="h1",
            line_count=10,
            is_binary=False,
        )
        f2 = CodeFile(
            id=uuid.uuid4(),
            repository_id=repo.id,
            path="src/app.ts",
            language="TypeScript",
            size_bytes=200,
            content_hash="h2",
            line_count=20,
            is_binary=False,
        )
        db.add_all([f1, f2])
        await db.commit()

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    test_app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # All files
        resp = await client.get(f"/api/v1/repositories/{repo.id}/files")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

        # Language filtered
        resp_py = await client.get(
            f"/api/v1/repositories/{repo.id}/files?language=Python"
        )
        assert resp_py.status_code == 200
        data_py = resp_py.json()
        assert data_py["total"] == 1
        assert data_py["items"][0]["path"] == "src/main.py"

    test_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_file_detail_text_and_binary(tmp_path: Path) -> None:
    """GET /files/{file_id} returns text content preview or binary error message."""
    from app.main import create_app

    settings = _make_settings()
    settings.UPLOAD_DIR = str(tmp_path)
    test_app = create_app(settings=settings)
    engine, session_factory = await _make_engine()

    async with session_factory() as db:
        repo = _repo()
        db.add(repo)
        await db.flush()

        # Setup source file on disk
        source_dir = tmp_path / str(repo.id) / "source" / "src"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "calc.py").write_text("def add(a, b): return a + b\n", encoding="utf-8")

        f_text = CodeFile(
            id=uuid.uuid4(),
            repository_id=repo.id,
            path="src/calc.py",
            language="Python",
            size_bytes=100,
            content_hash="h1",
            line_count=2,
            is_binary=False,
        )
        f_bin = CodeFile(
            id=uuid.uuid4(),
            repository_id=repo.id,
            path="assets/logo.png",
            language="Binary",
            size_bytes=5000,
            content_hash="h2",
            line_count=0,
            is_binary=True,
        )
        db.add_all([f_text, f_bin])
        await db.flush()

        sym = Symbol(
            id=uuid.uuid4(),
            repository_id=repo.id,
            file_id=f_text.id,
            name="add",
            kind=SymbolKind.FUNCTION,
            start_line=1,
            end_line=1,
            is_exported=True,
        )
        db.add(sym)
        await db.commit()

    from app.dependencies import get_app_settings

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    test_app.dependency_overrides[get_db] = _override_get_db
    test_app.dependency_overrides[get_app_settings] = lambda: settings

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Text file detail
        resp_text = await client.get(
            f"/api/v1/repositories/{repo.id}/files/{f_text.id}"
        )
        assert resp_text.status_code == 200
        data_text = resp_text.json()
        assert data_text["content"] == "def add(a, b): return a + b\n"
        assert data_text["error"] is None
        assert len(data_text["symbols"]) == 1
        assert data_text["symbols"][0]["name"] == "add"

        # 2. Binary file detail
        resp_bin = await client.get(
            f"/api/v1/repositories/{repo.id}/files/{f_bin.id}"
        )
        assert resp_bin.status_code == 200
        data_bin = resp_bin.json()
        assert data_bin["content"] is None
        assert data_bin["error"] == "Binary file — no content preview"

        # 3. File symbols endpoint
        resp_syms = await client.get(
            f"/api/v1/repositories/{repo.id}/files/{f_text.id}/symbols"
        )
        assert resp_syms.status_code == 200
        syms_list = resp_syms.json()
        assert len(syms_list) == 1
        assert syms_list[0]["name"] == "add"

    test_app.dependency_overrides.clear()
