"""API-key hashing, bootstrap provisioning, and FastAPI authentication."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import get_app_settings, get_db
from app.exceptions import AuthenticationError
from app.models.api_key import ApiKey


def hash_api_key(key: str) -> str:
    """Return the SHA-256 digest used as the persisted key representation."""
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a URL-safe plaintext credential for one-time presentation."""
    return secrets.token_urlsafe(32)


async def bootstrap_admin_api_key(
    db: AsyncSession, settings: Settings
) -> ApiKey | None:
    """Create the configured bootstrap key once, only when no keys exist."""
    if not settings.ADMIN_API_KEY:
        return None

    key_count = await db.scalar(select(func.count()).select_from(ApiKey))
    if key_count:
        return None

    api_key = ApiKey(
        key_hash=hash_api_key(settings.ADMIN_API_KEY),
        label="bootstrap-admin",
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key


async def get_current_key_optional(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    x_api_key: str | None = Header(default=None),
) -> ApiKey | None:
    """Allow local mode; validate the API key when the request policy requires it."""
    requires_key = settings.REQUIRE_AUTH and (
        request.method != "GET" or settings.REQUIRE_AUTH_FOR_READS
    )
    if not requires_key:
        return None
    if not x_api_key:
        raise AuthenticationError()

    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == hash_api_key(x_api_key))
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise AuthenticationError(message="Invalid API key")

    api_key.last_used_at = datetime.now(UTC)
    await db.commit()
    return api_key


get_current_key = get_current_key_optional
