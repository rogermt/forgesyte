"""Test unified jobs endpoint for v0.9.2.

Tests that:
1. GET /v1/jobs/{id} returns job status and results
2. GET /v1/jobs/{id} returns None for results when job is not completed
3. GET /v1/jobs/{id} returns results when job is completed
4. GET /v1/jobs/{id} works for both image and video jobs
5. GET /v1/jobs/{id} returns 404 for non-existent jobs
"""

import json
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.job import Job, JobStatus
from app.services.storage.local_storage import LocalStorageService


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


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


def test_get_job_pending(client):
    """Test GET /v1/jobs/{id} for pending job."""
    db = SessionLocal()

    # Create a pending job
    job = Job(
        job_id=uuid4(),
        status=JobStatus.pending,
        plugin_id="ocr",
        tool="extract_text",
        input_path="image/input/test.png",
        job_type="image",
    )
    db.add(job)
    db.commit()

    response = client.get(f"/v1/jobs/{job.job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == str(job.job_id)
    assert data["results"] is None
    assert "created_at" in data
    assert "updated_at" in data

    db.close()


def test_get_job_running(client):
    """Test GET /v1/jobs/{id} for running job."""
    db = SessionLocal()

    # Create a running job
    job = Job(
        job_id=uuid4(),
        status=JobStatus.running,
        plugin_id="yolo",
        tool="detect_objects",
        input_path="video/input/test.mp4",
        job_type="video",
    )
    db.add(job)
    db.commit()

    response = client.get(f"/v1/jobs/{job.job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == str(job.job_id)
    assert data["results"] is None

    db.close()


def test_get_job_completed(client, storage):
    """Test GET /v1/jobs/{id} for completed job with results."""
    db = SessionLocal()

    # Create a completed job
    job_id = uuid4()
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="ocr",
        tool="extract_text",
        input_path="image/input/test.png",
        output_path="image/output/test.json",
        job_type="image",
    )
    db.add(job)
    db.commit()

    # Create results file
    results_data = {"results": {"text": "extracted text"}}
    results_json = json.dumps(results_data)
    storage.save_file(BytesIO(results_json.encode()), "image/output/test.json")

    response = client.get(f"/v1/jobs/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == str(job_id)
    assert data["results"] is not None
    assert data["results"]["results"]["text"] == "extracted text"

    db.close()


def test_get_job_failed(client):
    """Test GET /v1/jobs/{id} for failed job."""
    db = SessionLocal()

    # Create a failed job
    job = Job(
        job_id=uuid4(),
        status=JobStatus.failed,
        plugin_id="ocr",
        tool="extract_text",
        input_path="image/input/test.png",
        job_type="image",
        error_message="Processing failed",
    )
    db.add(job)
    db.commit()

    response = client.get(f"/v1/jobs/{job.job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == str(job.job_id)
    assert data["results"] is None

    db.close()


def test_get_job_image_type(client, storage):
    """Test GET /v1/jobs/{id} for image job."""
    db = SessionLocal()

    # Create a completed image job
    job_id = uuid4()
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="ocr",
        tool="extract_text",
        input_path="image/input/test.png",
        output_path="image/output/test.json",
        job_type="image",
    )
    db.add(job)
    db.commit()

    # Create results file
    results_data = {"results": {"text": "OCR result"}}
    results_json = json.dumps(results_data)
    storage.save_file(BytesIO(results_json.encode()), "image/output/test.json")

    response = client.get(f"/v1/jobs/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["results"]["results"]["text"] == "OCR result"

    db.close()


def test_get_job_video_type(client, storage):
    """Test GET /v1/jobs/{id} for video job."""
    db = SessionLocal()

    # Create a completed video job
    job_id = uuid4()
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="yolo",
        tool="detect_objects",
        input_path="video/input/test.mp4",
        output_path="video/output/test.json",
        job_type="video",
    )
    db.add(job)
    db.commit()

    # Create results file
    results_data = {"results": {"objects": []}}
    results_json = json.dumps(results_data)
    storage.save_file(BytesIO(results_json.encode()), "video/output/test.json")

    response = client.get(f"/v1/jobs/{job_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["results"]["results"]["objects"] == []

    db.close()


def test_get_job_results_file_not_found(client):
    """Test GET /v1/jobs/{id} when results file is missing."""
    db = SessionLocal()

    # Create a completed job without results file
    job_id = uuid4()
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="ocr",
        tool="extract_text",
        input_path="image/input/test.png",
        output_path="image/output/nonexistent.json",
        job_type="image",
    )
    db.add(job)
    db.commit()

    response = client.get(f"/v1/jobs/{job_id}")

    assert response.status_code == 404
    assert "results file not found" in response.json()["detail"].lower()

    db.close()


def test_get_job_results_invalid_json(client, storage):
    """Test GET /v1/jobs/{id} when results file contains invalid JSON."""
    db = SessionLocal()

    # Create a completed job with invalid JSON results
    job_id = uuid4()
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="ocr",
        tool="extract_text",
        input_path="image/input/test.png",
        output_path="image/output/invalid.json",
        job_type="image",
    )
    db.add(job)
    db.commit()

    # Create invalid JSON file
    storage.save_file(BytesIO(b"invalid json"), "image/output/invalid.json")

    response = client.get(f"/v1/jobs/{job_id}")

    assert response.status_code == 500
    assert "invalid results file" in response.json()["detail"].lower()

    db.close()