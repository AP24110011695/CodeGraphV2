"""Authentication foundation stub.

This module provides a FastAPI dependency that reads the optional X-API-Key
header from requests. In the default local/self-hosted developer mode
(REQUIRE_AUTH=false), it never rejects a request.

Phase 20 replaces the body of get_current_key_optional() with real
DB-backed API key enforcement without changing its name or signature,
so no endpoint wiring changes are needed later.
"""

from fastapi import Header


async def get_current_key_optional(
    x_api_key: str | None = Header(default=None),
) -> str | None:
    """Extract the X-API-Key header if present, without rejecting requests.

    This stub always returns the key value (or None). It does not validate
    or enforce authentication — that behavior is added in Phase 20 when
    REQUIRE_AUTH is set to true.

    Args:
        x_api_key: The optional X-API-Key header value.

    Returns:
        The API key string if provided, or None.
    """
    return x_api_key
