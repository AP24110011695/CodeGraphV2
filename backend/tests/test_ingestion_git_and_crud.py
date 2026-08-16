"""Tests for git clone ingestion and repository CRUD endpoints."""

import io
import subprocess
import uuid
import zipfile
from collections.abc import AsyncGenerator
from pathlib import Path
from types import CoroutineType
from unittest.mock import AsyncMock, MagicMock, patch

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

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


async def _create_test_engine_and_session(
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Create an in-memory SQLite engine and session factory for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    return engine, session_factory


def _make_settings(tmp_path: Path, **overrides: object) -> Settings:
    base: dict[str, object] = {
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/0",
        "SECRET_KEY": "test-secret",
        "LLM_API_KEY": "test-key",
        "UPLOAD_DIR": str(tmp_path / "uploads"),
        "MAX_REPO_SIZE_MB": 500,
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


async def _make_app(
    tmp_path: Path,
    session_factory: async_sessionmaker[AsyncSession],
    **setting_overrides: object,
) -> tuple[object, Settings]:
    settings = _make_settings(tmp_path, **setting_overrides)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app = create_app(settings=settings)
    app.dependency_overrides[get_db] = override_get_db  # type: ignore[attr-defined]
    app.dependency_overrides[get_app_settings] = lambda: settings  # type: ignore[attr-defined]
    return app, settings


def _create_sample_zip() -> bytes:
    """Return a minimal sample zip with two files."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("sample-repo/main.py", "def main(): pass\n")
        zf.writestr("sample-repo/utils.py", "def add(a, b): return a + b\n")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Git clone tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clone_repository_success(tmp_path: Path) -> None:
    """Test successful git clone using a local bare repo as the remote."""
    # Create a local bare git repo to clone (no network needed)
    bare_repo = tmp_path / "bare.git"
    bare_repo.mkdir()
    subprocess.run(
        ["git", "init", "--bare", str(bare_repo)],
        check=True, capture_output=True,
    )

    # Create a working repo, commit a file, push to bare
    work_repo = tmp_path / "work"
    work_repo.mkdir()
    subprocess.run(["git", "init", str(work_repo)], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=str(work_repo), check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=str(work_repo), check=True, capture_output=True,
    )
    (work_repo / "README.md").write_text("hello")
    subprocess.run(
        ["git", "add", "."], cwd=str(work_repo), check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=str(work_repo), check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "remote", "add", "origin", str(bare_repo)],
        cwd=str(work_repo), check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "push", "origin", "HEAD"],
        cwd=str(work_repo), check=True, capture_output=True,
    )

    engine, session_factory = await _create_test_engine_and_session()
    app, settings = await _make_app(tmp_path, session_factory)

    # Patch _validate_git_url to accept file:// URL for this local test
    with patch(
        "app.services.ingestion._validate_git_url",
        side_effect=lambda url: url,
    ):
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/repositories/clone",
                json={"git_url": bare_repo.as_uri()},
            )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "id" in data
    assert data["status"] == "ingesting"
    assert data["source"] == "git_clone"

    await engine.dispose()


@pytest.mark.asyncio
async def test_clone_repository_rejects_file_url(tmp_path: Path) -> None:
    """Test that file:// git URLs are rejected with 400."""
    engine, session_factory = await _create_test_engine_and_session()
    app, _ = await _make_app(tmp_path, session_factory)

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/repositories/clone",
            json={"git_url": "file:///etc/passwd"},
        )

    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_GIT_URL"

    await engine.dispose()


@pytest.mark.asyncio
async def test_clone_repository_rejects_git_scheme(tmp_path: Path) -> None:
    """Test that git:// URLs are rejected with 400."""
    engine, session_factory = await _create_test_engine_and_session()
    app, _ = await _make_app(tmp_path, session_factory)

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/repositories/clone",
            json={"git_url": "git://github.com/owner/repo.git"},
        )

    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "INVALID_GIT_URL"

    await engine.dispose()


@pytest.mark.asyncio
async def test_clone_repository_timeout(tmp_path: Path) -> None:
    """Test that a git clone timeout results in a 400 VALIDATION_ERROR."""
    engine, session_factory = await _create_test_engine_and_session()
    app, _ = await _make_app(tmp_path, session_factory)

    # Mock asyncio.create_subprocess_exec to simulate a timeout
    mock_proc = MagicMock()
    mock_proc.kill = MagicMock()
    # communicate() is called a second time after kill() — must succeed
    mock_proc.communicate = AsyncMock(return_value=(b"", b""))


    async def _fake_wait_for(coro: object, timeout: float) -> None:
        if isinstance(coro, CoroutineType):
            coro.close()
        raise TimeoutError()

    with (
        patch(
            "app.services.ingestion._validate_git_url",
            side_effect=lambda url: url,
        ),
        patch(
            "app.services.ingestion.asyncio.create_subprocess_exec",
            new_callable=AsyncMock,
            return_value=mock_proc,
        ),
        patch(
            "app.services.ingestion.asyncio.wait_for",
            side_effect=_fake_wait_for,
        ),
    ):
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/repositories/clone",
                json={"git_url": "https://github.com/slow/repo.git"},
            )

    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "GIT_CLONE_TIMEOUT"

    await engine.dispose()


