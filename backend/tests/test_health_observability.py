"""Focused tests for Phase 22 health, metrics, and request tracing."""

import uuid
from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.main import create_app


def _settings() -> Settings:
    return Settings(
        DATABASE_URL="postgresql+asyncpg://localhost/test",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret",
        LLM_API_KEY="test-key",
    )


async def test_health_reports_dependency_checks_and_request_id(
    monkeypatch,
) -> None:
    """Health remains additive and returns a UUID request correlation header."""
    checks = {"database": "ok", "redis": "ok", "celery": "ok"}
    health_checks = AsyncMock(return_value=checks)
    monkeypatch.setattr("app.main.run_health_checks", health_checks)
    app = create_app(settings=_settings())

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": "2.0.0",
        "checks": checks,
    }
    uuid.UUID(response.headers["X-Request-ID"])
    health_checks.assert_awaited_once_with(app)


async def test_metrics_exposes_custom_codegraph_metrics() -> None:
    """Prometheus endpoint exposes the four CodeGraph-specific metric families."""
    app = create_app(settings=_settings())

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    for metric in (
        "codegraph_repositories_total",
        "codegraph_analysis_duration_seconds",
        "codegraph_llm_tokens_total",
        "codegraph_chunks_indexed_total",
    ):
        assert metric in response.text
    uuid.UUID(response.headers["X-Request-ID"])
