"""Pydantic request/response schemas for all API endpoints."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Standardized Error Envelope
# ---------------------------------------------------------------------------

class ValidationError(BaseModel):
    row: Optional[int] = None
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    status: str = "error"
    code: str = "VALIDATION_ERROR"
    message: str = ""
    errors: list[ValidationError] = []


# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------

class CourseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class CourseResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Exam
# ---------------------------------------------------------------------------

class ExamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class ExamResponse(BaseModel):
    id: UUID
    course_id: UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Upload Responses
# ---------------------------------------------------------------------------

class ScoresUploadResponse(BaseModel):
    status: str
    row_count: int = 0
    errors: list[ValidationError] = []


class MappingUploadResponse(BaseModel):
    status: str
    concept_count: int = 0
    errors: list[ValidationError] = []


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

class GraphNode(BaseModel):
    id: str
    label: str


class GraphEdge(BaseModel):
    source: str
    target: str
    weight: float = 0.5


class GraphUploadRequest(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class GraphUploadResponse(BaseModel):
    status: str
    node_count: int = 0
    edge_count: int = 0
    is_dag: bool = True
    errors: list[ValidationError] = []


class GraphPatchRequest(BaseModel):
    add_nodes: list[GraphNode] = []
    remove_nodes: list[str] = []
    add_edges: list[GraphEdge] = []
    remove_edges: list[GraphEdge] = []


class GraphPatchResponse(BaseModel):
    status: str
    is_dag: bool = True
    cycle_path: Optional[list[str]] = None


# ---------------------------------------------------------------------------
# Compute
# ---------------------------------------------------------------------------

class ComputeRequest(BaseModel):
    alpha: float = 1.0
    beta: float = 0.3
    gamma: float = 0.2
    threshold: float = 0.6
    k: int = 4


class ComputeResponse(BaseModel):
    status: str
    run_id: Optional[UUID] = None
    students_processed: int = 0
    concepts_processed: int = 0
    time_ms: float = 0.0


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class HeatmapCell(BaseModel):
    concept_id: str
    concept_label: str
    bucket: str
    count: int
    percentage: float


class AlertItem(BaseModel):
    concept_id: str
    concept_label: str
    class_average_readiness: float
    students_below_threshold: int
    downstream_concepts: list[str]
    impact: float
    recommended_action: str


class AggregateItem(BaseModel):
    concept_id: str
    concept_label: str
    mean_readiness: float
    median_readiness: float
    std_readiness: float
    below_threshold_count: int


class DashboardResponse(BaseModel):
    heatmap: list[HeatmapCell] = []
    alerts: list[AlertItem] = []
    aggregates: list[AggregateItem] = []


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

class UpstreamContribution(BaseModel):
    concept_id: str
    concept_label: str
    readiness: float
    contribution_weight: float
    penalty_contribution: float


class DownstreamContribution(BaseModel):
    concept_id: str
    concept_label: str
    readiness: float
    boost_contribution: float


class WaterfallStep(BaseModel):
    label: str
    value: float
    cumulative: float


class TraceResponse(BaseModel):
    concept_id: str
    concept_label: str
    direct_readiness: Optional[float]
    upstream: list[UpstreamContribution] = []
    downstream: list[DownstreamContribution] = []
    waterfall: list[WaterfallStep] = []
    students_affected: int = 0


# ---------------------------------------------------------------------------
# Clusters
# ---------------------------------------------------------------------------

class ClusterItem(BaseModel):
    id: UUID
    cluster_label: str
    student_count: int
    centroid: dict[str, float] = {}
    top_weak_concepts: list[str] = []
    suggested_interventions: list[str] = []


class ClusterAssignmentSummary(BaseModel):
    student_id: str
    cluster_label: str


class ClustersResponse(BaseModel):
    clusters: list[ClusterItem] = []
    assignments_summary: list[ClusterAssignmentSummary] = []


# ---------------------------------------------------------------------------
# Student Report
# ---------------------------------------------------------------------------

class StudentConceptReadiness(BaseModel):
    concept_id: str
    concept_label: str
    direct_readiness: Optional[float]
    final_readiness: float
    confidence: str


class WeakConceptItem(BaseModel):
    concept_id: str
    concept_label: str
    readiness: float
    confidence: str


class StudyPlanItem(BaseModel):
    concept_id: str
    concept_label: str
    readiness: float
    confidence: str
    reason: str
    explanation: str


class StudentReportResponse(BaseModel):
    student_id: str
    exam_id: UUID
    concept_graph: dict[str, Any] = {}
    readiness: list[StudentConceptReadiness] = []
    top_weak_concepts: list[WeakConceptItem] = []
    study_plan: list[StudyPlanItem] = []


# ---------------------------------------------------------------------------
# Report Tokens (instructor-facing token list)
# ---------------------------------------------------------------------------

class StudentTokenItem(BaseModel):
    student_id: str
    token: str
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


class StudentTokenListResponse(BaseModel):
    tokens: list[StudentTokenItem] = []


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

class ParametersSchema(BaseModel):
    alpha: float = Field(1.0, ge=0.0, le=5.0)
    beta: float = Field(0.3, ge=0.0, le=5.0)
    gamma: float = Field(0.2, ge=0.0, le=5.0)
    threshold: float = Field(0.6, ge=0.0, le=1.0)
    k: int = Field(4, ge=2, le=20)


class ParametersResponse(BaseModel):
    status: str = "ok"
    alpha: float
    beta: float
    gamma: float
    threshold: float
    k: int = 4

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Intervention Results
# ---------------------------------------------------------------------------

class InterventionItem(BaseModel):
    concept_id: str
    students_affected: int
    downstream_concepts: int
    current_readiness: float
    impact: float
    rationale: str
    suggested_format: str


class InterventionsResponse(BaseModel):
    interventions: list[InterventionItem] = []


# ---------------------------------------------------------------------------
# AI Suggestions
# ---------------------------------------------------------------------------

class ConceptTagSuggestion(BaseModel):
    concept_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str


class ConceptTagRequest(BaseModel):
    question_text: str
    concept_catalog: list[str] = []


class ConceptTagResponse(BaseModel):
    request_id: UUID
    suggestion_id: UUID
    suggestions: list[ConceptTagSuggestion] = []
    model: str = ""
    prompt_version: str = ""


class PrereqEdgeSuggestion(BaseModel):
    source: str
    target: str
    weight: float = Field(0.5, ge=0.0, le=1.0)
    rationale: str


class PrereqEdgeRequest(BaseModel):
    concepts: list[str]
    context: str = ""


class PrereqEdgeResponse(BaseModel):
    request_id: UUID
    suggestion_id: UUID
    suggestions: list[PrereqEdgeSuggestion] = []
    model: str = ""
    prompt_version: str = ""


class InterventionDraftRequest(BaseModel):
    cluster_centroid: dict[str, float]
    weak_concepts: list[str]
    student_count: int = 0


class InterventionDraftItem(BaseModel):
    concept_id: str
    intervention_type: str
    description: str
    rationale: str


class InterventionDraftResponse(BaseModel):
    request_id: UUID
    suggestion_id: UUID
    drafts: list[InterventionDraftItem] = []
    model: str = ""
    prompt_version: str = ""


# ---------------------------------------------------------------------------
# AI Suggestion Review
# ---------------------------------------------------------------------------

class SuggestionReviewAction(BaseModel):
    action: str = Field(..., pattern="^(accept|reject)$")
    note: str = ""


class BulkReviewRequest(BaseModel):
    suggestion_ids: list[UUID]
    action: str = Field(..., pattern="^(accept|reject)$")
    note: str = ""


class SuggestionListItem(BaseModel):
    id: UUID
    suggestion_type: str
    status: str
    output_payload: dict[str, Any]
    validation_errors: Optional[list[dict[str, Any]]] = None
    model: Optional[str] = None
    prompt_version: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None
    created_at: datetime


class SuggestionListResponse(BaseModel):
    suggestions: list[SuggestionListItem] = []
    total: int = 0
    pending: int = 0
    accepted: int = 0
    rejected: int = 0
    applied: int = 0


class ApplySuggestionsRequest(BaseModel):
    suggestion_ids: list[UUID]


class ApplySuggestionsResponse(BaseModel):
    status: str
    applied_count: int = 0
    errors: list[str] = []


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

class ExportRequest(BaseModel):
    compute_run_id: Optional[UUID] = None


class ExportStatusResponse(BaseModel):
    id: UUID
    exam_id: UUID
    status: str
    file_checksum: Optional[str] = None
    manifest: Optional[dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ExportListResponse(BaseModel):
    exports: list[ExportStatusResponse] = []


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    service: str
    database: str = "unknown"
    openai: str = "unknown"


# ---------------------------------------------------------------------------
# Compute Runs
# ---------------------------------------------------------------------------

class ComputeRunResponse(BaseModel):
    id: UUID
    run_id: UUID
    exam_id: UUID
    status: str
    students_processed: Optional[int] = None
    concepts_processed: Optional[int] = None
    parameters: Optional[dict[str, Any]] = None
    graph_version: Optional[int] = None
    duration_ms: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Chat (agentic AI assistant)
# ---------------------------------------------------------------------------

class ChatSessionCreate(BaseModel):
    exam_id: Optional[UUID] = None
    title: str = ""


class ChatSessionResponse(BaseModel):
    id: UUID
    exam_id: Optional[UUID] = None
    title: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageResponse(BaseModel):
    id: UUID
    role: str
    content: Optional[str] = None
    tool_calls: Optional[list[dict[str, Any]]] = None
    tool_name: Optional[str] = None
    created_at: datetime


class ChatSendRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    exam_id: Optional[UUID] = None


class ChatSendResponse(BaseModel):
    session_id: UUID
    assistant_message: str
    tool_calls_made: list[str] = []
