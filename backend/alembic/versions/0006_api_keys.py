"""Create API key table.

Revision ID: 0006_api_keys
Revises: 0005_chat_tables
Create Date: 2026-08-16 18:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006_api_keys"
down_revision: str | None = "0005_chat_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the table that stores only SHA-256 API-key hashes."""
    op.create_table(
        "api_key",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_api_key_key_hash", "api_key", ["key_hash"])
    op.create_index("ix_api_key_owner_id", "api_key", ["owner_id"])


def downgrade() -> None:
    """Drop API-key storage."""
    op.drop_index("ix_api_key_owner_id", table_name="api_key")
    op.drop_index("ix_api_key_key_hash", table_name="api_key")
    op.drop_table("api_key")
