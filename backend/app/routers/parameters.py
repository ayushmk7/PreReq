"""Parameters endpoints: API-10 (GET) and API-11 (PUT)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_instructor
from app.database import get_db
from app.models.models import Exam, Parameter
from app.schemas.schemas import ParametersResponse, ParametersSchema

router = APIRouter(prefix="/api/v1/exams", tags=["Parameters"])


@router.get("/{exam_id}/parameters", response_model=ParametersResponse)
async def get_parameters(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """Get current computation parameters for an exam."""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Exam not found")

    p_result = await db.execute(
        select(Parameter).where(Parameter.exam_id == exam_id)
    )
    params = p_result.scalar_one_or_none()

    if not params:
        return ParametersResponse(
            alpha=1.0, beta=0.3, gamma=0.2, threshold=0.6, k=4,
        )

    return ParametersResponse(
        alpha=params.alpha,
        beta=params.beta,
        gamma=params.gamma,
        threshold=params.threshold,
        k=params.k,
    )


@router.put("/{exam_id}/parameters", response_model=ParametersResponse)
async def update_parameters(
    exam_id: UUID,
    body: ParametersSchema,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """Update computation parameters for an exam.

    Note: Updating parameters does NOT automatically trigger recomputation.
    Call POST /compute after updating parameters to apply changes.
    """
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Exam not found")

    p_result = await db.execute(
        select(Parameter).where(Parameter.exam_id == exam_id)
    )
    params = p_result.scalar_one_or_none()

    if not params:
        params = Parameter(exam_id=exam_id)
        db.add(params)

    params.alpha = body.alpha
    params.beta = body.beta
    params.gamma = body.gamma
    params.threshold = body.threshold
    params.k = body.k
    await db.flush()
    await db.refresh(params)

    return ParametersResponse(
        status="ok",
        alpha=params.alpha,
        beta=params.beta,
        gamma=params.gamma,
        threshold=params.threshold,
        k=params.k,
    )
