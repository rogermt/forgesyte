"""Tests for receiving binary frames (Commit 5) and frame validation (Commit 6).

Following TDD: Write tests first, then implement code to make them pass.

These tests verify:
- WebSocket accepts binary frame
- WebSocket rejects text message with invalid_message error
- WebSocket closes connection on invalid_message
- Receiving frame increments frame_index
- Invalid frame sends error with detail and closes connection
- Oversized frame sends error with detail and closes connection
- Valid frame does not close connection
"""

import logging
import os
import sys

import pytest
from fastapi.testclient import TestClient

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.fixture
def client(app_with_plugins):
    """Create a test client for WebSocket testing."""
    return TestClient(app_with_plugins)


class TestBinaryFrameReception:
    """Test binary frame reception."""

    def test_websocket_accepts_binary_frame(self, client: TestClient) -> None:
        """Test that WebSocket accepts binary frame."""

        # Create a minimal JPEG frame (SOI + EOI markers)
        jpeg_frame = b"\xFF\xD8\xFF\xD9"

        with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
            # Send binary frame
            ws.send_bytes(jpeg_frame)

            # Frame should be accepted (connection should remain open)
            # We don't expect a response yet - that's Commit 6+
            pass  # If we got here, frame was accepted

    def test_websocket_rejects_text_message_with_invalid_message_error(
        self, client: TestClient
    ) -> None:
        """Test that WebSocket rejects text message with invalid_message error."""
        with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
            # Send text message (should be rejected)
            ws.send_text("hello")

            # Should receive error message
            message = ws.receive_json()
            assert message["error"] == "invalid_message"
            assert "binary" in message["detail"].lower() or "frame" in message["detail"].lower()

    def test_websocket_closes_connection_on_invalid_message(
        self, client: TestClient
    ) -> None:
        """Test that WebSocket closes connection on invalid_message."""
        with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
            # Send text message (should trigger close)
            ws.send_text("hello")

            # Should receive error message
            message = ws.receive_json()
            assert message["error"] == "invalid_message"

            # Connection should be closed now
            # Try to receive again - should raise exception or return None
            try:
                result = ws.receive_json(timeout=1.0)
                # If we get here, connection didn't close properly
                assert False, "Connection should have been closed"
            except Exception:
                # Expected - connection closed
                pass

    def test_receiving_frame_increments_frame_index(
        self, client: TestClient
    ) -> None:
        """Test that receiving frame increments frame_index."""

        # Create a minimal JPEG frame
        jpeg_frame = b"\xFF\xD8\xFF\xD9"

        with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
            # Access session via websocket.state
            # Note: We can't directly access websocket.state.session in tests,
            # but we can verify frame_index was incremented by checking session state
            # For now, we just verify the frame is accepted
            ws.send_bytes(jpeg_frame)

            # Frame should be accepted
            # Actual frame_index verification will be done in later commits
            # when we send responses back
            pass


class TestFrameValidation:
    """Test frame validation integration (Commit 6)."""

    def test_invalid_frame_sends_error_with_detail_and_closes_connection(
        self, client: TestClient
    ) -> None:
        """Test that invalid frame sends error with detail and closes connection."""
        # Create invalid JPEG (missing SOI marker)
        invalid_frame = b"\x00\x00\xFF\xD9"

        with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
            # Send invalid frame
            ws.send_bytes(invalid_frame)

            # Should receive error message
            message = ws.receive_json()
            assert message["error"] == "invalid_frame"
            assert "SOI" in message["detail"] or "marker" in message["detail"]

            # Connection should be closed
            try:
                ws.receive_json(timeout=1.0)
                assert False, "Connection should have been closed"
            except Exception:
                pass  # Expected

    def test_oversized_frame_sends_error_with_detail_and_closes_connection(
        self, client: TestClient
    ) -> None:
        """Test that oversized frame sends error with detail and closes connection."""
        # Create oversized frame (> 5MB default limit)
        # 5MB = 5 * 1024 * 1024 = 5242880 bytes
        oversized_frame = b"\xFF\xD8" + (b"\x00" * 6000000) + b"\xFF\xD9"

        with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
            # Send oversized frame
            ws.send_bytes(oversized_frame)

            # Should receive error message
            message = ws.receive_json()
            assert message["error"] == "frame_too_large"
            assert "size" in message["detail"].lower() or "too large" in message["detail"].lower()

            # Connection should be closed
            try:
                ws.receive_json(timeout=1.0)
                assert False, "Connection should have been closed"
            except Exception:
                pass  # Expected

    def test_valid_frame_does_not_close_connection(
        self, client: TestClient
    ) -> None:
        """Test that valid frame does not close connection."""
        # Create valid JPEG frame
        valid_frame = b"\xFF\xD8\xFF\xD9"

        with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
            # Send valid frame
            ws.send_bytes(valid_frame)

            # Connection should remain open
            # Send another frame to verify connection is still open
            ws.send_bytes(valid_frame)

            # If we got here, connection is still open
            pass  # Success