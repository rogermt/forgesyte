"""TDD tests for plugin progress callback support."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.plugin_management_service import PluginManagementService


@pytest.fixture
def mock_registry():
    """Create a mock plugin registry."""
    registry = MagicMock()
    return registry


@pytest.mark.unit
def test_run_plugin_tool_accepts_progress_callback(mock_registry):
    """RED: Verify run_plugin_tool accepts progress_callback parameter."""
    service = PluginManagementService(mock_registry)

    # Mock plugin
    mock_plugin = MagicMock()
    mock_plugin.tools = {"detect": MagicMock()}
    mock_plugin.run_tool = MagicMock(return_value={"result": "ok"})
    mock_registry.get.return_value = mock_plugin

    # Mock health registry
    mock_health_registry = MagicMock()
    mock_health_registry.get_status.return_value = None
    mock_health_registry.record_success = MagicMock()

    with patch(
        "app.services.plugin_management_service.get_registry",
        return_value=mock_health_registry,
    ):
        # Define progress callback
        def progress_callback(current: int, total: int) -> None:
            pass

        # Should not raise when progress_callback is provided
        service.run_plugin_tool(
            plugin_id="test-plugin",
            tool_name="detect",
            args={"video_path": "/tmp/test.mp4"},
            progress_callback=progress_callback,
        )


@pytest.mark.unit
def test_run_plugin_tool_without_callback_backward_compatible(mock_registry):
    """RED: Verify run_plugin_tool works without progress_callback."""
    service = PluginManagementService(mock_registry)

    # Mock plugin
    mock_plugin = MagicMock()
    mock_plugin.tools = {"detect": MagicMock()}
    mock_plugin.run_tool = MagicMock(return_value={"result": "ok"})
    mock_registry.get.return_value = mock_plugin

    # Mock health registry
    mock_health_registry = MagicMock()
    mock_health_registry.get_status.return_value = None
    mock_health_registry.record_success = MagicMock()

    with patch(
        "app.services.plugin_management_service.get_registry",
        return_value=mock_health_registry,
    ):
        # Should work without progress_callback (backward compatible)
        service.run_plugin_tool(
            plugin_id="test-plugin",
            tool_name="detect",
            args={"video_path": "/tmp/test.mp4"},
            # No progress_callback
        )


@pytest.mark.unit
def test_progress_callback_passed_to_tool_function(mock_registry):
    """RED: Verify progress_callback is passed to tool function."""
    service = PluginManagementService(mock_registry)

    # Mock plugin
    mock_plugin = MagicMock()
    mock_plugin.tools = {"detect": MagicMock()}
    mock_plugin.run_tool = MagicMock(return_value={"result": "ok"})
    mock_registry.get.return_value = mock_plugin

    # Mock health registry
    mock_health_registry = MagicMock()
    mock_health_registry.get_status.return_value = None
    mock_health_registry.record_success = MagicMock()

    with patch(
        "app.services.plugin_management_service.get_registry",
        return_value=mock_health_registry,
    ):
        # Define progress callback
        def progress_callback(current: int, total: int) -> None:
            pass

        # Run tool with callback
        service.run_plugin_tool(
            plugin_id="test-plugin",
            tool_name="detect",
            args={"video_path": "/tmp/test.mp4"},
            progress_callback=progress_callback,
        )

        # Verify run_tool was called
        mock_plugin.run_tool.assert_called_once()

        # run_tool(tool_name, kwargs_dict) - check the kwargs dict
        call_args = mock_plugin.run_tool.call_args
        # call_args[0] is positional args, [1] is kwargs
        # run_tool is called as: plugin.run_tool(tool_name, kw)
        # where kw is a dict containing the args + progress_callback
        kwargs_dict = call_args[0][1]  # Second positional arg is the kwargs dict

        # The progress_callback should be in the kwargs dict
        assert "progress_callback" in kwargs_dict
        assert kwargs_dict["progress_callback"] == progress_callback
