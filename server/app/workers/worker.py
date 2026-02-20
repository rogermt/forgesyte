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
import threading
import time
from io import BytesIO
from typing import Any, Dict, List, Optional, Protocol

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
        plugin_service=None,
    ) -> None:
        """Initialize worker.

        Args:
            queue: Ignored (kept for backward compatibility with tests)
            session_factory: Session factory (defaults to SessionLocal from database.py)
            storage: StorageService instance for file I/O
            plugin_service: PluginManagementService instance for plugin execution
        """
        self._session_factory = session_factory or SessionLocal
        self._storage = storage
        self._plugin_service = plugin_service
        self._running = True

        # Register signal handlers only if running in main thread
        if threading.current_thread() is threading.main_thread():
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
            # Verify storage and plugin_service are available
            if not self._storage:
                logger.warning("Job %s: storage service not available", job.job_id)
                job.status = JobStatus.failed
                job.error_message = "Storage service not configured"
                db.commit()
                return False

            # Use injected plugin_service or create default
            if self._plugin_service:
                plugin_service = self._plugin_service
            else:
                from ..plugin_loader import PluginRegistry
                from ..services.plugin_management_service import PluginManagementService

                plugin_manager = PluginRegistry()
                plugin_service = PluginManagementService(plugin_manager)

            manifest = plugin_service.get_plugin_manifest(job.plugin_id)
            if not manifest:
                job.status = JobStatus.failed
                job.error_message = f"Plugin '{job.plugin_id}' not found"
                db.commit()
                return False

            # Find tool definition in manifest (support both list and dict formats)
            tools = manifest.get("tools", [])
            tool_def = None

            # Handle list format (Phase 12+)
            if isinstance(tools, list):
                for tool in tools:
                    if tool.get("id") == job.tool:
                        tool_def = tool
                        break
            # Handle dict format (legacy)
            elif isinstance(tools, dict):
                for tool_name, tool_info in tools.items():
                    if tool_name == job.tool:
                        tool_def = tool_info
                        tool_def["id"] = tool_name
                        break

            if not tool_def:
                job.status = JobStatus.failed
                job.error_message = (
                    f"Tool '{job.tool}' not found in plugin '{job.plugin_id}'"
                )
                db.commit()
                return False

            # Validate tool supports job_type
            # inputs can be a list (legacy canonicalized) or dict (new format with parameter names)
            tool_inputs = tool_def.get("inputs", [])
            input_type_list = []

            if isinstance(tool_inputs, list):
                # Legacy format: ["image_bytes", "video_path"]
                input_type_list = tool_inputs
            elif isinstance(tool_inputs, dict):
                # New format: {"image_base64": "string", "video_path": "string"}
                input_type_list = list(tool_inputs.keys())

            if job.job_type == "video":
                if not any(i in input_type_list for i in ("video", "video_path")):
                    job.status = JobStatus.failed
                    job.error_message = (
                        f"Tool '{job.tool}' does not support video input"
                    )
                    db.commit()
                    return False
            elif job.job_type == "image":
                if not any(
                    i in input_type_list for i in ("image_bytes", "image_base64")
                ):
                    job.status = JobStatus.failed
                    job.error_message = (
                        f"Tool '{job.tool}' does not support image input"
                    )
                    db.commit()
                    return False
            else:
                job.status = JobStatus.failed
                job.error_message = f"Unknown job_type: {job.job_type}"
                db.commit()
                return False

            # Branch by job_type to prepare arguments
            args: Dict[str, Any] = {}

            if job.job_type == "video":
                # Load video file from storage
                video_path = self._storage.load_file(job.input_path)
                args = {"video_path": str(video_path)}
                logger.info("Job %s: loaded video file %s", job.job_id, video_path)
            elif job.job_type == "image":
                # Load image file from storage
                image_path = self._storage.load_file(job.input_path)
                with open(image_path, "rb") as f:
                    image_bytes = f.read()

                # Determine parameter name from manifest
                # Use image_base64 if manifest specifies it, otherwise fall back to image_bytes
                if "image_base64" in input_type_list:
                    import base64

                    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                    args = {"image_base64": image_base64}
                    # Add default values for optional parameters if not specified
                    if "language" in input_type_list:
                        args["language"] = "eng"
                    if "psm" in input_type_list:
                        args["psm"] = 6
                else:
                    args = {"image_bytes": image_bytes}
                logger.info("Job %s: loaded image file %s", job.job_id, image_path)
            else:
                # Should never reach here due to validation above
                job.status = JobStatus.failed
                job.error_message = f"Unknown job_type: {job.job_type}"
                db.commit()
                return False

            # Execute tool via plugin_service (includes sandbox and error handling)
            result = plugin_service.run_plugin_tool(job.plugin_id, job.tool, args)
            logger.info("Job %s: tool executed successfully", job.job_id)

            # Prepare JSON output with unified storage path
            output_data = {"results": result}
            output_json = json.dumps(output_data)
            output_bytes = BytesIO(output_json.encode())

            # Save results to storage with job_type subdirectory
            output_path = self._storage.save_file(
                output_bytes,
                f"{job.job_type}/output/{job.job_id}.json",
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
