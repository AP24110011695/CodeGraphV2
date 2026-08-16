"""FastAPI application factory and main entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import Settings, get_settings
from app.core.metrics import run_health_checks, setup_metrics
from app.core.rate_limiter import (
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
    limiter,
    rate_limit_exceeded_handler,
)
from app.exceptions import register_exception_handlers
from app.logging_config import get_logger, setup_logging
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.request_id import RequestIdMiddleware

logger = get_logger(__name__)


def run_migrations() -> None:
    """Run alembic migrations to head programmatically."""
    from alembic.config import Config

    from alembic import command

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan handler for startup/shutdown hooks."""
    from app.core.auth import bootstrap_admin_api_key
    from app.core.redis_client import close_redis, init_redis
    from app.db.session import AsyncSessionLocal

    settings = getattr(app.state, "settings", get_settings())
    if settings.is_development:
        try:
            run_migrations()
            logger.info("database_migrations_applied")
        except Exception as exc:
            logger.warning("database_migrations_failed_or_skipped", error=str(exc))

    async with AsyncSessionLocal() as db:
        api_key = await bootstrap_admin_api_key(db, settings)
        if api_key is not None:
            logger.info("bootstrap_api_key_created", key_id=str(api_key.id))

    # Initialize async Redis client pool
    app.state.redis = await init_redis(settings)
    logger.info("redis_client_initialized")

    yield

    # Shutdown
    await close_redis()
    app.state.redis = None
    logger.info("redis_client_closed")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional settings override (useful for testing).
            If None, loads from environment/.env file.

    Returns:
        Configured FastAPI application instance.
    """
    if settings is None:
        settings = get_settings()

    # The process-local fallback storage starts clean for each application
    # instance (including independent application-factory test instances).
    limiter.reset()

    # Configure logging
    setup_logging(
        log_level=settings.LOG_LEVEL,
        is_production=settings.is_production,
    )

    application = FastAPI(
        title="CodeGraph v2 API",
        description="AI-powered codebase intelligence platform backend API service.",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    application.state.settings = settings
    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    application.add_middleware(SlowAPIMiddleware)
    application.add_middleware(RequestSizeLimitMiddleware)
    application.add_middleware(SecurityHeadersMiddleware)

    # CORS middleware
    cors_origins: list[str] = (
        ["*"] if settings.is_development else settings.CORS_ORIGINS
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(RequestIdMiddleware)

    from app.api.v1 import api_v1_router

    # Register exception handlers
    register_exception_handlers(application)
    application.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # Mount API v1 router
    application.include_router(api_v1_router, prefix="/api/v1")
    setup_metrics(application)

    # Health endpoint
    @application.get("/health")
    async def health() -> dict[str, object]:
        """Report backend liveness plus database, Redis, and Celery readiness."""
        checks = await run_health_checks(application)
        return {"status": "ok", "version": "2.0.0", "checks": checks}

    return application


app = create_app()
