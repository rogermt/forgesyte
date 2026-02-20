"""Job worker for Phase 16 asynchronous processing.

This worker:
1. Dequeues job_ids from the queue
2. Updates job status to RUNNING
3. Executes pipeline on input file (Commit 6)
4. Saves results to storage as JSON
5. Handles errors with graceful failure
6. Handles signals (SIGINT/SIGTERM) for graceful shutdown
"""

import json
import logging
import signal
import time
from io import BytesIO
from typing import List, Optional, Protocol

from ..core.database import SessionLocal
from ..models.job import Job, JobStatus
from ..services.queue.memory_queue import InMemoryQueueService
from .worker_state import worker_last_heartbeat

logger = logging.getLogger(__name__)


class StorageService(Protocol):
    """Protocol for storage service (allows dependency injection)."""

    def load_file(self, path: str):
        """Load file from storage."""
        ...

    def save_file(self, src, dest_path: str) -> str:
        """Save file to storage."""
        ...


class PipelineService(Protocol):
    """Protocol for pipeline service (allows dependency injection)."""

    def run_on_file(
        self,
        mp4_path: str,
        pipeline_id: str,
        tools: List[str],
    ):
        """Execute pipeline on video file."""
        ...


class JobWorker:
    """Processes jobs from the queue."""

    def __init__(
        self,
        queue: Optional[InMemoryQueueService] = None,
        session_factory=None,
        storage: Optional[StorageService] = None,
        pipeline_service: Optional[PipelineService] = None,
    ) -> None:
        """Initialize worker.

        Args:
            queue: Ignored (kept for backward compatibility with tests)
            session_factory: Session factory (defaults to SessionLocal from database.py)
            storage: StorageService instance for file I/O
            pipeline_service: PipelineService instance for pipeline execution
        """
        self._session_factory = session_factory or SessionLocal
        self._storage = storage
        self._pipeline_service = pipeline_service
        self._running = True

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum: int, frame) -> None:
        """Handle shutdown signals gracefully.

        Args:
            signum: Signal number (SIGINT, SIGTERM)
            frame: Signal frame
        """
        logger.info("Received signal %s, shutting down gracefully", signum)
        self._running = False

    def run_once(self) -> bool:
        """Process one job from the database.

        Returns:
            True if a job was processed, False if no pending jobs
        """
        db = self._session_factory()
        try:
            job = (
                db.query(Job)
                .filter(Job.status == JobStatus.pending)
                .order_by(Job.created_at.asc())
                .first()
            )

            if job is None:
                return False

            rows_updated = (
                db.query(Job)
                .filter(Job.job_id == job.job_id)
                .filter(Job.status == JobStatus.pending)
                .update({"status": JobStatus.running})
            )
            db.commit()

            if rows_updated == 0:
                return False

            db.refresh(job)

            logger.info("Job %s marked RUNNING", job.job_id)

            # COMMIT 6: Execute pipeline on input file
            return self._execute_pipeline(job, db)
        finally:
            db.close()

    def _execute_pipeline(self, job: Job, db) -> bool:
        """Execute pipeline on job input file.

        Args:
            job: Job model instance
            db: Database session

        Returns:
            True if pipeline executed successfully, False on error
        """
        try:
            # Verify storage and pipeline services are available
            if not self._storage or not self._pipeline_service:
                logger.warning(
                    "Job %s: storage or pipeline service not available", job.job_id
                )
                job.status = JobStatus.failed
                job.error_message = "Pipeline execution services not configured"
                db.commit()
                return False

            # Load input file from storage
            input_file_path = self._storage.load_file(job.input_path)
            logger.info("Job %s: loaded input file %s", job.job_id, input_file_path)

            # Execute pipeline on video file
            results = self._pipeline_service.run_on_file(
                str(input_file_path),
                job.pipeline_id,
                json.loads(job.tools) if job.tools else [],
            )
            logger.info(
                "Job %s: pipeline executed, %d results", job.job_id, len(results)
            )

            # Prepare JSON output
            output_data = {"results": results}
            output_json = json.dumps(output_data)
            output_bytes = BytesIO(output_json.encode())

            # Save results to storage
            output_path = self._storage.save_file(
                output_bytes,
                f"output/{job.job_id}.json",
            )
            logger.info("Job %s: saved results to %s", job.job_id, output_path)

            # Mark job as completed
            job.status = JobStatus.completed
            job.output_path = output_path
            job.error_message = None
            db.commit()

            logger.info("Job %s marked COMPLETED", job.job_id)
            return True

        except Exception as e:
            # Mark job as failed with error message
            logger.error("Job %s: pipeline execution failed: %s", job.job_id, str(e))
            job.status = JobStatus.failed
            job.error_message = str(e)
            db.commit()
            return False

    def run_forever(self) -> None:
        """Run the worker loop until shutdown signal is received."""
        logger.info("Worker started")
        while self._running:
            # Send heartbeat to indicate worker is alive
            worker_last_heartbeat.beat()

            processed = self.run_once()
            if not processed:
                time.sleep(0.5)
        logger.info("Worker stopped")
