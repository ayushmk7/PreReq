"""Export endpoints for Canvas-ready download bundles."""

import os
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
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
    ExportRun,
    InterventionResult,
    Parameter,
    Question,
    QuestionConceptMap,
    ReadinessResult,
)
from app.schemas.schemas import ExportListResponse, ExportRequest, ExportStatusResponse
from app.services.export_service import generate_export_bundle, validate_export_bundle

router = APIRouter(prefix="/api/v1/exams", tags=["Export"])


@router.post("/{exam_id}/export", response_model=ExportStatusResponse)
async def create_export(
    exam_id: UUID,
    body: ExportRequest = ExportRequest(),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """Generate a Canvas-ready export bundle from the latest (or specified) compute run."""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Determine compute run
    compute_run_id = None
    if body.compute_run_id:
        run_result = await db.execute(
            select(ComputeRun).where(
                ComputeRun.run_id == body.compute_run_id,
                ComputeRun.exam_id == exam_id,
            )
        )
        run = run_result.scalar_one_or_none()
        if not run:
            raise HTTPException(status_code=404, detail="Compute run not found")
        compute_run_id = str(run.run_id)

    # Create export run record
    export_run = ExportRun(
        exam_id=exam_id,
        compute_run_id=body.compute_run_id,
        status="generating",
    )
    db.add(export_run)
    await db.flush()

    try:
        # Load graph
        g_result = await db.execute(
            select(ConceptGraph)
            .where(ConceptGraph.exam_id == exam_id)
            .order_by(ConceptGraph.version.desc())
            .limit(1)
        )
        graph_row = g_result.scalar_one_or_none()
        graph_json = graph_row.graph_json if graph_row else {"nodes": [], "edges": []}

        # Load readiness results
        rr_result = await db.execute(
            select(ReadinessResult).where(ReadinessResult.exam_id == exam_id)
        )
        readiness_rows = rr_result.scalars().all()
        readiness_data = [
            {
                "student_id": r.student_id_external,
                "concept_id": r.concept_id,
                "direct_readiness": r.direct_readiness,
                "prerequisite_penalty": r.prerequisite_penalty,
                "downstream_boost": r.downstream_boost,
                "final_readiness": r.final_readiness,
                "confidence": r.confidence,
            }
            for r in readiness_rows
        ]

        # Load class aggregates
        agg_result = await db.execute(
            select(ClassAggregate).where(ClassAggregate.exam_id == exam_id)
        )
        agg_rows = agg_result.scalars().all()
        agg_data = [
            {
                "concept_id": a.concept_id,
                "mean_readiness": a.mean_readiness,
                "median_readiness": a.median_readiness,
                "std_readiness": a.std_readiness,
                "below_threshold_count": a.below_threshold_count,
            }
            for a in agg_rows
        ]

        # Load clusters
        cl_result = await db.execute(
            select(Cluster).where(Cluster.exam_id == exam_id)
        )
        clusters = cl_result.scalars().all()
        cluster_data = [
            {
                "cluster_label": c.cluster_label,
                "student_count": c.student_count,
                "centroid": c.centroid_json or {},
            }
            for c in clusters
        ]

        # Load cluster assignments
        ca_result = await db.execute(
            select(ClusterAssignment, Cluster)
            .join(Cluster, ClusterAssignment.cluster_id == Cluster.id)
            .where(ClusterAssignment.exam_id == exam_id)
        )
        assignment_data = [
            {
                "student_id": a.student_id_external,
                "cluster_label": c.cluster_label,
            }
            for a, c in ca_result.all()
        ]

        # Load interventions
        iv_result = await db.execute(
            select(InterventionResult)
            .where(InterventionResult.exam_id == exam_id)
            .order_by(InterventionResult.impact.desc())
        )
        iv_rows = iv_result.scalars().all()
        iv_data = [
            {
                "concept_id": iv.concept_id,
                "students_affected": iv.students_affected,
                "downstream_concepts": iv.downstream_concepts,
                "current_readiness": iv.current_readiness,
                "impact": iv.impact,
                "rationale": iv.rationale,
                "suggested_format": iv.suggested_format,
            }
            for iv in iv_rows
        ]

        # Load parameters
        p_result = await db.execute(
            select(Parameter).where(Parameter.exam_id == exam_id)
        )
        params = p_result.scalar_one_or_none()
        params_data = {
            "alpha": params.alpha if params else 1.0,
            "beta": params.beta if params else 0.3,
            "gamma": params.gamma if params else 0.2,
            "threshold": params.threshold if params else 0.6,
            "k": params.k if params else 4,
        }

        # Load question-concept mapping
        qcm_result = await db.execute(
            select(QuestionConceptMap, Question)
            .join(Question, QuestionConceptMap.question_id == Question.id)
            .where(Question.exam_id == exam_id)
        )
        mapping_data = [
            {
                "question_id": q.question_id_external,
                "concept_id": qcm.concept_id,
                "weight": qcm.weight,
            }
            for qcm, q in qcm_result.all()
        ]

        # Generate bundle
        file_path, checksum, manifest = generate_export_bundle(
            exam_id=str(exam_id),
            exam_name=exam.name,
            graph_json=graph_json,
            readiness_results=readiness_data,
            class_aggregates=agg_data,
            clusters=cluster_data,
            cluster_assignments=assignment_data,
            interventions=iv_data,
            parameters=params_data,
            question_mapping=mapping_data,
            compute_run_id=compute_run_id,
        )

        # Validate the generated bundle
        validation_errors = validate_export_bundle(file_path, manifest)
        if validation_errors:
            export_run.status = "failed"
            export_run.error_message = "; ".join(validation_errors)
        else:
            export_run.status = "ready"

        export_run.file_path = file_path
        export_run.file_checksum = checksum
        export_run.manifest_json = manifest
        export_run.completed_at = datetime.utcnow()
        await db.flush()
        await db.refresh(export_run)

        return ExportStatusResponse(
            id=export_run.id,
            exam_id=export_run.exam_id,
            status=export_run.status,
            file_checksum=export_run.file_checksum,
            manifest=export_run.manifest_json,
            created_at=export_run.created_at,
            completed_at=export_run.completed_at,
            error_message=export_run.error_message,
        )

    except Exception as e:
        export_run.status = "failed"
        export_run.error_message = str(e)
        export_run.completed_at = datetime.utcnow()
        await db.flush()
        raise HTTPException(status_code=500, detail=f"Export generation failed: {str(e)}")


@router.get("/{exam_id}/export", response_model=ExportListResponse)
async def list_exports(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """List all export runs for an exam."""
    result = await db.execute(
        select(ExportRun)
        .where(ExportRun.exam_id == exam_id)
        .order_by(ExportRun.created_at.desc())
    )
    exports = result.scalars().all()

    return ExportListResponse(
        exports=[
            ExportStatusResponse(
                id=e.id,
                exam_id=e.exam_id,
                status=e.status,
                file_checksum=e.file_checksum,
                manifest=e.manifest_json,
                created_at=e.created_at,
                completed_at=e.completed_at,
                error_message=e.error_message,
            )
            for e in exports
        ]
    )


@router.get("/{exam_id}/export/{export_id}/download")
async def download_export(
    exam_id: UUID,
    export_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """Download the export zip bundle."""
    result = await db.execute(
        select(ExportRun).where(
            ExportRun.id == export_id,
            ExportRun.exam_id == exam_id,
        )
    )
    export_run = result.scalar_one_or_none()
    if not export_run:
        raise HTTPException(status_code=404, detail="Export not found")

    if export_run.status != "ready":
        raise HTTPException(
            status_code=409,
            detail=f"Export is not ready (status: {export_run.status})",
        )

    if not export_run.file_path or not os.path.exists(export_run.file_path):
        raise HTTPException(status_code=404, detail="Export file not found on disk")

    filename = os.path.basename(export_run.file_path)
    return FileResponse(
        path=export_run.file_path,
        media_type="application/zip",
        filename=filename,
    )
