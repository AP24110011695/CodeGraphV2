"""Tests for Phase 20 database-backed API-key authentication."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import EnvironmentType, Settings
from app.core.auth import bootstrap_admin_api_key, hash_api_key
from app.db.base import Base
from app.dependencies import get_app_settings, get_db
from app.models.api_key import ApiKey


def _settings(tmp_path: Path, *, require_auth: bool) -> Settings:
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret",
        LLM_API_KEY="test-key",
        UPLOAD_DIR=str(tmp_path / "uploads"),
        ENVIRONMENT=EnvironmentType.PRODUCTION,
        REQUIRE_AUTH=require_auth,
    )


async def _app_with_database(tmp_path: Path, *, require_auth: bool):
    from app.main import create_app

    settings = _settings(tmp_path, require_auth=require_auth)
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app = create_app(settings=settings)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_app_settings] = lambda: settings
    return app, engine, session_factory


def _zip_payload() -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("repo/main.py", "def main(): pass\n")
    return stream.getvalue()


@pytest.mark.asyncio
async def test_auth_disabled_leaves_mutating_request_open(tmp_path: Path) -> None:
    """Default local mode accepts a repository upload without a key."""
    app, engine, _session_factory = await _app_with_database(
        tmp_path, require_auth=False
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/repositories",
            files={"file": ("repo.zip", _zip_payload(), "application/zip")},
        )

    app.dependency_overrides.clear()
    await engine.dispose()
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_auth_enabled_rejects_missing_and_invalid_keys(tmp_path: Path) -> None:
    """Enforced mode returns canonical 401 responses for missing/invalid keys."""
    app, engine, _session_factory = await _app_with_database(
        tmp_path, require_auth=True
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        missing = await client.post(
            "/api/v1/repositories",
            files={"file": ("repo.zip", _zip_payload(), "application/zip")},
        )
        invalid = await client.post(
            "/api/v1/repositories",
            headers={"X-API-Key": "not-a-real-key"},
            files={"file": ("repo.zip", _zip_payload(), "application/zip")},
        )

    app.dependency_overrides.clear()
    await engine.dispose()
    for response in (missing, invalid):
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "AUTH_REQUIRED"


@pytest.mark.asyncio
async def test_read_auth_is_optional_unless_explicitly_enabled(tmp_path: Path) -> None:
    """GET requests remain public by default in enforced hosted mode."""
    app, engine, _session_factory = await _app_with_database(
        tmp_path, require_auth=True
    )
    settings = app.dependency_overrides[get_app_settings]()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        public_response = await client.get("/api/v1/repositories")
        settings.REQUIRE_AUTH_FOR_READS = True
        protected_response = await client.get("/api/v1/repositories")

    app.dependency_overrides.clear()
    await engine.dispose()
    assert public_response.status_code == 200
    assert protected_response.status_code == 401


@pytest.mark.asyncio
async def test_auth_enabled_accepts_valid_key_and_updates_last_used(
    tmp_path: Path,
) -> None:
    """A stored hash authenticates the request without retaining plaintext."""
    plaintext_key = "test-valid-key"
    app, engine, session_factory = await _app_with_database(tmp_path, require_auth=True)
    async with session_factory() as db:
        db.add(ApiKey(key_hash=hash_api_key(plaintext_key), label="test"))
        await db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/repositories",
            headers={"X-API-Key": plaintext_key},
            files={"file": ("repo.zip", _zip_payload(), "application/zip")},
        )

    async with session_factory() as db:
        api_key = (await db.execute(select(ApiKey))).scalar_one()
        assert api_key.last_used_at is not None
        assert api_key.key_hash != plaintext_key

    app.dependency_overrides.clear()
    await engine.dispose()
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_bootstrap_key_is_created_once(tmp_path: Path) -> None:
    """ADMIN_API_KEY creates a hashed bootstrap key only for an empty key store."""
    settings = _settings(tmp_path, require_auth=True).model_copy(
        update={"ADMIN_API_KEY": "bootstrap-secret"}
    )
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        created = await bootstrap_admin_api_key(db, settings)
        skipped = await bootstrap_admin_api_key(db, settings)
        keys = list((await db.execute(select(ApiKey))).scalars())

    await engine.dispose()
    assert created is not None
    assert skipped is None
    assert len(keys) == 1
    assert keys[0].key_hash == hash_api_key("bootstrap-secret")
