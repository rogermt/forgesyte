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

import logging
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
