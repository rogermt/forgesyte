"""Background task management and job processing.

This module provides asynchronous job processing with resilience patterns
and structured logging. It uses a service layer pattern with Protocol-based
abstractions for testing and flexibility.

The TaskProcessor orchestrates image analysis tasks in the background,
updating job status and handling errors with proper logging.
"""

import asyncio
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from .exceptions import PluginExecutionError
from .models import JobStatus
from .plugin_loader import PluginRegistry
from .protocols import JobStore as JobStoreProtocol
from .schemas.normalisation import normalise_output

# Configure logging
logger = logging.getLogger(__name__)


class JobStore:
    """In-memory job storage with thread-safe operations.

    Stores job records in memory with automatic cleanup of old completed jobs
    when maximum capacity is reached. For production use, consider replacing
    with Redis or database-backed implementation.

    Attributes:
        _jobs: Dictionary mapping job_id to job record
        _max_jobs: Maximum number of jobs to store before cleanup
        _lock: AsyncIO lock for thread-safe operations

    Notes:
        Uses asyncio.Lock for thread safety in concurrent scenarios.
        Cleanup removes oldest 20% of completed/failed jobs when at capacity.
    """

    def __init__(self, max_jobs: int = 1000):
        """Initialize job store.

        Args:
            max_jobs: Maximum number of jobs to retain (default 1000)

        Raises:
            None
        """
        self._jobs: dict[str, dict[str, Any]] = {}
        self._max_jobs = max_jobs
        self._lock = asyncio.Lock()
        logger.debug("JobStore initialized", extra={"max_jobs": max_jobs})

    async def create(self, job_id: str, job_data: dict[str, Any]) -> None:
        """Create a new job entry.

        Args:
            job_id: Unique identifier for the job
            job_data: Job data dictionary with initial state

        Raises:
            RuntimeError: If job already exists or storage fails

        Notes:
            Automatically cleanup old jobs if at capacity.
        """
        async with self._lock:
            if job_id in self._jobs:
                raise RuntimeError(f"Job {job_id} already exists")

            # Cleanup old jobs if at capacity
            if len(self._jobs) >= self._max_jobs:
                await self._cleanup_old_jobs()

            self._jobs[job_id] = job_data
            logger.debug(
                "Job created",
                extra={"job_id": job_id, "plugin": job_data.get("plugin")},
            )

    async def update(
        self, job_id: str, updates: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Update a job's status and fields.

        Args:
            job_id: Unique identifier for the job
            updates: Dictionary of fields to update (status, result, error, progress)

        Returns:
            Updated job dictionary, or None if job not found

        Raises:
            RuntimeError: If update fails

        Notes:
            Logs update operations with changed fields for debugging.
        """
        async with self._lock:
            if job_id not in self._jobs:
                logger.warning("Cannot update: job not found", extra={"job_id": job_id})
                return None

            self._jobs[job_id].update(updates)
            logger.debug(
                "Job updated",
                extra={"job_id": job_id, "fields": list(updates.keys())},
            )
            return self._jobs[job_id]

    async def get(self, job_id: str) -> Optional[dict[str, Any]]:
        """Get a job by ID.

        Args:
            job_id: Unique identifier for the job

        Returns:
            Job dictionary or None if not found

        Raises:
            None
        """
        return self._jobs.get(job_id)

    async def list_jobs(
        self,
        status: Optional[str] = None,
        plugin: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List jobs with optional filtering.

        Args:
            status: Filter by job status (optional)
            plugin: Filter by plugin name (optional)
            limit: Maximum number of jobs to return (default 50)

        Returns:
            List of job dictionaries, sorted by created_at (newest first)

        Raises:
            None
        """
        jobs = list(self._jobs.values())

        if status:
            jobs = [j for j in jobs if j.get("status") == status]
        if plugin:
            jobs = [j for j in jobs if j.get("plugin") == plugin]

        # Sort by created_at descending (newest first)
        jobs.sort(
            key=lambda j: j.get("created_at", datetime.now(timezone.utc)), reverse=True
        )
        result = jobs[:limit]
        logger.debug(
            "Listed jobs",
            extra={
                "count": len(result),
                "total": len(self._jobs),
                "status_filter": status,
                "plugin_filter": plugin,
            },
        )
        return result

    async def _cleanup_old_jobs(self) -> None:
        """Remove oldest completed jobs when at capacity.

        Removes oldest 20% of completed or failed jobs to maintain
        memory efficiency.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        # Find completed or failed jobs
        completed = [
            (k, v)
            for k, v in self._jobs.items()
            if v.get("status") in (JobStatus.DONE, JobStatus.ERROR)
        ]

        if not completed:
            logger.debug("No completed jobs to clean up")
            return

        # Sort by created_at ascending (oldest first)
        completed.sort(key=lambda x: x[1].get("created_at", datetime.now(timezone.utc)))

        # Remove oldest 20%
        remove_count = max(1, len(completed) // 5)
        removed_ids = []
        for job_id, _ in completed[:remove_count]:
            del self._jobs[job_id]
            removed_ids.append(job_id)

        logger.info(
            "Cleaned up old jobs",
            extra={"removed_count": remove_count, "total_jobs": len(self._jobs)},
        )


class TaskProcessor:
    """Orchestrates asynchronous image analysis task processing.

    Manages the lifecycle of background analysis jobs using a thread pool
    for CPU-intensive plugin operations. Provides job submission, status
    tracking, and result retrieval with structured logging throughout.

    Uses callback pattern for completion notifications and maintains
    thread safety with asyncio.Lock in the underlying JobStore.

    Attributes:
        plugin_manager: PluginRegistry for accessing available plugins
        job_store: JobStore for persisting job records
        _executor: ThreadPoolExecutor for CPU-intensive work
        _callbacks: Dictionary mapping job_id to completion callbacks

    Notes:
        ThreadPoolExecutor runs plugin.run_tool() in thread pool to avoid
        blocking the event loop for CPU-intensive operations.
    """

    def __init__(
        self,
        plugin_manager: PluginRegistry,
        job_store: JobStoreProtocol,
        max_workers: int = 4,
        device_tracker=None,
    ):
        """Initialize task processor.

        Args:
            plugin_manager: PluginRegistry implementation for plugin access
            job_store: JobStore implementation for job persistence
            max_workers: Number of threads in executor pool (default 4)
            device_tracker: Optional DeviceTracker for logging device usage

        Raises:
            None
        """
        self.plugin_manager = plugin_manager
        self.job_store = job_store
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._callbacks: dict[str, Callable[[dict[str, Any]], Any]] = {}
        self.device_tracker = device_tracker
        logger.debug("TaskProcessor initialized", extra={"max_workers": max_workers})

    async def submit_job(
        self,
        image_bytes: bytes,
        plugin_name: str,
        options: Optional[dict[str, Any]] = None,
        device: str = "cpu",
        callback: Optional[Callable[[dict[str, Any]], Any]] = None,
    ) -> str:
        """Submit a new image analysis job.

        Creates a job record and dispatches it for asynchronous processing
        in the background. Returns immediately with the job_id.

        Args:
            image_bytes: Raw image data (PNG, JPEG, etc.)
            plugin_name: Name of the analysis plugin to use
            options: Plugin-specific analysis options (optional)
            device: Device preference ("cpu" or "gpu", default "cpu")
            callback: Callable invoked when job completes (optional)

        Returns:
            Job ID for status tracking and result retrieval

        Raises:
            ValueError: If image_bytes is empty or plugin_name is missing
        """
        if not image_bytes:
            logger.warning("Submitted job with empty image data")
            raise ValueError("image_bytes cannot be empty")

        if not plugin_name:
            logger.warning("Submitted job without plugin name")
            raise ValueError("plugin_name is required")

        job_id = str(uuid.uuid4())

        # Create job record
        job_data: dict[str, Any] = {
            "job_id": job_id,
            "status": JobStatus.QUEUED,
            "result": None,
            "error": None,
            "created_at": datetime.now(timezone.utc),
            "completed_at": None,
            "plugin": plugin_name,
            "device_requested": device.lower(),
            "progress": 0.0,
        }
        await self.job_store.create(job_id, job_data)

        if callback:
            self._callbacks[job_id] = callback

        # Dispatch background task without blocking
        asyncio.create_task(
            self._process_job(job_id, image_bytes, plugin_name, options or {}, device)
        )

        logger.info(
            "Job submitted",
            extra={
                "job_id": job_id,
                "plugin": plugin_name,
                "device_requested": device.lower(),
                "has_callback": callback is not None,
            },
        )
        return job_id

    async def _process_job(
        self,
        job_id: str,
        image_bytes: bytes,
        plugin_name: str,
        options: dict[str, Any],
        device: str = "cpu",
    ) -> None:
        """Process a job asynchronously.

        Runs the actual analysis in a thread pool, updates job status,
        handles errors, and invokes completion callbacks.

        Args:
            job_id: Unique job identifier
            image_bytes: Raw image data to analyze
            plugin_name: Name of the plugin to run
            options: Plugin-specific options
            device: Device preference ("cpu" or "gpu")

        Returns:
            None

        Raises:
            None (catches all exceptions and logs them)
        """
        await self.job_store.update(
            job_id, {"status": JobStatus.RUNNING, "progress": 0.1}
        )

        logger.debug(
            "Job processing started",
            extra={"job_id": job_id, "plugin": plugin_name, "device_requested": device},
        )

        # Get plugin
        plugin = self.plugin_manager.get(plugin_name)
        if not plugin:
            error_msg = f"Plugin '{plugin_name}' not found"
            logger.warning(
                "Plugin not found",
                extra={"job_id": job_id, "plugin": plugin_name},
            )
            await self.job_store.update(
                job_id,
                {"status": JobStatus.ERROR, "error": error_msg},
            )
            await self._notify_callback(job_id)
            return

        try:
            # Time the analysis
            start_time = time.perf_counter()
            loop = asyncio.get_event_loop()

            # Run CPU-intensive work in thread pool
            # Use default tool if not specified
            tool_name = options.get("tool", "default")
            tool_args = {
                "image_bytes": image_bytes,
                "options": {k: v for k, v in options.items() if k != "tool"},
            }
            result = await loop.run_in_executor(
                self._executor, plugin.run_tool, tool_name, tool_args
            )

            processing_time_ms = (time.perf_counter() - start_time) * 1000

            # Update with successful result
            # Handle both dict and Pydantic model returns from plugins
            result_dict = (
                result.model_dump() if hasattr(result, "model_dump") else result
            )

            # Normalise plugin output to canonical schema
            try:
                normalised_result = normalise_output(result_dict)
            except ValueError as e:
                logger.warning(
                    "Plugin output normalisation failed",
                    extra={"job_id": job_id, "plugin": plugin_name, "error": str(e)},
                )
                # For now, continue with raw result if normalisation fails
                # (This allows graceful degradation during rollout)
                normalised_result = result_dict

            # For now, device_used = device_requested (no actual fallback logic yet)
            # In future, plugin execution will determine actual device used
            job_data = await self.job_store.get(job_id)
            device_requested = (
                job_data.get("device_requested", "cpu") if job_data else "cpu"
            )
            device_used = device_requested  # Placeholder for now

            await self.job_store.update(
                job_id,
                {
                    "status": JobStatus.DONE,
                    "result": {
                        **normalised_result,
                        "processing_time_ms": processing_time_ms,
                    },
                    "completed_at": datetime.now(timezone.utc),
                    "progress": 1.0,
                    "device_used": device_used,
                },
            )

            # Log device usage to observability table
            if self.device_tracker:
                try:
                    await self.device_tracker.log_device_usage(
                        job_id=job_id,
                        device_requested=device_requested,
                        device_used=device_used,
                    )
                except Exception as e:
                    logger.warning(
                        "Device usage logging failed (continuing)",
                        extra={"job_id": job_id, "error": str(e)},
                    )

            logger.info(
                "Job completed successfully",
                extra={
                    "job_id": job_id,
                    "processing_time_ms": processing_time_ms,
                    "device_requested": device_requested,
                    "device_used": device_used,
                },
            )

        except PluginExecutionError as e:
            logger.error(
                "Plugin execution failed",
                extra={"job_id": job_id, "plugin": plugin_name, "error": str(e)},
            )
            await self.job_store.update(
                job_id,
                {
                    "status": JobStatus.ERROR,
                    "error": str(e),
                    "completed_at": datetime.now(timezone.utc),
                },
            )

        except Exception as e:
            logger.exception(
                "Job failed with exception",
                extra={"job_id": job_id, "error": str(e)},
            )
            await self.job_store.update(
                job_id,
                {
                    "status": JobStatus.ERROR,
                    "error": f"Unexpected error: {str(e)}",
                    "completed_at": datetime.now(timezone.utc),
                },
            )

        finally:
            await self._notify_callback(job_id)

    async def _notify_callback(self, job_id: str) -> None:
        """Notify callback if registered for job completion.

        Invokes the callback function with the final job state.
        Handles both sync and async callbacks.

        Args:
            job_id: Unique job identifier

        Returns:
            None

        Raises:
            None (catches exceptions from callbacks and logs them)
        """
        if job_id not in self._callbacks:
            return

        callback = self._callbacks.pop(job_id)
        job = await self.job_store.get(job_id)

        try:
            if job and asyncio.iscoroutinefunction(callback):
                await callback(job)
            elif job:
                callback(job)
            logger.debug("Callback executed successfully", extra={"job_id": job_id})
        except Exception as e:
            logger.error(
                "Callback execution failed",
                extra={"job_id": job_id, "error": str(e)},
            )

    async def get_result(self, job_id: str) -> Optional[dict[str, Any]]:
        """Get the final result for a completed job.

        Args:
            job_id: Unique job identifier

        Returns:
            Job result dictionary if job completed, None if not found

        Raises:
            RuntimeError: If job has not completed yet
        """
        job = await self.job_store.get(job_id)
        if not job:
            return None
        if job.get("status") != JobStatus.DONE:
            raise RuntimeError(
                f"Job {job_id} has not completed (status: {job.get('status')})"
            )
        return job.get("result")

    async def get_job(self, job_id: str) -> Optional[dict[str, Any]]:
        """Get job status and results.

        Args:
            job_id: Unique job identifier

        Returns:
            Job dictionary or None if not found

        Raises:
            None
        """
        return await self.job_store.get(job_id)

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued job (best effort).

        Can only cancel jobs that haven't started processing yet.
        Running or completed jobs cannot be cancelled.

        Args:
            job_id: Unique job identifier

        Returns:
            True if job was cancelled, False if not possible

        Raises:
            None
        """
        job = await self.job_store.get(job_id)
        if not job:
            logger.warning("Cannot cancel: job not found", extra={"job_id": job_id})
            return False

        if job.get("status") != JobStatus.QUEUED:
            logger.info(
                "Cannot cancel: job not queued",
                extra={"job_id": job_id, "status": job.get("status")},
            )
            return False

        await self.job_store.update(
            job_id,
            {
                "status": JobStatus.ERROR,
                "error": "Cancelled by user",
                "completed_at": datetime.now(timezone.utc),
            },
        )

        logger.info("Job cancelled", extra={"job_id": job_id})
        return True


# Global instances
job_store = JobStore()
task_processor: Optional[TaskProcessor] = None


def init_task_processor(plugin_manager: PluginRegistry) -> TaskProcessor:
    """Initialize the module-level task processor.

    Called during application startup to set up the global task processor.

    Args:
        plugin_manager: PluginRegistry instance for plugin access

    Returns:
        TaskProcessor instance

    Raises:
        None
    """
    global task_processor
    task_processor = TaskProcessor(plugin_manager, job_store)
    logger.info("Task processor initialized")
    return task_processor
