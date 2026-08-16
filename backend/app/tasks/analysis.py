"""Celery background tasks for the automated repository processing pipeline.

Pipeline Chain:
  ingest_repository_task -> extract_files_task -> parse_repository_task
  -> build_graph_task -> index_repository_task

Canonical Phases & Progress Milestones:
  ingestion (10%) -> extraction (25%) -> parsing (50%) -> graph (70%)
  -> indexing (100%)
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Coroutine
from typing import Any, TypeVar

import redis
from celery import chain, shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import get_settings
from app.exceptions import AppException
from app.logging_config import get_logger
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.code_file import CodeFile
from app.models.repository import RepositoryStatus
from app.services import code_parser, file_extractor, graph_builder, indexer, ingestion

logger = get_logger(__name__)

T = TypeVar("T")


def _run_async(coro: Coroutine[Any, Any, T]) -> T:  # noqa: UP047
    """Run an async coroutine synchronously in Celery task worker process."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(coro)).result()
    else:
        return asyncio.run(coro)


def _publish_redis_event(
    repo_id: str,
    status_val: str,
    progress: int,
    phase: str,
    error_message: str | None = None,
) -> None:
    """Publish a repository progress payload to its Redis pub/sub channel."""
    settings = get_settings()
    try:
        client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        payload = {
            "repo_id": repo_id,
            "status": status_val,
            "progress": progress,
            "phase": phase,
            "error_message": error_message,
        }
        client.publish(f"repo_events:{repo_id}", json.dumps(payload))
        client.close()
    except Exception as err:
        logger.debug("Redis pub/sub message publish skipped: %s", err)


def _retry_transient_failure(task: Any, exc: Exception) -> None:
    """Retry operational failures, but surface validation/domain errors at once."""
    if isinstance(exc, AppException):
        raise exc
    raise task.retry(exc=exc, countdown=2**task.request.retries)


async def _get_or_create_job(repo_id: uuid.UUID, db: AsyncSession) -> AnalysisJob:
    """Fetch the latest AnalysisJob for repo_id or create a new one."""
    res = await db.execute(
        select(AnalysisJob)
        .where(AnalysisJob.repository_id == repo_id)
        .order_by(AnalysisJob.created_at.desc())
    )
    job = res.scalars().first()
    if not job:
        job = AnalysisJob(
            id=uuid.uuid4(),
            repository_id=repo_id,
            phase="ingestion",
            status=JobStatus.PENDING,
            progress=0,
        )
        db.add(job)
        await db.flush()
    return job


async def _handle_step_failure(
    repo_id: uuid.UUID, phase: str, exc: Exception, db: AsyncSession
) -> None:
    """Update job and repository status to error/failed on step failure."""
    err_str = str(exc)
    repo = await ingestion.get_repository(repo_id, db)
    repo.status = RepositoryStatus.ERROR
    repo.error_message = err_str

    job = await _get_or_create_job(repo_id, db)
    job.status = JobStatus.FAILED
    job.phase = phase
    job.error = err_str

    await db.commit()
    _publish_redis_event(
        repo_id=str(repo_id),
        status_val=RepositoryStatus.ERROR.value,
        progress=job.progress,
        phase=phase,
        error_message=err_str,
    )


# ---------------------------------------------------------------------------
# Task 1: Ingestion
# ---------------------------------------------------------------------------


@shared_task(name="app.tasks.analysis.ingest_repository_task", bind=True, max_retries=3)
def ingest_repository_task(self: Any, repo_id_str: str) -> str:
    """Step 1: Start ingestion phase, mark status ingesting, progress=10."""
    logger.info("Task [1/5] Ingesting repository %s", repo_id_str)
    settings = get_settings()

    async def _async_ingest() -> str:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async with AsyncSession(engine, expire_on_commit=False) as db:
            repo_id = uuid.UUID(repo_id_str)
            try:
                repo = await ingestion.get_repository(repo_id, db)
                repo.status = RepositoryStatus.INGESTING

                job = await _get_or_create_job(repo_id, db)
                job.status = JobStatus.RUNNING
                job.phase = "ingestion"
                job.progress = 10
                await db.commit()

                _publish_redis_event(
                    repo_id=repo_id_str,
                    status_val=RepositoryStatus.INGESTING.value,
                    progress=10,
                    phase="ingestion",
                )
                return repo_id_str
            except Exception as exc:
                await _handle_step_failure(repo_id, "ingestion", exc, db)
                raise exc
        await engine.dispose()

    try:
        return _run_async(_async_ingest())
    except Exception as exc:
        _retry_transient_failure(self, exc)


# ---------------------------------------------------------------------------
# Task 2: Extraction
# ---------------------------------------------------------------------------


@shared_task(name="app.tasks.analysis.extract_files_task", bind=True, max_retries=3)
def extract_files_task(self: Any, repo_id_str: str) -> str:
    """Step 2: Extract code files from disk/zip, phase=extraction, progress=25."""
    logger.info("Task [2/5] Extracting files for repository %s", repo_id_str)
    settings = get_settings()

    async def _async_extract() -> str:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async with AsyncSession(engine, expire_on_commit=False) as db:
            repo_id = uuid.UUID(repo_id_str)
            try:
                repo = await ingestion.get_repository(repo_id, db)
                repo.status = RepositoryStatus.PARSING

                job = await _get_or_create_job(repo_id, db)
                job.phase = "extraction"
                job.progress = 25
                await db.commit()

                _publish_redis_event(
                    repo_id=repo_id_str,
                    status_val=RepositoryStatus.PARSING.value,
                    progress=25,
                    phase="extraction",
                )

                await file_extractor.extract_files(
                    repo, db, upload_dir=settings.UPLOAD_DIR
                )
                return repo_id_str
            except Exception as exc:
                await _handle_step_failure(repo_id, "extraction", exc, db)
                raise exc
        await engine.dispose()

    try:
        return _run_async(_async_extract())
    except Exception as exc:
        _retry_transient_failure(self, exc)


