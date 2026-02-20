"""Tests for clustering service and intervention ranking."""

import numpy as np
import pytest

from app.services.cluster_service import rank_interventions, run_clustering


class TestClustering:

    def test_basic_clustering(self):
        matrix = np.array([
            [0.9, 0.1],
            [0.8, 0.2],
            [0.1, 0.9],
            [0.2, 0.8],
        ])
        result = run_clustering(matrix, ["C1", "C2"], ["S1", "S2", "S3", "S4"], k=2)
        assert len(result["clusters"]) == 2
        assert sum(c["student_count"] for c in result["clusters"]) == 4

    def test_single_student_fallback(self):
        matrix = np.array([[0.5, 0.3]])
        result = run_clustering(matrix, ["C1", "C2"], ["S1"], k=4)
        assert len(result["clusters"]) == 1
        assert result["clusters"][0]["student_count"] == 1

    def test_deterministic(self):
        matrix = np.random.RandomState(42).rand(20, 5)
        r1 = run_clustering(matrix, [f"C{i}" for i in range(5)], [f"S{i}" for i in range(20)])
        r2 = run_clustering(matrix, [f"C{i}" for i in range(5)], [f"S{i}" for i in range(20)])
        for c1, c2 in zip(r1["clusters"], r2["clusters"]):
            assert c1["cluster_label"] == c2["cluster_label"]
            assert c1["student_count"] == c2["student_count"]

    def test_top_weak_concepts(self):
        matrix = np.array([
            [0.9, 0.1, 0.5],
            [0.8, 0.2, 0.4],
        ])
        result = run_clustering(matrix, ["C1", "C2", "C3"], ["S1", "S2"], k=2)
        for cluster in result["clusters"]:
            assert len(cluster["top_weak_concepts"]) <= 3


class TestInterventionRanking:

    def test_basic_ranking(self):
        matrix = np.array([[0.3, 0.8], [0.4, 0.9]])
        adj = np.array([[0.0, 0.5], [0.0, 0.0]])
        result = rank_interventions(matrix, ["C1", "C2"], adj, threshold=0.6)
        assert len(result) > 0
        assert result[0]["impact"] >= result[-1]["impact"] if len(result) > 1 else True

    def test_no_interventions_when_all_above_threshold(self):
        matrix = np.array([[0.9, 0.8]])
        adj = np.array([[0.0, 0.5], [0.0, 0.0]])
        result = rank_interventions(matrix, ["C1", "C2"], adj, threshold=0.6)
        assert len(result) == 0

    def test_impact_formula(self):
        matrix = np.array([[0.3], [0.4]])
        adj = np.array([[0.0]])
        result = rank_interventions(matrix, ["C1"], adj, threshold=0.6)
        assert len(result) == 1
        expected_students = 2
        expected_downstream = max(1, 0)
        expected_readiness = np.mean([0.3, 0.4])
        expected_impact = expected_students * expected_downstream * (1 - expected_readiness)
        assert result[0]["impact"] == pytest.approx(expected_impact)
