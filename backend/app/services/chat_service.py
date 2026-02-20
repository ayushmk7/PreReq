"""Agentic AI chat service using OpenAI function calling.

The assistant has full read access to all ConceptLens data and can
trigger actions like recomputation, parameter updates, export generation,
and AI suggestion workflows. Every tool call maps to a real database
query or system action.
"""

import json
import logging
from typing import Any, Optional
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.models import (
    ChatMessage,
    ChatSession,
    ClassAggregate,
    Cluster,
    ClusterAssignment,
    ComputeRun,
    ConceptGraph,
    Course,
    Exam,
    InterventionResult,
    Parameter,
    Question,
    QuestionConceptMap,
    ReadinessResult,
    Score,
)

logger = logging.getLogger("conceptlens.chat")

_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=60,
            max_retries=2,
        )
    return _client


SYSTEM_PROMPT = """You are the ConceptLens AI Assistant — an expert educational analytics agent built into a concept-readiness analysis platform for university instructors.

You have FULL access to the instructor's course data through your tools. You can:
- Look up any student's grades, readiness scores, and study plans
- Analyze class-wide performance patterns, concept mastery distributions, and foundational gaps
- Inspect the concept dependency graph (prerequisites, weights)
- View cluster analysis and intervention recommendations
- Trigger recomputation with different parameters
- Update computation parameters (alpha, beta, gamma, threshold, k)
- Generate Canvas-ready export bundles for download
- Draft AI-powered concept tag suggestions and prerequisite edge suggestions

IMPORTANT BEHAVIORAL RULES:
- Always use your tools to fetch real data before answering data questions — never guess or hallucinate numbers.
- When asked about a student, always pull their actual readiness data first.
- When asked about class performance, pull aggregates first.
- Be proactive: if an instructor asks "how are my students doing", pull the class aggregates and alerts.
- When performing actions (compute, parameter updates, exports), confirm what you did and share the result.
- Present data clearly with key numbers highlighted. Use tables when comparing multiple items.
- If the exam_id context is set for the session, use it automatically. Otherwise ask the instructor which exam they mean.
- Be concise but thorough. Instructors are busy.
- Never reveal raw database IDs to the instructor — use human-readable names and labels."""


