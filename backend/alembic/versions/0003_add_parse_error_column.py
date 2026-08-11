"""Add parse_error column to code_file table

Revision ID: 0003_add_parse_error_column
Revises: 0002_add_frameworks_column
Create Date: 2026-08-11 18:27:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_add_parse_error_column"
down_revision: str | None = "0002_add_frameworks_column"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add parse_error column to code_file table."""
    op.add_column(
        "code_file",
        sa.Column("parse_error", sa.String(length=2048), nullable=True),
    )


def downgrade() -> None:
    """Remove parse_error column from code_file table."""
    op.drop_column("code_file", "parse_error")
