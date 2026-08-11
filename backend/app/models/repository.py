"""Repository ORM model."""

import uuid
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, BigInteger, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.analysis_job import AnalysisJob
    from app.models.code_chunk import CodeChunk
    from app.models.code_file import CodeFile
    from app.models.dependency import Dependency
    from app.models.symbol import Symbol


class RepositorySource(StrEnum):
    """Source of the repository."""

    UPLOAD = "upload"
    GIT_CLONE = "git_clone"


class RepositoryStatus(StrEnum):
    """Lifecycle status of the repository."""

    PENDING = "pending"
    INGESTING = "ingesting"
    PARSING = "parsing"
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"


class Repository(Base, TimestampMixin):
    """Repository model representing an ingested codebase."""

    __tablename__ = "repository"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[RepositorySource] = mapped_column(
        Enum(RepositorySource, native_enum=False), nullable=False
    )
    git_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[RepositoryStatus] = mapped_column(
        Enum(RepositoryStatus, native_enum=False),
        default=RepositoryStatus.PENDING,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    size_bytes: Mapped[int] = mapped_column(
        BigInteger, default=0, server_default="0", nullable=False
    )
    primary_language: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    detected_languages: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )

    file_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )


    # Relationships
    files: Mapped[list["CodeFile"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan", lazy="selectin"
    )
    symbols: Mapped[list["Symbol"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )
    dependencies: Mapped[list["Dependency"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )
    code_chunks: Mapped[list["CodeChunk"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )
    analysis_jobs: Mapped[list["AnalysisJob"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )
