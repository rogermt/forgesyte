"""Test PluginExecutionService for delegation to ToolRunner.

Tests verify:
- Delegation to ToolRunner
- Correct return shape
- No direct plugin.run() calls
- Input/output validation
"""

import pytest
import pytest_asyncio

from app.core.validation.execution_validation import (
    InputValidationError,
    OutputValidationError,
)
from app.services.execution.plugin_execution_service import PluginExecutionService


class MockToolRunner:
    """Mock ToolRunner for testing delegation."""

    def __init__(self, should_fail: bool = False, fail_message: str = "Tool failed"):
        self.call_count: int = 0
        self.last_tool_name: str | None = None
        self.last_args: dict[str, object] | None = None
        self.should_fail = should_fail
        self.fail_message = fail_message

    async def __call__(self, tool_name: str, args: dict):
        self.call_count += 1
        self.last_tool_name = tool_name
        self.last_args = args

        if self.should_fail:
            raise RuntimeError(self.fail_message)

        return {"result": "success", "data": [1, 2, 3]}


class TestPluginExecutionService:
    """Tests for PluginExecutionService."""

    @pytest_asyncio.fixture
    async def mock_tool_runner(self):
        """Create a mock ToolRunner."""
        return MockToolRunner()

    @pytest_asyncio.fixture
    async def service(self, mock_tool_runner):
        """Create a PluginExecutionService instance."""
        return PluginExecutionService(tool_runner=mock_tool_runner)

    @pytest.mark.asyncio
    async def test_delegates_to_tool_runner(self, service, mock_tool_runner):
        """Service should delegate execution to ToolRunner."""
        await service.execute_tool(
            tool_name="test_tool",
            args={"image": b"test_image_data", "option": "value"},
        )

        # Verify ToolRunner was called
        assert mock_tool_runner.call_count == 1
        assert mock_tool_runner.last_tool_name == "test_tool"
        assert mock_tool_runner.last_args == {
            "image": b"test_image_data",
            "option": "value",
        }

    @pytest.mark.asyncio
    async def test_returns_validated_result(self, service, mock_tool_runner):
        """Service should return validated result from ToolRunner."""
        result = await service.execute_tool(
            tool_name="test_tool",
            args={"image": b"test_image_data"},
        )

        # Verify result shape
        assert isinstance(result, dict)
        assert result == {"result": "success", "data": [1, 2, 3]}

    @pytest.mark.asyncio
    async def test_validates_input_payload(self, service, mock_tool_runner):
        """Service should validate input payload before execution."""
        # Missing image
        with pytest.raises(InputValidationError):
            await service.execute_tool(
                tool_name="test_tool",
                args={},  # No image
            )

        # ToolRunner should NOT be called
        assert mock_tool_runner.call_count == 0

    @pytest.mark.asyncio
    async def test_validates_output_from_tool_runner(self):
        """Service should validate output from ToolRunner."""

        # Create a runner that returns None
        class NoneReturningRunner:
            async def __call__(self, tool_name: str, args: dict) -> None:
                return None

        service_none = PluginExecutionService(tool_runner=NoneReturningRunner())

        with pytest.raises(OutputValidationError):
            await service_none.execute_tool(
                tool_name="test_tool",
                args={"image": b"test_image_data"},
            )

    @pytest.mark.asyncio
    async def test_propagates_tool_runner_errors(self):
        """Service should propagate errors from ToolRunner."""
        mock_runner_fail = MockToolRunner(should_fail=True)
        service_fail = PluginExecutionService(tool_runner=mock_runner_fail)

        with pytest.raises(Exception) as exc_info:
            await service_fail.execute_tool(
                tool_name="failing_tool",
                args={"image": b"test_image_data"},
            )

        assert "Tool failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_no_direct_plugin_run_calls(self, service, mock_tool_runner):
        """Service should NOT call plugin.run() directly - only ToolRunner."""
        # This test verifies the architecture: PluginExecutionService
        # only knows about ToolRunner (the callable passed in),
        # not about plugins or their run() method.

        # Execute a tool
        await service.execute_tool(
            tool_name="some_tool",
            args={"image": b"test"},
        )

        # Verify the contract: service only calls the tool_runner callable
        assert mock_tool_runner.call_count == 1
        # The service itself doesn't have a reference to any plugin
        assert not hasattr(service, "_plugin")
        assert not hasattr(service, "run")


class TestSyncExecution:
    """Tests for synchronous execution path.

    Note: execute_tool_sync is async to support both sync and async tool runners.
    """

    @pytest.fixture
    def sync_tool_runner(self):
        """Create a synchronous mock ToolRunner."""

        class SyncRunner:
            def __init__(self):
                self.call_count = 0
                self.last_tool_name = None
                self.last_args = None

            def __call__(self, tool_name: str, args: dict):
                self.call_count += 1
                self.last_tool_name = tool_name
                self.last_args = args
                return {"result": "sync_success", "data": [4, 5, 6]}

        return SyncRunner()

    @pytest.mark.asyncio
    async def test_execute_tool_sync_validates_input(self, sync_tool_runner):
        """Sync execution should also validate input."""
        service = PluginExecutionService(tool_runner=sync_tool_runner)

        # Missing image should raise
        with pytest.raises(InputValidationError):
            await service.execute_tool_sync(
                tool_name="test_tool",
                args={},
            )

        assert sync_tool_runner.call_count == 0

    @pytest.mark.asyncio
    async def test_execute_tool_sync_returns_result(self, sync_tool_runner):
        """Sync execution should return validated result."""
        service = PluginExecutionService(tool_runner=sync_tool_runner)

        result = await service.execute_tool_sync(
            tool_name="test_tool",
            args={"image": b"test_image_data"},
        )

        assert result == {"result": "sync_success", "data": [4, 5, 6]}
        assert sync_tool_runner.call_count == 1

    @pytest.mark.asyncio
    async def test_execute_tool_sync_propagates_errors(self):
        """Sync execution should propagate errors."""

        class FailingRunner:
            def __call__(self, tool_name: str, args: dict):
                raise RuntimeError("Sync failure")

        service = PluginExecutionService(tool_runner=FailingRunner())

        with pytest.raises(Exception) as exc_info:
            await service.execute_tool_sync(
                tool_name="failing_tool",
                args={"image": b"test"},
            )

        assert "Sync failure" in str(exc_info.value)
