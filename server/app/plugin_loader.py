"""Unified plugin discovery and management system.

Loads plugins exclusively via Python entry points (pip installable).
"""

import logging
from importlib.metadata import entry_points
from typing import Dict, Optional

from app.plugins.base import BasePlugin

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

                seen_names[plugin.name] = ep.name
                self._plugins[plugin.name] = plugin
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


# Backward compatibility alias
PluginManager = PluginRegistry
