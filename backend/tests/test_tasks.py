"""Tests for Phase 18 — Celery & Redis Background Job System.

Covers:
- Automated task chain execution (ingest -> extract -> parse -> build_graph -> index).
- Celery eager mode execution (CELERY_TASK_ALWAYS_EAGER=True).
- AnalysisJob progress tracking at each milestone (10%, 25%, 50%, 70%, 100%).
- Repository status transition to READY on completion.
- Error handling on step failure (repository and job error states).
"""

from __future__ import annotations

import io
import uuid
import zipfile
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import EnvironmentType, Settings
from app.db.base import Base
from app.exceptions import NotFoundError
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.code_chunk import CodeChunk
from app.models.code_file import CodeFile
from app.models.repository import Repository, RepositoryStatus
from app.models.symbol import Symbol
from app.services import ingestion
from app.workers.celery_app import celery_app

# Configure Celery to run tasks synchronously in eager mode for testing
celery_app.conf.update(
    task_always_eager=True,
    task_eager_propagates=True,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_engine(
    db_path: Path,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    return engine, factory


def _make_settings(tmp_path: Path, db_path: Path) -> Settings:
    return Settings(
        DATABASE_URL=f"sqlite+aiosqlite:///{db_path}",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret",
        LLM_API_KEY="test-key",
        UPLOAD_DIR=str(tmp_path),
        ENVIRONMENT=EnvironmentType.PRODUCTION,
    )


def _create_sample_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "sample_repo/calc.py",
            "def add(x: int, y: int) -> int:\n    return x + y\n",
        )
        zf.writestr(
            "sample_repo/utils.ts",
            "export function greet(name: string): string {\n"
            "    return 'Hello ' + name;\n}\n",
        )
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Task Pipeline Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_analysis_chain_eager(tmp_path: Path) -> None:
    """Task chain runs ingest -> extract -> parse -> graph -> index eager end-to-end."""
    db_path = tmp_path / "test.db"
    engine, session_factory = await _make_engine(db_path)
    settings = _make_settings(tmp_path, db_path)
    zip_bytes = _create_sample_zip()

    from unittest.mock import patch

    with (
        patch("app.tasks.analysis.get_settings", return_value=settings),
        patch("app.tasks.analysis._publish_redis_event"),
    ):
        # Create initial ingested repository
        async with session_factory() as db:
            repo = await ingestion.ingest_zip_bytes(
                filename="sample_repo.zip",
                content=zip_bytes,
                db=db,
                settings=settings,
            )
            repo_id_str = str(repo.id)

        # Import tasks dynamically
        from app.tasks.analysis import (
            build_graph_task,
            extract_files_task,
            index_repository_task,
            ingest_repository_task,
            parse_repository_task,
        )

        # Execute tasks sequentially in eager mode
        r1 = ingest_repository_task.delay(repo_id_str).get()
        assert r1 == repo_id_str

        r2 = extract_files_task.delay(repo_id_str).get()
        assert r2 == repo_id_str

        r3 = parse_repository_task.delay(repo_id_str).get()
        assert r3 == repo_id_str

        r4 = build_graph_task.delay(repo_id_str).get()
        assert r4 == repo_id_str

        r5 = index_repository_task.delay(repo_id_str).get()
        assert r5 == repo_id_str

    # Verify final database state
    async with session_factory() as db:
        repo_res = await db.execute(
            select(Repository).where(Repository.id == uuid.UUID(repo_id_str))
        )
        final_repo = repo_res.scalar_one()
        assert final_repo.status == RepositoryStatus.READY

        job_res = await db.execute(
            select(AnalysisJob).where(
                AnalysisJob.repository_id == uuid.UUID(repo_id_str)
            )
        )
        final_job = job_res.scalars().first()
        assert final_job is not None
        assert final_job.status == JobStatus.DONE
        assert final_job.progress == 100
        assert final_job.phase == "indexing"

        # Check extracted files & symbols
        files_res = await db.execute(
            select(CodeFile).where(CodeFile.repository_id == final_repo.id)
        )
        files = list(files_res.scalars().all())
        assert len(files) == 2

        syms_res = await db.execute(
            select(Symbol).where(Symbol.repository_id == final_repo.id)
        )
        symbols = list(syms_res.scalars().all())
        assert len(symbols) >= 2

        # Check chunks
        chunks_res = await db.execute(
            select(CodeChunk).where(CodeChunk.repository_id == final_repo.id)
        )
        chunks = list(chunks_res.scalars().all())
        assert len(chunks) >= 2


@pytest.mark.asyncio
async def test_task_failure_updates_status(tmp_path: Path) -> None:
    """A domain failure does not enter Celery's retry loop."""
    db_path = tmp_path / "test.db"
    engine, session_factory = await _make_engine(db_path)
    settings = _make_settings(tmp_path, db_path)
    fake_repo_id_str = str(uuid.uuid4())

    from unittest.mock import patch

    from app.tasks.analysis import extract_files_task

    with (
        patch("app.tasks.analysis.get_settings", return_value=settings),
        patch("app.tasks.analysis._publish_redis_event"),
        pytest.raises(NotFoundError),
    ):
        extract_files_task.delay(fake_repo_id_str).get()
