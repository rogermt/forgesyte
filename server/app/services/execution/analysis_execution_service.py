"""Analysis execution service for API-facing orchestration.

This service:
- API-facing orchestration layer
- Validates high-level request shape (not deep validation)
- Creates job → runs job → returns result/error
- Does NOT call ToolRunner directly

Execution Chain:
    API Endpoint → AnalysisExecutionService → JobExecutionService
                                              ↓
                                    PluginExecutionService
                                              ↓
                                          ToolRunner
"""

import logging
from typing import Any, Dict, Optional, Tuple

from app.models_pydantic import JobStatus

from .job_execution_service import JobExecutionService

logger = logging.getLogger(__name__)


class AnalysisExecutionService:
    """Service for API-facing analysis orchestration.

    Responsibilities:
    - Receive high-level analysis requests from API
    - Validate request shape (not deep validation - that's JobExecutionService's job)
    - Create job via JobExecutionService
    - Run job and return result/error
    - Present results in API-friendly format

    Does NOT:
    - Call ToolRunner directly
    - Handle low-level input/output validation (delegated down)
    - Manage job lifecycle (delegated to JobExecutionService)

    This is the top-level service that API routes interact with.
    """

    def __init__(self, job_execution_service: JobExecutionService):
        """Initialize analysis execution service.

        Args:
            job_execution_service: Service for job lifecycle management
        """
        self._job_execution_service = job_execution_service
        logger.debug("AnalysisExecutionService initialized")

    # -------------------------------------------------------------------------
    # Synchronous execution (for API compatibility)
    # -------------------------------------------------------------------------
    async def analyze(
        self,
        plugin_name: str,
        args: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """Synchronous analysis execution.

        Creates a job, runs it immediately, and returns (result, error).
        This is the asynchronous wrapper that API routes expect.

        Args:
            plugin_name: Name of the plugin to execute
            args: Tool-specific arguments including 'image' and 'mime_type'

        Returns:
            Tuple of (result_dict, error_dict) where error_dict is None on success
        """
        # Extract tool_name from args if present
        # If not provided, pass None to JobExecutionService which handles tool selection
        tool_name: Optional[str] = args.get("tool_name")

        # Create and run job asynchronously without asyncio.run()
        # JobExecutionService validates tool_name against plugin manifest
        job_id = await self._job_execution_service.create_job(
            plugin_name=plugin_name,
            tool_name=tool_name or "",  # type: ignore  # JobExecutionService handles validation
            args=args,
        )
        job_result = await self._job_execution_service.run_job(job_id)

        # Return (result, error) tuple
        if job_result.get("error"):
            error_response: dict[str, Any] = {
                "type": "execution_error",
                "message": job_result["error"],
            }
            return {}, error_response
        result_data: dict[str, Any] = job_result.get("result", {})
        return result_data, None

    async def submit_analysis(
        self,
        plugin_name: str,
        tool_name: str,
        args: Dict[str, Any],
        mime_type: str = "image/png",
    ) -> Dict[str, Any]:
        """Submit an analysis request for execution.

        Creates a job and executes it synchronously, returning the result.

        Args:
            plugin_name: Name of the plugin to execute
            tool_name: Name of the tool to run
            args: Tool-specific arguments
            mime_type: MIME type of the input (default: "image/png")

        Returns:
            Dictionary containing:
                - job_id: Unique job identifier
                - status: Job status (success/error)
                - result: Execution result (if successful)
                - error: Error message (if failed)

        Raises:
            ValueError: If request parameters are invalid
        """
        # Validate high-level request shape
        self._validate_request_shape(plugin_name, tool_name, args)

        logger.info(
            "Analysis request received",
            extra={
                "plugin_name": plugin_name,
                "tool_name": tool_name,
            },
        )

        # Create job
        job_id = await self._job_execution_service.create_job(
            plugin_name=plugin_name,
            tool_name=tool_name,
            args={
                **args,
                "mime_type": mime_type,
            },
        )

        # Run job
        job_result = await self._job_execution_service.run_job(job_id)

        # Format response
        return {
            "job_id": job_id,
            "status": job_result["status"],
            "result": job_result.get("result"),
            "error": job_result.get("error"),
            "created_at": job_result["created_at"],
            "completed_at": job_result["completed_at"],
        }

    async def submit_analysis_async(
        self,
        plugin_name: str,
        tool_name: str,
        args: Dict[str, Any],
        mime_type: str = "image/png",
    ) -> Dict[str, Any]:
        """Submit an analysis request asynchronously.

        Creates a job and returns immediately with job_id.
        Use get_job_result() to poll for results.

        Args:
            plugin_name: Name of the plugin to execute
            tool_name: Name of the tool to run
            args: Tool-specific arguments
            mime_type: MIME type of the input (default: "image/png")

        Returns:
            Dictionary containing:
                - job_id: Unique job identifier for tracking
                - status: Initial job status (pending)
                - created_at: Job creation timestamp
        """
        # Validate high-level request shape
        self._validate_request_shape(plugin_name, tool_name, args)

        logger.info(
            "Async analysis request received",
            extra={
                "plugin_name": plugin_name,
                "tool_name": tool_name,
            },
        )

        # Create job (doesn't start execution yet)
        job_id = await self._job_execution_service.create_job(
            plugin_name=plugin_name,
            tool_name=tool_name,
            args={
                **args,
                "mime_type": mime_type,
            },
        )

        return {
            "job_id": job_id,
            "status": JobStatus.QUEUED.value,
            "created_at": self._job_execution_service._jobs[
                job_id
            ].created_at.isoformat(),
        }

    async def start_job(self, job_id: str) -> Dict[str, Any]:
        """Start execution of a pending job.

        Args:
            job_id: Unique job identifier

        Returns:
            Job dictionary with updated status
        """
        return await self._job_execution_service.run_job(job_id)

    async def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the result of a job.

        Args:
            job_id: Unique job identifier

        Returns:
            Job dictionary with status, result, or error; or None if not found
        """
        return await self._job_execution_service.get_job(job_id)

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
            List of job dictionaries
        """
        return await self._job_execution_service.list_jobs(status=status, limit=limit)

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job.

        Args:
            job_id: Unique job identifier

        Returns:
            True if job was cancelled, False if not possible
        """
        return await self._job_execution_service.cancel_job(job_id)

    def _validate_request_shape(
        self,
        plugin_name: str,
        tool_name: str,
        args: Dict[str, Any],
    ) -> None:
        """Validate high-level request shape.

        Performs basic validation only - not deep validation.
        Deep validation is handled by downstream services.

        Args:
            plugin_name: Name of the plugin
            tool_name: Name of the tool
            args: Tool arguments

        Raises:
            ValueError: If request shape is invalid
        """
        if not plugin_name or not isinstance(plugin_name, str):
            raise ValueError("plugin_name must be a non-empty string")

        if not tool_name or not isinstance(tool_name, str):
            raise ValueError("tool_name must be a non-empty string")

        if not isinstance(args, dict):
            raise ValueError("args must be a dictionary")

        logger.debug(
            "Request shape validated",
            extra={
                "plugin_name": plugin_name,
                "tool_name": tool_name,
            },
        )