# ---------------------------------------------------------------------------
# Tool definitions for OpenAI function calling
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_courses",
            "description": "List all courses the instructor has created.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_exams",
            "description": "List all exams for a specific course.",
            "parameters": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "string", "description": "Course UUID"},
                },
                "required": ["course_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_student_list",
            "description": "Get the list of all students who have scores for a given exam.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {"type": "string", "description": "Exam UUID"},
                },
                "required": ["exam_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_student_readiness",
            "description": "Get detailed readiness scores for a specific student across all concepts. Shows direct readiness, penalties, boosts, final score, and confidence per concept.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {"type": "string", "description": "Exam UUID"},
                    "student_id": {"type": "string", "description": "External student ID (e.g. S001)"},
                },
                "required": ["exam_id", "student_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_class_aggregates",
            "description": "Get class-wide aggregate statistics per concept: mean, median, std deviation, and count of students below threshold.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {"type": "string", "description": "Exam UUID"},
                },
                "required": ["exam_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_concept_graph",
            "description": "Get the concept dependency graph (nodes and prerequisite edges with weights).",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {"type": "string", "description": "Exam UUID"},
                },
                "required": ["exam_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_clusters",
            "description": "Get misconception cluster analysis: cluster centroids, student counts, top weak concepts, and student-to-cluster assignments.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {"type": "string", "description": "Exam UUID"},
                },
                "required": ["exam_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_interventions",
            "description": "Get ranked intervention recommendations sorted by estimated impact. Shows affected students, downstream effects, and suggested actions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {"type": "string", "description": "Exam UUID"},
                },
                "required": ["exam_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_struggling_students",
            "description": "Find students whose readiness for a specific concept is below a given threshold.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {"type": "string", "description": "Exam UUID"},
                    "concept_id": {"type": "string", "description": "Concept ID to check"},
                    "threshold": {"type": "number", "description": "Readiness threshold (default 0.6)"},
                },
                "required": ["exam_id", "concept_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_student_scores",
            "description": "Get raw exam scores for a specific student — shows score per question with max score.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {"type": "string", "description": "Exam UUID"},
                    "student_id": {"type": "string", "description": "External student ID"},
                },
                "required": ["exam_id", "student_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_parameters",
            "description": "Get the current computation parameters for an exam (alpha, beta, gamma, threshold, k).",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {"type": "string", "description": "Exam UUID"},
                },
                "required": ["exam_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_parameters",
            "description": "Update computation parameters for an exam. Does NOT automatically recompute — instructor must trigger compute separately.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {"type": "string", "description": "Exam UUID"},
                    "alpha": {"type": "number", "description": "Weight of direct readiness (0-5, default 1.0)"},
                    "beta": {"type": "number", "description": "Weight of prerequisite penalty (0-5, default 0.3)"},
                    "gamma": {"type": "number", "description": "Weight of downstream boost (0-5, default 0.2)"},
                    "threshold": {"type": "number", "description": "Weakness threshold (0-1, default 0.6)"},
                    "k": {"type": "integer", "description": "Number of clusters (2-20, default 4)"},
                },
                "required": ["exam_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_compute",
            "description": "Run the full readiness computation pipeline for an exam. This recomputes all student readiness scores, class aggregates, clusters, and interventions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {"type": "string", "description": "Exam UUID"},
                },
                "required": ["exam_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_export",
            "description": "Generate a Canvas-ready export zip bundle containing all readiness data, graphs, clusters, and interventions for manual download and Canvas upload.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {"type": "string", "description": "Exam UUID"},
                },
                "required": ["exam_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_and_bottom_students",
            "description": "Get the top N and bottom N performing students by average readiness across all concepts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {"type": "string", "description": "Exam UUID"},
                    "n": {"type": "integer", "description": "Number of top/bottom students to return (default 5)"},
                },
                "required": ["exam_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_concept_detail",
            "description": "Get detailed info about a specific concept: class average readiness, student distribution, upstream prerequisites, and downstream dependents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {"type": "string", "description": "Exam UUID"},
                    "concept_id": {"type": "string", "description": "Concept ID"},
                },
                "required": ["exam_id", "concept_id"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Tool execution: each function queries the DB or triggers an action
# ---------------------------------------------------------------------------

async def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
    db: AsyncSession,
    session_exam_id: Optional[str] = None,
) -> str:
    """Execute a tool call and return the result as a JSON string."""
    if "exam_id" not in arguments and session_exam_id:
        arguments["exam_id"] = session_exam_id

    try:
        handler = _TOOL_HANDLERS.get(tool_name)
        if not handler:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        result = await handler(arguments, db)
        return json.dumps(result, default=str)
    except Exception as e:
        logger.exception(f"Tool execution error: {tool_name}")
        return json.dumps({"error": str(e)})


async def _list_courses(args: dict, db: AsyncSession) -> Any:
    result = await db.execute(select(Course).order_by(Course.created_at.desc()))
    courses = result.scalars().all()
    return {"courses": [{"id": str(c.id), "name": c.name} for c in courses]}


async def _list_exams(args: dict, db: AsyncSession) -> Any:
    cid = args["course_id"]
    result = await db.execute(
        select(Exam).where(Exam.course_id == cid).order_by(Exam.created_at.desc())
    )
    exams = result.scalars().all()
    return {"exams": [{"id": str(e.id), "name": e.name} for e in exams]}


async def _get_student_list(args: dict, db: AsyncSession) -> Any:
    eid = args["exam_id"]
    result = await db.execute(
        select(Score.student_id_external)
        .where(Score.exam_id == eid)
        .distinct()
        .order_by(Score.student_id_external)
    )
    students = [row[0] for row in result.all()]
    return {"exam_id": eid, "student_count": len(students), "students": students}


