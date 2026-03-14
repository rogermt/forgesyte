"""TDD tests for Job model progress field."""

from app.models.job import Job, JobStatus
from app.models.job_tool import JobTool


def test_job_model_accepts_progress_field(session):
    """RED: Verify Job model can store progress value."""
    job = Job(
        plugin_id="test-plugin",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
        progress=50,  # Should accept progress value
    )
    session.add(job)
    session.flush()

    # Add tool to job_tools table (v0.15.1: replaced tool column)
    job_tool = JobTool(job_id=job.job_id, tool_id="test-tool", tool_order=0)
    session.add(job_tool)
    session.commit()

    # Verify progress was stored
    assert job.progress == 50


def test_job_model_allows_null_progress(session):
    """RED: Verify Job model allows null progress (backward compatibility)."""
    job = Job(
        plugin_id="test-plugin",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
        progress=None,  # Should allow null
    )
    session.add(job)
    session.flush()

    # Add tool to job_tools table (v0.15.1: replaced tool column)
    job_tool = JobTool(job_id=job.job_id, tool_id="test-tool", tool_order=0)
    session.add(job_tool)
    session.commit()

    # Verify progress is null
    assert job.progress is None


def test_job_model_progress_defaults_to_none(session):
    """RED: Verify Job model progress defaults to None."""
    job = Job(
        plugin_id="test-plugin",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
        # No progress specified - should default to None
    )
    session.add(job)
    session.flush()

    # Add tool to job_tools table (v0.15.1: replaced tool column)
    job_tool = JobTool(job_id=job.job_id, tool_id="test-tool", tool_order=0)
    session.add(job_tool)
    session.commit()

    # Verify progress defaults to None
    assert job.progress is None
