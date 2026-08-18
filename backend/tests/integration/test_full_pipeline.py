"""PostgreSQL integration coverage for the eager repository analysis pipeline."""

import io
import uuid
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.config import EnvironmentType, Settings
from app.models.code_chunk import CodeChunk
from app.models.repository import Repository, RepositoryStatus
from app.models.repository_graph import RepositoryGraph
from app.models.symbol import Symbol
from app.services import ingestion
from app.tasks.analysis import (
    build_graph_task,
    extract_files_task,
    index_repository_task,
    ingest_repository_task,
    parse_repository_task,
)
from app.workers.celery_app import celery_app


def _sample_repository_zip() -> bytes:
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("sample_repo/calc.py", "def add(a, b):\n    return a + b\n")
        zip_file.writestr("sample_repo/utils.py", "from .calc import add\n")
    return archive.getvalue()


async def test_full_pipeline_reaches_ready_with_indexed_graph(
    integration_engine: AsyncEngine, tmp_path: Path
) -> None:
    """ZIP upload flows through every eager task into persisted graph and chunks."""
    session_factory = async_sessionmaker(
        integration_engine, class_=AsyncSession, expire_on_commit=False
    )
    settings = Settings(
        DATABASE_URL=str(integration_engine.url),
        REDIS_URL="redis://localhost:6379/15",
        SECRET_KEY="test-secret",
        LLM_API_KEY="test-key",
        UPLOAD_DIR=str(tmp_path),
        ENVIRONMENT=EnvironmentType.PRODUCTION,
    )
    vector = [0.0] * settings.EMBEDDING_DIM
    vector[0] = 1.0
    provider = AsyncMock()
    provider.embed.side_effect = lambda texts: [vector for _ in texts]
    previous_eager = celery_app.conf.task_always_eager
    previous_propagates = celery_app.conf.task_eager_propagates
    celery_app.conf.update(task_always_eager=True, task_eager_propagates=True)

    try:
        async with session_factory() as db:
            repository = await ingestion.ingest_zip_bytes(
                filename="sample_repo.zip",
                content=_sample_repository_zip(),
                db=db,
                settings=settings,
            )
            repository_id = str(repository.id)

        with (
            patch("app.tasks.analysis.get_settings", return_value=settings),
            patch("app.tasks.analysis._publish_redis_event"),
            patch("app.services.indexer.get_embedding_provider", return_value=provider),
        ):
            for task in (
                ingest_repository_task,
                extract_files_task,
                parse_repository_task,
                build_graph_task,
                index_repository_task,
            ):
                assert task.delay(repository_id).get() == repository_id
    finally:
        celery_app.conf.update(
            task_always_eager=previous_eager,
            task_eager_propagates=previous_propagates,
        )

    async with session_factory() as db:
        repo_id = uuid.UUID(repository_id)
        repository = await db.get(Repository, repo_id)
        assert repository is not None
        assert repository.status is RepositoryStatus.READY
        assert repository.file_count == 2
        assert len(list((await db.execute(select(Symbol))).scalars())) >= 1
        assert len(list((await db.execute(select(CodeChunk))).scalars())) >= 2
        graph = await db.scalar(
            select(RepositoryGraph).where(RepositoryGraph.repository_id == repo_id)
        )
        assert graph is not None
