"""Ingestion service for repository ZIP archive uploads and git clones."""

import asyncio
import os
import re
import shutil
import uuid
import zipfile
from pathlib import Path
from urllib.parse import urlparse

from fastapi import UploadFile
from slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.exceptions import NotFoundError, TooLargeError, ValidationError
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.repository import Repository, RepositorySource, RepositoryStatus

MAX_FILE_COUNT = 50_000
GIT_CLONE_TIMEOUT = 30  # seconds


def detect_repo_name(extract_path: Path, default_name: str = "repository") -> str:
    """Infer a human-readable name from the top-level directory in extracted source.

    Args:
        extract_path: Path to extracted repository source directory.
        default_name: Default fallback name.

    Returns:
        Human-readable repository name.
    """
    children = [
        p
        for p in extract_path.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    ]
    if len(children) == 1:
        return children[0].name
    return default_name


def _create_unique_slug(name: str, repo_id: uuid.UUID) -> str:
    """Create a URL-friendly unique slug for a repository.

    Args:
        name: The base repository name.
        repo_id: The repository UUID.

    Returns:
        Slugified string appended with a short UUID suffix.
    """
    base_slug = slugify(name) or "repository"
    short_suffix = str(repo_id).split("-")[0]
    return f"{base_slug}-{short_suffix}"


def _validate_zip_members(zip_file: zipfile.ZipFile) -> int:
    """Validate zip file members for path traversal and file count limits.

    Args:
        zip_file: Open ZipFile object.

    Returns:
        Count of valid non-directory files.

    Raises:
        ValidationError: If path traversal or excessive file count is detected.
    """
    file_count = 0
    for member in zip_file.infolist():
        filename = member.filename

        # Path traversal checks
        normalized = os.path.normpath(filename)
        if (
            normalized.startswith("..")
            or normalized.startswith("/")
            or normalized.startswith("\\")
            or "../" in filename
            or "..\\" in filename
            or Path(filename).is_absolute()
        ):
            raise ValidationError(
                message=f"Zip archive contains insecure path traversal: {filename}",
                code="PATH_TRAVERSAL_DETECTED",
            )

        if not member.is_dir():
            file_count += 1

    if file_count > MAX_FILE_COUNT:
        raise ValidationError(
            message=f"Zip archive exceeds max allowed file count of {MAX_FILE_COUNT}",
            code="TOO_MANY_FILES",
        )

    return file_count


def _validate_git_url(git_url: str) -> str:
    """Validate that the git URL uses the HTTPS scheme.

    Only HTTPS URLs are permitted to block dangerous schemes such as
    ``file://``, ``git://``, ``ssh://``, and local paths.

    Args:
        git_url: The raw git URL string provided by the caller.

    Returns:
        The validated git URL (stripped of whitespace).

    Raises:
        ValidationError: If the URL does not start with ``https://``.
    """
    url = git_url.strip()
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValidationError(
            message=(
                f"Only HTTPS git URLs are allowed. "
                f"Received scheme: '{parsed.scheme or url[:20]}'"
            ),
            code="INVALID_GIT_URL",
        )
    if not parsed.netloc:
        raise ValidationError(
            message="Git URL must include a valid host.",
            code="INVALID_GIT_URL",
        )
    return url


async def ingest_git(
    git_url: str,
    db: AsyncSession,
    settings: Settings | None = None,
) -> Repository:
    """Clone a git repository and record it in the database.

    Performs a shallow clone (``--depth 1``) of *git_url* into
    ``UPLOAD_DIR/{repo_id}/source/`` using ``asyncio.create_subprocess_exec``.
    The subprocess is killed if it exceeds ``GIT_CLONE_TIMEOUT`` seconds.

    Args:
        git_url: HTTPS git URL to clone.
        db: Async database session.
        settings: Optional Settings override.

    Returns:
        Created Repository database instance.

    Raises:
        ValidationError: If the URL scheme is not HTTPS or the clone fails.
    """
    if settings is None:
        settings = get_settings()

    validated_url = _validate_git_url(git_url)

    # Derive a clean repo name from the URL path (last path component, strip .git)
    url_path = urlparse(validated_url).path.rstrip("/")
    raw_name = Path(url_path).stem or "repository"
    clean_name = re.sub(r"[^\w\s-]", "", raw_name).strip() or "repository"

    repo_id = uuid.uuid4()
    slug = _create_unique_slug(clean_name, repo_id)

    upload_dir = Path(settings.UPLOAD_DIR) / str(repo_id)
    source_dir = upload_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)

    # Shallow clone via asyncio subprocess (non-blocking)
    try:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--depth",
            "1",
            validated_url,
            str(source_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=GIT_CLONE_TIMEOUT
            )
        except TimeoutError:
            proc.kill()
            await proc.communicate()
            shutil.rmtree(upload_dir, ignore_errors=True)
            raise ValidationError(
                message=(
                    f"Git clone timed out after {GIT_CLONE_TIMEOUT}s for: "
                    f"{validated_url}"
                ),
                code="GIT_CLONE_TIMEOUT",
            ) from None

        if proc.returncode != 0:
            shutil.rmtree(upload_dir, ignore_errors=True)
            err_text = stderr.decode(errors="replace").strip()[:256]
            raise ValidationError(
                message=f"Git clone failed: {err_text}",
                code="GIT_CLONE_FAILED",
            )
    except ValidationError:
        raise
    except Exception as exc:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise ValidationError(
            message=f"Git clone encountered an unexpected error: {exc}",
            code="GIT_CLONE_FAILED",
        ) from exc

    # Compute disk size
    total_size = sum(
        f.stat().st_size for f in source_dir.rglob("*") if f.is_file()
    )

    repo = Repository(
        id=repo_id,
        name=clean_name,
        slug=slug,
        source=RepositorySource.GIT_CLONE,
        status=RepositoryStatus.INGESTING,
        size_bytes=total_size,
        file_count=0,  # will be populated by file extraction phase
    )
    db.add(repo)
    await db.flush()

    analysis_job = AnalysisJob(
        repository_id=repo.id,
        phase="ingestion",
        status=JobStatus.RUNNING,
        progress=10,
    )
    db.add(analysis_job)
    await db.commit()
    await db.refresh(repo)

    return repo


