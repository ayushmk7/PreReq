"""OpenAI-backed AI assistive service for ConceptLens.

Features:
  - Concept tag suggestion from question text
  - Prerequisite edge suggestion from concept list
  - Intervention narrative drafting from cluster stats

Design:
  - Structured JSON output via response_format
  - Versioned prompts for auditability
  - Timeout/retry/fallback handling
  - Token usage tracking
"""

import json
import logging
import time
import uuid
from typing import Any, Optional

from openai import AsyncOpenAI, APITimeoutError, APIConnectionError, RateLimitError

from app.config import settings

logger = logging.getLogger("conceptlens.ai")

PROMPT_VERSION = "v1.0"

_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
            max_retries=settings.OPENAI_MAX_RETRIES,
        )
    return _client


async def _call_openai(
    system_prompt: str,
    user_prompt: str,
    model: Optional[str] = None,
) -> dict[str, Any]:
    """Make a structured JSON call to OpenAI with error handling.

    Returns dict with: parsed_output, raw_response, model, token_usage, latency_ms, error.
    """
    client = _get_client()
    request_id = str(uuid.uuid4())
    model = model or settings.OPENAI_MODEL
    start = time.time()

    result: dict[str, Any] = {
        "request_id": request_id,
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "parsed_output": None,
        "token_usage": None,
        "latency_ms": 0,
        "error": None,
    }

    try:
        response = await client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

        result["latency_ms"] = round((time.time() - start) * 1000, 2)
        result["token_usage"] = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        }

        raw = response.choices[0].message.content or "{}"
        result["parsed_output"] = json.loads(raw)

    except json.JSONDecodeError as e:
        result["error"] = f"Failed to parse JSON response: {str(e)}"
        result["latency_ms"] = round((time.time() - start) * 1000, 2)
        logger.error("OpenAI JSON parse error", extra={"request_id": request_id, "error": str(e)})

    except (APITimeoutError, APIConnectionError) as e:
        result["error"] = f"OpenAI connection error: {str(e)}"
        result["latency_ms"] = round((time.time() - start) * 1000, 2)
        logger.error("OpenAI connection error", extra={"request_id": request_id, "error": str(e)})

    except RateLimitError as e:
        result["error"] = f"OpenAI rate limit: {str(e)}"
        result["latency_ms"] = round((time.time() - start) * 1000, 2)
        logger.warning("OpenAI rate limited", extra={"request_id": request_id})

    except Exception as e:
        result["error"] = f"OpenAI unexpected error: {str(e)}"
        result["latency_ms"] = round((time.time() - start) * 1000, 2)
        logger.exception("OpenAI unexpected error", extra={"request_id": request_id})

    return result


# ---------------------------------------------------------------------------
# Feature A: Concept Tag Suggestions
# ---------------------------------------------------------------------------

CONCEPT_TAG_SYSTEM = """You are an expert educational assessment analyst. Given exam question text and a catalog of valid concepts, suggest which concepts the question tests.

IMPORTANT RULES:
- Only suggest concepts from the provided catalog (if one is given)
- Assign a confidence score between 0.0 and 1.0
- Provide a brief rationale for each suggestion
- Return 1-5 suggestions ordered by confidence (highest first)
- If the catalog is empty, suggest reasonable concept names

Respond with valid JSON in this exact format:
{
  "suggestions": [
    {"concept_id": "string", "confidence": 0.0, "rationale": "string"}
  ]
}"""


async def suggest_concept_tags(
    question_text: str,
    concept_catalog: list[str],
) -> dict[str, Any]:
    """Suggest concept tags for a question using OpenAI.

    Returns dict with suggestions, metadata, and any errors.
    """
    catalog_str = ", ".join(concept_catalog) if concept_catalog else "(no catalog provided — suggest reasonable concept names)"

    user_prompt = f"""Question text:
{question_text}

Available concept catalog:
{catalog_str}

Analyze this question and suggest which concepts it tests."""

    result = await _call_openai(CONCEPT_TAG_SYSTEM, user_prompt)

    if result["error"]:
        return {
            "suggestions": [],
            "request_id": result["request_id"],
            "model": result["model"],
            "prompt_version": result["prompt_version"],
            "token_usage": result["token_usage"],
            "latency_ms": result["latency_ms"],
            "error": result["error"],
        }

    output = result["parsed_output"] or {}
    suggestions = output.get("suggestions", [])

    return {
        "suggestions": suggestions,
        "request_id": result["request_id"],
        "model": result["model"],
        "prompt_version": result["prompt_version"],
        "token_usage": result["token_usage"],
        "latency_ms": result["latency_ms"],
        "error": None,
    }


