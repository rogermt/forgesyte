"""TDD tests for job status endpoint with progress."""

from uuid import uuid4

import pytest

from app.models.job import Job, JobStatus


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_job_status_returns_progress_for_v096_jobs(client, session):
    """RED: Verify /v1/video/status returns progress for v0.9.6+ jobs."""
    # Create job with progress
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        plugin_id="yolo",
        tool="detect",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
        progress=75,
    )
    session.add(job)
    session.commit()

    # Query status endpoint
    response = await client.get(f"/v1/video/status/{job_id}")
    assert response.status_code == 200

    data = response.json()
    assert "progress" in data
    assert data["progress"] == 75.0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_job_status_returns_null_for_old_jobs(client, session):
    """RED: Verify /v1/video/status returns null for pre-v0.9.6 jobs."""
    # Create job without progress (simulating old job)
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        plugin_id="yolo",
        tool="detect",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
        progress=None,  # No progress data
    )
    session.add(job)
    session.commit()

    # Query status endpoint
    response = await client.get(f"/v1/video/status/{job_id}")
    assert response.status_code == 200

    data = response.json()
    assert "progress" in data
    assert data["progress"] is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_job_status_returns_100_for_completed_jobs(client, session):
    """RED: Verify /v1/video/status returns 100 for completed jobs."""
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        plugin_id="yolo",
        tool="detect",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.completed,
        progress=100,
    )
    session.add(job)
    session.commit()

    # Query status endpoint
    response = await client.get(f"/v1/video/status/{job_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "completed"
    assert data["progress"] == 100.0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_job_status_returns_0_for_pending_jobs(client, session):
    """RED: Verify /v1/video/status returns 0 for pending jobs with progress set."""
    job_id = str(uuid4())
    job = Job(
        job_id=job_id,
        plugin_id="yolo",
        tool="detect",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.pending,
        progress=0,  # Progress explicitly set to 0
    )
    session.add(job)
    session.commit()

    # Query status endpoint
    response = await client.get(f"/v1/video/status/{job_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "pending"
    # v0.9.6: Returns actual progress from DB
    assert data["progress"] == 0.0
