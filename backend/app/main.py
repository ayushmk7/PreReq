"""ConceptLens FastAPI application entry point."""

import logging
import sys

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.middleware.observability import ObservabilityMiddleware
from app.routers import (
    ai_suggestions,
    chat,
    clusters,
    compute,
    courses,
    dashboard,
    exams,
    export,
    graph,
    parameters,
    reports,
    upload,
)

# ---------------------------------------------------------------------------
# Structured logging configuration
# ---------------------------------------------------------------------------

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="ConceptLens API",
    description=(
        "Backend API for ConceptLens — a concept readiness analysis platform "
        "for instructors and students. Computes per-student concept readiness "
        "scores using a DAG-based inference engine, provides instructor "
        "dashboards with heatmaps and root-cause tracing, generates "
        "personalized student reports, and offers AI-assisted concept "
        "tagging, graph generation, and intervention drafting."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(ObservabilityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Include routers
# ---------------------------------------------------------------------------

app.include_router(courses.router)
app.include_router(exams.router)
app.include_router(upload.router)
app.include_router(graph.router)
app.include_router(compute.router)
app.include_router(dashboard.router)
app.include_router(clusters.router)
app.include_router(reports.router)
app.include_router(parameters.router)
app.include_router(ai_suggestions.router)
app.include_router(export.router)
app.include_router(chat.router)


# ---------------------------------------------------------------------------
# Health check with dependency probes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check with dependency status."""
    from app.config import settings
    from app.database import engine

    health = {
        "status": "healthy",
        "service": "conceptlens-api",
        "database": "unknown",
        "openai": "unknown",
    }

    # Database probe
    try:
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        health["database"] = "connected"
    except Exception as e:
        health["database"] = f"error: {str(e)[:100]}"
        health["status"] = "degraded"

    # OpenAI probe (check key is configured, not actual API call)
    if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 10:
        health["openai"] = "configured"
    else:
        health["openai"] = "not_configured"

    return health
