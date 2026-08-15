"""Pydantic schemas for semantic search API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Schema for semantic search request body."""

    query: str = Field(
        ...,
        min_length=1,
        description="Natural language search query.",
        examples=["authentication login flow"],
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of search results to return.",
    )


class SearchResult(BaseModel):
    """A single semantic search result chunk."""

    chunk_id: str = Field(description="CodeChunk UUID as string.")
    file_id: str = Field(description="CodeFile UUID as string.")
    path: str = Field(description="Repository-relative file path.")
    content: str = Field(description="Source content of the chunk.")
    start_line: int = Field(description="1-indexed start line.")
    end_line: int = Field(description="1-indexed end line.")
    score: float = Field(description="Cosine similarity score (0.0 to 1.0).")
    chunk_type: str = Field(description="Type of chunk: 'symbol' or 'block'.")
    symbol_id: str | None = Field(
        default=None, description="Symbol UUID as string if symbol chunk."
    )


class SearchResponse(BaseModel):
    """Container response schema for semantic search."""

    query: str
    results: list[SearchResult]
    total: int
