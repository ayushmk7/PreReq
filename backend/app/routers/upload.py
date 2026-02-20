"""Upload endpoints: API-01 (scores), API-02 (mapping), API-03 (graph)."""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_instructor
from app.database import get_db
from app.models.models import (
    ConceptGraph,
    Exam,
    Question,
    QuestionConceptMap,
    Score,
)
from app.schemas.schemas import (
    GraphUploadRequest,
    GraphUploadResponse,
    MappingUploadResponse,
    ScoresUploadResponse,
)
from app.services.csv_service import validate_mapping_csv, validate_scores_csv
from app.services.graph_service import validate_graph
from app.services.object_storage_service import upload_raw_upload_artifact

router = APIRouter(prefix="/api/v1/exams", tags=["Upload"])


# ---------------------------------------------------------------------------
# API-01: Upload Scores CSV
# ---------------------------------------------------------------------------

@router.post("/{exam_id}/scores", response_model=ScoresUploadResponse)
async def upload_scores(
    exam_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """Upload exam scores CSV. Validates and persists to DB.

    Required columns: StudentID, QuestionID, Score
    Optional: MaxScore (defaults to 1.0)
    """
    # Verify exam exists
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Exam not found")

    content = await file.read()
    await upload_raw_upload_artifact(str(exam_id), "scores.csv", content, "text/csv")
    df, errors, student_detection = await validate_scores_csv(content, include_student_detection=True)

    if errors:
        return ScoresUploadResponse(status="error", errors=errors)

    # Clear existing scores and questions for this exam
    await db.execute(delete(Score).where(Score.exam_id == exam_id))
    await db.execute(delete(Question).where(Question.exam_id == exam_id))
    await db.flush()

    # Insert questions (unique question IDs)
    question_map = {}  # external_id -> db Question object
    unique_questions = df[["QuestionID", "MaxScore"]].drop_duplicates(subset=["QuestionID"])
    for _, row in unique_questions.iterrows():
        q = Question(
            exam_id=exam_id,
            question_id_external=row["QuestionID"],
            max_score=float(row["MaxScore"]),
        )
        db.add(q)
        await db.flush()
        question_map[row["QuestionID"]] = q

    # Insert scores
    for _, row in df.iterrows():
        q = question_map[row["QuestionID"]]
        score = Score(
            exam_id=exam_id,
            student_id_external=row["StudentID"],
            question_id=q.id,
            score=float(row["Score"]),
        )
        db.add(score)

    await db.flush()

    return ScoresUploadResponse(
        status="success",
        row_count=len(df),
        student_detection=student_detection,
    )


# ---------------------------------------------------------------------------
# API-02: Upload Mapping CSV
# ---------------------------------------------------------------------------

@router.post("/{exam_id}/mapping", response_model=MappingUploadResponse)
async def upload_mapping(
    exam_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """Upload question-to-concept mapping CSV.

    Required columns: QuestionID, ConceptID
    Optional: Weight (defaults to 1.0)
    """
    # Verify exam exists
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Exam not found")

    # Get existing question IDs for cross-validation
    q_result = await db.execute(
        select(Question.question_id_external).where(Question.exam_id == exam_id)
    )
    existing_qids = {row[0] for row in q_result.fetchall()}

    content = await file.read()
    await upload_raw_upload_artifact(str(exam_id), "mapping.csv", content, "text/csv")
    df, errors = await validate_mapping_csv(content, existing_qids)

    if errors:
        return MappingUploadResponse(status="error", errors=errors)

    # Get question ID mapping (external -> internal)
    q_result = await db.execute(
        select(Question).where(Question.exam_id == exam_id)
    )
    questions = {q.question_id_external: q for q in q_result.scalars().all()}

    # Clear existing mappings
    for q in questions.values():
        await db.execute(
            delete(QuestionConceptMap).where(QuestionConceptMap.question_id == q.id)
        )
    await db.flush()

    # Insert mappings
    concept_ids = set()
    for _, row in df.iterrows():
        q = questions.get(row["QuestionID"])
        if q:
            mapping = QuestionConceptMap(
                question_id=q.id,
                concept_id=row["ConceptID"],
                weight=float(row["Weight"]),
            )
            db.add(mapping)
            concept_ids.add(row["ConceptID"])

    await db.flush()

    return MappingUploadResponse(
        status="success",
        concept_count=len(concept_ids),
    )


# ---------------------------------------------------------------------------
# API-03: Upload Graph (JSON body)
# ---------------------------------------------------------------------------

@router.post("/{exam_id}/graph", response_model=GraphUploadResponse)
async def upload_graph(
    exam_id: UUID,
    body: GraphUploadRequest,
    db: AsyncSession = Depends(get_db),
    _user: str = Depends(get_current_instructor),
):
    """Upload concept dependency graph as JSON.

    Body: {"nodes": [{"id": "...", "label": "..."}], "edges": [{"source": "...", "target": "...", "weight": 0.5}]}
    """
    # Verify exam exists
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Exam not found")

    graph_json = {
        "nodes": [n.model_dump() for n in body.nodes],
        "edges": [e.model_dump() for e in body.edges],
    }
    await upload_raw_upload_artifact(
        str(exam_id),
        "graph.json",
        json.dumps(graph_json).encode("utf-8"),
        "application/json",
    )

    is_valid, errors, cycle_path = validate_graph(graph_json)

    if not is_valid:
        return GraphUploadResponse(
            status="error",
            node_count=len(body.nodes),
            edge_count=len(body.edges),
            is_dag=False,
            errors=errors,
        )

    # Get current version number
    v_result = await db.execute(
        select(ConceptGraph.version)
        .where(ConceptGraph.exam_id == exam_id)
        .order_by(ConceptGraph.version.desc())
        .limit(1)
    )
    current_version = v_result.scalar_one_or_none() or 0

    # Store new version
    cg = ConceptGraph(
        exam_id=exam_id,
        version=current_version + 1,
        graph_json=graph_json,
    )
    db.add(cg)
    await db.flush()

    return GraphUploadResponse(
        status="success",
        node_count=len(body.nodes),
        edge_count=len(body.edges),
        is_dag=True,
    )
