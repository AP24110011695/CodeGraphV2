"""Add repository_graph table and cycle columns to repository

Revision ID: 0004_repository_graph
Revises: 0003_add_parse_error_column
Create Date: 2026-08-11 19:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_repository_graph"
down_revision: str | None = "0003_add_parse_error_column"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add has_cycles/cycle_count to repository and create repository_graph table."""
    # Add cycle detection columns to repository
    op.add_column(
        "repository",
        sa.Column("has_cycles", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "repository",
        sa.Column("cycle_count", sa.Integer(), nullable=False, server_default="0"),
    )

    # Create repository_graph table
    op.create_table(
        "repository_graph",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repository.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column(
            "nodes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "edges",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "metrics",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )


def downgrade() -> None:
    """Drop repository_graph table and cycle columns."""
    op.drop_table("repository_graph")
    op.drop_column("repository", "cycle_count")
    op.drop_column("repository", "has_cycles")
