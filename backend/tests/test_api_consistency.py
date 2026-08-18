"""Tests for Phase 17 — API Contract Consistency Audit & OpenAPI Docs.

Audits:
- Canonical error response shape across endpoints (404, 422, 400).
- Canonical paginated list response shape across list endpoints.
- OpenAPI schema documentation generation at /openapi.json, /docs, /redoc.
"""

from __future__ import annotations

import uuid

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
from app.models.repository import Repository, RepositorySource, RepositoryStatus

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


# ---------------------------------------------------------------------------
# OpenAPI & Docs Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_openapi_docs_endpoints() -> None:
    """OpenAPI schema and HTML docs endpoints are accessible and populated."""
    from app.main import create_app

    app = create_app(_make_settings())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # /openapi.json
        resp_spec = await client.get("/openapi.json")
        assert resp_spec.status_code == 200
        spec = resp_spec.json()
        assert spec["info"]["title"] == "CodeGraph v2 API"
        assert spec["info"]["version"] == "2.0.0"
        assert "/api/v1/repositories" in spec["paths"]
        assert "/api/v1/repositories/{repo_id}/files" in spec["paths"]
        assert "/health" in spec["paths"]

        # /docs
        resp_docs = await client.get("/docs")
        assert resp_docs.status_code == 200
        assert "swagger" in resp_docs.text.lower() or "html" in resp_docs.text.lower()

        # /redoc
        resp_redoc = await client.get("/redoc")
        assert resp_redoc.status_code == 200
        assert "redoc" in resp_redoc.text.lower() or "html" in resp_redoc.text.lower()


# ---------------------------------------------------------------------------
# Canonical Error Response Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_canonical_error_format_on_404() -> None:
    """404 errors adhere strictly to the canonical error object shape."""
    from app.main import create_app

    settings = _make_settings()
    test_app = create_app(settings=settings)
    engine, session_factory = await _make_engine()

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    test_app.dependency_overrides[get_db] = _override_get_db
    fake_id = uuid.uuid4()

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        endpoints_404 = [
            f"/api/v1/repositories/{fake_id}",
            f"/api/v1/repositories/{fake_id}/status",
            f"/api/v1/repositories/{fake_id}/files",
            f"/api/v1/repositories/{fake_id}/files/{uuid.uuid4()}",
            f"/api/v1/repositories/{fake_id}/graph",
        ]

        for url in endpoints_404:
            resp = await client.get(url)
            assert resp.status_code == 404, f"Expected 404 for {url}"
            data = resp.json()
            assert "error" in data, f"Missing 'error' wrapper in {url}"
            err = data["error"]
            assert "code" in err
            assert "message" in err
            assert "details" in err
            assert err["code"] in ("NOT_FOUND", "REPOSITORY_NOT_FOUND")

    test_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_canonical_error_format_on_422_validation() -> None:
    """422 validation errors adhere strictly to canonical error format."""
    from app.main import create_app

    settings = _make_settings()
    test_app = create_app(settings=settings)

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid query parameter type page=-5 or invalid page_size
        resp = await client.get("/api/v1/repositories?page=invalid")
        assert resp.status_code == 422
        data = resp.json()
        assert "error" in data
        err = data["error"]
        assert err["code"] == "VALIDATION_ERROR"
        assert "errors" in err["details"]


# ---------------------------------------------------------------------------
# Canonical Paginated List Response Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_canonical_paginated_list_format() -> None:
    """List endpoints use {"items": [...], "total": N, "page": 1, "page_size": 20}."""
    from app.main import create_app

    settings = _make_settings()
    test_app = create_app(settings=settings)
    engine, session_factory = await _make_engine()

    async with session_factory() as db:
        repo = Repository(
            id=uuid.uuid4(),
            name="test-repo-consistency",
            slug=f"slug-{uuid.uuid4().hex[:6]}",
            source=RepositorySource.UPLOAD,
            status=RepositoryStatus.READY,
            size_bytes=100,
            file_count=0,
        )
        db.add(repo)
        await db.commit()

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    test_app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Repositories list
        resp_repos = await client.get("/api/v1/repositories?page=1&page_size=10")
        assert resp_repos.status_code == 200
        data_repos = resp_repos.json()
        assert "items" in data_repos
        assert "total" in data_repos
        assert data_repos["page"] == 1
        assert data_repos["page_size"] == 10

        # Files list
        resp_files = await client.get(
            f"/api/v1/repositories/{repo.id}/files?page=1&page_size=5"
        )
        assert resp_files.status_code == 200
        data_files = resp_files.json()
        assert "items" in data_files
        assert "total" in data_files
        assert data_files["page"] == 1
        assert data_files["page_size"] == 5

    test_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Health Endpoint Test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_check_endpoint() -> None:
    """GET /health returns status ok."""
    from app.main import create_app

    app = create_app(_make_settings())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["status"] == "ok"
        assert payload["version"] == "2.0.0"
        assert set(payload["checks"]) == {"database", "redis", "celery"}
