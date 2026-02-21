"""Tests for video submission endpoint unified paths.

Tests verify:
1. Jobs are created with job_type="video"
2. Files are saved to video/input/ path
3. Invalid files are rejected
"""

from io import BytesIO
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api_routes.routes.video_submit import get_plugin_manager, get_plugin_service
from app.main import app
from app.models.job import Job


@pytest.fixture
def mock_plugin():
    """Create a mock plugin with tools attribute."""
    plugin = MagicMock()
    plugin.name = "yolo-tracker"
    plugin.tools = {
        "player_detection": {
            "handler": "player_detection_handler",
            "description": "Detect players",
            "input_schema": {"properties": {"video_path": {"type": "string"}}},
            "output_schema": {},
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


@pytest.fixture
def client_with_mocks(mock_plugin_registry, mock_plugin_service):
    """Create a test client with mocked dependencies."""
    def override_get_plugin_manager():
        return mock_plugin_registry

    def override_get_plugin_service():
        return mock_plugin_service

    app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
    app.dependency_overrides[get_plugin_service] = override_get_plugin_service

    yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.mark.unit
def test_video_submit_creates_job_with_video_type(
    session: Session, client_with_mocks
):
    """Test that video submit creates a job with job_type='video'."""
    mp4_data = b"ftypmp42" + b"\x00" * 100

    response = client_with_mocks.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
        params={"plugin_id": "yolo-tracker", "tool": "player_detection"},
    )

    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # Check database
    job = session.query(Job).filter(Job.job_id == job_id).first()
    assert job is not None
    assert job.job_type == "video"


@pytest.mark.unit
def test_video_submit_saves_to_video_input(
    session: Session, client_with_mocks
):
    """Test that video is saved to video/input/ path."""
    mp4_data = b"ftypmp42" + b"\x00" * 100

    response = client_with_mocks.post(
        "/v1/video/submit",
        files={"file": ("test.mp4", BytesIO(mp4_data))},
        params={"plugin_id": "yolo-tracker", "tool": "player_detection"},
    )

    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # Check database
    job = session.query(Job).filter(Job.job_id == job_id).first()
    assert job is not None
    assert job.input_path.startswith("video/input/")


@pytest.mark.unit
def test_video_submit_invalid_file(client_with_mocks):
    """Test that invalid MP4 files are rejected."""
    invalid_data = b"NOT AN MP4 FILE"

    response = client_with_mocks.post(
        "/v1/video/submit",
        files={"file": ("test.txt", BytesIO(invalid_data))},
        params={"plugin_id": "yolo-tracker", "tool": "player_detection"},
    )

    assert response.status_code == 400
    assert "Invalid MP4" in response.json()["detail"]
