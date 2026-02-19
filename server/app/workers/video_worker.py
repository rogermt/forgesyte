"""Video worker - processes video analysis jobs from queue."""

import asyncio
import logging
from typing import Any, Optional

from server.app.services.video_file_pipeline_service import VideoFilePipelineService

logger = logging.getLogger(__name__)

# Default pipeline if job doesn't specify one
DEFAULT_VIDEO_PIPELINE = "ocr_only"


class FakeJobRepo:
    """Minimal in-memory job repository for testing."""

    def __init__(self):
        self.jobs = {}
        self.queue = []

    def get(self, job_id: str) -> Any:
        """Get job by ID."""
        if job_id not in self.jobs:
            raise KeyError(f"Job {job_id} not found")
        return self.jobs[job_id]

    def save(self, job: Any) -> None:
        """Save/update job."""
        self.jobs[job.id] = job

    def enqueue(self, job_id: str) -> None:
        """Add job to processing queue."""
        if job_id not in self.queue:
            self.queue.append(job_id)

    def dequeue(self) -> Optional[str]:
        """Remove and return next job from queue, or None."""
        if self.queue:
            return self.queue.pop(0)
        return None


# Global job repository
job_repo = FakeJobRepo()


async def process_job(job_id: str) -> None:
    """
    Process a single video analysis job.

    Args:
        job_id: ID of job to process

    Raises:
        KeyError: If job not found in repository
    """
    job = job_repo.get(job_id)

    logger.info(f"🎬 Worker: starting job {job_id} pipeline={job.pipeline_id}")

    try:
        # Ensure pipeline_id is set (backward compatibility)
        pipeline_id = getattr(job, "pipeline_id", None) or DEFAULT_VIDEO_PIPELINE

        # Use existing VideoFilePipelineService
        result = await VideoFilePipelineService.run_on_file(
            pipeline_id=pipeline_id,
            file_path=job.input_path,
        )

        job.result = result
        job.status = "done"
        logger.info(f"✅ Worker: job {job_id} completed successfully")

    except Exception as e:
        job.status = "error"
        job.error = str(e)
        logger.error(f"❌ Worker: job {job_id} failed: {e}")

    finally:
        job_repo.save(job)


async def worker_loop() -> None:
    """
    Main worker loop - continuously dequeue and process jobs.

    This runs as a separate process (see run_video_worker.py).
    """
    logger.info("👷 Worker loop started")

    while True:
        job_id = job_repo.dequeue()

        if job_id:
            logger.info(f"📥 Worker: picked up job {job_id}")
            await process_job(job_id)
        else:
            # No jobs in queue, sleep briefly before checking again
            await asyncio.sleep(0.5)