# ---------------------------------------------------------------------------
# Feature B: Prerequisite Edge Suggestions
# ---------------------------------------------------------------------------

PREREQ_EDGE_SYSTEM = """You are an expert curriculum designer. Given a list of educational concepts, suggest prerequisite relationships between them as directed edges (source -> target means source is a prerequisite for target).

IMPORTANT RULES:
- Only suggest edges between concepts in the provided list
- Assign dependency weights between 0.0 and 1.0 (higher = stronger dependency)
- Provide a rationale for each suggested edge
- Do NOT create cycles — ensure the relationships form a DAG
- Only suggest edges where a genuine learning dependency exists

Respond with valid JSON in this exact format:
{
  "suggestions": [
    {"source": "string", "target": "string", "weight": 0.0, "rationale": "string"}
  ]
}"""


async def suggest_prerequisite_edges(
    concepts: list[str],
    context: str = "",
) -> dict[str, Any]:
    """Suggest prerequisite edges between concepts using OpenAI."""
    concepts_str = "\n".join(f"- {c}" for c in concepts)
    context_str = f"\n\nAdditional context:\n{context}" if context else ""

    user_prompt = f"""Concepts:
{concepts_str}{context_str}

Suggest prerequisite relationships between these concepts. A prerequisite means the source concept should be learned before the target concept."""

    result = await _call_openai(PREREQ_EDGE_SYSTEM, user_prompt)

    if result["error"]:
        return {
            "suggestions": [],
            "request_id": result["request_id"],
            "model": result["model"],
            "prompt_version": result["prompt_version"],
            "token_usage": result["token_usage"],
            "latency_ms": result["latency_ms"],
            "error": result["error"],
        }

    output = result["parsed_output"] or {}
    suggestions = output.get("suggestions", [])

    return {
        "suggestions": suggestions,
        "request_id": result["request_id"],
        "model": result["model"],
        "prompt_version": result["prompt_version"],
        "token_usage": result["token_usage"],
        "latency_ms": result["latency_ms"],
        "error": None,
    }


# ---------------------------------------------------------------------------
# Feature C: Intervention Narrative Drafting
# ---------------------------------------------------------------------------

INTERVENTION_SYSTEM = """You are an expert educational intervention specialist. Given cluster statistics showing student weakness patterns, generate specific, actionable intervention recommendations for instructors.

IMPORTANT RULES:
- Each intervention should target a specific weak concept
- Suggest a concrete intervention type (review session, practice set, office hours, peer tutoring, etc.)
- Provide a clear description of what the intervention should cover
- Explain why this intervention would help based on the data
- Be specific and practical, not generic

Respond with valid JSON in this exact format:
{
  "drafts": [
    {
      "concept_id": "string",
      "intervention_type": "string",
      "description": "string",
      "rationale": "string"
    }
  ]
}"""


async def draft_intervention_narratives(
    cluster_centroid: dict[str, float],
    weak_concepts: list[str],
    student_count: int = 0,
) -> dict[str, Any]:
    """Generate intervention narratives for a cluster's weak concepts."""
    centroid_str = "\n".join(
        f"  {concept}: {score:.2f}" for concept, score in
        sorted(cluster_centroid.items(), key=lambda x: x[1])
    )

    user_prompt = f"""Cluster statistics:
- Student count: {student_count}
- Weakest concepts: {', '.join(weak_concepts)}

Full centroid readiness scores (0 = no readiness, 1 = full mastery):
{centroid_str}

Generate targeted intervention recommendations for the weak concepts in this student cluster."""

    result = await _call_openai(INTERVENTION_SYSTEM, user_prompt)

    if result["error"]:
        return {
            "drafts": [],
            "request_id": result["request_id"],
            "model": result["model"],
            "prompt_version": result["prompt_version"],
            "token_usage": result["token_usage"],
            "latency_ms": result["latency_ms"],
            "error": result["error"],
        }

    output = result["parsed_output"] or {}
    drafts = output.get("drafts", [])

    return {
        "drafts": drafts,
        "request_id": result["request_id"],
        "model": result["model"],
        "prompt_version": result["prompt_version"],
        "token_usage": result["token_usage"],
        "latency_ms": result["latency_ms"],
        "error": None,
    }
