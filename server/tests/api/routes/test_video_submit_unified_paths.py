"""Test video submit endpoint unified paths for v0.9.2.

Tests that:
1. Video submit endpoint uses video/input/ storage paths
2. Video submit endpoint creates job with job_type="video"
3. Video submit endpoint saves file to data/jobs/video/input/
"""

from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.job import Job
from app.services.storage.local_storage import LocalStorageService


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_video_submit_creates_job_with_video_type(client):
    """Test that video submit creates job with job_type='video'."""
    from app.core.database import SessionLocal
    from app.models.job import Job

    # Create a fake MP4 video
    fake_mp4 = b"ftyp" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit?plugin_id=yolo&tool=detect_objects",
        files={"file": ("test.mp4", BytesIO(fake_mp4), "video/mp4")},
    )

    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # Verify job was created with job_type="video"
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        assert job is not None
        assert job.job_type == "video"
        assert job.plugin_id == "yolo"
        assert job.tool == "detect_objects"
        assert job.status.value == "pending"
    finally:
        db.close()


def test_video_submit_saves_to_video_input(client):
    """Test that video submit saves file to video/input/."""

    # Create a fake MP4 video
    fake_mp4 = b"ftyp" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit?plugin_id=yolo&tool=detect_objects",
        files={"file": ("test.mp4", BytesIO(fake_mp4), "video/mp4")},
    )

    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # Verify file was saved to storage
    storage = LocalStorageService()
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
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
    finally:
        db.close()


def test_video_submit_invalid_file(client):
    """Test submitting an invalid video file."""
    # Create a fake invalid file
    fake_file = b"this is not a video"

    response = client.post(
        "/v1/video/submit?plugin_id=yolo&tool=detect_objects",
        files={"file": ("test.txt", BytesIO(fake_file), "text/plain")},
    )

    assert response.status_code == 400
    assert "Invalid MP4 file" in response.json()["detail"]


def test_video_submit_invalid_plugin(client):
    """Test submitting with non-existent plugin."""
    fake_mp4 = b"ftyp" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit?plugin_id=nonexistent&tool=detect_objects",
        files={"file": ("test.mp4", BytesIO(fake_mp4), "video/mp4")},
    )

    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


def test_video_submit_invalid_tool(client):
    """Test submitting with non-existent tool."""
    fake_mp4 = b"ftyp" + b"\x00" * 100

    response = client.post(
        "/v1/video/submit?plugin_id=yolo&tool=nonexistent_tool",
        files={"file": ("test.mp4", BytesIO(fake_mp4), "video/mp4")},
    )

    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()
