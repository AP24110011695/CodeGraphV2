"""Opt-in smoke test against a fully running CodeGraph deployment."""

from __future__ import annotations

import io
import os
import time
import zipfile

import httpx
import pytest

pytestmark = pytest.mark.e2e


def _enabled() -> bool:
    return os.getenv("E2E", "false").lower() == "true"


def _sample_archive() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "sample/main.py", "def greet(name):\n    return f'Hi {name}'\n"
        )
    return buffer.getvalue()


@pytest.mark.skipif(not _enabled(), reason="set E2E=true to run against services")
def test_upload_search_and_chat_smoke() -> None:
    """Exercise upload, asynchronous processing, semantic search, and chat."""
    base_url = os.getenv("E2E_API_BASE_URL", "http://localhost:8000").rstrip("/")
    headers = {}
    if api_key := os.getenv("E2E_API_KEY"):
        headers["X-API-Key"] = api_key

    with httpx.Client(base_url=base_url, headers=headers, timeout=30.0) as client:
        health = client.get("/health")
        assert health.status_code == 200, health.text

        upload = client.post(
            "/api/v1/repositories",
            files={"file": ("sample.zip", _sample_archive(), "application/zip")},
        )
        assert upload.status_code == 200, upload.text
        repository_id = upload.json()["id"]

        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            status = client.get(f"/api/v1/repositories/{repository_id}/status")
            assert status.status_code == 200, status.text
            payload = status.json()
            if payload["status"] == "ready":
                break
            assert payload["status"] != "error", payload
            time.sleep(1)
        else:
            pytest.fail("repository did not reach ready within 90 seconds")

        search = client.post(
            f"/api/v1/repositories/{repository_id}/search",
            json={"query": "greeting function", "limit": 5},
        )
        assert search.status_code == 200, search.text
        assert search.json()

        session = client.post(
            f"/api/v1/repositories/{repository_id}/chat/sessions",
            json={"title": "Smoke"},
        )
        assert session.status_code == 201, session.text
        chat = client.post(
            f"/api/v1/repositories/{repository_id}/chat/sessions/"
            f"{session.json()['session_id']}/messages",
            json={"question": "What does greet do?"},
        )
        assert chat.status_code == 200, chat.text
        assert "data: [DONE]" in chat.text