# ---------------------------------------------------------------------------
# Task 3: Parsing
# ---------------------------------------------------------------------------


@shared_task(name="app.tasks.analysis.parse_repository_task", bind=True, max_retries=3)
def parse_repository_task(self: Any, repo_id_str: str) -> str:
    """Step 3: Parse AST symbols & dependencies, phase=parsing, progress=50."""
    logger.info("Task [3/5] Parsing AST for repository %s", repo_id_str)
    settings = get_settings()

    async def _async_parse() -> str:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async with AsyncSession(engine, expire_on_commit=False) as db:
            repo_id = uuid.UUID(repo_id_str)
            try:
                repo = await ingestion.get_repository(repo_id, db)

                job = await _get_or_create_job(repo_id, db)
                job.phase = "parsing"
                job.progress = 50
                await db.commit()

                _publish_redis_event(
                    repo_id=repo_id_str,
                    status_val=RepositoryStatus.PARSING.value,
                    progress=50,
                    phase="parsing",
                )

                res = await db.execute(
                    select(CodeFile).where(CodeFile.repository_id == repo_id)
                )
                code_files = list(res.scalars().all())

                await code_parser.parse_repository(
                    repo, code_files, db, upload_dir=settings.UPLOAD_DIR
                )
                return repo_id_str
            except Exception as exc:
                await _handle_step_failure(repo_id, "parsing", exc, db)
                raise exc
        await engine.dispose()

    try:
        return _run_async(_async_parse())
    except Exception as exc:
        _retry_transient_failure(self, exc)


# ---------------------------------------------------------------------------
# Task 4: Graph Building
# ---------------------------------------------------------------------------


@shared_task(name="app.tasks.analysis.build_graph_task", bind=True, max_retries=3)
def build_graph_task(self: Any, repo_id_str: str) -> str:
    """Construct dependency graph and page-rank metrics at 70% progress."""
    logger.info("Task [4/5] Building graph for repository %s", repo_id_str)
    settings = get_settings()

    async def _async_graph() -> str:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async with AsyncSession(engine, expire_on_commit=False) as db:
            repo_id = uuid.UUID(repo_id_str)
            try:
                repo = await ingestion.get_repository(repo_id, db)

                job = await _get_or_create_job(repo_id, db)
                job.phase = "graph"
                job.progress = 70
                await db.commit()

                _publish_redis_event(
                    repo_id=repo_id_str,
                    status_val=RepositoryStatus.PARSING.value,
                    progress=70,
                    phase="graph",
                )

                await graph_builder.build_graph(
                    repo, db, upload_dir=settings.UPLOAD_DIR
                )
                return repo_id_str
            except Exception as exc:
                await _handle_step_failure(repo_id, "graph", exc, db)
                raise exc
        await engine.dispose()

    try:
        return _run_async(_async_graph())
    except Exception as exc:
        _retry_transient_failure(self, exc)


# ---------------------------------------------------------------------------
# Task 5: Indexing
# ---------------------------------------------------------------------------


@shared_task(name="app.tasks.analysis.index_repository_task", bind=True, max_retries=3)
def index_repository_task(self: Any, repo_id_str: str) -> str:
    """Step 5: Vector chunking & embedding generation, phase=indexing, progress=100."""
    logger.info("Task [5/5] Vector indexing repository %s", repo_id_str)
    settings = get_settings()

    async def _async_index() -> str:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async with AsyncSession(engine, expire_on_commit=False) as db:
            repo_id = uuid.UUID(repo_id_str)
            try:
                repo = await ingestion.get_repository(repo_id, db)

                job = await _get_or_create_job(repo_id, db)
                job.phase = "indexing"
                job.progress = 90
                await db.commit()

                _publish_redis_event(
                    repo_id=repo_id_str,
                    status_val=RepositoryStatus.INDEXING.value,
                    progress=90,
                    phase="indexing",
                )

                await indexer.index_repository(
                    repo, db, settings=settings, upload_dir=settings.UPLOAD_DIR
                )

                # Finalize
                repo.status = RepositoryStatus.READY
                job.status = JobStatus.DONE
                job.progress = 100
                job.phase = "indexing"
                await db.commit()

                _publish_redis_event(
                    repo_id=repo_id_str,
                    status_val=RepositoryStatus.READY.value,
                    progress=100,
                    phase="indexing",
                )
                logger.info("Repository %s successfully indexed and READY", repo_id_str)
                return repo_id_str
            except Exception as exc:
                await _handle_step_failure(repo_id, "indexing", exc, db)
                raise exc
        await engine.dispose()

    try:
        return _run_async(_async_index())
    except Exception as exc:
        _retry_transient_failure(self, exc)


# ---------------------------------------------------------------------------
# Pipeline Trigger Helper
# ---------------------------------------------------------------------------


def start_analysis_pipeline(repo_id: str) -> Any:
    """Construct and trigger the full Celery task chain for repository analysis."""
    pipeline = chain(
        ingest_repository_task.s(repo_id),
        extract_files_task.s(),
        parse_repository_task.s(),
        build_graph_task.s(),
        index_repository_task.s(),
    )
    return pipeline.apply_async()
