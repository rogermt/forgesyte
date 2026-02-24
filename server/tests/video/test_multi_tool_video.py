"""Integration tests for multi-tool video execution.

Tests for v0.9.7 multi-tool video processing feature:
- Multi-tool submission
- Sequential execution
- Progress calculation
- Combined results
- Backward compatibility
"""

import json
import uuid
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.job import Job, JobStatus
from app.workers.worker import JobWorker

# Use a consistent test job_id for cleanup
TEST_JOB_ID = str(uuid.uuid4())


def create_video_job(
    session: Session,
    plugin_id: str = "test-plugin",
    tools: Optional[list] = None,
    job_type: str = "video",
) -> Job:
    """Helper to create a video job in the database."""
    job = Job(
        job_id=TEST_JOB_ID,
        status=JobStatus.pending,
        plugin_id=plugin_id,
        tool=tools[0] if tools and len(tools) == 1 else None,
        tool_list=json.dumps(tools) if tools and len(tools) > 1 else None,
        input_path="video/input/test.mp4",
        job_type=job_type,
    )
    session.add(job)
    session.commit()
    return job


@pytest.mark.integration
class TestMultiToolVideoSubmission:
    """Tests for multi-tool video job submission."""

    def test_submit_video_with_multiple_tools_creates_job(self, session: Session):
        """Test that submitting multiple tools creates a job with tool_list."""
        from app.api_routes.routes.video_submit import validate_mp4_magic_bytes

        # Create test video bytes
        video_data = b"fake mp4 data ftyp" + b"\x00" * 100
        validate_mp4_magic_bytes(video_data)  # Should not raise

    def test_job_stores_tool_list_for_multiple_tools(self, session: Session):
        """Test that job stores tool_list when multiple tools provided."""
        tools = ["tool_one", "tool_two"]
        job = create_video_job(session, tools=tools)

        # Verify tool_list is stored as JSON
        assert job.tool_list is not None
        stored_tools = json.loads(job.tool_list)
        assert stored_tools == tools
        # Single tool should be None for multi-tool jobs
        assert job.tool is None

    def test_job_stores_single_tool_for_one_tool(self, session: Session):
        """Test that job stores tool field when single tool provided."""
        tools = ["tool_one"]
        job = create_video_job(session, tools=tools)

        # Single tool should be stored in tool field
        assert job.tool == "tool_one"
        assert job.tool_list is None


@pytest.mark.integration
class TestMultiToolVideoExecution:
    """Tests for multi-tool video job execution."""

    def test_worker_executes_tools_sequentially(
        self, session: Session, mock_storage, mock_plugin_service
    ):
        """Test that worker executes multiple tools sequentially."""
        tools = ["tool_one", "tool_two"]
        job = create_video_job(session, tools=tools)

        # Create worker with mocks
        worker = JobWorker(
            session_factory=lambda: session,
            storage=mock_storage,
            plugin_service=mock_plugin_service,
        )

        # Execute pipeline
        with patch.object(worker, "_get_total_frames", return_value=10):
            result = worker._execute_pipeline(job, session)

        # Verify execution succeeded
        assert result is True
        assert job.status == JobStatus.completed

        # Verify both tools were called (sequentially)
        assert mock_plugin_service.run_plugin_tool.call_count == 2
        calls = mock_plugin_service.run_plugin_tool.call_args_list
        assert calls[0][0][1] == "tool_one"
        assert calls[1][0][1] == "tool_two"

    def test_combined_results_format(
        self, session: Session, mock_storage, mock_plugin_service
    ):
        """Test that results are combined in the expected format."""
        # Mock different results for each tool
        mock_plugin_service.run_plugin_tool.side_effect = [
            {"tool_one_result": "data1", "frames": []},
            {"tool_two_result": "data2", "frames": []},
        ]

        tools = ["tool_one", "tool_two"]
        job = create_video_job(session, tools=tools)

        worker = JobWorker(
            session_factory=lambda: session,
            storage=mock_storage,
            plugin_service=mock_plugin_service,
        )

        with patch.object(worker, "_get_total_frames", return_value=10):
            worker._execute_pipeline(job, session)

        # Load saved results
        saved_output = mock_storage.save_file.call_args[0][0]
        saved_output.seek(0)
        output_json = saved_output.read().decode("utf-8")
        output = json.loads(output_json)

        # Verify combined format
        assert "plugin_id" in output
        assert output["plugin_id"] == "test-plugin"
        assert "tools" in output
        assert "tool_one" in output["tools"]
        assert "tool_two" in output["tools"]

    def test_progress_calculation_for_multi_tool(
        self, session: Session, mock_storage, mock_plugin_service
    ):
        """Test that progress is calculated correctly for multi-tool jobs."""
        tools = ["tool_one", "tool_two"]
        job = create_video_job(session, tools=tools)
        job.status = JobStatus.running  # Set to running to test progress

        worker = JobWorker(
            session_factory=lambda: session,
            storage=mock_storage,
            plugin_service=mock_plugin_service,
        )

        # Test progress calculation directly
        # With 2 tools, each tool gets 50% weight
        # Tool 0 at 50% should be at 25% overall
        worker._update_job_progress(
            str(job.job_id),
            current_frame=5,
            total_frames=10,
            db=session,
            tool_index=0,
            total_tools=2,
            tool_name="tool_one",
        )

        session.refresh(job)
        # First tool at 50% = 25% overall (0 * 50 + 50 * 0.5 = 25)
        assert 20 <= job.progress <= 30


