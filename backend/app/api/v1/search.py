"""Semantic search API router.

Exposes:
  POST /api/v1/repositories/{repo_id}/search
"""

from __future__ import annotations

import math
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.auth import get_current_key
from app.dependencies import get_app_settings, get_db
from app.exceptions import NotFoundError
from app.models.code_chunk import CodeChunk
from app.models.code_file import CodeFile
from app.schemas.search import SearchRequest, SearchResult
from app.services.embedding_service import get_embedding_provider
from app.services.ingestion import get_repository

router = APIRouter(
    prefix="/repositories", tags=["search"], dependencies=[Depends(get_current_key)]
)


def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


@router.post(
    "/{repo_id}/search",
    response_model=list[SearchResult],
    summary="Semantic vector search across repository code chunks",
    responses={
        404: {"description": "Repository not found"},
    },
)
async def search_repository(
    repo_id: uuid.UUID,
    search_req: SearchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> list[SearchResult]:
    """Perform a semantic vector similarity search for *search_req.query*.

    Embeds the user's natural language query using the configured embedding provider,
    executes vector similarity search over the repository's ``CodeChunk`` vectors,
    and returns ranked results.
    """
    # 1. Verify repository exists
    try:
        await get_repository(repo_id, db)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_id}' not found.",
        )

    # 2. Embed the query
    provider = get_embedding_provider(settings)
    query_embeddings = await provider.embed([search_req.query])
    if not query_embeddings:
        return []
    query_vec = query_embeddings[0]

    # 3. Query DB
    # Check dialect for PostgreSQL pgvector vs SQLite fallback
    dialect_name = db.bind.dialect.name if db.bind else "postgresql"

    if dialect_name == "postgresql":
        # pgvector cosine distance operator: embedding <=> query_vec
        # Cosine similarity score = 1.0 - distance
        dist_expr = CodeChunk.embedding.cosine_distance(query_vec)
        stmt = (
            select(CodeChunk, CodeFile, dist_expr.label("distance"))
            .join(CodeFile, CodeFile.id == CodeChunk.file_id)
            .where(CodeChunk.repository_id == repo_id)
            .order_by(dist_expr.asc())
            .limit(search_req.limit)
        )
        res = await db.execute(stmt)
        results: list[SearchResult] = []
        for chunk, code_file, distance in res.all():
            score = max(0.0, 1.0 - float(distance or 0.0))
            results.append(
                SearchResult(
                    chunk_id=str(chunk.id),
                    file_id=str(code_file.id),
                    path=code_file.path,
                    content=chunk.content,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    score=round(score, 4),
                    chunk_type=str(chunk.chunk_type),
                    symbol_id=str(chunk.symbol_id) if chunk.symbol_id else None,
                )
            )
        return results

    # Fallback for SQLite / non-PostgreSQL (in-memory test engine)
    stmt = (
        select(CodeChunk, CodeFile)
        .join(CodeFile, CodeFile.id == CodeChunk.file_id)
        .where(CodeChunk.repository_id == repo_id)
    )
    res = await db.execute(stmt)
    scored_items: list[tuple[float, CodeChunk, CodeFile]] = []
    for chunk, code_file in res.all():
        if chunk.embedding:
            score = _cosine_similarity(query_vec, chunk.embedding)
        else:
            score = 0.0
        scored_items.append((score, chunk, code_file))

    scored_items.sort(key=lambda item: item[0], reverse=True)
    top_k = scored_items[: search_req.limit]

    return [
        SearchResult(
            chunk_id=str(chunk.id),
            file_id=str(code_file.id),
            path=code_file.path,
            content=chunk.content,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            score=round(score, 4),
            chunk_type=str(chunk.chunk_type),
            symbol_id=str(chunk.symbol_id) if chunk.symbol_id else None,
        )
        for score, chunk, code_file in top_k
    ]
