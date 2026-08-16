"""Structured request lifecycle logging middleware."""

from __future__ import annotations

from time import perf_counter

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.logging_config import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request start and completion without logging request content."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        started_at = perf_counter()
        logger.info("request_started", method=request.method, path=request.url.path)
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request_failed",
                method=request.method,
                path=request.url.path,
                duration_seconds=round(perf_counter() - started_at, 6),
            )
            raise
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_seconds=round(perf_counter() - started_at, 6),
        )
        return response
