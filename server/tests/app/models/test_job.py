"""Tests for Job model."""

import pytest

from app.models.job import Job, JobStatus


@pytest.mark.unit
def test_job_defaults(session):
    """Test Job model defaults."""
    job = Job(plugin_id="yolo-tracker", input_path="video/test.mp4", job_type="video")
    session.add(job)
    session.commit()

    assert job.job_id is not None
    assert job.status == JobStatus.pending
    assert job.created_at is not None
    assert job.updated_at is not None
    assert job.job_type == "video"


@pytest.mark.unit
def test_job_status_enum(session):
    """Test Job status enum."""
    job = Job(
        plugin_id="yolo-tracker",
        input_path="video/test.mp4",
        status=JobStatus.running,
        job_type="video",
    )
    session.add(job)
    session.commit()

    assert job.status == JobStatus.running


@pytest.mark.unit
def test_job_all_fields(session):
    """Test Job with all fields."""
    job = Job(
        plugin_id="yolo-tracker",
        input_path="video/test.mp4",
        output_path="video/output/test_output.json",
        status=JobStatus.completed,
        error_message=None,
        job_type="video",
    )
    session.add(job)
    session.commit()

    retrieved = session.query(Job).filter_by(job_id=job.job_id).first()
    assert retrieved is not None
    assert retrieved.plugin_id == "yolo-tracker"
    assert retrieved.input_path == "video/test.mp4"
    assert retrieved.output_path == "video/output/test_output.json"
    assert retrieved.status == JobStatus.completed
    assert retrieved.error_message is None
    assert retrieved.job_type == "video"


@pytest.mark.unit
def test_job_error_message(session):
    """Test Job with error message."""
    job = Job(
        plugin_id="yolo-tracker",
        input_path="video/test.mp4",
        status=JobStatus.failed,
        error_message="Model not found",
        job_type="video",
    )
    session.add(job)
    session.commit()

    assert job.status == JobStatus.failed
    assert job.error_message == "Model not found"


# Discussion #354: Pre-computed summary for /v1/jobs hot path
@pytest.mark.unit
def test_job_summary_column(session):
    """Test Job has summary column for pre-computed video summary.

    Discussion #354: Summary is computed once during worker finalization
    and stored in DB to avoid loading full artifacts on /v1/jobs endpoint.
    """
    import json

    summary_dict = {
        "frame_count": 100,
        "detection_count": 500,
        "classes": ["player", "ball"],
    }
    job = Job(
        plugin_id="yolo-tracker",
        input_path="video/test.mp4",
        output_path="video/output/test.json",
        status=JobStatus.completed,
        job_type="video",
        summary=json.dumps(summary_dict),  # Pre-computed summary
    )
    session.add(job)
    session.commit()

    retrieved = session.query(Job).filter_by(job_id=job.job_id).first()
    assert retrieved is not None
    assert retrieved.summary is not None
    # Summary is stored as JSON string
    loaded_summary = json.loads(retrieved.summary)
    assert loaded_summary["frame_count"] == 100
    assert loaded_summary["detection_count"] == 500
    assert loaded_summary["classes"] == ["player", "ball"]


@pytest.mark.unit
def test_job_summary_nullable(session):
    """Test Job summary is nullable (for old jobs or image jobs)."""
    job = Job(
        plugin_id="ocr-plugin",
        input_path="image/test.png",
        output_path="image/output/test.json",
        status=JobStatus.completed,
        job_type="image",
        summary=None,  # Nullable for old jobs
    )
    session.add(job)
    session.commit()

    retrieved = session.query(Job).filter_by(job_id=job.job_id).first()
    assert retrieved is not None
    assert retrieved.summary is None
