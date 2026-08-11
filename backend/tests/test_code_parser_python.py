"""Tests for Python AST parser, generic parser, and code_parser service."""

import uuid
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.parsers.generic_parser import GenericParser
from app.core.parsers.python_parser import PythonParser
from app.db.base import Base
from app.models.code_file import CodeFile
from app.models.repository import Repository, RepositorySource, RepositoryStatus
from app.models.symbol import Symbol
from app.services.code_parser import parse_repository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_PY = FIXTURES_DIR / "sample.py"


async def _create_engine() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    return engine, factory


def _make_code_file(path: str = "sample.py", language: str = "Python") -> CodeFile:
    return CodeFile(
        id=uuid.uuid4(),
        repository_id=uuid.uuid4(),
        path=path,
        language=language,
        size_bytes=100,
        content_hash="abc123hash",
        line_count=20,
        is_binary=False,
    )


# ---------------------------------------------------------------------------
# PythonParser Unit Tests
# ---------------------------------------------------------------------------


def test_python_parser_extracts_functions() -> None:
    """PythonParser should extract functions with correct signatures and docstrings."""
    cf = _make_code_file()
    parser = PythonParser()
    res = parser.parse(SAMPLE_PY, cf)

    assert res.error is None
    names = [s.name for s in res.symbols]
    assert "add" in names
    assert "fetch_data" in names

    add_sym = next(s for s in res.symbols if s.name == "add")
    assert add_sym.kind == "function"
    assert add_sym.docstring == "Add two numbers."
    assert "def add(" in (add_sym.signature or "")
    assert add_sym.is_exported is True


def test_python_parser_extracts_class_and_methods() -> None:
    """PythonParser should extract class and its methods."""
    cf = _make_code_file()
    parser = PythonParser()
    res = parser.parse(SAMPLE_PY, cf)

    calc_sym = next((s for s in res.symbols if s.name == "Calculator"), None)
    assert calc_sym is not None
    assert calc_sym.kind == "class"
    assert calc_sym.docstring == "A simple calculator class."

    method_names = [s.name for s in res.symbols if s.kind == "method"]
    assert "Calculator.__init__" in method_names
    assert "Calculator.multiply" in method_names

    mult_sym = next(s for s in res.symbols if s.name == "Calculator.multiply")
    assert mult_sym.docstring == "Multiply current value."


def test_python_parser_detects_private_symbols() -> None:
    """Symbols starting with _ should be marked is_exported=False unless in __all__."""
    cf = _make_code_file()
    parser = PythonParser()
    res = parser.parse(SAMPLE_PY, cf)

    helper_sym = next(s for s in res.symbols if s.name == "_internal_helper")
    assert helper_sym.is_exported is False


def test_python_parser_extracts_imports() -> None:
    """PythonParser should extract import statements."""
    cf = _make_code_file()
    parser = PythonParser()
    res = parser.parse(SAMPLE_PY, cf)

    import_paths = [i.import_path for i in res.imports]
    assert "os" in import_paths
    assert "typing.Any" in import_paths


def test_python_parser_handles_syntax_error(tmp_path: Path) -> None:
    """PythonParser should return error on invalid syntax without raising."""
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("def broken_func(:", encoding="utf-8")

    cf = _make_code_file(path="bad.py")
    parser = PythonParser()
    res = parser.parse(bad_file, cf)

    assert res.error is not None
    assert "SyntaxError" in res.error
    assert len(res.symbols) == 0


# ---------------------------------------------------------------------------
# GenericParser Unit Tests
# ---------------------------------------------------------------------------


def test_generic_parser_returns_empty_result(tmp_path: Path) -> None:
    """GenericParser should return empty symbols and imports for unsupported files."""
    txt_file = tmp_path / "data.txt"
    txt_file.write_text("random text line 1\nrandom text line 2", encoding="utf-8")

    cf = _make_code_file(path="data.txt", language="Text")
    parser = GenericParser()
    res = parser.parse(txt_file, cf)

    assert res.error is None
    assert len(res.symbols) == 0
    assert len(res.imports) == 0


# ---------------------------------------------------------------------------
# parse_repository Integration Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parse_repository_inserts_symbols(tmp_path: Path) -> None:
    """parse_repository should populate Symbol rows for python files."""
    engine, factory = await _create_engine()

    async with factory() as session:
        repo_id = uuid.uuid4()
        repo = Repository(
            id=repo_id,
            name="test-repo",
            slug=f"test-repo-{str(repo_id)[:8]}",
            source=RepositorySource.UPLOAD,
            status=RepositoryStatus.PARSING,
            size_bytes=1000,
            file_count=1,
        )
        session.add(repo)
        await session.commit()
        await session.refresh(repo)

        # Setup source tree
        source_dir = tmp_path / "uploads" / str(repo_id) / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "sample.py").write_text(SAMPLE_PY.read_text(encoding="utf-8"))

        code_file = CodeFile(
            id=uuid.uuid4(),
            repository_id=repo.id,
            path="sample.py",
            language="Python",
            size_bytes=500,
            content_hash="hash123",
            line_count=25,
            is_binary=False,
        )
        session.add(code_file)
        await session.commit()
        await session.refresh(code_file)

        symbols = await parse_repository(
            repo, [code_file], session, upload_dir=str(tmp_path / "uploads")
        )

        assert len(symbols) > 0
        sym_names = [s.name for s in symbols]
        assert "add" in sym_names
        assert "Calculator" in sym_names

        # Check DB persistence
        res = await session.execute(
            select(Symbol).where(Symbol.repository_id == repo.id)
        )
        db_symbols = res.scalars().all()
        assert len(db_symbols) == len(symbols)

        # Check repo status updated
        await session.refresh(repo)
        assert repo.status == RepositoryStatus.INDEXING

    await engine.dispose()


@pytest.mark.asyncio
async def test_parse_repository_records_parse_error(tmp_path: Path) -> None:
    """Syntax errors should set CodeFile.parse_error without breaking execution."""
    engine, factory = await _create_engine()

    async with factory() as session:
        repo_id = uuid.uuid4()
        repo = Repository(
            id=repo_id,
            name="test-repo",
            slug=f"test-repo-{str(repo_id)[:8]}",
            source=RepositorySource.UPLOAD,
            status=RepositoryStatus.PARSING,
            size_bytes=1000,
            file_count=1,
        )
        session.add(repo)
        await session.commit()

        source_dir = tmp_path / "uploads" / str(repo_id) / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "bad.py").write_text("def broken(:")

        code_file = CodeFile(
            id=uuid.uuid4(),
            repository_id=repo.id,
            path="bad.py",
            language="Python",
            size_bytes=20,
            content_hash="badhash",
            line_count=1,
            is_binary=False,
        )
        session.add(code_file)
        await session.commit()

        symbols = await parse_repository(
            repo, [code_file], session, upload_dir=str(tmp_path / "uploads")
        )

        assert len(symbols) == 0
        await session.refresh(code_file)
        assert code_file.parse_error is not None
        assert "SyntaxError" in code_file.parse_error

    await engine.dispose()
