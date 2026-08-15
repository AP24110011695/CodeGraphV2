"""Code chunker for preparing source files for vector embedding.

Strategy
--------
1. **Symbol-level chunks** (preferred): one chunk per extracted Symbol
   (function / class / method / …) containing the full source lines for that
   symbol.  The chunk is prefixed with file-path and symbol-name context lines
   so that embeddings are location-aware.

2. **Sliding-window fallback**: for files with no extracted symbols the file
   is split into 50-line windows with 10-line overlap.

3. **Oversized symbols**: if a single symbol's source exceeds *MAX_CHUNK_CHARS*
   (8 000 characters) it is split further at inner function/class definition
   boundaries (lines starting with ``def `` or ``class `` after stripping) or,
   failing that, every 100 lines.

Each produced ``ChunkData`` carries enough information to create a ``CodeChunk``
row (content, line range, chunk_type, optional symbol_id) without touching the
database.

This module is **intentionally** pure-Python and stateless — no DB, no async.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum

# ---------------------------------------------------------------------------
# Public data structures
# ---------------------------------------------------------------------------


class ChunkTypeValue(StrEnum):
    """Mirrors CodeChunk.ChunkType without importing the ORM."""

    SYMBOL = "symbol"
    BLOCK = "block"


@dataclass(slots=True)
class SymbolData:
    """Minimal symbol descriptor used by the chunker (decoupled from ORM)."""

    id: uuid.UUID
    name: str
    kind: str
    start_line: int  # 1-indexed, inclusive
    end_line: int  # 1-indexed, inclusive


@dataclass(slots=True)
class ChunkData:
    """A single embeddable chunk produced by the chunker."""

    content: str
    start_line: int  # 1-indexed, inclusive
    end_line: int  # 1-indexed, inclusive
    chunk_type: ChunkTypeValue
    symbol_id: uuid.UUID | None = None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_CHUNK_CHARS: int = 8_000
SLIDING_WINDOW_LINES: int = 50
SLIDING_OVERLAP_LINES: int = 10
OVERSIZED_SPLIT_LINES: int = 100

# Lines whose stripped content starts with these tokens are considered logical
# split points when breaking oversized symbol chunks.
_SPLIT_TOKENS = ("def ", "async def ", "class ")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _make_header(file_path: str, symbol_name: str | None = None) -> str:
    """Return the context prefix prepended to every chunk."""
    lines = [f"# File: {file_path}"]
    if symbol_name:
        lines.append(f"# Symbol: {symbol_name}")
    lines.append("")
    lines.append("")  # blank line separating header from code
    return "\n".join(lines)


def _split_oversized(
    lines: list[str],
    start_line: int,
    file_path: str,
    symbol_name: str,
    symbol_id: uuid.UUID,
) -> list[ChunkData]:
    """Split a too-large symbol into sub-chunks.

    Tries to break at inner definition boundaries first; falls back to
    splitting every OVERSIZED_SPLIT_LINES lines.
    """
    # Collect logical split indices (relative to `lines`)
    split_indices: list[int] = [0]
    for i, raw_line in enumerate(lines):
        if i == 0:
            continue  # never split at the very first line
        stripped = raw_line.lstrip()
        if any(stripped.startswith(tok) for tok in _SPLIT_TOKENS):
            split_indices.append(i)

    # If no logical breaks exist (or only one), fall back to fixed-size splits
    if len(split_indices) <= 1:
        split_indices = list(range(0, len(lines), OVERSIZED_SPLIT_LINES))
        if not split_indices or split_indices[0] != 0:
            split_indices.insert(0, 0)

    split_indices.append(len(lines))  # sentinel

    chunks: list[ChunkData] = []
    for idx in range(len(split_indices) - 1):
        seg_start = split_indices[idx]
        seg_end = split_indices[idx + 1]
        seg_lines = lines[seg_start:seg_end]
        if not seg_lines:
            continue
        header = _make_header(file_path, symbol_name)
        content = header + "\n".join(seg_lines)
        abs_start = start_line + seg_start
        abs_end = start_line + seg_end - 1
        chunks.append(
            ChunkData(
                content=content,
                start_line=abs_start,
                end_line=abs_end,
                chunk_type=ChunkTypeValue.SYMBOL,
                symbol_id=symbol_id,
            )
        )
    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def chunk_file(
    file_path: str,
    source: str,
    symbols: list[SymbolData],
) -> list[ChunkData]:
    """Produce embeddable chunks for a single source file.

    Args:
        file_path: Repository-relative path (used in the chunk header).
        source: Full source text of the file.
        symbols: Extracted symbol descriptors for this file.

    Returns:
        Ordered list of ``ChunkData`` ready for embedding.
    """
    if not source.strip():
        return []

    all_lines: list[str] = source.splitlines()
    total_lines = len(all_lines)

    # ---- Symbol-level strategy -------------------------------------------
    if symbols:
        chunks: list[ChunkData] = []
        for sym in symbols:
            # Clamp to actual file length (graceful handling of metadata errors)
            s = max(1, sym.start_line)
            e = min(total_lines, sym.end_line)
            sym_lines = all_lines[s - 1 : e]  # 0-indexed slice

            header = _make_header(file_path, sym.name)
            content = header + "\n".join(sym_lines)

            if len(content) <= MAX_CHUNK_CHARS:
                chunks.append(
                    ChunkData(
                        content=content,
                        start_line=s,
                        end_line=e,
                        chunk_type=ChunkTypeValue.SYMBOL,
                        symbol_id=sym.id,
                    )
                )
            else:
                # Symbol is too large — split it
                sub = _split_oversized(sym_lines, s, file_path, sym.name, sym.id)
                chunks.extend(sub)
        return chunks

    # ---- Sliding-window fallback -----------------------------------------
    chunks = []
    pos = 0
    while pos < total_lines:
        window_lines = all_lines[pos : pos + SLIDING_WINDOW_LINES]
        header = _make_header(file_path)
        content = header + "\n".join(window_lines)
        start_line = pos + 1
        end_line = pos + len(window_lines)
        chunks.append(
            ChunkData(
                content=content,
                start_line=start_line,
                end_line=end_line,
                chunk_type=ChunkTypeValue.BLOCK,
                symbol_id=None,
            )
        )
        pos += SLIDING_WINDOW_LINES - SLIDING_OVERLAP_LINES
        if pos >= total_lines:
            break

    return chunks
