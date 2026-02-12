"""Tests for REST Pipeline Endpoint.

Phase 13 - Multi-Tool Linear Pipelines

These tests verify that the /video/pipeline endpoint validates request structure.
The endpoint will execute pipelines via VideoPipelineService in Phase 13.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.skip(
    reason="Phase 13: Endpoints will be implemented when VideoPipelineService is ready"
)
def test_post_video_pipeline(app_with_plugins):
    """Test POST /video/pipeline returns 200 with result."""
    client = TestClient(app_with_plugins)
    response = client.post(
        "/video/pipeline",
        json={
            "plugin_id": "test-plugin",
            "tools": ["detect_players"],
            "payload": {"test": "data"},
        },
    )

    assert response.status_code == 200
    assert "result" in response.json()


@pytest.mark.skip(
    reason="Phase 13: Validation will be tested when endpoint is implemented"
)
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


@pytest.mark.skip(
    reason="Phase 13: Validation will be tested when endpoint is implemented"
)
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


@pytest.mark.skip(
    reason="Phase 13: Validation will be tested when endpoint is implemented"
)
def test_pipeline_empty_tools_returns_422(app_with_plugins):
    """Test validation error when tools is empty list."""
    client = TestClient(app_with_plugins)
    response = client.post(
        "/video/pipeline",
        json={
            "plugin_id": "test-plugin",
            "tools": [],
            "payload": {"test": "data"},
        },
    )

    assert response.status_code == 422
