"""FastAPI application factory and main entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.exceptions import register_exception_handlers
from app.logging_config import get_logger, setup_logging

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
    settings = get_settings()
    if settings.is_development:
        try:
            run_migrations()
            logger.info("database_migrations_applied")
        except Exception as exc:
            logger.warning("database_migrations_failed_or_skipped", error=str(exc))
    yield

    # Shutdown


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

    # Configure logging
    setup_logging(
        log_level=settings.LOG_LEVEL,
        is_production=settings.is_production,
    )

    application = FastAPI(
        title="CodeGraph v2",
        description="AI-powered codebase intelligence platform",
        version="2.0.0",
        lifespan=lifespan,
    )

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

    from app.api.v1 import api_v1_router

    # Register exception handlers
    register_exception_handlers(application)

    # Mount API v1 router
    application.include_router(api_v1_router, prefix="/api/v1")

    # Health endpoint
    @application.get("/health")
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok", "version": "2.0.0"}

    return application



app = create_app()
