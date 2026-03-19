"""Tests for GET /v1/jobs/{job_id}/result endpoint.

Issue #350: Artifact Pattern for video job lazy loading.

This endpoint provides on-demand access to large video job results.
Two modes:
- redirect: Returns a signed URL for the client to fetch directly
- stream: Returns the JSON content directly (for small results or local dev)
"""

import json
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.job import Job, JobStatus
from app.services.storage.local_storage import LocalStorageService


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


@pytest.mark.unit
def test_get_job_result_returns_signed_url_for_video_job(client, session, storage):
    """Test that GET /v1/jobs/{id}/result returns result_url for video job.

    Issue #350: Video jobs should return a URL for lazy loading.
    """
    job_id = uuid4()
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="yolo-tracker",
        input_path="video/input/test.mp4",
        output_path=f"video/output/{job_id}.json",
        job_type="video",
    )
    session.add(job)
    session.commit()

    # Create a test results file
    results = {"frames": [{"frame": 1, "detections": []}]}
    results_bytes = BytesIO(json.dumps(results).encode())
    storage.save_file(results_bytes, f"video/output/{job_id}.json")

    # Request with mode=redirect (default for video)
    response = client.get(f"/v1/jobs/{job_id}/result?mode=redirect")

    assert response.status_code == 200
    data = response.json()
    assert "result_url" in data
    assert data["result_url"] is not None


@pytest.mark.unit
def test_get_job_result_streams_json_for_stream_mode(client, session, storage):
    """Test that GET /v1/jobs/{id}/result?mode=stream returns JSON content.

    Issue #350: Stream mode returns the actual JSON content.
    """
    job_id = uuid4()
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="yolo-tracker",
        input_path="video/input/test.mp4",
        output_path=f"video/output/{job_id}.json",
        job_type="video",
    )
    session.add(job)
    session.commit()

    # Create a test results file
    results = {"frames": [{"frame": 1, "detections": []}]}
    results_bytes = BytesIO(json.dumps(results).encode())
    storage.save_file(results_bytes, f"video/output/{job_id}.json")

    # Request with mode=stream
    response = client.get(f"/v1/jobs/{job_id}/result?mode=stream")

    assert response.status_code == 200
    data = response.json()
    assert "frames" in data


@pytest.mark.unit
def test_get_job_result_404_for_nonexistent_job(client):
    """Test that GET /v1/jobs/{id}/result returns 404 for nonexistent job.

    Issue #350: Should return 404 if job not found.
    """
    fake_id = uuid4()
    response = client.get(f"/v1/jobs/{fake_id}/result")

    assert response.status_code == 404


@pytest.mark.unit
def test_get_job_result_404_for_pending_job(client, session):
    """Test that GET /v1/jobs/{id}/result returns 404 for pending job.

    Issue #350: Should return 404 if job has no results yet.
    """
    job_id = uuid4()
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        plugin_id="yolo-tracker",
        input_path="video/input/test.mp4",
        job_type="video",
    )
    session.add(job)
    session.commit()

    response = client.get(f"/v1/jobs/{job_id}/result")

    assert response.status_code == 404
    assert "no results" in response.json()["detail"].lower()


@pytest.mark.unit
def test_get_job_result_404_for_missing_file(client, session):
    """Test that GET /v1/jobs/{id}/result returns 404 if file missing.

    Issue #350: Should return 404 if results file doesn't exist.
    """
    job_id = uuid4()
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="yolo-tracker",
        input_path="video/input/test.mp4",
        output_path="video/output/nonexistent.json",  # File doesn't exist
        job_type="video",
    )
    session.add(job)
    session.commit()

    response = client.get(f"/v1/jobs/{job_id}/result")

    assert response.status_code == 404


@pytest.mark.unit
def test_get_job_result_default_mode_is_redirect(client, session, storage):
    """Test that default mode is redirect for video jobs.

    Issue #350: Without mode param, should return redirect URL.
    """
    job_id = uuid4()
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="yolo-tracker",
        input_path="video/input/test.mp4",
        output_path=f"video/output/{job_id}.json",
        job_type="video",
    )
    session.add(job)
    session.commit()

    # Create a test results file
    results = {"frames": []}
    results_bytes = BytesIO(json.dumps(results).encode())
    storage.save_file(results_bytes, f"video/output/{job_id}.json")

    # Request without mode param
    response = client.get(f"/v1/jobs/{job_id}/result")

    assert response.status_code == 200
    data = response.json()
    assert "result_url" in data
