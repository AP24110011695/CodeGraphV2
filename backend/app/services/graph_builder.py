"""Dependency graph builder service.

Constructs a networkx DiGraph from Dependency rows, computes per-node metrics
(in/out degree, PageRank, entry-point, leaf flags), detects cycles, serialises
the result to JSONB-friendly dicts, and persists a RepositoryGraph record.

For repositories with >5000 files the serialised graph is truncated to the top
500 nodes by PageRank plus all their edges; the full graph is also written to
disk as ``{UPLOAD_DIR}/{repo_id}/graph.json``.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import networkx as nx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis_job import AnalysisJob, JobStatus
from app.models.code_file import CodeFile
from app.models.dependency import Dependency, DependencyType
from app.models.repository import Repository
from app.models.repository_graph import RepositoryGraph
from app.models.symbol import Symbol

logger = logging.getLogger(__name__)

# Maximum nodes to serialise into the DB when repo has many files.
_MAX_DB_NODES = 500


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _count_symbols_per_file(
    symbols: list[Symbol],
) -> dict[str, int]:
    """Return a mapping of file_id (str) -> symbol count."""
    counts: dict[str, int] = {}
    for sym in symbols:
        key = str(sym.file_id)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _build_networkx_graph(
    files: list[CodeFile],
    internal_deps: list[Dependency],
) -> nx.DiGraph:
    """Build a networkx DiGraph from CodeFile nodes and internal Dependency edges.

    Args:
        files: All CodeFile records for the repository.
        internal_deps: Only INTERNAL Dependency records (to_file_id is not None).

    Returns:
        Directed graph with file UUIDs (as strings) as node identifiers.
    """
    G: nx.DiGraph = nx.DiGraph()

    for cf in files:
        G.add_node(str(cf.id))

    for dep in internal_deps:
        if dep.to_file_id is None:
            continue
        G.add_edge(str(dep.from_file_id), str(dep.to_file_id), import_name=dep.import_name)

    return G


def _detect_cycles(G: nx.DiGraph) -> tuple[bool, int]:
    """Return (has_cycles, cycle_count) for the given digraph.

    ``cycle_count`` is the number of simple cycles found (capped at 1000 to
    avoid exhausting memory on pathological graphs).
    """
    try:
        nx.find_cycle(G)
        has_cycles = True
    except nx.NetworkXNoCycle:
        return False, 0

    cycle_count = 0
    for _ in nx.simple_cycles(G):
        cycle_count += 1
        if cycle_count >= 1000:
            break  # safety cap

    return True, cycle_count


def _compute_node_metrics(
    G: nx.DiGraph,
) -> dict[str, dict[str, Any]]:
    """Compute per-node metrics dictionary.

    Returns:
        node_id -> {in_degree, out_degree, pagerank, is_entry_point, is_leaf}
    """
    if G.number_of_nodes() == 0:
        return {}

    pagerank: dict[str, float] = nx.pagerank(G, alpha=0.85)

    metrics: dict[str, dict[str, Any]] = {}
    for node in G.nodes():
        in_deg = G.in_degree(node)
        out_deg = G.out_degree(node)
        metrics[node] = {
            "in_degree": in_deg,
            "out_degree": out_deg,
            "pagerank": round(pagerank.get(node, 0.0), 8),
            "is_entry_point": (in_deg == 0 and out_deg > 0),
            "is_leaf": (out_deg == 0),
        }

    return metrics


def _serialize_graph(
    G: nx.DiGraph,
    files: list[CodeFile],
    internal_deps: list[Dependency],
    symbol_counts: dict[str, int],
    node_metrics: dict[str, dict[str, Any]],
    truncate: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Serialise nodes and edges to JSONB-friendly Python dicts.

    When *truncate* is True only the top _MAX_DB_NODES nodes by PageRank are
    included, plus all edges between those nodes.
    """
    file_map = {str(cf.id): cf for cf in files}

    # Determine which nodes to include
    if truncate and G.number_of_nodes() > _MAX_DB_NODES:
        sorted_nodes = sorted(
            G.nodes(),
            key=lambda n: node_metrics.get(n, {}).get("pagerank", 0.0),
            reverse=True,
        )
        included_ids = set(sorted_nodes[:_MAX_DB_NODES])
    else:
        included_ids = set(G.nodes())

    nodes_out: list[dict[str, Any]] = []
    for node_id in included_ids:
        cf = file_map.get(node_id)
        if cf is None:
            continue
        m = node_metrics.get(node_id, {
            "in_degree": 0, "out_degree": 0, "pagerank": 0.0,
            "is_entry_point": False, "is_leaf": True,
        })
        nodes_out.append({
            "id": node_id,
            "path": cf.path,
            "language": cf.language,
            "symbol_count": symbol_counts.get(node_id, 0),
            "metrics": m,
        })

    edges_out: list[dict[str, Any]] = []
    for dep in internal_deps:
        from_id = str(dep.from_file_id)
        to_id = str(dep.to_file_id) if dep.to_file_id else None
        if to_id is None:
            continue
        if from_id not in included_ids or to_id not in included_ids:
            continue
        edges_out.append({
            "from_file_id": from_id,
            "to_file_id": to_id,
            "import_name": dep.import_name,
        })

    return nodes_out, edges_out


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def build_graph(
    repo: Repository,
    db: AsyncSession,
    upload_dir: str = "./uploads",
) -> RepositoryGraph:
    """Build and persist the dependency graph for a repository.

    Steps:
    1. Load all CodeFiles and internal Dependency rows from the DB.
    2. Build a networkx DiGraph.
    3. Compute PageRank + per-node metrics.
    4. Detect cycles — update Repository columns.
    5. Serialise to dicts; truncate if >5000 files.
    6. Persist full graph to disk as ``graph.json``.
    7. Upsert RepositoryGraph row in the DB.

    Args:
        repo: Repository ORM instance.
        db: Async SQLAlchemy session.
        upload_dir: Base uploads directory (default ``./uploads``).

    Returns:
        Persisted RepositoryGraph ORM instance.
    """
    logger.info("Building dependency graph for repo %s", repo.id)

    # ---- Update AnalysisJob phase ----------------------------------------
    job_result = await db.execute(
        select(AnalysisJob).where(AnalysisJob.repository_id == repo.id)
    )
    job = job_result.scalar_one_or_none()
    if job:
        job.phase = "graph"
        job.status = JobStatus.RUNNING
        job.progress = 70
        await db.flush()

    # ---- Load data from DB -------------------------------------------------
    files_result = await db.execute(
        select(CodeFile).where(CodeFile.repository_id == repo.id)
    )
    files: list[CodeFile] = list(files_result.scalars().all())

    deps_result = await db.execute(
        select(Dependency).where(
            Dependency.repository_id == repo.id,
            Dependency.dependency_type == DependencyType.INTERNAL,
            Dependency.to_file_id.is_not(None),
        )
    )
    internal_deps: list[Dependency] = list(deps_result.scalars().all())

    # Count symbols per file
    sym_counts_result = await db.execute(
        select(Symbol.file_id, func.count(Symbol.id).label("cnt"))
        .where(Symbol.repository_id == repo.id)
        .group_by(Symbol.file_id)
    )
    symbol_counts: dict[str, int] = {
        str(row.file_id): row.cnt for row in sym_counts_result
    }

    # ---- Build graph -------------------------------------------------------
    G = _build_networkx_graph(files, internal_deps)
    node_metrics = _compute_node_metrics(G)
    has_cycles, cycle_count = _detect_cycles(G)

    # Update Repository cycle columns
    repo.has_cycles = has_cycles
    repo.cycle_count = cycle_count

    # ---- Aggregate metrics -------------------------------------------------
    entry_point_count = sum(
        1 for m in node_metrics.values() if m["is_entry_point"]
    )
    leaf_count = sum(
        1 for m in node_metrics.values() if m["is_leaf"]
    )
    aggregate_metrics: dict[str, Any] = {
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "has_cycles": has_cycles,
        "cycle_count": cycle_count,
        "entry_point_count": entry_point_count,
        "leaf_count": leaf_count,
    }

    # ---- Serialise ---------------------------------------------------------
    large_repo = G.number_of_nodes() > 5000
    nodes_out, edges_out = _serialize_graph(
        G, files, internal_deps, symbol_counts, node_metrics, truncate=large_repo
    )

    # Write full graph to disk for large repos
    graph_dir = Path(upload_dir) / str(repo.id)
    graph_dir.mkdir(parents=True, exist_ok=True)
    graph_path = graph_dir / "graph.json"
    full_nodes, full_edges = _serialize_graph(
        G, files, internal_deps, symbol_counts, node_metrics, truncate=False
    )
    graph_path.write_text(
        json.dumps(
            {"metrics": aggregate_metrics, "nodes": full_nodes, "edges": full_edges},
            default=str,
        ),
        encoding="utf-8",
    )
    logger.info("Wrote full graph to %s (%d nodes, %d edges)", graph_path, len(full_nodes), len(full_edges))

    # ---- Upsert RepositoryGraph row ----------------------------------------
    existing_result = await db.execute(
        select(RepositoryGraph).where(RepositoryGraph.repository_id == repo.id)
    )
    repo_graph = existing_result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if repo_graph is None:
        repo_graph = RepositoryGraph(
            repository_id=repo.id,
            nodes=nodes_out,
            edges=edges_out,
            metrics=aggregate_metrics,
            generated_at=now,
        )
        db.add(repo_graph)
    else:
        repo_graph.nodes = nodes_out
        repo_graph.edges = edges_out
        repo_graph.metrics = aggregate_metrics
        repo_graph.generated_at = now

    await db.flush()
    logger.info(
        "Graph for repo %s: %d nodes, %d edges, cycles=%s",
        repo.id, len(nodes_out), len(edges_out), has_cycles,
    )
    return repo_graph
