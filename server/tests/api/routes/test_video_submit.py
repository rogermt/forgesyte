"""Tests for video submission endpoint."""

from io import BytesIO
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api_routes.routes.video_submit import get_plugin_manager, get_plugin_service
from app.main import app


@pytest.fixture
def mock_plugin_service():
    """Create a mock plugin management service."""
    mock = MagicMock()
    mock.get_plugin_manifest.return_value = {
        "tools": [
            {
                "id": "video_track",
                "inputs": ["video_path"],
            }
        ]
    }
    return mock


@pytest.fixture
def mock_plugin_registry():
    """Create a mock plugin registry with a loaded plugin."""
    mock = MagicMock()
    mock.get.return_value = MagicMock(
        name="yolo-tracker",
        description="YOLO Tracker",
        version="1.0.0",
    )
    return mock


@pytest.mark.unit
def test_submit_video_success(session, mock_plugin_registry, mock_plugin_service):
    """Test successful video submission."""
    # Override dependencies
    def override_get_plugin_manager():
        return mock_plugin_registry

    def override_get_plugin_service():
        return mock_plugin_service

    app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
    app.dependency_overrides[get_plugin_service] = override_get_plugin_service

    client = TestClient(app)

    # Create a fake MP4 file (magic bytes: ftyp)
    mp4_data = b"ftypmp42" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
        params={"plugin_id": "yolo-tracker", "tool": "video_track"},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "job_id" in response.json()


@pytest.mark.unit
def test_submit_video_invalid_mp4():
    """Test submission with invalid MP4 file."""
    client = TestClient(app)

    # Invalid file (no ftyp magic bytes)
    invalid_data = b"invalid video data"

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(invalid_data))},
        params={"plugin_id": "yolo-tracker", "tool": "video_track"},
    )

    assert response.status_code == 400


@pytest.mark.unit
def test_submit_video_missing_plugin_id():
    """Test submission without plugin_id returns 422."""
    client = TestClient(app)

    mp4_data = b"ftypmp42" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
    )

    # Should fail because plugin_id is required
    assert response.status_code == 422
