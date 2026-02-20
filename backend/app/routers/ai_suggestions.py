"""AI suggestion endpoints: concept tagging, graph edge suggestions, intervention drafting.

All AI outputs are persisted as pending suggestions requiring instructor review.
"""

import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_instructor
from app.database import get_db
from app.models.models import (
    AISuggestion,
    AuditLog,
    ConceptGraph,
    Exam,
    Question,
    QuestionConceptMap,
)
from app.schemas.schemas import (
    ApplySuggestionsRequest,
    ApplySuggestionsResponse,
    BulkReviewRequest,
    ConceptTagRequest,
    ConceptTagResponse,
    ConceptTagSuggestion,
    InterventionDraftItem,
    InterventionDraftRequest,
    InterventionDraftResponse,
    PrereqEdgeRequest,
    PrereqEdgeResponse,
    PrereqEdgeSuggestion,
    SuggestionListItem,
    SuggestionListResponse,
    SuggestionReviewAction,
)
from app.services.ai_service import (
    draft_intervention_narratives,
    suggest_concept_tags,
    suggest_prerequisite_edges,
)
from app.services.graph_service import apply_patch, build_graph, graph_to_json
from app.services.validation_service import (
    validate_concept_tag_suggestions,
    validate_prereq_edge_suggestions,
)

router = APIRouter(prefix="/api/v1/exams", tags=["AI Suggestions"])


# ---------------------------------------------------------------------------
# Suggest Concept Tags
# ---------------------------------------------------------------------------

@router.post("/{exam_id}/ai/suggest-tags", response_model=ConceptTagResponse)
async def suggest_tags(
    exam_id: UUID,
    body: ConceptTagRequest,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """Generate AI concept-tag suggestions for a question. Stored as pending review."""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Exam not found")

    # Build concept catalog from existing graph
    g_result = await db.execute(
        select(ConceptGraph)
        .where(ConceptGraph.exam_id == exam_id)
        .order_by(ConceptGraph.version.desc())
        .limit(1)
    )
    graph_row = g_result.scalar_one_or_none()
    if graph_row:
        catalog = [n["id"] for n in graph_row.graph_json.get("nodes", [])]
    else:
        catalog = body.concept_catalog

    ai_result = await suggest_concept_tags(body.question_text, catalog)

    if ai_result.get("error"):
        # Persist failed attempt for observability
        suggestion = AISuggestion(
            exam_id=exam_id,
            suggestion_type="concept_tag",
            status="pending",
            input_payload={"question_text": body.question_text, "catalog": catalog},
            output_payload={"suggestions": [], "error": ai_result["error"]},
            model=ai_result.get("model"),
            prompt_version=ai_result.get("prompt_version"),
            token_usage=ai_result.get("token_usage"),
            latency_ms=ai_result.get("latency_ms"),
            validation_errors=[{"error": ai_result["error"]}],
        )
        db.add(suggestion)
        await db.flush()

        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {ai_result['error']}",
        )

    raw_suggestions = ai_result.get("suggestions", [])
    valid_set = set(catalog) if catalog else set()
    valid_suggestions, validation_errors = validate_concept_tag_suggestions(
        raw_suggestions, valid_set,
    )

    suggestion = AISuggestion(
        exam_id=exam_id,
        suggestion_type="concept_tag",
        status="pending",
        input_payload={"question_text": body.question_text, "catalog": catalog},
        output_payload={"suggestions": valid_suggestions},
        model=ai_result.get("model"),
        prompt_version=ai_result.get("prompt_version"),
        token_usage=ai_result.get("token_usage"),
        latency_ms=ai_result.get("latency_ms"),
        validation_errors=validation_errors if validation_errors else None,
    )
    db.add(suggestion)
    await db.flush()
    await db.refresh(suggestion)

    return ConceptTagResponse(
        request_id=suggestion.request_id,
        suggestion_id=suggestion.id,
        suggestions=[
            ConceptTagSuggestion(
                concept_id=s["concept_id"],
                confidence=s.get("confidence", 0.5),
                rationale=s.get("rationale", ""),
            )
            for s in valid_suggestions
        ],
        model=ai_result.get("model", ""),
        prompt_version=ai_result.get("prompt_version", ""),
    )


