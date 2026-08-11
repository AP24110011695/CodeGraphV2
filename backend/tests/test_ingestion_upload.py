"""Tests for repository ZIP upload ingestion and validation."""

import io
import zipfile
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings
from app.db.base import Base
from app.dependencies import get_app_settings, get_db
from app.main import create_app


def _create_sample_zip() -> bytes:
    """Generate a valid sample ZIP archive in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("sample-repo/main.py", "def main():\n    print('Hello World')\n")
        zf.writestr("sample-repo/utils.py", "def add(a, b):\n    return a + b\n")
    return buf.getvalue()


def _create_traversal_zip() -> bytes:
    """Generate a ZIP archive containing path traversal filenames."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../malicious.txt", "hacked")
        zf.writestr("sample/ok.py", "print('ok')")
    return buf.getvalue()


async def _create_test_engine_and_session() -> tuple[
    AsyncEngine, async_sessionmaker[AsyncSession]
]:
    """Initialize an in-memory SQLite engine and session factory for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    return engine, session_factory


@pytest.mark.asyncio
async def test_upload_repository_zip_success(tmp_path: Path) -> None:
    """Test successful ZIP upload and repository ingestion."""
    engine, session_factory = await _create_test_engine_and_session()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret",
        LLM_API_KEY="test-key",
        UPLOAD_DIR=str(tmp_path / "uploads"),
        MAX_REPO_SIZE_MB=500,
    )
    test_app = create_app(settings=settings)
    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_app_settings] = lambda: settings

    zip_bytes = _create_sample_zip()
    transport = ASGITransport(app=test_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/repositories",
            files={"file": ("sample_repo.zip", zip_bytes, "application/zip")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["name"] == "sample-repo"
    assert data["status"] in ("ingesting", "pending")
    assert data["file_count"] == 2

    # Check disk extraction
    repo_id = data["id"]
    extracted_source = tmp_path / "uploads" / repo_id / "source"
    assert extracted_source.exists()
    assert (extracted_source / "sample-repo" / "main.py").exists()

    await engine.dispose()


@pytest.mark.asyncio
async def test_upload_repository_zip_path_traversal(tmp_path: Path) -> None:
    """Test path traversal ZIP upload rejection with 400."""
    engine, session_factory = await _create_test_engine_and_session()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret",
        LLM_API_KEY="test-key",
        UPLOAD_DIR=str(tmp_path / "uploads"),
    )
    test_app = create_app(settings=settings)
    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_app_settings] = lambda: settings

    zip_bytes = _create_traversal_zip()
    transport = ASGITransport(app=test_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/repositories",
            files={"file": ("malicious.zip", zip_bytes, "application/zip")},
        )

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "PATH_TRAVERSAL_DETECTED"

    await engine.dispose()


@pytest.mark.asyncio
async def test_upload_repository_zip_exceeds_size_limit(tmp_path: Path) -> None:
    """Test oversized ZIP upload rejection with 413."""
    engine, session_factory = await _create_test_engine_and_session()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    settings = Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret",
        LLM_API_KEY="test-key",
        UPLOAD_DIR=str(tmp_path / "uploads"),
        MAX_REPO_SIZE_MB=1,  # Set 1MB limit for testing
    )
    test_app = create_app(settings=settings)
    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_app_settings] = lambda: settings

    # Create dummy data > 1MB
    large_data = b"0" * (1 * 1024 * 1024 + 1024)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("large.txt", large_data)
    large_zip_bytes = buf.getvalue()

    transport = ASGITransport(app=test_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/repositories",
            files={"file": ("large.zip", large_zip_bytes, "application/zip")},
        )

    assert response.status_code == 413
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "PAYLOAD_TOO_LARGE"

    await engine.dispose()
