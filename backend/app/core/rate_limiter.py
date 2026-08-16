"""Per-client API rate limiting and HTTP security middleware."""

from __future__ import annotations

import hashlib

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from starlette.types import ASGIApp, Message, Receive, Scope, Send

MAX_REQUEST_BODY_BYTES = 600 * 1024 * 1024


def get_api_key_identifier(request: Request) -> str:
    """Use a non-reversible key digest, or client IP in anonymous local mode."""
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"key:{hashlib.sha256(api_key.encode()).hexdigest()}"
    host = request.client.host if request.client else "unknown"
    return f"ip:{host}"


limiter = Limiter(key_func=get_api_key_identifier, default_limits=["100/minute"])


def rate_limit_exceeded_handler(
    _request: Request, _exc: RateLimitExceeded
) -> Response:
    """Return the API contract's canonical 429 error body."""
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Rate limit exceeded",
                "details": {},
            }
        },
    )


class RequestSizeLimitMiddleware:
    """Reject declared and streamed HTTP request bodies larger than 600 MiB."""

    def __init__(self, app: ASGIApp, max_content_size: int = MAX_REQUEST_BODY_BYTES):
        self.app = app
        self.max_content_size = max_content_size

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        content_length = headers.get(b"content-length")
        if content_length is not None:
            try:
                if int(content_length) > self.max_content_size:
                    await self._send_too_large(scope, receive, send)
                    return
            except ValueError:
                await self._send_too_large(scope, receive, send)
                return

        received_bytes = 0

        async def limited_receive() -> Message:
            nonlocal received_bytes
            message = await receive()
            if message["type"] == "http.request":
                received_bytes += len(message.get("body", b""))
                if received_bytes > self.max_content_size:
                    raise _RequestBodyTooLargeError
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _RequestBodyTooLargeError:
            await self._send_too_large(scope, receive, send)

    async def _send_too_large(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        response = JSONResponse(
            status_code=413,
            content={
                "error": {
                    "code": "PAYLOAD_TOO_LARGE",
                    "message": "Request body exceeds the 600 MiB limit",
                    "details": {},
                }
            },
        )
        await response(scope, receive, send)


class _RequestBodyTooLargeError(Exception):
    """Internal signal raised when a chunked body crosses the configured limit."""


class SecurityHeadersMiddleware:
    """Append API-focused browser hardening headers to every HTTP response."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_security_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(
                    [
                        (b"x-content-type-options", b"nosniff"),
                        (b"x-frame-options", b"DENY"),
                        (
                            b"content-security-policy",
                            b"default-src 'none'; frame-ancestors 'none'; "
                            b"base-uri 'none'",
                        ),
                    ]
                )
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_security_headers)
