"""Job execution service for managing job lifecycle transitions.

This service:
- Manages job lifecycle: PENDING → RUNNING → SUCCESS/FAILED
- Stores job result/error
- Delegates execution to PluginExecutionService
- No persistence beyond in-memory (Phase 12 requirement)

Execution Chain:
    AnalysisExecutionService → JobExecutionService → PluginExecutionService
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.models import JobStatus

from .plugin_execution_service import PluginExecutionService

logger = logging.getLogger(__name__)


@dataclass
class Job:
    """Job data structure for in-memory storage.

    Attributes:
        job_id: Unique job identifier
        plugin_name: Name of the plugin to execute
        tool_name: Name of the tool to run
        args: Tool-specific arguments
        status: Current job status
        result: Job result (populated on success)
        error: Error message (populated on failure)
        created_at: Job creation timestamp
        started_at: Job start timestamp
        completed_at: Job completion timestamp
    """

    job_id: str
    plugin_name: str
    tool_name: str
    args: Dict[str, Any]
    status: JobStatus = JobStatus.QUEUED
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobExecutionService:
    """Service for managing job lifecycle and execution.

    Responsibilities:
    - Create and track jobs
    - Manage lifecycle transitions: PENDING → RUNNING → SUCCESS/FAILED
    - Store job results and errors
    - Delegate execution to PluginExecutionService
    - In-memory storage only (Phase 12 requirement)

    Does NOT:
    - Call ToolRunner directly (delegates to PluginExecutionService)
    - Handle API-level validation (handled by AnalysisExecutionService)
    """

    def __init__(self, plugin_execution_service: PluginExecutionService):
        """Initialize job execution service.

        Args:
            plugin_execution_service: Service for executing plugin tools
        """
        self._plugin_execution_service = plugin_execution_service
        self._jobs: Dict[str, Job] = {}
        self._lock = asyncio.Lock()
        logger.debug("JobExecutionService initialized")

    async def create_job(
        self,
        plugin_name: str,
        tool_name: str,
        args: Dict[str, Any],
    ) -> str:
        """Create a new job in PENDING status.

        Args:
            plugin_name: Name of the plugin to execute
            tool_name: Name of the tool to run
            args: Tool-specific arguments

        Returns:
            Job ID for tracking the job
        """
        job_id = str(uuid.uuid4())

        job = Job(
            job_id=job_id,
            plugin_name=plugin_name,
            tool_name=tool_name,
            args=args,
        )

        async with self._lock:
            self._jobs[job_id] = job

        logger.info(
            "Job created",
            extra={
                "job_id": job_id,
                "plugin_name": plugin_name,
                "tool_name": tool_name,
            },
        )

        return job_id

    async def run_job(self, job_id: str) -> Dict[str, Any]:
        """Execute a pending job.

        Transitions job from QUEUED → RUNNING → SUCCESS/FAILED.
        Delegates actual execution to PluginExecutionService.

        Args:
            job_id: Unique job identifier

        Returns:
            Job dictionary with status, result, or error

        Raises:
            JobNotFoundError: If job doesn't exist
            JobStateError: If job is not in QUEUED status
        """
        async with self._lock:
            if job_id not in self._jobs:
                raise ValueError(f"Job '{job_id}' not found")

            job = self._jobs[job_id]

            if job.status != JobStatus.QUEUED:
                raise ValueError(
                    f"Job '{job_id}' is not queued (current: {job.status})"
                )

            # Transition to RUNNING
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)

        logger.info(
            "Job started",
            extra={
                "job_id": job_id,
                "plugin_name": job.plugin_name,
                "tool_name": job.tool_name,
            },
        )

        start_time = time.perf_counter()

        try:
            # Delegate to PluginExecutionService
            result = await self._plugin_execution_service.execute_tool(
                tool_name=job.tool_name,
                args=job.args,
            )

            processing_time_ms = (time.perf_counter() - start_time) * 1000

            # Transition to SUCCESS
            async with self._lock:
                job.status = JobStatus.DONE
                job.result = {
                    **result,
                    "processing_time_ms": processing_time_ms,
                }
                job.completed_at = datetime.now(timezone.utc)

            logger.info(
                "Job completed successfully",
                extra={
                    "job_id": job_id,
                    "processing_time_ms": processing_time_ms,
                },
            )

            return self._job_to_dict(job)

        except Exception as e:
            processing_time_ms = (time.perf_counter() - start_time) * 1000

            # Transition to FAILED
            async with self._lock:
                job.status = JobStatus.ERROR
                job.error = str(e)
                job.completed_at = datetime.now(timezone.utc)

            logger.error(
                "Job failed",
                extra={
                    "job_id": job_id,
                    "error": str(e),
                    "processing_time_ms": processing_time_ms,
                },
            )

            return self._job_to_dict(job)

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID.

        Args:
            job_id: Unique job identifier

        Returns:
            Job dictionary or None if not found
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            return self._job_to_dict(job)

    async def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 50,
    ) -> list[Dict[str, Any]]:
        """List jobs with optional filtering.

        Args:
            status: Filter by job status (optional)
            limit: Maximum number of jobs to return (default 50)

        Returns:
            List of job dictionaries, sorted by created_at (newest first)
        """
        async with self._lock:
            jobs = list(self._jobs.values())

        if status:
            jobs = [j for j in jobs if j.status == status]

        # Sort by created_at descending (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        return [self._job_to_dict(j) for j in jobs[:limit]]

    def _job_to_dict(self, job: Job) -> Dict[str, Any]:
        """Convert Job dataclass to dictionary.

        Args:
            job: Job instance

        Returns:
            Dictionary representation of the job
        """
        return {
            "job_id": job.job_id,
            "plugin_name": job.plugin_name,
            "tool_name": job.tool_name,
            "status": job.status.value,
            "result": job.result,
            "error": job.error,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued job (best effort).

        Can only cancel jobs that haven't started processing yet.
        Running or completed jobs cannot be cancelled.

        Args:
            job_id: Unique job identifier

        Returns:
            True if job was cancelled, False if not possible
        """
        async with self._lock:
            if job_id not in self._jobs:
                return False

            job = self._jobs[job_id]

            if job.status != JobStatus.QUEUED:
                return False

            job.status = JobStatus.ERROR
            job.error = "Cancelled by user"
            job.completed_at = datetime.now(timezone.utc)

        logger.info("Job cancelled", extra={"job_id": job_id})
        return True
