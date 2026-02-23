"""Tests for video_submit endpoint."""

from io import BytesIO
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api_routes.routes.video_submit import get_plugin_manager, get_plugin_service
from app.main import app


@pytest.fixture
def mock_plugin():
    """Create a mock plugin with tools attribute."""
    plugin = MagicMock()
    plugin.name = "yolo-tracker"
    plugin.tools = {
        "player_detection": {
            "handler": "player_detection_handler",
            "description": "Detect players",
            "input_types": ["video"],  # v0.9.5: Video input support
            "input_schema": {"properties": {"video_path": {"type": "string"}}},
            "output_schema": {"properties": {"detections": {"type": "array"}}},
        }
    }
    return plugin


@pytest.fixture
def mock_plugin_service(mock_plugin):
    """Create a mock plugin management service."""
    mock = MagicMock()
    mock.get_available_tools.return_value = list(mock_plugin.tools.keys())
    return mock


@pytest.fixture
def mock_plugin_registry(mock_plugin):
    """Create a mock plugin registry with a loaded plugin."""
    mock = MagicMock()
    mock.get.return_value = mock_plugin
    return mock


@pytest.mark.unit
def test_submit_video_success(
    session: Session, mock_plugin_registry, mock_plugin_service
):
    """Test video submission with valid MP4 file."""

    def override_get_plugin_manager():
        return mock_plugin_registry

    def override_get_plugin_service():
        return mock_plugin_service

    app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
    app.dependency_overrides[get_plugin_service] = override_get_plugin_service

    client = TestClient(app)

    # Create fake MP4 data with ftyp marker
    mp4_data = b"ftypmp42" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
        params={"plugin_id": "yolo-tracker", "tool": "player_detection"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data


@pytest.mark.unit
def test_submit_video_invalid_plugin(mock_plugin_service):
    """Test video submission with invalid plugin returns 400."""
    mock_registry = MagicMock()
    mock_registry.get.return_value = None  # Plugin not found

    def override_get_plugin_manager():
        return mock_registry

    def override_get_plugin_service():
        return mock_plugin_service

    app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
    app.dependency_overrides[get_plugin_service] = override_get_plugin_service

    client = TestClient(app)

    mp4_data = b"ftypmp42" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
        params={"plugin_id": "nonexistent", "tool": "player_detection"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400


@pytest.mark.unit
def test_submit_video_invalid_tool(mock_plugin, mock_plugin_registry):
    """Test video submission with invalid tool returns 400."""
    mock_service = MagicMock()
    mock_service.get_available_tools.return_value = ["different_tool"]

    def override_get_plugin_manager():
        return mock_plugin_registry

    def override_get_plugin_service():
        return mock_service

    app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
    app.dependency_overrides[get_plugin_service] = override_get_plugin_service

    client = TestClient(app)

    mp4_data = b"ftypmp42" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
        params={"plugin_id": "yolo-tracker", "tool": "invalid_tool"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400


@pytest.mark.unit
def test_submit_video_invalid_file_format(mock_plugin_registry, mock_plugin_service):
    """Test video submission with invalid file format returns 400."""

    def override_get_plugin_manager():
        return mock_plugin_registry

    def override_get_plugin_service():
        return mock_plugin_service

    app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
    app.dependency_overrides[get_plugin_service] = override_get_plugin_service

    client = TestClient(app)

    # Invalid file (no ftyp marker)
    invalid_data = b"INVALID VIDEO DATA"

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.txt", BytesIO(invalid_data))},
        params={"plugin_id": "yolo-tracker", "tool": "player_detection"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
