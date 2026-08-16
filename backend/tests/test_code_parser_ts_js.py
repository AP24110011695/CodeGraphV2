"""Tests for TS/JS tree-sitter parsers, import resolution, and Dependency."""

import io
import uuid
import zipfile
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings
from app.core.import_resolver import resolve_import_path
from app.core.parsers.base import ImportData
from app.core.parsers.javascript_parser import JavaScriptParser
from app.core.parsers.typescript_parser import TypeScriptParser
from app.db.base import Base
from app.dependencies import get_app_settings, get_db
from app.main import create_app
from app.models.code_file import CodeFile
from app.models.dependency import Dependency
from app.models.repository import Repository, RepositorySource, RepositoryStatus
from app.services.code_parser import parse_repository

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_TS = FIXTURES_DIR / "sample.ts"
SAMPLE_JS = FIXTURES_DIR / "sample.js"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_engine() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    return engine, factory


def _make_settings(tmp_path: Path, **kwargs: object) -> Settings:
    base: dict[str, object] = {
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/0",
        "SECRET_KEY": "test-secret",
        "LLM_API_KEY": "test-key",
        "UPLOAD_DIR": str(tmp_path / "uploads"),
    }
    base.update(kwargs)
    return Settings(**base)  # type: ignore[arg-type]


def _make_code_file(path: str, language: str) -> CodeFile:
    return CodeFile(
        id=uuid.uuid4(),
        repository_id=uuid.uuid4(),
        path=path,
        language=language,
        size_bytes=100,
        content_hash="hash123",
        line_count=20,
        is_binary=False,
    )


# ---------------------------------------------------------------------------
# TypeScriptParser Unit Tests
# ---------------------------------------------------------------------------


def test_typescript_parser_extracts_symbols() -> None:
    """TypeScriptParser should extract interface, type, class, method, function."""
    cf = _make_code_file("sample.ts", "TypeScript")
    parser = TypeScriptParser()
    res = parser.parse(SAMPLE_TS, cf)

    assert res.error is None
    names = [s.name for s in res.symbols]
    kinds = {s.name: s.kind for s in res.symbols}

    assert "User" in names
    assert kinds["User"] == "interface"

    assert "UserRole" in names
    assert kinds["UserRole"] == "type"

    assert "UserService" in names
    assert kinds["UserService"] == "class"

    assert "UserService.getUser" in names
    assert kinds["UserService.getUser"] == "method"

    assert "formatUser" in names
    assert kinds["formatUser"] == "function"


def test_typescript_parser_extracts_imports() -> None:
    """TypeScriptParser should extract relative and module imports."""
    cf = _make_code_file("sample.ts", "TypeScript")
    parser = TypeScriptParser()
    res = parser.parse(SAMPLE_TS, cf)

    import_names = [i.import_name for i in res.imports]
    import_paths = [i.import_path for i in res.imports]

    assert "add" in import_names
    assert "./utils" in import_paths
    assert "axios" in import_names


# ---------------------------------------------------------------------------
# JavaScriptParser Unit Tests
# ---------------------------------------------------------------------------


def test_javascript_parser_extracts_symbols() -> None:
    """JavaScriptParser should extract functions, arrow functions, methods."""
    cf = _make_code_file("sample.js", "JavaScript")
    parser = JavaScriptParser()
    res = parser.parse(SAMPLE_JS, cf)

    assert res.error is None
    names = [s.name for s in res.symbols]

    assert "calculateTotal" in names
    assert "formatCurrency" in names


def test_javascript_parser_extracts_commonjs_requires() -> None:
    """JavaScriptParser should extract CommonJS require statements."""
    cf = _make_code_file("sample.js", "JavaScript")
    parser = JavaScriptParser()
    res = parser.parse(SAMPLE_JS, cf)

    import_names = [i.import_name for i in res.imports]
    import_paths = [i.import_path for i in res.imports]

    assert "fs" in import_names
    assert "fs" in import_paths
    assert "helper" in import_names
    assert "./utils" in import_paths


# ---------------------------------------------------------------------------
# Import Resolver Unit Tests
# ---------------------------------------------------------------------------


def test_import_resolver_internal_relative() -> None:
    """Relative import should resolve to matching internal CodeFile."""
    from_file = _make_code_file("src/components/Header.tsx", "TypeScript")
    target_file = _make_code_file("src/utils/format.ts", "TypeScript")

    repo_files = {
        from_file.path: from_file,
        target_file.path: target_file,
    }

    imp = ImportData(
        import_name="format", import_path="../utils/format", is_relative=True
    )
    resolved, dep_type = resolve_import_path(imp, from_file, repo_files)

    assert dep_type == "internal"
    assert resolved is target_file


