"""Test GET /v1/jobs list endpoint.

Tests verify:
1. List endpoint returns jobs with correct pagination
2. Status values are returned correctly (Issue #212 alignment)
3. Progress is calculated correctly
4. Results are loaded only for completed jobs
5. Empty database returns empty list
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


def create_job(session, status: JobStatus, plugin_id="ocr", with_result=False):
    """Helper to create a test job."""
    job = Job(
        job_id=uuid4(),
        status=status,
        plugin_id=plugin_id,
        tool="analyze",
        job_type="image",
        input_path="jobs/input.png",
        output_path="jobs/output.json" if with_result else None,
        error_message="test error" if status == JobStatus.failed else None,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def test_list_jobs_empty(client, session):
    """Test GET /v1/jobs when database is empty."""
    # Clean database
    session.query(Job).delete()
    session.commit()

    response = client.get("/v1/jobs?limit=10&skip=0")

    assert response.status_code == 200
    data = response.json()
    assert data["jobs"] == []
    assert data["count"] == 0


def test_list_jobs_basic(client, session):
    """Test GET /v1/jobs returns jobs with correct status values."""
    # Clean database
    session.query(Job).delete()
    session.commit()

    # Create jobs with different statuses
    create_job(session, JobStatus.pending)
    create_job(session, JobStatus.running)
    create_job(session, JobStatus.completed, with_result=False)
    create_job(session, JobStatus.failed)

    response = client.get("/v1/jobs?limit=10&skip=0")

    assert response.status_code == 200
    data = response.json()

    assert "jobs" in data
    assert "count" in data
    assert data["count"] == 4

    # Verify status values (Issue #212 aligned)
    statuses = {j["status"] for j in data["jobs"]}
    assert statuses == {"pending", "running", "completed", "failed"}

    # Verify progress values (0.0, 0.5, 1.0)
    progress_values = {j["progress"] for j in data["jobs"]}
    assert progress_values == {0.0, 0.5, 1.0}


def test_list_jobs_pagination(client, session):
    """Test GET /v1/jobs with limit and skip parameters."""
    # Clean database
    session.query(Job).delete()
    session.commit()

    # Create 15 jobs
    for _ in range(15):
        create_job(session, JobStatus.pending)

    # First page
    response1 = client.get("/v1/jobs?limit=10&skip=0")
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1["jobs"]) == 10
    assert data1["count"] == 15

    # Second page
    response2 = client.get("/v1/jobs?limit=10&skip=10")
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["jobs"]) == 5
    assert data2["count"] == 15


def test_list_jobs_with_results(client, session, storage):
    """Test GET /v1/jobs loads results for completed jobs."""
    # Clean database
    session.query(Job).delete()
    session.commit()

    # Create completed job with results
    create_job(session, JobStatus.completed, with_result=True)

    # Create results file
    results_data = {"text": "OCR result"}
    results_json = json.dumps(results_data)
    storage.save_file(BytesIO(results_json.encode()), "jobs/output.json")

    # Create pending job (should not have results)
    create_job(session, JobStatus.pending)

    response = client.get("/v1/jobs?limit=10&skip=0")

    assert response.status_code == 200
    data = response.json()

    # Find completed job
    completed_job = next((j for j in data["jobs"] if j["status"] == "completed"), None)
    assert completed_job is not None
    assert completed_job["result"] is not None

    # Find pending job
    pending_job = next((j for j in data["jobs"] if j["status"] == "pending"), None)
    assert pending_job is not None
    assert pending_job["result"] is None


def test_list_jobs_includes_plugin_and_tool(client, session):
    """Test GET /v1/jobs includes plugin_id and tool."""
    # Clean database
    session.query(Job).delete()
    session.commit()

    # Create job with specific plugin and tool
    create_job(session, JobStatus.pending, plugin_id="yolo-tracker")

    response = client.get("/v1/jobs?limit=10&skip=0")

    assert response.status_code == 200
    data = response.json()

    assert len(data["jobs"]) == 1
    job = data["jobs"][0]
    assert "plugin" in job
    assert job["plugin"] == "yolo-tracker"


def test_list_jobs_ordering(client, session):
    """Test GET /v1/jobs returns jobs ordered by created_at desc (newest first)."""
    # Clean database
    session.query(Job).delete()
    session.commit()

    # Create jobs with different timestamps
    job1 = create_job(session, JobStatus.pending)
    job1_id = str(job1.job_id)
    job2 = create_job(session, JobStatus.pending)
    job2_id = str(job2.job_id)
    job3 = create_job(session, JobStatus.pending)
    job3_id = str(job3.job_id)

    response = client.get("/v1/jobs?limit=10&skip=0")

    assert response.status_code == 200
    data = response.json()

    # Jobs should be ordered newest first
    job_ids = [j["job_id"] for j in data["jobs"]]
    assert job_ids[0] == job3_id
    assert job_ids[1] == job2_id
    assert job_ids[2] == job1_id
