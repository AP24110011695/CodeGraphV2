"""Files API router.

Exposes:
  GET /api/v1/repositories/{repo_id}/files (paginated)
  GET /api/v1/repositories/{repo_id}/files/{file_id}
  GET /api/v1/repositories/{repo_id}/files/{file_id}/symbols
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.auth import get_current_key
from app.dependencies import get_app_settings, get_db
from app.exceptions import NotFoundError
from app.models.code_file import CodeFile
from app.models.symbol import Symbol
from app.schemas.file import (
    FileDetail,
    FileListItem,
    FileListResponse,
    SymbolResponse,
)
from app.services.ingestion import get_repository

router = APIRouter(
    prefix="/repositories", tags=["files"], dependencies=[Depends(get_current_key)]
)


@router.get(
    "/{repo_id}/files",
    response_model=FileListResponse,
    summary="List repository files (paginated)",
    responses={
        404: {"description": "Repository not found"},
    },
)
async def list_repository_files(
    repo_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Annotated[int, Query(ge=1, description="1-indexed page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 20,
    language: Annotated[str | None, Query(description="Filter files by language")] = None,
) -> FileListResponse:
    """Retrieve a paginated list of ingested files for *repo_id*."""
    try:
        await get_repository(repo_id, db)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_id}' not found.",
        )

    base_query = select(CodeFile).where(CodeFile.repository_id == repo_id)
    if language:
        base_query = base_query.where(CodeFile.language == language)

    # Count total
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Query items
    offset = (page - 1) * page_size
    items_stmt = (
        base_query.order_by(CodeFile.path.asc()).offset(offset).limit(page_size)
    )
    res = await db.execute(items_stmt)
    code_files = list(res.scalars().all())

    items = [FileListItem.model_validate(cf) for cf in code_files]
    return FileListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{repo_id}/files/{file_id}",
    response_model=FileDetail,
    summary="Get file detail and source code content",
    responses={
        400: {"description": "Invalid file path traversal detected"},
        404: {"description": "Repository or file not found"},
    },
)
async def get_file_detail(
    repo_id: uuid.UUID,
    file_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> FileDetail:
    """Retrieve detailed file metadata, AST symbols, and source content from disk."""
    try:
        await get_repository(repo_id, db)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_id}' not found.",
        )

    # Query CodeFile
    file_res = await db.execute(
        select(CodeFile).where(
            CodeFile.id == file_id,
            CodeFile.repository_id == repo_id,
        )
    )
    code_file = file_res.scalar_one_or_none()
    if code_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{file_id}' not found in repository '{repo_id}'.",
        )

    # Fetch symbols
    sym_res = await db.execute(
        select(Symbol)
        .where(Symbol.file_id == file_id)
        .order_by(Symbol.start_line.asc())
    )
    symbols = [SymbolResponse.model_validate(s) for s in sym_res.scalars().all()]

    # Read content with path containment check
    content: str | None = None
    error: str | None = None

    if code_file.is_binary:
        error = "Binary file — no content preview"
    else:
        upload_root = Path(settings.UPLOAD_DIR).resolve()
        source_root = (upload_root / str(repo_id) / "source").resolve()
        target_path = (source_root / code_file.path).resolve()

        # Security check: path traversal containment
        try:
            target_path.relative_to(source_root)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path containment",
            )

        if target_path.is_file():
            try:
                content = target_path.read_text(encoding="utf-8", errors="replace")
            except Exception as err:
                error = f"Error reading file content: {err}"
        else:
            error = "File source not found on disk"

    return FileDetail(
        id=code_file.id,
        repository_id=code_file.repository_id,
        path=code_file.path,
        language=code_file.language,
        size_bytes=code_file.size_bytes,
        line_count=code_file.line_count,
        is_binary=code_file.is_binary,
        content=content,
        error=error,
        symbols=symbols,
    )


@router.get(
    "/{repo_id}/files/{file_id}/symbols",
    response_model=list[SymbolResponse],
    summary="Get AST symbols extracted from a file",
    responses={
        404: {"description": "Repository or file not found"},
    },
)
async def list_file_symbols(
    repo_id: uuid.UUID,
    file_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[SymbolResponse]:
    """Retrieve all AST symbols associated with a specific code file."""
    try:
        await get_repository(repo_id, db)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_id}' not found.",
        )

    file_res = await db.execute(
        select(CodeFile).where(
            CodeFile.id == file_id,
            CodeFile.repository_id == repo_id,
        )
    )
    if file_res.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{file_id}' not found in repository '{repo_id}'.",
        )

    sym_res = await db.execute(
        select(Symbol)
        .where(Symbol.file_id == file_id)
        .order_by(Symbol.start_line.asc())
    )
    return [SymbolResponse.model_validate(s) for s in sym_res.scalars().all()]
