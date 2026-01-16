"""Unified plugin discovery and management system.

Supports entry-point plugins (pip installable).
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from importlib.metadata import entry_points
from typing import Any, Dict, Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class PluginInterface(Protocol):
    """Protocol defining the plugin contract.

    All plugins must implement this protocol to be recognized
    by the plugin manager system.
    """

    name: str

    def metadata(self) -> Dict[str, Any]:
        """Return plugin metadata.

        Returns:
            Dictionary containing plugin metadata (name, version, description, etc).
        """
        ...

    def analyze(
        self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze an image and return results.

        Args:
            image_bytes: Raw image bytes to analyze.
            options: Optional plugin-specific analysis options.

        Returns:
            Dictionary containing analysis results and metadata.

        Raises:
            ValueError: If image format is unsupported or analysis fails.
        """
        ...

    def on_load(self) -> None:
        """Called when plugin is loaded.

        Raises:
            Exception: If initialization fails.
        """
        ...

    def on_unload(self) -> None:
        """Called when plugin is unloaded.

        Raises:
            Exception: If cleanup fails.
        """
        ...


class BasePlugin(ABC):
    """Base class for plugins with common functionality.

    Provides default implementations for lifecycle management,
    async analysis support, and image validation.
    """

    name: str = "base"
    version: str = "1.0.0"
    description: str = "Base plugin"

    def __init__(self) -> None:
        """Initialize the plugin with executor for async operations."""
        self._executor = ThreadPoolExecutor(max_workers=2)
        logger.debug(
            "Plugin executor initialized",
            extra={"plugin_name": self.name, "max_workers": 2},
        )

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Return plugin metadata.

        Returns:
            Dictionary with plugin metadata.
        """
        pass

    @abstractmethod
    def analyze(
        self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Synchronous analysis - subclasses must override this.

        Args:
            image_bytes: Raw image bytes to analyze.
            options: Optional plugin-specific analysis options.

        Returns:
            Dictionary containing analysis results.
        """
        pass

    async def analyze_async(
        self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Async wrapper for analysis.

        Runs synchronous analyze() in thread pool executor to avoid blocking.

        Args:
            image_bytes: Raw image bytes to analyze.
            options: Optional plugin-specific analysis options.

        Returns:
            Dictionary containing analysis results.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, self.analyze, image_bytes, options or {}
        )

    def on_load(self) -> None:
        """Called when plugin is loaded.

        Subclasses can override to perform initialization.
        """
        logger.info("Plugin loaded", extra={"plugin_name": self.name})

    def on_unload(self) -> None:
        """Called when plugin is unloaded.

        Cleans up executor and releases resources.
        """
        logger.info("Plugin unloaded", extra={"plugin_name": self.name})
        self._executor.shutdown(wait=False)

    def validate_image(self, image_bytes: bytes) -> bool:
        """Validate image data format.

        Checks for common image file headers (JPEG, PNG, GIF, WebP).

        Args:
            image_bytes: Raw image data to validate.

        Returns:
            True if image format is recognized, False otherwise.
        """
        if not image_bytes or len(image_bytes) < 100:
            return False
        headers: Dict[bytes, str] = {
            b"\xff\xd8\xff": "jpeg",
            b"\x89PNG": "png",
            b"GIF8": "gif",
            b"RIFF": "webp",
        }
        for header in headers:
            if image_bytes[: len(header)] == header:
                return True
        return False


class PluginManager:
    """Manages plugin discovery, loading, and lifecycle.

    Loads plugins via entry-points (pip installable packages).
    """

    def __init__(self) -> None:
        """Initialize the plugin manager."""
        self.plugins: Dict[str, PluginInterface] = {}
        logger.debug("PluginManager initialized")

    def load_entrypoint_plugins(self):
        """Load plugins from entry points.

        Returns:
            Tuple of (loaded plugins dict, errors dict)
        """
        loaded = {}
        errors = {}

        eps = entry_points(group="forgesyte.plugins")

        for ep in eps:
            try:
                plugin_class = ep.load()
                plugin = plugin_class()

                if not isinstance(plugin, PluginInterface):
                    raise TypeError(
                        f"Plugin {ep.name} does not implement PluginInterface"
                    )

                plugin.on_load()
                self.plugins[plugin.name] = plugin
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

    def load_plugins(
        self,
    ) -> Dict[str, Dict[str, str]]:
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

    def get(self, name: str) -> Optional[PluginInterface]:
        """Get a plugin by name.

        Args:
            name: The name of the plugin to retrieve.

        Returns:
            PluginInterface instance if found, None otherwise.
        """
        return self.plugins.get(name)

    def __contains__(self, name: str) -> bool:
        """Check if a plugin is loaded.

        Args:
            name: The name of the plugin to check.

        Returns:
            True if plugin is loaded, False otherwise.
        """
        return name in self.plugins

    def list(self) -> Dict[str, Dict[str, Any]]:
        """List all plugins with their metadata.

        Returns:
            Dictionary mapping plugin names to their metadata dictionaries.

        Note:
            Handles both dict metadata (legacy) and Pydantic model metadata.
        """
        result = {}
        for name, plugin in self.plugins.items():
            metadata = plugin.metadata()
            if hasattr(metadata, "model_dump"):
                metadata = metadata.model_dump()
            result[name] = metadata
        return result

    def reload_plugin(self, name: str) -> bool:
        """Reload a specific plugin.

        Unloads the existing plugin and removes it from the registry.
        Re-discovery of entry-point plugins requires reload_all().

        Args:
            name: The name of the plugin to reload.

        Returns:
            True if plugin was unloaded, False if plugin not found.

        Raises:
            None - catches and logs all exceptions.
        """
        if name in self.plugins:
            plugin = self.plugins[name]
            try:
                plugin.on_unload()
            except Exception as e:
                logger.warning(
                    "Error during plugin unload",
                    extra={"plugin_name": name, "error": str(e)},
                )
            del self.plugins[name]
            logger.info(
                "Plugin unloaded (use reload_all to rediscover entry-points)",
                extra={"plugin_name": name},
            )
            return True
        return False

    def reload_all(self) -> Dict[str, Dict[str, str]]:
        """Reload all plugins.

        Unloads all currently loaded plugins, clears the registry,
        then reloads all plugins from entry points.

        Returns:
            Dictionary with 'loaded' (successful) and 'errors' (failed) keys.

        Raises:
            None - catches and logs all exceptions during unload.
        """
        for plugin in self.plugins.values():
            try:
                plugin.on_unload()
            except Exception as e:
                logger.warning(
                    "Error unloading plugin",
                    extra={"plugin_name": plugin.name, "error": str(e)},
                )

        self.plugins.clear()
        logger.info("All plugins cleared, reloading from entry points")
        return self.load_plugins()

    def uninstall_plugin(self, name: str) -> bool:
        """Uninstall a plugin.

        Calls on_unload() lifecycle method and removes from registry.

        Args:
            name: Name of the plugin to uninstall.

        Returns:
            True if plugin was loaded and uninstalled, False otherwise.

        Raises:
            None - catches exceptions during unload.
        """
        if name in self.plugins:
            try:
                self.plugins[name].on_unload()
            except Exception as e:
                logger.warning(
                    "Error unloading plugin",
                    extra={"plugin_name": name, "error": str(e)},
                )
            del self.plugins[name]
            logger.info(
                "Plugin uninstalled",
                extra={"plugin_name": name},
            )
            return True
        return False
