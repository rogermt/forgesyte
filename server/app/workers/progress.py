"""Progress callback module for WebSocket job progress streaming.

v0.10.0: Emits real-time progress events for video jobs.
v0.15.9: Fixed broadcast from sync worker thread (Discussion #355).

This module provides:
- ProgressEvent: Dataclass for progress event data
- progress_callback: Function to create and broadcast progress events
- set_main_event_loop: Set the main event loop for thread-safe broadcast
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from app.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

# Module-level reference to the main event loop
# Set during startup via set_main_event_loop()
_main_event_loop: Optional[asyncio.AbstractEventLoop] = None


def set_main_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Store reference to the main event loop for thread-safe broadcast.

    Discussion #355: The worker runs in a sync thread without an event loop.
    This function is called during startup to store a reference to the main
    event loop, allowing the worker to broadcast via run_coroutine_threadsafe.

    Args:
        loop: The main asyncio event loop (from asyncio.get_running_loop())
    """
    global _main_event_loop
    _main_event_loop = loop
    logger.info("Progress callback: main event loop reference stored")


@dataclass
class ProgressEvent:
    """Progress event for video job processing.

    Attributes:
        job_id: Job UUID string
        current_frame: Current frame number being processed
        total_frames: Total frames in video
        current_tool: Optional name of current tool being executed
        tools_total: Optional total number of tools in multi-tool job
        tools_completed: Optional count of completed tools
    """

    job_id: str
    current_frame: int
    total_frames: int
    current_tool: Optional[str] = None
    tools_total: Optional[int] = None
    tools_completed: Optional[int] = None

    @property
    def percent(self) -> int:
        """Calculate percentage (0-100)."""
        if self.total_frames <= 0:
            return 0
        return int((self.current_frame / self.total_frames) * 100)

    def to_dict(self) -> dict:
        """Serialize to dict for WebSocket broadcast."""
        result = {
            "job_id": self.job_id,
            "current_frame": self.current_frame,
            "total_frames": self.total_frames,
            "percent": self.percent,
        }

        # Include optional fields if present
        if self.current_tool is not None:
            result["current_tool"] = self.current_tool
        if self.tools_total is not None:
            result["tools_total"] = self.tools_total
        if self.tools_completed is not None:
            result["tools_completed"] = self.tools_completed

        return result


def progress_callback(
    job_id: str,
    current_frame: int,
    total_frames: int,
    current_tool: Optional[str] = None,
    tools_total: Optional[int] = None,
    tools_completed: Optional[int] = None,
) -> ProgressEvent:
    """
    Create progress event and broadcast via WebSocket.

    Called by worker during video processing to emit real-time progress.

    Args:
        job_id: Job UUID string
        current_frame: Current frame number being processed
        total_frames: Total frames in video
        current_tool: Optional name of current tool
        tools_total: Optional total tools in multi-tool job
        tools_completed: Optional count of completed tools

    Returns:
        ProgressEvent that was broadcast
    """
    # Discussion #356: Debug logging for diagnosing fetch issues
    logger.debug(
        "[PROGRESS] job=%s tool=%s percent=%s frame=%s/%s",
        job_id,
        current_tool,
        int((current_frame / total_frames) * 100) if total_frames > 0 else 0,
        current_frame,
        total_frames,
    )

    event = ProgressEvent(
        job_id=job_id,
        current_frame=current_frame,
        total_frames=total_frames,
        current_tool=current_tool,
        tools_total=tools_total,
        tools_completed=tools_completed,
    )

    # Broadcast to job topic subscribers
    # Discussion #355: Support broadcast from sync worker thread
    # Three cases:
    # 1. Running in async context - use create_task
    # 2. In sync thread with main loop reference - use run_coroutine_threadsafe
    # 3. No loop available - silently skip broadcast (fallback to HTTP polling)
    broadcast_done = False

    # Case 1: Already in async context
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(ws_manager.broadcast(event.to_dict(), topic=f"job:{job_id}"))
        broadcast_done = True
    except RuntimeError:
        pass  # No running loop, try thread-safe approach

    # Case 2: In sync thread with main loop reference
    if not broadcast_done and _main_event_loop is not None:
        try:
            asyncio.run_coroutine_threadsafe(
                ws_manager.broadcast(event.to_dict(), topic=f"job:{job_id}"),
                _main_event_loop,
            )
            broadcast_done = True
        except Exception as e:
            logger.warning(
                f"Progress broadcast failed via run_coroutine_threadsafe: {e}"
            )

    # Case 3: No loop available - broadcast silently skipped
    # Frontend will still get progress via HTTP polling

    return event


def send_job_completed(job_id: str) -> None:
    """Broadcast a job completed event to WebSocket subscribers.

    v0.10.0: Notifies frontend that job finished successfully so it can
    close the WebSocket cleanly without showing an error.

    Args:
        job_id: Job UUID string
    """
    import asyncio

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(
            ws_manager.broadcast(
                {"job_id": job_id, "status": "completed"},
                topic=f"job:{job_id}",
            )
        )
    except RuntimeError:
        # No running event loop - completion event not broadcast
        # Frontend will poll and still see completed status
        pass
