"""Tests for Job model plugin_id column."""

import pytest

from app.models.job import Job, JobStatus


@pytest.mark.unit
def test_job_accepts_plugin_id(session):
    """Test Job model accepts plugin_id column."""
    job = Job(plugin_id="ocr", input_path="image/test.png", job_type="image")
    session.add(job)
    session.commit()

    assert job.job_id is not None
    assert job.plugin_id == "ocr"
    assert job.status == JobStatus.pending


@pytest.mark.unit
def test_job_plugin_id_not_nullable(session):
    """Test Job model requires plugin_id (NOT NULL constraint)."""
    from sqlalchemy.exc import IntegrityError

    # This should fail because plugin_id is required
    with pytest.raises(IntegrityError):
        job = Job(plugin_id=None, input_path="test.mp4", job_type="video")  # NOT NULL
        session.add(job)
        session.commit()


@pytest.mark.unit
def test_job_plugin_id_persists_through_status_change(session):
    """Test plugin_id persists when job status changes."""
    job = Job(plugin_id="yolo-tracker", input_path="video/test.mp4", job_type="video")
    session.add(job)
    session.commit()

    # Update status
    job.status = JobStatus.running
    session.commit()

    # Refresh and verify plugin_id persists
    session.expire_all()
    retrieved = session.query(Job).filter_by(job_id=job.job_id).first()
    assert retrieved is not None
    assert retrieved.plugin_id == "yolo-tracker"
    assert retrieved.status == JobStatus.running
