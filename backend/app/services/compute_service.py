"""Readiness inference engine: Stages 1-4, confidence estimation, and class aggregates.

Implements the full computation pipeline from PRD §2.1-2.2:
  Stage 1: Direct Readiness (weighted average of question scores per concept)
  Stage 2: Prerequisite Penalty (upstream weakness propagation)
  Stage 3: Downstream Boost (validation from children, capped at 0.2)
  Stage 4: Final Readiness = clamp(alpha * direct - beta * penalty + gamma * boost)

Deterministic guarantees:
  - Sorted student/concept ordering for reproducibility
  - NaN guards on all final outputs
  - Fixed random seeds propagated to clustering
"""

from typing import Any, Optional

import networkx as nx
import numpy as np

from app.services.graph_service import build_graph, get_topological_order


def _sanitize_float(val: float) -> float:
    """Replace NaN/Inf with 0.0 — no NaN ever reaches the database."""
    if np.isnan(val) or np.isinf(val):
        return 0.0
    return float(val)


# ---------------------------------------------------------------------------
# Stage 1: Direct Readiness
# ---------------------------------------------------------------------------

def compute_direct_readiness(
    scores: dict[str, dict[str, float]],
    max_scores: dict[str, float],
    question_concept_map: dict[str, list[tuple[str, float]]],
    concepts: list[str],
    students: list[str],
) -> np.ndarray:
    """Compute DirectReadiness(S, C) for all student-concept pairs.

    DirectReadiness(S, C) = SUM(w_q * (score_q / maxscore_q)) / SUM(w_q)

    Returns:
        np.ndarray of shape (num_students, num_concepts) with NaN for missing.
    """
    n_students = len(students)
    n_concepts = len(concepts)
    student_idx = {s: i for i, s in enumerate(students)}
    concept_idx = {c: i for i, c in enumerate(concepts)}

    readiness = np.full((n_students, n_concepts), np.nan)

    for concept in concepts:
        c_idx = concept_idx[concept]
        tagged_questions = question_concept_map.get(concept, [])

        if not tagged_questions:
            continue

        for student in students:
            s_idx = student_idx[student]
            student_scores = scores.get(student, {})

            weighted_sum = 0.0
            weight_sum = 0.0

            for q_id, w_q in tagged_questions:
                if q_id in student_scores:
                    ms = max_scores.get(q_id, 1.0)
                    normalized = student_scores[q_id] / ms if ms > 0 else 0.0
                    weighted_sum += w_q * normalized
                    weight_sum += w_q

            if weight_sum > 0:
                readiness[s_idx, c_idx] = weighted_sum / weight_sum

    return readiness


# ---------------------------------------------------------------------------
# Stage 2: Prerequisite Penalty
# ---------------------------------------------------------------------------

def compute_prerequisite_penalty(
    direct_readiness: np.ndarray,
    adjacency: np.ndarray,
    concepts: list[str],
    topo_order: list[str],
    threshold: float,
) -> np.ndarray:
    """Compute PrerequisitePenalty(S, C) for all student-concept pairs.

    PrerequisitePenalty(S, C) = SUM over parents P of:
        edge_weight(P, C) * max(0, threshold - DirectReadiness(S, P))
    """
    concept_idx = {c: i for i, c in enumerate(concepts)}
    n_students = direct_readiness.shape[0]
    n_concepts = len(concepts)
    penalty = np.zeros((n_students, n_concepts))

    for concept in topo_order:
        c_idx = concept_idx[concept]
        for p_concept in concepts:
            p_idx = concept_idx[p_concept]
            edge_weight = adjacency[p_idx, c_idx]
            if edge_weight > 0:
                parent_readiness = np.where(
                    np.isnan(direct_readiness[:, p_idx]),
                    0.0,
                    direct_readiness[:, p_idx],
                )
                gap = np.maximum(0.0, threshold - parent_readiness)
                penalty[:, c_idx] += edge_weight * gap

    return penalty


# ---------------------------------------------------------------------------
# Stage 3: Downstream Boost
# ---------------------------------------------------------------------------

def compute_downstream_boost(
    direct_readiness: np.ndarray,
    adjacency: np.ndarray,
    concepts: list[str],
) -> np.ndarray:
    """Compute DownstreamBoost(S, P) for all student-concept pairs.

    DownstreamBoost(S, P) = SUM over children D of:
        validation_weight * DirectReadiness(S, D)
    where validation_weight = edge_weight * 0.4
    Boost is capped at 0.2.
    """
    concept_idx = {c: i for i, c in enumerate(concepts)}
    n_students = direct_readiness.shape[0]
    n_concepts = len(concepts)
    boost = np.zeros((n_students, n_concepts))

    for parent in concepts:
        p_idx = concept_idx[parent]
        for child in concepts:
            d_idx = concept_idx[child]
            edge_weight = adjacency[p_idx, d_idx]
            if edge_weight > 0:
                validation_weight = edge_weight * 0.4
                child_readiness = np.where(
                    np.isnan(direct_readiness[:, d_idx]),
                    0.0,
                    direct_readiness[:, d_idx],
                )
                boost[:, p_idx] += validation_weight * child_readiness

    boost = np.minimum(boost, 0.2)
    return boost


