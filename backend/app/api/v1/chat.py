"""Chat API router.

Exposes:
  POST /api/v1/repositories/{repo_id}/chat/sessions
  GET  /api/v1/repositories/{repo_id}/chat/sessions/{session_id}
  POST /api/v1/repositories/{repo_id}/chat/sessions/{session_id}/messages
  GET  /api/v1/repositories/{repo_id}/chat/sessions/{session_id}/messages
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.core.auth import get_current_key
from app.core.rate_limiter import limiter
from app.dependencies import get_app_settings, get_db
from app.exceptions import NotFoundError
from app.schemas.chat import (
    ChatMessageResponse,
    ChatSessionResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    SendMessageRequest,
)
from app.services import chat_service
from app.services.ingestion import get_repository
from app.services.rag_service import stream_rag_answer

router = APIRouter(
    prefix="/repositories", tags=["chat"], dependencies=[Depends(get_current_key)]
)


@router.post(
    "/{repo_id}/chat/sessions",
    response_model=CreateSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat session for a repository",
    responses={
        404: {"description": "Repository not found"},
    },
)
async def create_chat_session(
    repo_id: uuid.UUID,
    req: CreateSessionRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CreateSessionResponse:
    """Create a new multi-turn chat session bound to *repo_id*."""
    try:
        await get_repository(repo_id, db)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_id}' not found.",
        )

    session = await chat_service.create_session(repo_id, db, title=req.title)
    return CreateSessionResponse(session_id=session.id)


@router.get(
    "/{repo_id}/chat/sessions/{session_id}",
    response_model=ChatSessionResponse,
    summary="Get chat session detail",
    responses={
        404: {"description": "Repository or chat session not found"},
    },
)
async def get_chat_session_detail(
    repo_id: uuid.UUID,
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChatSessionResponse:
    """Get metadata for a specific chat session."""
    try:
        await get_repository(repo_id, db)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_id}' not found.",
        )

    session = await chat_service.get_session(session_id, repo_id, db)
    return ChatSessionResponse.model_validate(session)


@router.post(
    "/{repo_id}/chat/sessions/{session_id}/messages",
    summary="Send a question and stream grounded RAG answer (SSE)",
    responses={
        200: {
            "description": "SSE Event stream with data tokens, sources, and [DONE] sentinel.",
            "content": {"text/event-stream": {}},
        },
        404: {"description": "Repository or chat session not found"},
    },
)
@limiter.limit("60/hour")
async def send_chat_message(
    request: Request,
    repo_id: uuid.UUID,
    session_id: uuid.UUID,
    msg_req: SendMessageRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> StreamingResponse:
    """Send a user question in *session_id* and receive a streamed SSE RAG response."""
    try:
        await get_repository(repo_id, db)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_id}' not found.",
        )

    # Verify session exists
    await chat_service.get_session(session_id, repo_id, db)

    event_generator = stream_rag_answer(
        repo_id=repo_id,
        session_id=session_id,
        question=msg_req.question,
        db=db,
        settings=settings,
    )

    return StreamingResponse(
        event_generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/{repo_id}/chat/sessions/{session_id}/messages",
    response_model=list[ChatMessageResponse],
    summary="Get conversation history for a chat session",
    responses={
        404: {"description": "Repository or chat session not found"},
    },
)
async def get_chat_history(
    repo_id: uuid.UUID,
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ChatMessageResponse]:
    """Retrieve all historical messages and grounded source citations for a session."""
    try:
        await get_repository(repo_id, db)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_id}' not found.",
        )

    messages = await chat_service.list_messages(session_id, repo_id, db)
    return [ChatMessageResponse.model_validate(m) for m in messages]
