"""Backpressure logic for Phase 17 streaming.

Provides static methods for backpressure decision-making.

This module provides:
- Frame dropping logic
- Slow-down signal logic
- Configuration-based thresholds

Author: Roger
Phase: 17
"""


class Backpressure:
    """Static utility class for backpressure decisions.

    Implements the backpressure algorithm defined in Phase 17:
    - Drop frames if processing is too slow OR drop rate is too high
    - Send slow-down signals if drop rate exceeds threshold
    """

    @staticmethod
    def should_drop(
        processing_time_ms: float,
        drop_rate: float,
        drop_threshold: float,
    ) -> bool:
        """Determine if a frame should be dropped.

        Args:
            processing_time_ms: Time taken to process the last frame (in ms)
            drop_rate: Current drop rate (dropped_frames / total_frames)
            drop_threshold: Threshold for dropping frames (default 0.10)

        Returns:
            True if frame should be dropped, False otherwise

        Algorithm:
            - Condition 1: Processing too slow (> frame interval)
            - Condition 2: Drop rate too high (> threshold)
        """
        # Condition 1: Processing too slow
        # Assume 30 FPS target = ~33ms per frame
        frame_interval_ms = 33.33
        if processing_time_ms > frame_interval_ms:
            return True

        # Condition 2: Drop rate too high
        if drop_rate > drop_threshold:
            return True

        return False

    @staticmethod
    def should_slow_down(
        drop_rate: float,
        slowdown_threshold: float,
    ) -> bool:
        """Determine if client should be sent a slow-down signal.

        Args:
            drop_rate: Current drop rate (dropped_frames / total_frames)
            slowdown_threshold: Threshold for slow-down signal (default 0.30)

        Returns:
            True if slow-down signal should be sent, False otherwise

        Algorithm:
            - Send slow-down if drop rate exceeds slowdown threshold
        """
        return drop_rate > slowdown_threshold