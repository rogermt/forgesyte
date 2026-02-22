"""Tests for status field in JobResultsResponse (Issue #211).

The /v1/jobs/{id} response was missing the status field, which the web-UI
needs to determine the job state for polling and display.
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


class TestJobResultsResponseStatusField:
    """Tests for Issue #211: Response missing status field."""

    def test_get_job_includes_status_pending(self, client, session):
        """Test that pending job response includes status field."""
        # Create a pending job
        job = Job(
            job_id=uuid4(),
            status=JobStatus.pending,
            plugin_id="ocr",
            tool="analyze",
            input_path="image/input/test.png",
            job_type="image",
        )
        session.add(job)
        session.commit()

        response = client.get(f"/v1/jobs/{job.job_id}")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "pending"

    def test_get_job_includes_status_running(self, client, session):
        """Test that running job response includes status field."""
        # Create a running job
        job = Job(
            job_id=uuid4(),
            status=JobStatus.running,
            plugin_id="yolo",
            tool="detect_objects",
            input_path="video/input/test.mp4",
            job_type="video",
        )
        session.add(job)
        session.commit()

        response = client.get(f"/v1/jobs/{job.job_id}")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "running"

    def test_get_job_includes_status_completed(self, client, session, storage):
        """Test that completed job response includes status field."""
        # Create a completed job
        job_id = uuid4()
        job = Job(
            job_id=job_id,
            status=JobStatus.completed,
            plugin_id="ocr",
            tool="analyze",
            input_path="image/input/test.png",
            output_path="image/output/test.json",
            job_type="image",
        )
        session.add(job)
        session.commit()

        # Create results file
        results_data = {"results": {"text": "extracted text"}}
        results_json = json.dumps(results_data)
        storage.save_file(BytesIO(results_json.encode()), "image/output/test.json")

        response = client.get(f"/v1/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "completed"

    def test_get_job_includes_status_failed(self, client, session):
        """Test that failed job response includes status field."""
        # Create a failed job
        job = Job(
            job_id=uuid4(),
            status=JobStatus.failed,
            plugin_id="ocr",
            tool="analyze",
            input_path="image/input/test.png",
            job_type="image",
            error_message="Processing failed",
        )
        session.add(job)
        session.commit()

        response = client.get(f"/v1/jobs/{job.job_id}")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "failed"
        # Also check error_message is included
        assert "error_message" in data
        assert data["error_message"] == "Processing failed"