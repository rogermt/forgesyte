"""Session Manager for Phase 17 streaming.

Manages per-connection state for WebSocket streaming sessions.

This module provides:
- Session state tracking (frame_index, dropped_frames, etc.)
- Backpressure delegation
- Timing utilities
- Environment variable configuration

Author: Roger
Phase: 17
"""

import os
import time
import uuid
from typing import Optional

from app.services.streaming.backpressure import Backpressure


class SessionManager:
    """Manages state for a single WebSocket streaming session.

    Each WebSocket connection gets its own SessionManager instance.
    State is ephemeral (not persisted) and destroyed on disconnect.
    """

    def __init__(self, pipeline_id: str) -> None:
        """Initialize session manager.

        Args:
            pipeline_id: ID of the pipeline being used for this session
        """
        self.session_id: str = str(uuid.uuid4())
        self.pipeline_id: str = pipeline_id

        # Frame tracking
        self.frame_index: int = 0
        self.dropped_frames: int = 0
        self.last_processed_ts: Optional[float] = None

        # Backpressure state
        self.backpressure_state: str = "normal"

        # Configuration (from env vars or defaults)
        self.drop_threshold: float = float(
            os.getenv("STREAM_DROP_THRESHOLD", "0.10")
        )
        self.slowdown_threshold: float = float(
            os.getenv("STREAM_SLOWDOWN_THRESHOLD", "0.30")
        )

    @staticmethod
    def now_ms() -> float:
        """Get current time in milliseconds.

        Returns:
            Current time in milliseconds since epoch
        """
        return time.time() * 1000.0

    def increment_frame(self) -> None:
        """Increment the frame counter."""
        self.frame_index += 1

    def mark_drop(self) -> None:
        """Increment the dropped frames counter."""
        self.dropped_frames += 1

    def drop_rate(self) -> float:
        """Calculate the current drop rate.

        Returns:
            Drop rate as a float (dropped_frames / frame_index)
            Returns 0.0 if no frames have been processed
        """
        if self.frame_index == 0:
            return 0.0
        return self.dropped_frames / self.frame_index

    def should_drop_frame(self, processing_time_ms: float) -> bool:
        """Check if a frame should be dropped due to backpressure.

        Delegates to Backpressure.should_drop().

        Args:
            processing_time_ms: Time taken to process the last frame (in ms)

        Returns:
            True if frame should be dropped, False otherwise
        """
        return Backpressure.should_drop(
            processing_time_ms=processing_time_ms,
            drop_rate=self.drop_rate(),
            drop_threshold=self.drop_threshold,
        )

    def should_slow_down(self) -> bool:
        """Check if client should be sent a slow-down signal.

        Delegates to Backpressure.should_slow_down().

        Returns:
            True if slow-down signal should be sent, False otherwise
        """
        return Backpressure.should_slow_down(
            drop_rate=self.drop_rate(),
            slowdown_threshold=self.slowdown_threshold,
        )