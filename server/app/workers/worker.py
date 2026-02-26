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

    @staticmethod
    def _get_total_frames(video_path: str) -> int:
        """Get total frame count from video metadata using OpenCV.

        Uses cv2.VideoCapture to read frame count from video header.
        This is fast (metadata-only, no decoding).

        Args:
            video_path: Path to video file

        Returns:
            Total frame count, or 100 as fallback heuristic if OpenCV fails
        """
        try:
            import cv2

            cap = cv2.VideoCapture(video_path)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            return total if total > 0 else 100
        except Exception:
            return 100  # Fallback heuristic

    def _update_job_progress(
        self,
        job_id: str,
        current_frame: int,
        total_frames: int,
        db,
        tool_index: int = 0,
        total_tools: int = 1,
        tool_name: str = "",
    ) -> None:
        """Update job progress in database, throttled to every 5%.

        v0.9.7: Supports unified progress tracking for multi-tool video jobs.
        v0.10.0: Also broadcasts progress via WebSocket for real-time updates.

        For single-tool jobs:
        - Updates progress based on current_frame / total_frames

        For multi-tool jobs:
        - Equal weighting per tool: tool_weight = 100 / total_tools
        - Global progress = (completed_tools * tool_weight) + (frame_progress * tool_weight)

        Throttles DB updates to reduce database write volume:
        - Updates on first frame (1%)
        - Updates on every 5% boundary
        - Always updates on last frame (100%)

        WebSocket broadcasts happen on every call for real-time updates.

        Args:
            job_id: Job UUID string
            current_frame: Current frame being processed (1-indexed)
            total_frames: Total frames in video
            db: Database session
            tool_index: v0.9.7: Current tool index (0-based)
            total_tools: v0.9.7: Total number of tools
            tool_name: v0.9.7: Current tool name
        """
        if total_frames <= 0:
            logger.warning("Progress update skipped: total_frames <= 0")
            return

        # v0.9.7: Calculate unified progress for multi-tool
        if total_tools > 1:
            tool_weight = 100 / total_tools
            frame_percent = (current_frame / total_frames) * 100
            global_progress = (tool_index * tool_weight) + (
                frame_percent * tool_weight / 100
            )
            percent = int(global_progress)
        else:
            # Single-tool: original calculation
            percent = int((current_frame / total_frames) * 100)

        percent = max(0, min(100, percent))

        # v0.10.0: Always broadcast via WebSocket for real-time updates
        from .progress import progress_callback
        progress_callback(
            job_id=job_id,
            current_frame=current_frame,
            total_frames=total_frames,
            current_tool=tool_name if tool_name else None,
            tools_total=total_tools if total_tools > 1 else None,
            tools_completed=tool_index if total_tools > 1 else None,
        )

        # Throttle: only update every 5% to reduce DB writes
        # Also update on first frame (1) and last frame (total_frames)
        if current_frame == 1 or current_frame == total_frames or percent % 5 == 0:
            job = db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.progress = percent
                db.commit()
                logger.info(
                    "Progress updated: job=%s tool=%s tool_index=%d/%d frame=%d/%d percent=%d",
                    job_id,
                    tool_name,
                    tool_index + 1,
                    total_tools,
                    current_frame,
                    total_frames,
                    percent,
                )
            else:
                logger.warning("Progress update failed: job %s not found in DB", job_id)

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

        v0.9.4: Supports multi-tool execution for image_multi job type.
        - Parses tool_list for multi-tool jobs
        - Executes tools sequentially via run_plugin_tool()
        - Aggregates results into {"plugin_id": ..., "tools": {...}} format
        - Fail-fast: one tool failure fails entire job

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

            # v0.9.4: Determine tools to execute based on job_type
            # v0.9.8: video_multi job type support
            is_multi_tool = job.job_type in ("image_multi", "video_multi")

            if is_multi_tool:
                # Parse tool_list from JSON
                if not job.tool_list:
                    job.status = JobStatus.failed
                    job.error_message = "Multi-tool job has no tool_list"
                    db.commit()
                    return False
                tools_to_run = json.loads(job.tool_list)
            else:
                # Single-tool job
                if not job.tool:
                    job.status = JobStatus.failed
                    job.error_message = "Single-tool job has no tool"
                    db.commit()
                    return False
                tools_to_run = [job.tool]

            # Validate all tools exist and support the job type
            manifest_tools = manifest.get("tools", [])

            for tool_name in tools_to_run:
                tool_def = None

                # Handle list format (Phase 12+)
                if isinstance(manifest_tools, list):
                    for t in manifest_tools:
                        if t.get("id") == tool_name:
                            tool_def = t
                            break
                # Handle dict format (legacy)
                elif isinstance(manifest_tools, dict):
                    if tool_name in manifest_tools:
                        tool_def = manifest_tools[tool_name]
                        tool_def["id"] = tool_name

                if not tool_def:
                    job.status = JobStatus.failed
                    job.error_message = (
                        f"Tool '{tool_name}' not found in plugin '{job.plugin_id}'"
                    )
                    db.commit()
                    return False

                # Validate tool supports job_type
                # v0.9.8: Prefer input_types (new) over inputs (legacy)
                input_types = tool_def.get("input_types")
                if not isinstance(input_types, list):
                    # Fallback to inputs keys for legacy manifests
                    tool_inputs = tool_def.get("inputs", {})
                    if isinstance(tool_inputs, dict):
                        input_types = list(tool_inputs.keys())
                    else:
                        input_types = []

                if job.job_type in ("image", "image_multi"):
                    if (
                        "image_bytes" not in input_types
                        and "image_base64" not in input_types
                    ):
                        job.status = JobStatus.failed
                        job.error_message = (
                            f"Tool '{tool_name}' does not support image input"
                        )
                        db.commit()
                        return False
                elif job.job_type in ("video", "video_multi"):
                    if "video" not in input_types and "video_path" not in input_types:
                        job.status = JobStatus.failed
                        job.error_message = (
                            f"Tool '{tool_name}' does not support video input"
                        )
                        db.commit()
                        return False

            # Branch by job_type to prepare arguments
            args: Dict[str, Any] = {}

            if job.job_type in ("image", "image_multi"):
                # Load image file from storage
                image_path = self._storage.load_file(job.input_path)
                with open(image_path, "rb") as f:
                    image_bytes = f.read()

                # Determine parameter name from first tool's manifest
                first_tool_def = None
                if isinstance(manifest_tools, list):
                    for t in manifest_tools:
                        if t.get("id") == tools_to_run[0]:
                            first_tool_def = t
                            break
                elif isinstance(manifest_tools, dict):
                    first_tool_def = manifest_tools.get(tools_to_run[0])

                if first_tool_def:
                    tool_inputs = first_tool_def.get("inputs", [])
                    if isinstance(tool_inputs, dict):
                        input_type_list = list(tool_inputs.keys())
                    else:
                        input_type_list = tool_inputs
                else:
                    input_type_list = []

                # Use image_base64 if manifest specifies it, otherwise fall back to image_bytes
                if "image_base64" in input_type_list:
                    import base64

                    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                    args = {"image_base64": image_base64}
                    if "language" in input_type_list:
                        args["language"] = "eng"
                    if "psm" in input_type_list:
                        args["psm"] = 6
                else:
                    args = {"image_bytes": image_bytes}
                logger.info("Job %s: loaded image file %s", job.job_id, image_path)

            elif job.job_type in ("video", "video_multi"):
                # Load video file from storage
                video_path = self._storage.load_file(job.input_path)

                # v0.9.6: Get total frames for progress tracking
                # v0.9.7: For multi-tool, we need progress per tool
                total_frames = self._get_total_frames(str(video_path))
                total_tools = len(tools_to_run)
                logger.info(
                    "Job %s: video has %d frames, %d tools for unified progress tracking",
                    job.job_id,
                    total_frames,
                    total_tools,
                )

                args = {"video_path": str(video_path)}
                logger.info("Job %s: loaded video file %s", job.job_id, video_path)
            else:
                job.status = JobStatus.failed
                job.error_message = f"Unknown job_type: {job.job_type}"
                db.commit()
                return False

            # v0.9.4: Execute tools
            # v0.9.7: Updated to use unified progress for multi-tool video jobs
            results: Dict[str, Any] = {}
            num_tools = len(tools_to_run)

            for idx, tool_name in enumerate(tools_to_run):
                logger.info("Job %s: executing tool '%s'", job.job_id, tool_name)

                # v0.9.8: Create per-tool progress callback for video jobs
                progress_callback = None
                if job.job_type in ("video", "video_multi"):

                    def make_progress_cb(tool_index: int):
                        def cb(current_frame: int, total: int = total_frames) -> None:
                            per_total = total if total and total > 0 else total_frames
                            overall_total = per_total * num_tools
                            overall_current = (tool_index * per_total) + current_frame
                            self._update_job_progress(
                                str(job.job_id), overall_current, overall_total, db
                            )

                        return cb

                    progress_callback = make_progress_cb(idx)

                tool_args = args.copy() if args else {}

                # Execute tool via plugin_service (includes sandbox and error handling)
                result = plugin_service.run_plugin_tool(
                    job.plugin_id,
                    tool_name,
                    tool_args,
                    progress_callback=progress_callback,
                )

                # Handle Pydantic models
                if hasattr(result, "model_dump"):
                    result = result.model_dump()
                elif hasattr(result, "dict"):
                    result = result.dict()

                results[tool_name] = result
                logger.info(
                    "Job %s: tool '%s' executed successfully", job.job_id, tool_name
                )

            # v0.9.8: Prepare output based on job type
            output_data: Dict[str, Any]
            if job.job_type in ("video", "video_multi"):
                # Canonical video results JSON
                output_data = {
                    "job_id": str(job.job_id),
                    "status": "completed",
                    "results": [
                        {"tool": t, "output": results[t]} for t in tools_to_run
                    ],
                }
            elif is_multi_tool:
                # Multi-tool image format
                output_data = {"plugin_id": job.plugin_id, "tools": results}
            else:
                # Single-tool job (image)
                output_data = {
                    "plugin_id": job.plugin_id,
                    "tool": tools_to_run[0],
                    "results": results[tools_to_run[0]],
                }

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
            # v0.9.8: Ensure 100% progress on completion for video jobs
            if job.job_type in ("video", "video_multi"):
                job.progress = 100
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
