"""Tests for REST Pipeline Endpoint.

Phase 13 - Multi-Tool Linear Pipelines

These tests verify that the /video/pipeline endpoint validates request structure.
The endpoint will execute pipelines via VideoPipelineService in Phase 13.
"""

from fastapi.testclient import TestClient


def test_post_video_pipeline(app_with_plugins):
    """Test POST /video/pipeline returns 200 with result."""
    from unittest.mock import patch

    client = TestClient(app_with_plugins)

    with patch(
        "app.routes_pipeline.PluginManagementService.run_plugin_tool"
    ) as mock_run:
        mock_run.return_value = {
            "tool": "detect_players",
            "step_completed": "detect_players",
        }

        response = client.post(
            "/video/pipeline",
            json={
                "plugin_id": "test-plugin",
                "tools": ["detect_players"],
                "payload": {"test": "data"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "steps" in data
        assert len(data["steps"]) == 1


def test_pipeline_missing_plugin_id_returns_422(app_with_plugins):
    """Test validation error when plugin_id is missing."""
    client = TestClient(app_with_plugins)
    response = client.post(
        "/video/pipeline",
        json={
            "tools": ["detect_players"],
            "payload": {"test": "data"},
        },
    )

    assert response.status_code == 422


def test_pipeline_missing_tools_returns_422(app_with_plugins):
    """Test validation error when tools is missing."""
    client = TestClient(app_with_plugins)
    response = client.post(
        "/video/pipeline",
        json={
            "plugin_id": "test-plugin",
            "payload": {"test": "data"},
        },
    )

    assert response.status_code == 422


def test_pipeline_empty_tools_returns_200_with_empty_result(app_with_plugins):
    """Test that empty tools list returns 200 with empty steps."""
    client = TestClient(app_with_plugins)

    response = client.post(
        "/video/pipeline",
        json={
            "plugin_id": "test-plugin",
            "tools": [],
            "payload": {"test": "data"},
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["result"] == {}
    assert data["steps"] == []