async def _get_student_readiness(args: dict, db: AsyncSession) -> Any:
    eid, sid = args["exam_id"], args["student_id"]
    result = await db.execute(
        select(ReadinessResult).where(
            ReadinessResult.exam_id == eid,
            ReadinessResult.student_id_external == sid,
        )
    )
    rows = result.scalars().all()
    if not rows:
        return {"error": f"No readiness data found for student '{sid}'"}

    label_map = await _get_label_map(eid, db)
    concepts = []
    for r in sorted(rows, key=lambda x: x.final_readiness):
        concepts.append({
            "concept": label_map.get(r.concept_id, r.concept_id),
            "concept_id": r.concept_id,
            "direct_readiness": round(r.direct_readiness, 3) if r.direct_readiness is not None else None,
            "prerequisite_penalty": round(r.prerequisite_penalty, 3),
            "downstream_boost": round(r.downstream_boost, 3),
            "final_readiness": round(r.final_readiness, 3),
            "confidence": r.confidence,
        })
    avg = sum(c["final_readiness"] for c in concepts) / len(concepts) if concepts else 0
    return {
        "student_id": sid,
        "average_readiness": round(avg, 3),
        "concepts": concepts,
    }


async def _get_class_aggregates(args: dict, db: AsyncSession) -> Any:
    eid = args["exam_id"]
    result = await db.execute(
        select(ClassAggregate).where(ClassAggregate.exam_id == eid)
    )
    rows = result.scalars().all()
    label_map = await _get_label_map(eid, db)
    aggs = []
    for a in sorted(rows, key=lambda x: x.mean_readiness):
        aggs.append({
            "concept": label_map.get(a.concept_id, a.concept_id),
            "mean": round(a.mean_readiness, 3),
            "median": round(a.median_readiness, 3),
            "std": round(a.std_readiness, 3),
            "below_threshold": a.below_threshold_count,
        })
    return {"aggregates": aggs}


async def _get_concept_graph(args: dict, db: AsyncSession) -> Any:
    eid = args["exam_id"]
    result = await db.execute(
        select(ConceptGraph)
        .where(ConceptGraph.exam_id == eid)
        .order_by(ConceptGraph.version.desc())
        .limit(1)
    )
    g = result.scalar_one_or_none()
    if not g:
        return {"error": "No concept graph found for this exam"}
    nodes = g.graph_json.get("nodes", [])
    edges = g.graph_json.get("edges", [])
    return {
        "version": g.version,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": [{"id": n["id"], "label": n.get("label", n["id"])} for n in nodes],
        "edges": [{"from": e["source"], "to": e["target"], "weight": e.get("weight", 0.5)} for e in edges],
    }


async def _get_clusters(args: dict, db: AsyncSession) -> Any:
    eid = args["exam_id"]
    cl_result = await db.execute(select(Cluster).where(Cluster.exam_id == eid))
    clusters = cl_result.scalars().all()
    if not clusters:
        return {"error": "No clusters found. Run compute first."}

    label_map = await _get_label_map(eid, db)
    items = []
    for c in clusters:
        centroid = c.centroid_json or {}
        sorted_concepts = sorted(centroid.items(), key=lambda x: x[1])
        weak = [label_map.get(k, k) for k, _ in sorted_concepts[:3]]
        items.append({
            "label": c.cluster_label,
            "student_count": c.student_count,
            "top_weak_concepts": weak,
            "centroid_summary": {label_map.get(k, k): round(v, 3) for k, v in sorted_concepts[:5]},
        })

    assign_result = await db.execute(
        select(ClusterAssignment, Cluster)
        .join(Cluster, ClusterAssignment.cluster_id == Cluster.id)
        .where(ClusterAssignment.exam_id == eid)
    )
    assignments = [
        {"student": a.student_id_external, "cluster": c.cluster_label}
        for a, c in assign_result.all()
    ]
    return {"clusters": items, "assignments": assignments}


