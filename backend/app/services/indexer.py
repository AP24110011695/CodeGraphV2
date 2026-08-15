"""Repository vector indexing service.

Chunks non-binary source files, batch-embeds the text chunks using the configured
embedding provider, and populates CodeChunk rows with vector embeddings.
Updates AnalysisJob progress and sets Repository.status to "ready".
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.chunker import ChunkData, ChunkTypeValue, SymbolData, chunk_file
from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.code_chunk import ChunkType, CodeChunk
from app.models.code_file import CodeFile
from app.models.repository import Repository, RepositoryStatus
from app.models.symbol import Symbol
from app.services.embedding_service import get_embedding_provider

logger = logging.getLogger(__name__)

BATCH_INSERT_SIZE = 500


async def index_repository(
    repo: Repository,
    db: AsyncSession,
    settings: Settings | None = None,
    upload_dir: str = "./uploads",
) -> int:
    """Chunk, embed, and index all non-binary source files in a repository.

    Args:
        repo: Repository ORM instance.
        db: Async SQLAlchemy database session.
        settings: Application settings override (optional).
        upload_dir: Storage directory path for source files.

    Returns:
        Number of CodeChunk records created and inserted.
    """
    if settings is None:
        settings = get_settings()

    logger.info("Starting vector indexing for repository %s", repo.id)

    # 1. Update AnalysisJob & Repository status
    job_result = await db.execute(
        select(AnalysisJob).where(AnalysisJob.repository_id == repo.id)
    )
    job = job_result.scalar_one_or_none()
    if job:
        job.phase = "indexing"
        job.status = JobStatus.RUNNING
        job.progress = 80
        await db.flush()

    repo.status = RepositoryStatus.INDEXING
    await db.flush()

    # Clear pre-existing chunks for idempotency
    await db.execute(delete(CodeChunk).where(CodeChunk.repository_id == repo.id))
    await db.flush()

    # 2. Fetch CodeFile and Symbol rows
    files_result = await db.execute(
        select(CodeFile).where(
            CodeFile.repository_id == repo.id,
            CodeFile.is_binary == False,  # noqa: E712
        )
    )
    non_binary_files: list[CodeFile] = list(files_result.scalars().all())

    symbols_result = await db.execute(
        select(Symbol).where(Symbol.repository_id == repo.id)
    )
    all_symbols: list[Symbol] = list(symbols_result.scalars().all())

    # Map file_id -> list[SymbolData]
    file_symbols_map: dict[uuid.UUID, list[SymbolData]] = {}
    for sym in all_symbols:
        sdata = SymbolData(
            id=sym.id,
            name=sym.name,
            kind=str(sym.kind),
            start_line=sym.start_line,
            end_line=sym.end_line,
        )
        file_symbols_map.setdefault(sym.file_id, []).append(sdata)

    source_root = Path(upload_dir) / str(repo.id) / "source"

    # 3. Chunk files
    file_chunk_pairs: list[tuple[CodeFile, ChunkData]] = []
    for code_file in non_binary_files:
        abs_path = source_root / code_file.path
        if not abs_path.is_file():
            continue

        try:
            source_text = abs_path.read_text(encoding="utf-8", errors="replace")
        except Exception as err:
            logger.warning("Could not read file %s for chunking: %s", code_file.path, err)
            continue

        file_syms = file_symbols_map.get(code_file.id, [])
        chunks = chunk_file(code_file.path, source_text, file_syms)

        for chunk_data in chunks:
            file_chunk_pairs.append((code_file, chunk_data))

    if not file_chunk_pairs:
        logger.info("No chunks produced for repo %s", repo.id)
        repo.status = RepositoryStatus.READY
        if job:
            job.progress = 100
            job.status = JobStatus.DONE
        await db.commit()
        await db.refresh(repo)
        return 0

    # 4. Generate embeddings
    texts_to_embed = [cd.content for _, cd in file_chunk_pairs]
    embeddings: list[list[float]] = []
    if texts_to_embed:
        try:
            provider = get_embedding_provider(settings)
            embeddings = await provider.embed(texts_to_embed)
        except Exception as err:
            logger.warning(
                "Embedding generation failed for repo %s (%s); defaulting to zero vectors.",
                repo.id,
                err,
            )
            embeddings = [[0.0] * settings.EMBEDDING_DIM for _ in texts_to_embed]

    # 5. Build and bulk insert CodeChunk records
    chunks_to_insert: list[CodeChunk] = []
    for (code_file, chunk_data), embedding_vec in zip(file_chunk_pairs, embeddings):
        chunk_type_enum = (
            ChunkType.SYMBOL
            if chunk_data.chunk_type == ChunkTypeValue.SYMBOL
            else ChunkType.BLOCK
        )
        cc = CodeChunk(
            id=uuid.uuid4(),
            file_id=code_file.id,
            repository_id=repo.id,
            content=chunk_data.content,
            start_line=chunk_data.start_line,
            end_line=chunk_data.end_line,
            chunk_type=chunk_type_enum,
            symbol_id=chunk_data.symbol_id,
            embedding=embedding_vec,
        )
        chunks_to_insert.append(cc)

    total_chunks = len(chunks_to_insert)
    for i in range(0, total_chunks, BATCH_INSERT_SIZE):
        batch = chunks_to_insert[i : i + BATCH_INSERT_SIZE]
        db.add_all(batch)
        await db.flush()

        if job:
            job.progress = min(99, 80 + int(20 * (i + len(batch)) / total_chunks))
            await db.flush()

    # 6. Finalize statuses
    repo.status = RepositoryStatus.READY
    if job:
        job.progress = 100
        job.status = JobStatus.DONE

    await db.commit()
    await db.refresh(repo)

    logger.info(
        "Successfully indexed %d chunks for repository %s", total_chunks, repo.id
    )
    return total_chunks
