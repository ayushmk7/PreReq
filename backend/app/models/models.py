"""SQLAlchemy ORM models for all database tables."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _uuid():
    return uuid.uuid4()


def _now():
    return datetime.utcnow()


# ---------------------------------------------------------------------------
# Courses & Exams
# ---------------------------------------------------------------------------

class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=_now, nullable=False)

    exams = relationship("Exam", back_populates="course", cascade="all, delete-orphan")


class Exam(Base):
    __tablename__ = "exams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=_now, nullable=False)

    course = relationship("Course", back_populates="exams")
    concept_graphs = relationship("ConceptGraph", back_populates="exam", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="exam", cascade="all, delete-orphan")
    readiness_results = relationship("ReadinessResult", back_populates="exam", cascade="all, delete-orphan")
    class_aggregates = relationship("ClassAggregate", back_populates="exam", cascade="all, delete-orphan")
    clusters = relationship("Cluster", back_populates="exam", cascade="all, delete-orphan")
    cluster_assignments = relationship("ClusterAssignment", back_populates="exam", cascade="all, delete-orphan")
    student_tokens = relationship("StudentToken", back_populates="exam", cascade="all, delete-orphan")
    parameters = relationship("Parameter", back_populates="exam", uselist=False, cascade="all, delete-orphan")
    compute_runs = relationship("ComputeRun", back_populates="exam", cascade="all, delete-orphan")
    ai_suggestions = relationship("AISuggestion", back_populates="exam", cascade="all, delete-orphan")
    intervention_results = relationship("InterventionResult", back_populates="exam", cascade="all, delete-orphan")
    export_runs = relationship("ExportRun", back_populates="exam", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Concept Graphs
# ---------------------------------------------------------------------------

class ConceptGraph(Base):
    __tablename__ = "concept_graphs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    graph_json = Column(JSONB, nullable=False)
    annotation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)

    exam = relationship("Exam", back_populates="concept_graphs")


# ---------------------------------------------------------------------------
# Questions & Concept Mapping
# ---------------------------------------------------------------------------

class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    question_id_external = Column(String(255), nullable=False)
    question_text = Column(Text, nullable=True)
    max_score = Column(Float, nullable=False, default=1.0)

    exam = relationship("Exam", back_populates="questions")
    concept_maps = relationship("QuestionConceptMap", back_populates="question", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="question", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("exam_id", "question_id_external", name="uq_question_exam_external"),
    )


class QuestionConceptMap(Base):
    __tablename__ = "question_concept_map"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    concept_id = Column(String(255), nullable=False)
    weight = Column(Float, nullable=False, default=1.0)

    question = relationship("Question", back_populates="concept_maps")


# ---------------------------------------------------------------------------
# Scores
# ---------------------------------------------------------------------------

class Score(Base):
    __tablename__ = "scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    student_id_external = Column(String(255), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    score = Column(Float, nullable=False)

    exam = relationship("Exam", back_populates="scores")
    question = relationship("Question", back_populates="scores")

    __table_args__ = (
        UniqueConstraint("exam_id", "student_id_external", "question_id", name="uq_score_student_question"),
    )


# ---------------------------------------------------------------------------
# Readiness Results
# ---------------------------------------------------------------------------

class ReadinessResult(Base):
    __tablename__ = "readiness_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    run_id = Column(UUID(as_uuid=True), nullable=True)
    student_id_external = Column(String(255), nullable=False)
    concept_id = Column(String(255), nullable=False)
    direct_readiness = Column(Float, nullable=True)
    prerequisite_penalty = Column(Float, nullable=False, default=0.0)
    downstream_boost = Column(Float, nullable=False, default=0.0)
    final_readiness = Column(Float, nullable=False)
    confidence = Column(String(10), nullable=False)
    explanation_trace_json = Column(JSONB, nullable=True)

    exam = relationship("Exam", back_populates="readiness_results")

    __table_args__ = (
        UniqueConstraint("exam_id", "student_id_external", "concept_id", name="uq_readiness_student_concept"),
    )


# ---------------------------------------------------------------------------
# Class Aggregates
# ---------------------------------------------------------------------------

class ClassAggregate(Base):
    __tablename__ = "class_aggregates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    run_id = Column(UUID(as_uuid=True), nullable=True)
    concept_id = Column(String(255), nullable=False)
    mean_readiness = Column(Float, nullable=False)
    median_readiness = Column(Float, nullable=False)
    std_readiness = Column(Float, nullable=False)
    below_threshold_count = Column(Integer, nullable=False)

    exam = relationship("Exam", back_populates="class_aggregates")

    __table_args__ = (
        UniqueConstraint("exam_id", "concept_id", name="uq_aggregate_exam_concept"),
    )


# ---------------------------------------------------------------------------
# Clusters
# ---------------------------------------------------------------------------

class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    run_id = Column(UUID(as_uuid=True), nullable=True)
    cluster_label = Column(String(100), nullable=False)
    centroid_json = Column(JSONB, nullable=True)
    student_count = Column(Integer, nullable=False, default=0)

    exam = relationship("Exam", back_populates="clusters")
    assignments = relationship("ClusterAssignment", back_populates="cluster", cascade="all, delete-orphan")


class ClusterAssignment(Base):
    __tablename__ = "cluster_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    student_id_external = Column(String(255), nullable=False)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("clusters.id", ondelete="CASCADE"), nullable=False)

    exam = relationship("Exam", back_populates="cluster_assignments")
    cluster = relationship("Cluster", back_populates="assignments")

    __table_args__ = (
        UniqueConstraint("exam_id", "student_id_external", name="uq_cluster_assignment_student"),
    )


# ---------------------------------------------------------------------------
# Student Tokens
# ---------------------------------------------------------------------------

class StudentToken(Base):
    __tablename__ = "student_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    student_id_external = Column(String(255), nullable=False)
    token = Column(UUID(as_uuid=True), default=_uuid, unique=True, nullable=False)
    created_at = Column(DateTime, default=_now, nullable=False)

    exam = relationship("Exam", back_populates="student_tokens")

    __table_args__ = (
        UniqueConstraint("exam_id", "student_id_external", name="uq_token_exam_student"),
    )


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

class Parameter(Base):
    __tablename__ = "parameters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, unique=True)
    alpha = Column(Float, nullable=False, default=1.0)
    beta = Column(Float, nullable=False, default=0.3)
    gamma = Column(Float, nullable=False, default=0.2)
    threshold = Column(Float, nullable=False, default=0.6)
    k = Column(Integer, nullable=False, default=4)

    exam = relationship("Exam", back_populates="parameters")


# ---------------------------------------------------------------------------
# Compute Runs (deterministic tracking)
# ---------------------------------------------------------------------------

class ComputeRun(Base):
    __tablename__ = "compute_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    run_id = Column(UUID(as_uuid=True), default=_uuid, unique=True, nullable=False)
    status = Column(String(20), nullable=False, default="running")  # running, success, failed
    students_processed = Column(Integer, nullable=True)
    concepts_processed = Column(Integer, nullable=True)
    parameters_json = Column(JSONB, nullable=True)
    graph_version = Column(Integer, nullable=True)
    duration_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    exam = relationship("Exam", back_populates="compute_runs")


# ---------------------------------------------------------------------------
# Intervention Results (persisted from compute)
# ---------------------------------------------------------------------------

class InterventionResult(Base):
    __tablename__ = "intervention_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    run_id = Column(UUID(as_uuid=True), nullable=True)
    concept_id = Column(String(255), nullable=False)
    students_affected = Column(Integer, nullable=False)
    downstream_concepts = Column(Integer, nullable=False)
    current_readiness = Column(Float, nullable=False)
    impact = Column(Float, nullable=False)
    rationale = Column(Text, nullable=True)
    suggested_format = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)

    exam = relationship("Exam", back_populates="intervention_results")


# ---------------------------------------------------------------------------
# AI Suggestions (LLM-assisted features with review workflow)
# ---------------------------------------------------------------------------

class AISuggestion(Base):
    __tablename__ = "ai_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    suggestion_type = Column(String(50), nullable=False)  # concept_tag, prereq_edge, intervention
    status = Column(String(20), nullable=False, default="pending")  # pending, accepted, rejected, applied
    input_payload = Column(JSONB, nullable=True)
    output_payload = Column(JSONB, nullable=False)
    model = Column(String(100), nullable=True)
    prompt_version = Column(String(50), nullable=True)
    request_id = Column(UUID(as_uuid=True), default=_uuid, nullable=False)
    token_usage = Column(JSONB, nullable=True)
    latency_ms = Column(Float, nullable=True)
    validation_errors = Column(JSONB, nullable=True)
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_note = Column(Text, nullable=True)
    applied_at = Column(DateTime, nullable=True)
    before_snapshot = Column(JSONB, nullable=True)
    after_snapshot = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)

    exam = relationship("Exam", back_populates="ai_suggestions")


# ---------------------------------------------------------------------------
# Audit Log (tracks all state-changing operations)
# ---------------------------------------------------------------------------

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    exam_id = Column(UUID(as_uuid=True), nullable=True)
    actor = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(255), nullable=True)
    before_payload = Column(JSONB, nullable=True)
    after_payload = Column(JSONB, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)


# ---------------------------------------------------------------------------
# Export Runs
# ---------------------------------------------------------------------------

class ExportRun(Base):
    __tablename__ = "export_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    compute_run_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(20), nullable=False, default="generating")  # generating, ready, failed
    file_path = Column(Text, nullable=True)
    file_checksum = Column(String(64), nullable=True)
    manifest_json = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    exam = relationship("Exam", back_populates="export_runs")


# ---------------------------------------------------------------------------
# Chat (agentic AI assistant)
# ---------------------------------------------------------------------------

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(255), nullable=True)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan",
                            order_by="ChatMessage.created_at")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, tool
    content = Column(Text, nullable=True)
    tool_calls_json = Column(JSONB, nullable=True)
    tool_call_id = Column(String(255), nullable=True)
    tool_name = Column(String(100), nullable=True)
    token_usage = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)

    session = relationship("ChatSession", back_populates="messages")
