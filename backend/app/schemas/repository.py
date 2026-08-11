"""Pydantic schemas for Repository API endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.repository import RepositorySource, RepositoryStatus


class RepositoryCreate(BaseModel):
    """Schema for repository creation."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class RepositoryCloneRequest(BaseModel):
    """Schema for git clone ingestion request."""

    git_url: str = Field(
        ...,
        description="HTTPS git URL to clone (must start with https://).",
        examples=["https://github.com/owner/repo.git"],
    )


class RepositoryResponse(BaseModel):
    """Schema for full repository detail response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    status: RepositoryStatus
    source: RepositorySource
    size_bytes: int = 0
    file_count: int = 0
    created_at: datetime


class RepositoryListItem(BaseModel):
    """Schema for a single item in repository list response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    status: RepositoryStatus
    source: RepositorySource
    file_count: int = 0
    created_at: datetime


class RepositoryListResponse(BaseModel):
    """Paginated list of repositories."""

    items: list[RepositoryListItem]
    total: int
    page: int
    page_size: int