def test_import_resolver_external_npm() -> None:
    """Non-relative package import should resolve as external."""
    from_file = _make_code_file("src/index.ts", "TypeScript")
    repo_files = {from_file.path: from_file}

    imp = ImportData(import_name="axios", import_path="axios", is_relative=False)
    resolved, dep_type = resolve_import_path(imp, from_file, repo_files)

    assert dep_type == "external"
    assert resolved is None


def test_import_resolver_python_stdlib() -> None:
    """Python stdlib import should resolve as stdlib."""
    from_file = _make_code_file("app/main.py", "Python")
    repo_files = {from_file.path: from_file}

    imp = ImportData(import_name="os", import_path="os", is_relative=False)
    resolved, dep_type = resolve_import_path(imp, from_file, repo_files)

    assert dep_type == "stdlib"
    assert resolved is None


# ---------------------------------------------------------------------------
# Integration Tests: parse_repository + Dependency Rows
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parse_repository_populates_dependencies(tmp_path: Path) -> None:
    """parse_repository populates Dependency rows for internal & external imports."""
    engine, factory = await _create_engine()

    async with factory() as session:
        repo_id = uuid.uuid4()
        repo = Repository(
            id=repo_id,
            name="ts-repo",
            slug=f"ts-repo-{str(repo_id)[:8]}",
            source=RepositorySource.UPLOAD,
            status=RepositoryStatus.PARSING,
            size_bytes=2000,
            file_count=2,
        )
        session.add(repo)
        await session.commit()

        source_dir = tmp_path / "uploads" / str(repo_id) / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "sample.ts").write_text(SAMPLE_TS.read_text(encoding="utf-8"))
        (source_dir / "utils.ts").write_text(
            "export function add(a: number, b: number) { return a + b; }"
        )

        cf_sample = CodeFile(
            id=uuid.uuid4(),
            repository_id=repo.id,
            path="sample.ts",
            language="TypeScript",
            size_bytes=500,
            content_hash="h1",
            line_count=20,
            is_binary=False,
        )
        cf_utils = CodeFile(
            id=uuid.uuid4(),
            repository_id=repo.id,
            path="utils.ts",
            language="TypeScript",
            size_bytes=200,
            content_hash="h2",
            line_count=5,
            is_binary=False,
        )
        session.add_all([cf_sample, cf_utils])
        await session.commit()

        symbols = await parse_repository(
            repo, [cf_sample, cf_utils], session, upload_dir=str(tmp_path / "uploads")
        )

        assert len(symbols) > 0

        # Query Dependency rows
        dep_result = await session.execute(
            select(Dependency).where(Dependency.repository_id == repo.id)
        )
        deps = dep_result.scalars().all()
        assert len(deps) >= 2

        # Verify internal dependency link
        internal_dep = next((d for d in deps if d.dependency_type == "internal"), None)
        assert internal_dep is not None
        assert internal_dep.from_file_id == cf_sample.id
        assert internal_dep.to_file_id == cf_utils.id

        # Verify external dependency link
        external_dep = next((d for d in deps if d.dependency_type == "external"), None)
        assert external_dep is not None
        assert external_dep.import_path == "axios"

    await engine.dispose()


@pytest.mark.skip(
    reason="Phase 18: debug /parse endpoint was removed; parsing is now "
           "automated via the Celery pipeline chain. See test_tasks.py for "
           "end-to-end pipeline tests."
)
@pytest.mark.asyncio
async def test_parse_endpoint_integration(tmp_path: Path) -> None:
    """POST /{repo_id}/parse debug endpoint triggers full extraction and parsing."""
    engine, factory = await _create_engine()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    settings = _make_settings(tmp_path)
    app = create_app(settings=settings)
    app.dependency_overrides[get_db] = override_get_db  # type: ignore[attr-defined]
    app.dependency_overrides[get_app_settings] = lambda: settings  # type: ignore[attr-defined]

    # Create sample zip with TS files
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("repo/main.ts", SAMPLE_TS.read_bytes())
        zf.writestr(
            "repo/utils.ts",
            "export function add(a: number, b: number) { return a + b; }",
        )
    zip_bytes = buf.getvalue()

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        upload_resp = await client.post(
            "/api/v1/repositories",
            files={"file": ("ts_repo.zip", zip_bytes, "application/zip")},
        )
        assert upload_resp.status_code == 200
        repo_id = upload_resp.json()["id"]

        parse_resp = await client.post(f"/api/v1/repositories/{repo_id}/parse")

    assert parse_resp.status_code == 200
    data = parse_resp.json()
    assert data["repo_id"] == repo_id
    assert data["file_count"] >= 2
    assert data["symbol_count"] >= 4

    await engine.dispose()
