"""File-extraction service: walk a repository source tree and populate CodeFile rows.

This service is CPU-bound (hashing, binary detection). Its public entry point
``extract_files()`` offloads the synchronous walk to a thread-pool executor so
the async event loop is not blocked.
"""

import asyncio
import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.framework_detector import detect_frameworks
from app.core.ignore_patterns import IgnoreFilter
from app.core.language_detector import compute_language_stats, detect_language
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.code_file import CodeFile
from app.models.repository import Repository, RepositoryStatus

# Thread-pool reused across calls (bounded to 4 workers to avoid saturating I/O)
_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="file_extractor")

# Binary-detection sample size (first 8 KB)
_BINARY_SAMPLE_BYTES = 8 * 1024

# Hash chunk size
_HASH_CHUNK_BYTES = 64 * 1024


# ---------------------------------------------------------------------------
# Synchronous helpers (run inside executor)
# ---------------------------------------------------------------------------


def _is_binary(path: Path) -> bool:
    """Return ``True`` if *path* looks like a binary file.

    Reads the first :data:`_BINARY_SAMPLE_BYTES` bytes and checks for null
    bytes, which are a strong indicator of binary content.

    Args:
        path: Absolute path to the file.

    Returns:
        ``True`` when a null byte is found in the sample.
    """
    try:
        sample = path.read_bytes()[:_BINARY_SAMPLE_BYTES]
        return b"\x00" in sample
    except OSError:
        return False


def _sha256(path: Path) -> str:
    """Compute the SHA-256 hex digest of *path* in streaming chunks.

    Args:
        path: Absolute path to the file.

    Returns:
        Lowercase hex digest string, or empty string on read error.
    """
    h = hashlib.sha256()
    try:
        with path.open("rb") as fh:
            while chunk := fh.read(_HASH_CHUNK_BYTES):
                h.update(chunk)
    except OSError:
        return ""
    return h.hexdigest()


def _count_lines(path: Path) -> int:
    """Count newlines in *path* (non-binary files only).

    Args:
        path: Absolute path to the file.

    Returns:
        Number of lines, or 0 on read error.
    """
    try:
        content = path.read_bytes()
        return content.count(b"\n")
    except OSError:
        return 0


def _walk_and_collect(
    source_dir: Path,
    ignore_filter: IgnoreFilter,
) -> list[dict[str, object]]:
    """Walk *source_dir* and return file metadata dicts for non-ignored files.

    Args:
        source_dir: Root of the extracted source tree.
        ignore_filter: Pre-built :class:`~app.core.ignore_patterns.IgnoreFilter`.

    Returns:
        List of ``{rel_path, abs_path, size_bytes, content_hash,
        line_count, is_binary}`` dicts.
    """
    records: list[dict[str, object]] = []

    for abs_path in sorted(source_dir.rglob("*")):
        if not abs_path.is_file():
            continue

        rel_path = abs_path.relative_to(source_dir)

        if ignore_filter.should_ignore(rel_path):
            continue

        binary = _is_binary(abs_path)
        size = abs_path.stat().st_size
        content_hash = _sha256(abs_path)
        line_count = 0 if binary else _count_lines(abs_path)

        records.append(
            {
                "rel_path": rel_path.as_posix(),
                "abs_path": abs_path,
                "size_bytes": size,
                "content_hash": content_hash,
                "line_count": line_count,
                "is_binary": binary,
            }
        )

    return records


# ---------------------------------------------------------------------------
# Async public entry point
# ---------------------------------------------------------------------------


async def extract_files(
    repo: Repository,
    db: AsyncSession,
    upload_dir: str = "./uploads",
) -> list[CodeFile]:
    """Walk a repository's source tree and upsert :class:`CodeFile` rows.

    The CPU-bound directory walk and file hashing is offloaded to a thread-pool
    executor so the async event loop remains unblocked.

    Steps:
    1. Mark the current ``AnalysisJob`` as ``extraction`` / in-progress.
    2. Walk ``{upload_dir}/{repo_id}/source/`` in a thread.
    3. Upsert a ``CodeFile`` row for each non-ignored file.
    4. Update ``Repository.file_count`` and ``Repository.status``.

    Args:
        repo: The :class:`Repository` ORM instance to extract files for.
        db: Async database session.
        upload_dir: Base upload directory (``Settings.UPLOAD_DIR``).

    Returns:
        List of all upserted :class:`CodeFile` ORM instances.
    """
    source_dir = Path(upload_dir) / str(repo.id) / "source"
    if not source_dir.exists():
        return []

    # ---- 1. Update AnalysisJob to extraction / in-progress ----
    job_result = await db.execute(
        select(AnalysisJob).where(AnalysisJob.repository_id == repo.id)
    )
    job = job_result.scalar_one_or_none()
    if job:
        job.phase = "extraction"
        job.status = JobStatus.RUNNING
        job.progress = 25
        await db.flush()

    # ---- 2. Walk in executor (CPU-bound) ----
    ignore_filter = IgnoreFilter.from_repo_root(source_dir)
    loop = asyncio.get_event_loop()
    records = await loop.run_in_executor(
        _EXECUTOR,
        _walk_and_collect,
        source_dir,
        ignore_filter,
    )

    # ---- 3. Upsert CodeFile rows ----
    code_files: list[CodeFile] = []
    for rec in records:
        rel_path = str(rec["rel_path"])

        # Check for existing row (upsert by repo_id + path)
        existing_result = await db.execute(
            select(CodeFile).where(
                CodeFile.repository_id == repo.id,
                CodeFile.path == rel_path,
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing is not None:
            existing.size_bytes = int(str(rec["size_bytes"]))
            existing.content_hash = str(rec["content_hash"])
            existing.line_count = int(str(rec["line_count"]))
            existing.is_binary = bool(rec["is_binary"])
            code_files.append(existing)
        else:
            cf = CodeFile(
                repository_id=repo.id,
                path=rel_path,
                size_bytes=int(str(rec["size_bytes"])),
                content_hash=str(rec["content_hash"]),
                line_count=int(str(rec["line_count"])),
                is_binary=bool(rec["is_binary"]),
            )
            db.add(cf)
            code_files.append(cf)

    await db.flush()

    # ---- 4. Language detection per file ----
    lang_line_pairs: list[tuple[str | None, int]] = []
    for cf in code_files:
        if not cf.is_binary:
            lang = detect_language(cf.path)
            cf.language = lang
            lang_line_pairs.append((lang, cf.line_count))

    await db.flush()

    # ---- 5. Repository-level language + framework aggregation ----
    primary_lang, lang_stats = compute_language_stats(lang_line_pairs)
    repo.primary_language = primary_lang
    repo.detected_languages = {k: v for k, v in lang_stats.items()}
    repo.frameworks = detect_frameworks(source_dir)

    repo.file_count = len(code_files)
    repo.status = RepositoryStatus.PARSING

    if job:
        job.status = JobStatus.DONE
        job.progress = 100

    await db.commit()
    await db.refresh(repo)

    return code_files
