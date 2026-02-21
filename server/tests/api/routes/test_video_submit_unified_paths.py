"""Test video submit endpoint unified paths for v0.9.2.

Tests that:
1. Video submit endpoint uses video/input/ storage paths
2. Video submit endpoint creates job with job_type="video"
3. Video submit endpoint saves file to data/jobs/video/input/
"""

from io import BytesIO
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api_routes.routes.video_submit import get_plugin_manager, get_plugin_service
from app.main import app
from app.models.job import Job
from app.services.storage.local_storage import LocalStorageService


@pytest.fixture
def mock_plugin_service():
    """Create a mock plugin management service."""
    mock = MagicMock()
    mock.get_plugin_manifest.return_value = {
        "tools": [
            {
                "id": "detect_objects",
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
        name="yolo",
        description="YOLO Tracker",
        version="1.0.0",
    )
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


def test_video_submit_creates_job_with_video_type(client_with_mocks, session: Session):
    """Test that video submit creates job with job_type='video'."""
    # Create a fake MP4 video
    fake_mp4 = b"ftyp" + b"\x00" * 100

    response = client_with_mocks.post(
        "/v1/video/submit?plugin_id=yolo&tool=detect_objects",
        files={"file": ("test.mp4", BytesIO(fake_mp4), "video/mp4")},
    )

    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # Verify job was created with job_type="video"
    # Use the session fixture which is connected to the test database
    job = session.query(Job).filter(Job.job_id == job_id).first()
    assert job is not None
    assert job.job_type == "video"
    assert job.plugin_id == "yolo"
    assert job.tool == "detect_objects"
    assert job.status.value == "pending"


def test_video_submit_saves_to_video_input(client_with_mocks, session: Session):
    """Test that video submit saves file to video/input/."""

    # Create a fake MP4 video
    fake_mp4 = b"ftyp" + b"\x00" * 100

    response = client_with_mocks.post(
        "/v1/video/submit?plugin_id=yolo&tool=detect_objects",
        files={"file": ("test.mp4", BytesIO(fake_mp4), "video/mp4")},
    )

    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # Verify file was saved to storage
    storage = LocalStorageService()
    
    # Use the session fixture which is connected to the test database
    job = session.query(Job).filter(Job.job_id == job_id).first()
    assert job is not None

    # Verify input_path starts with "video/input/"
    assert job.input_path.startswith("video/input/")
    assert job.input_path == f"video/input/{job_id}.mp4"

    # Verify file exists under data/jobs/video/input/
    file_path = storage.load_file(job.input_path)
    assert file_path.exists()
    assert "video/input" in str(file_path)

    # Verify file content
    with open(file_path, "rb") as f:
        saved_content = f.read()
    assert saved_content == fake_mp4


def test_video_submit_invalid_file(client_with_mocks):
    """Test submitting an invalid video file."""
    # Create a fake invalid file
    fake_file = b"this is not a video"

    response = client_with_mocks.post(
        "/v1/video/submit?plugin_id=yolo&tool=detect_objects",
        files={"file": ("test.txt", BytesIO(fake_file), "text/plain")},
    )

    assert response.status_code == 400
    assert "Invalid MP4 file" in response.json()["detail"]


def test_video_submit_invalid_plugin(mock_plugin_service):
    """Test submitting with non-existent plugin."""
    # Create a mock that returns None for invalid plugin
    mock_registry = MagicMock()
    mock_registry.get.return_value = None  # Plugin not found

    def override_get_plugin_manager():
        return mock_registry

    def override_get_plugin_service():
        return mock_plugin_service

    app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
    app.dependency_overrides[get_plugin_service] = override_get_plugin_service

    client = TestClient(app)

    fake_mp4 = b"ftyp" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit?plugin_id=nonexistent&tool=detect_objects",
        files={"file": ("test.mp4", BytesIO(fake_mp4), "video/mp4")},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


def test_video_submit_invalid_tool(mock_plugin_registry):
    """Test submitting with non-existent tool."""
    # Create a mock service that doesn't have the tool
    mock_service = MagicMock()
    mock_service.get_plugin_manifest.return_value = {
        "tools": [
            {
                "id": "different_tool",  # Not detect_objects
                "inputs": ["video_path"],
            }
        ]
    }

    def override_get_plugin_manager():
        return mock_plugin_registry

    def override_get_plugin_service():
        return mock_service

    app.dependency_overrides[get_plugin_manager] = override_get_plugin_manager
    app.dependency_overrides[get_plugin_service] = override_get_plugin_service

    client = TestClient(app)

    fake_mp4 = b"ftyp" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit?plugin_id=yolo&tool=nonexistent_tool",
        files={"file": ("test.mp4", BytesIO(fake_mp4), "video/mp4")},
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()