async def _get_interventions(args: dict, db: AsyncSession) -> Any:
    eid = args["exam_id"]
    result = await db.execute(
        select(InterventionResult)
        .where(InterventionResult.exam_id == eid)
        .order_by(InterventionResult.impact.desc())
    )
    rows = result.scalars().all()
    label_map = await _get_label_map(eid, db)
    return {
        "interventions": [
            {
                "concept": label_map.get(r.concept_id, r.concept_id),
                "students_affected": r.students_affected,
                "downstream_concepts": r.downstream_concepts,
                "current_readiness": round(r.current_readiness, 3),
                "impact": round(r.impact, 2),
                "rationale": r.rationale,
                "suggested_format": r.suggested_format,
            }
            for r in rows
        ]
    }


async def _find_struggling_students(args: dict, db: AsyncSession) -> Any:
    eid = args["exam_id"]
    cid = args["concept_id"]
    threshold = args.get("threshold", 0.6)
    result = await db.execute(
        select(ReadinessResult).where(
            ReadinessResult.exam_id == eid,
            ReadinessResult.concept_id == cid,
            ReadinessResult.final_readiness < threshold,
        ).order_by(ReadinessResult.final_readiness)
    )
    rows = result.scalars().all()
    label_map = await _get_label_map(eid, db)
    return {
        "concept": label_map.get(cid, cid),
        "threshold": threshold,
        "count": len(rows),
        "students": [
            {"student_id": r.student_id_external, "readiness": round(r.final_readiness, 3), "confidence": r.confidence}
            for r in rows
        ],
    }


async def _get_student_scores(args: dict, db: AsyncSession) -> Any:
    eid, sid = args["exam_id"], args["student_id"]
    result = await db.execute(
        select(Score, Question)
        .join(Question, Score.question_id == Question.id)
        .where(Score.exam_id == eid, Score.student_id_external == sid)
    )
    rows = result.all()
    if not rows:
        return {"error": f"No scores found for student '{sid}'"}
    total = sum(s.score for s, _ in rows)
    max_total = sum(q.max_score for _, q in rows)
    return {
        "student_id": sid,
        "total_score": total,
        "max_possible": max_total,
        "percentage": round(total / max_total * 100, 1) if max_total > 0 else 0,
        "questions": [
            {"question": q.question_id_external, "score": s.score, "max_score": q.max_score}
            for s, q in rows
        ],
    }


async def _get_parameters(args: dict, db: AsyncSession) -> Any:
    eid = args["exam_id"]
    result = await db.execute(select(Parameter).where(Parameter.exam_id == eid))
    p = result.scalar_one_or_none()
    if not p:
        return {"alpha": 1.0, "beta": 0.3, "gamma": 0.2, "threshold": 0.6, "k": 4}
    return {"alpha": p.alpha, "beta": p.beta, "gamma": p.gamma, "threshold": p.threshold, "k": p.k}


async def _update_parameters(args: dict, db: AsyncSession) -> Any:
    eid = args["exam_id"]
    result = await db.execute(select(Parameter).where(Parameter.exam_id == eid))
    p = result.scalar_one_or_none()
    if not p:
        return {"error": "No parameters found for this exam"}

    updated = {}
    for key in ("alpha", "beta", "gamma", "threshold", "k"):
        if key in args and args[key] is not None:
            setattr(p, key, args[key])
            updated[key] = args[key]
    await db.flush()
    return {"status": "updated", "changed": updated, "note": "Parameters updated. Run compute to apply changes."}


