"""Shared compute runner used by API sync mode and background workers."""

from __future__ import annotations

import time
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    ClassAggregate,
    Cluster,
    ClusterAssignment,
    ComputeRun,
    ConceptGraph,
    InterventionResult,
    Question,
    QuestionConceptMap,
    ReadinessResult,
    Score,
    StudentToken,
)
from app.services.cluster_service import rank_interventions, run_clustering
from app.services.compute_service import run_readiness_pipeline
from app.services.report_service import generate_student_token


async def run_compute_pipeline_for_run(
    db: AsyncSession,
    exam_id: UUID,
    run_id: UUID,
    alpha: float,
    beta: float,
    gamma: float,
    threshold: float,
    k: int,
) -> dict[str, float | int]:
    """Execute full compute pipeline for an existing run record."""
    start = time.time()

    run_result = await db.execute(
        select(ComputeRun).where(ComputeRun.run_id == run_id)
    )
    compute_run = run_result.scalar_one_or_none()
    if not compute_run:
        raise HTTPException(status_code=404, detail="Compute run not found")

    compute_run.status = "running"
    compute_run.parameters_json = {
        "alpha": alpha,
        "beta": beta,
        "gamma": gamma,
        "threshold": threshold,
        "k": k,
    }
    await db.flush()

    g_result = await db.execute(
        select(ConceptGraph)
        .where(ConceptGraph.exam_id == exam_id)
        .order_by(ConceptGraph.version.desc())
        .limit(1)
    )
    graph_row = g_result.scalar_one_or_none()
    graph_version = graph_row.version if graph_row else 0
    compute_run.graph_version = graph_version
    await db.flush()

    try:
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
            scores_dict.setdefault(sid, {})[qid] = score_obj.score
            max_scores_dict[qid] = question_obj.max_score

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
            question_concept_map.setdefault(cid, []).append((qid, qcm_obj.weight))

        if not graph_row:
            all_concepts = sorted(question_concept_map.keys())
            question_to_concepts: dict[str, list[str]] = {}
            for cid, q_list in question_concept_map.items():
                for qid, _w in q_list:
                    question_to_concepts.setdefault(qid, []).append(cid)

            first_seen: dict[str, int] = {}
            for idx, qid in enumerate(sorted(question_to_concepts.keys())):
                for cid in question_to_concepts[qid]:
                    first_seen.setdefault(cid, idx)

            edge_set: set[tuple[str, str]] = set()
            for concepts_on_q in question_to_concepts.values():
                if len(concepts_on_q) < 2:
                    continue
                ordered = sorted(concepts_on_q, key=lambda c: first_seen.get(c, 999))
                for i in range(len(ordered) - 1):
                    edge_set.add((ordered[i], ordered[i + 1]))

            graph_json = {
                "nodes": [{"id": c, "label": c} for c in all_concepts],
                "edges": [{"source": s, "target": t, "weight": 0.5} for s, t in sorted(edge_set)],
            }
            auto_graph = ConceptGraph(exam_id=exam_id, version=1, graph_json=graph_json)
            db.add(auto_graph)
            await db.flush()
            compute_run.graph_version = 1
        else:
            graph_json = graph_row.graph_json

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

        await db.execute(delete(ReadinessResult).where(ReadinessResult.exam_id == exam_id))
        await db.execute(delete(ClassAggregate).where(ClassAggregate.exam_id == exam_id))
        await db.execute(delete(ClusterAssignment).where(ClusterAssignment.exam_id == exam_id))
        await db.execute(delete(Cluster).where(Cluster.exam_id == exam_id))
        await db.execute(delete(InterventionResult).where(InterventionResult.exam_id == exam_id))
        await db.flush()

        for r in pipeline_result["readiness_results"]:
            db.add(
                ReadinessResult(
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
            )

        for agg in pipeline_result["class_aggregates"]:
            db.add(
                ClassAggregate(
                    exam_id=exam_id,
                    run_id=run_id,
                    concept_id=agg["concept_id"],
                    mean_readiness=agg["mean_readiness"],
                    median_readiness=agg["median_readiness"],
                    std_readiness=agg["std_readiness"],
                    below_threshold_count=agg["below_threshold_count"],
                )
            )

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
                    db.add(
                        ClusterAssignment(
                            exam_id=exam_id,
                            student_id_external=student_id,
                            cluster_id=cluster.id,
                        )
                    )

        interventions = rank_interventions(
            final_readiness_matrix=pipeline_result["final_readiness_matrix"],
            concepts=pipeline_result["concepts"],
            adjacency=pipeline_result["adjacency"],
            threshold=threshold,
        )
        for iv in interventions:
            db.add(
                InterventionResult(
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
            )

        for student_id in pipeline_result["students"]:
            existing = await db.execute(
                select(StudentToken).where(
                    StudentToken.exam_id == exam_id,
                    StudentToken.student_id_external == student_id,
                )
            )
            if not existing.scalar_one_or_none():
                db.add(
                    StudentToken(
                        exam_id=exam_id,
                        student_id_external=student_id,
                        token=generate_student_token(),
                    )
                )

        await db.flush()
        elapsed = round((time.time() - start) * 1000, 2)
        compute_run.status = "success"
        compute_run.students_processed = len(pipeline_result["students"])
        compute_run.concepts_processed = len(pipeline_result["concepts"])
        compute_run.duration_ms = elapsed
        compute_run.completed_at = datetime.utcnow()
        await db.flush()

        return {
            "students_processed": len(pipeline_result["students"]),
            "concepts_processed": len(pipeline_result["concepts"]),
            "time_ms": elapsed,
        }

    except HTTPException as exc:
        compute_run.status = "failed"
        compute_run.error_message = str(exc.detail)
        compute_run.completed_at = datetime.utcnow()
        compute_run.duration_ms = round((time.time() - start) * 1000, 2)
        await db.flush()
        raise
    except Exception as exc:
        compute_run.status = "failed"
        compute_run.error_message = str(exc)
        compute_run.completed_at = datetime.utcnow()
        compute_run.duration_ms = round((time.time() - start) * 1000, 2)
        await db.flush()
        raise HTTPException(status_code=500, detail=f"Computation failed: {str(exc)}")
