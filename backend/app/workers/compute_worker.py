"""Background worker scaffold for async compute jobs."""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from app.config import settings
from app.database import async_session
from app.services.compute_queue_service import pop_next_compute_job
from app.services.compute_runner_service import run_compute_pipeline_for_run

logger = logging.getLogger("prereq.compute_worker")


async def process_next_job() -> bool:
    """Process a single queued job, returning True if one was processed."""
    job = await pop_next_compute_job()
    if not job:
        return False

    async with async_session() as db:
        try:
            await run_compute_pipeline_for_run(
                db=db,
                exam_id=UUID(job.exam_id),
                run_id=UUID(job.run_id),
                alpha=job.alpha,
                beta=job.beta,
                gamma=job.gamma,
                threshold=job.threshold,
                k=job.k,
            )
            await db.commit()
            logger.info("compute_job_success run_id=%s exam_id=%s", job.run_id, job.exam_id)
        except Exception:
            await db.commit()
            logger.exception("compute_job_failed run_id=%s exam_id=%s", job.run_id, job.exam_id)

    return True


async def main() -> None:
    """Run worker loop."""
    poll_seconds = max(1, settings.COMPUTE_WORKER_POLL_SECONDS)
    logger.info("compute_worker_started backend=%s", settings.COMPUTE_QUEUE_BACKEND)
    while True:
        did_work = await process_next_job()
        if not did_work:
            await asyncio.sleep(poll_seconds)


if __name__ == "__main__":
    asyncio.run(main())