# ---------------------------------------------------------------------------
# Suggest Prerequisite Edges
# ---------------------------------------------------------------------------

@router.post("/{exam_id}/ai/suggest-edges", response_model=PrereqEdgeResponse)
async def suggest_edges(
    exam_id: UUID,
    body: PrereqEdgeRequest,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """Generate AI prerequisite-edge suggestions. Stored as pending review."""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Exam not found")

    g_result = await db.execute(
        select(ConceptGraph)
        .where(ConceptGraph.exam_id == exam_id)
        .order_by(ConceptGraph.version.desc())
        .limit(1)
    )
    graph_row = g_result.scalar_one_or_none()
    graph_json = graph_row.graph_json if graph_row else {
        "nodes": [{"id": c, "label": c} for c in body.concepts],
        "edges": [],
    }

    ai_result = await suggest_prerequisite_edges(body.concepts, body.context)

    if ai_result.get("error"):
        suggestion = AISuggestion(
            exam_id=exam_id,
            suggestion_type="prereq_edge",
            status="pending",
            input_payload={"concepts": body.concepts, "context": body.context},
            output_payload={"suggestions": [], "error": ai_result["error"]},
            model=ai_result.get("model"),
            prompt_version=ai_result.get("prompt_version"),
            token_usage=ai_result.get("token_usage"),
            latency_ms=ai_result.get("latency_ms"),
            validation_errors=[{"error": ai_result["error"]}],
        )
        db.add(suggestion)
        await db.flush()

        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {ai_result['error']}",
        )

    raw_suggestions = ai_result.get("suggestions", [])
    valid_suggestions, validation_errors = validate_prereq_edge_suggestions(
        raw_suggestions, graph_json,
    )

    suggestion = AISuggestion(
        exam_id=exam_id,
        suggestion_type="prereq_edge",
        status="pending",
        input_payload={"concepts": body.concepts, "context": body.context},
        output_payload={"suggestions": valid_suggestions},
        model=ai_result.get("model"),
        prompt_version=ai_result.get("prompt_version"),
        token_usage=ai_result.get("token_usage"),
        latency_ms=ai_result.get("latency_ms"),
        validation_errors=validation_errors if validation_errors else None,
    )
    db.add(suggestion)
    await db.flush()
    await db.refresh(suggestion)

    return PrereqEdgeResponse(
        request_id=suggestion.request_id,
        suggestion_id=suggestion.id,
        suggestions=[
            PrereqEdgeSuggestion(
                source=s["source"],
                target=s["target"],
                weight=s.get("weight", 0.5),
                rationale=s.get("rationale", ""),
            )
            for s in valid_suggestions
        ],
        model=ai_result.get("model", ""),
        prompt_version=ai_result.get("prompt_version", ""),
    )


# ---------------------------------------------------------------------------
# Draft Intervention Narratives
# ---------------------------------------------------------------------------

