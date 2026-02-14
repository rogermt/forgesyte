"""Job worker for Phase 16 asynchronous processing.

This worker:
1. Dequeues job_ids from the queue
2. Updates job status to RUNNING
3. Yields control to pipeline execution (Commit 6)
4. Handles signals (SIGINT/SIGTERM) for graceful shutdown
"""

import logging
import signal
import time
from typing import Optional

from app.core.database import SessionLocal
from app.models.job import Job, JobStatus
from app.services.queue.memory_queue import InMemoryQueueService

logger = logging.getLogger(__name__)


class JobWorker:
    """Processes jobs from the queue."""

    def __init__(
        self,
        queue: Optional[InMemoryQueueService] = None,
        session_factory=None,
    ) -> None:
        """Initialize worker with queue service.

        Args:
            queue: QueueService instance (defaults to InMemoryQueueService)
            session_factory: Session factory (defaults to SessionLocal from database.py)
        """
        self._queue = queue or InMemoryQueueService()
        self._session_factory = session_factory or SessionLocal
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
        """Process one job from the queue.

        Returns:
            True if a job was processed, False if queue was empty
        """
        job_id = self._queue.dequeue()
        if job_id is None:
            return False

        db = self._session_factory()
        try:
            job = db.query(Job).filter(Job.job_id == job_id).first()

            if job is None:
                logger.warning("Dequeued job %s but no DB record found", job_id)
                return False

            job.status = JobStatus.running
            db.commit()

            logger.info("Job %s marked RUNNING", job_id)
            return True
        finally:
            db.close()

    def run_forever(self) -> None:
        """Run the worker loop until shutdown signal is received."""
        logger.info("Worker started")
        while self._running:
            processed = self.run_once()
            if not processed:
                time.sleep(0.5)
        logger.info("Worker stopped")
