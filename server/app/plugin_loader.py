"""Unified plugin discovery and management system.

Supports:
- Entry-point plugins (pip installable)
- Local development plugins (file-based)
"""

import asyncio
import importlib.util
import logging
import sys
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from importlib.metadata import entry_points
from pathlib import Path
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
        # Check for common image headers
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

    Supports both entry-point plugins (pip installable) and local development plugins.
    """

    def __init__(self, plugins_dir: Optional[str] = None) -> None:
        """Initialize the plugin manager.

        Args:
            plugins_dir: Optional path to local plugins directory for development.
                        If None, only entry-point plugins will be loaded.

        Raises:
            None - gracefully handles missing directories.
        """
        self.plugins_dir = Path(plugins_dir) if plugins_dir else None
        self.plugins: Dict[str, PluginInterface] = {}
        self._watchers: list[Any] = []
        logger.debug(
            "PluginManager initialized",
            extra={"plugins_dir": str(self.plugins_dir)},
        )

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

    def load_local_plugins(self):
        """Load local development plugins from directory.

        Searches for plugin.py in both direct subdirectories and nested
        package directories (e.g., ocr/plugin.py or ocr/forgesyte_ocr/plugin.py).

        Returns:
            Tuple of (loaded plugins dict, errors dict)
        """
        loaded = {}
        errors = {}

        # If no plugins_dir is set, return empty results
        if self.plugins_dir is None:
            logger.info("No plugins directory specified, skipping local plugin loading")
            return loaded, errors

        if not self.plugins_dir.exists():
            logger.info(
                f"Plugins dir {self.plugins_dir} doesn't exist, "
                "skipping local plugin loading"
            )
            return loaded, errors

        for item in self.plugins_dir.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                # First, check for plugin.py directly in subdirectory
                plugin_file = item / "plugin.py"

                # If not found, search recursively for plugin.py in nested dirs
                if not plugin_file.exists():
                    plugin_files = list(item.glob("**/plugin.py"))
                    if plugin_files:
                        # Use first plugin.py found (typically in package dir)
                        plugin_file = plugin_files[0]
                    else:
                        # No plugin.py found
                        continue

                try:
                    plugin = self._load_plugin_from_file(plugin_file, item.name)
                    if plugin:
                        plugin.on_load()
                        self.plugins[plugin.name] = plugin
                        loaded[plugin.name] = str(plugin_file)
                        logger.info(
                            "Local plugin loaded successfully",
                            extra={
                                "plugin_name": plugin.name,
                                "plugin_file": str(plugin_file),
                            },
                        )
                except (ImportError, TypeError, AttributeError) as e:
                    errors[item.name] = str(e)
                    logger.error(
                        "Failed to load local plugin",
                        extra={"plugin_dir": item.name, "error": str(e)},
                    )

        return loaded, errors

    def load_plugins(
        self,
    ) -> Dict[str, Dict[str, str]]:
        """Load all plugins from both entry points and local directory.

        Returns:
            Dictionary with 'loaded' (successful) and 'errors' (failed) keys.
            Each contains plugin names mapped to file paths or error messages.

        Raises:
            None - catches and logs all exceptions to allow partial loading.
        """
        loaded: Dict[str, str] = {}
        errors: Dict[str, str] = {}

        # Load entry-point plugins first
        ep_loaded, ep_errors = self.load_entrypoint_plugins()
        loaded.update(ep_loaded)
        errors.update(ep_errors)

        # Load local development plugins
        local_loaded, local_errors = self.load_local_plugins()
        loaded.update(local_loaded)
        errors.update(local_errors)

        return {"loaded": loaded, "errors": errors}

    def _load_plugin_from_file(
        self, plugin_file: Path, module_name: str
    ) -> Optional[PluginInterface]:
        """Load a single plugin from a file.

        Dynamically imports a plugin module and instantiates its Plugin class,
        verifying it implements the PluginInterface protocol.

        Args:
            plugin_file: Path to plugin.py file to load.
            module_name: Name for the dynamically loaded module (used in sys.modules).

        Returns:
            Plugin instance if successful, None if file doesn't exist or module
            spec cannot be created.

        Raises:
            ImportError: If module spec cannot be loaded or file is missing.
            TypeError: If Plugin class doesn't implement PluginInterface protocol.
            AttributeError: If no Plugin class found in module.
        """
        spec = importlib.util.spec_from_file_location(
            f"vision_plugins.{module_name}", plugin_file
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module spec for {plugin_file}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        # Look for Plugin class
        if hasattr(module, "Plugin"):
            plugin_class = module.Plugin
            instance = plugin_class()

            if isinstance(instance, PluginInterface):
                logger.debug(
                    "Plugin loaded from file",
                    extra={"module_name": module_name, "plugin_file": str(plugin_file)},
                )
                return instance
            else:
                raise TypeError(
                    f"Plugin class from {module_name} does not implement "
                    f"PluginInterface"
                )

        raise AttributeError(f"No Plugin class found in module {module_name}")

    def get(self, name: str) -> Optional[PluginInterface]:
        """Get a plugin by name.

        Args:
            name: The name of the plugin to retrieve.

        Returns:
            PluginInterface instance if found, None otherwise.
        """
        return self.plugins.get(name)

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
            # Convert Pydantic models to dict if necessary
            if hasattr(metadata, "model_dump"):
                metadata = metadata.model_dump()
            result[name] = metadata
        return result

    def reload_plugin(self, name: str) -> bool:
        """Reload a specific plugin.

        Unloads the existing plugin, removes it from the registry, then
        attempts to reload it from disk.

        Args:
            name: The name of the plugin to reload.

        Returns:
            True if reload successful, False if plugin not found or reload failed.

        Raises:
            None - catches and logs all exceptions.
        """
        if name in self.plugins:
            plugin = self.plugins[name]
            if plugin:  # Extra check to satisfy mypy
                try:
                    plugin.on_unload()
                except Exception as e:
                    logger.warning(
                        "Error during plugin unload",
                        extra={"plugin_name": name, "error": str(e)},
                    )
            del self.plugins[name]

        # Only attempt to reload from disk if plugins_dir is set and exists
        if self.plugins_dir is not None and self.plugins_dir.exists():
            # Find and reload
            plugin_dir = self.plugins_dir / name
            plugin_file = plugin_dir / "plugin.py"

            # If not found directly, search recursively
            if not plugin_file.exists():
                plugin_files = list(plugin_dir.glob("**/plugin.py"))
                if plugin_files:
                    plugin_file = plugin_files[0]

            if plugin_file.exists():
                try:
                    loaded_plugin = self._load_plugin_from_file(plugin_file, name)
                    if loaded_plugin:
                        self.plugins[loaded_plugin.name] = loaded_plugin
                        loaded_plugin.on_load()
                        logger.info(
                            "Plugin reloaded successfully",
                            extra={"plugin_name": name},
                        )
                        return True
                except (ImportError, TypeError, AttributeError) as e:
                    logger.error(
                        "Failed to reload plugin",
                        extra={"plugin_name": name, "error": str(e)},
                    )

        return False

    def reload_all(self) -> Dict[str, Dict[str, str]]:
        """Reload all plugins.

        Unloads all currently loaded plugins, clears the registry,
        then reloads all plugins from disk if plugins_dir is available.

        Returns:
            Dictionary with 'loaded' (successful) and 'errors' (failed) keys.

        Raises:
            None - catches and logs all exceptions during unload.
        """
        # Unload existing
        for plugin in self.plugins.values():
            try:
                plugin.on_unload()
            except Exception as e:
                logger.warning(
                    "Error unloading plugin",
                    extra={"plugin_name": plugin.name, "error": str(e)},
                )

        self.plugins.clear()

        # Only reload from disk if plugins_dir is set and exists
        if self.plugins_dir is not None and self.plugins_dir.exists():
            logger.info("All plugins cleared, reloading from disk")
            return self.load_plugins()
        else:
            logger.info("All plugins cleared, no plugin directory to reload from")
            return {"loaded": {}, "errors": {}}

    def install_plugin(self, source: str) -> bool:
        """Install a plugin from a URL or path.

        Args:
            source: URL or file path to plugin source.

        Returns:
            True if installation successful, False otherwise.

        Raises:
            NotImplementedError: Feature not yet implemented.
        """
        raise NotImplementedError("Plugin installation not supported in this version")

    def uninstall_plugin(self, name: str) -> bool:
        """Uninstall a plugin.

        Calls on_unload() lifecycle method, removes from registry, but does not
        delete plugin files from disk.

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
