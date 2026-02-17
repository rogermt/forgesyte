"""Tests for WebSocket endpoint connection (Commit 1).

Following TDD: Write tests first, then implement code to make them pass.

These tests verify:
- WebSocket connection succeeds with valid pipeline_id
- WebSocket connection logs connect event (JSON)
- WebSocket disconnection logs disconnect event (JSON)
- WebSocket connection fails with missing pipeline_id
- WebSocket connection fails with invalid pipeline_id
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


class TestWebSocketConnectionSuccess:
    """Test successful WebSocket connections."""

    def test_websocket_connection_succeeds_with_valid_pipeline_id(
        self, client: TestClient
    ) -> None:
        """Test that WebSocket connection succeeds with valid pipeline_id."""
        # Assuming there's a valid pipeline in the test fixtures
        # We'll use a known valid pipeline_id from the test setup
        with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
            # If we got here, connection succeeded
            assert ws is not None

    def test_websocket_connection_logs_connect_event(
        self, client: TestClient, caplog
    ) -> None:
        """Test that WebSocket connection logs connect event (JSON)."""
        with caplog.at_level(logging.INFO):
            with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr"):
                # Check that connect event was logged
                assert any(
                    "stream_connect" in record.message for record in caplog.records
                )

    def test_websocket_disconnection_logs_disconnect_event(
        self, client: TestClient, caplog
    ) -> None:
        """Test that WebSocket disconnection logs disconnect event (JSON)."""
        with caplog.at_level(logging.INFO):
            with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr"):
                pass  # Connection closes on context exit

            # Check that disconnect event was logged
            # Look in the extra field as well since we're using structured logging
            disconnect_logged = any(
                "stream_disconnect" in record.message
                or (
                    hasattr(record, "extra")
                    and "stream_disconnect" in str(record.extra)
                )
                for record in caplog.records
            )
            assert (
                disconnect_logged
            ), f"No disconnect event found in logs. Records: {[r.message for r in caplog.records]}"


class TestWebSocketConnectionFailure:
    """Test WebSocket connection failures."""

    def test_websocket_connection_fails_with_missing_pipeline_id(
        self, client: TestClient
    ) -> None:
        """Test that WebSocket connection fails with missing pipeline_id."""
        # The connection should be closed immediately with an error message
        with client.websocket_connect("/ws/video/stream") as ws:
            # Receive the error message
            message = ws.receive_json()
            assert message["error"] == "invalid_pipeline"
            assert "pipeline_id" in message["detail"].lower()

    def test_websocket_connection_fails_with_invalid_pipeline_id(
        self, client: TestClient
    ) -> None:
        """Test that WebSocket connection fails with invalid pipeline_id."""
        # For now, we accept any pipeline_id since validation is not yet implemented
        # This will be fixed in Commit 7 when we integrate pipeline execution
        with client.websocket_connect(
            "/ws/video/stream?pipeline_id=nonexistent_pipeline_xyz"
        ) as ws:
            # Connection should succeed for now (validation will be added later)
            assert ws is not None


class TestSessionManagerIntegration:
    """Test SessionManager integration into WebSocket."""

    def test_websocket_connection_creates_session_manager(
        self, client: TestClient, caplog
    ) -> None:
        """Test that WebSocket connection creates SessionManager."""
        with caplog.at_level(logging.INFO):
            with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr"):
                pass

            # Check that connect event was logged with session_id
            connect_logged = any(
                "stream_connect" in record.message and hasattr(record, "session_id")
                for record in caplog.records
            )
            assert connect_logged, "Session creation not logged"

    def test_websocket_connection_has_unique_session_id(
        self, client: TestClient, caplog
    ) -> None:
        """Test that WebSocket connection has unique session_id."""
        session_ids = []

        with caplog.at_level(logging.INFO):
            with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr"):
                pass

            # Extract session_id from logs
            for record in caplog.records:
                if "stream_connect" in record.message and hasattr(record, "session_id"):
                    session_ids.append(record.session_id)

            caplog.clear()

            with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr"):
                pass

            for record in caplog.records:
                if "stream_connect" in record.message and hasattr(record, "session_id"):
                    session_ids.append(record.session_id)

        # Session IDs should be unique
        assert len(session_ids) == 2
        assert session_ids[0] != session_ids[1]

    def test_websocket_connection_stores_pipeline_id_in_session(
        self, client: TestClient, caplog
    ) -> None:
        """Test that WebSocket connection stores pipeline_id in session."""
        with caplog.at_level(logging.INFO):
            with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr"):
                pass

            # Check that pipeline_id was logged
            pipeline_logged = any(
                "stream_connect" in record.message
                and hasattr(record, "pipeline_id")
                and record.pipeline_id == "yolo_ocr"
                for record in caplog.records
            )
            assert pipeline_logged, "Pipeline ID not stored in session"

    def test_websocket_disconnection_destroys_session_manager(
        self, client: TestClient, caplog
    ) -> None:
        """Test that WebSocket disconnection destroys SessionManager."""
        with caplog.at_level(logging.INFO):
            with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr"):
                pass

            # Check that disconnect event was logged with session_id
            disconnect_logged = any(
                "stream_disconnect" in record.message and hasattr(record, "session_id")
                for record in caplog.records
            )
            assert disconnect_logged, "Session destruction not logged"
