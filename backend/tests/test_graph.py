"""Tests for graph service: DAG validation, cycle detection, patch operations."""

import pytest

from app.schemas.schemas import GraphEdge, GraphNode, GraphPatchRequest
from app.services.graph_service import (
    apply_patch,
    build_graph,
    get_topological_order,
    graph_to_json,
    validate_graph,
)


class TestBuildGraph:

    def test_basic_build(self, sample_graph_json):
        G = build_graph(sample_graph_json)
        assert len(G.nodes) == 4
        assert len(G.edges) == 3

    def test_empty_graph(self):
        G = build_graph({"nodes": [], "edges": []})
        assert len(G.nodes) == 0

    def test_roundtrip(self, sample_graph_json):
        G = build_graph(sample_graph_json)
        result = graph_to_json(G)
        assert len(result["nodes"]) == 4
        assert len(result["edges"]) == 3


class TestValidateGraph:

    def test_valid_dag(self, sample_graph_json):
        is_valid, errors, cycle = validate_graph(sample_graph_json)
        assert is_valid
        assert errors == []
        assert cycle is None

    def test_cycle_detection(self, sample_graph_with_cycle):
        is_valid, errors, cycle = validate_graph(sample_graph_with_cycle)
        assert not is_valid
        assert len(errors) > 0
        assert cycle is not None

    def test_missing_edge_node(self):
        graph = {
            "nodes": [{"id": "A", "label": "A"}],
            "edges": [{"source": "A", "target": "MISSING", "weight": 0.5}],
        }
        is_valid, errors, _ = validate_graph(graph)
        assert not is_valid
        assert any("MISSING" in e.message for e in errors)

    def test_invalid_weight(self):
        graph = {
            "nodes": [{"id": "A", "label": "A"}, {"id": "B", "label": "B"}],
            "edges": [{"source": "A", "target": "B", "weight": 1.5}],
        }
        is_valid, errors, _ = validate_graph(graph)
        assert not is_valid

    def test_negative_weight(self):
        graph = {
            "nodes": [{"id": "A", "label": "A"}, {"id": "B", "label": "B"}],
            "edges": [{"source": "A", "target": "B", "weight": -0.1}],
        }
        is_valid, errors, _ = validate_graph(graph)
        assert not is_valid


class TestTopologicalOrder:

    def test_returns_order(self, sample_graph_json):
        G = build_graph(sample_graph_json)
        order = get_topological_order(G)
        assert len(order) == 4
        assert order.index("C_limits") < order.index("C_derivatives")
        assert order.index("C_derivatives") < order.index("C_chain_rule")
        assert order.index("C_derivatives") < order.index("C_integrals")


class TestApplyPatch:

    def test_add_node(self, sample_graph_json):
        patch = GraphPatchRequest(
            add_nodes=[GraphNode(id="C_new", label="New Concept")],
        )
        result, is_dag, cycle, errors = apply_patch(sample_graph_json, patch)
        assert is_dag
        assert errors == []
        assert len(result["nodes"]) == 5

    def test_remove_node(self, sample_graph_json):
        patch = GraphPatchRequest(
            remove_nodes=["C_chain_rule"],
        )
        result, is_dag, cycle, errors = apply_patch(sample_graph_json, patch)
        assert is_dag
        node_ids = {n["id"] for n in result["nodes"]}
        assert "C_chain_rule" not in node_ids

    def test_add_edge(self, sample_graph_json):
        patch = GraphPatchRequest(
            add_edges=[GraphEdge(source="C_limits", target="C_integrals", weight=0.3)],
        )
        result, is_dag, cycle, errors = apply_patch(sample_graph_json, patch)
        assert is_dag
        assert len(result["edges"]) == 4

    def test_add_cycle_blocked(self, sample_graph_json):
        patch = GraphPatchRequest(
            add_edges=[GraphEdge(source="C_chain_rule", target="C_limits", weight=0.5)],
        )
        result, is_dag, cycle, errors = apply_patch(sample_graph_json, patch)
        assert not is_dag
        assert cycle is not None
        assert len(errors) > 0

    def test_duplicate_node_error(self, sample_graph_json):
        patch = GraphPatchRequest(
            add_nodes=[GraphNode(id="C_limits", label="Duplicate")],
        )
        result, is_dag, cycle, errors = apply_patch(sample_graph_json, patch)
        assert len(errors) > 0

    def test_remove_nonexistent_node_error(self, sample_graph_json):
        patch = GraphPatchRequest(remove_nodes=["DOES_NOT_EXIST"])
        result, is_dag, cycle, errors = apply_patch(sample_graph_json, patch)
        assert len(errors) > 0
