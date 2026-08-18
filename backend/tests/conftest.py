"""Shared fixtures for fast unit tests and optional PostgreSQL integration tests."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.config import EnvironmentType, Settings
from app.db.base import Base
from app.main import create_app


@pytest.fixture
def test_settings(tmp_path) -> Settings:
    """Return isolated settings suitable for API tests without a lifespan."""
    return Settings(
        DATABASE_URL="postgresql+asyncpg://localhost/codegraph_test",
        REDIS_URL="redis://localhost:6379/15",
        SECRET_KEY="test-secret",
        LLM_API_KEY="test-key",
        UPLOAD_DIR=str(tmp_path),
        ENVIRONMENT=EnvironmentType.PRODUCTION,
    )


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Redis client mock with successful ping and no-op close operations."""
    redis = AsyncMock()
    redis.ping.return_value = True
    return redis


@pytest.fixture
def mock_llm_provider() -> MagicMock:
    """LLM provider mock with deterministic token accounting."""
    provider = MagicMock()
    provider.model_name = "test-model"
    provider.max_context_tokens = 1_000
    provider.count_tokens.side_effect = lambda value: max(1, len(value) // 4)
    return provider


@pytest_asyncio.fixture
async def async_client(test_settings: Settings) -> AsyncIterator[AsyncClient]:
    """ASGI client for endpoint tests that do not require startup services."""
    application = create_app(settings=test_settings)
    async with AsyncClient(
        transport=ASGITransport(app=application), base_url="http://test"
    ) as client:
        yield client


@pytest_asyncio.fixture
async def integration_engine() -> AsyncIterator[AsyncEngine]:
    """Fresh PostgreSQL schema for integration tests.

    The explicit environment variable prevents unit tests from silently using
    SQLite where pgvector behavior would differ from production.
    """
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")
    if not database_url.startswith("postgresql+"):
        pytest.fail("TEST_DATABASE_URL must use a PostgreSQL async SQLAlchemy URL")

    engine = create_async_engine(database_url, echo=False)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)
        yield engine
    finally:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(integration_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Transaction-scoped database session backed by the PostgreSQL test schema."""
    async with AsyncSession(integration_engine, expire_on_commit=False) as session:
        yield session
        await session.rollback()
