"""Test unified jobs endpoint for v0.9.2.

Tests that:
1. GET /v1/jobs/{id} returns job status
2. GET /v1/jobs/{id} returns result_url for completed jobs
3. GET /v1/jobs/{id} returns summary for completed jobs
4. GET /v1/jobs/{id} works for both image and video jobs
5. GET /v1/jobs/{id} returns 404 for non-existent jobs

Clean Break (Issue #350):
- No more inline results field
- All jobs return result_url for lazy loading
- Summary contains derived metadata
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


def test_get_job_not_found(client):
    """Test GET /v1/jobs/{id} for non-existent job."""
    fake_job_id = uuid4()
    response = client.get(f"/v1/jobs/{fake_job_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_job_pending(client, session):
    """Test GET /v1/jobs/{id} for pending job.

    Clean Break: Pending jobs have no result_url or summary.
    """
    # Create a pending job
    job = Job(
        job_id=uuid4(),
        status=JobStatus.pending,
        plugin_id="ocr",
        input_path="image/input/test.png",
        job_type="image",
    )
    session.add(job)
    session.commit()

    response = client.get(f"/v1/jobs/{job.job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == str(job.job_id)
    # Clean Break: No inline results field
    assert "result_url" in data
    assert data["result_url"] is None
    assert "summary" in data
    assert data["summary"] is None
    assert "created_at" in data
    assert "updated_at" in data


def test_get_job_running(client, session):
    """Test GET /v1/jobs/{id} for running job.

    Clean Break: Running jobs have no result_url or summary.
    """
    # Create a running job
    job = Job(
        job_id=uuid4(),
        status=JobStatus.running,
        plugin_id="yolo",
        input_path="video/input/test.mp4",
        job_type="video",
    )
    session.add(job)
    session.commit()

    response = client.get(f"/v1/jobs/{job.job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == str(job.job_id)
    # Clean Break: No inline results field
    assert data["result_url"] is None
    assert data["summary"] is None


def test_get_job_completed(client, session, storage):
    """Test GET /v1/jobs/{id} for completed job with results.

    Clean Break: Completed jobs return result_url, not inline results.
    v0.16.8: Summary is pre-computed by worker and stored in job.summary.
    """
    # Create a completed job with pre-computed summary (set by worker)
    job_id = uuid4()
    output_path = f"image/output/{job_id}.json"
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="ocr",
        input_path="image/input/test.png",
        output_path=output_path,
        job_type="image",
        # v0.16.8: Pre-computed summary from worker (plugin provides this)
        summary=json.dumps({"text_length": 14, "word_count": 2}),
    )
    session.add(job)
    session.commit()

    # Create results file at the correct path
    results_data = {"text": "extracted text"}
    results_json = json.dumps(results_data)
    storage.save_file(BytesIO(results_json.encode()), output_path)

    response = client.get(f"/v1/jobs/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == str(job_id)
    # Clean Break: Completed jobs return result_url, not inline results
    assert data["result_url"] is not None
    assert data["summary"] is not None
    # No inline results field
    assert "results" not in data


def test_get_job_failed(client, session):
    """Test GET /v1/jobs/{id} for failed job.

    Clean Break: Failed jobs have no result_url or summary.
    """
    # Create a failed job
    job = Job(
        job_id=uuid4(),
        status=JobStatus.failed,
        plugin_id="ocr",
        input_path="image/input/test.png",
        job_type="image",
        error_message="Processing failed",
    )
    session.add(job)
    session.commit()

    response = client.get(f"/v1/jobs/{job.job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == str(job.job_id)
    # Clean Break: No inline results field
    assert data["result_url"] is None
    assert data["summary"] is None
    assert data["error_message"] == "Processing failed"


def test_get_job_image_type(client, session, storage):
    """Test GET /v1/jobs/{id} for image job.

    Clean Break: Image jobs also use result_url for consistency.
    v0.16.8: Summary is pre-computed by worker and stored in job.summary.
    """
    # Create a completed image job with pre-computed summary
    job_id = uuid4()
    output_path = f"image/output/{job_id}.json"
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="ocr",
        input_path="image/input/test.png",
        output_path=output_path,
        job_type="image",
        # v0.16.8: Pre-computed summary from worker
        summary=json.dumps({"text_length": 10, "word_count": 2}),
    )
    session.add(job)
    session.commit()

    # Create results file at the correct path
    results_data = {"text": "OCR result"}
    results_json = json.dumps(results_data)
    storage.save_file(BytesIO(results_json.encode()), output_path)

    response = client.get(f"/v1/jobs/{job_id}")

    assert response.status_code == 200
    data = response.json()
    # Clean Break: All jobs return result_url
    assert data["result_url"] is not None
    assert data["summary"] is not None
    # No inline results field
    assert "results" not in data


def test_get_job_video_type(client, session, storage):
    """Test GET /v1/jobs/{id} for video job.

    Issue #350: Video jobs return result_url instead of inline results.
    v0.16.8: Summary is pre-computed by worker and stored in job.summary.
    """
    # Create a completed video job with pre-computed summary
    job_id = uuid4()
    output_path = f"video/output/{job_id}.json"
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="yolo",
        input_path="video/input/test.mp4",
        output_path=output_path,
        job_type="video",
        # v0.16.8: Pre-computed summary from worker
        summary=json.dumps({"frame_count": 1, "detection_count": 0, "classes": []}),
    )
    session.add(job)
    session.commit()

    # Create results file at the correct path
    results_data = {"frames": [{"detections": []}]}
    results_json = json.dumps(results_data)
    storage.save_file(BytesIO(results_json.encode()), output_path)

    response = client.get(f"/v1/jobs/{job_id}")

    assert response.status_code == 200
    data = response.json()
    # Clean Break: Video jobs return result_url, not inline results
    assert data["result_url"] is not None
    assert data["summary"] is not None
    # No inline results field
    assert "results" not in data


def test_get_job_results_file_not_found(client, session):
    """Test GET /v1/jobs/{id} when results file is missing."""
    # Create a completed job without results file
    job_id = uuid4()
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="ocr",
        input_path="image/input/test.png",
        output_path="image/output/nonexistent.json",
        job_type="image",
    )
    session.add(job)
    session.commit()

    response = client.get(f"/v1/jobs/{job_id}")

    assert response.status_code == 404
    assert "results file not found" in response.json()["detail"].lower()


def test_get_job_results_invalid_json(client, session, storage):
    """Test GET /v1/jobs/{id} when results file contains invalid JSON.

    v0.16.8: API no longer parses the JSON file for summary - it comes from
    job.summary (pre-computed by worker). API just checks file existence.
    Invalid JSON would have been caught by the worker when saving results.
    """
    # Create a completed job with pre-computed summary
    job_id = uuid4()
    output_path = f"image/output/{job_id}.json"
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="ocr",
        input_path="image/input/test.png",
        output_path=output_path,
        job_type="image",
        summary=json.dumps({"text_length": 0, "word_count": 0}),
    )
    session.add(job)
    session.commit()

    # Create a file (even with invalid JSON - API doesn't parse it)
    storage.save_file(BytesIO(b"invalid json"), output_path)

    response = client.get(f"/v1/jobs/{job_id}")

    # v0.16.8: API returns 200 because file exists, summary comes from DB
    assert response.status_code == 200
    data = response.json()
    assert data["result_url"] is not None
    assert data["summary"] is not None


# Issue #350: Artifact Pattern - video jobs return result_url, not results


def test_get_job_video_returns_result_url(client, session, storage):
    """Test GET /v1/jobs/{id} returns result_url for video jobs.

    Issue #350: Video jobs should return a URL for lazy loading.
    v0.16.8: Summary is pre-computed by worker and stored in job.summary.
    """
    job_id = uuid4()
    output_path = f"video/output/{job_id}.json"
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="yolo-tracker",
        input_path="video/input/test.mp4",
        output_path=output_path,
        job_type="video",
        # v0.16.8: Pre-computed summary from worker
        summary=json.dumps(
            {"frame_count": 100, "detection_count": 200, "classes": ["player", "ball"]}
        ),
    )
    session.add(job)
    session.commit()

    # Create a test results file with large data
    results_data = {
        "frames": [
            {"frame": i, "detections": [{"class": "player"}, {"class": "ball"}]}
            for i in range(100)
        ]
    }
    results_json = json.dumps(results_data)
    storage.save_file(BytesIO(results_json.encode()), output_path)

    response = client.get(f"/v1/jobs/{job_id}")

    assert response.status_code == 200
    data = response.json()
    # Video job should have result_url
    assert data["result_url"] is not None
    # Clean Break: No inline results field
    assert "results" not in data
    # Video job should have summary
    assert data["summary"] is not None


def test_get_job_video_includes_summary(client, session, storage):
    """Test GET /v1/jobs/{id} includes summary for video jobs.

    Issue #350: Summary contains derived metadata.
    v0.16.8: Summary is pre-computed by worker and stored in job.summary.
    """
    job_id = uuid4()
    output_path = f"video/output/{job_id}.json"
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="yolo-tracker",
        input_path="video/input/test.mp4",
        output_path=output_path,
        job_type="video",
        # v0.16.8: Pre-computed summary from worker (matches test assertions)
        summary=json.dumps(
            {"frame_count": 50, "detection_count": 100, "classes": ["player", "ball"]}
        ),
    )
    session.add(job)
    session.commit()

    # Create a test results file
    results_data = {
        "frames": [
            {"frame": i, "detections": [{"class": "player"}, {"class": "ball"}]}
            for i in range(50)
        ]
    }
    results_json = json.dumps(results_data)
    storage.save_file(BytesIO(results_json.encode()), output_path)

    response = client.get(f"/v1/jobs/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["summary"] is not None
    assert data["summary"]["frame_count"] == 50
    assert data["summary"]["detection_count"] == 100
    assert "player" in data["summary"]["classes"]
    assert "ball" in data["summary"]["classes"]


def test_get_job_video_multi_returns_result_url(client, session, storage):
    """Test GET /v1/jobs/{id} returns result_url for video_multi jobs.

    Issue #350: video_multi jobs should also use lazy loading.
    """
    job_id = uuid4()
    output_path = f"video/output/{job_id}.json"
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="multi-tool-plugin",
        input_path="video/input/test.mp4",
        output_path=output_path,
        job_type="video_multi",
    )
    session.add(job)
    session.commit()

    # Create a test results file
    results_data = {"tools": {"yolo": {"frames": []}, "ocr": {"frames": []}}}
    results_json = json.dumps(results_data)
    storage.save_file(BytesIO(results_json.encode()), output_path)

    response = client.get(f"/v1/jobs/{job_id}")

    assert response.status_code == 200
    data = response.json()
    # video_multi job should have result_url
    assert data["result_url"] is not None
    # Clean Break: No inline results field
    assert "results" not in data


# Issue #350: GET /v1/jobs/{job_id}/result endpoint for lazy loading


def test_get_job_result_returns_json_file(client, session, storage):
    """Test GET /v1/jobs/{job_id}/result returns JSON file for download.

    TDD: This test should fail initially (endpoint doesn't exist).
    """
    job_id = uuid4()
    output_path = f"video/output/{job_id}.json"
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="test-plugin",
        input_path="video/input/test.mp4",
        output_path=output_path,
        job_type="video",
    )
    session.add(job)
    session.commit()

    # Create a test results file
    results_data = {"frames": [{"detections": [{"class": "player"}]}]}
    results_json = json.dumps(results_data)
    storage.save_file(BytesIO(results_json.encode()), output_path)

    response = client.get(f"/v1/jobs/{job_id}/result")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    # Should return the JSON content
    data = response.json()
    assert "frames" in data


def test_get_job_result_not_found(client, session):
    """Test GET /v1/jobs/{job_id}/result returns 404 for non-existent job."""
    fake_job_id = uuid4()

    response = client.get(f"/v1/jobs/{fake_job_id}/result")

    assert response.status_code == 404


def test_get_job_result_no_output_path(client, session):
    """Test GET /v1/jobs/{job_id}/result returns 404 if job has no output_path."""
    job_id = uuid4()
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,  # Pending jobs have no output
        plugin_id="test-plugin",
        input_path="video/input/test.mp4",  # Required field
        job_type="video",
    )
    session.add(job)
    session.commit()

    response = client.get(f"/v1/jobs/{job_id}/result")

    assert response.status_code == 404
