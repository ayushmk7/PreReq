"""Centralized validation service for all input types.

Covers:
  - CSV file size and row limits
  - AI suggestion output validation (concept IDs, edges, cycles)
  - Parameter range enforcement
  - Standardized error envelope
"""

from typing import Any, Optional

import networkx as nx

from app.schemas.schemas import ValidationError
from app.services.graph_service import build_graph

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_ROW_COUNT = 500_000


def validate_file_limits(content: bytes) -> list[ValidationError]:
    """Enforce PRD file size and row limits."""
    errors: list[ValidationError] = []
    if len(content) > MAX_FILE_SIZE_BYTES:
        errors.append(ValidationError(
            message=f"File exceeds maximum size of {MAX_FILE_SIZE_BYTES // (1024*1024)} MB",
        ))
    line_count = content.count(b"\n")
    if line_count > MAX_ROW_COUNT:
        errors.append(ValidationError(
            message=f"File exceeds maximum row count of {MAX_ROW_COUNT:,}",
        ))
    return errors


def validate_concept_tag_suggestions(
    suggestions: list[dict[str, Any]],
    valid_concept_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validate AI concept-tag suggestions against the concept catalog.

    Returns (valid_suggestions, validation_errors).
    """
    valid = []
    errors = []
    seen = set()

    for s in suggestions:
        concept_id = s.get("concept_id", "")
        confidence = s.get("confidence", 0.0)

        if not concept_id:
            errors.append({"concept_id": concept_id, "error": "Empty concept_id"})
            continue

        if valid_concept_ids and concept_id not in valid_concept_ids:
            errors.append({
                "concept_id": concept_id,
                "error": f"Unknown concept_id '{concept_id}' not in catalog",
            })
            continue

        if concept_id in seen:
            errors.append({
                "concept_id": concept_id,
                "error": f"Duplicate concept_id '{concept_id}'",
            })
            continue

        if not (0.0 <= confidence <= 1.0):
            errors.append({
                "concept_id": concept_id,
                "error": f"Confidence {confidence} out of [0, 1] range",
            })
            continue

        seen.add(concept_id)
        valid.append(s)

    return valid, errors


def validate_prereq_edge_suggestions(
    suggestions: list[dict[str, Any]],
    graph_json: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validate AI prerequisite-edge suggestions against graph constraints.

    Checks: node existence, self-loops, duplicate edges, weight range, and cycle creation.
    Returns (valid_suggestions, validation_errors).
    """
    valid = []
    errors = []

    node_ids = {n["id"] for n in graph_json.get("nodes", [])}
    existing_edges = {
        (e["source"], e["target"])
        for e in graph_json.get("edges", [])
    }

    G = build_graph(graph_json)

    for s in suggestions:
        source = s.get("source", "")
        target = s.get("target", "")
        weight = s.get("weight", 0.5)

        if source == target:
            errors.append({
                "source": source, "target": target,
                "error": "Self-loop: source and target are the same",
            })
            continue

        if source not in node_ids:
            errors.append({
                "source": source, "target": target,
                "error": f"Source node '{source}' does not exist in graph",
            })
            continue

        if target not in node_ids:
            errors.append({
                "source": source, "target": target,
                "error": f"Target node '{target}' does not exist in graph",
            })
            continue

        if (source, target) in existing_edges:
            errors.append({
                "source": source, "target": target,
                "error": "Duplicate: edge already exists in graph",
            })
            continue

        if not (0.0 <= weight <= 1.0):
            errors.append({
                "source": source, "target": target,
                "error": f"Edge weight {weight} out of [0, 1] range",
            })
            continue

        # Cycle check: temporarily add edge and test
        G.add_edge(source, target, weight=weight)
        if not nx.is_directed_acyclic_graph(G):
            try:
                cycle = nx.find_cycle(G, orientation="original")
                cycle_path = [e[0] for e in cycle] + [cycle[-1][1]]
            except nx.NetworkXNoCycle:
                cycle_path = []
            G.remove_edge(source, target)
            errors.append({
                "source": source, "target": target,
                "error": f"Would create cycle: {' -> '.join(cycle_path)}",
            })
            continue

        valid.append(s)

    return valid, errors


def validate_parameter_ranges(
    params: dict[str, Any],
) -> list[ValidationError]:
    """Validate parameter values are within acceptable ranges."""
    errors: list[ValidationError] = []

    ranges = {
        "alpha": (0.0, 5.0),
        "beta": (0.0, 5.0),
        "gamma": (0.0, 5.0),
        "threshold": (0.0, 1.0),
    }

    for key, (lo, hi) in ranges.items():
        val = params.get(key)
        if val is not None:
            if not isinstance(val, (int, float)):
                errors.append(ValidationError(
                    field=key,
                    message=f"{key} must be numeric, got {type(val).__name__}",
                ))
            elif val < lo or val > hi:
                errors.append(ValidationError(
                    field=key,
                    message=f"{key} must be in [{lo}, {hi}], got {val}",
                ))

    k = params.get("k")
    if k is not None:
        if not isinstance(k, int):
            errors.append(ValidationError(
                field="k",
                message=f"k must be an integer, got {type(k).__name__}",
            ))
        elif k < 2 or k > 20:
            errors.append(ValidationError(
                field="k",
                message=f"k must be in [2, 20], got {k}",
            ))

    return errors
