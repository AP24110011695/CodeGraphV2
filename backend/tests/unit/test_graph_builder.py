"""Graph algorithm coverage for disconnected components and PageRank invariants."""

import networkx as nx

from app.services.graph_builder import _compute_node_metrics, _detect_cycles


def test_disconnected_subgraphs_have_metrics_for_every_node() -> None:
    graph = nx.DiGraph([("a", "b"), ("c", "d")])
    metrics = _compute_node_metrics(graph)

    assert set(metrics) == {"a", "b", "c", "d"}
    assert metrics["a"]["is_entry_point"] is True
    assert metrics["d"]["is_leaf"] is True
    assert _detect_cycles(graph) == (False, 0)


def test_pagerank_is_normalized_for_disconnected_graphs() -> None:
    graph = nx.DiGraph([("a", "b"), ("c", "d")])
    metrics = _compute_node_metrics(graph)

    assert abs(sum(item["pagerank"] for item in metrics.values()) - 1.0) < 1e-6
