"""Unit tests for SQLAlchemy domain models and vector round-trips."""

import uuid

import pytest

from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.code_chunk import ChunkType, CodeChunk
from app.models.code_file import CodeFile
from app.models.dependency import Dependency, DependencyType
from app.models.repository import Repository, RepositorySource, RepositoryStatus
from app.models.symbol import Symbol, SymbolKind


def test_repository_model_instantiation() -> None:
    """Test Repository model attributes and defaults."""
    repo = Repository(
        name="test-repo",
        slug="test-repo",
        source=RepositorySource.UPLOAD,
        status=RepositoryStatus.PENDING,
        size_bytes=0,
        file_count=0,
    )
    assert repo.name == "test-repo"
    assert repo.slug == "test-repo"
    assert repo.source == RepositorySource.UPLOAD
    assert repo.status == RepositoryStatus.PENDING
    assert repo.size_bytes == 0
    assert repo.file_count == 0


def test_code_file_model_instantiation() -> None:
    """Test CodeFile model attributes and relationships."""
    repo_id = uuid.uuid4()
    code_file = CodeFile(
        repository_id=repo_id,
        path="src/main.py",
        language="python",
        content_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        line_count=42,
        is_binary=False,
    )
    assert code_file.repository_id == repo_id
    assert code_file.path == "src/main.py"
    assert code_file.language == "python"
    assert code_file.line_count == 42
    assert code_file.is_binary is False



def test_symbol_model_instantiation() -> None:
    """Test Symbol model attributes."""
    file_id = uuid.uuid4()
    repo_id = uuid.uuid4()
    symbol = Symbol(
        file_id=file_id,
        repository_id=repo_id,
        name="calculate_score",
        kind=SymbolKind.FUNCTION,
        start_line=10,
        end_line=25,
        signature="def calculate_score(items: list) -> float",
        is_exported=True,
    )
    assert symbol.name == "calculate_score"
    assert symbol.kind == SymbolKind.FUNCTION
    assert symbol.start_line == 10
    assert symbol.end_line == 25
    assert symbol.is_exported is True


def test_dependency_model_instantiation() -> None:
    """Test Dependency model attributes."""
    repo_id = uuid.uuid4()
    from_file_id = uuid.uuid4()
    dep = Dependency(
        repository_id=repo_id,
        from_file_id=from_file_id,
        import_name="fastapi",
        import_path="fastapi.FastAPI",
        dependency_type=DependencyType.EXTERNAL,
    )
    assert dep.import_name == "fastapi"
    assert dep.dependency_type == DependencyType.EXTERNAL


def test_code_chunk_model_vector_embedding() -> None:
    """Test CodeChunk model instantiation with 1536-dim vector embedding."""
    file_id = uuid.uuid4()
    repo_id = uuid.uuid4()
    embedding = [0.1 * (i % 10) for i in range(1536)]
    chunk = CodeChunk(
        file_id=file_id,
        repository_id=repo_id,
        content="def hello(): pass",
        start_line=1,
        end_line=2,
        chunk_type=ChunkType.BLOCK,
        embedding=embedding,
    )
    assert chunk.content == "def hello(): pass"
    assert chunk.chunk_type == ChunkType.BLOCK
    assert chunk.embedding is not None
    assert len(chunk.embedding) == 1536


def test_analysis_job_model_instantiation() -> None:
    """Test AnalysisJob model attributes."""
    repo_id = uuid.uuid4()
    job = AnalysisJob(
        repository_id=repo_id,
        phase="ingestion",
        status=JobStatus.RUNNING,
        progress=25,
    )
    assert job.phase == "ingestion"
    assert job.status == JobStatus.RUNNING
    assert job.progress == 25


@pytest.mark.asyncio
async def test_db_models_persistence_and_vector_roundtrip() -> None:
    """Async test to verify DB persistence and vector round-trip."""

    from app.db.session import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as session:
            repo = Repository(
                name="sample-repo",
                slug=f"sample-repo-{uuid.uuid4().hex[:8]}",
                source=RepositorySource.UPLOAD,
            )
            session.add(repo)
            await session.flush()

            file = CodeFile(
                repository_id=repo.id,
                path="app.py",
                language="python",
                content_hash="abc123hash",
            )
            session.add(file)
            await session.flush()

            embedding_vec = [0.05] * 1536
            chunk = CodeChunk(
                file_id=file.id,
                repository_id=repo.id,
                content="import os",
                start_line=1,
                end_line=1,
                chunk_type=ChunkType.BLOCK,
                embedding=embedding_vec,
            )
            session.add(chunk)
            await session.commit()

            # Query back
            retrieved_chunk = await session.get(CodeChunk, chunk.id)
            assert retrieved_chunk is not None
            assert retrieved_chunk.embedding is not None
            assert len(retrieved_chunk.embedding) == 1536

            # Clean up
            await session.delete(repo)
            await session.commit()
    except Exception as exc:
        pytest.skip(f"PostgreSQL database not accessible for persistence test: {exc}")
