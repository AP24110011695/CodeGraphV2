"""Pydantic schemas for the dependency graph API."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class NodeMetrics(BaseModel):
    """Per-node computed graph metrics."""

    in_degree: int = Field(description="Number of files that import this file.")
    out_degree: int = Field(description="Number of files this file imports (internal).")
    pagerank: float = Field(description="PageRank score (alpha=0.85).")
    is_entry_point: bool = Field(
        description="True when in_degree=0 and out_degree>0 (nothing imports this file, but it imports others)."
    )
    is_leaf: bool = Field(
        description="True when out_degree=0 (this file imports nothing internally)."
    )


class NodeRecord(BaseModel):
    """A single node in the dependency graph."""

    id: str = Field(description="CodeFile UUID as string.")
    path: str = Field(description="Repository-relative file path.")
    language: str | None = Field(default=None, description="Detected language.")
    symbol_count: int = Field(default=0, description="Number of extracted symbols.")
    metrics: NodeMetrics


class EdgeRecord(BaseModel):
    """A directed edge representing a file-level dependency (internal only)."""

    from_file_id: str
    to_file_id: str
    import_name: str = Field(description="The imported name / module alias.")


class GraphMetrics(BaseModel):
    """Aggregate graph-level metrics."""

    node_count: int
    edge_count: int
    has_cycles: bool
    cycle_count: int
    entry_point_count: int
    leaf_count: int


class GraphResponse(BaseModel):
    """Full serialized dependency graph for a repository."""

    repository_id: uuid.UUID
    generated_at: datetime
    metrics: GraphMetrics
    nodes: list[NodeRecord]
    edges: list[EdgeRecord]


# ---------------------------------------------------------------------------
# Node detail endpoint schemas
# ---------------------------------------------------------------------------


class DependencyInfo(BaseModel):
    """A single dependency link (one hop)."""

    file_id: str
    path: str
    language: str | None = None
    import_name: str


class SymbolInfo(BaseModel):
    """Slim symbol summary used in node detail responses."""

    id: str
    name: str
    kind: str
    start_line: int
    end_line: int


class NodeDetailResponse(BaseModel):
    """Detailed view of a single graph node."""

    id: str
    path: str
    language: str | None = None
    symbol_count: int
    metrics: NodeMetrics
    symbols: list[SymbolInfo] = Field(
        default_factory=list,
        description="Symbols extracted from this file.",
    )
    dependencies: list[DependencyInfo] = Field(
        default_factory=list,
        description="Files this file directly imports.",
    )
    dependents: list[DependencyInfo] = Field(
        default_factory=list,
        description="Files that directly import this file.",
    )
