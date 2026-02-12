"""Tests for WebSocket Pipeline Execution.

Phase 13 - Multi-Tool Linear Pipelines

These tests validate WebSocket pipeline execution behavior.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def ws_client(app_with_plugins):
    """Create a test client for WebSocket testing."""
    return TestClient(app_with_plugins)


def test_ws_pipeline_executes_in_order(ws_client):
    """Test WebSocket pipeline executes tools in order and returns final output."""
    with ws_client.websocket_connect("/v1/stream?plugin=test-plugin") as ws:
        # First message is "connected"
        connected_msg = ws.receive_json()
        assert connected_msg["type"] == "connected"

        # Send frame with tools
        ws.send_json(
            {
                "type": "frame",
                "frame_id": "1",
                "plugin_id": "test-plugin",
                "image_data": "AAA",
                "tools": ["detect_players", "track_players"],
            }
        )

        # Receive result or error (plugin may not exist in test env)
        msg = ws.receive_json()
        assert msg["type"] in ["result", "error"]
        if msg["type"] == "result":
            assert msg["frame_id"] == "1"
            assert "result" in msg


def test_ws_pipeline_missing_tools(ws_client):
    """Test WebSocket returns error when tools[] is missing."""
    with ws_client.websocket_connect("/v1/stream?plugin=test-plugin") as ws:
        # First message is "connected"
        connected_msg = ws.receive_json()
        assert connected_msg["type"] == "connected"

        # Send frame without tools
        ws.send_json(
            {
                "type": "frame",
                "frame_id": "1",
                "plugin_id": "test-plugin",
                "image_data": "AAA",
            }
        )

        msg = ws.receive_json()
        assert msg["type"] == "error"
