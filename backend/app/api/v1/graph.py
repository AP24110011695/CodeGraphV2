"""Graph API endpoints.

Exposes:
  GET /api/v1/repositories/{repo_id}/graph
  GET /api/v1/repositories/{repo_id}/graph/node/{file_id}
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.exceptions import NotFoundError
from app.models.code_file import CodeFile
from app.models.dependency import Dependency, DependencyType
from app.models.repository_graph import RepositoryGraph
from app.models.symbol import Symbol
from app.schemas.graph import (
    DependencyInfo,
    EdgeRecord,
    GraphMetrics,
    GraphResponse,
    NodeDetailResponse,
    NodeMetrics,
    NodeRecord,
    SymbolInfo,
)
from app.services.ingestion import get_repository

router = APIRouter(prefix="/repositories", tags=["graph"])


# ---------------------------------------------------------------------------
# GET /repositories/{repo_id}/graph
# ---------------------------------------------------------------------------


@router.get(
    "/{repo_id}/graph",
    response_model=GraphResponse,
    summary="Get the dependency graph for a repository",
    responses={
        404: {"description": "Repository or graph not found"},
    },
)
async def get_graph(
    repo_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GraphResponse:
    """Return the serialised dependency graph stored for *repo_id*.

    The graph is computed during the pipeline (after parsing) and stored as
    JSONB in the ``repository_graph`` table.  Call the parse endpoint first if
    the graph has not been built yet.
    """
    # Verify repo exists
    try:
        await get_repository(repo_id, db)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_id}' not found.",
        )

    result = await db.execute(
        select(RepositoryGraph).where(RepositoryGraph.repository_id == repo_id)
    )
    repo_graph = result.scalar_one_or_none()
    if repo_graph is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Graph not found for this repository. "
                "Run the parse pipeline first."
            ),
        )

    # Deserialise stored JSONB into schema objects
    nodes = [
        NodeRecord(
            id=n["id"],
            path=n["path"],
            language=n.get("language"),
            symbol_count=n.get("symbol_count", 0),
            metrics=NodeMetrics(**n["metrics"]),
        )
        for n in repo_graph.nodes
    ]
    edges = [
        EdgeRecord(
            from_file_id=e["from_file_id"],
            to_file_id=e["to_file_id"],
            import_name=e.get("import_name", ""),
        )
        for e in repo_graph.edges
    ]
    metrics = GraphMetrics(**repo_graph.metrics)

    return GraphResponse(
        repository_id=repo_id,
        generated_at=repo_graph.generated_at,
        metrics=metrics,
        nodes=nodes,
        edges=edges,
    )


# ---------------------------------------------------------------------------
# GET /repositories/{repo_id}/graph/node/{file_id}
# ---------------------------------------------------------------------------


@router.get(
    "/{repo_id}/graph/node/{file_id}",
    response_model=NodeDetailResponse,
    summary="Get detailed graph info for a single file node",
    responses={
        404: {"description": "Repository, graph, or file not found"},
    },
)
async def get_graph_node(
    repo_id: uuid.UUID,
    file_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NodeDetailResponse:
    """Return detailed graph info for a specific file node.

    Includes:
    - The file's computed graph metrics (in/out degree, pagerank, …)
    - All symbols extracted from the file
    - Direct dependencies (files this file imports)
    - Direct dependents (files that import this file)
    """
    # Verify repo exists
    try:
        await get_repository(repo_id, db)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository '{repo_id}' not found.",
        )

    # Fetch the stored graph to get precomputed metrics
    graph_result = await db.execute(
        select(RepositoryGraph).where(RepositoryGraph.repository_id == repo_id)
    )
    repo_graph = graph_result.scalar_one_or_none()
    if repo_graph is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Graph not found. Run the parse pipeline first.",
        )

    # Find the node in the stored data
    file_id_str = str(file_id)
    node_data = next(
        (n for n in repo_graph.nodes if n["id"] == file_id_str), None
    )
    if node_data is None:
        # Node may have been excluded (truncated large graph) — fall back to DB
        cf_result = await db.execute(
            select(CodeFile).where(
                CodeFile.id == file_id,
                CodeFile.repository_id == repo_id,
            )
        )
        cf = cf_result.scalar_one_or_none()
        if cf is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File '{file_id}' not found in repository '{repo_id}'.",
            )
        # Build minimal metrics on the fly from edges in the stored graph
        in_deg = sum(1 for e in repo_graph.edges if e["to_file_id"] == file_id_str)
        out_deg = sum(1 for e in repo_graph.edges if e["from_file_id"] == file_id_str)
        node_data = {
            "id": file_id_str,
            "path": cf.path,
            "language": cf.language,
            "symbol_count": 0,
            "metrics": {
                "in_degree": in_deg,
                "out_degree": out_deg,
                "pagerank": 0.0,
                "is_entry_point": in_deg == 0 and out_deg > 0,
                "is_leaf": out_deg == 0,
            },
        }

    # Symbols
    syms_result = await db.execute(
        select(Symbol).where(
            Symbol.file_id == file_id,
            Symbol.repository_id == repo_id,
        )
    )
    symbols: list[SymbolInfo] = [
        SymbolInfo(
            id=str(s.id),
            name=s.name,
            kind=str(s.kind),
            start_line=s.start_line,
            end_line=s.end_line,
        )
        for s in syms_result.scalars().all()
    ]

    # Dependencies (files this file imports internally)
    deps_out_result = await db.execute(
        select(Dependency, CodeFile)
        .join(CodeFile, CodeFile.id == Dependency.to_file_id)
        .where(
            Dependency.from_file_id == file_id,
            Dependency.repository_id == repo_id,
            Dependency.dependency_type == DependencyType.INTERNAL,
        )
    )
    dependencies: list[DependencyInfo] = [
        DependencyInfo(
            file_id=str(cf.id),
            path=cf.path,
            language=cf.language,
            import_name=dep.import_name,
        )
        for dep, cf in deps_out_result.all()
    ]

    # Dependents (files that import this file)
    deps_in_result = await db.execute(
        select(Dependency, CodeFile)
        .join(CodeFile, CodeFile.id == Dependency.from_file_id)
        .where(
            Dependency.to_file_id == file_id,
            Dependency.repository_id == repo_id,
            Dependency.dependency_type == DependencyType.INTERNAL,
        )
    )
    dependents: list[DependencyInfo] = [
        DependencyInfo(
            file_id=str(cf.id),
            path=cf.path,
            language=cf.language,
            import_name=dep.import_name,
        )
        for dep, cf in deps_in_result.all()
    ]

    return NodeDetailResponse(
        id=node_data["id"],
        path=node_data["path"],
        language=node_data.get("language"),
        symbol_count=node_data.get("symbol_count", 0),
        metrics=NodeMetrics(**node_data["metrics"]),
        symbols=symbols,
        dependencies=dependencies,
        dependents=dependents,
    )