async def _trigger_compute(args: dict, db: AsyncSession) -> Any:
    from app.routers.compute import compute_readiness
    from app.schemas.schemas import ComputeRequest

    eid = args["exam_id"]
    p_result = await db.execute(select(Parameter).where(Parameter.exam_id == eid))
    p = p_result.scalar_one_or_none()

    body = ComputeRequest(
        alpha=p.alpha if p else 1.0,
        beta=p.beta if p else 0.3,
        gamma=p.gamma if p else 0.2,
        threshold=p.threshold if p else 0.6,
        k=p.k if p else 4,
    )

    try:
        result = await compute_readiness(
            exam_id=UUID(eid),
            body=body,
            db=db,
            _user="ai_assistant",
        )
        return {
            "status": "success",
            "run_id": str(result.run_id),
            "students_processed": result.students_processed,
            "concepts_processed": result.concepts_processed,
            "time_ms": result.time_ms,
        }
    except Exception as e:
        return {"error": f"Compute failed: {str(e)}"}


async def _generate_export(args: dict, db: AsyncSession) -> Any:
    from app.routers.export import create_export
    from app.schemas.schemas import ExportRequest

    eid = args["exam_id"]
    try:
        result = await create_export(
            exam_id=UUID(eid),
            body=ExportRequest(),
            db=db,
            _user="ai_assistant",
        )
        return {
            "status": result.status,
            "export_id": str(result.id),
            "checksum": result.file_checksum,
            "note": "Export bundle generated. The instructor can download it from the export endpoint.",
        }
    except Exception as e:
        return {"error": f"Export failed: {str(e)}"}


async def _get_top_and_bottom_students(args: dict, db: AsyncSession) -> Any:
    eid = args["exam_id"]
    n = args.get("n", 5)
    result = await db.execute(
        select(
            ReadinessResult.student_id_external,
            func.avg(ReadinessResult.final_readiness).label("avg_readiness"),
        )
        .where(ReadinessResult.exam_id == eid)
        .group_by(ReadinessResult.student_id_external)
        .order_by(func.avg(ReadinessResult.final_readiness).desc())
    )
    all_students = result.all()
    top = [{"student": s, "avg_readiness": round(float(a), 3)} for s, a in all_students[:n]]
    bottom = [{"student": s, "avg_readiness": round(float(a), 3)} for s, a in all_students[-n:]]
    return {"top_performers": top, "struggling_students": list(reversed(bottom)), "total_students": len(all_students)}


async def _get_concept_detail(args: dict, db: AsyncSession) -> Any:
    eid, cid = args["exam_id"], args["concept_id"]
    label_map = await _get_label_map(eid, db)

    rr_result = await db.execute(
        select(ReadinessResult).where(
            ReadinessResult.exam_id == eid,
            ReadinessResult.concept_id == cid,
        )
    )
    rows = rr_result.scalars().all()
    if not rows:
        return {"error": f"No data for concept '{cid}'"}

    scores = [r.final_readiness for r in rows]
    import numpy as np
    arr = np.array(scores)

    g_result = await db.execute(
        select(ConceptGraph)
        .where(ConceptGraph.exam_id == eid)
        .order_by(ConceptGraph.version.desc())
        .limit(1)
    )
    graph_row = g_result.scalar_one_or_none()
    prereqs, dependents = [], []
    if graph_row:
        for e in graph_row.graph_json.get("edges", []):
            if e["target"] == cid:
                prereqs.append({"concept": label_map.get(e["source"], e["source"]), "weight": e.get("weight", 0.5)})
            if e["source"] == cid:
                dependents.append({"concept": label_map.get(e["target"], e["target"]), "weight": e.get("weight", 0.5)})

    return {
        "concept": label_map.get(cid, cid),
        "concept_id": cid,
        "student_count": len(rows),
        "mean_readiness": round(float(np.mean(arr)), 3),
        "median_readiness": round(float(np.median(arr)), 3),
        "std_readiness": round(float(np.std(arr)), 3),
        "below_06": int(np.sum(arr < 0.6)),
        "below_04": int(np.sum(arr < 0.4)),
        "prerequisites": prereqs,
        "dependents": dependents,
    }


