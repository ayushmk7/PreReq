"""Queue abstraction for async compute jobs.

Current implementation uses a JSON file queue as a portable scaffold that works
without extra infrastructure. OCI Queue integration can replace this backend
behind the same interface.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional
from uuid import UUID

from app.config import settings


@dataclass
class ComputeQueueJob:
    exam_id: str
    run_id: str
    alpha: float
    beta: float
    gamma: float
    threshold: float
    k: int


def _queue_file_path() -> Path:
    return Path(settings.COMPUTE_QUEUE_FILE)


def _read_queue() -> list[dict]:
    queue_file = _queue_file_path()
    if not queue_file.exists():
        return []
    content = queue_file.read_text(encoding="utf-8").strip()
    if not content:
        return []
    try:
        data = json.loads(content)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _write_queue(items: list[dict]) -> None:
    queue_file = _queue_file_path()
    queue_file.parent.mkdir(parents=True, exist_ok=True)
    queue_file.write_text(json.dumps(items), encoding="utf-8")


async def enqueue_compute_job(
    exam_id: UUID,
    run_id: UUID,
    alpha: float,
    beta: float,
    gamma: float,
    threshold: float,
    k: int,
) -> bool:
    """Enqueue a compute job for async processing."""
    if settings.COMPUTE_QUEUE_BACKEND != "file":
        return False

    def _enqueue() -> bool:
        jobs = _read_queue()
        job = ComputeQueueJob(
            exam_id=str(exam_id),
            run_id=str(run_id),
            alpha=alpha,
            beta=beta,
            gamma=gamma,
            threshold=threshold,
            k=k,
        )
        jobs.append(asdict(job))
        _write_queue(jobs)
        return True

    return await asyncio.to_thread(_enqueue)


async def pop_next_compute_job() -> Optional[ComputeQueueJob]:
    """Pop one queued compute job, returning None when queue is empty."""
    if settings.COMPUTE_QUEUE_BACKEND != "file":
        return None

    def _pop() -> Optional[ComputeQueueJob]:
        jobs = _read_queue()
        if not jobs:
            return None
        raw = jobs.pop(0)
        _write_queue(jobs)
        return ComputeQueueJob(**raw)

    return await asyncio.to_thread(_pop)
