"""Repository API endpoints — upload, clone, list, get, delete."""

import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.session import get_db
from app.dependencies import get_app_settings
from app.schemas.repository import (
    RepositoryCloneRequest,
    RepositoryListItem,
    RepositoryListResponse,
    RepositoryResponse,
)
from app.services import code_parser, file_extractor, ingestion

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post(
    "",
    response_model=RepositoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload repository ZIP archive",
    description="Upload a ZIP file containing source code for repository ingestion.",
)
async def upload_repository(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> RepositoryResponse:
    """Upload a ZIP archive and initiate repository ingestion.

    Args:
        file: The uploaded ZIP file.
        db: Database session.
        settings: Application settings.

    Returns:
        RepositoryResponse with repository metadata and initial ingestion status.
    """
    repo = await ingestion.ingest_zip(file, db, settings)
    return RepositoryResponse.model_validate(repo)


@router.post(
    "/clone",
    response_model=RepositoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Clone repository from git URL",
    description=(
        "Initiate a shallow git clone of a repository from an HTTPS URL. "
        "Only https:// URLs are accepted."
    ),
)
async def clone_repository(
    body: RepositoryCloneRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> RepositoryResponse:
    """Clone a remote git repository and begin ingestion.

    Args:
        body: Clone request containing the HTTPS git URL.
        db: Database session.
        settings: Application settings.

    Returns:
        RepositoryResponse with repository metadata and initial ingestion status.
    """
    repo = await ingestion.ingest_git(body.git_url, db, settings)
    return RepositoryResponse.model_validate(repo)


@router.get(
    "",
    response_model=RepositoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all repositories",
    description="Return a paginated list of all ingested repositories.",
)
async def list_repositories(
    page: int = Query(default=1, ge=1, description="Page number (1-based)."),
    page_size: int = Query(
        default=20, ge=1, le=100, description="Number of items per page."
    ),
    db: AsyncSession = Depends(get_db),
) -> RepositoryListResponse:
    """List repositories with pagination.

    Args:
        page: 1-based page number.
        page_size: Items per page (max 100).
        db: Database session.

    Returns:
        Paginated list of repositories.
    """
    items, total = await ingestion.list_repositories(db, page=page, page_size=page_size)
    return RepositoryListResponse(
        items=[RepositoryListItem.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{repo_id}",
    response_model=RepositoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get repository detail",
    description="Retrieve full metadata for a single repository by ID.",
)
async def get_repository(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> RepositoryResponse:
    """Retrieve a repository by its UUID.

    Args:
        repo_id: The repository UUID path parameter.
        db: Database session.

    Returns:
        Full repository detail.

    Raises:
        NotFoundError: If the repository does not exist.
    """
    repo = await ingestion.get_repository(repo_id, db)
    return RepositoryResponse.model_validate(repo)


@router.delete(
    "/{repo_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete repository",
    description="Delete a repository record and all associated files from disk.",
)
async def delete_repository(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> dict[str, str]:
    """Delete a repository and its on-disk files.

    Args:
        repo_id: The repository UUID path parameter.
        db: Database session.
        settings: Application settings.

    Returns:
        Confirmation message.

    Raises:
        NotFoundError: If the repository does not exist.
    """
    await ingestion.delete_repository(repo_id, db, settings)
    return {"message": f"Repository '{repo_id}' deleted successfully."}


@router.post(
    "/{repo_id}/extract",
    status_code=status.HTTP_200_OK,
    summary="[Debug] Extract repository files",
    description=(
        "Synchronously walk the source tree, hash all files, and populate "
        "CodeFile rows. Debug-only — will be superseded by the Celery pipeline "
        "in Phase 18."
    ),
)
async def extract_repository_files(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> dict[str, object]:
    """Walk the source tree of a repository and upsert CodeFile rows.

    Args:
        repo_id: The repository UUID path parameter.
        db: Database session.
        settings: Application settings.

    Returns:
        Summary dict with ``file_count`` and ``repo_id``.

    Raises:
        NotFoundError: If the repository does not exist.
    """
    repo = await ingestion.get_repository(repo_id, db)
    code_files = await file_extractor.extract_files(
        repo, db, upload_dir=settings.UPLOAD_DIR
    )
    return {
        "repo_id": str(repo_id),
        "file_count": len(code_files),
        "message": "File extraction completed.",
    }


@router.post(
    "/{repo_id}/parse",
    status_code=status.HTTP_200_OK,
    summary="[Debug] Parse repository symbols & dependencies",
    description=(
        "Synchronously extract files, run AST parsers (Python, TS, JS), and "
        "resolve imports into Symbol and Dependency database rows. Debug-only."
    ),
)
async def parse_repository_endpoint(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> dict[str, object]:
    """Extract files and parse AST symbols & dependencies for a repository.

    Args:
        repo_id: The repository UUID path parameter.
        db: Database session.
        settings: Application settings.

    Returns:
        Summary dict with ``repo_id`` and ``symbol_count``.

    Raises:
        NotFoundError: If the repository does not exist.
    """
    repo = await ingestion.get_repository(repo_id, db)
    code_files = await file_extractor.extract_files(
        repo, db, upload_dir=settings.UPLOAD_DIR
    )
    symbols = await code_parser.parse_repository(
        repo, code_files, db, upload_dir=settings.UPLOAD_DIR
    )
    return {
        "repo_id": str(repo_id),
        "file_count": len(code_files),
        "symbol_count": len(symbols),
        "message": "Repository parsing completed.",
    }


