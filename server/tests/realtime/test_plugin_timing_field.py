"""Test Phase 10: Extended job model with plugin timings field.

This test verifies that the extended job model includes the optional
plugin_timings field.
"""

from datetime import datetime, timezone

from app.extended_job import ExtendedJobResponse
from app.models_pydantic import JobStatus


def test_job_response_includes_plugin_timings_field():
    """Verify extended job response has optional plugin_timings field."""
    job = ExtendedJobResponse(
        job_id="test-job",
        status=JobStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
        plugin="test-plugin",
        plugin_timings={"ocr": 12.5, "detector": 45.2},
    )
    assert job.plugin_timings is not None
    assert "ocr" in job.plugin_timings
    assert job.plugin_timings["ocr"] == 12.5


def test_job_response_plugin_timings_type():
    """Verify plugin_timings field is Optional[Dict[str, float]]."""
    job = ExtendedJobResponse(
        job_id="test-job",
        status=JobStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
        plugin="test-plugin",
        plugin_timings={"ocr": 10.0},
    )
    assert isinstance(job.plugin_timings, dict)
    assert all(isinstance(v, float) for v in job.plugin_timings.values())


def test_job_response_plugin_timings_none_by_default():
    """Verify plugin_timings field is None by default."""
    job = ExtendedJobResponse(
        job_id="test-job",
        status=JobStatus.QUEUED,
        created_at=datetime.now(timezone.utc),
        plugin="test-plugin",
    )
    assert job.plugin_timings is None


def test_job_response_warnings_field():
    """Verify extended job response has optional warnings field."""
    job = ExtendedJobResponse(
        job_id="test-job",
        status=JobStatus.RUNNING,
        created_at=datetime.now(timezone.utc),
        plugin="test-plugin",
        warnings=["Warning 1", "Warning 2"],
    )
    assert job.warnings is not None
    assert len(job.warnings) == 2
