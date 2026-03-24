"""Tests for websocket_router.py - Phase 10 real-time communication."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.realtime.websocket_router import connection_manager, router


@pytest.fixture
def app():
    """Create a FastAPI app with the realtime router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.mark.unit
class TestWebsocketEndpointConnection:
    """Tests for WebSocket endpoint connection."""

    def test_websocket_endpoint_accepts_connection(self, client: TestClient) -> None:
        """Test that /v1/realtime endpoint accepts connections."""
        with client.websocket_connect("/v1/realtime") as websocket:
            # Connection should be established
            assert websocket is not None

    def test_websocket_endpoint_with_session_id(self, client: TestClient) -> None:
        """Test WebSocket connection with custom session_id."""
        with client.websocket_connect(
            "/v1/realtime?session_id=test-session-123"
        ) as websocket:
            assert websocket is not None

    def test_websocket_endpoint_without_session_id(self, client: TestClient) -> None:
        """Test WebSocket connection without session_id uses default."""
        with client.websocket_connect("/v1/realtime") as websocket:
            assert websocket is not None


@pytest.mark.unit
class TestWebsocketMessageHandling:
    """Tests for WebSocket message handling."""

    def test_websocket_echoes_message(self, client: TestClient) -> None:
        """Test that WebSocket echoes back messages with ack type."""
        with client.websocket_connect("/v1/realtime") as websocket:
            test_message = {"type": "test", "data": "hello"}
            websocket.send_json(test_message)

            response = websocket.receive_json()

            assert response["type"] == "ack"
            assert "payload" in response
            assert response["payload"]["original"] == test_message
            assert "timestamp" in response

    def test_websocket_handles_multiple_messages(self, client: TestClient) -> None:
        """Test that WebSocket handles multiple messages in sequence."""
        with client.websocket_connect("/v1/realtime") as websocket:
            for i in range(3):
                message = {"type": "test", "count": i}
                websocket.send_json(message)
                response = websocket.receive_json()
                assert response["type"] == "ack"
                assert response["payload"]["original"] == message

    def test_websocket_message_with_complex_payload(self, client: TestClient) -> None:
        """Test WebSocket handles complex nested JSON payloads."""
        with client.websocket_connect("/v1/realtime") as websocket:
            complex_message = {
                "type": "frame",
                "frame_id": "frame-123",
                "data": {
                    "image": "base64data",
                    "metadata": {"width": 640, "height": 480},
                },
            }
            websocket.send_json(complex_message)
            response = websocket.receive_json()

            assert response["type"] == "ack"
            assert response["payload"]["original"] == complex_message


@pytest.mark.unit
class TestWebsocketConnectionManager:
    """Tests for ConnectionManager integration."""

    def test_connection_manager_tracks_connections(self, client: TestClient) -> None:
        """Test that ConnectionManager tracks active connections."""
        # Clear any existing connections
        connection_manager.active_connections.clear()

        with client.websocket_connect("/v1/realtime?session_id=session-1"):
            # Connection should be tracked
            assert connection_manager.is_connected("session-1")

        # After disconnect, should no longer be tracked
        assert not connection_manager.is_connected("session-1")

        def test_connection_manager_tracks_multiple_sessions(
            self, client: TestClient
        ) -> None:
            """Test ConnectionManager tracks multiple concurrent sessions."""

            connection_manager.active_connections.clear()

            with client.websocket_connect("/v1/realtime?session_id=session-a"):

                with client.websocket_connect("/v1/realtime?session_id=session-b"):

                    assert connection_manager.is_connected("session-a")

                    assert connection_manager.is_connected("session-b")

                    assert len(connection_manager.get_active_connections()) == 2

            # Both should be disconnected after context exits

            assert not connection_manager.is_connected("session-a")

            assert not connection_manager.is_connected("session-b")


@pytest.mark.unit
class TestWebsocketTimestamp:
    """Tests for timestamp in WebSocket responses."""

    def test_timestamp_in_iso_format(self, client: TestClient) -> None:
        """Test that timestamp is in ISO format with timezone."""
        with client.websocket_connect("/v1/realtime") as websocket:
            websocket.send_json({"type": "test"})
            response = websocket.receive_json()

            timestamp = response["timestamp"]
            # ISO format should contain 'T' separator
            assert "T" in timestamp
            # Should end with timezone (e.g., +00:00 or Z)
            assert "+" in timestamp or timestamp.endswith("Z")


@pytest.mark.unit
class TestWebsocketDisconnect:
    """Tests for WebSocket disconnect handling."""

    def test_graceful_disconnect(self, client: TestClient) -> None:
        """Test that disconnect is handled gracefully without errors."""
        connection_manager.active_connections.clear()

        with client.websocket_connect(
            "/v1/realtime?session_id=graceful-test"
        ) as websocket:
            websocket.send_json({"type": "test"})
            response = websocket.receive_json()
            assert response["type"] == "ack"

        # After context exit, connection should be cleaned up
        assert not connection_manager.is_connected("graceful-test")
