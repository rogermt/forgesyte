"""Tests for GET /plugins/{id}/manifest endpoint."""

import json
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.asyncio


async def test_get_plugin_manifest_success(client):
    """Test successfully retrieving plugin manifest."""
    # Mock the service to return a valid manifest
    expected_manifest = {
        "id": "test-plugin",
        "name": "Test Plugin",
        "version": "1.0.0",
        "description": "A test plugin",
        "tools": {
            "detect": {
                "description": "Detect objects",
                "inputs": {"frame_base64": "string"},
                "outputs": {"detections": "array"},
            }
        },
    }

    with patch(
        "app.services.plugin_management_service.PluginManagementService.get_plugin_manifest"
    ) as mock_get:
        mock_get.return_value = expected_manifest

        response = await client.get("/v1/plugins/test-plugin/manifest")

        assert response.status_code == 200
        assert response.json() == expected_manifest


async def test_get_plugin_manifest_not_found(client):
    """Test 404 when plugin doesn't exist."""
    with patch(
        "app.services.plugin_management_service.PluginManagementService.get_plugin_manifest"
    ) as mock_get:
        mock_get.return_value = None

        response = await client.get("/v1/plugins/nonexistent/manifest")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


async def test_get_plugin_manifest_invalid_json(client):
    """Test 500 when manifest.json is invalid."""
    with patch(
        "app.services.plugin_management_service.PluginManagementService.get_plugin_manifest"
    ) as mock_get:
        # Simulate invalid JSON error
        mock_get.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        response = await client.get("/v1/plugins/bad-plugin/manifest")

        assert response.status_code == 500


async def test_get_plugin_manifest_schema(client):
    """Test that manifest follows expected schema."""
    expected_manifest = {
        "id": "yolo-tracker",
        "name": "YOLO Tracker",
        "version": "1.0.0",
        "tools": {
            "player_detection": {
                "description": "Detect players",
                "inputs": {
                    "frame_base64": "string",
                    "device": "string",
                    "annotated": "boolean",
                },
                "outputs": {"detections": "array", "annotated_frame_base64": "string?"},
            }
        },
    }

    with patch(
        "app.services.plugin_management_service.PluginManagementService.get_plugin_manifest"
    ) as mock_get:
        mock_get.return_value = expected_manifest

        response = await client.get("/v1/plugins/yolo-tracker/manifest")

        assert response.status_code == 200
        manifest = response.json()

        # Verify schema
        assert "id" in manifest
        assert "tools" in manifest
        assert "player_detection" in manifest["tools"]

        tool = manifest["tools"]["player_detection"]
        assert "description" in tool
        assert "inputs" in tool
        assert "outputs" in tool
