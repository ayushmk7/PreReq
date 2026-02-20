"""Compute endpoints."""

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_instructor
from app.config import settings
from app.database import get_db
from app.models.models import ComputeRun, Exam, InterventionResult, Parameter
from app.schemas.schemas import ComputeRequest, ComputeResponse, ComputeRunResponse
from app.services.compute_queue_service import enqueue_compute_job
from app.services.compute_runner_service import run_compute_pipeline_for_run

router = APIRouter(prefix="/api/v1/exams", tags=["Compute"])


@router.post("/{exam_id}/compute", response_model=ComputeResponse)
async def compute_readiness(
    exam_id: UUID,
    body: ComputeRequest = ComputeRequest(),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """Run compute in sync mode or enqueue in async mode."""
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

    async_enabled = settings.COMPUTE_ASYNC_ENABLED
    compute_run = ComputeRun(
        exam_id=exam_id,
        run_id=run_id,
        status="queued" if async_enabled else "running",
        parameters_json={
            "alpha": alpha, "beta": beta, "gamma": gamma,
            "threshold": threshold, "k": k,
        },
    )
    db.add(compute_run)
    await db.flush()

    if async_enabled:
        queued = await enqueue_compute_job(
            exam_id=exam_id,
            run_id=run_id,
            alpha=alpha,
            beta=beta,
            gamma=gamma,
            threshold=threshold,
            k=k,
        )
        if not queued:
            compute_run.status = "failed"
            compute_run.error_message = (
                f"Unsupported queue backend: {settings.COMPUTE_QUEUE_BACKEND}"
            )
            await db.flush()
            raise HTTPException(status_code=500, detail="Failed to enqueue compute job")

        return ComputeResponse(status="queued", run_id=run_id)

    result_stats = await run_compute_pipeline_for_run(
        db=db,
        exam_id=exam_id,
        run_id=run_id,
        alpha=alpha,
        beta=beta,
        gamma=gamma,
        threshold=threshold,
        k=k,
    )
    return ComputeResponse(
        status="success",
        run_id=run_id,
        students_processed=int(result_stats["students_processed"]),
        concepts_processed=int(result_stats["concepts_processed"]),
        time_ms=float(result_stats["time_ms"]),
    )


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
