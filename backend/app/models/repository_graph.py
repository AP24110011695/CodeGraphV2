"""RepositoryGraph ORM model."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.repository import Repository


class RepositoryGraph(Base):
    """Serialized dependency graph for a repository.

    Stores the fully-computed graph (nodes, edges, and aggregate metrics) as
    JSONB blobs so it can be served directly from the database without rebuilding
    the networkx graph on every request.
    """

    __tablename__ = "repository_graph"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repository.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # JSONB columns — stored as Python dicts/lists at the ORM level.
    # Use JSON().with_variant(JSONB, "postgresql") for cross-dialect compatibility
    # (allows SQLite in unit tests, JSONB in production PostgreSQL).
    nodes: Mapped[list[Any]] = mapped_column(
        JSON().with_variant(JSONB(astext_type=Text()), "postgresql"),
        nullable=False,
        default=list,
    )
    edges: Mapped[list[Any]] = mapped_column(
        JSON().with_variant(JSONB(astext_type=Text()), "postgresql"),
        nullable=False,
        default=list,
    )
    metrics: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB(astext_type=Text()), "postgresql"),
        nullable=False,
        default=dict,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    # Relationships
    repository: Mapped["Repository"] = relationship(back_populates="graph")
