"""CodeChunk ORM model with pgvector embedding column."""

import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.code_file import CodeFile
    from app.models.repository import Repository
    from app.models.symbol import Symbol


class ChunkType(StrEnum):
    """Type of code chunk."""

    SYMBOL = "symbol"
    BLOCK = "block"


class CodeChunk(Base):
    """CodeChunk model representing a chunk of code for vector indexing."""

    __tablename__ = "code_chunk"
    __table_args__ = (
        Index(
            "idx_code_chunk_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("code_file.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repository.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_type: Mapped[ChunkType] = mapped_column(
        Enum(ChunkType, native_enum=False), nullable=False
    )
    symbol_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("symbol.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536), nullable=True
    )

    # Relationships
    file: Mapped["CodeFile"] = relationship(back_populates="chunks")
    repository: Mapped["Repository"] = relationship(back_populates="code_chunks")
    symbol: Mapped["Symbol | None"] = relationship()