# ---------------------------------------------------------------------------
# Stage 4: Final Readiness
# ---------------------------------------------------------------------------

def compute_final_readiness(
    direct_readiness: np.ndarray,
    penalty: np.ndarray,
    boost: np.ndarray,
    alpha: float,
    beta: float,
    gamma: float,
) -> np.ndarray:
    """Compute FinalReadiness = clamp([0, 1], alpha * direct - beta * penalty + gamma * boost)."""
    direct = np.where(np.isnan(direct_readiness), 0.0, direct_readiness)
    final = alpha * direct - beta * penalty + gamma * boost
    final = np.clip(final, 0.0, 1.0)
    # NaN guard: replace any remaining NaN/Inf with 0
    final = np.where(np.isfinite(final), final, 0.0)
    return final


# ---------------------------------------------------------------------------
# Confidence Estimation (PRD §2.2)
# ---------------------------------------------------------------------------

def compute_confidence(
    concept: str,
    question_concept_map: dict[str, list[tuple[str, float]]],
    max_scores: dict[str, float],
    direct_readiness: np.ndarray,
    concept_idx: int,
    concepts: list[str],
    adjacency: np.ndarray,
) -> str:
    """Compute confidence level for a concept: min of 3 factors.

    Factors:
    1. Tagged questions: >= 3 -> high, 2 -> medium, 0-1 -> low
    2. Total points coverage: >= 10 -> high, 5-9 -> medium, < 5 -> low
    3. Variance across related concepts: < 0.15 -> high, 0.15-0.30 -> medium, > 0.30 -> low
    """
    levels = {"high": 3, "medium": 2, "low": 1}

    tagged = question_concept_map.get(concept, [])
    num_tagged = len(tagged)

    if num_tagged >= 3:
        f1 = "high"
    elif num_tagged == 2:
        f1 = "medium"
    else:
        f1 = "low"

    total_points = sum(max_scores.get(q_id, 1.0) for q_id, _ in tagged)
    if total_points >= 10:
        f2 = "high"
    elif total_points >= 5:
        f2 = "medium"
    else:
        f2 = "low"

    c_idx_val = concept_idx
    neighbors = []
    for i, c in enumerate(concepts):
        if adjacency[c_idx_val, i] > 0 or adjacency[i, c_idx_val] > 0:
            neighbors.append(i)

    if neighbors:
        related_indices = [c_idx_val] + neighbors
        means = []
        for ri in related_indices:
            vals = direct_readiness[:, ri]
            valid = vals[~np.isnan(vals)]
            if len(valid) > 0:
                means.append(float(np.mean(valid)))
        if len(means) > 1:
            variance = float(np.var(means))
        else:
            variance = 0.0
    else:
        variance = 0.0

    if variance < 0.15:
        f3 = "high"
    elif variance <= 0.30:
        f3 = "medium"
    else:
        f3 = "low"

    min_level = min(levels[f1], levels[f2], levels[f3])
    reverse = {3: "high", 2: "medium", 1: "low"}
    return reverse[min_level]


# ---------------------------------------------------------------------------
# Explanation Traces
# ---------------------------------------------------------------------------

def build_explanation_trace(
    student: str,
    concept: str,
    direct: Optional[float],
    penalty: float,
    boost: float,
    final: float,
    confidence: str,
    adjacency: np.ndarray,
    concepts: list[str],
    concept_idx_map: dict[str, int],
    direct_readiness: np.ndarray,
    student_idx: int,
    alpha: float,
    beta: float,
    gamma: float,
    threshold: float,
) -> dict[str, Any]:
    """Build a JSON-serializable explanation trace for one (student, concept)."""
    c_idx = concept_idx_map[concept]
    trace: dict[str, Any] = {
        "concept_id": concept,
        "student_id": student,
        "direct_readiness": direct,
        "confidence": confidence,
        "upstream_penalties": [],
        "downstream_boosts": [],
        "formula": {
            "alpha": alpha, "beta": beta, "gamma": gamma,
            "direct_component": _sanitize_float(alpha * (direct if direct is not None else 0.0)),
            "penalty_component": _sanitize_float(beta * penalty),
            "boost_component": _sanitize_float(gamma * boost),
            "final_readiness": _sanitize_float(final),
        },
    }

    for p_concept in concepts:
        p_idx = concept_idx_map[p_concept]
        edge_weight = adjacency[p_idx, c_idx]
        if edge_weight > 0:
            p_readiness = direct_readiness[student_idx, p_idx]
            p_val = float(p_readiness) if not np.isnan(p_readiness) else 0.0
            gap = max(0.0, threshold - p_val)
            if gap > 0:
                trace["upstream_penalties"].append({
                    "concept_id": p_concept,
                    "readiness": _sanitize_float(p_val),
                    "edge_weight": _sanitize_float(edge_weight),
                    "penalty_contribution": _sanitize_float(edge_weight * gap),
                })

    for d_concept in concepts:
        d_idx = concept_idx_map[d_concept]
        edge_weight = adjacency[c_idx, d_idx]
        if edge_weight > 0:
            d_readiness = direct_readiness[student_idx, d_idx]
            d_val = float(d_readiness) if not np.isnan(d_readiness) else 0.0
            validation_weight = edge_weight * 0.4
            trace["downstream_boosts"].append({
                "concept_id": d_concept,
                "readiness": _sanitize_float(d_val),
                "validation_weight": _sanitize_float(validation_weight),
                "boost_contribution": _sanitize_float(validation_weight * d_val),
            })

    return trace


