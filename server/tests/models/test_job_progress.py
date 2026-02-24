"""TDD tests for Job model progress field."""

from app.models.job import Job, JobStatus


def test_job_model_accepts_progress_field(session):
    """RED: Verify Job model can store progress value."""
    job = Job(
        plugin_id="test-plugin",
        tool="test-tool",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
        progress=50,  # Should accept progress value
    )
    session.add(job)
    session.commit()

    # Verify progress was stored
    assert job.progress == 50


def test_job_model_allows_null_progress(session):
    """RED: Verify Job model allows null progress (backward compatibility)."""
    job = Job(
        plugin_id="test-plugin",
        tool="test-tool",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
        progress=None,  # Should allow null
    )
    session.add(job)
    session.commit()

    # Verify progress is null
    assert job.progress is None


def test_job_model_progress_defaults_to_none(session):
    """RED: Verify Job model progress defaults to None."""
    job = Job(
        plugin_id="test-plugin",
        tool="test-tool",
        input_path="/tmp/test.mp4",
        job_type="video",
        status=JobStatus.running,
        # No progress specified - should default to None
    )
    session.add(job)
    session.commit()

    # Verify progress defaults to None
    assert job.progress is None
