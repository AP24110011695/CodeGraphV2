"""Tests for Phase 21 rate limits and HTTP security hardening."""

from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.v1.files import get_file_detail
from app.config import EnvironmentType, Settings
from app.core.rate_limiter import MAX_REQUEST_BODY_BYTES, limiter
from app.db.base import Base
from app.models.code_file import CodeFile
from app.models.repository import Repository, RepositorySource, RepositoryStatus


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret",
        LLM_API_KEY="test-key",
        UPLOAD_DIR=str(tmp_path / "uploads"),
        ENVIRONMENT=EnvironmentType.PRODUCTION,
    )


@pytest.mark.asyncio
async def test_general_rate_limit_and_security_headers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The 101st general request is rejected with canonical 429 and headers."""
    from app.main import create_app

    limiter.reset()
    monkeypatch.setattr(
        "app.main.run_health_checks",
        AsyncMock(return_value={"database": "ok", "redis": "ok", "celery": "ok"}),
    )
    app = create_app(settings=_settings(tmp_path))
    transport = ASGITransport(app=app, client=("198.51.100.1", 1234))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        responses = [await client.get("/health") for _ in range(101)]

    first = responses[0]
    limited = responses[-1]
    assert first.status_code == 200
    assert first.headers["x-content-type-options"] == "nosniff"
    assert first.headers["x-frame-options"] == "DENY"
    assert "default-src 'none'" in first.headers["content-security-policy"]
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_request_body_limit_is_enforced(tmp_path: Path) -> None:
    """A declared body larger than 600 MiB is rejected before route handling."""
    from app.main import create_app

    limiter.reset()
    app = create_app(settings=_settings(tmp_path))
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/health",
            content=b"",
            headers={"Content-Length": str(MAX_REQUEST_BODY_BYTES + 1)},
        )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


@pytest.mark.asyncio
async def test_file_detail_rejects_path_outside_source_root(tmp_path: Path) -> None:
    """Stored traversal paths cannot escape a repository's source directory."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    settings = _settings(tmp_path)

    async with session_factory() as db:
        repo = Repository(
            id=uuid.uuid4(),
            name="security-test",
            slug="security-test",
            source=RepositorySource.UPLOAD,
            status=RepositoryStatus.READY,
            size_bytes=1,
            file_count=1,
        )
        code_file = CodeFile(
            id=uuid.uuid4(),
            repository_id=repo.id,
            path="../outside.py",
            content_hash="0" * 64,
            size_bytes=1,
            line_count=1,
            is_binary=False,
        )
        db.add_all([repo, code_file])
        await db.commit()

        with pytest.raises(HTTPException) as exc_info:
            await get_file_detail(repo.id, code_file.id, db, settings)

    await engine.dispose()
    assert exc_info.value.status_code == 400
