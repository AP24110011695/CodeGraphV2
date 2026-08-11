"""Tests for the /health endpoint and settings loading."""

from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.main import create_app


async def test_health_returns_ok() -> None:
    """GET /health should return 200 with status ok and version."""
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://localhost/test",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret",
        LLM_API_KEY="test-key",
    )
    test_app = create_app(settings=settings)
    transport = ASGITransport(app=test_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "2.0.0"


async def test_settings_loads_defaults() -> None:
    """Settings should load with sensible defaults."""
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://localhost/test",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret",
        LLM_API_KEY="test-key",
    )
    assert settings.REQUIRE_AUTH is False
    assert settings.REQUIRE_AUTH_FOR_READS is False
    assert settings.MAX_REPO_SIZE_MB == 500
    assert settings.EMBEDDING_DIM == 1536
    assert settings.ENVIRONMENT.value == "development"
    assert settings.is_development is True
    assert settings.is_production is False


async def test_cors_origins_parsing() -> None:
    """CORS_ORIGINS should parse comma-separated strings."""
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://localhost/test",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret",
        LLM_API_KEY="test-key",
        CORS_ORIGINS="http://localhost:3000,http://localhost:5173",  # type: ignore[arg-type]
    )
    assert settings.CORS_ORIGINS == [
        "http://localhost:3000",
        "http://localhost:5173",
    ]


async def test_health_with_api_key_header() -> None:
    """GET /health with X-API-Key header should still succeed (REQUIRE_AUTH=false)."""
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://localhost/test",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret",
        LLM_API_KEY="test-key",
        REQUIRE_AUTH=False,
    )
    test_app = create_app(settings=settings)
    transport = ASGITransport(app=test_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/health", headers={"X-API-Key": "some-key"}
        )

    assert response.status_code == 200


async def test_error_format_on_404() -> None:
    """Non-existent endpoints should return the canonical error format."""
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://localhost/test",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret",
        LLM_API_KEY="test-key",
    )
    test_app = create_app(settings=settings)
    transport = ASGITransport(app=test_app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/nonexistent")

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
