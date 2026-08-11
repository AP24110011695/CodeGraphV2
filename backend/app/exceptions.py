"""Custom exception classes and FastAPI exception handlers.

All exceptions produce responses matching the canonical error format:
    {"error": {"code": "CODE", "message": "Message", "details": {}}}
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.logging_config import get_logger

logger = get_logger(__name__)





class AppException(Exception):  # noqa: N818
    """Base exception for application-specific errors."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(AppException):
    """Resource not found (404)."""

    def __init__(
        self,
        message: str = "Resource not found",
        code: str = "NOT_FOUND",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=code, message=message, status_code=404, details=details
        )


class ValidationError(AppException):
    """Validation error (400)."""

    def __init__(
        self,
        message: str = "Validation error",
        code: str = "VALIDATION_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=code, message=message, status_code=400, details=details
        )


class AuthenticationError(AppException):
    """Authentication required or invalid (401)."""

    def __init__(
        self,
        message: str = "Authentication required",
        code: str = "AUTH_REQUIRED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=code, message=message, status_code=401, details=details
        )


class ForbiddenError(AppException):
    """Forbidden (403)."""

    def __init__(
        self,
        message: str = "Forbidden",
        code: str = "FORBIDDEN",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=code, message=message, status_code=403, details=details
        )


class TooLargeError(AppException):
    """Payload too large (413)."""

    def __init__(
        self,
        message: str = "Payload too large",
        code: str = "TOO_LARGE",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=code, message=message, status_code=413, details=details
        )


class RateLimitError(AppException):
    """Rate limit exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        code: str = "RATE_LIMIT_EXCEEDED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=code, message=message, status_code=429, details=details
        )


def _error_response(
    status_code: int, code: str, message: str, details: dict[str, Any] | None = None
) -> JSONResponse:
    """Build a canonical error JSON response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
    )


async def app_exception_handler(
    _request: Request, exc: AppException
) -> JSONResponse:
    """Handle application-specific exceptions."""
    logger.warning(
        "app_exception",
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
    )
    return _error_response(exc.status_code, exc.code, exc.message, exc.details)


async def http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle HTTP exceptions (FastAPI & Starlette) in canonical error format."""
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
    return _error_response(exc.status_code, code, detail)


async def unhandled_exception_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions, returning a generic 500 error."""
    logger.error("unhandled_exception", error=str(exc), exc_info=True)
    return _error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)



