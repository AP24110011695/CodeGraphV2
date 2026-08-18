"""Additional edge-case coverage for the pure chunking algorithm."""

import uuid

from app.core.chunker import MAX_CHUNK_CHARS, ChunkTypeValue, SymbolData, chunk_file


def test_huge_symbol_without_inner_definitions_uses_bounded_chunks() -> None:
    """A huge function falls back to fixed-size chunks when no split point exists."""
    source = "def enormous():\n" + "    value = 'padding' * 10\n" * 600
    symbol = SymbolData(uuid.uuid4(), "enormous", "function", 1, 601)
    chunks = chunk_file("src/huge.py", source, [symbol])

    assert len(chunks) > 1
    assert all(chunk.chunk_type is ChunkTypeValue.SYMBOL for chunk in chunks)
    assert all(len(chunk.content) <= MAX_CHUNK_CHARS + 200 for chunk in chunks)


def test_no_symbols_preserves_first_and_last_line_in_windows() -> None:
    """Sliding windows cover the whole file even when the source has no symbols."""
    source = "\n".join(f"line-{number}" for number in range(1, 140))
    chunks = chunk_file("README.txt", source, [])

    assert chunks[0].start_line == 1
    assert chunks[-1].end_line == 139
    assert all(chunk.chunk_type is ChunkTypeValue.BLOCK for chunk in chunks)
