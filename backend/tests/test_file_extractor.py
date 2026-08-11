"""Tests for Phase 7: file extraction, hashing, binary detection, ignore patterns."""

import hashlib
import io
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
from app.core.ignore_patterns import IgnoreFilter, load_gitignore_spec
from app.db.base import Base
from app.dependencies import get_app_settings, get_db
from app.main import create_app
from app.models.code_file import CodeFile
from app.models.repository import Repository, RepositorySource, RepositoryStatus
from app.services.file_extractor import (
    _count_lines,
    _is_binary,
    _sha256,
    _walk_and_collect,
    extract_files,
)

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


def _build_source_tree(base: Path) -> None:
    """Populate a small source tree under *base* for tests."""
    base.mkdir(parents=True, exist_ok=True)
    (base / "main.py").write_text("def main():\n    pass\n", encoding="utf-8")
    (base / "utils.py").write_text(
        "def add(a, b):\n    return a + b\n", encoding="utf-8"
    )
    sub = base / "sub"
    sub.mkdir()
    (sub / "helper.py").write_text("helper = True\n", encoding="utf-8")
    # Binary file
    (base / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")


# ---------------------------------------------------------------------------
# Unit tests: helpers
# ---------------------------------------------------------------------------


def test_is_binary_detects_binary_content(tmp_path: Path) -> None:
    """Files containing null bytes are classified as binary."""
    f = tmp_path / "binary.bin"
    f.write_bytes(b"hello\x00world")
    assert _is_binary(f) is True


def test_is_binary_detects_text_content(tmp_path: Path) -> None:
    """Plain text files are not classified as binary."""
    f = tmp_path / "text.py"
    f.write_text("print('hello')\n", encoding="utf-8")
    assert _is_binary(f) is False


def test_sha256_correctness(tmp_path: Path) -> None:
    """SHA-256 computed by helper matches hashlib reference."""
    content = b"hello codegraph"
    f = tmp_path / "sample.txt"
    f.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()
    assert _sha256(f) == expected


def test_count_lines(tmp_path: Path) -> None:
    """Line count returns number of newlines in the file."""
    f = tmp_path / "lines.txt"
    f.write_text("line1\nline2\nline3\n", encoding="utf-8")
    assert _count_lines(f) == 3


def test_count_lines_empty(tmp_path: Path) -> None:
    """Empty file has 0 lines."""
    f = tmp_path / "empty.txt"
    f.write_bytes(b"")
    assert _count_lines(f) == 0


# ---------------------------------------------------------------------------
# Unit tests: IgnoreFilter
# ---------------------------------------------------------------------------


def test_ignore_filter_ignores_node_modules(tmp_path: Path) -> None:
    filt = IgnoreFilter.from_repo_root(tmp_path)
    assert filt.should_ignore(Path("node_modules/lodash/index.js")) is True


def test_ignore_filter_ignores_pycache(tmp_path: Path) -> None:
    filt = IgnoreFilter.from_repo_root(tmp_path)
    assert filt.should_ignore(Path("app/__pycache__/main.cpython-312.pyc")) is True


def test_ignore_filter_ignores_min_js(tmp_path: Path) -> None:
    filt = IgnoreFilter.from_repo_root(tmp_path)
    assert filt.should_ignore(Path("static/bundle.min.js")) is True


def test_ignore_filter_ignores_lock_files(tmp_path: Path) -> None:
    filt = IgnoreFilter.from_repo_root(tmp_path)
    assert filt.should_ignore(Path("package-lock.json")) is True


def test_ignore_filter_allows_normal_file(tmp_path: Path) -> None:
    filt = IgnoreFilter.from_repo_root(tmp_path)
    assert filt.should_ignore(Path("app/main.py")) is False


def test_ignore_filter_respects_gitignore(tmp_path: Path) -> None:
    """Patterns in .gitignore should cause matching files to be ignored."""
    (tmp_path / ".gitignore").write_text("*.log\nsecrets/\n", encoding="utf-8")
    filt = IgnoreFilter.from_repo_root(tmp_path)
    assert filt.should_ignore(Path("debug.log")) is True
    assert filt.should_ignore(Path("secrets/api_key.txt")) is True
    assert filt.should_ignore(Path("app/main.py")) is False


def test_load_gitignore_spec_returns_none_when_absent(tmp_path: Path) -> None:
    assert load_gitignore_spec(tmp_path) is None


def test_load_gitignore_spec_returns_spec_when_present(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("*.env\n", encoding="utf-8")
    spec = load_gitignore_spec(tmp_path)
    assert spec is not None
    assert spec.match_file("prod.env") is True


# ---------------------------------------------------------------------------
# Unit tests: _walk_and_collect
# ---------------------------------------------------------------------------


def test_walk_and_collect_finds_files(tmp_path: Path) -> None:
    """Walk should discover all non-ignored files."""
    _build_source_tree(tmp_path)
    filt = IgnoreFilter.from_repo_root(tmp_path)
    records = _walk_and_collect(tmp_path, filt)
    paths = {r["rel_path"] for r in records}
    assert "main.py" in paths
    assert "utils.py" in paths
    assert "sub/helper.py" in paths
    assert "image.png" in paths  # binary but not ignored


def test_walk_and_collect_detects_binary(tmp_path: Path) -> None:
    """Binary files are marked is_binary=True."""
    _build_source_tree(tmp_path)
    filt = IgnoreFilter.from_repo_root(tmp_path)
    records = _walk_and_collect(tmp_path, filt)
    binary_rec = next(r for r in records if r["rel_path"] == "image.png")
    assert binary_rec["is_binary"] is True


def test_walk_and_collect_hashes_files(tmp_path: Path) -> None:
    """Content hash should be correct for a known file."""
    content = b"hello codegraph"
    f = tmp_path / "known.txt"
    f.write_bytes(content)
    filt = IgnoreFilter.from_repo_root(tmp_path)
    records = _walk_and_collect(tmp_path, filt)
    rec = next(r for r in records if r["rel_path"] == "known.txt")
    assert rec["content_hash"] == hashlib.sha256(content).hexdigest()


def test_walk_and_collect_respects_gitignore(tmp_path: Path) -> None:
    """Files matching .gitignore patterns should be excluded."""
    (tmp_path / ".gitignore").write_text("*.log\n", encoding="utf-8")
    (tmp_path / "app.log").write_text("log data\n")
    (tmp_path / "main.py").write_text("pass\n")
    filt = IgnoreFilter.from_repo_root(tmp_path)
    records = _walk_and_collect(tmp_path, filt)
    paths = {r["rel_path"] for r in records}
    # .gitignore itself is not ignored, but app.log should be
    assert "app.log" not in paths
    assert "main.py" in paths


# ---------------------------------------------------------------------------
# Async unit tests: extract_files()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_extract_files_creates_code_file_rows(tmp_path: Path) -> None:
    """extract_files() should create CodeFile rows for each non-ignored file."""
    engine, factory = await _create_engine()

    async with factory() as session:
        import uuid

        repo_id = uuid.uuid4()
        repo = Repository(
            id=repo_id,
            name="test-repo",
            slug=f"test-repo-{str(repo_id)[:8]}",
            source=RepositorySource.UPLOAD,
            status=RepositoryStatus.INGESTING,
            size_bytes=0,
            file_count=0,
        )
        session.add(repo)
        await session.commit()
        await session.refresh(repo)

        # Build source tree
        source_dir = tmp_path / "uploads" / str(repo_id) / "source"
        _build_source_tree(source_dir)

        code_files = await extract_files(
            repo, session, upload_dir=str(tmp_path / "uploads")
        )

        assert len(code_files) >= 3  # main.py, utils.py, sub/helper.py + binary

        # Verify rows in DB
        result = await session.execute(
            select(CodeFile).where(CodeFile.repository_id == repo_id)
        )
        db_files = result.scalars().all()
        assert len(db_files) == len(code_files)

    await engine.dispose()


@pytest.mark.asyncio
async def test_extract_files_marks_binary_correctly(tmp_path: Path) -> None:
    """extract_files() should mark binary files with is_binary=True."""
    engine, factory = await _create_engine()

    async with factory() as session:
        import uuid

        repo_id = uuid.uuid4()
        repo = Repository(
            id=repo_id,
            name="test-repo",
            slug=f"test-repo-{str(repo_id)[:8]}",
            source=RepositorySource.UPLOAD,
            status=RepositoryStatus.INGESTING,
            size_bytes=0,
            file_count=0,
        )
        session.add(repo)
        await session.commit()
        await session.refresh(repo)

        source_dir = tmp_path / "uploads" / str(repo_id) / "source"
        _build_source_tree(source_dir)

        code_files = await extract_files(
            repo, session, upload_dir=str(tmp_path / "uploads")
        )

        binary_files = [cf for cf in code_files if cf.is_binary]
        text_files = [cf for cf in code_files if not cf.is_binary]
        assert len(binary_files) >= 1
        png_file = next((cf for cf in binary_files if "image.png" in cf.path), None)
        assert png_file is not None
        assert len(text_files) >= 3

    await engine.dispose()


@pytest.mark.asyncio
async def test_extract_files_stores_correct_hash(tmp_path: Path) -> None:
    """The stored SHA-256 hash should match the actual file content."""
    engine, factory = await _create_engine()

    async with factory() as session:
        import uuid

        repo_id = uuid.uuid4()
        repo = Repository(
            id=repo_id,
            name="test-repo",
            slug=f"test-repo-{str(repo_id)[:8]}",
            source=RepositorySource.UPLOAD,
            status=RepositoryStatus.INGESTING,
            size_bytes=0,
            file_count=0,
        )
        session.add(repo)
        await session.commit()
        await session.refresh(repo)

        source_dir = tmp_path / "uploads" / str(repo_id) / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        content = b"known content for hash test"
        (source_dir / "known.py").write_bytes(content)

        code_files = await extract_files(
            repo, session, upload_dir=str(tmp_path / "uploads")
        )

        known_file = next(cf for cf in code_files if cf.path == "known.py")
        assert known_file.content_hash == hashlib.sha256(content).hexdigest()

    await engine.dispose()


@pytest.mark.asyncio
async def test_extract_files_respects_gitignore(tmp_path: Path) -> None:
    """Files matching .gitignore should not appear in CodeFile rows."""
    engine, factory = await _create_engine()

    async with factory() as session:
        import uuid

        repo_id = uuid.uuid4()
        repo = Repository(
            id=repo_id,
            name="test-repo",
            slug=f"test-repo-{str(repo_id)[:8]}",
            source=RepositorySource.UPLOAD,
            status=RepositoryStatus.INGESTING,
            size_bytes=0,
            file_count=0,
        )
        session.add(repo)
        await session.commit()
        await session.refresh(repo)

        source_dir = tmp_path / "uploads" / str(repo_id) / "source"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / ".gitignore").write_text("*.log\n", encoding="utf-8")
        (source_dir / "app.log").write_text("log data", encoding="utf-8")
        (source_dir / "main.py").write_text("pass\n", encoding="utf-8")

        code_files = await extract_files(
            repo, session, upload_dir=str(tmp_path / "uploads")
        )

        paths = {cf.path for cf in code_files}
        assert "app.log" not in paths
        assert "main.py" in paths

    await engine.dispose()


@pytest.mark.asyncio
async def test_extract_files_updates_repo_file_count(tmp_path: Path) -> None:
    """After extraction, Repository.file_count equals the number of files found."""
    engine, factory = await _create_engine()

    async with factory() as session:
        import uuid

        repo_id = uuid.uuid4()
        repo = Repository(
            id=repo_id,
            name="test-repo",
            slug=f"test-repo-{str(repo_id)[:8]}",
            source=RepositorySource.UPLOAD,
            status=RepositoryStatus.INGESTING,
            size_bytes=0,
            file_count=0,
        )
        session.add(repo)
        await session.commit()
        await session.refresh(repo)

        source_dir = tmp_path / "uploads" / str(repo_id) / "source"
        _build_source_tree(source_dir)

        code_files = await extract_files(
            repo, session, upload_dir=str(tmp_path / "uploads")
        )

        await session.refresh(repo)
        assert repo.file_count == len(code_files)
        assert repo.status == RepositoryStatus.PARSING

    await engine.dispose()


# ---------------------------------------------------------------------------
# API integration test: POST /{repo_id}/extract
# ---------------------------------------------------------------------------


def _make_sample_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("myrepo/main.py", "def main(): pass\n")
        zf.writestr("myrepo/utils.py", "def helper(): pass\n")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_extract_endpoint_success(tmp_path: Path) -> None:
    """POST /{repo_id}/extract should return file_count > 0 for a valid repo."""
    engine, factory = await _create_engine()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    settings = _make_settings(tmp_path)
    app = create_app(settings=settings)
    app.dependency_overrides[get_db] = override_get_db  # type: ignore[attr-defined]
    app.dependency_overrides[get_app_settings] = lambda: settings  # type: ignore[attr-defined]

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Upload a repo first
        upload_resp = await client.post(
            "/api/v1/repositories",
            files={"file": ("repo.zip", _make_sample_zip(), "application/zip")},
        )
        assert upload_resp.status_code == 200
        repo_id = upload_resp.json()["id"]

        # Trigger extraction
        extract_resp = await client.post(f"/api/v1/repositories/{repo_id}/extract")

    assert extract_resp.status_code == 200
    data = extract_resp.json()
    assert data["repo_id"] == repo_id
    assert data["file_count"] >= 2

    await engine.dispose()


@pytest.mark.asyncio
async def test_extract_endpoint_not_found(tmp_path: Path) -> None:
    """POST /{repo_id}/extract should return 404 for an unknown repo ID."""
    import uuid

    engine, factory = await _create_engine()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with factory() as session:
            yield session

    settings = _make_settings(tmp_path)
    app = create_app(settings=settings)
    app.dependency_overrides[get_db] = override_get_db  # type: ignore[attr-defined]
    app.dependency_overrides[get_app_settings] = lambda: settings  # type: ignore[attr-defined]

    missing_id = uuid.uuid4()
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(f"/api/v1/repositories/{missing_id}/extract")

    assert resp.status_code == 404

    await engine.dispose()
