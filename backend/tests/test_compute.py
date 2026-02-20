"""Unit tests for the deterministic readiness inference engine.

Covers:
  - All four stages of the readiness pipeline
  - Confidence estimation at all threshold boundaries
  - Class aggregates computation
  - NaN guards and determinism
  - Edge cases: single concept, no edges, disconnected nodes, zero weights
"""

import numpy as np
import pytest

from app.services.compute_service import (
    compute_class_aggregates,
    compute_confidence,
    compute_direct_readiness,
    compute_downstream_boost,
    compute_final_readiness,
    compute_prerequisite_penalty,
    run_readiness_pipeline,
)


class TestDirectReadiness:
    """Stage 1: Direct Readiness computation."""

    def test_basic_computation(self, sample_scores, sample_max_scores, sample_question_concept_map):
        concepts = sorted(sample_question_concept_map.keys())
        students = sorted(sample_scores.keys())
        result = compute_direct_readiness(
            sample_scores, sample_max_scores, sample_question_concept_map,
            concepts, students,
        )
        assert result.shape == (3, 4)
        assert not np.all(np.isnan(result))

    def test_perfect_score_gives_1(self):
        scores = {"S1": {"Q1": 10.0}}
        max_scores = {"Q1": 10.0}
        qcm = {"C1": [("Q1", 1.0)]}
        result = compute_direct_readiness(scores, max_scores, qcm, ["C1"], ["S1"])
        assert result[0, 0] == pytest.approx(1.0)

    def test_zero_score_gives_0(self):
        scores = {"S1": {"Q1": 0.0}}
        max_scores = {"Q1": 10.0}
        qcm = {"C1": [("Q1", 1.0)]}
        result = compute_direct_readiness(scores, max_scores, qcm, ["C1"], ["S1"])
        assert result[0, 0] == pytest.approx(0.0)

    def test_no_questions_gives_nan(self):
        scores = {"S1": {"Q1": 5.0}}
        max_scores = {"Q1": 10.0}
        qcm = {"C1": []}
        result = compute_direct_readiness(scores, max_scores, qcm, ["C1"], ["S1"])
        assert np.isnan(result[0, 0])

    def test_weighted_average(self):
        scores = {"S1": {"Q1": 10.0, "Q2": 0.0}}
        max_scores = {"Q1": 10.0, "Q2": 10.0}
        qcm = {"C1": [("Q1", 1.0), ("Q2", 1.0)]}
        result = compute_direct_readiness(scores, max_scores, qcm, ["C1"], ["S1"])
        assert result[0, 0] == pytest.approx(0.5)


class TestPrerequisitePenalty:
    """Stage 2: Upstream weakness propagation."""

    def test_no_edges_no_penalty(self):
        direct = np.array([[0.5]])
        adj = np.array([[0.0]])
        penalty = compute_prerequisite_penalty(direct, adj, ["C1"], ["C1"], 0.6)
        assert penalty[0, 0] == pytest.approx(0.0)

    def test_weak_parent_creates_penalty(self):
        direct = np.array([[0.3, 0.8]])  # parent weak, child strong
        adj = np.array([[0.0, 0.7], [0.0, 0.0]])
        penalty = compute_prerequisite_penalty(
            direct, adj, ["P", "C"], ["P", "C"], threshold=0.6,
        )
        expected = 0.7 * (0.6 - 0.3)
        assert penalty[0, 1] == pytest.approx(expected)

    def test_strong_parent_no_penalty(self):
        direct = np.array([[0.8, 0.5]])
        adj = np.array([[0.0, 0.7], [0.0, 0.0]])
        penalty = compute_prerequisite_penalty(
            direct, adj, ["P", "C"], ["P", "C"], threshold=0.6,
        )
        assert penalty[0, 1] == pytest.approx(0.0)


class TestDownstreamBoost:
    """Stage 3: Downstream validation boost with cap."""

    def test_boost_from_strong_child(self):
        direct = np.array([[0.5, 0.9]])
        adj = np.array([[0.0, 0.8], [0.0, 0.0]])
        boost = compute_downstream_boost(direct, adj, ["P", "C"])
        expected = min(0.8 * 0.4 * 0.9, 0.2)
        assert boost[0, 0] == pytest.approx(expected)

    def test_boost_capped_at_02(self):
        direct = np.array([[0.5, 1.0, 1.0]])
        adj = np.array([
            [0.0, 1.0, 1.0],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
        ])
        boost = compute_downstream_boost(direct, adj, ["P", "C1", "C2"])
        assert boost[0, 0] <= 0.2


class TestFinalReadiness:
    """Stage 4: Final clamped readiness."""

    def test_clamp_to_0_1(self):
        direct = np.array([[0.0]])
        penalty = np.array([[1.0]])
        boost = np.array([[0.0]])
        final = compute_final_readiness(direct, penalty, boost, 1.0, 0.3, 0.2)
        assert final[0, 0] >= 0.0
        assert final[0, 0] <= 1.0

    def test_nan_direct_treated_as_zero(self):
        direct = np.array([[np.nan]])
        penalty = np.array([[0.0]])
        boost = np.array([[0.1]])
        final = compute_final_readiness(direct, penalty, boost, 1.0, 0.3, 0.2)
        assert not np.isnan(final[0, 0])
        assert final[0, 0] >= 0.0

    def test_no_nan_in_output(self):
        direct = np.array([[np.nan, 0.5], [0.8, np.nan]])
        penalty = np.zeros((2, 2))
        boost = np.zeros((2, 2))
        final = compute_final_readiness(direct, penalty, boost, 1.0, 0.3, 0.2)
        assert not np.any(np.isnan(final))


