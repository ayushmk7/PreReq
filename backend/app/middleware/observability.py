"""Observability middleware: structured logging, correlation IDs, and request metrics.

Attaches a unique correlation_id to every request and logs structured
request/response metadata for operational transparency.
"""

import logging
import time
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("conceptlens.http")

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware that adds correlation IDs and logs request/response metrics."""

    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        correlation_id_var.set(req_id)

        start = time.time()
        method = request.method
        path = request.url.path

        logger.info(
            "request_start",
            extra={
                "correlation_id": req_id,
                "method": method,
                "path": path,
                "client": request.client.host if request.client else "unknown",
            },
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.time() - start) * 1000, 2)
            logger.error(
                "request_error",
                extra={
                    "correlation_id": req_id,
                    "method": method,
                    "path": path,
                    "duration_ms": duration_ms,
                    "error": str(exc),
                },
            )
            raise

        duration_ms = round((time.time() - start) * 1000, 2)
        status_code = response.status_code

        log_level = logging.WARNING if status_code >= 400 else logging.INFO
        logger.log(
            log_level,
            "request_complete",
            extra={
                "correlation_id": req_id,
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
        )

        response.headers["X-Request-ID"] = req_id
        response.headers["X-Duration-Ms"] = str(duration_ms)

        return response


def get_correlation_id() -> str:
    """Get the current request's correlation ID from context."""
    return correlation_id_var.get()
