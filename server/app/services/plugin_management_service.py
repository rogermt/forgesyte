"""Plugin management service for discovering and controlling plugins.

This service provides an abstraction layer for plugin operations:
- List available plugins with metadata
- Retrieve detailed plugin information
- Reload individual plugins
- Reload all plugins at once

The service depends on the PluginRegistry protocol, enabling testability
and support for different plugin storage backends.

Example:
    from .plugin_management_service import PluginManagementService

    service = PluginManagementService(plugin_registry)
    plugins = await service.list_plugins()
    info = await service.get_plugin_info("ocr")
    success = await service.reload_plugin("ocr")
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..protocols import PluginRegistry

logger = logging.getLogger(__name__)


class PluginManagementService:
    """Service for managing vision plugins.

    Responsible for:
    - Discovering available plugins
    - Retrieving plugin metadata and capabilities
    - Reloading plugins for live updates

    Depends on Protocols for flexibility:
    - PluginRegistry: Abstracts plugin storage and lifecycle
    """

    def __init__(self, registry: PluginRegistry) -> None:
        """Initialize plugin management service with registry.

        Args:
            registry: Plugin registry implementing PluginRegistry protocol

        Raises:
            TypeError: If registry doesn't have required methods
        """
        self.registry = registry
        logger.debug("PluginManagementService initialized")

    async def list_plugins(self) -> List[Dict[str, Any]]:
        """List all available vision plugins with metadata.

        Retrieves metadata for all loaded plugins including:
        - Name and version
        - Description and capabilities
        - Input/output specifications
        - Configuration options

        Returns:
            List of plugin metadata dictionaries, each containing:
                - name: Plugin identifier
                - version: Semantic version
                - description: Human-readable description
                - capabilities: List of analysis capabilities
                - input_formats: Supported image formats
                - output_schema: Result structure

        Raises:
            RuntimeError: If plugin registry is unavailable
        """
        try:
            plugins_dict = self.registry.list()
            plugins_list = (
                list(plugins_dict.values())
                if isinstance(plugins_dict, dict)
                else plugins_dict
            )

            logger.debug("Listed plugins", extra={"count": len(plugins_list)})
            return plugins_list
        except Exception as e:
            logger.exception("Failed to list plugins", extra={"error": str(e)})
            raise

    async def get_plugin_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific plugin.

        Retrieves comprehensive metadata for a single plugin:
        - Basic info: name, version, description
        - Capabilities: what analyses it can perform
        - Configuration: available options and defaults
        - Status: whether currently loaded and operational

        Args:
            name: Plugin identifier

        Returns:
            Plugin metadata dictionary if found, None if not found
            Contains: name, version, description, capabilities, etc.

        Raises:
            RuntimeError: If plugin registry is unavailable
        """
        try:
            plugin = self.registry.get(name)
            if plugin:
                # Plugin may be a loaded instance with metadata() method
                if hasattr(plugin, "metadata") and callable(plugin.metadata):
                    metadata = plugin.metadata()
                    logger.debug("Retrieved plugin info", extra={"plugin": name})
                    return metadata  # type: ignore[return-value]
                else:
                    # Or may be a dict if from list()
                    logger.debug("Retrieved plugin info", extra={"plugin": name})
                    return plugin  # type: ignore[return-value]
            else:
                logger.debug("Plugin not found", extra={"plugin": name})
                return None
        except Exception as e:
            logger.exception(
                "Failed to retrieve plugin info",
                extra={"plugin": name, "error": str(e)},
            )
            raise

    async def reload_plugin(self, name: str) -> bool:
        """Reload a specific plugin to refresh code and state.

        Triggers reload of a single plugin:
        - Unloads current plugin instance
        - Reloads plugin code from disk
        - Reinitializes plugin with fresh state
        - Validates plugin after reload

        This is useful for:
        - Applying code updates without server restart
        - Recovering from plugin errors
        - Testing plugin changes in development

        Args:
            name: Plugin identifier

        Returns:
            True if reload succeeded, False if reload failed or plugin not found

        Raises:
            RuntimeError: If plugin registry is unavailable
        """
        try:
            success = self.registry.reload_plugin(name)
            if success:
                logger.info("Plugin reloaded successfully", extra={"plugin": name})
            else:
                logger.warning(
                    "Failed to reload plugin",
                    extra={"plugin": name, "reason": "reload failed or not found"},
                )
            return success
        except Exception as e:
            logger.exception(
                "Error during plugin reload",
                extra={"plugin": name, "error": str(e)},
            )
            raise

    async def reload_all_plugins(self) -> Dict[str, Any]:
        """Reload all plugins to refresh code and state.

        Triggers reload of all registered plugins:
        - Unloads all plugin instances
        - Reloads all plugin code from disk
        - Reinitializes all plugins with fresh state
        - Validates all plugins after reload

        Returns:
            Dictionary with reload results:
                - success: Boolean indicating overall success
                - reloaded: List of successfully reloaded plugin names
                - failed: List of plugins that failed to reload
                - total: Total number of plugins
                - errors: Optional dict mapping failed plugin names to errors

        Raises:
            RuntimeError: If plugin registry is unavailable
        """
        try:
            result = self.registry.reload_all()
            logger.info(
                "All plugins reloaded",
                extra={
                    "total": result.get("total", 0),
                    "reloaded": len(result.get("reloaded", [])),
                    "failed": len(result.get("failed", [])),
                },
            )
            return result
        except Exception as e:
            logger.exception(
                "Error during reload all plugins",
                extra={"error": str(e)},
            )
            raise

    def get_plugin_manifest(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get manifest from a loaded plugin.

        Reads the plugin's manifest.json file if available. This is a synchronous
        operation that should be fast (usually <10ms) since manifests are small.

        Args:
            plugin_id: Plugin ID

        Returns:
            Manifest dict from manifest.json, or None if plugin not found

        Raises:
            Exception: If manifest file cannot be read
        """
        # Find plugin in registry by ID
        plugin = self.registry.get(plugin_id)
        if not plugin:
            return None

        # Try to read manifest.json from plugin module
        try:
            # Get plugin module
            plugin_module_name = plugin.__class__.__module__
            plugin_module = sys.modules.get(plugin_module_name)
            if not plugin_module or not hasattr(plugin_module, "__file__"):
                logger.warning(
                    f"Could not locate module for plugin '{plugin_id}': "
                    f"{plugin_module_name}"
                )
                return None

            # Find manifest.json relative to plugin module
            module_file = plugin_module.__file__
            if not module_file:
                return None

            plugin_dir = Path(module_file).parent
            manifest_path = plugin_dir / "manifest.json"

            if not manifest_path.exists():
                logger.warning(
                    f"No manifest.json found for plugin '{plugin_id}' "
                    f"at {manifest_path}"
                )
                return None

            with open(manifest_path, "r") as f:
                manifest = json.load(f)

            logger.debug(
                f"Loaded manifest for plugin '{plugin_id}': "
                f"{len(manifest.get('tools', {}))} tools"
            )

            return manifest

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in manifest for '{plugin_id}': {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading manifest for plugin '{plugin_id}': {e}")
            raise

    def run_plugin_tool(
        self,
        plugin_id: str,
        tool_name: str,
        args: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a plugin tool with given arguments.

        Finds the plugin, locates the tool function, validates arguments,
        and executes the tool. Handles both sync and async tool functions.

        Args:
            plugin_id: Plugin ID
            tool_name: Tool function name (must exist as method on plugin)
            args: Tool arguments (dict, should match manifest input schema)

        Returns:
            Tool result dict (should match manifest output schema)

        Raises:
            ValueError: Plugin/tool not found, or validation error
            TimeoutError: Tool execution exceeded timeout
            Exception: Tool execution failed
        """
        # 1. Find plugin in registry
        plugins_dict = self.registry.list()
        if isinstance(plugins_dict, dict):
            plugin = plugins_dict.get(plugin_id)
        else:
            plugin = next(
                (p for p in plugins_dict if getattr(p, "name", None) == plugin_id),
                None,
            )

        if not plugin:
            available = (
                list(plugins_dict.keys())
                if isinstance(plugins_dict, dict)
                else [getattr(p, "name", "unknown") for p in plugins_dict]
            )
            raise ValueError(
                f"Plugin '{plugin_id}' not found. " f"Available: {available}"
            )

        logger.debug(f"Found plugin: {plugin}")

        # 2. Validate tool exists
        if not hasattr(plugin, tool_name) or not callable(getattr(plugin, tool_name)):
            available_tools = [
                attr
                for attr in dir(plugin)
                if not attr.startswith("_") and callable(getattr(plugin, attr))
            ]
            raise ValueError(
                f"Tool '{tool_name}' not found in plugin '{plugin_id}'. "
                f"Available: {available_tools}"
            )

        logger.debug(f"Found tool: {plugin}.{tool_name}")

        # 3. Get tool function
        tool_func = getattr(plugin, tool_name)

        # 4. Execute tool (handle async/sync)
        try:
            if asyncio.iscoroutinefunction(tool_func):
                # Async tool: run in event loop with timeout
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    result = loop.run_until_complete(
                        asyncio.wait_for(
                            tool_func(**args),
                            timeout=30.0,  # 30-second timeout per frame
                        )
                    )
                finally:
                    loop.close()
            else:
                # Sync tool: call directly
                result = tool_func(**args)

            result_keys = list(result.keys()) if isinstance(result, dict) else "unknown"
            logger.debug(f"Tool returned result with keys: {result_keys}")

            return result

        except asyncio.TimeoutError as e:
            raise TimeoutError(
                f"Tool '{tool_name}' execution exceeded 30 second timeout"
            ) from e

        except TypeError as e:
            # Argument mismatch
            raise ValueError(
                f"Invalid arguments for tool '{tool_name}': {e}. "
                f"Check manifest input schema."
            ) from e

        except Exception as e:
            # Tool execution error
            logger.error(
                f"Tool '{tool_name}' execution failed: {e}",
                exc_info=True,
            )
            raise Exception(f"Tool execution error: {str(e)}") from e