async def ingest_zip_bytes(
    filename: str,
    content: bytes,
    db: AsyncSession,
    settings: Settings | None = None,
) -> Repository:
    """Validate, store, extract, and record a repository ZIP archive from raw bytes."""
    if settings is None:
        settings = get_settings()

    max_size_bytes = settings.MAX_REPO_SIZE_MB * 1024 * 1024

    if not filename.lower().endswith(".zip"):
        raise ValidationError(
            message="Only .zip files are supported for archive upload",
            code="INVALID_FILE_TYPE",
        )

    if len(content) > max_size_bytes:
        raise TooLargeError(
            message=f"Uploaded ZIP exceeds max size of {settings.MAX_REPO_SIZE_MB}MB",
            code="PAYLOAD_TOO_LARGE",
        )

    repo_id = uuid.uuid4()
    raw_name = Path(filename).stem
    clean_name = re.sub(r"[^\w\s-]", "", raw_name).strip() or "repository"
    slug = _create_unique_slug(clean_name, repo_id)

    upload_dir = Path(settings.UPLOAD_DIR) / str(repo_id)
    raw_zip_path = upload_dir / "raw.zip"
    source_dir = upload_dir / "source"

    upload_dir.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(parents=True, exist_ok=True)

    raw_zip_path.write_bytes(content)

    try:
        with zipfile.ZipFile(raw_zip_path, "r") as zf:
            file_count = _validate_zip_members(zf)
            zf.extractall(source_dir)
    except zipfile.BadZipFile as err:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise ValidationError(
            message="Uploaded file is not a valid or readable ZIP archive",
            code="CORRUPTED_ZIP",
        ) from err
    except Exception:
        shutil.rmtree(upload_dir, ignore_errors=True)
        raise

    repo_name = detect_repo_name(source_dir, default_name=clean_name)
    total_size = len(content)

    repo = Repository(
        id=repo_id,
        name=repo_name,
        slug=slug,
        source=RepositorySource.UPLOAD,
        status=RepositoryStatus.PENDING,
        size_bytes=total_size,
        file_count=file_count,
    )
    db.add(repo)
    await db.flush()

    repo.status = RepositoryStatus.INGESTING
    analysis_job = AnalysisJob(
        repository_id=repo.id,
        phase="ingestion",
        status=JobStatus.RUNNING,
        progress=10,
    )
    db.add(analysis_job)
    await db.commit()
    await db.refresh(repo)

    return repo


async def ingest_zip(
    file: UploadFile,
    db: AsyncSession,
    settings: Settings | None = None,
) -> Repository:
    """Validate, store, extract, and record an uploaded ZIP repository archive."""
    filename = file.filename or "upload.zip"
    contents = await file.read()
    return await ingest_zip_bytes(filename, contents, db, settings)


async def get_repository(repo_id: uuid.UUID, db: AsyncSession) -> Repository:
    """Fetch a single repository by ID.

    Args:
        repo_id: The repository UUID.
        db: Async database session.

    Returns:
        The Repository ORM instance.

    Raises:
        NotFoundError: If no repository with the given ID exists.
    """
    result = await db.execute(
        select(Repository).where(Repository.id == repo_id)
    )
    repo = result.scalar_one_or_none()
    if repo is None:
        raise NotFoundError(
            message=f"Repository '{repo_id}' not found.",
            code="REPOSITORY_NOT_FOUND",
        )
    return repo


async def list_repositories(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Repository], int]:
    """Return a paginated list of all repositories.

    Args:
        db: Async database session.
        page: 1-based page number.
        page_size: Number of items per page (max 100).

    Returns:
        A tuple of (items, total) where items is the page of repositories
        and total is the count of all repositories.
    """
    page_size = min(page_size, 100)
    offset = (page - 1) * page_size

    count_result = await db.execute(select(func.count()).select_from(Repository))
    total: int = count_result.scalar_one()

    result = await db.execute(
        select(Repository)
        .order_by(Repository.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items = list(result.scalars().all())
    return items, total


async def delete_repository(
    repo_id: uuid.UUID,
    db: AsyncSession,
    settings: Settings | None = None,
) -> None:
    """Delete a repository record and its on-disk files.

    Args:
        repo_id: The repository UUID.
        db: Async database session.
        settings: Optional Settings override.

    Raises:
        NotFoundError: If the repository does not exist.
    """
    if settings is None:
        settings = get_settings()

    repo = await get_repository(repo_id, db)

    # Remove files from disk
    repo_dir = Path(settings.UPLOAD_DIR) / str(repo_id)
    shutil.rmtree(repo_dir, ignore_errors=True)

    await db.delete(repo)
    await db.commit()
