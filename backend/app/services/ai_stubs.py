"""Legacy AI compatibility wrappers.

This module is retained for backward compatibility only.
Active runtime AI behavior is implemented in `app.services.ai_service`.
"""

from typing import Any

from app.services.ai_service import (
    draft_intervention_narratives,
    suggest_concept_tags as _suggest_concept_tags,
    suggest_prerequisite_edges as _suggest_prerequisite_edges,
)

async def suggest_concept_tags(question_text: str) -> list[dict[str, Any]]:
    """Compatibility wrapper to `app.services.ai_service.suggest_concept_tags`."""
    result = await _suggest_concept_tags(question_text, concept_catalog=[])
    return result.get("suggestions", [])


async def suggest_prerequisite_edges(
    concepts: list[str],
) -> list[dict[str, Any]]:
    """Compatibility wrapper to `app.services.ai_service.suggest_prerequisite_edges`."""
    result = await _suggest_prerequisite_edges(concepts, context="")
    return result.get("suggestions", [])


async def generate_cluster_interventions(
    cluster_centroid: dict[str, float],
    weak_concepts: list[str],
) -> list[str]:
    """Compatibility wrapper that returns draft intervention descriptions."""
    result = await draft_intervention_narratives(
        cluster_centroid=cluster_centroid,
        weak_concepts=weak_concepts,
    )
    drafts = result.get("drafts", [])
    if drafts:
        return [d.get("description", "") for d in drafts if d.get("description")]
    return [
        f"Review session recommended for '{c}' - consider practice problems and targeted exercises."
        for c in weak_concepts
    ]
