"""Tests for REST Pipeline Endpoint.

Phase 13 - Multi-Tool Linear Pipelines

These tests validate the /video/pipeline endpoint.
"""

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_rest_pipeline_executes_two_tools(client):
    """Test REST pipeline executes a 2-tool pipeline and returns structured output."""
    with patch(
        "app.services.video_pipeline_service.VideoPipelineService.run_pipeline"
    ) as mock_run:
        mock_run.return_value = {
            "result": {"detections": []},
            "steps": [
                {"tool": "detect_players", "output": {"detections": []}},
                {"tool": "track_players", "output": {"tracks": []}},
            ],
        }

        resp = await client.post(
            "/video/pipeline",
            json={
                "plugin_id": "test-plugin",
                "tools": ["detect_players", "track_players"],
                "payload": {"image_bytes": "AAA"},
            },
        )

        assert resp.status_code == 200
        data = resp.json()

        assert "result" in data
        assert "steps" in data
        assert len(data["steps"]) == 2
        assert data["steps"][0]["tool"] == "detect_players"
        assert data["steps"][1]["tool"] == "track_players"


@pytest.mark.asyncio
async def test_rest_pipeline_missing_tools(client):
    """Test REST pipeline returns 422 when tools[] is missing (validation error)."""
    resp = await client.post(
        "/video/pipeline",
        json={
            "plugin_id": "test-plugin",
            "payload": {"image_bytes": "AAA"},
        },
    )

    # FastAPI returns 422 for validation errors (missing required field)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_rest_pipeline_unknown_tool(client):
    """Test REST pipeline returns 400 when tool doesn't exist in plugin."""
    with patch(
        "app.services.video_pipeline_service.VideoPipelineService.run_pipeline"
    ) as mock_run:
        mock_run.side_effect = ValueError("Tool 'does_not_exist' not found in plugin 'test-plugin'")

        resp = await client.post(
            "/video/pipeline",
            json={
                "plugin_id": "test-plugin",
                "tools": ["does_not_exist"],
                "payload": {"image_bytes": "AAA"},
            },
        )

        # ValueError from service translates to 400 Bad Request
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_rest_pipeline_unknown_plugin(client):
    """Test REST pipeline returns 400 when plugin doesn't exist."""
    with patch(
        "app.services.video_pipeline_service.VideoPipelineService.run_pipeline"
    ) as mock_run:
        mock_run.side_effect = ValueError("Plugin 'unknown-plugin' not found")

        resp = await client.post(
            "/video/pipeline",
            json={
                "plugin_id": "unknown-plugin",
                "tools": ["detect_players"],
                "payload": {"image_bytes": "AAA"},
            },
        )

        # ValueError from service translates to 400 Bad Request
        assert resp.status_code == 400
