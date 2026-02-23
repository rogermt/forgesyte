"""Tests ensuring tool validation uses Plugin.tools, not manifest.json.

This test validates the fix from docs/releases/v0.9.3/TOOL_CHECK_FIX.md:
- Plugin class defines actual tools in Plugin.tools attribute
- Manifest.json defines lifecycle methods (on_load, run_tool, etc.)
- Endpoints must validate against Plugin.tools, NOT manifest.json

v0.9.5 Update:
- input_types is read from manifest.json, not plugin.tools
- plugin.tools uses ToolSchema which forbids input_types (extra="forbid")
"""

from io import BytesIO
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api_routes.routes.image_submit import get_plugin_manager, get_plugin_service
from app.api_routes.routes.video_submit import (
    get_plugin_manager as get_video_plugin_manager,
)
from app.api_routes.routes.video_submit import (
    get_plugin_service as get_video_plugin_service,
)
from app.main import app
from app.models.job import Job


class FakePlugin:
    """Fake plugin with tools attribute for testing.

    NOTE: plugin.tools uses ToolSchema which forbids input_types (extra="forbid").
    So we don't include input_types here - it comes from the manifest.
    """

    name = "test-plugin"
    tools = {
        "player_detection": {
            "handler": "dummy_handler",
            "description": "Detect players",
            "input_schema": {"properties": {"video_path": {"type": "string"}}},
            "output_schema": {"properties": {"detections": {"type": "array"}}},
        },
        "analyze": {
            "handler": "dummy_handler",
            "description": "Extract text from images",
            "input_schema": {"properties": {"image_bytes": {"type": "string"}}},
            "output_schema": {"properties": {"text": {"type": "string"}}},
        },
    }

    def dummy_handler(self, *args, **kwargs):
        return {"result": "ok"}


@pytest.fixture
def mock_manifest():
    """Create a mock manifest with input_types.

    The manifest.json file contains input_types which plugin.tools cannot have
    due to ToolSchema's extra="forbid" restriction.
    """
    return {
        "id": "test-plugin",
        "name": "Test Plugin",
        "version": "1.0.0",
        "tools": [
            {
                "id": "player_detection",
                "title": "Player Detection",
                "description": "Detect players",
                "input_types": ["video"],
                "output_types": ["detections"],
            },
            {
                "id": "analyze",
                "title": "Analyze",
                "description": "Extract text from images",
                "input_types": ["image_bytes"],
                "output_types": ["text"],
            },
        ],
    }


@pytest.fixture
def mock_plugin_registry():
    """Create a mock plugin registry with fake plugin."""
    mock = MagicMock()
    mock.get.return_value = FakePlugin()
    mock.list.return_value = {"test-plugin": FakePlugin()}
    return mock


@pytest.fixture
def mock_plugin_service(mock_plugin_registry, mock_manifest):
    """Create a mock plugin service with manifest support."""
    mock = MagicMock()
    mock.get_available_tools.return_value = list(FakePlugin.tools.keys())
    mock.get_plugin_manifest.return_value = mock_manifest
    return mock


@pytest.mark.unit
def test_image_submit_validates_against_plugin_tools(
    session: Session, mock_plugin_service, mock_plugin_registry
):
    """Ensure image_submit validates tool against Plugin.tools, not manifest."""

    def override_get_plugin_manager():
        return mock_plugin_registry

    def override_get_plugin_service():
        return mock_plugin_service

    app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
    app.dependency_overrides[get_plugin_service] = override_get_plugin_service

    client = TestClient(app)

    try:
        # Valid tool from Plugin.tools
        jpeg_data = b"\xFF\xD8\xFF" + b"\x00" * 100
        response = client.post(
            "/v1/image/submit",
            files={"file": ("test.jpg", BytesIO(jpeg_data))},
            params={"plugin_id": "test-plugin", "tool": "analyze"},
        )
        assert response.status_code == 200

        # Verify job was created
        job_id = response.json()["job_id"]
        job = session.query(Job).filter(Job.job_id == job_id).first()
        assert job is not None

        # Invalid tool (not in Plugin.tools)
        response = client.post(
            "/v1/image/submit",
            files={"file": ("test.jpg", BytesIO(jpeg_data))},
            params={"plugin_id": "test-plugin", "tool": "on_load"},  # lifecycle method
        )
        assert response.status_code == 400
        assert "Available:" in response.json()["detail"]
        assert "analyze" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
def test_video_submit_validates_against_plugin_tools(
    session: Session, mock_plugin_service, mock_plugin_registry
):
    """Ensure video_submit validates tool against Plugin.tools, not manifest."""

    def override_get_plugin_manager():
        return mock_plugin_registry

    def override_get_plugin_service():
        return mock_plugin_service

    app.dependency_overrides[get_video_plugin_manager] = override_get_plugin_manager
    app.dependency_overrides[get_video_plugin_service] = override_get_plugin_service

    client = TestClient(app)

    try:
        # Valid tool from Plugin.tools
        mp4_data = b"ftypmp42" + b"\x00" * 100
        response = client.post(
            "/v1/video/submit",
            files={"file": ("test.mp4", BytesIO(mp4_data))},
            params={"plugin_id": "test-plugin", "tool": "player_detection"},
        )
        assert response.status_code == 200

        # Verify job was created
        job_id = response.json()["job_id"]
        job = session.query(Job).filter(Job.job_id == job_id).first()
        assert job is not None

        # Invalid tool (not in Plugin.tools)
        response = client.post(
            "/v1/video/submit",
            files={"file": ("test.mp4", BytesIO(mp4_data))},
            params={"plugin_id": "test-plugin", "tool": "run_tool"},  # lifecycle method
        )
        assert response.status_code == 400
        assert "Available:" in response.json()["detail"]
        assert "player_detection" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.unit
def test_get_available_tools_returns_plugin_tools_keys(mock_plugin_service):
    """Test that get_available_tools returns keys from Plugin.tools."""
    tools = mock_plugin_service.get_available_tools("test-plugin")
    assert isinstance(tools, list)
    assert "player_detection" in tools
    assert "analyze" in tools
    assert "on_load" not in tools  # lifecycle method should NOT be in tools
