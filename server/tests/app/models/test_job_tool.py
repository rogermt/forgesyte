"""Tests for JobTool model.

Tests verify:
1. JobTool model can be created
2. JobTool has correct relationship to Job
3. Multiple JobTools can be associated with one Job
4. Cascade delete works when Job is deleted
"""

import pytest

from app.models.job import Job, JobStatus


@pytest.mark.unit
def test_job_tool_model_exists():
    """RED: Verify JobTool model can be imported."""
    try:
        from app.models.job_tool import JobTool

        assert JobTool is not None
    except ImportError:
        pytest.fail("JobTool model not found - need to create it")


@pytest.mark.unit
def test_job_tool_create(session):
    """RED: Test creating a JobTool record."""
    from app.models.job_tool import JobTool

    # Create a job first
    job = Job(
        plugin_id="test-plugin",
        input_path="test/input.jpg",
        job_type="image",
        status=JobStatus.pending,
    )
    session.add(job)
    session.commit()

    # Create job_tool
    job_tool = JobTool(job_id=job.job_id, tool_id="tool_a")
    session.add(job_tool)
    session.commit()

    assert job_tool.id is not None
    assert str(job_tool.job_id) == str(job.job_id)
    assert job_tool.tool_id == "tool_a"


@pytest.mark.unit
def test_job_multiple_tools(session):
    """RED: Test a Job can have multiple JobTools."""
    from app.models.job_tool import JobTool

    # Create a job
    job = Job(
        plugin_id="test-plugin",
        input_path="test/input.jpg",
        job_type="image_multi",
        status=JobStatus.pending,
    )
    session.add(job)
    session.commit()

    # Add multiple tools
    tools = ["tool_a", "tool_b", "tool_c"]
    for tool_id in tools:
        job_tool = JobTool(job_id=job.job_id, tool_id=tool_id)
        session.add(job_tool)
    session.commit()

    # Query tools for this job
    job_tools = session.query(JobTool).filter_by(job_id=job.job_id).all()
    assert len(job_tools) == 3
    tool_ids = [jt.tool_id for jt in job_tools]
    assert set(tool_ids) == set(tools)


@pytest.mark.unit
def test_job_tool_preserves_order(session):
    """RED: Test that tool order is preserved via insertion order."""
    from app.models.job_tool import JobTool

    # Create a job
    job = Job(
        plugin_id="test-plugin",
        input_path="test/input.jpg",
        job_type="image_multi",
        status=JobStatus.pending,
    )
    session.add(job)
    session.commit()

    # Add tools in specific order
    tools = ["first_tool", "second_tool", "third_tool"]
    for tool_id in tools:
        job_tool = JobTool(job_id=job.job_id, tool_id=tool_id)
        session.add(job_tool)
    session.commit()

    # Query and verify order
    job_tools = (
        session.query(JobTool).filter_by(job_id=job.job_id).order_by(JobTool.id).all()
    )
    retrieved_tools = [jt.tool_id for jt in job_tools]
    assert retrieved_tools == tools


@pytest.mark.unit
def test_job_tool_cascade_delete(session):
    """RED: Test that JobTools are deleted when Job is deleted."""
    from app.models.job_tool import JobTool

    # Create a job with tools
    job = Job(
        plugin_id="test-plugin",
        input_path="test/input.jpg",
        job_type="image_multi",
        status=JobStatus.pending,
    )
    session.add(job)
    session.commit()

    job_tool = JobTool(job_id=job.job_id, tool_id="tool_a")
    session.add(job_tool)
    session.commit()

    job_id = job.job_id

    # Delete the job
    session.delete(job)
    session.commit()

    # Verify job_tool is also deleted
    remaining = session.query(JobTool).filter_by(job_id=job_id).all()
    assert len(remaining) == 0