# ---------------------------------------------------------------------------
# CRUD tests
# ---------------------------------------------------------------------------


async def _seed_repo(
    client: AsyncClient, zip_bytes: bytes | None = None
) -> dict[str, object]:
    """Upload a ZIP and return the created repo JSON."""
    payload = zip_bytes or _create_sample_zip()
    resp = await client.post(
        "/api/v1/repositories",
        files={"file": ("repo.zip", payload, "application/zip")},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()  # type: ignore[return-value]


@pytest.mark.asyncio
async def test_list_repositories_returns_created(tmp_path: Path) -> None:
    """Test GET /repositories returns repos created via upload."""
    engine, session_factory = await _create_test_engine_and_session()
    app, _ = await _make_app(tmp_path, session_factory)

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        repo = await _seed_repo(client)
        repo_id = repo["id"]

        resp = await client.get("/api/v1/repositories")

    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    ids = [item["id"] for item in data["items"]]
    assert repo_id in ids

    await engine.dispose()


@pytest.mark.asyncio
async def test_list_repositories_pagination(tmp_path: Path) -> None:
    """Test that page/page_size parameters work correctly."""
    engine, session_factory = await _create_test_engine_and_session()
    app, _ = await _make_app(tmp_path, session_factory)

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Seed 3 repos
        for _ in range(3):
            await _seed_repo(client)

        resp_p1 = await client.get("/api/v1/repositories?page=1&page_size=2")
        resp_p2 = await client.get("/api/v1/repositories?page=2&page_size=2")

    assert resp_p1.status_code == 200
    d1 = resp_p1.json()
    assert len(d1["items"]) == 2
    assert d1["total"] == 3
    assert d1["page"] == 1
    assert d1["page_size"] == 2

    assert resp_p2.status_code == 200
    d2 = resp_p2.json()
    assert len(d2["items"]) == 1
    assert d2["page"] == 2

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_repository_detail(tmp_path: Path) -> None:
    """Test GET /repositories/{id} returns correct detail."""
    engine, session_factory = await _create_test_engine_and_session()
    app, _ = await _make_app(tmp_path, session_factory)

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        repo = await _seed_repo(client)
        repo_id = repo["id"]

        resp = await client.get(f"/api/v1/repositories/{repo_id}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == repo_id
    assert data["name"] == repo["name"]
    assert "slug" in data
    assert "status" in data

    await engine.dispose()


@pytest.mark.asyncio
async def test_get_repository_not_found(tmp_path: Path) -> None:
    """Test GET /repositories/{id} returns 404 for unknown ID."""
    engine, session_factory = await _create_test_engine_and_session()
    app, _ = await _make_app(tmp_path, session_factory)

    missing_id = uuid.uuid4()
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(f"/api/v1/repositories/{missing_id}")

    assert resp.status_code == 404
    data = resp.json()
    assert data["error"]["code"] == "REPOSITORY_NOT_FOUND"

    await engine.dispose()


@pytest.mark.asyncio
async def test_delete_repository(tmp_path: Path) -> None:
    """Test DELETE /repositories/{id} removes the record; subsequent GET returns 404."""
    engine, session_factory = await _create_test_engine_and_session()
    app, _ = await _make_app(tmp_path, session_factory)

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        repo = await _seed_repo(client)
        repo_id = repo["id"]

        del_resp = await client.delete(f"/api/v1/repositories/{repo_id}")
        assert del_resp.status_code == 200
        assert "deleted" in del_resp.json()["message"].lower()

        get_resp = await client.get(f"/api/v1/repositories/{repo_id}")
        assert get_resp.status_code == 404

    await engine.dispose()


@pytest.mark.asyncio
async def test_delete_repository_not_found(tmp_path: Path) -> None:
    """Test DELETE /repositories/{id} returns 404 for unknown ID."""
    engine, session_factory = await _create_test_engine_and_session()
    app, _ = await _make_app(tmp_path, session_factory)

    missing_id = uuid.uuid4()
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.delete(f"/api/v1/repositories/{missing_id}")

    assert resp.status_code == 404

    await engine.dispose()
