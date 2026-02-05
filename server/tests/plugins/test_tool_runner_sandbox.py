"""Tests for ToolRunner sandbox integration (Commit 5).

Verifies that plugin tool execution is properly wrapped in sandbox
with state tracking and error isolation.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.plugins.loader.plugin_registry import PluginRegistry, get_registry
from app.plugins.sandbox import run_plugin_sandboxed
from app.plugins.sandbox.sandbox_runner import PluginSandboxResult
from app.services.plugin_management_service import PluginManagementService


class MockPlugin:
    """Mock plugin for testing."""

    name = "test_plugin"

    def __init__(self):
        self.tools = {
            "echo": {
                "handler": "echo_tool",
                "description": "Echo tool",
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"},
            }
        }

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
    """Create a fresh registry for each test."""
    registry = PluginRegistry()
    # Reset singleton for clean tests
    import app.plugins.loader.plugin_registry as pr_module

    pr_module._registry = registry
    return registry


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
        result = service.run_plugin_tool("test_plugin", "echo_tool", {"message": "hello"})

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
