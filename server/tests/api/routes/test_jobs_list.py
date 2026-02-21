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


@pytest.fixture(autouse=True)
def clean_database():
    """Clean database before each test."""
    db = SessionLocal()
    db.query(Job).delete()
    db.commit()
    db.close()
    yield
    # Cleanup after test
    db = SessionLocal()
    db.query(Job).delete()
    db.commit()
    db.close()


def create_job(db, status: JobStatus, plugin_id="ocr", with_result=False):
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
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def test_list_jobs_empty(client):
    """Test GET /v1/jobs when database is empty."""
    response = client.get("/v1/jobs?limit=10&skip=0")
    
    assert response.status_code == 200
    data = response.json()
    assert data["jobs"] == []
    assert data["count"] == 0


def test_list_jobs_basic(client):
    """Test GET /v1/jobs returns jobs with correct status values."""
    db = SessionLocal()
    
    # Create jobs with different statuses
    create_job(db, JobStatus.pending)
    create_job(db, JobStatus.running)
    create_job(db, JobStatus.completed, with_result=False)
    create_job(db, JobStatus.failed)
    
    db.close()
    
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


def test_list_jobs_pagination(client):
    """Test GET /v1/jobs with limit and skip parameters."""
    db = SessionLocal()
    
    # Create 15 jobs
    for _ in range(15):
        create_job(db, JobStatus.pending)
    
    db.close()
    
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


def test_list_jobs_with_results(client, storage):
    """Test GET /v1/jobs loads results for completed jobs."""
    db = SessionLocal()
    
    # Create completed job with results
    job = create_job(db, JobStatus.completed, with_result=True)
    
    # Create results file
    results_data = {"text": "OCR result"}
    results_json = json.dumps(results_data)
    storage.save_file(BytesIO(results_json.encode()), "jobs/output.json")
    
    # Create pending job (should not have results)
    create_job(db, JobStatus.pending)
    
    db.close()
    
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


def test_list_jobs_includes_plugin_and_tool(client):
    """Test GET /v1/jobs includes plugin_id and tool."""
    db = SessionLocal()
    
    # Create job with specific plugin and tool
    create_job(db, JobStatus.pending, plugin_id="yolo-tracker")
    
    db.close()
    
    response = client.get("/v1/jobs?limit=10&skip=0")
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["jobs"]) == 1
    job = data["jobs"][0]
    assert "plugin" in job
    assert job["plugin"] == "yolo-tracker"


def test_list_jobs_ordering(client):
    """Test GET /v1/jobs returns jobs ordered by created_at desc (newest first)."""
    db = SessionLocal()
    
    # Create jobs with different timestamps
    job1 = create_job(db, JobStatus.pending)
    job1_id = str(job1.job_id)
    job2 = create_job(db, JobStatus.pending)
    job2_id = str(job2.job_id)
    job3 = create_job(db, JobStatus.pending)
    job3_id = str(job3.job_id)
    
    db.close()
    
    response = client.get("/v1/jobs?limit=10&skip=0")
    
    assert response.status_code == 200
    data = response.json()
    
    # Jobs should be ordered newest first
    job_ids = [j["job_id"] for j in data["jobs"]]
    assert job_ids[0] == job3_id
    assert job_ids[1] == job2_id
    assert job_ids[2] == job1_id