# ---------------------------------------------------------------------------
# Class Aggregates
# ---------------------------------------------------------------------------

def compute_class_aggregates(
    final_readiness: np.ndarray,
    concepts: list[str],
    threshold: float,
) -> list[dict[str, Any]]:
    """Compute class-wide aggregate statistics per concept."""
    aggregates = []
    for i, concept in enumerate(concepts):
        vals = final_readiness[:, i]
        aggregates.append({
            "concept_id": concept,
            "mean_readiness": _sanitize_float(np.mean(vals)),
            "median_readiness": _sanitize_float(np.median(vals)),
            "std_readiness": _sanitize_float(np.std(vals)),
            "below_threshold_count": int(np.sum(vals < threshold)),
        })
    return aggregates


# ---------------------------------------------------------------------------
# Full Pipeline Orchestrator
# ---------------------------------------------------------------------------

def run_readiness_pipeline(
    scores: dict[str, dict[str, float]],
    max_scores: dict[str, float],
    question_concept_map: dict[str, list[tuple[str, float]]],
    graph_json: dict[str, Any],
    alpha: float = 1.0,
    beta: float = 0.3,
    gamma: float = 0.2,
    threshold: float = 0.6,
) -> dict[str, Any]:
    """Run the full readiness computation pipeline.

    Deterministic: sorted students/concepts, fixed seeds, NaN-free output.
    """
    G = build_graph(graph_json)
    # Stable sorted ordering for determinism
    concepts = sorted(G.nodes)
    students = sorted(scores.keys())
    concept_idx_map = {c: i for i, c in enumerate(concepts)}
    student_idx_map = {s: i for i, s in enumerate(students)}

    n_concepts = len(concepts)
    adjacency = np.zeros((n_concepts, n_concepts))
    for u, v, data in G.edges(data=True):
        adjacency[concept_idx_map[u], concept_idx_map[v]] = data.get("weight", 0.5)

    topo_order = get_topological_order(G)

    direct_readiness = compute_direct_readiness(
        scores, max_scores, question_concept_map, concepts, students,
    )

    penalty = compute_prerequisite_penalty(
        direct_readiness, adjacency, concepts, topo_order, threshold,
    )

    boost = compute_downstream_boost(direct_readiness, adjacency, concepts)

    final = compute_final_readiness(direct_readiness, penalty, boost, alpha, beta, gamma)

    # NaN integrity assertion — should never fire given our guards
    assert not np.any(np.isnan(final)), "NaN detected in final readiness output"
    assert np.all((final >= 0.0) & (final <= 1.0)), "Final readiness out of [0,1] range"

    readiness_results = []
    for student in students:
        s_idx = student_idx_map[student]
        for concept in concepts:
            c_idx = concept_idx_map[concept]
            dr = direct_readiness[s_idx, c_idx]
            dr_val = _sanitize_float(dr) if not np.isnan(dr) else None

            conf = compute_confidence(
                concept, question_concept_map, max_scores,
                direct_readiness, c_idx, concepts, adjacency,
            )

            trace = build_explanation_trace(
                student, concept, dr_val,
                _sanitize_float(penalty[s_idx, c_idx]),
                _sanitize_float(boost[s_idx, c_idx]),
                _sanitize_float(final[s_idx, c_idx]),
                conf,
                adjacency, concepts, concept_idx_map,
                direct_readiness, s_idx,
                alpha, beta, gamma, threshold,
            )

            readiness_results.append({
                "student_id": student,
                "concept_id": concept,
                "direct_readiness": dr_val,
                "prerequisite_penalty": _sanitize_float(penalty[s_idx, c_idx]),
                "downstream_boost": _sanitize_float(boost[s_idx, c_idx]),
                "final_readiness": _sanitize_float(final[s_idx, c_idx]),
                "confidence": conf,
                "explanation_trace": trace,
            })

    class_aggs = compute_class_aggregates(final, concepts, threshold)

    return {
        "readiness_results": readiness_results,
        "class_aggregates": class_aggs,
        "concepts": concepts,
        "students": students,
        "graph": G,
        "adjacency": adjacency,
        "direct_readiness_matrix": direct_readiness,
        "final_readiness_matrix": final,
    }
