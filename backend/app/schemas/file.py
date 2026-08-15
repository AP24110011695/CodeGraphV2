"""Pydantic schemas for File & Symbol API endpoints."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.symbol import SymbolKind


class SymbolResponse(BaseModel):
    """Schema for symbol detail."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    kind: SymbolKind
    start_line: int
    end_line: int
    is_exported: bool = True
    docstring: str | None = None


class FileListItem(BaseModel):
    """Schema for a file entry in the paginated file list."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    path: str
    language: str
    size_bytes: int
    line_count: int
    is_binary: bool
    parse_error: str | None = None


class FileListResponse(BaseModel):
    """Paginated list of repository files."""

    items: list[FileListItem]
    total: int
    page: int
    page_size: int


class FileDetail(BaseModel):
    """Schema for full file detail including content and symbols."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repository_id: uuid.UUID
    path: str
    language: str
    size_bytes: int
    line_count: int
    is_binary: bool
    content: str | None = Field(
        default=None, description="Source code text content (None for binary files)."
    )
    error: str | None = Field(
        default=None, description="Error message if content preview cannot be loaded."
    )
    symbols: list[SymbolResponse] = Field(
        default_factory=list, description="AST symbols extracted from this file."
    )
