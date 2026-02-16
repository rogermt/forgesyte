"""Tests for Session Manager (Commit 2).

Following TDD: Write tests first, then implement code to make them pass.

These tests verify:
- SessionManager creates with correct initial state
- increment_frame() increments correctly
- mark_drop() increments correctly
- drop_rate() calculates correctly
- should_drop_frame() delegates to Backpressure
- should_slow_down() delegates to Backpressure
- Thresholds load from environment variables
- now_ms() returns current time in milliseconds
"""

import os
import sys
import time
import uuid

import pytest

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestSessionManagerInitialization:
    """Test SessionManager initialization."""

    def test_session_manager_creates_with_correct_initial_state(self) -> None:
        """Test that SessionManager creates with correct initial state."""
        from app.services.streaming.session_manager import SessionManager

        session = SessionManager(pipeline_id="yolo_ocr")

        # Check UUID is generated
        assert session.session_id is not None
        assert len(session.session_id) > 0

        # Check initial values
        assert session.pipeline_id == "yolo_ocr"
        assert session.frame_index == 0
        assert session.dropped_frames == 0
        assert session.last_processed_ts is None
        assert session.backpressure_state == "normal"

        # Check default thresholds
        assert session.drop_threshold == 0.10
        assert session.slowdown_threshold == 0.30


class TestSessionManagerFrameOperations:
    """Test frame counting operations."""

    def test_increment_frame_increments_correctly(self) -> None:
        """Test that increment_frame() increments correctly."""
        from app.services.streaming.session_manager import SessionManager

        session = SessionManager(pipeline_id="yolo_ocr")

        assert session.frame_index == 0
        session.increment_frame()
        assert session.frame_index == 1
        session.increment_frame()
        assert session.frame_index == 2

    def test_mark_drop_increments_correctly(self) -> None:
        """Test that mark_drop() increments correctly."""
        from app.services.streaming.session_manager import SessionManager

        session = SessionManager(pipeline_id="yolo_ocr")

        assert session.dropped_frames == 0
        session.mark_drop()
        assert session.dropped_frames == 1
        session.mark_drop()
        assert session.dropped_frames == 2


class TestSessionManagerDropRate:
    """Test drop rate calculation."""

    def test_drop_rate_calculates_correctly(self) -> None:
        """Test that drop_rate() calculates correctly."""
        from app.services.streaming.session_manager import SessionManager

        session = SessionManager(pipeline_id="yolo_ocr")

        # No frames processed yet
        assert session.drop_rate() == 0.0

        # Process 10 frames, drop 2
        for _ in range(10):
            session.increment_frame()
        for _ in range(2):
            session.mark_drop()

        # Drop rate should be 2 / 10 = 0.2
        assert session.drop_rate() == 0.2

    def test_drop_rate_with_zero_frame_index(self) -> None:
        """Test that drop_rate() returns 0 when frame_index is 0."""
        from app.services.streaming.session_manager import SessionManager

        session = SessionManager(pipeline_id="yolo_ocr")

        # Drop some frames without processing any
        session.mark_drop()
        session.mark_drop()

        # Should still return 0.0 since frame_index is 0
        assert session.drop_rate() == 0.0


class TestSessionManagerTiming:
    """Test timing utilities."""

    def test_now_ms_returns_current_time_in_milliseconds(self) -> None:
        """Test that now_ms() returns current time in milliseconds."""
        from app.services.streaming.session_manager import SessionManager

        before = time.time() * 1000.0
        result = SessionManager.now_ms()
        after = time.time() * 1000.0

        # Result should be between before and after
        assert before <= result <= after


class TestSessionManagerBackpressureDelegation:
    """Test backpressure delegation."""

    def test_should_drop_frame_delegates_to_backpressure(self) -> None:
        """Test that should_drop_frame() delegates to Backpressure."""
        from app.services.streaming.session_manager import SessionManager

        session = SessionManager(pipeline_id="yolo_ocr")

        # This should delegate to Backpressure.should_drop()
        # For now, we just verify the method exists and can be called
        result = session.should_drop_frame(processing_time_ms=0.0)
        assert isinstance(result, bool)

    def test_should_slow_down_delegates_to_backpressure(self) -> None:
        """Test that should_slow_down() delegates to Backpressure."""
        from app.services.streaming.session_manager import SessionManager

        session = SessionManager(pipeline_id="yolo_ocr")

        # This should delegate to Backpressure.should_slow_down()
        # For now, we just verify the method exists and can be called
        result = session.should_slow_down()
        assert isinstance(result, bool)


class TestSessionManagerEnvironmentVariables:
    """Test environment variable loading."""

    def test_thresholds_load_from_environment_variables(self) -> None:
        """Test that thresholds load from environment variables."""
        # Set environment variables
        os.environ["STREAM_DROP_THRESHOLD"] = "0.25"
        os.environ["STREAM_SLOWDOWN_THRESHOLD"] = "0.50"

        try:
            # Import after setting env vars
            from app.services.streaming.session_manager import SessionManager

            session = SessionManager(pipeline_id="yolo_ocr")

            # Check that thresholds are loaded from env vars
            assert session.drop_threshold == 0.25
            assert session.slowdown_threshold == 0.50
        finally:
            # Clean up
            del os.environ["STREAM_DROP_THRESHOLD"]
            del os.environ["STREAM_SLOWDOWN_THRESHOLD"]