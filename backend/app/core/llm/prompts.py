"""Prompt management and templates for CodeGraph v2 RAG pipeline."""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT: str = """You are CodeGraph AI, an expert software architecture and codebase intelligence assistant.

Your task is to answer user questions about a codebase accurately, concisely, and strictly grounded in the provided code context.

RULES & DIRECTIVES:
1. Grounding: Base your answer STRICTLY on the retrieved code context blocks provided below. Do not invent code details, functions, or architectural decisions not supported by the context.
2. Insufficient Context: If the provided code context does not contain enough information to answer the question, state clearly: "I don't know based on the provided codebase context."
3. Citations: Explicitly cite source files and line ranges in your answer whenever referencing specific implementations or files (e.g., `[src/auth.py:L10-L45]`).
4. Tone & Style: Be direct, clear, and technical. Use GitHub-flavored markdown code blocks with appropriate language syntax highlighting for code snippets.
"""

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

CONTEXT_BLOCK_TEMPLATE: str = """---
[Context Item #{index}]
File: {file_path} (Lines {start_line}-{end_line})
{symbol_info}Content:
```
{content}
```
"""

RAG_USER_PROMPT_TEMPLATE: str = """Retrieved Codebase Context:
==========================
{context_text}

==========================
User Question: {question}

Answer:"""


# ---------------------------------------------------------------------------
# Formatting Helpers
# ---------------------------------------------------------------------------


def format_context_block(
    index: int,
    file_path: str,
    start_line: int,
    end_line: int,
    content: str,
    symbol_name: str | None = None,
) -> str:
    """Format a single code chunk into a standardized context block."""
    symbol_info = f"Symbol: {symbol_name}\n" if symbol_name else ""
    return CONTEXT_BLOCK_TEMPLATE.format(
        index=index,
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        symbol_info=symbol_info,
        content=content.strip(),
    )


def build_rag_prompt(
    question: str,
    context_items: list[dict[str, Any]],
) -> str:
    """Combine retrieved context items and user question into a formatted prompt.

    Args:
        question: User query string.
        context_items: List of dicts with keys: file_path, start_line, end_line, content, optional symbol_name.

    Returns:
        Formatted prompt text string.
    """
    if not context_items:
        context_text = "No relevant codebase context found."
    else:
        blocks = []
        for idx, item in enumerate(context_items, start=1):
            block = format_context_block(
                index=idx,
                file_path=item.get("file_path", item.get("path", "unknown")),
                start_line=item.get("start_line", 1),
                end_line=item.get("end_line", 1),
                content=item.get("content", ""),
                symbol_name=item.get("symbol_name"),
            )
            blocks.append(block)
        context_text = "\n".join(blocks)

    return RAG_USER_PROMPT_TEMPLATE.format(
        context_text=context_text,
        question=question,
    )
