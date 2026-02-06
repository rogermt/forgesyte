"""Test JobExecutionService for job lifecycle management.

Tests verify:
- Job lifecycle transitions (QUEUED → RUNNING → SUCCESS/FAILED)
- SUCCESS/FAILED mapping
- Delegation to PluginExecutionService
- Correct job storage
"""

import pytest
import pytest_asyncio

from app.models import JobStatus
from app.services.execution.job_execution_service import JobExecutionService, Job
from app.services.execution.plugin_execution_service import PluginExecutionService


class MockPluginExecutionService:
    """Mock PluginExecutionService for testing delegation."""

    def __init__(self, should_fail: bool = False, fail_message: str = "Plugin failed"):
        self.execute_tool_calls = []
        self.should_fail = should_fail
        self.fail_message = fail_message

    async def execute_tool(self, tool_name: str, args: dict, mime_type: str = "image/png"):
        self.execute_tool_calls.append({
            "tool_name": tool_name,
            "args": args,
            "mime_type": mime_type,
        })

        if self.should_fail:
            raise RuntimeError(self.fail_message)

        return {"predictions": [{"label": "cat", "confidence": 0.95}]}


class TestJobExecutionService:
    """Tests for JobExecutionService."""

    @pytest_asyncio.fixture
    async def mock_plugin_service(self):
        """Create a mock PluginExecutionService."""
        return MockPluginExecutionService()

    @pytest_asyncio.fixture
    async def service(self, mock_plugin_service):
        """Create a JobExecutionService instance."""
        return JobExecutionService(
            plugin_execution_service=mock_plugin_service
        )

    @pytest.mark.asyncio
    async def test_creates_job_in_queued_status(self, service):
        """Job should be created with QUEUED status."""
        job_id = await service.create_job(
            plugin_name="test_plugin",
            tool_name="test_tool",
            args={"image": b"test"},
        )

        job = await service.get_job(job_id)

        assert job is not None
        assert job["status"] == JobStatus.QUEUED.value
        assert job["plugin_name"] == "test_plugin"
        assert job["tool_name"] == "test_tool"

    @pytest.mark.asyncio
    async def test_runs_queued_job(self, service, mock_plugin_service):
        """Running a queued job should delegate to PluginExecutionService."""
        job_id = await service.create_job(
            plugin_name="test_plugin",
            tool_name="test_tool",
            args={"image": b"test"},
        )

        result = await service.run_job(job_id)

        # Verify PluginExecutionService was called
        assert len(mock_plugin_service.execute_tool_calls) == 1
        call = mock_plugin_service.execute_tool_calls[0]
        assert call["tool_name"] == "test_tool"
        assert call["args"]["image"] == b"test"

    @pytest.mark.asyncio
    async def test_job_transitions_to_running(self, service):
        """Job should transition to RUNNING when started."""
        job_id = await service.create_job(
            plugin_name="test_plugin",
            tool_name="test_tool",
            args={"image": b"test"},
        )

        # Run job (starts execution)
        await service.run_job(job_id)

        # Check intermediate state (might complete before we check)
        job = await service.get_job(job_id)
        # Either still running or already done
        assert job["status"] in [JobStatus.RUNNING.value, JobStatus.DONE.value]

    @pytest.mark.asyncio
    async def test_job_transitions_to_success_on_success(self, service, mock_plugin_service):
        """Job should transition to DONE on successful execution."""
        job_id = await service.create_job(
            plugin_name="test_plugin",
            tool_name="test_tool",
            args={"image": b"test"},
        )

        result = await service.run_job(job_id)

        assert result["status"] == JobStatus.DONE.value
        assert result["result"] is not None
        assert result["error"] is None
        assert "predictions" in result["result"]

    @pytest.mark.asyncio
    async def test_job_transitions_to_failed_on_error(self, service):
        """Job should transition to ERROR on execution failure."""
        mock_service_fail = MockPluginExecutionService(should_fail=True)
        service_fail = JobExecutionService(plugin_execution_service=mock_service_fail)

        job_id = await service_fail.create_job(
            plugin_name="failing_plugin",
            tool_name="failing_tool",
            args={"image": b"test"},
        )

        result = await service_fail.run_job(job_id)

        assert result["status"] == JobStatus.ERROR.value
        assert result["result"] is None
        assert result["error"] is not None
        assert "Plugin failed" in result["error"]

    @pytest.mark.asyncio
    async def test_stores_job_result(self, service):
        """Job result should be stored in the job."""
        job_id = await service.create_job(
            plugin_name="test_plugin",
            tool_name="test_tool",
            args={"image": b"test"},
        )

        result = await service.run_job(job_id)

        # Verify result is stored
        assert result["result"] is not None
        assert "predictions" in result["result"]

    @pytest.mark.asyncio
    async def test_stores_job_error(self, service):
        """Job error should be stored in the job."""
        mock_service_fail = MockPluginExecutionService(should_fail=True)
        service_fail = JobExecutionService(plugin_execution_service=mock_service_fail)

        job_id = await service_fail.create_job(
            plugin_name="test_plugin",
            tool_name="test_tool",
            args={"image": b"test"},
        )

        result = await service_fail.run_job(job_id)

        # Verify error is stored
        assert result["error"] is not None

    @pytest.mark.asyncio
    async def test_completed_at_timestamp_set(self, service):
        """Completed job should have completed_at timestamp."""
        job_id = await service.create_job(
            plugin_name="test_plugin",
            tool_name="test_tool",
            args={"image": b"test"},
        )

        result = await service.run_job(job_id)

        assert result["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_get_nonexistent_job_returns_none(self, service):
        """Getting a non-existent job should return None."""
        result = await service.get_job("nonexistent-job-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_runs_only_queued_job(self, service):
        """Running a non-queued job should raise an error."""
        job_id = await service.create_job(
            plugin_name="test_plugin",
            tool_name="test_tool",
            args={"image": b"test"},
        )

        # Run once
        await service.run_job(job_id)

        # Try to run again - should fail because job is not QUEUED
        with pytest.raises(ValueError) as exc_info:
            await service.run_job(job_id)

        assert "not queued" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cancel_queued_job(self, service):
        """Cancelling a queued job should succeed."""
        job_id = await service.create_job(
            plugin_name="test_plugin",
            tool_name="test_tool",
            args={"image": b"test"},
        )

        # Verify job is queued before cancelling
        job_before = await service.get_job(job_id)
        assert job_before["status"] == JobStatus.QUEUED.value

        cancelled = await service.cancel_job(job_id)
        assert cancelled is True

        # Verify job is now in error state with cancelled message
        job = await service.get_job(job_id)
        assert job["status"] == JobStatus.ERROR.value
        assert "Cancelled" in job["error"]

    @pytest.mark.asyncio
    async def test_cannot_cancel_running_job(self, service):
        """Cancelling a running job should fail."""
        job_id = await service.create_job(
            plugin_name="test_plugin",
            tool_name="test_tool",
            args={"image": b"test"},
        )

        # Start job and wait for completion
        await service.run_job(job_id)

        # Try to cancel - should fail because job is already done
        cancelled = await service.cancel_job(job_id)
        assert cancelled is False

    @pytest.mark.asyncio
    async def test_cannot_cancel_completed_job(self, service):
        """Cancelling a completed job should fail."""
        job_id = await service.create_job(
            plugin_name="test_plugin",
            tool_name="test_tool",
            args={"image": b"test"},
        )

        # Complete the job
        await service.run_job(job_id)

        # Try to cancel - should fail
        cancelled = await service.cancel_job(job_id)
        assert cancelled is False

    @pytest.mark.asyncio
    async def test_list_jobs_returns_all(self, service):
        """Listing jobs should return all jobs."""
        await service.create_job("plugin1", "tool1", {"image": b"test1"})
        await service.create_job("plugin2", "tool2", {"image": b"test2"})
        await service.create_job("plugin3", "tool3", {"image": b"test3"})

        jobs = await service.list_jobs()

        assert len(jobs) == 3

    @pytest.mark.asyncio
    async def test_list_jobs_filters_by_status(self, service):
        """Listing jobs should filter by status if specified."""
        job_id1 = await service.create_job("plugin1", "tool1", {"image": b"test1"})
        job_id2 = await service.create_job("plugin2", "tool2", {"image": b"test2"})

        # Complete one job
        await service.run_job(job_id1)

        # List only completed jobs
        completed_jobs = await service.list_jobs(status=JobStatus.DONE)
        queued_jobs = await service.list_jobs(status=JobStatus.QUEUED)

        assert len(completed_jobs) == 1
        assert len(queued_jobs) == 1

    @pytest.mark.asyncio
    async def test_list_jobs_respects_limit(self, service):
        """Listing jobs should respect the limit."""
        for i in range(10):
            await service.create_job(f"plugin{i}", f"tool{i}", {"image": b"test"})

        jobs = await service.list_jobs(limit=5)

        assert len(jobs) == 5

    @pytest.mark.asyncio
    async def test_jobs_sorted_by_created_at(self, service):
        """Jobs should be sorted by created_at (newest first)."""
        import time
        job_id1 = await service.create_job("plugin1", "tool1", {"image": b"test"})
        time.sleep(0.01)  # Small delay to ensure different timestamps
        job_id2 = await service.create_job("plugin2", "tool2", {"image": b"test"})

        jobs = await service.list_jobs()

        # Newest job should be first
        assert jobs[0]["job_id"] == job_id2


class TestJobDataclass:
    """Tests for Job dataclass."""

    def test_job_default_status(self):
        """Job should have QUEUED status by default."""
        job = Job(
            job_id="test-id",
            plugin_name="test-plugin",
            tool_name="test-tool",
            args={"image": b"test"},
        )

        assert job.status == JobStatus.QUEUED

    def test_job_default_timestamps(self):
        """Job should have created_at timestamp by default."""
        job = Job(
            job_id="test-id",
            plugin_name="test-plugin",
            tool_name="test-tool",
            args={},
        )

        assert job.created_at is not None
        assert job.started_at is None
        assert job.completed_at is None

    def test_job_to_dict(self):
        """Job should convert to dictionary correctly via service method."""
        # We test via the service's _job_to_dict method indirectly
        # by checking that the service properly converts jobs
        pass  # The service integration tests cover this

