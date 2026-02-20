"""Shared test fixtures for ConceptLens backend tests."""

import numpy as np
import pytest


@pytest.fixture
def sample_scores():
    """Sample scores dict: {student_id: {question_id: score}}."""
    return {
        "S001": {"Q1": 8.0, "Q2": 5.0, "Q3": 9.0},
        "S002": {"Q1": 6.0, "Q2": 3.0, "Q3": 7.0},
        "S003": {"Q1": 10.0, "Q2": 10.0, "Q3": 10.0},
    }


@pytest.fixture
def sample_max_scores():
    return {"Q1": 10.0, "Q2": 10.0, "Q3": 10.0}


@pytest.fixture
def sample_question_concept_map():
    """question-concept map: {concept_id: [(question_id, weight), ...]}."""
    return {
        "C_derivatives": [("Q1", 1.0), ("Q3", 0.8)],
        "C_limits": [("Q1", 0.5)],
        "C_integrals": [("Q2", 1.0)],
        "C_chain_rule": [("Q3", 1.0)],
    }


@pytest.fixture
def sample_graph_json():
    return {
        "nodes": [
            {"id": "C_limits", "label": "Limits"},
            {"id": "C_derivatives", "label": "Derivatives"},
            {"id": "C_chain_rule", "label": "Chain Rule"},
            {"id": "C_integrals", "label": "Integrals"},
        ],
        "edges": [
            {"source": "C_limits", "target": "C_derivatives", "weight": 0.7},
            {"source": "C_derivatives", "target": "C_chain_rule", "weight": 0.8},
            {"source": "C_derivatives", "target": "C_integrals", "weight": 0.5},
        ],
    }


@pytest.fixture
def sample_graph_with_cycle():
    return {
        "nodes": [
            {"id": "A", "label": "A"},
            {"id": "B", "label": "B"},
            {"id": "C", "label": "C"},
        ],
        "edges": [
            {"source": "A", "target": "B", "weight": 0.5},
            {"source": "B", "target": "C", "weight": 0.5},
            {"source": "C", "target": "A", "weight": 0.5},
        ],
    }
