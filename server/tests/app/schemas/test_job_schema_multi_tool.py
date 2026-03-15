"""Tests for v0.9.4 multi-tool Job schema changes.

Tests verify:
1. JobResultsResponse includes tools field (v0.15.1: replaced tool_list)
2. JobResultsResponse includes job_type field
3. JobResultsResponse includes tool field (backward compatible)
4. Schema serialization works with multi-tool job data
"""

from datetime import datetime
from uuid import uuid4

import pytest

from app.schemas.job import JobResultsResponse


@pytest.mark.unit
def test_job_results_response_includes_tools():
    """Test that JobResultsResponse includes tools field."""
    response = JobResultsResponse(
        job_id=uuid4(),
        status="completed",
        plugin_id="yolo-tracker",  # Issue #296: Now required
        results={"plugin_id": "yolo-tracker", "tools": {"t1": {}, "t2": {}}},
        tools=["player_detection", "ball_detection"],
        job_type="image_multi",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert response.tools == ["player_detection", "ball_detection"]
    assert response.job_type == "image_multi"


@pytest.mark.unit
def test_job_results_response_single_tool_backward_compatible():
    """Test that JobResultsResponse works with single tool (backward compatible)."""
    response = JobResultsResponse(
        job_id=uuid4(),
        status="completed",
        plugin_id="ocr-plugin",  # Issue #296: Now required
        results={"text": "extracted text"},
        tools=["analyze"],
        job_type="image",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert response.tool is None  # Not set when tools is used
    assert response.tools == ["analyze"]
    assert response.job_type == "image"


@pytest.mark.unit
def test_job_results_response_from_attributes(session):
    """Test that JobResultsResponse can be created from ORM model."""
    from app.models.job import Job, JobStatus
    from app.models.job_tool import JobTool

    job_id = uuid4()
    job = Job(
        job_id=job_id,
        status=JobStatus.completed,
        plugin_id="yolo-tracker",
        input_path="image/test.png",
        output_path="image/output/test.json",
        job_type="image_multi",
    )
    session.add(job)
    session.flush()

    # Add tools to job_tools table
    for order, tool_id in enumerate(["t1", "t2"]):
        job_tool = JobTool(job_id=job_id, tool_id=tool_id, tool_order=order)
        session.add(job_tool)
    session.commit()

    # Simulate from_attributes behavior
    response = JobResultsResponse(
        job_id=job.job_id,
        status=job.status.value,
        plugin_id=job.plugin_id,  # Issue #296: Now required
        results={"tools": {}},
        tools=["t1", "t2"],
        job_type=job.job_type,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )

    assert response.tools == ["t1", "t2"]
    assert response.job_type == "image_multi"


@pytest.mark.unit
def test_job_results_response_serialization():
    """Test that JobResultsResponse serializes correctly to dict."""
    response = JobResultsResponse(
        job_id=uuid4(),
        status="completed",
        plugin_id="test-plugin",  # Issue #296: Now required
        results={"plugin_id": "test", "tools": {"t1": {"data": 1}}},
        tools=["t1"],
        job_type="image_multi",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    data = response.model_dump()

    assert "tools" in data
    assert "job_type" in data
    assert "tool" in data
    assert "plugin_id" in data  # Issue #296
    assert data["tools"] == ["t1"]
    assert data["job_type"] == "image_multi"
    assert data["tool"] is None


@pytest.mark.unit
def test_job_results_response_all_optional_fields():
    """Test that all optional fields can be None."""
    response = JobResultsResponse(
        job_id=uuid4(),
        status="pending",
        plugin_id="test-plugin",  # Issue #296: Now required (was missing)
        results=None,
        job_type=None,
        error_message=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert response.results is None
    assert response.tool is None
    assert response.tools is None
    assert response.job_type is None
    assert response.error_message is None
