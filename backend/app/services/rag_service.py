"""RAG (Retrieval-Augmented Generation) Service.

Orchestrates:
1. Question embedding and vector search over repository CodeChunks.
2. Multi-turn chat history assembly and prompt token-budget management.
3. Grounded LLM response generation with real-time SSE streaming.
4. Automatic persistence of user/assistant messages and cited source metadata.
"""

from __future__ import annotations

import json
import logging
import math
import uuid
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.llm import Message, get_llm_provider
from app.core.llm.prompts import SYSTEM_PROMPT, build_rag_prompt
from app.models.code_chunk import CodeChunk
from app.models.code_file import CodeFile
from app.models.symbol import Symbol
from app.services.chat_service import list_messages, save_message
from app.services.embedding_service import get_embedding_provider

logger = logging.getLogger(__name__)

DEFAULT_TOP_K: int = 8
MAX_HISTORY_TURNS: int = 6


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


async def retrieve_context_chunks(
    repo_id: uuid.UUID,
    question: str,
    db: AsyncSession,
    settings: Settings,
    top_k: int = DEFAULT_TOP_K,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Embed the question and retrieve top-K relevant CodeChunks.

    Returns:
        Tuple of (context_items, sources).
    """
    # Embed question
    provider = get_embedding_provider(settings)
    query_embeddings = await provider.embed([question])
    if not query_embeddings:
        return [], []
    query_vec = query_embeddings[0]

    dialect_name = db.bind.dialect.name if db.bind else "postgresql"

    chunks_with_files: list[tuple[CodeChunk, CodeFile]] = []
    if dialect_name == "postgresql":
        dist_expr = CodeChunk.embedding.cosine_distance(query_vec)
        stmt = (
            select(CodeChunk, CodeFile)
            .join(CodeFile, CodeFile.id == CodeChunk.file_id)
            .where(CodeChunk.repository_id == repo_id)
            .order_by(dist_expr.asc())
            .limit(top_k)
        )
        res = await db.execute(stmt)
        chunks_with_files = list(res.all())
    else:
        # SQLite fallback for unit tests
        stmt = (
            select(CodeChunk, CodeFile)
            .join(CodeFile, CodeFile.id == CodeChunk.file_id)
            .where(CodeChunk.repository_id == repo_id)
        )
        res = await db.execute(stmt)
        scored: list[tuple[float, CodeChunk, CodeFile]] = []
        for chunk, cf in res.all():
            sc = _cosine_similarity(query_vec, chunk.embedding or [])
            scored.append((sc, chunk, cf))
        scored.sort(key=lambda x: x[0], reverse=True)
        chunks_with_files = [(chunk, cf) for _, chunk, cf in scored[:top_k]]

    # Fetch symbol names if symbol_id is present
    symbol_ids = [c.symbol_id for c, _ in chunks_with_files if c.symbol_id]
    symbol_map: dict[uuid.UUID, str] = {}
    if symbol_ids:
        sym_res = await db.execute(select(Symbol).where(Symbol.id.in_(symbol_ids)))
        symbol_map = {s.id: s.name for s in sym_res.scalars().all()}

    context_items: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    seen_sources: set[tuple[str, int, int]] = set()

    for chunk, cf in chunks_with_files:
        sym_name = symbol_map.get(chunk.symbol_id) if chunk.symbol_id else None
        context_items.append({
            "file_path": cf.path,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "content": chunk.content,
            "symbol_name": sym_name,
        })

        src_key = (cf.path, chunk.start_line, chunk.end_line)
        if src_key not in seen_sources:
            seen_sources.add(src_key)
            sources.append({
                "path": cf.path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "symbol_name": sym_name,
            })

    return context_items, sources


async def stream_rag_answer(
    repo_id: uuid.UUID,
    session_id: uuid.UUID,
    question: str,
    db: AsyncSession,
    settings: Settings | None = None,
    top_k: int = DEFAULT_TOP_K,
) -> AsyncIterator[str]:
    """Generate an SSE-streamed RAG response grounded in code context.

    Yields SSE formatted strings:
    - ``data: <token>\n\n``
    - ``data: __sources__:<json>\n\n``
    - ``data: [DONE]\n\n``
    """
    if settings is None:
        settings = get_settings()

    # 1. Save user question message
    await save_message(session_id, role="user", content=question, db=db)

    # 2. Retrieve code context
    context_items, sources = await retrieve_context_chunks(
        repo_id=repo_id,
        question=question,
        db=db,
        settings=settings,
        top_k=top_k,
    )

    # 3. Fetch past conversation turns for multi-turn context
    past_messages = await list_messages(session_id, repo_id, db)
    # Take last MAX_HISTORY_TURNS excluding current question
    recent_history = [m for m in past_messages[:-1] if m.role in ("user", "assistant")][-MAX_HISTORY_TURNS:]

    # 4. Prepare LLM prompt
    llm = get_llm_provider(settings)
    rag_user_prompt = build_rag_prompt(question, context_items)

    messages_payload: list[Message] = [Message(role="system", content=SYSTEM_PROMPT)]
    for m in recent_history:
        messages_payload.append(Message(role=m.role, content=m.content))
    messages_payload.append(Message(role="user", content=rag_user_prompt))

    # Token budget trimming
    max_budget = int(llm.max_context_tokens * 0.7)
    total_tokens = sum(llm.count_tokens(m.content) for m in messages_payload)

    # Trim context if exceeding budget
    if total_tokens > max_budget and context_items:
        logger.info("Trimming context chunks to fit token budget (%d > %d)", total_tokens, max_budget)
        while len(context_items) > 1 and total_tokens > max_budget:
            context_items.pop()
            rag_user_prompt = build_rag_prompt(question, context_items)
            messages_payload[-1] = Message(role="user", content=rag_user_prompt)
            total_tokens = sum(llm.count_tokens(m.content) for m in messages_payload)

    # 5. Call LLM with streaming
    stream_response = await llm.chat(messages_payload, stream=True)

    accumulated_tokens: list[str] = []
    if isinstance(stream_response, AsyncIterator):
        async for token in stream_response:
            accumulated_tokens.append(token)
            yield f"data: {token}\n\n"
    else:
        # Fallback if provider returns a plain string
        accumulated_tokens.append(stream_response)
        yield f"data: {stream_response}\n\n"

    full_answer = "".join(accumulated_tokens)

    # 6. Save assistant answer with sources
    await save_message(
        session_id=session_id,
        role="assistant",
        content=full_answer,
        db=db,
        sources=sources,
    )

    # 7. Emit sources event and final [DONE] sentinel
    sources_json = json.dumps(sources)
    yield f"data: __sources__:{sources_json}\n\n"
    yield "data: [DONE]\n\n"
