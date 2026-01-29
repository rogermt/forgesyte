"""Tests for PluginManagementService."""

import os
import sys
from unittest.mock import Mock

import pytest

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.protocols import PluginRegistry
from app.services.plugin_management_service import PluginManagementService


class TestPluginManagementService:
    """Test PluginManagementService functionality."""

    @pytest.fixture
    def mock_registry(self):
        return Mock(spec=PluginRegistry)

    @pytest.fixture
    def service(self, mock_registry):
        return PluginManagementService(registry=mock_registry)

    @pytest.mark.asyncio
    async def test_list_plugins_success(self, service, mock_registry):
        """Test listing plugins successfully."""
        plugins_dict = {
            "plugin1": {"name": "plugin1", "version": "1.0"},
            "plugin2": {"name": "plugin2", "version": "2.0"},
        }
        mock_registry.list.return_value = plugins_dict

        result = await service.list_plugins()

        assert len(result) == 2
        assert result[0]["name"] == "plugin1"
        assert result[1]["name"] == "plugin2"

    @pytest.mark.asyncio
    async def test_list_plugins_exception(self, service, mock_registry):
        """Test exception handling in list_plugins."""
        mock_registry.list.side_effect = Exception("Registry Error")

        with pytest.raises(Exception, match="Registry Error"):
            await service.list_plugins()

    @pytest.mark.asyncio
    async def test_get_plugin_info_found_instance(self, service, mock_registry):
        """Test getting plugin info when plugin is an object with metadata()."""
        mock_plugin = Mock()
        mock_plugin.metadata.return_value = {"name": "plugin1", "version": "1.0"}
        mock_registry.get.return_value = mock_plugin

        result = await service.get_plugin_info("plugin1")

        # Service returns the plugin instance, not the metadata
        assert result is mock_plugin
        # Caller would call metadata() to get the dict
        assert result.metadata() == {"name": "plugin1", "version": "1.0"}

    @pytest.mark.asyncio
    async def test_get_plugin_info_found_dict(self, service, mock_registry):
        """Test getting plugin info when registry returns a dict."""
        plugin_data = {"name": "plugin1", "version": "1.0"}
        # Mock registry.get to return dict directly (simulating some implementations)
        # However, registry.get typically returns the plugin instance.
        # If the service handles it, let's test it.
        # The service code:
        # if hasattr(plugin, "metadata") and callable(plugin.metadata): ...
        # else: return plugin
        mock_registry.get.return_value = plugin_data

        result = await service.get_plugin_info("plugin1")

        assert result == plugin_data

    @pytest.mark.asyncio
    async def test_get_plugin_info_not_found(self, service, mock_registry):
        """Test getting plugin info when not found."""
        mock_registry.get.return_value = None

        result = await service.get_plugin_info("unknown")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_plugin_info_exception(self, service, mock_registry):
        """Test exception handling in get_plugin_info."""
        mock_registry.get.side_effect = Exception("Error")

        with pytest.raises(Exception, match="Error"):
            await service.get_plugin_info("plugin1")

    @pytest.mark.asyncio
    async def test_reload_plugin_success(self, service, mock_registry):
        """Test successful plugin reload."""
        mock_registry.reload_plugin.return_value = True

        result = await service.reload_plugin("plugin1")

        assert result is True
        mock_registry.reload_plugin.assert_called_once_with("plugin1")

    @pytest.mark.asyncio
    async def test_reload_plugin_failure(self, service, mock_registry):
        """Test failed plugin reload."""
        mock_registry.reload_plugin.return_value = False

        result = await service.reload_plugin("plugin1")

        assert result is False

    @pytest.mark.asyncio
    async def test_reload_plugin_exception(self, service, mock_registry):
        """Test exception handling in reload_plugin."""
        mock_registry.reload_plugin.side_effect = Exception("Reload Error")

        with pytest.raises(Exception, match="Reload Error"):
            await service.reload_plugin("plugin1")

    @pytest.mark.asyncio
    async def test_reload_all_plugins_success(self, service, mock_registry):
        """Test successful reload all plugins."""
        expected_result = {
            "success": True,
            "reloaded": ["p1", "p2"],
            "failed": [],
            "total": 2,
        }
        mock_registry.reload_all.return_value = expected_result

        result = await service.reload_all_plugins()

        assert result == expected_result
        mock_registry.reload_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_reload_all_plugins_exception(self, service, mock_registry):
        """Test exception handling in reload_all_plugins."""
        mock_registry.reload_all.side_effect = Exception("Reload All Error")

        with pytest.raises(Exception, match="Reload All Error"):
            await service.reload_all_plugins()

    def test_run_plugin_tool_success_sync(self, service, mock_registry):
        """Test successful sync tool execution via registry.get()."""
        # Create a mock plugin with a callable tool method
        mock_plugin = Mock()
        mock_plugin.test_tool.return_value = {"result": "success"}

        # registry.get() returns the plugin instance
        mock_registry.get.return_value = mock_plugin

        # Execute the tool
        result = service.run_plugin_tool(
            plugin_id="test-plugin",
            tool_name="test_tool",
            args={"arg1": "value1"},
        )

        assert result == {"result": "success"}
        mock_registry.get.assert_called_once_with("test-plugin")
        mock_plugin.test_tool.assert_called_once_with(arg1="value1")

    def test_run_plugin_tool_plugin_not_found(self, service, mock_registry):
        """Test ValueError when plugin not found."""
        # registry.get() returns None when plugin not found
        mock_registry.get.return_value = None
        mock_registry.list.return_value = {"other-plugin": {}}

        with pytest.raises(ValueError) as exc_info:
            service.run_plugin_tool(
                plugin_id="nonexistent",
                tool_name="some_tool",
                args={},
            )

        assert "Plugin 'nonexistent' not found" in str(exc_info.value)
        assert "other-plugin" in str(exc_info.value)
        mock_registry.get.assert_called_once_with("nonexistent")

    def test_run_plugin_tool_tool_not_found(self, service, mock_registry):
        """Test ValueError when tool not found on plugin."""
        mock_plugin = Mock(spec=["metadata"])  # No test_tool method
        mock_plugin.metadata.return_value = {"name": "test-plugin"}
        mock_registry.get.return_value = mock_plugin

        with pytest.raises(ValueError) as exc_info:
            service.run_plugin_tool(
                plugin_id="test-plugin",
                tool_name="nonexistent_tool",
                args={},
            )

        assert "Tool 'nonexistent_tool' not found" in str(exc_info.value)

    def test_run_plugin_tool_get_returns_instance_not_metadata(
        self, service, mock_registry
    ):
        """Verify registry.get() returns PluginInterface instance, not metadata dict."""
        # Create a mock plugin instance with callable methods
        mock_plugin = Mock()
        mock_plugin.some_method.return_value = {"data": "test"}
        mock_plugin.metadata.return_value = {"name": "plugin1", "version": "1.0"}

        # Simulate the difference between registry.get() and registry.list()
        # registry.get() -> returns plugin instance (has callable methods)
        # registry.list() -> returns metadata dict (no callable methods)
        mock_registry.get.return_value = mock_plugin
        mock_registry.list.return_value = {
            "plugin1": {"name": "plugin1", "version": "1.0"}
        }

        # This should work because registry.get() returns the instance
        result = service.run_plugin_tool(
            plugin_id="plugin1",
            tool_name="some_method",
            args={},
        )

        assert result == {"data": "test"}
        mock_registry.get.assert_called_once_with("plugin1")

    def test_run_plugin_tool_success_async(self, service, mock_registry):
        """Test successful async tool execution via run_plugin_tool."""

        # Create a mock async plugin method
        # Note: run_plugin_tool handles the event loop internally
        async def async_tool(**kwargs):
            return {"async_result": "success"}

        mock_plugin = Mock()
        mock_plugin.async_tool = async_tool

        mock_registry.get.return_value = mock_plugin

        result = service.run_plugin_tool(
            plugin_id="async-plugin",
            tool_name="async_tool",
            args={"param": "value"},
        )

        assert result == {"async_result": "success"}
