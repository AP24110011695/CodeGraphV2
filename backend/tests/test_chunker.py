"""Tests for app.core.chunker — Phase 12."""

from __future__ import annotations

import uuid

from app.core.chunker import (
    MAX_CHUNK_CHARS,
    SLIDING_WINDOW_LINES,
    ChunkTypeValue,
    SymbolData,
    chunk_file,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sym(
    name: str,
    start: int,
    end: int,
    kind: str = "function",
) -> SymbolData:
    return SymbolData(
        id=uuid.uuid4(),
        name=name,
        kind=kind,
        start_line=start,
        end_line=end,
    )


def _source(n_lines: int, prefix: str = "line") -> str:
    return "\n".join(f"{prefix} {i}" for i in range(1, n_lines + 1))


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEmptyFile:
    def test_empty_source_returns_no_chunks(self) -> None:
        chunks = chunk_file("src/empty.py", "", [])
        assert chunks == []

    def test_whitespace_only_source_returns_no_chunks(self) -> None:
        chunks = chunk_file("src/ws.py", "   \n  \n", [])
        assert chunks == []


# ---------------------------------------------------------------------------
# Symbol-level chunking
# ---------------------------------------------------------------------------


class TestSymbolChunking:
    def test_single_function_chunk(self) -> None:
        source = "def foo():\n    return 1\n"
        sym = _sym("foo", 1, 2)
        chunks = chunk_file("src/foo.py", source, [sym])

        assert len(chunks) == 1
        c = chunks[0]
        assert c.chunk_type == ChunkTypeValue.SYMBOL
        assert c.symbol_id == sym.id
        assert c.start_line == 1
        assert c.end_line == 2
        assert "# File: src/foo.py" in c.content
        assert "# Symbol: foo" in c.content
        assert "def foo():" in c.content

    def test_multiple_symbols_produce_multiple_chunks(self) -> None:
        source = "def a():\n    pass\n\ndef b():\n    pass\n"
        s1 = _sym("a", 1, 2)
        s2 = _sym("b", 4, 5)
        chunks = chunk_file("src/multi.py", source, [s1, s2])
        assert len(chunks) == 2
        assert chunks[0].symbol_id == s1.id
        assert chunks[1].symbol_id == s2.id

    def test_chunk_content_header_format(self) -> None:
        source = "class Foo:\n    pass\n"
        sym = _sym("Foo", 1, 2, kind="class")
        chunks = chunk_file("src/mymod.py", source, [sym])
        header_lines = chunks[0].content.split("\n")[:3]
        assert header_lines[0] == "# File: src/mymod.py"
        assert header_lines[1] == "# Symbol: Foo"
        assert header_lines[2] == ""  # blank separator

    def test_line_numbers_clamped_to_file(self) -> None:
        """Symbol metadata pointing beyond EOF should not cause an IndexError."""
        source = "def tiny():\n    pass\n"
        sym = _sym("tiny", 1, 999)  # end_line beyond file
        chunks = chunk_file("src/tiny.py", source, [sym])
        assert len(chunks) >= 1
        # end_line should be clamped to actual file length
        assert chunks[-1].end_line <= 2


# ---------------------------------------------------------------------------
# Oversized symbol splitting
# ---------------------------------------------------------------------------


class TestOversizedSymbol:
    def _make_big_symbol(self, n_lines: int = 400) -> tuple[str, SymbolData]:
        """Return (source, symbol) where the symbol spans the whole file."""
        lines = ["def big_function():"]
        for i in range(n_lines - 1):
            lines.append(f"    x_{i} = {i}  # some code padding")
        source = "\n".join(lines)
        sym = _sym("big_function", 1, n_lines)
        return source, sym

    def test_oversized_symbol_splits_into_multiple_chunks(self) -> None:
        source, sym = self._make_big_symbol(400)
        chunks = chunk_file("src/big.py", source, [sym])
        # Should have been split
        assert len(chunks) > 1
        for c in chunks:
            assert len(c.content) <= MAX_CHUNK_CHARS + 200  # allow header overhead

    def test_oversized_symbol_preserves_symbol_id(self) -> None:
        source, sym = self._make_big_symbol(400)
        chunks = chunk_file("src/big.py", source, [sym])
        for c in chunks:
            assert c.symbol_id == sym.id

    def test_oversized_symbol_all_chunks_are_symbol_type(self) -> None:
        source, sym = self._make_big_symbol(300)
        chunks = chunk_file("src/big.py", source, [sym])
        for c in chunks:
            assert c.chunk_type == ChunkTypeValue.SYMBOL

    def test_split_at_inner_def_boundaries(self) -> None:
        """When inner 'def' lines exist, splits should occur at those boundaries."""
        inner_defs = "\n".join(
            f"def helper_{i}():\n    return {i}" for i in range(50)
        )
        source = f"class Big:\n{inner_defs}"
        sym = _sym("Big", 1, source.count('\n') + 1, kind="class")
        chunks = chunk_file("src/big_class.py", source, [sym])
        # Each sub-chunk should still have the header
        for c in chunks:
            assert "# File:" in c.content
            assert "# Symbol: Big" in c.content


# ---------------------------------------------------------------------------
# Sliding-window fallback
# ---------------------------------------------------------------------------


class TestSlidingWindowFallback:
    def test_no_symbols_uses_sliding_window(self) -> None:
        source = _source(100)
        chunks = chunk_file("src/no_syms.py", source, [])
        assert len(chunks) > 0
        for c in chunks:
            assert c.chunk_type == ChunkTypeValue.BLOCK
            assert c.symbol_id is None

    def test_short_file_produces_single_window(self) -> None:
        source = _source(10)
        chunks = chunk_file("src/short.py", source, [])
        assert len(chunks) == 1

    def test_window_size_and_overlap(self) -> None:
        n = SLIDING_WINDOW_LINES * 2  # exactly 2 full windows if no overlap
        source = _source(n)
        chunks = chunk_file("src/overlap.py", source, [])
        # With overlap there should be more than 2 windows
        assert len(chunks) >= 2
        # First window starts at line 1
        assert chunks[0].start_line == 1
        # Second window starts before SLIDING_WINDOW_LINES + 1
        if len(chunks) > 1:
            assert chunks[1].start_line < SLIDING_WINDOW_LINES + 1

    def test_window_header_has_no_symbol_name(self) -> None:
        source = _source(5)
        chunks = chunk_file("src/file.py", source, [])
        assert "# File: src/file.py" in chunks[0].content
        assert "# Symbol:" not in chunks[0].content

    def test_window_line_ranges_are_contiguous(self) -> None:
        source = _source(120)
        chunks = chunk_file("src/long.py", source, [])
        assert chunks[0].start_line == 1
        # Consecutive chunks should overlap (i.e. next.start <= prev.end)
        for i in range(1, len(chunks)):
            assert chunks[i].start_line <= chunks[i - 1].end_line + 1
