"""Async Redis client factory for the application.

Provides a shared async Redis client instance for pub/sub, caching, and
Celery broker interactions. Exposes ``get_redis_client`` for dependency
injection and ``redis_client`` singleton for lifespan management.
"""

from __future__ import annotations

import redis.asyncio as aioredis

from app.config import Settings, get_settings

# Module-level singleton — created once during lifespan startup.
_redis_client: aioredis.Redis | None = None


async def init_redis(settings: Settings | None = None) -> aioredis.Redis:
    """Initialise the async Redis connection pool and return the client.

    Safe to call multiple times; subsequent calls return the existing client.
    """
    global _redis_client
    if _redis_client is None:
        settings = settings or get_settings()
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection pool gracefully."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


def get_redis_client() -> aioredis.Redis:
    """Return the shared async Redis client (requires lifespan initialisation).

    Raises:
        RuntimeError: If called before ``init_redis()`` is awaited.
    """
    if _redis_client is None:
        raise RuntimeError(
            "Redis client not initialised. Ensure init_redis() is called "
            "during the application lifespan startup."
        )
    return _redis_client
