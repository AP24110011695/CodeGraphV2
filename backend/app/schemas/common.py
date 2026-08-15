"""Common reusable Pydantic schemas for pagination and error responses."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    page: int = Field(default=1, ge=1, description="1-indexed page number.")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Number of items per page (max 100)."
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic container for paginated list responses."""

    items: list[T]
    total: int = Field(description="Total number of matching items.")
    page: int = Field(description="Current 1-indexed page number.")
    page_size: int = Field(description="Page size limit.")


class ErrorDetail(BaseModel):
    """Canonical error payload structure."""

    code: str = Field(description="Machine-readable error code (e.g., REPO_NOT_FOUND).")
    message: str = Field(description="Human-readable error explanation.")
    details: dict[str, object] = Field(
        default_factory=dict, description="Optional extra error metadata."
    )


class ErrorResponse(BaseModel):
    """Container schema for error responses."""

    error: ErrorDetail
