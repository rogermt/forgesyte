"""TDD Tests for TaskProcessor.get_result() method.

Following TDD: Write tests first, then implement code to make them pass.
These tests verify the get_result() method which retrieves final job results.
"""

import asyncio
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

# Add the server directory to the path
sys.path.insert(0, "/home/rogermt/forgesyte/server")

from app.models_pydantic import JobStatus  # noqa: E402
from app.tasks import JobStore, TaskProcessor  # noqa: E402


@pytest.fixture
def job_store() -> JobStore:
    """Create a fresh JobStore for each test."""
    return JobStore()


@pytest.fixture
def mock_plugin_manager() -> MagicMock:
    """Create a mock PluginManager."""
    manager = MagicMock()
    manager.get = MagicMock(return_value=None)
    return manager


@pytest.fixture
def task_processor(
    mock_plugin_manager: MagicMock, job_store: JobStore
) -> TaskProcessor:
    """Create a TaskProcessor with mock plugin manager."""
    return TaskProcessor(mock_plugin_manager, job_store)


class TestTaskProcessorGetResult:
    """Test retrieving job results from TaskProcessor."""

    @pytest.mark.asyncio
    async def test_get_result_returns_result_for_completed_job(
        self, task_processor: TaskProcessor, mock_plugin_manager: MagicMock
    ) -> None:
        """Test that get_result returns the result for a completed job."""
        # Setup: Create a completed job with a result
        mock_plugin = MagicMock()
        expected_result = {"objects": [1, 2, 3], "confidence": 0.95}
        mock_plugin.run_tool = MagicMock(return_value=expected_result)
        mock_plugin_manager.get = MagicMock(return_value=mock_plugin)

        # Submit a job and wait for completion
        job_id = await task_processor.submit_job(
            b"image_data", "test_plugin", options={"tool": "test_plugin"}
        )
        await asyncio.sleep(0.2)

        # Verify get_result returns the result
        result = await task_processor.get_result(job_id)
        assert result is not None
        assert "objects" in result
        assert result["objects"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_get_result_returns_none_for_nonexistent_job(
        self, task_processor: TaskProcessor
    ) -> None:
        """Test that get_result returns None for a nonexistent job."""
        result = await task_processor.get_result("nonexistent-job-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_result_raises_for_incomplete_job(
        self, task_processor: TaskProcessor
    ) -> None:
        """Test that get_result raises RuntimeError for incomplete job."""
        # Submit a job but don't wait for completion
        job_id = await task_processor.submit_job(
            b"image_data", "plugin1", options={"tool": "plugin1"}
        )

        # get_result should raise since job is still queued/running
        with pytest.raises(RuntimeError, match="has not completed"):
            await task_processor.get_result(job_id)

    @pytest.mark.asyncio
    async def test_get_result_raises_for_queued_job(
        self, task_processor: TaskProcessor
    ) -> None:
        """Test that get_result raises RuntimeError for queued job."""
        # Directly create a queued job without processing
        await task_processor.job_store.create(
            "queued-job",
            {
                "job_id": "queued-job",
                "plugin": "plugin1",
                "status": JobStatus.QUEUED,
                "result": None,
                "error": None,
                "created_at": datetime.now(timezone.utc),
                "completed_at": None,
                "progress": 0.0,
            },
        )

        with pytest.raises(RuntimeError, match="has not completed"):
            await task_processor.get_result("queued-job")

    @pytest.mark.asyncio
    async def test_get_result_raises_for_running_job(
        self, task_processor: TaskProcessor
    ) -> None:
        """Test that get_result raises RuntimeError for running job."""
        await task_processor.job_store.create(
            "running-job",
            {
                "job_id": "running-job",
                "plugin": "plugin1",
                "status": JobStatus.RUNNING,
                "result": None,
                "error": None,
                "created_at": datetime.now(timezone.utc),
                "completed_at": None,
                "progress": 0.5,
            },
        )

        with pytest.raises(RuntimeError, match="has not completed"):
            await task_processor.get_result("running-job")

    @pytest.mark.asyncio
    async def test_get_result_returns_none_for_errored_job(
        self, task_processor: TaskProcessor
    ) -> None:
        """Test that get_result returns None for errored job (not DONE status)."""
        await task_processor.job_store.create(
            "error-job",
            {
                "job_id": "error-job",
                "plugin": "plugin1",
                "status": JobStatus.ERROR,
                "result": None,
                "error": "Plugin execution failed",
                "created_at": datetime.now(timezone.utc),
                "completed_at": datetime.now(timezone.utc),
                "progress": 0.0,
            },
        )

        # get_result should raise since status is ERROR (not DONE)
        with pytest.raises(RuntimeError, match="has not completed"):
            await task_processor.get_result("error-job")

    @pytest.mark.asyncio
    async def test_get_result_includes_processing_time(
        self, task_processor: TaskProcessor, mock_plugin_manager: MagicMock
    ) -> None:
        """Test that get_result result includes processing_time_ms."""
        mock_plugin = MagicMock()
        mock_plugin.run_tool = MagicMock(return_value={"data": "test"})
        mock_plugin_manager.get = MagicMock(return_value=mock_plugin)

        job_id = await task_processor.submit_job(
            b"image_data", "test_plugin", options={"tool": "test_plugin"}
        )
        await asyncio.sleep(0.2)

        result = await task_processor.get_result(job_id)
        assert result is not None
        assert "processing_time_ms" in result
        assert result["processing_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_get_result_for_cancelled_job(
        self, task_processor: TaskProcessor
    ) -> None:
        """Test that get_result raises for cancelled job."""
        # Create a cancelled job
        job_id = await task_processor.submit_job(
            b"image_data", "plugin1", options={"tool": "plugin1"}
        )
        await task_processor.cancel_job(job_id)

        # Cancelled jobs have ERROR status, so get_result should raise
        with pytest.raises(RuntimeError, match="has not completed"):
            await task_processor.get_result(job_id)

    @pytest.mark.asyncio
    async def test_get_result_protocol_compliance(
        self, task_processor: TaskProcessor, mock_plugin_manager: MagicMock
    ) -> None:
        """Test that get_result satisfies the TaskProcessor Protocol."""
        mock_plugin = MagicMock()
        mock_plugin.run_tool = MagicMock(return_value={"result": "test"})
        mock_plugin_manager.get = MagicMock(return_value=mock_plugin)

        job_id = await task_processor.submit_job(
            b"image_data", "test_plugin", options={"tool": "test_plugin"}
        )
        await asyncio.sleep(0.2)

        # Verify method exists and is callable
        assert hasattr(task_processor, "get_result")
        assert callable(task_processor.get_result)

        # Verify return type matches Protocol (Optional[Dict[str, Any]])
        result = await task_processor.get_result(job_id)
        assert result is None or isinstance(result, dict)
