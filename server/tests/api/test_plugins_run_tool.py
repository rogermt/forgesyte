"""Tests for POST /plugins/{id}/tools/{tool}/run endpoint."""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.asyncio


async def test_run_plugin_tool_success(client):
    """Test successfully running a plugin tool."""
    expected_result = {
        "detections": [{"x1": 100, "y1": 200, "x2": 150, "y2": 350, "confidence": 0.92}]
    }

    with patch(
        "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
    ) as mock_run:
        mock_run.return_value = expected_result

        response = await client.post(
            "/v1/plugins/test-plugin/tools/detect/run",
            json={
                "tools": ["detect"],
                "args": {"frame_base64": "iVBORw0K...", "device": "cpu"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tool_name"] == "detect"
        assert data["plugin_id"] == "test-plugin"
        assert data["result"] == expected_result
        assert data["processing_time_ms"] >= 0


async def test_run_plugin_tool_not_found(client):
    """Test 404 when plugin doesn't exist."""
    with patch(
        "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
    ) as mock_run:
        mock_run.side_effect = ValueError("Plugin 'nonexistent' not found")

        response = await client.post(
            "/v1/plugins/nonexistent/tools/detect/run",
            json={
                "tools": ["detect"],
                "args": {"frame_base64": "iVBORw0K..."},
            },
        )

        assert response.status_code == 400


async def test_run_plugin_tool_invalid_args(client):
    """Test 400 when invalid arguments provided."""
    with patch(
        "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
    ) as mock_run:
        mock_run.side_effect = ValueError("Invalid arguments for tool 'detect'")

        response = await client.post(
            "/v1/plugins/test-plugin/tools/detect/run",
            json={
                "tools": ["detect"],
                "args": {"missing_required_arg": "value"},
            },
        )

        assert response.status_code == 400


async def test_run_plugin_tool_timeout(client):
    """Test 408 when tool execution times out."""
    with patch(
        "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
    ) as mock_run:
        mock_run.side_effect = TimeoutError("Tool execution exceeded timeout")

        response = await client.post(
            "/v1/plugins/test-plugin/tools/slow_detect/run",
            json={
                "tools": ["slow_detect"],
                "args": {"frame_base64": "iVBORw0K..."},
            },
        )

        assert response.status_code == 408


async def test_run_plugin_tool_unexpected_error(client):
    """Test 500 on unexpected error."""
    with patch(
        "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
    ) as mock_run:
        mock_run.side_effect = Exception("Model loading failed")

        response = await client.post(
            "/v1/plugins/test-plugin/tools/detect/run",
            json={
                "tools": ["detect"],
                "args": {"frame_base64": "iVBORw0K..."},
            },
        )

        assert response.status_code == 500


async def test_run_plugin_tool_response_schema(client):
    """Test response has correct schema."""
    expected_result = {"detections": [], "annotated_frame_base64": None}

    with patch(
        "app.services.plugin_management_service.PluginManagementService.run_plugin_tool"
    ) as mock_run:
        mock_run.return_value = expected_result

        response = await client.post(
            "/v1/plugins/yolo-tracker/tools/player_detection/run",
            json={
                "tools": ["player_detection"],
                "args": {
                    "frame_base64": "iVBORw0K...",
                    "device": "cpu",
                    "annotated": False,
                },
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response schema
        assert "tool_name" in data
        assert "plugin_id" in data
        assert "result" in data
        assert "processing_time_ms" in data

        # Verify values
        assert data["tool_name"] == "player_detection"
        assert data["plugin_id"] == "yolo-tracker"
        assert data["result"] == expected_result
        assert isinstance(data["processing_time_ms"], int)