class TestConfidence:
    """Confidence estimation at all threshold boundaries."""

    def test_high_confidence(self):
        qcm = {"C1": [("Q1", 1.0), ("Q2", 1.0), ("Q3", 1.0)]}
        max_scores = {"Q1": 5.0, "Q2": 5.0, "Q3": 5.0}
        direct = np.array([[0.7, 0.7]])
        adj = np.array([[0.0, 0.5], [0.0, 0.0]])
        conf = compute_confidence("C1", qcm, max_scores, direct, 0, ["C1", "C2"], adj)
        assert conf == "high"

    def test_low_tagged_questions(self):
        qcm = {"C1": [("Q1", 1.0)]}
        max_scores = {"Q1": 5.0}
        direct = np.array([[0.7]])
        adj = np.array([[0.0]])
        conf = compute_confidence("C1", qcm, max_scores, direct, 0, ["C1"], adj)
        assert conf == "low"

    def test_low_points_coverage(self):
        qcm = {"C1": [("Q1", 1.0), ("Q2", 1.0), ("Q3", 1.0)]}
        max_scores = {"Q1": 1.0, "Q2": 1.0, "Q3": 1.0}
        direct = np.array([[0.7]])
        adj = np.array([[0.0]])
        conf = compute_confidence("C1", qcm, max_scores, direct, 0, ["C1"], adj)
        assert conf == "low"


class TestClassAggregates:
    """Class-wide aggregate computation."""

    def test_basic_aggregates(self):
        final = np.array([[0.3, 0.8], [0.7, 0.9]])
        aggs = compute_class_aggregates(final, ["C1", "C2"], 0.6)
        assert len(aggs) == 2
        assert aggs[0]["concept_id"] == "C1"
        assert aggs[0]["below_threshold_count"] == 1


class TestFullPipeline:
    """End-to-end pipeline tests."""

    def test_deterministic(
        self, sample_scores, sample_max_scores, sample_question_concept_map, sample_graph_json,
    ):
        r1 = run_readiness_pipeline(
            sample_scores, sample_max_scores, sample_question_concept_map,
            sample_graph_json,
        )
        r2 = run_readiness_pipeline(
            sample_scores, sample_max_scores, sample_question_concept_map,
            sample_graph_json,
        )
        for a, b in zip(r1["readiness_results"], r2["readiness_results"]):
            assert a["final_readiness"] == b["final_readiness"]
            assert a["confidence"] == b["confidence"]

    def test_no_nan_in_final_output(
        self, sample_scores, sample_max_scores, sample_question_concept_map, sample_graph_json,
    ):
        result = run_readiness_pipeline(
            sample_scores, sample_max_scores, sample_question_concept_map,
            sample_graph_json,
        )
        for r in result["readiness_results"]:
            assert r["final_readiness"] is not None
            assert 0.0 <= r["final_readiness"] <= 1.0

    def test_all_values_in_range(
        self, sample_scores, sample_max_scores, sample_question_concept_map, sample_graph_json,
    ):
        result = run_readiness_pipeline(
            sample_scores, sample_max_scores, sample_question_concept_map,
            sample_graph_json,
        )
        mat = result["final_readiness_matrix"]
        assert np.all(mat >= 0.0)
        assert np.all(mat <= 1.0)
        assert not np.any(np.isnan(mat))

    def test_single_concept_no_edges(self):
        scores = {"S1": {"Q1": 7.0}}
        max_scores = {"Q1": 10.0}
        qcm = {"C1": [("Q1", 1.0)]}
        graph = {"nodes": [{"id": "C1", "label": "C1"}], "edges": []}
        result = run_readiness_pipeline(scores, max_scores, qcm, graph)
        assert len(result["readiness_results"]) == 1
        assert result["readiness_results"][0]["final_readiness"] == pytest.approx(0.7)

    def test_disconnected_nodes(self):
        scores = {"S1": {"Q1": 5.0, "Q2": 8.0}}
        max_scores = {"Q1": 10.0, "Q2": 10.0}
        qcm = {"C1": [("Q1", 1.0)], "C2": [("Q2", 1.0)]}
        graph = {
            "nodes": [{"id": "C1", "label": "C1"}, {"id": "C2", "label": "C2"}],
            "edges": [],
        }
        result = run_readiness_pipeline(scores, max_scores, qcm, graph)
        results_map = {r["concept_id"]: r for r in result["readiness_results"]}
        assert results_map["C1"]["final_readiness"] == pytest.approx(0.5)
        assert results_map["C2"]["final_readiness"] == pytest.approx(0.8)
