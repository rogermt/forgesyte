"""Progress callback module for WebSocket job progress streaming.

v0.10.0: Emits real-time progress events for video jobs.

This module provides:
- ProgressEvent: Dataclass for progress event data
- progress_callback: Function to create and broadcast progress events
"""

from dataclasses import dataclass
from typing import Optional

from app.websocket_manager import ws_manager


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
    event = ProgressEvent(
        job_id=job_id,
        current_frame=current_frame,
        total_frames=total_frames,
        current_tool=current_tool,
        tools_total=tools_total,
        tools_completed=tools_completed,
    )

    # Broadcast to job topic subscribers
    # Note: ws_manager.broadcast is async, but we use create_task
    # to avoid blocking the worker. The broadcast happens in the
    # background via the existing event loop.
    import asyncio

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(ws_manager.broadcast(event.to_dict(), topic=f"job:{job_id}"))
    except RuntimeError:
        # No running event loop - this can happen in sync contexts
        # Progress still returned, just not broadcast
        pass

    return event
