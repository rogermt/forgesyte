"""Tests for ToolRunner sandbox integration (Commit 5).

Verifies that plugin tool execution is properly wrapped in sandbox
with state tracking and error isolation.
"""

from unittest.mock import MagicMock

import pytest

from app.plugins.loader.plugin_registry import PluginRegistry
from app.plugins.sandbox import run_plugin_sandboxed
from app.services.plugin_management_service import PluginManagementService


class MockPlugin:
    """Mock plugin for testing."""

    name = "test_plugin"

    def __init__(self):
        self.tools = {
            "echo_tool": {
                "handler": "echo_tool",
                "description": "Echo tool",
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"},
            },
            "failing_tool": {
                "handler": "failing_tool",
                "description": "Failing tool",
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"},
            },
            "import_error_tool": {
                "handler": "import_error_tool",
                "description": "Import error tool",
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"},
            },
        }

    def run_tool(self, tool_name: str, args: dict) -> dict:
        """Dispatch tool by name (BasePlugin contract)."""
        handlers = {
            "echo_tool": self.echo_tool,
            "failing_tool": self.failing_tool,
            "import_error_tool": self.import_error_tool,
        }
        if tool_name not in handlers:
            raise ValueError(f"Unknown tool: {tool_name}")
        return handlers[tool_name](**args)

    def echo_tool(self, message: str = "") -> dict:
        """Simple echo tool."""
        return {"message": message}

    def failing_tool(self) -> dict:
        """Tool that raises an exception."""
        raise RuntimeError("Tool failed!")

    def import_error_tool(self) -> dict:
        """Tool that raises ImportError."""
        raise ImportError("Missing dependency")


@pytest.fixture
def registry():
    """Get the singleton registry for each test."""
    from app.plugins.loader.plugin_registry import get_registry

    # Reset singleton instance for clean tests (Phase 11)
    PluginRegistry._instance = None

    # Get fresh singleton
    return get_registry()


@pytest.fixture
def mock_plugin(registry):
    """Create and register a mock plugin."""
    plugin = MockPlugin()
    registry.register("test_plugin", "Test plugin", "1.0.0")
    registry.set_plugin_instance("test_plugin", plugin)
    registry.mark_initialized("test_plugin")
    return plugin


@pytest.fixture
def service(registry):
    """Create a plugin management service with mock registry."""
    # Create a mock registry that satisfies the protocol
    mock_registry = MagicMock()
    mock_registry.list.return_value = {}
    mock_registry.get.return_value = None
    return PluginManagementService(mock_registry)


class TestToolRunnerSandbox:
    """Test ToolRunner integration with sandbox."""

    def test_successful_tool_execution(self, registry, mock_plugin, service):
        """Test successful tool execution via sandbox."""
        # Setup: configure service to find our mock plugin
        service.registry.get.return_value = mock_plugin

        # Execute tool
        result = service.run_plugin_tool(
            "test_plugin", "echo_tool", {"message": "hello"}
        )

        # Verify result
        assert result == {"message": "hello"}

        # Verify state tracking
        status = registry.get_status("test_plugin")
        assert status.success_count == 1
        assert status.error_count == 0

    def test_sandbox_isolates_runtime_error(self, registry, mock_plugin, service):
        """Test that RuntimeError is isolated by sandbox."""
        # Setup
        service.registry.get.return_value = mock_plugin

        # Execute failing tool
        with pytest.raises(Exception) as exc_info:
            service.run_plugin_tool("test_plugin", "failing_tool", {})

        # Verify error was raised but isolated
        assert "Tool execution error" in str(exc_info.value)

        # Verify state tracking recorded error
        status = registry.get_status("test_plugin")
        assert status.error_count == 1

    def test_sandbox_isolates_import_error(self, registry, mock_plugin, service):
        """Test that ImportError is isolated by sandbox."""
        # Setup
        service.registry.get.return_value = mock_plugin

        # Execute tool with import error
        with pytest.raises(Exception) as exc_info:
            service.run_plugin_tool("test_plugin", "import_error_tool", {})

        # Verify error was raised but isolated
        assert "Tool execution error" in str(exc_info.value)

        # Verify state tracking recorded error
        status = registry.get_status("test_plugin")
        assert status.error_count == 1

    def test_mark_running_before_execution(self, registry, mock_plugin, service):
        """Test that plugin is marked RUNNING before execution."""
        # Setup
        service.registry.get.return_value = mock_plugin

        # Execute tool
        service.run_plugin_tool("test_plugin", "echo_tool", {"message": "test"})

        # Verify state was RUNNING at some point
        status = registry.get_status("test_plugin")
        assert status.last_used is not None

    def test_plugin_not_found_raises_value_error(self, service):
        """Test that missing plugin raises ValueError."""
        service.registry.get.return_value = None
        service.registry.list.return_value = {}

        with pytest.raises(ValueError) as exc_info:
            service.run_plugin_tool("missing_plugin", "tool", {})

        assert "not found" in str(exc_info.value)

    def test_tool_not_found_raises_value_error(self, mock_plugin, service):
        """Test that missing tool raises ValueError."""
        service.registry.get.return_value = mock_plugin

        with pytest.raises(ValueError) as exc_info:
            service.run_plugin_tool("test_plugin", "missing_tool", {})

        assert "not found" in str(exc_info.value)


