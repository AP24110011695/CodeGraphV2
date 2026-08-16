"""Prometheus metrics and dependency probes for CodeGraph."""

from __future__ import annotations

import asyncio
from typing import Literal

from fastapi import FastAPI
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from app.logging_config import get_logger

logger = get_logger(__name__)

REPOSITORIES_TOTAL = Counter(
    "codegraph_repositories_total",
    "Repositories observed by lifecycle status.",
    ["status"],
)
ANALYSIS_DURATION_SECONDS = Histogram(
    "codegraph_analysis_duration_seconds",
    "Duration of repository analysis pipeline stages.",
    ["phase"],
)
LLM_TOKENS_TOTAL = Counter(
    "codegraph_llm_tokens_total",
    "LLM tokens consumed by provider and token type.",
    ["provider", "type"],
)
CHUNKS_INDEXED_TOTAL = Counter(
    "codegraph_chunks_indexed_total",
    "Code chunks indexed by the backend.",
)


def setup_metrics(app: FastAPI) -> None:
    """Attach automatic HTTP instrumentation and expose Prometheus metrics."""
    for status in ("pending", "ingesting", "parsing", "indexing", "ready", "error"):
        REPOSITORIES_TOTAL.labels(status=status).inc(0)
    for phase in ("ingestion", "extraction", "parsing", "graph", "indexing"):
        ANALYSIS_DURATION_SECONDS.labels(phase=phase).observe(0)
    LLM_TOKENS_TOTAL.labels(provider="unknown", type="prompt").inc(0)
    LLM_TOKENS_TOTAL.labels(provider="unknown", type="completion").inc(0)
    CHUNKS_INDEXED_TOTAL.inc(0)
    Instrumentator().instrument(app).expose(app, include_in_schema=False)


async def probe_database() -> Literal["ok", "error"]:
    """Run a lightweight SQL query against the configured database."""
    from app.db.session import engine

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("health_database_failed", error=str(exc))
        return "error"
    return "ok"


async def probe_redis(app: FastAPI) -> Literal["ok", "error"]:
    """Ping the application Redis client initialized during lifespan."""
    try:
        redis_client = app.state.redis
        await redis_client.ping()
    except Exception as exc:
        logger.warning("health_redis_failed", error=str(exc))
        return "error"
    return "ok"


async def probe_celery() -> Literal["ok", "error"]:
    """Ask at least one Celery worker to respond to an inspect ping."""
    from app.workers.celery_app import celery_app

    try:
        inspector = celery_app.control.inspect(timeout=1.0)
        responses = await asyncio.to_thread(inspector.ping)
        if not responses:
            return "error"
    except Exception as exc:
        logger.warning("health_celery_failed", error=str(exc))
        return "error"
    return "ok"


async def run_health_checks(app: FastAPI) -> dict[str, Literal["ok", "error"]]:
    """Run independent infrastructure probes with bounded execution time."""
    checks = await asyncio.gather(
        asyncio.wait_for(probe_database(), timeout=1.0),
        asyncio.wait_for(probe_redis(app), timeout=1.0),
        asyncio.wait_for(probe_celery(), timeout=1.0),
        return_exceptions=True,
    )
    return {
        name: "ok" if result == "ok" else "error"
        for name, result in zip(("database", "redis", "celery"), checks, strict=True)
    }
