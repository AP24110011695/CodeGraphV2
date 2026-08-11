"""Tests for Phase 11 — Dependency Graph Construction & API.

Covers:
- Graph builder: correct in/out degrees, pagerank, entry-point/leaf flags.
- Cycle detection (acyclic and cyclic graphs).
- RepositoryGraph upsert behaviour.
- GET /api/v1/repositories/{repo_id}/graph endpoint.
- GET /api/v1/repositories/{repo_id}/graph/node/{file_id} endpoint.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base
from app.models.code_file import CodeFile
from app.models.dependency import Dependency, DependencyType
from app.models.repository import Repository, RepositorySource, RepositoryStatus
from app.models.repository_graph import RepositoryGraph
from app.models.symbol import Symbol, SymbolKind
from app.services.graph_builder import (
    _build_networkx_graph,
    _compute_node_metrics,
    _detect_cycles,
    _serialize_graph,
    build_graph,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


async def _make_engine() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Create an in-memory SQLite engine with all tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    return engine, factory


def _repo() -> Repository:
    return Repository(
        id=uuid.uuid4(),
        name="test-repo",
        slug="test-repo-aaaa",
        source=RepositorySource.UPLOAD,
        status=RepositoryStatus.PARSING,
        size_bytes=0,
        file_count=0,
    )


def _file(repo_id: uuid.UUID, path: str = "a.py", language: str = "Python") -> CodeFile:
    return CodeFile(
        id=uuid.uuid4(),
        repository_id=repo_id,
        path=path,
        language=language,
        size_bytes=100,
        content_hash=f"hash-{uuid.uuid4().hex[:8]}",
        line_count=10,
        is_binary=False,
    )


def _dep(
    repo_id: uuid.UUID,
    from_file: CodeFile,
    to_file: CodeFile,
    import_name: str = "mod",
) -> Dependency:
    return Dependency(
        id=uuid.uuid4(),
        repository_id=repo_id,
        from_file_id=from_file.id,
        to_file_id=to_file.id,
        import_name=import_name,
        import_path=import_name,
        dependency_type=DependencyType.INTERNAL,
    )


# ---------------------------------------------------------------------------
# Unit tests — graph builder internals
# ---------------------------------------------------------------------------


class TestBuildNetworkxGraph:
    def test_all_nodes_present(self) -> None:
        repo_id = uuid.uuid4()
        f1 = _file(repo_id, "a.py")
        f2 = _file(repo_id, "b.py")
        f3 = _file(repo_id, "c.py")
        d12 = _dep(repo_id, f1, f2)
        G = _build_networkx_graph([f1, f2, f3], [d12])
        assert G.number_of_nodes() == 3
        assert G.has_node(str(f1.id))
        assert G.has_node(str(f3.id))

    def test_edges_created_correctly(self) -> None:
        repo_id = uuid.uuid4()
        f1 = _file(repo_id, "a.py")
        f2 = _file(repo_id, "b.py")
        d = _dep(repo_id, f1, f2, import_name="b_module")
        G = _build_networkx_graph([f1, f2], [d])
        assert G.has_edge(str(f1.id), str(f2.id))
        assert G[str(f1.id)][str(f2.id)]["import_name"] == "b_module"

    def test_no_files_empty_graph(self) -> None:
        G = _build_networkx_graph([], [])
        assert G.number_of_nodes() == 0
        assert G.number_of_edges() == 0


class TestComputeNodeMetrics:
    def _graph_triangle(self) -> tuple[Any, list[str]]:
        """A → B → C (linear chain, no cycles)."""
        import networkx as nx

        G = nx.DiGraph()
        ids = [str(uuid.uuid4()) for _ in range(3)]
        G.add_node(ids[0])
        G.add_node(ids[1])
        G.add_node(ids[2])
        G.add_edge(ids[0], ids[1])
        G.add_edge(ids[1], ids[2])
        return G, ids

    def test_in_out_degrees(self) -> None:
        G, ids = self._graph_triangle()
        metrics = _compute_node_metrics(G)
        # A: in=0, out=1 → entry_point
        assert metrics[ids[0]]["in_degree"] == 0
        assert metrics[ids[0]]["out_degree"] == 1
        assert metrics[ids[0]]["is_entry_point"] is True
        assert metrics[ids[0]]["is_leaf"] is False
        # C: in=1, out=0 → leaf
        assert metrics[ids[2]]["in_degree"] == 1
        assert metrics[ids[2]]["out_degree"] == 0
        assert metrics[ids[2]]["is_entry_point"] is False
        assert metrics[ids[2]]["is_leaf"] is True

    def test_pagerank_present_and_valid(self) -> None:
        G, ids = self._graph_triangle()
        metrics = _compute_node_metrics(G)
        for node_id in ids:
            pr = metrics[node_id]["pagerank"]
            assert isinstance(pr, float)
            assert pr >= 0.0

    def test_empty_graph_returns_empty(self) -> None:
        import networkx as nx
        G = nx.DiGraph()
        assert _compute_node_metrics(G) == {}


class TestDetectCycles:
    def test_acyclic_graph(self) -> None:
        import networkx as nx
        G = nx.DiGraph()
        a, b, c = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
        G.add_edge(a, b)
        G.add_edge(b, c)
        has_cycles, count = _detect_cycles(G)
        assert has_cycles is False
        assert count == 0

    def test_cyclic_graph(self) -> None:
        import networkx as nx
        G = nx.DiGraph()
        a, b = str(uuid.uuid4()), str(uuid.uuid4())
        G.add_edge(a, b)
        G.add_edge(b, a)
        has_cycles, count = _detect_cycles(G)
        assert has_cycles is True
        assert count >= 1

    def test_self_loop(self) -> None:
        import networkx as nx
        G = nx.DiGraph()
        a = str(uuid.uuid4())
        G.add_edge(a, a)
        has_cycles, count = _detect_cycles(G)
        assert has_cycles is True
        assert count >= 1


class TestSerializeGraph:
    def test_all_nodes_and_edges_present(self) -> None:
        import networkx as nx

        repo_id = uuid.uuid4()
        f1 = _file(repo_id, "a.py")
        f2 = _file(repo_id, "b.py")
        d12 = _dep(repo_id, f1, f2)
        G = _build_networkx_graph([f1, f2], [d12])
        metrics = _compute_node_metrics(G)
        sym_counts = {str(f1.id): 3}

        nodes, edges = _serialize_graph(G, [f1, f2], [d12], sym_counts, metrics)

        node_ids = {n["id"] for n in nodes}
        assert str(f1.id) in node_ids
        assert str(f2.id) in node_ids

        assert len(edges) == 1
        assert edges[0]["from_file_id"] == str(f1.id)
        assert edges[0]["to_file_id"] == str(f2.id)
        assert edges[0]["import_name"] == "mod"

        # Symbol count propagated
        f1_node = next(n for n in nodes if n["id"] == str(f1.id))
        assert f1_node["symbol_count"] == 3


# ---------------------------------------------------------------------------
# Integration test — build_graph service with SQLite
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_graph_integration(tmp_path: Path) -> None:
    """build_graph() creates a RepositoryGraph row with correct metrics."""
    engine, Session = await _make_engine()

    async with Session() as db:
        repo = _repo()
        db.add(repo)
        await db.flush()

        f1 = _file(repo.id, "main.py")
        f2 = _file(repo.id, "utils.py")
        f3 = _file(repo.id, "isolated.py")  # no edges
        db.add_all([f1, f2, f3])
        await db.flush()

        # f1 → f2 (internal)
        dep = _dep(repo.id, f1, f2, import_name="utils")
        db.add(dep)
        await db.commit()

    async with Session() as db:
        # Re-fetch repo in this session
        result = await db.execute(select(Repository).where(Repository.id == repo.id))
        repo2 = result.scalar_one()

        upload_dir = str(tmp_path)
        rg = await build_graph(repo2, db, upload_dir=upload_dir)
        await db.commit()

        # Assertions on the returned graph object
        assert rg.repository_id == repo.id
        node_ids = {n["id"] for n in rg.nodes}
        assert str(f1.id) in node_ids
        assert str(f2.id) in node_ids
        assert str(f3.id) in node_ids

        assert len(rg.edges) == 1
        assert rg.edges[0]["from_file_id"] == str(f1.id)
        assert rg.edges[0]["to_file_id"] == str(f2.id)

        # Check metrics
        assert rg.metrics["node_count"] == 3
        assert rg.metrics["edge_count"] == 1
        assert rg.metrics["has_cycles"] is False

        # f1 should be entry point (in=0, out=1)
        f1_node = next(n for n in rg.nodes if n["id"] == str(f1.id))
        assert f1_node["metrics"]["is_entry_point"] is True
        # f2 should be leaf (out=0)
        f2_node = next(n for n in rg.nodes if n["id"] == str(f2.id))
        assert f2_node["metrics"]["is_leaf"] is True
        # f3: isolated — is_leaf and NOT is_entry_point
        f3_node = next(n for n in rg.nodes if n["id"] == str(f3.id))
        assert f3_node["metrics"]["is_leaf"] is True
        assert f3_node["metrics"]["is_entry_point"] is False

        # graph.json written to disk
        graph_json_path = tmp_path / str(repo.id) / "graph.json"
        assert graph_json_path.exists()

        # Repo cycle columns updated
        assert repo2.has_cycles is False
        assert repo2.cycle_count == 0


@pytest.mark.asyncio
async def test_build_graph_cycle_detection(tmp_path: Path) -> None:
    """build_graph() detects cycles and updates repo.has_cycles."""
    engine, Session = await _make_engine()

    async with Session() as db:
        repo = _repo()
        db.add(repo)
        await db.flush()

        f1 = _file(repo.id, "a.py")
        f2 = _file(repo.id, "b.py")
        db.add_all([f1, f2])
        await db.flush()

        # f1 → f2 → f1 (cycle)
        d12 = _dep(repo.id, f1, f2, import_name="b")
        d21 = _dep(repo.id, f2, f1, import_name="a")
        db.add_all([d12, d21])
        await db.commit()

    async with Session() as db:
        result = await db.execute(select(Repository).where(Repository.id == repo.id))
        repo2 = result.scalar_one()
        await build_graph(repo2, db, upload_dir=str(tmp_path))
        await db.commit()
        assert repo2.has_cycles is True
        assert repo2.cycle_count >= 1


@pytest.mark.asyncio
async def test_build_graph_upsert(tmp_path: Path) -> None:
    """Calling build_graph() twice updates the existing RepositoryGraph row."""
    engine, Session = await _make_engine()

    async with Session() as db:
        repo = _repo()
        db.add(repo)
        await db.flush()
        f1 = _file(repo.id, "x.py")
        db.add(f1)
        await db.commit()

    # First call
    async with Session() as db:
        result = await db.execute(select(Repository).where(Repository.id == repo.id))
        repo2 = result.scalar_one()
        rg1 = await build_graph(repo2, db, upload_dir=str(tmp_path))
        await db.commit()

    # Second call — should update, not insert a duplicate
    async with Session() as db:
        result = await db.execute(select(Repository).where(Repository.id == repo.id))
        repo3 = result.scalar_one()
        rg2 = await build_graph(repo3, db, upload_dir=str(tmp_path))
        await db.commit()

        count_result = await db.execute(
            select(RepositoryGraph).where(RepositoryGraph.repository_id == repo.id)
        )
        rows = count_result.scalars().all()
        assert len(rows) == 1


# ---------------------------------------------------------------------------
# API endpoint tests (using FastAPI TestClient / httpx)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_graph_api_404_no_graph(tmp_path: Path) -> None:
    """GET /graph returns 404 when no RepositoryGraph has been built yet."""
    from unittest.mock import AsyncMock, patch

    from httpx import ASGITransport, AsyncClient

    from app.config import EnvironmentType, Settings
    from app.dependencies import get_db
    from app.main import create_app

    # production env skips migration in lifespan → no DB connection on startup
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://localhost/test",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret",
        LLM_API_KEY="test-key",
        ENVIRONMENT=EnvironmentType.PRODUCTION,
    )
    test_app = create_app(settings=settings)

    repo_id = uuid.uuid4()
    fake_repo = MagicMock()
    fake_repo.id = repo_id

    # Use SQLite in-memory for get_db override
    engine, Session = await _make_engine()

    async def _override_get_db():
        async with Session() as session:
            yield session

    # Override dependencies on the app (no graph row → should return 404)
    test_app.dependency_overrides[get_db] = _override_get_db

    with patch("app.api.v1.graph.get_repository", new=AsyncMock(return_value=fake_repo)):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/v1/repositories/{repo_id}/graph")

    test_app.dependency_overrides.clear()
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_graph_api_returns_graph(tmp_path: Path) -> None:
    """GET /graph returns GraphResponse with correct structure."""
    from unittest.mock import AsyncMock, patch

    from httpx import ASGITransport, AsyncClient

    from app.config import EnvironmentType, Settings
    from app.dependencies import get_db
    from app.main import create_app

    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://localhost/test",
        REDIS_URL="redis://localhost:6379/0",
        SECRET_KEY="test-secret",
        LLM_API_KEY="test-key",
        ENVIRONMENT=EnvironmentType.PRODUCTION,
    )
    test_app = create_app(settings=settings)

    # Build graph in SQLite
    engine, Session = await _make_engine()

    async with Session() as db:
        repo = _repo()
        db.add(repo)
        await db.flush()
        f1 = _file(repo.id, "a.py")
        f2 = _file(repo.id, "b.py")
        db.add_all([f1, f2])
        await db.flush()
        dep = _dep(repo.id, f1, f2)
        db.add(dep)
        await db.commit()

    async with Session() as db:
        result = await db.execute(select(Repository).where(Repository.id == repo.id))
        r = result.scalar_one()
        await build_graph(r, db, upload_dir=str(tmp_path))
        await db.commit()

    fake_repo = MagicMock()
    fake_repo.id = repo.id

    async def _override_get_db():
        async with Session() as session:
            yield session

    test_app.dependency_overrides[get_db] = _override_get_db

    with patch("app.api.v1.graph.get_repository", new=AsyncMock(return_value=fake_repo)):
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/v1/repositories/{repo.id}/graph")

    test_app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert data["repository_id"] == str(repo.id)
    assert "nodes" in data
    assert "edges" in data
    assert "metrics" in data
    assert data["metrics"]["node_count"] == 2
    assert data["metrics"]["edge_count"] == 1

