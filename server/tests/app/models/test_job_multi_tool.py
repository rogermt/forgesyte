"""Tests for v0.9.4 multi-tool Job model changes.

Tests verify:
1. Job.tool is nullable for multi-tool jobs
2. Job.tool_list stores JSON-encoded list of tools
3. job_type="image_multi" for multi-tool jobs
4. Backward compatibility: single-tool jobs still work with tool field
"""

import json

import pytest

from app.models.job import Job, JobStatus


@pytest.mark.unit
def test_job_tool_nullable_for_multi_tool(session):
    """Test that tool can be null for multi-tool jobs."""
    job = Job(
        plugin_id="yolo-tracker",
        tool=None,  # Nullable for multi-tool
        tool_list=json.dumps(["player_detection", "ball_detection"]),
        input_path="image/test.png",
        job_type="image_multi",
    )
    session.add(job)
    session.commit()

    assert job.tool is None
    assert job.tool_list == json.dumps(["player_detection", "ball_detection"])
    assert job.job_type == "image_multi"


@pytest.mark.unit
def test_job_tool_list_stores_json_string(session):
    """Test that tool_list stores JSON-encoded list."""
    tools = ["player_detection", "ball_detection", "player_tracking"]
    job = Job(
        plugin_id="yolo-tracker",
        tool=None,
        tool_list=json.dumps(tools),
        input_path="image/test.png",
        job_type="image_multi",
    )
    session.add(job)
    session.commit()

    # Decode and verify
    decoded = json.loads(job.tool_list)
    assert decoded == tools
    assert len(decoded) == 3


@pytest.mark.unit
def test_job_single_tool_backward_compatible(session):
    """Test that single-tool jobs still work with tool field (backward compatible)."""
    job = Job(
        plugin_id="ocr",
        tool="analyze",
        tool_list=None,  # Not used for single-tool
        input_path="image/test.png",
        job_type="image",
    )
    session.add(job)
    session.commit()

    assert job.tool == "analyze"
    assert job.tool_list is None
    assert job.job_type == "image"


@pytest.mark.unit
def test_job_tool_list_empty_array(session):
    """Test that tool_list can store empty array (edge case)."""
    job = Job(
        plugin_id="test-plugin",
        tool=None,
        tool_list=json.dumps([]),
        input_path="image/test.png",
        job_type="image_multi",
    )
    session.add(job)
    session.commit()

    decoded = json.loads(job.tool_list)
    assert decoded == []


@pytest.mark.unit
def test_job_multi_tool_with_all_fields(session):
    """Test multi-tool job with all fields populated."""
    job = Job(
        plugin_id="yolo-tracker",
        tool=None,
        tool_list=json.dumps(["player_detection", "ball_detection"]),
        input_path="image/test.png",
        output_path="image/output/test.json",
        status=JobStatus.completed,
        error_message=None,
        job_type="image_multi",
    )
    session.add(job)
    session.commit()

    retrieved = session.query(Job).filter_by(job_id=job.job_id).first()
    assert retrieved is not None
    assert retrieved.tool is None
    assert json.loads(retrieved.tool_list) == ["player_detection", "ball_detection"]
    assert retrieved.job_type == "image_multi"
    assert retrieved.status == JobStatus.completed


@pytest.mark.unit
def test_job_tool_list_preserves_order(session):
    """Test that tool_list preserves tool execution order."""
    tools = ["detect_players", "detect_ball", "track_motion"]
    job = Job(
        plugin_id="yolo-tracker",
        tool=None,
        tool_list=json.dumps(tools),
        input_path="image/test.png",
        job_type="image_multi",
    )
    session.add(job)
    session.commit()

    decoded = json.loads(job.tool_list)
    assert decoded == tools  # Order preserved
    assert decoded[0] == "detect_players"
    assert decoded[1] == "detect_ball"
    assert decoded[2] == "track_motion"
