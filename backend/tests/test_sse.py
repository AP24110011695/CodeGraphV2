"""Tests for Phase 19 — Real-time Updates (SSE).

Covers:
- Connecting to the SSE endpoint.
- Publishing progress events to Redis and confirming they are received via SSE.
- Keepalive pings on silence.
- Stream termination when ready or error status is encountered.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.dependencies import get_app_settings
from app.main import create_app


class MockPubSub:
    """Mock for redis.asyncio.client.PubSub."""

    def __init__(self) -> None:
        self.queue: asyncio.Queue[str] = asyncio.Queue()

    async def subscribe(self, channel: str) -> None:
        pass

    async def unsubscribe(self, channel: str) -> None:
        pass

    async def get_message(
        self, ignore_subscribe_messages: bool = True, timeout: float = 0.1
    ) -> dict[str, str] | None:
        try:
            # Wait up to the timeout for a message from the queue
            val = await asyncio.wait_for(self.queue.get(), timeout=timeout)
            return {"type": "message", "data": val}
        except TimeoutError:
            return None

    async def aclose(self) -> None:
        pass


class MockRedis:
    """Mock for redis.asyncio.Redis client."""

    def __init__(self) -> None:
        self._pubsub = MockPubSub()

    def pubsub(self) -> MockPubSub:
        return self._pubsub

    async def publish(self, channel: str, message: str) -> None:
        await self._pubsub.queue.put(message)

    async def aclose(self) -> None:
        pass


def _make_settings(tmp_path: Path) -> Settings:
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret",
        LLM_API_KEY="test-key",
        UPLOAD_DIR=str(tmp_path / "uploads"),
    )


@pytest.mark.asyncio
async def test_sse_stream_receives_events(tmp_path: Path) -> None:
    """Subscribe to the events stream, publish a mock event, and verify receipt."""
    settings = _make_settings(tmp_path)
    app = create_app(settings=settings)
    app.dependency_overrides[get_app_settings] = lambda: settings

    # Ensure init_redis and close_redis in lifespan don't try to connect to real Redis
    with (
        patch("app.core.redis_client.init_redis", return_value=MagicMock()),
        patch("app.core.redis_client.close_redis", return_value=MagicMock()),
    ):
        mock_redis = MockRedis()
        app.state.redis = mock_redis

        # The endpoint uses the lifespan-managed Redis client.
        with patch("redis.asyncio.from_url", return_value=mock_redis):
            repo_id = uuid.uuid4()
            channel = f"repo_events:{repo_id}"

            # Delayed publisher task simulating Celery task progress
            async def publish_message_delayed() -> None:
                await asyncio.sleep(0.1)

                payload = {
                    "repo_id": str(repo_id),
                    "status": "parsing",
                    "progress": 50,
                    "phase": "parsing",
                }
                await mock_redis.publish(channel, json.dumps(payload))

                await asyncio.sleep(0.1)
                terminal_payload = {
                    "repo_id": str(repo_id),
                    "status": "ready",
                    "progress": 100,
                    "phase": "indexing",
                }
                await mock_redis.publish(channel, json.dumps(terminal_payload))

            pub_task = asyncio.create_task(publish_message_delayed())

            transport = ASGITransport(app=app)
            events = []

            try:
                async with (
                    AsyncClient(transport=transport, base_url="http://test") as client,
                    client.stream(
                        "GET", f"/api/v1/repositories/{repo_id}/events"
                    ) as response,
                ):
                    assert response.status_code == 200
                    assert response.headers["content-type"].startswith(
                        "text/event-stream"
                    )

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            event_data = json.loads(line[6:])
                            events.append(event_data)
                            if event_data.get("status") == "ready":
                                break
            finally:
                await pub_task

            assert len(events) == 2
            assert events[0]["status"] == "parsing"
            assert events[0]["progress"] == 50
            assert events[0]["phase"] == "parsing"
            assert events[1]["status"] == "ready"
            assert events[1]["progress"] == 100
            assert events[1]["phase"] == "indexing"


@pytest.mark.asyncio
async def test_sse_stream_sends_keepalive(tmp_path: Path) -> None:
    """Ensure keepalive ping is sent when there are no events."""
    settings = _make_settings(tmp_path)
    app = create_app(settings=settings)
    app.dependency_overrides[get_app_settings] = lambda: settings

    # Patch redis lifespan hook to avoid external connection
    with (
        patch("app.core.redis_client.init_redis", return_value=MagicMock()),
        patch("app.core.redis_client.close_redis", return_value=MagicMock()),
    ):
        mock_redis = MockRedis()
        app.state.redis = mock_redis

        # Temporarily set keepalive interval to 0.1s for testing speed
        with (
            patch("app.api.v1.events._KEEPALIVE_INTERVAL", 0.1),
            patch("redis.asyncio.from_url", return_value=mock_redis),
        ):
            repo_id = uuid.uuid4()
            transport = ASGITransport(app=app)
            pings = 0

            async def close_stream_after_pings() -> None:
                await asyncio.sleep(0.35)
                await mock_redis.publish(
                    f"repo_events:{repo_id}",
                    json.dumps(
                        {
                            "repo_id": str(repo_id),
                            "status": "ready",
                            "progress": 100,
                            "phase": "indexing",
                        }
                    ),
                )

            close_task = asyncio.create_task(close_stream_after_pings())

            try:
                async with (
                    AsyncClient(transport=transport, base_url="http://test") as client,
                    client.stream(
                        "GET", f"/api/v1/repositories/{repo_id}/events"
                    ) as response,
                ):
                    assert response.status_code == 200

                    async for line in response.aiter_lines():
                        if line == ":ping":
                            pings += 1
            finally:
                await close_task

            assert pings >= 2
