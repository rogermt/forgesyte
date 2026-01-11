"""Job management service for querying and controlling analysis jobs.

This service provides an abstraction layer for job persistence and task control:
- Retrieve job status and results
- List jobs with optional filtering
- Cancel queued or processing jobs

The service depends on JobStore and TaskProcessor protocols, enabling
testability through mock implementations and supporting different backends.

Example:
    from .job_management_service import JobManagementService
    from ..models import JobStatus

    service = JobManagementService(job_store, task_processor)
    job = await service.get_job_status("job-123")
    jobs = await service.list_jobs(status=JobStatus.COMPLETED, limit=50)
    cancelled = await service.cancel_job("job-456")
"""

import logging
from typing import Any, Dict, Iterable, Optional

from ..models import JobStatus
from ..protocols import JobStore, TaskProcessor

logger = logging.getLogger(__name__)


class JobManagementService:
    """Service for managing analysis job lifecycle.

    Responsible for:
    - Retrieving job status and results
    - Listing jobs with optional filtering
    - Canceling queued/processing jobs

    Depends on Protocols for flexibility:
    - JobStore: Abstracts job data persistence
    - TaskProcessor: Abstracts job cancellation logic
    """

    def __init__(self, store: JobStore, processor: TaskProcessor) -> None:
        """Initialize job management service with dependencies.

        Args:
            store: Job store implementing JobStore protocol
            processor: Task processor implementing TaskProcessor protocol

        Raises:
            TypeError: If dependencies don't have required methods
        """
        self.store = store
        self.processor = processor
        logger.debug("JobManagementService initialized")

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve status and results of a specific job.

        Queries the job store for complete job information including:
        - Current status (queued, processing, completed, failed, cancelled)
        - Job metadata (creation time, plugin, options)
        - Results (if available)
        - Error information (if job failed)

        Args:
            job_id: Unique job identifier

        Returns:
            Job data dictionary if found, None if not found
            Contains: job_id, status, plugin, created_at, results, error, etc.

        Raises:
            RuntimeError: If job store is unavailable
        """
        try:
            job = await self.store.get(job_id)
            if job:
                logger.debug(
                    "Retrieved job status",
                    extra={"job_id": job_id, "status": job.get("status")},
                )
            else:
                logger.debug("Job not found", extra={"job_id": job_id})
            return job
        except Exception as e:
            logger.exception(
                "Failed to retrieve job status",
                extra={"job_id": job_id, "error": str(e)},
            )
            raise

    async def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        plugin: Optional[str] = None,
        limit: int = 50,
    ) -> Iterable[Dict[str, Any]]:
        """List recent jobs with optional filtering.

        Queries the job store for multiple jobs with optional filters:
        - By status (queued, processing, completed, failed, cancelled)
        - By plugin name
        - Limited to N most recent (newest first)

        Args:
            status: Filter by job status (optional)
            plugin: Filter by plugin name (optional)
            limit: Maximum number of jobs to return (default: 50)

        Returns:
            Iterable of job data dictionaries, newest first
            Each dict contains: job_id, status, plugin, created_at, etc.

        Raises:
            RuntimeError: If job store is unavailable
            ValueError: If limit is invalid
        """
        if limit < 1 or limit > 200:
            raise ValueError("limit must be between 1 and 200")

        try:
            jobs = await self.store.list_jobs(status=status, plugin=plugin, limit=limit)
            logger.debug(
                "Listed jobs",
                extra={
                    "count": len(list(jobs)) if hasattr(jobs, "__len__") else "unknown",
                    "status": status,
                    "plugin": plugin,
                    "limit": limit,
                },
            )
            return jobs
        except Exception as e:
            logger.exception(
                "Failed to list jobs",
                extra={"status": status, "plugin": plugin, "error": str(e)},
            )
            raise

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued or processing job.

        Attempts to cancel a job if it's in a cancellable state:
        - Queued: Cancel immediately
        - Processing: Request cancellation (may not succeed)
        - Completed/Failed/Cancelled: Cannot cancel

        Args:
            job_id: Unique job identifier

        Returns:
            True if cancellation succeeded, False if job cannot be cancelled
            (already running, completed, or in terminal state)

        Raises:
            RuntimeError: If task processor is unavailable
        """
        try:
            success = await self.processor.cancel_job(job_id)
            if success:
                logger.info("Job cancelled successfully", extra={"job_id": job_id})
            else:
                logger.warning(
                    "Job cannot be cancelled",
                    extra={"job_id": job_id, "reason": "not in cancellable state"},
                )
            return success
        except Exception as e:
            logger.exception(
                "Failed to cancel job",
                extra={"job_id": job_id, "error": str(e)},
            )
            raise