class TestSandboxRunnerDirectly:
    """Test sandbox runner functions directly."""

    def test_run_plugin_sandboxed_success(self):
        """Test successful sandboxed execution."""

        def success_fn(x: int) -> int:
            return x * 2

        result = run_plugin_sandboxed(success_fn, x=5)

        assert result.ok is True
        assert result.result == 10
        assert result.error is None

    def test_run_plugin_sandboxed_runtime_error(self):
        """Test sandbox catches RuntimeError."""

        def fail_fn() -> None:
            raise RuntimeError("Test error")

        result = run_plugin_sandboxed(fail_fn)

        assert result.ok is False
        assert result.error_type == "RuntimeError"
        assert "Test error" in (result.error or "")

    def test_run_plugin_sandboxed_import_error(self):
        """Test sandbox catches ImportError."""

        def import_fail() -> None:
            raise ImportError("No module named 'missing'")

        result = run_plugin_sandboxed(import_fail)

        assert result.ok is False
        assert result.error_type == "ImportError"
        assert "No module named" in (result.error or "")

    def test_run_plugin_sandboxed_value_error(self):
        """Test sandbox catches ValueError."""

        def value_fail() -> None:
            raise ValueError("Invalid value")

        result = run_plugin_sandboxed(value_fail)

        assert result.ok is False
        assert result.error_type == "ValueError"

    def test_run_plugin_sandboxed_memory_error(self):
        """Test sandbox catches MemoryError."""

        def memory_fail() -> None:
            raise MemoryError("Out of memory")

        result = run_plugin_sandboxed(memory_fail)

        assert result.ok is False
        assert result.error_type == "MemoryError"

    def test_run_plugin_sandboxed_generic_exception(self):
        """Test sandbox catches generic Exception."""

        def generic_fail() -> None:
            raise Exception("Generic error")

        result = run_plugin_sandboxed(generic_fail)

        assert result.ok is False
        assert result.error_type == "Exception"
        assert "Generic error" in (result.error or "")


class TestRegistryStateTracking:
    """Test registry state tracking during tool execution."""

    def test_success_count_incremented(self, registry):
        """Test success count is incremented."""
        registry.register("test", "Test", "1.0")
        registry.record_success("test")
        registry.record_success("test")

        status = registry.get_status("test")
        assert status.success_count == 2

    def test_error_count_incremented(self, registry):
        """Test error count is incremented."""
        registry.register("test", "Test", "1.0")
        registry.record_error("test")

        status = registry.get_status("test")
        assert status.error_count == 1

    def test_mark_running_updates_last_used(self, registry):
        """Test mark_running updates last_used timestamp."""
        registry.register("test", "Test", "1.0")

        # Initially no last_used
        status = registry.get_status("test")
        assert status.last_used is None

        # After marking running
        registry.mark_running("test")
        status = registry.get_status("test")
        assert status.last_used is not None

    def test_plugin_instance_storage(self, registry):
        """Test plugin instance storage and retrieval."""
        mock_instance = {"name": "test_plugin"}

        registry.register("test", "Test", "1.0")
        registry.set_plugin_instance("test", mock_instance)

        retrieved = registry.get_plugin_instance("test")
        assert retrieved == mock_instance

    def test_get_plugin_instance_missing(self, registry):
        """Test getting missing plugin instance returns None."""
        result = registry.get_plugin_instance("nonexistent")
        assert result is None


class TestExecutionTimeTracking:
    """Test execution time tracking in sandbox and registry."""

    def test_sandbox_returns_execution_time_on_success(self):
        """Test that sandbox returns execution time on success."""

        def slow_fn() -> None:
            import time

            time.sleep(0.01)  # 10ms sleep

        result = run_plugin_sandboxed(slow_fn)

        assert result.ok is True
        assert result.execution_time_ms is not None
        assert result.execution_time_ms >= 10.0  # At least 10ms

    def test_sandbox_returns_execution_time_on_error(self):
        """Test that sandbox returns execution time even on error."""

        def slow_fail() -> None:
            import time

            time.sleep(0.01)  # 10ms sleep
            raise ValueError("Test error")

        result = run_plugin_sandboxed(slow_fail)

        assert result.ok is False
        assert result.execution_time_ms is not None
        assert result.execution_time_ms >= 10.0  # At least 10ms

    def test_execution_time_recorded_in_registry(self, registry):
        """Test that execution time is recorded in registry."""
        registry.register("test", "Test", "1.0")
        registry.record_success("test", 125.5)

        status = registry.get_status("test")
        assert status.last_execution_time_ms == 125.5
        assert status.avg_execution_time_ms == 125.5  # Average of 1 run

    def test_execution_time_error_recorded_in_registry(self, registry):
        """Test that execution time is recorded even on error."""
        registry.register("test", "Test", "1.0")
        registry.record_error("test", 85.3)

        status = registry.get_status("test")
        assert status.last_execution_time_ms == 85.3
        assert status.avg_execution_time_ms == 85.3

    def test_avg_execution_time_tracks_last_10_runs(self, registry):
        """Test that average is calculated from last 10 runs."""
        registry.register("test", "Test", "1.0")

        # Record 15 executions with different times
        for i in range(15):
            registry.record_success("test", 100.0 + i)

        status = registry.get_status("test")

        # Should track last 10 runs (105.0 to 114.0) - oldest 5 are dropped
        assert status.last_execution_time_ms == 114.0  # Last one (100 + 14)
        # Average of 105, 106, ..., 114 = 109.5
        assert status.avg_execution_time_ms == 109.5

    def test_execution_time_tracked_in_health_response(self, registry):
        """Test that execution time appears in health response."""
        registry.register("test", "Test", "1.0")
        registry.record_success("test", 42.5)

        status = registry.get_status("test")

        assert hasattr(status, "last_execution_time_ms")
        assert hasattr(status, "avg_execution_time_ms")
        assert status.last_execution_time_ms == 42.5
        assert status.avg_execution_time_ms == 42.5

    def test_execution_time_none_before_any_run(self, registry):
        """Test that execution time is None before any runs."""
        registry.register("test", "Test", "1.0")

        status = registry.get_status("test")

        assert status.last_execution_time_ms is None
        assert status.avg_execution_time_ms is None
