"""Add frameworks column to repository table

Revision ID: 0002_add_frameworks_column
Revises: 0001_initial_schema
Create Date: 2026-08-11 18:21:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_add_frameworks_column"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add frameworks JSONB column to the repository table."""
    op.add_column(
        "repository",
        sa.Column(
            "frameworks",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove frameworks column from the repository table."""
    op.drop_column("repository", "frameworks")