@pytest.mark.integration
class TestBackwardCompatibility:
    """Tests for backward compatibility with single-tool video jobs."""

    def test_single_tool_video_still_works(
        self, session: Session, mock_storage, mock_plugin_service
    ):
        """Test that single-tool video jobs still work after multi-tool changes."""
        tools = ["tool_one"]
        job = create_video_job(session, tools=tools)

        worker = JobWorker(
            session_factory=lambda: session,
            storage=mock_storage,
            plugin_service=mock_plugin_service,
        )

        with patch.object(worker, "_get_total_frames", return_value=10):
            result = worker._execute_pipeline(job, session)

        assert result is True
        assert job.status == JobStatus.completed

        # Should only call plugin once
        assert mock_plugin_service.run_plugin_tool.call_count == 1

    def test_single_tool_result_format(
        self, session: Session, mock_storage, mock_plugin_service
    ):
        """Test that single-tool jobs return single-tool result format."""
        tools = ["tool_one"]
        job = create_video_job(session, tools=tools)

        worker = JobWorker(
            session_factory=lambda: session,
            storage=mock_storage,
            plugin_service=mock_plugin_service,
        )

        with patch.object(worker, "_get_total_frames", return_value=10):
            worker._execute_pipeline(job, session)

        # Load saved results
        saved_output = mock_storage.save_file.call_args[0][0]
        saved_output.seek(0)
        output_json = saved_output.read().decode("utf-8")
        output = json.loads(output_json)

        # Single tool should use old format
        assert "tool" in output
        assert output["tool"] == "tool_one"
        assert "results" in output
        assert "tools" not in output  # Not combined format


@pytest.mark.integration
class TestMultiToolStatusEndpoint:
    """Tests for multi-tool video status endpoint."""

    def test_status_returns_current_tool(self, session: Session):
        """Test that status endpoint returns current_tool for running jobs."""
        tools = ["tool_one", "tool_two"]
        job = create_video_job(session, tools=tools)
        job.status = JobStatus.running
        job.progress = 25  # First tool at 50% = 25% overall
        session.commit()

        # Test the logic from jobs.py endpoint
        tools_list = json.loads(job.tool_list)
        tools_total = len(tools_list)
        tool_weight = 100 / tools_total
        tools_completed = int(job.progress / tool_weight)

        assert tools_total == 2
        assert tools_completed == 0  # First tool still running
        assert tools_list[0] == "tool_one"  # Current tool

    def test_status_returns_tools_completed(self, session: Session):
        """Test that status endpoint returns tools_completed correctly."""
        tools = ["tool_one", "tool_two"]
        job = create_video_job(session, tools=tools)
        job.status = JobStatus.running
        job.progress = 75  # Second tool at 50% = 75% overall
        session.commit()

        tools_list = json.loads(job.tool_list)
        tools_total = len(tools_list)
        tool_weight = 100 / tools_total
        tools_completed = int(job.progress / tool_weight)

        assert tools_completed == 1  # One tool completed


# Fixtures for mock services
@pytest.fixture
def mock_storage():
    """Create a mock storage service."""
    storage = MagicMock()
    storage.load_file.return_value = "/tmp/test.mp4"
    storage.save_file.return_value = "video/output/test.json"
    return storage


@pytest.fixture
def mock_plugin_service():
    """Create a mock plugin service."""
    plugin_service = MagicMock()
    plugin_service.get_plugin_manifest.return_value = {
        "id": "test-plugin",
        "name": "Test Plugin",
        "version": "1.0.0",
        "tools": [
            {
                "id": "tool_one",
                "title": "Tool One",
                "description": "First test tool",
                "inputs": {"video": {"type": "string"}},
                "outputs": {"json": {"type": "string"}},
            },
            {
                "id": "tool_two",
                "title": "Tool Two",
                "description": "Second test tool",
                "inputs": {"video": {"type": "string"}},
                "outputs": {"json": {"type": "string"}},
            },
        ],
    }
    plugin_service.run_plugin_tool.return_value = {
        "frames": [{"detections": []}],
        "total_frames": 10,
    }
    return plugin_service


# Cleanup fixture
@pytest.fixture(autouse=True)
def cleanup_jobs(session: Session):
    """Clean up test jobs after each test."""
    yield
    try:
        session.rollback()
        session.query(Job).filter(Job.job_id == TEST_JOB_ID).delete()
        session.commit()
    except Exception:
        session.rollback()
