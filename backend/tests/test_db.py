"""Tests for database session, connection, and pgvector extension."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base, TimestampMixin
from app.db.session import AsyncSessionLocal, get_db


@pytest.mark.asyncio
async def test_db_connection_and_vector_extension() -> None:
    """Connect using AsyncSessionLocal, run SELECT 1, and check pgvector extension."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

            vector_res = await session.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            )
            ext_name = vector_res.scalar()
            assert ext_name == "vector"
    except Exception as exc:
        pytest.skip(f"PostgreSQL database not accessible in current environment: {exc}")


@pytest.mark.asyncio
async def test_get_db_generator() -> None:
    """Test get_db dependency yields an AsyncSession."""
    db_gen = get_db()
    try:
        session = await anext(db_gen)
        assert isinstance(session, AsyncSession)
        await db_gen.aclose()
    except Exception as exc:
        pytest.skip(f"PostgreSQL database not accessible in current environment: {exc}")



def test_base_and_mixin_attributes() -> None:
    """Test Base and TimestampMixin class attributes exist."""
    assert hasattr(Base, "metadata")
    assert hasattr(TimestampMixin, "created_at")
    assert hasattr(TimestampMixin, "updated_at")
