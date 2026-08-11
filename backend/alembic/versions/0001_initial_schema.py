"""Initial domain schema

Revision ID: 0001_initial_schema
Revises: 0000_enable_pgvector
Create Date: 2026-08-11 14:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: str | None = "0000_enable_pgvector"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create initial domain tables and indexes."""
    # 1. repository
    op.create_table(
        "repository",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("git_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("primary_language", sa.String(length=100), nullable=True),
        sa.Column(
            "detected_languages",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("file_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_repository_slug", "repository", ["slug"], unique=True)

    # 2. code_file
    op.create_table(
        "code_file",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repository.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("language", sa.String(length=100), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("line_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_binary", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_code_file_repository_id", "code_file", ["repository_id"])
    op.create_index(
        "uix_code_file_repo_path", "code_file", ["repository_id", "path"], unique=True
    )

    # 3. symbol
    op.create_table(
        "symbol",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "file_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("code_file.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repository.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("signature", sa.Text(), nullable=True),
        sa.Column("docstring", sa.Text(), nullable=True),
        sa.Column("is_exported", sa.Boolean(), server_default="false", nullable=False),
    )
    op.create_index("ix_symbol_file_id", "symbol", ["file_id"])
    op.create_index("ix_symbol_repository_id", "symbol", ["repository_id"])
    op.create_index("ix_symbol_name", "symbol", ["name"])

    # 4. dependency
    op.create_table(
        "dependency",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repository.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "from_file_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("code_file.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "to_file_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("code_file.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("import_name", sa.String(length=255), nullable=False),
        sa.Column("import_path", sa.Text(), nullable=False),
        sa.Column("dependency_type", sa.String(length=50), nullable=False),
    )
    op.create_index("ix_dependency_repository_id", "dependency", ["repository_id"])
    op.create_index("ix_dependency_from_file_id", "dependency", ["from_file_id"])
    op.create_index("ix_dependency_to_file_id", "dependency", ["to_file_id"])

    # 5. code_chunk
    op.create_table(
        "code_chunk",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "file_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("code_file.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repository.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("chunk_type", sa.String(length=50), nullable=False),
        sa.Column(
            "symbol_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("symbol.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("embedding", Vector(1536), nullable=True),
    )
    op.create_index("ix_code_chunk_file_id", "code_chunk", ["file_id"])
    op.create_index("ix_code_chunk_repository_id", "code_chunk", ["repository_id"])
    op.create_index("ix_code_chunk_symbol_id", "code_chunk", ["symbol_id"])
    op.create_index(
        "idx_code_chunk_embedding",
        "code_chunk",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_with={"lists": 100},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    # 6. analysis_job
    op.create_table(
        "analysis_job",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "repository_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repository.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("phase", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("progress", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_analysis_job_repository_id", "analysis_job", ["repository_id"])


def downgrade() -> None:
    """Drop initial domain tables and indexes."""
    op.drop_table("analysis_job")
    op.drop_table("code_chunk")
    op.drop_table("dependency")
    op.drop_table("symbol")
    op.drop_table("code_file")
    op.drop_table("repository")
