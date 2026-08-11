"""Dependency ORM model."""

import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.code_file import CodeFile
    from app.models.repository import Repository


class DependencyType(StrEnum):
    """Type of dependency import."""

    INTERNAL = "internal"
    EXTERNAL = "external"
    STDLIB = "stdlib"


class Dependency(Base):
    """Dependency model representing code import/dependency relationships."""

    __tablename__ = "dependency"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repository.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("code_file.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_file_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("code_file.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    import_name: Mapped[str] = mapped_column(String(255), nullable=False)
    import_path: Mapped[str] = mapped_column(Text, nullable=False)
    dependency_type: Mapped[DependencyType] = mapped_column(
        Enum(DependencyType, native_enum=False), nullable=False
    )

    # Relationships
    repository: Mapped["Repository"] = relationship(back_populates="dependencies")
    from_file: Mapped["CodeFile"] = relationship(foreign_keys=[from_file_id])
    to_file: Mapped["CodeFile | None"] = relationship(foreign_keys=[to_file_id])
