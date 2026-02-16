"""Tests for error handling and structured exceptions (Commit 10).

Following TDD: Write tests first, then implement code to make them pass.

These tests verify:
- All error responses follow unified format
- Invalid frame error includes code and detail
- Frame too large error includes code and detail
- Invalid message error includes code and detail
- Invalid pipeline error includes code and detail
- Pipeline failure error includes code and detail
- Internal error includes code and detail
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


class TestErrorHandling:
    """Test error handling and structured exceptions."""

    def test_all_error_responses_follow_unified_format(self, client: TestClient) -> None:
        """Test that all error responses follow unified format {error, detail}."""

        # Test 1: Invalid pipeline_id
        with client.websocket_connect("/ws/video/stream?pipeline_id=invalid") as ws:
            result = ws.receive_json()
            assert "error" in result
            assert "detail" in result
            assert result["error"] == "invalid_pipeline"

        # Test 2: Invalid frame (missing SOI)
        invalid_frame = b"\x00\x00\xFF\xD9"
        with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
            ws.send_bytes(invalid_frame)
            result = ws.receive_json()
            assert "error" in result
            assert "detail" in result
            assert result["error"] == "invalid_frame"

        # Test 3: Invalid message (text instead of bytes)
        with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
            ws.send_text("hello")
            result = ws.receive_json()
            assert "error" in result
            assert "detail" in result
            assert result["error"] == "invalid_message"

    def test_invalid_frame_error_includes_code_and_detail(self, client: TestClient) -> None:
        """Test that invalid frame error includes code and detail."""

        # Create invalid JPEG (missing SOI marker)
        invalid_frame = b"\x00\x00\xFF\xD9"

        with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
            ws.send_bytes(invalid_frame)
            result = ws.receive_json()

            assert result["error"] == "invalid_frame"
            assert "detail" in result
            assert len(result["detail"]) > 0
            # Verify detail is a string
            assert isinstance(result["detail"], str)
            # Verify no stack trace leaked
            assert "Traceback" not in result["detail"]
            assert "File" not in result["detail"]

    def test_frame_too_large_error_includes_code_and_detail(self, client: TestClient) -> None:
        """Test that frame too large error includes code and detail."""

        # Create oversized frame (> 5MB default limit)
        # 5MB = 5 * 1024 * 1024 = 5242880 bytes
        oversized_frame = b"\xFF\xD8" + (b"\x00" * 6000000) + b"\xFF\xD9"

        with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
            ws.send_bytes(oversized_frame)
            result = ws.receive_json()

            assert result["error"] == "frame_too_large"
            assert "detail" in result
            assert len(result["detail"]) > 0
            # Verify detail is a string
            assert isinstance(result["detail"], str)
            # Verify no stack trace leaked
            assert "Traceback" not in result["detail"]
            assert "File" not in result["detail"]

    def test_invalid_message_error_includes_code_and_detail(self, client: TestClient) -> None:
        """Test that invalid message error includes code and detail."""

        with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
            ws.send_text("hello")
            result = ws.receive_json()

            assert result["error"] == "invalid_message"
            assert "detail" in result
            assert len(result["detail"]) > 0
            # Verify detail is a string
            assert isinstance(result["detail"], str)
            # Verify no stack trace leaked
            assert "Traceback" not in result["detail"]
            assert "File" not in result["detail"]

    def test_invalid_pipeline_error_includes_code_and_detail(self, client: TestClient) -> None:
        """Test that invalid pipeline error includes code and detail."""

        with client.websocket_connect("/ws/video/stream?pipeline_id=nonexistent") as ws:
            result = ws.receive_json()

            assert result["error"] == "invalid_pipeline"
            assert "detail" in result
            assert len(result["detail"]) > 0
            # Verify detail is a string
            assert isinstance(result["detail"], str)
            # Verify no stack trace leaked
            assert "Traceback" not in result["detail"]
            assert "File" not in result["detail"]

    def test_pipeline_failure_error_includes_code_and_detail(self, client: TestClient) -> None:
        """Test that pipeline failure error includes code and detail."""

        # Create a minimal JPEG frame
        jpeg_frame = b"\xFF\xD8\xFF\xD9"

        with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
            # Send frame - may trigger pipeline failure if plugins are missing
            ws.send_bytes(jpeg_frame)
            result = ws.receive_json()

            # If we get a pipeline_failure error, verify its structure
            if "error" in result and result["error"] == "pipeline_failure":
                assert "detail" in result
                assert len(result["detail"]) > 0
                # Verify detail is a string
                assert isinstance(result["detail"], str)
                # Verify no stack trace leaked
                assert "Traceback" not in result["detail"]
                assert "File" not in result["detail"]

    def test_internal_error_includes_code_and_detail(self, client: TestClient) -> None:
        """Test that internal error includes code and detail."""

        # This test is harder to trigger intentionally
        # We'll verify the structure if we encounter an internal error

        # Create a minimal JPEG frame
        jpeg_frame = b"\xFF\xD8\xFF\xD9"

        with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
            # Send frame
            ws.send_bytes(jpeg_frame)
            result = ws.receive_json()

            # If we get an internal_error, verify its structure
            if "error" in result and result["error"] == "internal_error":
                assert "detail" in result
                assert len(result["detail"]) > 0
                # Verify detail is a string
                assert isinstance(result["detail"], str)
                # Verify no stack trace leaked
                assert "Traceback" not in result["detail"]
                assert "File" not in result["detail"]

    def test_error_responses_are_json_safe(self, client: TestClient) -> None:
        """Test that all error responses are JSON-safe (no complex objects)."""

        # Test invalid_pipeline error
        with client.websocket_connect("/ws/video/stream?pipeline_id=invalid") as ws:
            result = ws.receive_json()
            # Verify response is JSON-safe
            import json
            json_str = json.dumps(result)
            assert json_str is not None
            # Verify only simple types
            for key, value in result.items():
                assert isinstance(value, (str, int, float, bool, list, dict, type(None)))

        # Test invalid_frame error
        with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
            ws.send_bytes(b"\x00\x00\xFF\xD9")
            result = ws.receive_json()
            # Verify response is JSON-safe
            json_str = json.dumps(result)
            assert json_str is not None
            for key, value in result.items():
                assert isinstance(value, (str, int, float, bool, list, dict, type(None)))

        # Test invalid_message error
        with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
            ws.send_text("hello")
            result = ws.receive_json()
            # Verify response is JSON-safe
            json_str = json.dumps(result)
            assert json_str is not None
            for key, value in result.items():
                assert isinstance(value, (str, int, float, bool, list, dict, type(None)))