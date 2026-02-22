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

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from ..plugins.loader.plugin_registry import get_registry
from ..plugins.sandbox import run_plugin_sandboxed
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

    def get_plugin_instance(self, plugin_id: str):
        """Return the loaded plugin instance.

        Args:
            plugin_id: Plugin identifier

        Returns:
            Plugin instance with .tools attribute

        Raises:
            ValueError: If plugin not found
        """
        plugin = self.registry.get(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_id}' not found")
        return plugin

    def get_available_tools(self, plugin_id: str) -> List[str]:
        """Return the list of tool IDs defined in the plugin class.

        This is the canonical source of truth for tool validation,
        NOT the manifest.json file.

        Args:
            plugin_id: Plugin identifier

        Returns:
            List of tool names available in the plugin

        Raises:
            ValueError: If plugin not found or has no tools attribute
        """
        plugin = self.get_plugin_instance(plugin_id)
        if not hasattr(plugin, "tools"):
            raise ValueError(f"Plugin '{plugin_id}' has no tools attribute")
        return list(plugin.tools.keys())

    async def list_plugins(self) -> List[Any]:
        """List all available vision plugins with metadata.

        Retrieves metadata for all loaded plugins including:
        - Name and version
        - Description and capabilities
        - Input/output specifications
        - Configuration options

        Returns:
            List of Plugin instances, each with a metadata() method to get:
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

    async def get_plugin_info(self, name: str) -> Optional[Any]:
        """Get detailed information about a specific plugin.

        Retrieves comprehensive metadata for a single plugin:
        - Basic info: name, version, description
        - Capabilities: what analyses it can perform
        - Configuration: available options and defaults
        - Status: whether currently loaded and operational

        Args:
            name: Plugin identifier

        Returns:
            Plugin instance if found, None if not found.
            Call plugin.metadata() to get PluginMetadata with details:
                - name, version, description, capabilities, etc.

        Raises:
            RuntimeError: If plugin registry is unavailable
        """
        try:
            plugin = self.registry.get(name)
            if plugin:
                logger.debug("Retrieved plugin info", extra={"plugin": name})
                return plugin
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
                raw_manifest = json.load(f)

            from ..models_manifest import PluginManifest

            manifest_model = PluginManifest(**raw_manifest)
            manifest = manifest_model.model_dump()

            for key in raw_manifest:
                if key not in manifest:
                    manifest[key] = raw_manifest[key]

            # Canonicalize inputs: normalize 'input_types' to 'inputs' for backward compatibility
            for tool in manifest.get("tools", []):
                if "inputs" not in tool or not tool["inputs"]:
                    if "input_types" in tool and tool["input_types"]:
                        tool["inputs"] = tool["input_types"]
                    else:
                        tool["inputs"] = []

            logger.debug(
                f"Loaded manifest for plugin '{plugin_id}': "
                f"{len(manifest.get('tools', []))} tools"
            )

            return manifest

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in manifest for '{plugin_id}': {e}")
            raise
        except ValidationError as e:
            logger.error(f"Manifest validation failed for '{plugin_id}': {e}")
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
        """Execute a plugin tool with given arguments using sandbox.

        Finds the plugin, locates the tool function, validates arguments,
        and executes the tool in a crash-proof sandbox. Handles both sync
        and async tool functions with state tracking.

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
        # Get registry for state tracking
        registry = get_registry()

        # 1. Find plugin in registry
        plugin = self.registry.get(plugin_id)

        if not plugin:
            plugins_dict = self.registry.list()
            available = (
                list(plugins_dict.keys())
                if isinstance(plugins_dict, dict)
                else [getattr(p, "name", "unknown") for p in plugins_dict]
            )
            raise ValueError(f"Plugin '{plugin_id}' not found. Available: {available}")

        logger.debug(f"Found plugin: {plugin}")

        # 2. Validate tool exists in plugin.tools (canonical source)
        if not hasattr(plugin, "tools") or tool_name not in plugin.tools:
            available_tools = (
                list(plugin.tools.keys()) if hasattr(plugin, "tools") else []
            )
            raise ValueError(
                f"Tool '{tool_name}' not found in plugin '{plugin_id}'. "
                f"Available: {available_tools}"
            )

        logger.info(
            "Executing plugin tool",
            extra={"plugin_id": plugin_id, "tool_name": tool_name},
        )

        # 3. Get tool function via BasePlugin contract dispatcher
        def tool_func(**kw):  # type: ignore[no-untyped-def]
            return plugin.run_tool(tool_name, kw)

        # 4. Mark plugin as RUNNING
        registry.mark_running(plugin_id)

        # 5. Execute tool in sandbox
        try:
            # Use sandbox for crash-proof execution
            sandbox_result = run_plugin_sandboxed(
                tool_func,
                **args,
            )

            if sandbox_result.ok:
                # Success: record and return result
                registry.record_success(plugin_id, sandbox_result.execution_time_ms)
                result = sandbox_result.result
                result_keys: Any = (
                    list(result.keys()) if isinstance(result, dict) else "unknown"
                )
                logger.debug(f"Tool returned result with keys: {result_keys}")
                return result
            else:
                # Sandbox caught an error: record and raise
                registry.record_error(plugin_id, sandbox_result.execution_time_ms)
                error_type = sandbox_result.error_type or "UnknownError"
                error_msg = sandbox_result.error or "Plugin execution failed"

                if error_type == "TimeoutError":
                    raise TimeoutError(
                        f"Tool '{tool_name}' execution exceeded timeout: {error_msg}"
                    )
                elif error_type == "ValueError":
                    raise ValueError(
                        f"Invalid arguments for tool '{tool_name}': {error_msg}. "
                        f"Check manifest input schema."
                    )
                else:
                    raise Exception(f"Tool execution error ({error_type}): {error_msg}")

        except Exception as e:
            # Catch any unexpected errors from sandbox wrapper itself
            # Note: Don't record error here - it's already recorded in sandbox error handling
            logger.error(
                f"Tool '{tool_name}' execution failed: {e}",
                exc_info=True,
            )
            raise Exception(f"Tool execution error: {str(e)}") from e
