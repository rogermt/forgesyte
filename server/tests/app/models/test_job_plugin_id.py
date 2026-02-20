"""Tests for Job model plugin_id and tool columns."""

import pytest

from app.models.job import Job, JobStatus


@pytest.mark.unit
def test_job_accepts_plugin_id_and_tool(session):
    """Test Job model accepts plugin_id and tool columns."""
    job = Job(
        plugin_id="ocr",
        tool="extract_text",
        input_path="video_jobs/test.mp4",
    )
    session.add(job)
    session.commit()

    assert job.job_id is not None
    assert job.plugin_id == "ocr"
    assert job.tool == "extract_text"
    assert job.status == JobStatus.pending


@pytest.mark.unit
def test_job_plugin_id_and_tool_not_nullable(session):
    """Test Job model requires plugin_id and tool (NOT NULL constraint)."""
    from sqlalchemy.exc import IntegrityError

    # This should fail because plugin_id and tool are required
    with pytest.raises(IntegrityError):
        job = Job(
            plugin_id=None,  # NOT NULL
            tool=None,  # NOT NULL
            input_path="test.mp4",
        )
        session.add(job)
        session.commit()


@pytest.mark.unit
def test_job_plugin_id_and_tool_persist_through_status_change(session):
    """Test plugin_id and tool persist when job status changes."""
    job = Job(
        plugin_id="yolo-tracker",
        tool="video_track",
        input_path="video_jobs/test.mp4",
    )
    session.add(job)
    session.commit()

    # Update status
    job.status = JobStatus.running
    session.commit()

    # Refresh and verify plugin_id and tool persist
    session.expire_all()
    retrieved = session.query(Job).filter_by(job_id=job.job_id).first()
    assert retrieved is not None
    assert retrieved.plugin_id == "yolo-tracker"
    assert retrieved.tool == "video_track"
    assert retrieved.status == JobStatus.running
