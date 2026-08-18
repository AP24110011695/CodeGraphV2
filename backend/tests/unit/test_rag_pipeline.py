"""Service-free RAG streaming tests using mocked persistence and providers."""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

from app.config import Settings
from app.services.rag_service import stream_rag_answer


async def _tokens() -> AsyncIterator[str]:
    yield "short "
    yield "answer"


async def test_rag_trims_context_and_emits_sources() -> None:
    """Context trimming preserves sources and the done sentinel."""
    contexts = [
        {"file_path": "one.py", "start_line": 1, "end_line": 2, "content": "x" * 400},
        {"file_path": "two.py", "start_line": 1, "end_line": 2, "content": "y" * 400},
    ]
    sources = [{"path": "one.py", "start_line": 1, "end_line": 2}]
    llm = MagicMock(max_context_tokens=100, model_name="test-model")
    llm.count_tokens.side_effect = lambda value: len(value) // 4
    llm.chat = AsyncMock(return_value=_tokens())

    with (
        patch("app.services.rag_service.save_message", new=AsyncMock()),
        patch(
            "app.services.rag_service.retrieve_context_chunks",
            new=AsyncMock(return_value=(contexts, sources)),
        ),
        patch("app.services.rag_service.list_messages", new=AsyncMock(return_value=[])),
        patch("app.services.rag_service.get_llm_provider", return_value=llm),
    ):
        events = [
            event
            async for event in stream_rag_answer(
                repo_id=MagicMock(),
                session_id=MagicMock(),
                question="What does this do?",
                db=MagicMock(),
                settings=Settings(SECRET_KEY="test", LLM_API_KEY="test"),
            )
        ]

    request_messages = llm.chat.await_args.args[0]
    assert "two.py" not in request_messages[-1].content
    assert events == [
        "data: short \n\n",
        "data: answer\n\n",
        'data: __sources__:[{"path": "one.py", "start_line": 1, "end_line": 2}]\n\n',
        "data: [DONE]\n\n",
    ]
