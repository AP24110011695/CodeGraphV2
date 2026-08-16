"""Server-Sent Events (SSE) endpoint for real-time repository processing updates.

Streams ``AnalysisJob`` pipeline progress events published by Celery workers
to the frontend. Each event corresponds to a pipeline phase update.

Event format (per API Contract):
    data: {"repo_id": "...", "status": "...", "progress": N, "phase": "..."}

Channel: ``repo_events:{repo_id}``
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.core.auth import get_current_key
from app.core.redis_client import get_redis_client
from app.logging_config import get_logger

router = APIRouter(
    prefix="/repositories", tags=["events"], dependencies=[Depends(get_current_key)]
)

logger = get_logger(__name__)

# How long to wait for new events before emitting a keepalive ping (seconds).
_KEEPALIVE_INTERVAL = 15


@router.get(
    "/{repo_id}/events",
    summary="Repository processing SSE stream",
    description=(
        "Subscribe to real-time processing progress events for a repository. "
        "Events are emitted as Server-Sent Events (SSE) for each pipeline phase "
        "(ingestion, extraction, parsing, graph, indexing). "
        "The stream auto-closes when status is 'ready' or 'error'."
    ),
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "SSE stream of progress events",
            "content": {"text/event-stream": {}},
        },
        404: {"description": "Repository not found"},
    },
)
async def repository_events(repo_id: uuid.UUID, request: Request) -> StreamingResponse:
    """Stream repository pipeline progress events via SSE.

    Subscribes to ``repo_events:{repo_id}`` on Redis pub/sub and forwards
    each published JSON payload as an SSE ``data:`` line.

    Keepalive ``:ping`` comments are sent every ``_KEEPALIVE_INTERVAL`` seconds.
    The stream terminates automatically when the ``status`` field is ``"ready"``
    or ``"error"``.
    """

    async def _event_generator() -> AsyncGenerator[str, None]:
        """Async generator that yields SSE-formatted strings."""
        redis_client: aioredis.Redis = getattr(request.app.state, "redis", None)
        if redis_client is None:
            # This only occurs when called outside the application's lifespan,
            # such as a direct ASGI test client.
            redis_client = get_redis_client()
        channel = f"repo_events:{repo_id}"
        pubsub = redis_client.pubsub()

        try:
            await pubsub.subscribe(channel)
            logger.debug("SSE: subscribed to channel %s", channel)

            last_ping_time = asyncio.get_event_loop().time()

            while True:
                try:
                    # Use a short timeout to keep the event loop responsive.
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True, timeout=0.1
                    )
                except asyncio.CancelledError:
                    logger.debug("SSE: client disconnected from channel %s", channel)
                    break
                except Exception as err:
                    logger.debug("SSE: error getting message: %s", err)
                    message = None

                current_time = asyncio.get_event_loop().time()

                if message is not None and message.get("type") == "message":
                    data: str = message.get("data", "")
                    yield f"data: {data}\n\n"
                    last_ping_time = current_time

                    # Parse the payload to check for terminal states
                    try:
                        import json

                        payload = json.loads(data)
                        if payload.get("status") in ("ready", "error"):
                            logger.debug(
                                "SSE: terminal status '%s' for %s, closing stream",
                                payload["status"],
                                repo_id,
                            )
                            break
                    except Exception:
                        pass
                else:
                    # Emit a ping if the channel has been quiet long enough.
                    if current_time - last_ping_time >= _KEEPALIVE_INTERVAL:
                        yield ":ping\n\n"
                        last_ping_time = current_time

                    # Yield control to prevent busy looping
                    await asyncio.sleep(0.05)

        except asyncio.CancelledError:
            logger.debug("SSE: generator cancelled for channel %s", channel)
        finally:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.aclose()
                logger.debug(
                    "SSE: unsubscribed and closed Redis for channel %s", channel
                )
            except Exception as cleanup_err:
                logger.debug("SSE: cleanup error: %s", cleanup_err)

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Nginx passthrough
            "Connection": "keep-alive",
        },
    )
