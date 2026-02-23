"""Tests for v0.9.4 multi-tool Job schema changes.

Tests verify:
1. JobResultsResponse includes tool_list field
2. JobResultsResponse includes job_type field
3. JobResultsResponse includes tool field (backward compatible)
4. Schema serialization works with multi-tool job data
"""

import json
from datetime import datetime
from uuid import uuid4

import pytest

from app.schemas.job import JobResultsResponse


@pytest.mark.unit
def test_job_results_response_includes_tool_list():
    """Test that JobResultsResponse includes tool_list field."""
    response = JobResultsResponse(
        job_id=uuid4(),
        status="completed",
        results={"plugin_id": "yolo-tracker", "tools": {"t1": {}, "t2": {}}},
        tool_list=["player_detection", "ball_detection"],
        job_type="image_multi",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert response.tool_list == ["player_detection", "ball_detection"]
    assert response.job_type == "image_multi"


@pytest.mark.unit
def test_job_results_response_single_tool_backward_compatible():
    """Test that JobResultsResponse works with single tool (backward compatible)."""
    response = JobResultsResponse(
        job_id=uuid4(),
        status="completed",
        results={"text": "extracted text"},
        tool="analyze",
        tool_list=None,
        job_type="image",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert response.tool == "analyze"
    assert response.tool_list is None
    assert response.job_type == "image"


@pytest.mark.unit
def test_job_results_response_from_attributes(session):
    """Test that JobResultsResponse can be created from ORM model."""
    from app.models.job import Job, JobStatus

    job = Job(
        job_id=uuid4(),
        status=JobStatus.completed,
        plugin_id="yolo-tracker",
        tool=None,
        tool_list=json.dumps(["t1", "t2"]),
        input_path="image/test.png",
        output_path="image/output/test.json",
        job_type="image_multi",
    )
    session.add(job)
    session.commit()

    # Simulate from_attributes behavior
    response = JobResultsResponse(
        job_id=job.job_id,
        status=job.status.value,
        results={"tools": {}},
        tool=job.tool,
        tool_list=json.loads(job.tool_list) if job.tool_list else None,
        job_type=job.job_type,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )

    assert response.tool is None
    assert response.tool_list == ["t1", "t2"]
    assert response.job_type == "image_multi"


@pytest.mark.unit
def test_job_results_response_serialization():
    """Test that JobResultsResponse serializes correctly to dict."""
    response = JobResultsResponse(
        job_id=uuid4(),
        status="completed",
        results={"plugin_id": "test", "tools": {"t1": {"data": 1}}},
        tool_list=["t1"],
        job_type="image_multi",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    data = response.model_dump()

    assert "tool_list" in data
    assert "job_type" in data
    assert "tool" in data
    assert data["tool_list"] == ["t1"]
    assert data["job_type"] == "image_multi"
    assert data["tool"] is None


@pytest.mark.unit
def test_job_results_response_all_optional_fields():
    """Test that all optional fields can be None."""
    response = JobResultsResponse(
        job_id=uuid4(),
        status="pending",
        results=None,
        tool=None,
        tool_list=None,
        job_type=None,
        error_message=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert response.results is None
    assert response.tool is None
    assert response.tool_list is None
    assert response.job_type is None
    assert response.error_message is None
