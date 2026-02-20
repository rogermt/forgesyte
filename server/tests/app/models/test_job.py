"""Tests for Job model."""

import pytest

from app.models.job import Job, JobStatus


@pytest.mark.unit
def test_job_defaults(session):
    """Test Job model defaults."""
    job = Job(plugin_id="yolo-tracker", tool="video_track", input_path="video_jobs/test.mp4")
    session.add(job)
    session.commit()

    assert job.job_id is not None
    assert job.status == JobStatus.pending
    assert job.created_at is not None
    assert job.updated_at is not None


@pytest.mark.unit
def test_job_status_enum(session):
    """Test Job status enum."""
    job = Job(
        plugin_id="yolo-tracker",
        tool="video_track",
        input_path="test.mp4",
        status=JobStatus.running,
    )
    session.add(job)
    session.commit()

    assert job.status == JobStatus.running


@pytest.mark.unit
def test_job_all_fields(session):
    """Test Job with all fields."""
    job = Job(
        plugin_id="yolo-tracker",
        tool="video_track",
        input_path="video_jobs/test.mp4",
        output_path="results/test_output.json",
        status=JobStatus.completed,
        error_message=None,
    )
    session.add(job)
    session.commit()

    retrieved = session.query(Job).filter_by(job_id=job.job_id).first()
    assert retrieved is not None
    assert retrieved.plugin_id == "yolo-tracker"
    assert retrieved.tool == "video_track"
    assert retrieved.input_path == "video_jobs/test.mp4"
    assert retrieved.output_path == "results/test_output.json"
    assert retrieved.status == JobStatus.completed
    assert retrieved.error_message is None


@pytest.mark.unit
def test_job_error_message(session):
    """Test Job with error message."""
    job = Job(
        plugin_id="yolo-tracker",
        tool="video_track",
        input_path="test.mp4",
        status=JobStatus.failed,
        error_message="Model not found",
    )
    session.add(job)
    session.commit()

    assert job.status == JobStatus.failed
    assert job.error_message == "Model not found"
