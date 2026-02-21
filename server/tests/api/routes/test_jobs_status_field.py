"""Tests for status field in JobResultsResponse (Issue #211).

The /v1/jobs/{id} response was missing the status field, which the web-UI
needs to determine the job state for polling and display.
"""

import json
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.models.job import Job, JobStatus
from app.services.storage.local_storage import LocalStorageService


@pytest.fixture
def client():
    """Create a test client."""
    from app.main import app

    return TestClient(app)


@pytest.fixture
def storage():
    """Create a storage service."""
    return LocalStorageService()


class TestJobResultsResponseStatusField:
    """Tests for Issue #211: Response missing status field."""

    def test_get_job_includes_status_pending(self, client):
        """Test that pending job response includes status field."""
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
        assert "status" in data
        assert data["status"] == "pending"

        db.close()

    def test_get_job_includes_status_running(self, client):
        """Test that running job response includes status field."""
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
        assert "status" in data
        assert data["status"] == "running"

        db.close()

    def test_get_job_includes_status_completed(self, client, storage):
        """Test that completed job response includes status field."""
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
        assert "status" in data
        assert data["status"] == "completed"

        db.close()

    def test_get_job_includes_status_failed(self, client):
        """Test that failed job response includes status field."""
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
        assert "status" in data
        assert data["status"] == "failed"
        # Also check error_message is included
        assert "error_message" in data
        assert data["error_message"] == "Processing failed"

        db.close()
