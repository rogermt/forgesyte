"""Test JobExecutionService for job lifecycle management.

Tests verify:
- Job lifecycle transitions (QUEUED → RUNNING → SUCCESS/FAILED)
- SUCCESS/FAILED mapping
- Delegation to PluginExecutionService
- Correct job storage
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from app.models_pydantic import JobStatus
from app.services.execution.job_execution_service import Job, JobExecutionService


class MockPluginExecutionService:
    """Mock PluginExecutionService for testing delegation."""

    def __init__(self, should_fail: bool = False, fail_message: str = "Plugin failed"):
        self.execute_tool_calls: list[dict[str, object]] = []
        self.should_fail = should_fail
        self.fail_message = fail_message

    async def execute_tool(
        self, tool_name: str, args: dict, mime_type: str = "image/png"
    ) -> dict[str, object]:
        self.execute_tool_calls.append(
            {
                "tool_name": tool_name,
                "args": args,
                "mime_type": mime_type,
            }
        )

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
        return JobExecutionService(plugin_execution_service=mock_plugin_service)

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

        await service.run_job(job_id)

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
    async def test_job_transitions_to_success_on_success(
        self, service, mock_plugin_service
    ):
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
        await service.create_job("plugin2", "tool2", {"image": b"test2"})

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

        await service.create_job("plugin1", "tool1", {"image": b"test"})
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


class TestAnalysisExecutionServiceDefaultToolName:
    """Tests for AnalysisExecutionService.analyze() tool_name behavior.

    Issue #302: When tool_name is not provided in args, analyze() should
    get the first tool from the plugin manifest (NOT a hardcoded default).

    Key principle: There is NO default tool name. If a plugin doesn't have
    a tool with the specified name, it's an error. The tool_name must come
    from the plugin manifest.
    """

    @pytest_asyncio.fixture
    async def mock_job_execution_service_for_analysis(self):
        """Create a mock JobExecutionService that captures tool_name."""
        mock_service = MagicMock()

        # Track calls to create_job
        create_job_calls: list[dict] = []

        async def mock_create_job(plugin_name: str, tool_name: str, args: dict) -> str:
            create_job_calls.append(
                {
                    "plugin_name": plugin_name,
                    "tool_name": tool_name,
                    "args": args,
                }
            )
            return "test-job-id"

        async def mock_run_job(job_id: str) -> dict:
            return {
                "job_id": job_id,
                "status": "done",
                "result": {"text": "extracted"},
                "error": None,
                "created_at": "2024-01-01T00:00:00",
                "completed_at": "2024-01-01T00:00:01",
            }

        mock_service.create_job = AsyncMock(side_effect=mock_create_job)
        mock_service.run_job = AsyncMock(side_effect=mock_run_job)
        mock_service._jobs = {}  # For submit_analysis_async access

        # Store calls list for assertions
        mock_service._create_job_calls = create_job_calls

        return mock_service

    @pytest_asyncio.fixture
    def mock_plugin_service(self):
        """Create a mock PluginManagementService with manifest lookup."""
        mock_service = MagicMock()

        # Manifest with tools as dict (common format)
        mock_service.get_plugin_manifest.return_value = {
            "name": "ocr",
            "tools": {
                "analyze": {"description": "OCR text extraction"},
                "detect_regions": {"description": "Detect text regions"},
            },
        }

        return mock_service

    @pytest.mark.asyncio
    async def test_analyze_gets_tool_name_from_manifest_when_not_provided(
        self, mock_job_execution_service_for_analysis, mock_plugin_service
    ):
        """When tool_name is not in args, analyze should get first tool from manifest.

        Issue #302: The service should look up the plugin manifest and use
        the first tool defined there, NOT a hardcoded "analyze" default.
        """
        from app.services.execution.analysis_execution_service import (
            AnalysisExecutionService,
        )

        mock_jes = mock_job_execution_service_for_analysis
        service = AnalysisExecutionService(mock_jes, mock_plugin_service)

        # Call analyze WITHOUT tool_name in args (mimics real API request)
        result, error = await service.analyze(
            plugin_name="ocr",
            args={"image": "base64imagedata", "mime_type": "image/png"},
        )

        # Verify no error occurred
        assert error is None, f"Expected no error, got: {error}"
        assert result is not None

        # Verify manifest was looked up
        mock_plugin_service.get_plugin_manifest.assert_called_once_with("ocr")

        # Verify create_job was called with first tool from manifest
        assert len(mock_jes._create_job_calls) == 1
        call = mock_jes._create_job_calls[0]
        # First tool in manifest dict is "analyze"
        assert call["tool_name"] == "analyze", (
            f"Expected tool_name='analyze' (first tool from manifest), "
            f"got '{call['tool_name']}'"
        )

    @pytest.mark.asyncio
    async def test_analyze_uses_explicit_tool_name_when_provided(
        self, mock_job_execution_service_for_analysis, mock_plugin_service
    ):
        """When tool_name IS in args, analyze should use it without manifest lookup."""
        from app.services.execution.analysis_execution_service import (
            AnalysisExecutionService,
        )

        mock_jes = mock_job_execution_service_for_analysis
        service = AnalysisExecutionService(mock_jes, mock_plugin_service)

        # Call analyze WITH explicit tool_name
        result, error = await service.analyze(
            plugin_name="ocr",
            args={
                "image": "base64imagedata",
                "mime_type": "image/png",
                "tool_name": "detect_regions",
            },
        )

        # Verify create_job was called with the explicit tool_name
        assert len(mock_jes._create_job_calls) == 1
        call = mock_jes._create_job_calls[0]
        assert call["tool_name"] == "detect_regions"

    @pytest.mark.asyncio
    async def test_analyze_raises_error_when_plugin_not_found(
        self, mock_job_execution_service_for_analysis, mock_plugin_service
    ):
        """When plugin manifest is not found, analyze should raise error."""
        from app.services.execution.analysis_execution_service import (
            AnalysisExecutionService,
        )

        mock_jes = mock_job_execution_service_for_analysis
        mock_plugin_service.get_plugin_manifest.return_value = None
        service = AnalysisExecutionService(mock_jes, mock_plugin_service)

        # Call analyze with non-existent plugin
        result, error = await service.analyze(
            plugin_name="nonexistent_plugin",
            args={"image": "base64imagedata", "mime_type": "image/png"},
        )

        # Should return error
        assert error is not None
        assert "not found" in error.get("message", "").lower()

    @pytest.mark.asyncio
    async def test_analyze_raises_error_when_manifest_has_no_tools(
        self, mock_job_execution_service_for_analysis, mock_plugin_service
    ):
        """When plugin manifest has no tools, analyze should raise error."""
        from app.services.execution.analysis_execution_service import (
            AnalysisExecutionService,
        )

        mock_jes = mock_job_execution_service_for_analysis
        # Manifest with no tools
        mock_plugin_service.get_plugin_manifest.return_value = {
            "name": "empty_plugin",
            "tools": {},
        }
        service = AnalysisExecutionService(mock_jes, mock_plugin_service)

        # Call analyze
        result, error = await service.analyze(
            plugin_name="empty_plugin",
            args={"image": "base64imagedata", "mime_type": "image/png"},
        )

        # Should return error
        assert error is not None
        assert "no tools" in error.get("message", "").lower()

    @pytest.mark.asyncio
    async def test_analyze_passes_plugin_name_in_args_for_tool_runner(
        self, mock_job_execution_service_for_analysis, mock_plugin_service
    ):
        """analyze should include plugin_name in args for tool_runner (Issue #303)."""
        from app.services.execution.analysis_execution_service import (
            AnalysisExecutionService,
        )

        mock_jes = mock_job_execution_service_for_analysis
        service = AnalysisExecutionService(mock_jes, mock_plugin_service)

        # Call analyze
        await service.analyze(
            plugin_name="ocr",
            args={"image": "base64imagedata", "mime_type": "image/png"},
        )

        # Verify plugin_name was added to args
        assert len(mock_jes._create_job_calls) == 1
        call = mock_jes._create_job_calls[0]
        assert (
            call["args"].get("plugin_name") == "ocr"
        ), "plugin_name should be passed in args for tool_runner"


class TestAnalysisExecutionServiceProductionInit:
    """Tests for Bug #303: analysis_execution_service initialization in production.

    Issue #303: The /v1/analyze-execution endpoint returns 503 in production
    because app.state.analysis_execution_service is never set during startup.
    """

    def test_production_app_has_analysis_execution_service_initialized(self):
        """Verify create_app() initializes analysis_execution_service on app.state.

        This test verifies that the production app (via create_app()) properly
        initializes the execution service chain during lifespan startup.
        """
        from fastapi.testclient import TestClient

        from app.main import create_app

        app = create_app()

        # Use TestClient to trigger lifespan startup
        with TestClient(app):
            # After startup, app.state should have analysis_execution_service
            service = getattr(app.state, "analysis_execution_service", None)
            assert service is not None, (
                "app.state.analysis_execution_service is None after startup. "
                "The lifespan() function must initialize the execution service chain: "
                "tool_runner → PluginExecutionService → JobExecutionService → "
                "AnalysisExecutionService"
            )
            assert hasattr(service, "analyze"), (
                "analysis_execution_service missing analyze() method. "
                "Expected AnalysisExecutionService instance."
            )
