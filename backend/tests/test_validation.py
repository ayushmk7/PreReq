"""Tests for validation services: CSV, graph, parameter, and AI-output validation."""

import pytest

from app.services.validation_service import (
    validate_concept_tag_suggestions,
    validate_file_limits,
    validate_parameter_ranges,
    validate_prereq_edge_suggestions,
)


class TestFileLimits:

    def test_within_limits(self):
        content = b"a" * 1000
        errors = validate_file_limits(content)
        assert errors == []

    def test_exceeds_size(self):
        content = b"a" * (51 * 1024 * 1024)
        errors = validate_file_limits(content)
        assert len(errors) == 1
        assert "size" in errors[0].message.lower()

    def test_exceeds_row_count(self):
        content = b"\n" * 600_000
        errors = validate_file_limits(content)
        assert len(errors) == 1
        assert "row" in errors[0].message.lower()


class TestConceptTagValidation:

    def test_valid_suggestions(self):
        suggestions = [
            {"concept_id": "C1", "confidence": 0.9, "rationale": "test"},
            {"concept_id": "C2", "confidence": 0.7, "rationale": "test"},
        ]
        valid, errors = validate_concept_tag_suggestions(suggestions, {"C1", "C2", "C3"})
        assert len(valid) == 2
        assert len(errors) == 0

    def test_unknown_concept(self):
        suggestions = [
            {"concept_id": "UNKNOWN", "confidence": 0.9, "rationale": "test"},
        ]
        valid, errors = validate_concept_tag_suggestions(suggestions, {"C1", "C2"})
        assert len(valid) == 0
        assert len(errors) == 1
        assert "Unknown" in errors[0]["error"]

    def test_duplicate_concept(self):
        suggestions = [
            {"concept_id": "C1", "confidence": 0.9, "rationale": "test"},
            {"concept_id": "C1", "confidence": 0.8, "rationale": "test2"},
        ]
        valid, errors = validate_concept_tag_suggestions(suggestions, {"C1"})
        assert len(valid) == 1
        assert len(errors) == 1

    def test_empty_concept_id(self):
        suggestions = [{"concept_id": "", "confidence": 0.9, "rationale": "test"}]
        valid, errors = validate_concept_tag_suggestions(suggestions, set())
        assert len(valid) == 0
        assert len(errors) == 1

    def test_confidence_out_of_range(self):
        suggestions = [{"concept_id": "C1", "confidence": 1.5, "rationale": "test"}]
        valid, errors = validate_concept_tag_suggestions(suggestions, {"C1"})
        assert len(valid) == 0
        assert len(errors) == 1


class TestPrereqEdgeValidation:

    def test_valid_edges(self):
        graph = {
            "nodes": [{"id": "A", "label": "A"}, {"id": "B", "label": "B"}],
            "edges": [],
        }
        suggestions = [{"source": "A", "target": "B", "weight": 0.5, "rationale": "test"}]
        valid, errors = validate_prereq_edge_suggestions(suggestions, graph)
        assert len(valid) == 1
        assert len(errors) == 0

    def test_self_loop(self):
        graph = {"nodes": [{"id": "A", "label": "A"}], "edges": []}
        suggestions = [{"source": "A", "target": "A", "weight": 0.5}]
        valid, errors = validate_prereq_edge_suggestions(suggestions, graph)
        assert len(valid) == 0
        assert "Self-loop" in errors[0]["error"]

    def test_unknown_source(self):
        graph = {"nodes": [{"id": "B", "label": "B"}], "edges": []}
        suggestions = [{"source": "UNKNOWN", "target": "B", "weight": 0.5}]
        valid, errors = validate_prereq_edge_suggestions(suggestions, graph)
        assert len(valid) == 0
        assert "does not exist" in errors[0]["error"]

    def test_duplicate_edge(self):
        graph = {
            "nodes": [{"id": "A", "label": "A"}, {"id": "B", "label": "B"}],
            "edges": [{"source": "A", "target": "B", "weight": 0.5}],
        }
        suggestions = [{"source": "A", "target": "B", "weight": 0.7}]
        valid, errors = validate_prereq_edge_suggestions(suggestions, graph)
        assert len(valid) == 0
        assert "already exists" in errors[0]["error"]

    def test_cycle_detection(self):
        graph = {
            "nodes": [{"id": "A", "label": "A"}, {"id": "B", "label": "B"}, {"id": "C", "label": "C"}],
            "edges": [
                {"source": "A", "target": "B", "weight": 0.5},
                {"source": "B", "target": "C", "weight": 0.5},
            ],
        }
        suggestions = [{"source": "C", "target": "A", "weight": 0.5}]
        valid, errors = validate_prereq_edge_suggestions(suggestions, graph)
        assert len(valid) == 0
        assert "cycle" in errors[0]["error"].lower()

    def test_weight_out_of_range(self):
        graph = {
            "nodes": [{"id": "A", "label": "A"}, {"id": "B", "label": "B"}],
            "edges": [],
        }
        suggestions = [{"source": "A", "target": "B", "weight": 1.5}]
        valid, errors = validate_prereq_edge_suggestions(suggestions, graph)
        assert len(valid) == 0
        assert "weight" in errors[0]["error"].lower()


class TestParameterRanges:

    def test_valid_parameters(self):
        errors = validate_parameter_ranges(
            {"alpha": 1.0, "beta": 0.3, "gamma": 0.2, "threshold": 0.6, "k": 4}
        )
        assert len(errors) == 0

    def test_alpha_out_of_range(self):
        errors = validate_parameter_ranges({"alpha": 10.0})
        assert len(errors) == 1

    def test_threshold_out_of_range(self):
        errors = validate_parameter_ranges({"threshold": 1.5})
        assert len(errors) == 1

    def test_k_too_small(self):
        errors = validate_parameter_ranges({"k": 1})
        assert len(errors) == 1

    def test_k_too_large(self):
        errors = validate_parameter_ranges({"k": 100})
        assert len(errors) == 1