@router.post("/{exam_id}/ai/draft-interventions", response_model=InterventionDraftResponse)
async def draft_interventions(
    exam_id: UUID,
    body: InterventionDraftRequest,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """Generate AI-drafted intervention suggestions. Stored as pending review."""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Exam not found")

    ai_result = await draft_intervention_narratives(
        cluster_centroid=body.cluster_centroid,
        weak_concepts=body.weak_concepts,
        student_count=body.student_count,
    )

    if ai_result.get("error"):
        suggestion = AISuggestion(
            exam_id=exam_id,
            suggestion_type="intervention",
            status="pending",
            input_payload=body.model_dump(),
            output_payload={"drafts": [], "error": ai_result["error"]},
            model=ai_result.get("model"),
            prompt_version=ai_result.get("prompt_version"),
            token_usage=ai_result.get("token_usage"),
            latency_ms=ai_result.get("latency_ms"),
            validation_errors=[{"error": ai_result["error"]}],
        )
        db.add(suggestion)
        await db.flush()

        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {ai_result['error']}",
        )

    drafts = ai_result.get("drafts", [])

    suggestion = AISuggestion(
        exam_id=exam_id,
        suggestion_type="intervention",
        status="pending",
        input_payload=body.model_dump(),
        output_payload={"drafts": drafts},
        model=ai_result.get("model"),
        prompt_version=ai_result.get("prompt_version"),
        token_usage=ai_result.get("token_usage"),
        latency_ms=ai_result.get("latency_ms"),
    )
    db.add(suggestion)
    await db.flush()
    await db.refresh(suggestion)

    return InterventionDraftResponse(
        request_id=suggestion.request_id,
        suggestion_id=suggestion.id,
        drafts=[
            InterventionDraftItem(
                concept_id=d.get("concept_id", ""),
                intervention_type=d.get("intervention_type", ""),
                description=d.get("description", ""),
                rationale=d.get("rationale", ""),
            )
            for d in drafts
        ],
        model=ai_result.get("model", ""),
        prompt_version=ai_result.get("prompt_version", ""),
    )


# ---------------------------------------------------------------------------
# List Suggestions
# ---------------------------------------------------------------------------