# Lookup helper
async def _get_label_map(exam_id: str, db: AsyncSession) -> dict[str, str]:
    result = await db.execute(
        select(ConceptGraph)
        .where(ConceptGraph.exam_id == exam_id)
        .order_by(ConceptGraph.version.desc())
        .limit(1)
    )
    g = result.scalar_one_or_none()
    if not g:
        return {}
    return {n["id"]: n.get("label", n["id"]) for n in g.graph_json.get("nodes", [])}


_TOOL_HANDLERS = {
    "list_courses": _list_courses,
    "list_exams": _list_exams,
    "get_student_list": _get_student_list,
    "get_student_readiness": _get_student_readiness,
    "get_class_aggregates": _get_class_aggregates,
    "get_concept_graph": _get_concept_graph,
    "get_clusters": _get_clusters,
    "get_interventions": _get_interventions,
    "find_struggling_students": _find_struggling_students,
    "get_student_scores": _get_student_scores,
    "get_parameters": _get_parameters,
    "update_parameters": _update_parameters,
    "trigger_compute": _trigger_compute,
    "generate_export": _generate_export,
    "get_top_and_bottom_students": _get_top_and_bottom_students,
    "get_concept_detail": _get_concept_detail,
}


# ---------------------------------------------------------------------------
# Agentic conversation loop
# ---------------------------------------------------------------------------

async def run_agent_turn(
    session: ChatSession,
    user_message: str,
    db: AsyncSession,
) -> tuple[str, list[str]]:
    """Run a full agent turn: send user message, loop through tool calls, return final response.

    Returns (assistant_text, list_of_tool_names_called).
    """
    client = _get_client()

    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=user_message,
    )
    db.add(user_msg)
    await db.flush()

    # Reload messages to include the one we just added
    msg_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at)
    )
    all_messages = msg_result.scalars().all()

    # Build conversation history from persisted messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if session.exam_id:
        messages[0]["content"] += f"\n\nCurrent exam context: exam_id = {session.exam_id}"

    for msg in all_messages:
        if msg.role == "user":
            messages.append({"role": "user", "content": msg.content or ""})
        elif msg.role == "assistant":
            entry: dict[str, Any] = {"role": "assistant"}
            if msg.content:
                entry["content"] = msg.content
            if msg.tool_calls_json:
                entry["tool_calls"] = msg.tool_calls_json
                if not msg.content:
                    entry["content"] = ""
            messages.append(entry)
        elif msg.role == "tool":
            messages.append({
                "role": "tool",
                "tool_call_id": msg.tool_call_id or "",
                "content": msg.content or "",
            })

    tools_called: list[str] = []
    max_iterations = 10

    for _ in range(max_iterations):
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.3,
        )

        choice = response.choices[0]
        assistant_msg = choice.message

        if assistant_msg.tool_calls:
            tc_json = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in assistant_msg.tool_calls
            ]

            db_assistant_msg = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=assistant_msg.content or "",
                tool_calls_json=tc_json,
                token_usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                },
            )
            db.add(db_assistant_msg)
            await db.flush()

            messages.append({
                "role": "assistant",
                "content": assistant_msg.content or "",
                "tool_calls": tc_json,
            })

            for tc in assistant_msg.tool_calls:
                tool_name = tc.function.name
                tools_called.append(tool_name)

                try:
                    tool_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                tool_result = await execute_tool(
                    tool_name,
                    tool_args,
                    db,
                    session_exam_id=str(session.exam_id) if session.exam_id else None,
                )

                tool_msg = ChatMessage(
                    session_id=session.id,
                    role="tool",
                    content=tool_result,
                    tool_call_id=tc.id,
                    tool_name=tool_name,
                )
                db.add(tool_msg)
                await db.flush()

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool_result,
                })

        else:
            final_text = assistant_msg.content or ""
            db_final = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=final_text,
                token_usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                },
            )
            db.add(db_final)
            await db.flush()
            return final_text, tools_called

    return "I've reached the maximum number of tool calls for this turn. Please try a more specific question.", tools_called
