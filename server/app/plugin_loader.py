"""Unified plugin discovery and management system.

Loads plugins exclusively via Python entry points (pip installable).
"""

import json
import logging
from importlib.metadata import entry_points
from typing import Any, Dict, Optional

from app.plugins.base import BasePlugin
from app.plugins.schemas import ToolSchema

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Manages plugin discovery, loading, and lifecycle.

    Loads plugins exclusively via entry-points (pip installable packages).
    Enforces single contract: all plugins must be BasePlugin subclasses.
    """

    def __init__(self) -> None:
        """Initialize the plugin registry."""
        self._plugins: Dict[str, BasePlugin] = {}
        logger.debug("PluginRegistry initialized")

    def load_entrypoint_plugins(self) -> tuple[Dict[str, str], Dict[str, str]]:
        """Load plugins from entry points.

        Enforces:
        - Plugin is BasePlugin subclass
        - Plugin name is unique (no duplicates)
        - All exceptions caught and logged

        Returns:
            Tuple of (loaded plugins dict, errors dict)
        """
        loaded: Dict[str, str] = {}
        errors: Dict[str, str] = {}
        seen_names: Dict[str, str] = {}  # Track plugin names for duplicates

        eps = entry_points(group="forgesyte.plugins")

        for ep in eps:
            try:
                plugin_class = ep.load()
                plugin = plugin_class()

                # Enforce BasePlugin contract
                if not isinstance(plugin, BasePlugin):
                    raise TypeError(
                        f"Plugin {ep.name} must subclass BasePlugin, got {type(plugin)}"
                    )

                # Enforce unique plugin names
                if plugin.name in seen_names:
                    error_msg = (
                        f"Duplicate plugin name '{plugin.name}' "
                        f"(entrypoints: {seen_names[plugin.name]}, {ep.name})"
                    )
                    errors[ep.name] = error_msg
                    logger.error(
                        "Duplicate plugin name detected",
                        extra={
                            "plugin_name": plugin.name,
                            "entrypoint": ep.name,
                            "first_entrypoint": seen_names[plugin.name],
                        },
                    )
                    continue

                # Call optional validation hook
                if hasattr(plugin, "validate") and callable(plugin.validate):
                    plugin.validate()

                # Register plugin (enforces contract and checks for duplicates)
                self.register(plugin)

                seen_names[plugin.name] = ep.name
                loaded[plugin.name] = f"entrypoint:{ep.name}"
                logger.info(
                    "Entrypoint plugin loaded successfully",
                    extra={
                        "plugin_name": plugin.name,
                        "source": f"entrypoint:{ep.name}",
                    },
                )

            except Exception as e:
                errors[ep.name] = str(e)
                logger.error(
                    "Failed to load entrypoint plugin",
                    extra={"plugin_name": ep.name, "error": str(e)},
                )

        return loaded, errors

    def load_plugins(self) -> Dict[str, Dict[str, str]]:
        """Load all plugins from entry points.

        Returns:
            Dictionary with 'loaded' (successful) and 'errors' (failed) keys.
            Each contains plugin names mapped to sources or error messages.

        Raises:
            None - catches and logs all exceptions to allow partial loading.
        """
        loaded: Dict[str, str] = {}
        errors: Dict[str, str] = {}

        ep_loaded, ep_errors = self.load_entrypoint_plugins()
        loaded.update(ep_loaded)
        errors.update(ep_errors)

        return {"loaded": loaded, "errors": errors}

    def get(self, name: str) -> Optional[BasePlugin]:
        """Get a plugin by name.

        Args:
            name: The name of the plugin to retrieve.

        Returns:
            BasePlugin instance if found, None otherwise.
        """
        return self._plugins.get(name)

    def list(self) -> Dict[str, BasePlugin]:
        """List all loaded plugins.

        Returns:
            Dictionary mapping plugin names to BasePlugin instances.
        """
        return dict(self._plugins)

    def register(self, plugin: BasePlugin) -> None:
        """Register a plugin after enforcing the BasePlugin contract.

        Validates plugin structure, enforces type identity, and validates tool schemas.

        Args:
            plugin: BasePlugin instance to register.

        Raises:
            TypeError: If plugin doesn't subclass BasePlugin.
            ValueError: If plugin structure invalid, duplicate name, or schemas
                malformed.
        """
        # Must subclass BasePlugin
        if not isinstance(plugin, BasePlugin):
            raise TypeError(
                f"Plugin '{plugin.__class__.__name__}' must subclass BasePlugin"
            )

        # Validate name
        if not isinstance(plugin.name, str) or not plugin.name.strip():
            raise ValueError(
                f"Plugin '{plugin.__class__.__name__}' must define "
                "a non-empty string 'name'"
            )

        # Validate tools dict
        if not isinstance(plugin.tools, dict):
            raise ValueError(f"Plugin '{plugin.name}' must define 'tools' as a dict")

        # Validate tool metadata and schemas
        for tool_name, tool_meta in plugin.tools.items():
            # BasePlugin already validated structure, but validate schemas here
            if not isinstance(tool_meta, dict):
                raise ValueError(
                    f"Tool '{tool_name}' in plugin '{plugin.name}' must be a dict"
                )

            # Pydantic schema validation
            try:
                ToolSchema(**tool_meta)
            except Exception as e:
                raise ValueError(
                    f"Invalid schema for tool '{tool_name}' in plugin "
                    f"'{plugin.name}': {e}"
                ) from e

            # Ensure schemas are JSON-serializable (exclude handler)
            try:
                schema_meta = {k: v for k, v in tool_meta.items() if k != "handler"}
                json.dumps(schema_meta)
            except Exception as e:
                raise ValueError(
                    f"Schema for tool '{tool_name}' in plugin '{plugin.name}' "
                    f"is not JSON-serializable: {e}"
                ) from e

        # Validate run_tool exists
        if not hasattr(plugin, "run_tool") or not callable(plugin.run_tool):
            raise ValueError(
                f"Plugin '{plugin.name}' must implement run_tool(tool_name, args)"
            )

        # Enforce unique names
        if plugin.name in self._plugins:
            raise ValueError(f"Duplicate plugin name: '{plugin.name}'")

        # Register
        self._plugins[plugin.name] = plugin
        logger.info(
            "Plugin registered successfully",
            extra={"plugin_name": plugin.name},
        )

    def reload_plugin(self, name: str) -> bool:
        """Reload a specific plugin to refresh code and state.

        Args:
            name: Plugin identifier

        Returns:
            True if reload succeeded, False if reload failed or plugin not found

        Raises:
            RuntimeError: If reload encounters unexpected errors
        """
        plugin = self._plugins.get(name)
        if not plugin:
            logger.warning("Plugin not found for reload", extra={"plugin_name": name})
            return False

        try:
            # Call optional reload hook if available
            if hasattr(plugin, "on_reload") and callable(plugin.on_reload):
                plugin.on_reload()
            logger.info("Plugin reloaded successfully", extra={"plugin_name": name})
            return True
        except Exception as e:
            logger.error(
                "Failed to reload plugin",
                extra={"plugin_name": name, "error": str(e)},
            )
            raise RuntimeError(f"Failed to reload plugin '{name}': {e}") from e

    def reload_all(self) -> Dict[str, Any]:
        """Reload all plugins to refresh code and state.

        Returns:
            Dictionary with reload operation results:
                - success: Boolean indicating overall success
                - reloaded: List of successfully reloaded plugin names
                - failed: List of plugins that failed to reload
                - total: Total number of plugins
                - errors: Optional dict mapping failed plugin names to error messages
        """
        reloaded: list = []
        failed: list = []
        errors: Dict[str, str] = {}

        for plugin_name in list(self._plugins.keys()):
            try:
                if self.reload_plugin(plugin_name):
                    reloaded.append(plugin_name)
                else:
                    failed.append(plugin_name)
            except Exception as e:
                failed.append(plugin_name)
                errors[plugin_name] = str(e)

        success = len(failed) == 0
        logger.info(
            "Plugin reload complete",
            extra={
                "success": success,
                "reloaded": len(reloaded),
                "failed": len(failed),
                "total": len(self._plugins),
            },
        )

        return {
            "success": success,
            "reloaded": reloaded,
            "failed": failed,
            "total": len(self._plugins),
            "errors": errors if errors else None,
        }
