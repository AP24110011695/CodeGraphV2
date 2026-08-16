"""Repository API endpoints — upload, clone, list, get, delete."""

import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.session import get_db
from app.dependencies import get_app_settings
from app.models.analysis_job import AnalysisJob
from app.models.repository import RepositoryStatus
from app.schemas.repository import (
    RepositoryCloneRequest,
    RepositoryListItem,
    RepositoryListResponse,
    RepositoryResponse,
    RepositoryStatusResponse,
)
from app.services import ingestion
from app.tasks.analysis import start_analysis_pipeline

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
    """Upload a ZIP archive and initiate automated repository analysis pipeline."""
    repo = await ingestion.ingest_zip(file, db, settings)
    try:
        start_analysis_pipeline(str(repo.id))
    except Exception:
        pass  # Pipeline trigger is best-effort; worker handles retries
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
    """Clone a remote git repository and begin automated analysis pipeline."""
    repo = await ingestion.ingest_git(body.git_url, db, settings)
    try:
        start_analysis_pipeline(str(repo.id))
    except Exception:
        pass  # Pipeline trigger is best-effort; worker handles retries
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


@router.get(
    "/{repo_id}/status",
    response_model=RepositoryStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get repository status, progress percentage, and pipeline phase",
    description="Polling fallback for coarse repository status, progress, and pipeline phase.",
    responses={
        404: {"description": "Repository not found"},
    },
)
async def get_repository_status(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> RepositoryStatusResponse:
    """Poll repository coarse status, progress percentage, and granular pipeline phase.

    Pulls from the latest AnalysisJob row for the repository.
    """
    repo = await ingestion.get_repository(repo_id, db)

    res = await db.execute(
        select(AnalysisJob).where(AnalysisJob.repository_id == repo.id)
    )
    job = res.scalar_one_or_none()

    if job:
        progress = job.progress
        phase = job.phase
        error_msg = repo.error_message
    else:
        if repo.status == RepositoryStatus.READY:
            progress = 100
            phase = "indexing"
        elif repo.status == RepositoryStatus.ERROR:
            progress = 0
            phase = "ingestion"
        else:
            progress = 0
            phase = "ingestion"
        error_msg = repo.error_message

    return RepositoryStatusResponse(
        status=repo.status,
        progress=progress,
        phase=phase,
        error_message=error_msg,
    )