@router.get("/{exam_id}/ai/suggestions", response_model=SuggestionListResponse)
async def list_suggestions(
    exam_id: UUID,
    suggestion_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """List AI suggestions for an exam, optionally filtered by type and status."""
    query = select(AISuggestion).where(AISuggestion.exam_id == exam_id)
    if suggestion_type:
        query = query.where(AISuggestion.suggestion_type == suggestion_type)
    if status:
        query = query.where(AISuggestion.status == status)
    query = query.order_by(AISuggestion.created_at.desc())

    result = await db.execute(query)
    suggestions = result.scalars().all()

    # Counts
    count_result = await db.execute(
        select(AISuggestion.status, func.count())
        .where(AISuggestion.exam_id == exam_id)
        .group_by(AISuggestion.status)
    )
    counts = dict(count_result.all())

    return SuggestionListResponse(
        suggestions=[
            SuggestionListItem(
                id=s.id,
                suggestion_type=s.suggestion_type,
                status=s.status,
                output_payload=s.output_payload,
                validation_errors=s.validation_errors,
                model=s.model,
                prompt_version=s.prompt_version,
                reviewed_by=s.reviewed_by,
                reviewed_at=s.reviewed_at,
                review_note=s.review_note,
                created_at=s.created_at,
            )
            for s in suggestions
        ],
        total=sum(counts.values()),
        pending=counts.get("pending", 0),
        accepted=counts.get("accepted", 0),
        rejected=counts.get("rejected", 0),
        applied=counts.get("applied", 0),
    )


# ---------------------------------------------------------------------------
# Review Single Suggestion
# ---------------------------------------------------------------------------

@router.post("/{exam_id}/ai/suggestions/{suggestion_id}/review")
async def review_suggestion(
    exam_id: UUID,
    suggestion_id: UUID,
    body: SuggestionReviewAction,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """Accept or reject a single AI suggestion."""
    result = await db.execute(
        select(AISuggestion).where(
            AISuggestion.id == suggestion_id,
            AISuggestion.exam_id == exam_id,
        )
    )
    suggestion = result.scalar_one_or_none()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    if suggestion.status not in ("pending",):
        raise HTTPException(
            status_code=409,
            detail=f"Suggestion already {suggestion.status}; only pending suggestions can be reviewed",
        )

    suggestion.status = "accepted" if body.action == "accept" else "rejected"
    suggestion.reviewed_by = _user
    suggestion.reviewed_at = datetime.utcnow()
    suggestion.review_note = body.note

    audit = AuditLog(
        exam_id=exam_id,
        actor=_user,
        action=f"suggestion_{body.action}",
        entity_type="ai_suggestion",
        entity_id=str(suggestion_id),
        after_payload={"status": suggestion.status, "note": body.note},
    )
    db.add(audit)
    await db.flush()

    return {"status": "ok", "suggestion_status": suggestion.status}


# ---------------------------------------------------------------------------
# Bulk Review
# ---------------------------------------------------------------------------

@router.post("/{exam_id}/ai/suggestions/bulk-review")
async def bulk_review(
    exam_id: UUID,
    body: BulkReviewRequest,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """Accept or reject multiple suggestions at once."""
    result = await db.execute(
        select(AISuggestion).where(
            AISuggestion.id.in_(body.suggestion_ids),
            AISuggestion.exam_id == exam_id,
            AISuggestion.status == "pending",
        )
    )
    suggestions = result.scalars().all()

    updated = 0
    for s in suggestions:
        s.status = "accepted" if body.action == "accept" else "rejected"
        s.reviewed_by = _user
        s.reviewed_at = datetime.utcnow()
        s.review_note = body.note
        updated += 1

    audit = AuditLog(
        exam_id=exam_id,
        actor=_user,
        action=f"bulk_suggestion_{body.action}",
        entity_type="ai_suggestion",
        after_payload={
            "suggestion_ids": [str(sid) for sid in body.suggestion_ids],
            "updated": updated,
        },
    )
    db.add(audit)
    await db.flush()

    return {"status": "ok", "updated": updated, "total_requested": len(body.suggestion_ids)}


# ---------------------------------------------------------------------------
# Apply Accepted Suggestions
# ---------------------------------------------------------------------------

@router.post("/{exam_id}/ai/suggestions/apply", response_model=ApplySuggestionsResponse)
async def apply_suggestions(
    exam_id: UUID,
    body: ApplySuggestionsRequest,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """Apply accepted suggestions to the actual data (graph/mapping).

    Only accepted suggestions can be applied. This mutates the graph
    or concept mappings and creates new versions.
    """
    result = await db.execute(
        select(AISuggestion).where(
            AISuggestion.id.in_(body.suggestion_ids),
            AISuggestion.exam_id == exam_id,
            AISuggestion.status == "accepted",
        )
    )
    suggestions = result.scalars().all()

    applied = 0
    errors = []

    for s in suggestions:
        try:
            if s.suggestion_type == "prereq_edge":
                await _apply_edge_suggestion(s, exam_id, db, _user)
                applied += 1
            elif s.suggestion_type == "concept_tag":
                await _apply_tag_suggestion(s, exam_id, db, _user)
                applied += 1
            elif s.suggestion_type == "graph_expansion":
                await _apply_graph_expansion_suggestion(s, exam_id, db, _user)
                applied += 1
            elif s.suggestion_type == "intervention":
                s.status = "applied"
                s.applied_at = datetime.utcnow()
                applied += 1
            else:
                errors.append(f"Unknown suggestion type: {s.suggestion_type}")
        except Exception as e:
            errors.append(f"Failed to apply suggestion {s.id}: {str(e)}")

    await db.flush()

    return ApplySuggestionsResponse(
        status="ok" if not errors else "partial",
        applied_count=applied,
        errors=errors,
    )


async def _apply_edge_suggestion(
    suggestion: AISuggestion,
    exam_id: UUID,
    db: AsyncSession,
    actor: str,
):
    """Apply accepted prerequisite edge suggestions to the graph."""
    g_result = await db.execute(
        select(ConceptGraph)
        .where(ConceptGraph.exam_id == exam_id)
        .order_by(ConceptGraph.version.desc())
        .limit(1)
    )
    graph_row = g_result.scalar_one_or_none()
    if not graph_row:
        raise ValueError("No graph found to apply edges to")

    before_json = graph_row.graph_json
    edges_to_add = suggestion.output_payload.get("suggestions", [])

    G = build_graph(before_json)
    for edge in edges_to_add:
        G.add_edge(edge["source"], edge["target"], weight=edge.get("weight", 0.5))

    after_json = graph_to_json(G)

    new_graph = ConceptGraph(
        exam_id=exam_id,
        version=graph_row.version + 1,
        graph_json=after_json,
        annotation=f"Applied AI edge suggestions (suggestion {suggestion.id})",
    )
    db.add(new_graph)

    suggestion.status = "applied"
    suggestion.applied_at = datetime.utcnow()
    suggestion.before_snapshot = before_json
    suggestion.after_snapshot = after_json

    audit = AuditLog(
        exam_id=exam_id,
        actor=actor,
        action="apply_edge_suggestion",
        entity_type="concept_graph",
        entity_id=str(new_graph.id),
        before_payload=before_json,
        after_payload=after_json,
    )
    db.add(audit)


async def _apply_tag_suggestion(
    suggestion: AISuggestion,
    exam_id: UUID,
    db: AsyncSession,
    actor: str,
):
    """Apply accepted concept-tag suggestions to question-concept mappings."""
    tags = suggestion.output_payload.get("suggestions", [])
    input_data = suggestion.input_payload or {}

    q_result = await db.execute(
        select(Question).where(
            Question.exam_id == exam_id,
        )
    )
    questions = q_result.scalars().all()

    applied_to = []
    for tag in tags:
        concept_id = tag.get("concept_id")
        if not concept_id:
            continue
        for q in questions:
            existing = await db.execute(
                select(QuestionConceptMap).where(
                    QuestionConceptMap.question_id == q.id,
                    QuestionConceptMap.concept_id == concept_id,
                )
            )
            if not existing.scalar_one_or_none():
                mapping = QuestionConceptMap(
                    question_id=q.id,
                    concept_id=concept_id,
                    weight=tag.get("confidence", 1.0),
                )
                db.add(mapping)
                applied_to.append({"question_id": str(q.id), "concept_id": concept_id})

    suggestion.status = "applied"
    suggestion.applied_at = datetime.utcnow()
    suggestion.after_snapshot = {"applied_mappings": applied_to}

    audit = AuditLog(
        exam_id=exam_id,
        actor=actor,
        action="apply_tag_suggestion",
        entity_type="question_concept_map",
        after_payload={"applied_mappings": applied_to},
    )
    db.add(audit)


async def _apply_graph_expansion_suggestion(
    suggestion: AISuggestion,
    exam_id: UUID,
    db: AsyncSession,
    actor: str,
):
    """Apply accepted graph-expansion suggestions by merging new nodes/edges into the latest graph version."""
    g_result = await db.execute(
        select(ConceptGraph)
        .where(ConceptGraph.exam_id == exam_id)
        .order_by(ConceptGraph.version.desc())
        .limit(1)
    )
    graph_row = g_result.scalar_one_or_none()
    if not graph_row:
        raise ValueError("No graph found to apply expansion to")

    before_json = graph_row.graph_json
    G = build_graph(before_json)

    new_nodes = suggestion.output_payload.get("nodes", [])
    new_edges = suggestion.output_payload.get("edges", [])

    for node in new_nodes:
        node_id = node.get("id")
        if not node_id or G.has_node(node_id):
            continue
        G.add_node(node_id, label=node.get("label", node_id))

    for edge in new_edges:
        src, tgt = edge.get("source"), edge.get("target")
        if not src or not tgt:
            continue
        if G.has_edge(src, tgt):
            continue
        if not G.has_node(src):
            G.add_node(src, label=src)
        if not G.has_node(tgt):
            G.add_node(tgt, label=tgt)
        G.add_edge(src, tgt, weight=edge.get("weight", 0.5))

    after_json = graph_to_json(G)

    new_graph = ConceptGraph(
        exam_id=exam_id,
        version=graph_row.version + 1,
        graph_json=after_json,
        annotation=f"Applied AI graph expansion (suggestion {suggestion.id})",
    )
    db.add(new_graph)

    suggestion.status = "applied"
    suggestion.applied_at = datetime.utcnow()
    suggestion.before_snapshot = before_json
    suggestion.after_snapshot = after_json

    audit = AuditLog(
        exam_id=exam_id,
        actor=actor,
        action="apply_graph_expansion",
        entity_type="concept_graph",
        entity_id=str(new_graph.id),
        before_payload=before_json,
        after_payload=after_json,
    )
    db.add(audit)
