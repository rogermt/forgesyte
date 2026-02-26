"""Tests for /v1/jobs/{job_id}/video endpoint.

TDD for v0.10.0 addendum - Video file serving for VideoResultsViewer.

Tests that:
1. GET /v1/jobs/{job_id}/video returns video file for completed video job
2. GET /v1/jobs/{job_id}/video returns 404 for non-existent job
3. GET /v1/jobs/{job_id}/video returns 404 when video file is missing
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.job import Job, JobStatus
from app.services.storage.local_storage import BASE_DIR, LocalStorageService

# Video storage directory (relative to server/data/jobs/)
VIDEO_INPUT_DIR = BASE_DIR / "video" / "input"


@pytest.fixture
def client(session):
    """Create a test client with dependency overrides for database session."""

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def storage():
    """Create a storage service."""
    return LocalStorageService()


@pytest.fixture(autouse=True)
def setup_video_dir():
    """Ensure video/input directory exists before tests and cleanup after."""
    # Create the directory
    VIDEO_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup test files (but keep directory structure)
    for f in VIDEO_INPUT_DIR.glob("*.mp4"):
        f.unlink()


class TestGetJobVideo:
    """Tests for GET /v1/jobs/{job_id}/video endpoint."""

    def test_get_job_video_success(self, client, session):
        """Test GET /v1/jobs/{job_id}/video returns video file."""
        job_id = uuid4()

        # Create a completed video job
        job = Job(
            job_id=job_id,
            status=JobStatus.completed,
            plugin_id="yolo",
            tool="video_player_tracking",
            input_path=f"video/input/{job_id}.mp4",
            output_path=f"video/output/{job_id}.json",
            job_type="video",
        )
        session.add(job)
        session.commit()

        # Create a fake MP4 file
        video_path = VIDEO_INPUT_DIR / f"{job_id}.mp4"
        video_path.write_bytes(b"\x00\x00\x00\x18ftypmp42")  # Minimal MP4 header

        response = client.get(f"/v1/jobs/{job_id}/video")

        assert response.status_code == 200
        assert response.headers["content-type"] == "video/mp4"
        assert response.content == b"\x00\x00\x00\x18ftypmp42"

    def test_get_job_video_job_not_found(self, client):
        """Test GET /v1/jobs/{job_id}/video returns 404 for non-existent job."""
        fake_job_id = uuid4()
        response = client.get(f"/v1/jobs/{fake_job_id}/video")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_job_video_file_not_found(self, client, session, storage):
        """Test GET /v1/jobs/{job_id}/video returns 404 when file missing."""
        job_id = uuid4()

        # Create a completed video job without the actual video file
        job = Job(
            job_id=job_id,
            status=JobStatus.completed,
            plugin_id="yolo",
            tool="video_player_tracking",
            input_path=f"video/input/{job_id}.mp4",
            output_path=f"video/output/{job_id}.json",
            job_type="video",
        )
        session.add(job)
        session.commit()

        # Don't create the video file
        response = client.get(f"/v1/jobs/{job_id}/video")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_job_video_pending_job(self, client, session):
        """Test GET /v1/jobs/{job_id}/video for pending job still returns video."""
        job_id = uuid4()

        # Create a pending video job (video should still be accessible)
        job = Job(
            job_id=job_id,
            status=JobStatus.pending,
            plugin_id="yolo",
            tool="video_player_tracking",
            input_path=f"video/input/{job_id}.mp4",
            job_type="video",
        )
        session.add(job)
        session.commit()

        # Create the video file
        video_path = VIDEO_INPUT_DIR / f"{job_id}.mp4"
        video_path.write_bytes(b"\x00\x00\x00\x18ftypmp42")

        response = client.get(f"/v1/jobs/{job_id}/video")

        # Video should be accessible even for pending jobs (for preview)
        assert response.status_code == 200
        assert response.headers["content-type"] == "video/mp4"
