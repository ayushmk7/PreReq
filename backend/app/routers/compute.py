"""Compute endpoint: API-05 — run readiness inference engine."""

import time
import uuid
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_instructor
from app.database import get_db
from app.models.models import (
    ClassAggregate,
    Cluster,
    ClusterAssignment,
    ComputeRun,
    ConceptGraph,
    Exam,
    InterventionResult,
    Parameter,
    Question,
    QuestionConceptMap,
    ReadinessResult,
    Score,
    StudentToken,
)
from app.schemas.schemas import ComputeRequest, ComputeResponse, ComputeRunResponse
from app.services.cluster_service import rank_interventions, run_clustering
from app.services.compute_service import run_readiness_pipeline
from app.services.report_service import generate_student_token

router = APIRouter(prefix="/api/v1/exams", tags=["Compute"])


@router.post("/{exam_id}/compute", response_model=ComputeResponse)
async def compute_readiness(
    exam_id: UUID,
    body: ComputeRequest = ComputeRequest(),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """Run the full readiness computation pipeline.

    1. Loads scores, mapping, graph from DB
    2. Runs 4-stage readiness inference
    3. Runs k-means clustering
    4. Ranks interventions by impact
    5. Generates student tokens
    6. Persists all results with run tracking
    """
    start = time.time()
    run_id = uuid.uuid4()

    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Exam not found")

    # Load parameters (request body overrides stored defaults)
    p_result = await db.execute(
        select(Parameter).where(Parameter.exam_id == exam_id)
    )
    params = p_result.scalar_one_or_none()
    alpha = body.alpha if body.alpha != 1.0 else (params.alpha if params else 1.0)
    beta = body.beta if body.beta != 0.3 else (params.beta if params else 0.3)
    gamma = body.gamma if body.gamma != 0.2 else (params.gamma if params else 0.2)
    threshold = body.threshold if body.threshold != 0.6 else (params.threshold if params else 0.6)
    k = body.k if body.k != 4 else (params.k if params else 4)

    # Get graph version for tracking
    g_result = await db.execute(
        select(ConceptGraph)
        .where(ConceptGraph.exam_id == exam_id)
        .order_by(ConceptGraph.version.desc())
        .limit(1)
    )
    graph_row = g_result.scalar_one_or_none()
    graph_version = graph_row.version if graph_row else 0

    # Create compute run record
    compute_run = ComputeRun(
        exam_id=exam_id,
        run_id=run_id,
        status="running",
        parameters_json={
            "alpha": alpha, "beta": beta, "gamma": gamma,
            "threshold": threshold, "k": k,
        },
        graph_version=graph_version,
    )
    db.add(compute_run)
    await db.flush()

    try:
        # Load scores
        score_result = await db.execute(
            select(Score, Question)
            .join(Question, Score.question_id == Question.id)
            .where(Score.exam_id == exam_id)
        )
        score_rows = score_result.all()

        if not score_rows:
            raise HTTPException(
                status_code=400,
                detail="No scores found. Upload scores first (POST /scores).",
            )

        scores_dict: dict[str, dict[str, float]] = {}
        max_scores_dict: dict[str, float] = {}
        for score_obj, question_obj in score_rows:
            sid = score_obj.student_id_external
            qid = question_obj.question_id_external
            if sid not in scores_dict:
                scores_dict[sid] = {}
            scores_dict[sid][qid] = score_obj.score
            max_scores_dict[qid] = question_obj.max_score

        # Load question-concept mapping
        qcm_result = await db.execute(
            select(QuestionConceptMap, Question)
            .join(Question, QuestionConceptMap.question_id == Question.id)
            .where(Question.exam_id == exam_id)
        )
        qcm_rows = qcm_result.all()

        if not qcm_rows:
            raise HTTPException(
                status_code=400,
                detail="No question-concept mapping found. Upload mapping first (POST /mapping).",
            )

        question_concept_map: dict[str, list[tuple[str, float]]] = {}
        for qcm_obj, question_obj in qcm_rows:
            cid = qcm_obj.concept_id
            qid = question_obj.question_id_external
            if cid not in question_concept_map:
                question_concept_map[cid] = []
            question_concept_map[cid].append((qid, qcm_obj.weight))

        # Load graph
        if not graph_row:
            all_concepts = set(question_concept_map.keys())
            graph_json = {
                "nodes": [{"id": c, "label": c} for c in sorted(all_concepts)],
                "edges": [],
            }
        else:
            graph_json = graph_row.graph_json

        # Run readiness pipeline
        pipeline_result = run_readiness_pipeline(
            scores=scores_dict,
            max_scores=max_scores_dict,
            question_concept_map=question_concept_map,
            graph_json=graph_json,
            alpha=alpha,
            beta=beta,
            gamma=gamma,
            threshold=threshold,
        )

        # Clear old results
        await db.execute(delete(ReadinessResult).where(ReadinessResult.exam_id == exam_id))
        await db.execute(delete(ClassAggregate).where(ClassAggregate.exam_id == exam_id))
        await db.execute(delete(ClusterAssignment).where(ClusterAssignment.exam_id == exam_id))
        await db.execute(delete(Cluster).where(Cluster.exam_id == exam_id))
        await db.execute(delete(InterventionResult).where(InterventionResult.exam_id == exam_id))
        await db.flush()

        # Persist readiness results
        for r in pipeline_result["readiness_results"]:
            rr = ReadinessResult(
                exam_id=exam_id,
                run_id=run_id,
                student_id_external=r["student_id"],
                concept_id=r["concept_id"],
                direct_readiness=r["direct_readiness"],
                prerequisite_penalty=r["prerequisite_penalty"],
                downstream_boost=r["downstream_boost"],
                final_readiness=r["final_readiness"],
                confidence=r["confidence"],
                explanation_trace_json=r["explanation_trace"],
            )
            db.add(rr)

        # Persist class aggregates
        for agg in pipeline_result["class_aggregates"]:
            ca = ClassAggregate(
                exam_id=exam_id,
                run_id=run_id,
                concept_id=agg["concept_id"],
                mean_readiness=agg["mean_readiness"],
                median_readiness=agg["median_readiness"],
                std_readiness=agg["std_readiness"],
                below_threshold_count=agg["below_threshold_count"],
            )
            db.add(ca)

        # Run clustering
        clustering_result = run_clustering(
            final_readiness_matrix=pipeline_result["final_readiness_matrix"],
            concepts=pipeline_result["concepts"],
            students=pipeline_result["students"],
            k=k,
        )

        for cl in clustering_result["clusters"]:
            cluster = Cluster(
                exam_id=exam_id,
                run_id=run_id,
                cluster_label=cl["cluster_label"],
                centroid_json=cl["centroid"],
                student_count=cl["student_count"],
            )
            db.add(cluster)
            await db.flush()

            for student_id, label in clustering_result["assignments"].items():
                if label == cl["cluster_label"]:
                    ca = ClusterAssignment(
                        exam_id=exam_id,
                        student_id_external=student_id,
                        cluster_id=cluster.id,
                    )
                    db.add(ca)

        # Rank and persist interventions
        interventions = rank_interventions(
            final_readiness_matrix=pipeline_result["final_readiness_matrix"],
            concepts=pipeline_result["concepts"],
            adjacency=pipeline_result["adjacency"],
            threshold=threshold,
        )
        for iv in interventions:
            ir = InterventionResult(
                exam_id=exam_id,
                run_id=run_id,
                concept_id=iv["concept_id"],
                students_affected=iv["students_affected"],
                downstream_concepts=iv["downstream_concepts"],
                current_readiness=iv["current_readiness"],
                impact=iv["impact"],
                rationale=iv["rationale"],
                suggested_format=iv["suggested_format"],
            )
            db.add(ir)

        # Generate student tokens (if not already existing)
        for student_id in pipeline_result["students"]:
            existing = await db.execute(
                select(StudentToken).where(
                    StudentToken.exam_id == exam_id,
                    StudentToken.student_id_external == student_id,
                )
            )
            if not existing.scalar_one_or_none():
                token = StudentToken(
                    exam_id=exam_id,
                    student_id_external=student_id,
                    token=generate_student_token(),
                )
                db.add(token)

        await db.flush()

        elapsed = (time.time() - start) * 1000

        # Update compute run
        compute_run.status = "success"
        compute_run.students_processed = len(pipeline_result["students"])
        compute_run.concepts_processed = len(pipeline_result["concepts"])
        compute_run.duration_ms = round(elapsed, 2)
        compute_run.completed_at = datetime.utcnow()
        await db.flush()

        return ComputeResponse(
            status="success",
            run_id=run_id,
            students_processed=len(pipeline_result["students"]),
            concepts_processed=len(pipeline_result["concepts"]),
            time_ms=round(elapsed, 2),
        )

    except HTTPException:
        raise
    except Exception as e:
        compute_run.status = "failed"
        compute_run.error_message = str(e)
        compute_run.completed_at = datetime.utcnow()
        compute_run.duration_ms = round((time.time() - start) * 1000, 2)
        await db.flush()
        raise HTTPException(status_code=500, detail=f"Computation failed: {str(e)}")


@router.get("/{exam_id}/compute/runs", response_model=list[ComputeRunResponse])
async def list_compute_runs(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """List all compute runs for an exam, most recent first."""
    result = await db.execute(
        select(ComputeRun)
        .where(ComputeRun.exam_id == exam_id)
        .order_by(ComputeRun.created_at.desc())
    )
    runs = result.scalars().all()
    return [
        ComputeRunResponse(
            id=r.id,
            run_id=r.run_id,
            exam_id=r.exam_id,
            status=r.status,
            students_processed=r.students_processed,
            concepts_processed=r.concepts_processed,
            parameters=r.parameters_json,
            graph_version=r.graph_version,
            duration_ms=r.duration_ms,
            error_message=r.error_message,
            created_at=r.created_at,
            completed_at=r.completed_at,
        )
        for r in runs
    ]


@router.get("/{exam_id}/interventions")
async def get_interventions(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """Get ranked intervention recommendations from the latest compute run."""
    result = await db.execute(
        select(InterventionResult)
        .where(InterventionResult.exam_id == exam_id)
        .order_by(InterventionResult.impact.desc())
    )
    interventions = result.scalars().all()
    return {
        "interventions": [
            {
                "concept_id": iv.concept_id,
                "students_affected": iv.students_affected,
                "downstream_concepts": iv.downstream_concepts,
                "current_readiness": iv.current_readiness,
                "impact": iv.impact,
                "rationale": iv.rationale,
                "suggested_format": iv.suggested_format,
            }
            for iv in interventions
        ]
    }
