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
from ..services.tool_router import iter_manifest_tools
from .progress import send_job_completed
from .worker_state import worker_last_heartbeat


def _derive_video_summary(results: dict) -> dict:
    """Derive summary metadata from video job results.

    Discussion #354: Extract lightweight metadata from video results
    for pre-computed storage to avoid loading full artifacts on hot path.

    Args:
        results: Full video results dict

    Returns:
        Summary dict with frame_count, detection_count, classes
    """
    frame_count = 0
    detection_count = 0
    classes: List[str] = []

    # Handle frames array (most common structure)
    frames = results.get("frames", [])
    if isinstance(frames, list):
        frame_count = len(frames)

        classes_set: set = set()
        for frame in frames:
            # Defensive: skip non-dict frames (malformed data)
            if not isinstance(frame, dict):
                continue
            detections = frame.get("detections", [])
            # Defensive: ensure detections is a list
            if not isinstance(detections, list):
                continue
            detection_count += len(detections)
            for det in detections:
                # Defensive: ensure det is a dict before key access
                if isinstance(det, dict) and "class" in det:
                    classes_set.add(det["class"])

        classes = sorted(classes_set)

    # Handle tools structure (multi-tool video jobs)
    tools = results.get("tools", {})
    if isinstance(tools, dict):
        tool_detections = 0
        tool_classes: set = set()

        for _tool_name, tool_results in tools.items():
            # Defensive: skip if tool_results is not a dict (malformed data)
            if not isinstance(tool_results, dict):
                continue
            tool_frames = tool_results.get("frames", [])
            # Defensive: skip if tool_frames is not a list
            if not isinstance(tool_frames, list):
                continue
            for frame in tool_frames:
                # Defensive: skip non-dict frames
                if not isinstance(frame, dict):
                    continue
                detections = frame.get("detections", [])
                if not isinstance(detections, list):
                    continue
                tool_detections += len(detections)
                for det in detections:
                    if isinstance(det, dict) and "class" in det:
                        tool_classes.add(det["class"])

        # Add to existing counts
        detection_count += tool_detections
        classes = sorted(set(classes) | tool_classes)

    return {
        "frame_count": frame_count,
        "detection_count": detection_count,
        "classes": classes,
    }


logger = logging.getLogger(__name__)


def _merge_video_frames(
    results: Dict[str, Any], tools_to_run: List[str], job_id: str
) -> Dict[str, Any]:
    """Merge frames from multiple video tools by frame_idx.

    For video_multi jobs, each tool produces its own frames array.
    This function merges them into a unified frames array where each
    frame contains data from all tools that processed that frame.

    Args:
        results: Dict mapping tool_name -> tool_output
        tools_to_run: List of tool names in execution order
        job_id: Job UUID string for output

    Returns:
        Dict with merged frames: {job_id, status, total_frames, frames}
        where frames[i] = {frame_idx, tool1: {...}, tool2: {...}, ...}

    Example:
        Input:
            results = {
                "player_tracker": {"frames": [{"frame_idx": 0, "detections": [...]}]},
                "ball_detector": {"frames": [{"frame_idx": 0, "balls": [...]}]}
            }
        Output:
            {
                "job_id": "...",
                "status": "completed",
                "total_frames": 1,
                "frames": [{"frame_idx": 0, "player_tracker": {...}, "ball_detector": {...}}]
            }
    """
    # Collect all frames indexed by frame_idx
    frames_by_idx: Dict[int, Dict[str, Any]] = {}
    total_frames = 0

    for tool_name in tools_to_run:
        tool_output = results.get(tool_name, {})

        if isinstance(tool_output, dict):
            tool_frames = tool_output.get("frames", [])
            if tool_output.get("total_frames", 0) > total_frames:
                total_frames = tool_output.get("total_frames", 0)
        elif isinstance(tool_output, list):
            tool_frames = tool_output
            if len(tool_output) > total_frames:
                total_frames = len(tool_output)
        else:
            # Unknown format - skip this tool
            logger.warning(
                f"Tool {tool_name} output has unexpected format: {type(tool_output)}"
            )
            continue

        for frame in tool_frames:
            if isinstance(frame, dict):
                frame_idx = frame.get("frame_idx", len(frames_by_idx))
            else:
                # Frame is not a dict - use index
                frame_idx = len(frames_by_idx)
                frame = {"value": frame}

            if frame_idx not in frames_by_idx:
                frames_by_idx[frame_idx] = {"frame_idx": frame_idx}

            # Add tool-specific data (exclude frame_idx to avoid duplication)
            frame_data = {k: v for k, v in frame.items() if k != "frame_idx"}
            frames_by_idx[frame_idx][tool_name] = frame_data

    # Sort frames by index
    merged_frames = [frames_by_idx[idx] for idx in sorted(frames_by_idx.keys())]

    # Only fall back to merged-frame count when tools did not report source video length
    # This preserves the actual video length for sparse outputs (e.g., detector only emits frames with hits)
    if total_frames == 0 and merged_frames:
        total_frames = len(merged_frames)

    return {
        "job_id": job_id,
        "status": "completed",
        "total_frames": total_frames,
        "frames": merged_frames,
    }


