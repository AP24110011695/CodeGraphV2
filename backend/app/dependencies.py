"""Shared FastAPI dependency injection helpers.

This module serves as the central location for FastAPI dependencies
used across the application. It starts near-empty and is extended
from Phase 3 onward (e.g., get_db, get_settings).
"""

from app.config import Settings, get_settings
from app.db.session import get_db

__all__ = ["get_app_settings", "get_db", "get_settings"]


def get_app_settings() -> Settings:

    """FastAPI dependency to provide the application settings.

    Returns:
        The application Settings instance.
    """
    return get_settings()
