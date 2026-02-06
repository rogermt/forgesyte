"""Test Phase 10: Extended job model with progress field.

This test verifies that ExtendedJobResponse includes the optional progress field.
"""

from datetime import datetime, timezone

from app.extended_job import ExtendedJobResponse
from app.models import JobStatus


def test_job_response_includes_progress_field():
    """Verify ExtendedJobResponse has optional progress field."""
    job = ExtendedJobResponse(
        job_id="test-job",
        status=JobStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
        plugin="test-plugin",
        progress=50,
    )
    assert job.progress == 50


def test_job_response_progress_field_type():
    """Verify progress field is optional int."""
    job = ExtendedJobResponse(
        job_id="test-job",
        status=JobStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
        plugin="test-plugin",
        progress=75,
    )
    assert job.progress == 75
    assert isinstance(job.progress, int)


def test_job_response_progress_none_by_default():
    """Verify progress field is None by default."""
    job = ExtendedJobResponse(
        job_id="test-job",
        status=JobStatus.QUEUED,
        created_at=datetime.now(timezone.utc),
        plugin="test-plugin",
    )
    assert job.progress is None