def get_ray_runtime_env() -> dict:
    """Build Ray runtime_env with FORGESYTE_* vars and PYTHONPATH sync.

    This shared helper ensures consistent runtime_env construction between
    main.py (WebSocket actors) and worker.py (background job processing).

    Returns:
        dict: runtime_env dict with env_vars containing:
            - FORGESYTE_* environment variables
            - RAY_* environment variables
            - PYTHONPATH with CWD prepended
    """
    import os
    from pathlib import Path

    cwd = str(Path.cwd().resolve())
    current_pythonpath = os.environ.get("PYTHONPATH", "")
    new_pythonpath = f"{cwd}:{current_pythonpath}" if current_pythonpath else cwd

    runtime_env = {
        "env_vars": {
            k: v for k, v in os.environ.items() if k.startswith(("FORGESYTE_", "RAY_"))
        }
    }
    runtime_env["env_vars"]["PYTHONPATH"] = new_pythonpath
    return runtime_env


def init_ray() -> bool:
    """Initialize Ray with configurable mode.

    v0.12.0: Supports both local and remote Ray initialization.
    - If RAY_ADDRESS env var is set, connects to existing cluster
    - Otherwise, starts local Ray instance

    Returns:
        True if initialization succeeded, False otherwise
    """
    import os

    import ray

    try:
        # Skip if already initialized (e.g., by main.py for WebSocket actors)
        if ray.is_initialized():
            return True

        runtime_env = get_ray_runtime_env()

        ray_address = os.environ.get("RAY_ADDRESS")
        if ray_address:
            ray.init(
                address=ray_address,
                ignore_reinit_error=True,
                runtime_env=runtime_env,
            )
            logger.info(f"Ray connected to cluster at {ray_address}")
        else:
            ray.init(ignore_reinit_error=True, runtime_env=runtime_env)
            logger.info("Ray initialized locally with synced env_vars")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Ray: {e}")
        return False


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
    """Processes jobs from the queue using Ray for GPU-accelerated execution.

    v0.12.0: Added Ray integration for GPU-accelerated job processing.
    - Dispatches jobs to Ray cluster via execute_pipeline_remote.remote()
    - Polls active Ray futures for completion
    - Limits concurrent jobs to avoid OOM
    """

    def __init__(
        self,
        queue: Optional[InMemoryQueueService] = None,
        session_factory=None,
        storage: Optional[StorageService] = None,
        plugin_service=None,
        use_ray: bool = False,
    ) -> None:
        """Initialize worker.

        Args:
            queue: Ignored (kept for backward compatibility with tests)
            session_factory: Session factory (defaults to SessionLocal from database.py)
            storage: StorageService instance for file I/O
            plugin_service: PluginManagementService instance for plugin execution
            use_ray: If True, use Ray for GPU-accelerated execution. If False (default),
                     use synchronous execution for backward compatibility.
        """
        self._session_factory = session_factory or SessionLocal
        self._storage = storage
        self._plugin_service = plugin_service
        self._running = True
        self._use_ray = use_ray

        # v0.12.0: Ray state tracking for async job processing
        self.active_futures: Dict[Any, str] = {}  # { ray_ref: str(job_id) }
        self.job_metadata: Dict[str, Dict[str, Any]] = {}  # { str(job_id): dict }

        # v0.12.0: Recover orphaned Ray jobs on startup (Issue #270)
        if use_ray:
            self._recover_ray_jobs()

        # Register signal handlers only if running in main thread
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)

    def _recover_ray_jobs(self) -> None:
        """Recover orphaned Ray jobs on worker startup.

        v0.12.0: Called during __init__ when use_ray=True (Issue #270).

        Finds all RUNNING jobs with ray_future_id and attempts to reattach
        to their Ray futures. If Ray cluster is unavailable or futures are
        gone, marks jobs as failed.
        """
        db = self._session_factory()
        try:
            # Find all RUNNING jobs with ray_future_id
            orphaned_jobs = (
                db.query(Job)
                .filter(Job.status == JobStatus.running)
                .filter(Job.ray_future_id.isnot(None))
                .all()
            )

            if not orphaned_jobs:
                logger.info("No orphaned Ray jobs to recover")
                return

            logger.info(
                f"Found {len(orphaned_jobs)} orphaned Ray jobs, attempting recovery"
            )

            for job in orphaned_jobs:
                try:
                    # Try to reconstruct the Ray future reference
                    # Ray future IDs are strings like "ObjectRef(...)"
                    future_id = job.ray_future_id

                    # Check if we can still access this future in Ray
                    # Use ray.objects() or try to get the object
                    # For now, we'll mark these as failed since the cluster
                    # state is lost on worker restart
                    #
                    # Future enhancement: Could try to reattach if cluster persisted
                    logger.warning(
                        f"Job {job.job_id} was running before restart, "
                        f"marking as failed (Ray future {future_id} lost)"
                    )
                    job.status = JobStatus.failed
                    job.error_message = "Worker restarted - Ray future lost"
                    job.ray_future_id = None
                except Exception as e:
                    logger.error(f"Error recovering job {job.job_id}: {e}")
                    job.status = JobStatus.failed
                    job.error_message = f"Recovery failed: {e}"
                    job.ray_future_id = None

            db.commit()
            logger.info(
                f"Recovery complete: {len(orphaned_jobs)} jobs marked as failed"
            )

        except Exception as e:
            logger.error(f"Error during Ray job recovery: {e}")
        finally:
            db.close()

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
        # Discussion #356: Debug logging for diagnosing frame processing issues
        logger.debug(
            "[WORKER] job=%s tool=%s frame=%s/%s",
            job_id,
            tool_name,
            current_frame,
            total_frames,
        )

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
        """Process jobs using Ray for GPU-accelerated execution.

        v0.12.0: Refactored to use Ray for job execution.
        - Polls active Ray futures (non-blocking)
        - Dispatches new jobs to Ray cluster
        - Limits concurrency to avoid OOM

        Falls back to synchronous execution if use_ray is False (for backward compatibility).

        Returns:
            True if any work was done, False otherwise
        """
        # Backward compatibility: use synchronous execution if Ray is disabled
        if not self._use_ray:
            return self._run_once_sync()

        import ray

        from ..ray_tasks import execute_pipeline_remote

        processed_something = False

        # 1. Poll active Ray futures (non-blocking)
        if self.active_futures:
            ready_refs, _ = ray.wait(
                list(self.active_futures.keys()),
                num_returns=len(self.active_futures),
                timeout=0,
            )
            for ref in ready_refs:
                job_id = self.active_futures.pop(ref)
                meta = self.job_metadata.pop(job_id, {})
                try:
                    results = ray.get(ref)
                    self._finalize_job(job_id, meta, results)
                except Exception as e:
                    logger.error(
                        f"Ray task failed for job {job_id}: {e}", exc_info=True
                    )
                    self._fail_job(job_id, str(e))
                processed_something = True

        # 2. Dispatch new jobs (Limit concurrency to avoid OOM)
        if len(self.active_futures) < 2:
            db = self._session_factory()
            try:
                job = (
                    db.query(Job)
                    .filter(Job.status == JobStatus.pending)
                    .order_by(Job.created_at.asc())
                    .first()
                )
                if job:
                    # Atomic claim: only update if still pending
                    rows_updated = (
                        db.query(Job)
                        .filter(Job.job_id == job.job_id)
                        .filter(Job.status == JobStatus.pending)
                        .update({"status": JobStatus.running})
                    )
                    db.commit()

                    if rows_updated == 0:
                        # Already claimed by another worker
                        logger.debug(
                            f"Job {job.job_id} already claimed by another worker"
                        )
                        return processed_something

                    db.refresh(job)

                    # Query tools from job_tools table via service
                    from app.services.job_tools_service import JobToolsService

                    tools_to_run = JobToolsService.get_tools_for_job(db, job.job_id)
                    is_multi = len(tools_to_run) > 1
                    meta = {
                        "plugin_id": job.plugin_id,
                        "job_type": job.job_type,
                        "tools_to_run": tools_to_run,
                        "is_multi": is_multi,
                    }

                    # Dispatch to Ray Cluster (with failure handling)
                    try:
                        future = execute_pipeline_remote.remote(
                            plugin_id=job.plugin_id,
                            tools_to_run=tools_to_run,
                            input_path=job.input_path,
                            job_type=job.job_type,
                        )
                    except Exception as dispatch_exc:
                        # Dispatch failed - mark job as failed
                        logger.error(
                            f"Ray dispatch failed for job {job.job_id}: {dispatch_exc}"
                        )
                        job.status = JobStatus.failed
                        job.error_message = f"Ray dispatch failed: {dispatch_exc}"
                        db.commit()
                        raise

                    self.job_metadata[str(job.job_id)] = meta
                    self.active_futures[future] = str(job.job_id)

                    # v0.12.0: Persist ray_future_id for recovery (Issue #270)
                    job.ray_future_id = str(future)
                    db.commit()

                    logger.info(f"Job {job.job_id} dispatched to Ray cluster")
                    processed_something = True
            except Exception as e:
                logger.error(f"Error dispatching job: {e}")
            finally:
                db.close()

        return processed_something

    def _run_once_sync(self) -> bool:
        """Process one job synchronously (backward compatibility mode).

        This is the original run_once implementation before Ray integration.
        Used for unit tests and when Ray is not available.

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

            # Execute pipeline on input file
            return self._execute_pipeline(job, db)
        finally:
            db.close()

    def _finalize_job(self, job_id: str, meta: dict, results: dict) -> None:
        """Finalize a completed Ray job.

        Args:
            job_id: Job UUID string
            meta: Job metadata dict
            results: Results from Ray task
        """
        db = self._session_factory()
        try:
            job = db.query(Job).filter(Job.job_id == job_id).first()
            if not job:
                logger.warning(f"Job {job_id} not found in database")
                return

            tools_to_run = meta.get("tools_to_run", [])
            output_data: Dict[str, Any]

            if job.job_type == "video_multi":
                # Multi-tool video: merge frames from all tools by frame_idx
                output_data = _merge_video_frames(
                    results, tools_to_run, str(job.job_id)
                )
            elif job.job_type == "video":
                # Single-tool video: flatten first tool's output for UI compatibility
                first_tool_output = results.get(tools_to_run[0], {})
                if isinstance(first_tool_output, dict):
                    output_data = {
                        "job_id": str(job.job_id),
                        "status": "completed",
                        "total_frames": first_tool_output.get("total_frames"),
                        "frames": first_tool_output.get("frames", []),
                    }
                    for key in first_tool_output:
                        if key not in ("total_frames", "frames"):
                            output_data[key] = first_tool_output[key]
                elif isinstance(first_tool_output, list):
                    output_data = {
                        "job_id": str(job.job_id),
                        "status": "completed",
                        "total_frames": len(first_tool_output),
                        "frames": first_tool_output,
                    }
                else:
                    output_data = {
                        "job_id": str(job.job_id),
                        "status": "completed",
                        "results": first_tool_output,
                    }
            elif meta.get("is_multi"):
                output_data = {"plugin_id": job.plugin_id, "tools": results}
            else:
                output_data = {
                    "plugin_id": job.plugin_id,
                    "tool": tools_to_run[0],
                    "results": results.get(tools_to_run[0]),
                }

            output_json = json.dumps(output_data)
            if not self._storage:
                logger.error(f"No storage service for job {job_id}")
                self._fail_job(
                    job_id, "Storage service unavailable during finalization"
                )
                return
            output_path = self._storage.save_file(
                BytesIO(output_json.encode()),
                f"{job.job_type}/output/{job.job_id}.json",
            )
            job.status = JobStatus.completed
            job.output_path = output_path
            job.ray_future_id = None  # v0.12.0: Clear on completion (Issue #270)
            if job.job_type in ("video", "video_multi"):
                job.progress = 100
            # Discussion #354: Pre-compute summary for /v1/jobs hot path
            summary_dict = _derive_video_summary(output_data)
            job.summary = json.dumps(summary_dict)
            db.commit()
            send_job_completed(str(job.job_id))
            logger.info(f"Job {job.job_id} completed successfully via Ray")
        finally:
            db.close()

    def _fail_job(self, job_id: str, error_msg: str) -> None:
        """Mark a job as failed.

        Args:
            job_id: Job UUID string
            error_msg: Error message
        """
        db = self._session_factory()
        try:
            job = db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = JobStatus.failed
                job.error_message = error_msg
                job.ray_future_id = None  # v0.12.0: Clear on failure (Issue #270)
                db.commit()
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
                plugin_manager.load_plugins()  # Issue #304: Load plugins from entry points
                plugin_service = PluginManagementService(plugin_manager)

            manifest = plugin_service.get_plugin_manifest(job.plugin_id)
            if not manifest:
                job.status = JobStatus.failed
                job.error_message = f"Plugin '{job.plugin_id}' not found"
                db.commit()
                return False

            # v0.9.4: Determine tools to execute from job_tools table
            # v0.15.1: Query from job_tools via JobToolsService
            from app.services.job_tools_service import JobToolsService

            tools_to_run = JobToolsService.get_tools_for_job(db, job.job_id)

            if not tools_to_run:
                job.status = JobStatus.failed
                job.error_message = "Job has no tools"
                db.commit()
                return False

            is_multi_tool = len(tools_to_run) > 1

            # Validate all tools exist and support the job type
            manifest_tools = iter_manifest_tools(manifest)

            for tool_name in tools_to_run:
                tool_def = None
                for t in manifest_tools:
                    if t.get("id") == tool_name:
                        tool_def = t
                        break

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
                for t in manifest_tools:
                    if t.get("id") == tools_to_run[0]:
                        first_tool_def = t
                        break

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
            # v0.10.0: Flatten video results for VideoResultsViewer compatibility
            # v0.12.0: video_multi merges frames from all tools
            output_data: Dict[str, Any]
            if job.job_type == "video_multi":
                # Multi-tool video: merge frames from all tools by frame_idx
                output_data = _merge_video_frames(
                    results, tools_to_run, str(job.job_id)
                )
            elif job.job_type == "video":
                # v0.10.0: Flatten video results for UI
                # Frontend expects { total_frames, frames } at top level
                first_tool_output = results[tools_to_run[0]]

                # Handle both dict and list output formats
                if isinstance(first_tool_output, dict):
                    # Output is {frames: [...], total_frames: N, ...}
                    output_data = {
                        "job_id": str(job.job_id),
                        "status": "completed",
                        "total_frames": first_tool_output.get("total_frames"),
                        "frames": first_tool_output.get("frames", []),
                    }
                    # Include any additional fields from the output
                    for key in first_tool_output:
                        if key not in ("total_frames", "frames"):
                            output_data[key] = first_tool_output[key]
                elif isinstance(first_tool_output, list):
                    # Output is already a list of frames
                    output_data = {
                        "job_id": str(job.job_id),
                        "status": "completed",
                        "total_frames": len(first_tool_output),
                        "frames": first_tool_output,
                    }
                else:
                    # Fallback for unknown format
                    output_data = {
                        "job_id": str(job.job_id),
                        "status": "completed",
                        "results": first_tool_output,
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
            # Discussion #354: Pre-compute summary for /v1/jobs hot path
            summary_dict = _derive_video_summary(output_data)
            job.summary = json.dumps(summary_dict)
            db.commit()

            # Notify WebSocket subscribers
            send_job_completed(str(job.job_id))

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
