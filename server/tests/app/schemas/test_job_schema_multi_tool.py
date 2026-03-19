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


# Issue #350: Artifact Pattern - result_url and summary fields


@pytest.mark.unit
def test_job_results_response_includes_result_url():
    """Test that JobResultsResponse includes result_url field for lazy loading.

    Issue #350: Video jobs return result_url instead of inline results.
    """
    response = JobResultsResponse(
        job_id=uuid4(),
        status="completed",
        plugin_id="yolo-tracker",
        results=None,  # Large results stored separately
        result_url="/v1/jobs/test-job-id/result",
        job_type="video",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert response.result_url == "/v1/jobs/test-job-id/result"
    assert response.results is None


@pytest.mark.unit
def test_job_results_response_includes_summary():
    """Test that JobResultsResponse includes summary field for video jobs.

    Issue #350: Summary contains derived metadata (frame_count, detection_count, classes).
    """
    response = JobResultsResponse(
        job_id=uuid4(),
        status="completed",
        plugin_id="yolo-tracker",
        results=None,
        summary={
            "frame_count": 1500,
            "detection_count": 4500,
            "classes": ["player", "ball", "referee"],
        },
        job_type="video",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert response.summary is not None
    assert response.summary["frame_count"] == 1500
    assert response.summary["detection_count"] == 4500
    assert "player" in response.summary["classes"]


@pytest.mark.unit
def test_job_list_item_includes_result_url():
    """Test that JobListItem includes result_url field for lazy loading.

    Issue #350: Video jobs in list should return result_url, not full result.
    """
    from app.schemas.job import JobListItem

    item = JobListItem(
        job_id="test-job-id",
        status="completed",
        plugin="yolo-tracker",
        result=None,  # Large results not returned in list
        result_url="/v1/jobs/test-job-id/result",
        created_at=datetime.utcnow(),
    )

    assert item.result_url == "/v1/jobs/test-job-id/result"
    assert item.result is None


@pytest.mark.unit
def test_job_list_item_includes_summary():
    """Test that JobListItem includes summary field for video jobs.

    Issue #350: Summary allows UI to show metadata without loading full results.
    """
    from app.schemas.job import JobListItem

    item = JobListItem(
        job_id="test-job-id",
        status="completed",
        plugin="yolo-tracker",
        summary={"frame_count": 1000, "detection_count": 3000},
        created_at=datetime.utcnow(),
    )

    assert item.summary is not None
    assert item.summary["frame_count"] == 1000


@pytest.mark.unit
def test_job_results_response_backward_compatible_with_inline_results():
    """Test that image jobs still work with inline results (no result_url).

    Issue #350: Backward compatibility - image jobs return results inline.
    """
    response = JobResultsResponse(
        job_id=uuid4(),
        status="completed",
        plugin_id="ocr-plugin",
        results={"text": "extracted text"},  # Inline results for image jobs
        result_url=None,  # Not needed for small results
        summary=None,  # Not needed for image jobs
        job_type="image",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert response.results == {"text": "extracted text"}
    assert response.result_url is None
    assert response.summary is None
