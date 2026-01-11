"""Plugin discovery and management system.

This module provides plugin discovery, loading, and lifecycle management.
Plugins are dynamically loaded from a configured directory and must
implement the PluginInterface protocol.
"""

import asyncio
import importlib.util
import logging
import sys
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
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

    Dynamically loads plugin modules from a directory, validates them
    against PluginInterface protocol, and manages their lifecycle.
    """

    def __init__(self, plugins_dir: Optional[str] = None) -> None:
        """Initialize the plugin manager.

        Args:
            plugins_dir: Optional path to plugins directory.
                        Defaults to example_plugins relative to server directory.

        Raises:
            None - gracefully handles missing directories.
        """
        if plugins_dir is None:
            # Default to example_plugins directory outside of server
            self.plugins_dir = Path(__file__).parent.parent.parent / "example_plugins"
        else:
            self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, PluginInterface] = {}
        self._watchers: list[Any] = []
        logger.debug(
            "PluginManager initialized",
            extra={"plugins_dir": str(self.plugins_dir)},
        )

    def load_plugins(
        self,
    ) -> Dict[str, Dict[str, str]]:
        """Load all plugins from the plugins directory.

        Scans plugins_dir for subdirectories containing plugin.py files,
        loads each plugin, and validates it against PluginInterface protocol.

        Returns:
            Dictionary with 'loaded' (successful) and 'errors' (failed) keys.
            Each contains plugin names mapped to file paths or error messages.

        Raises:
            None - catches and logs all exceptions to allow partial loading.
        """
        loaded: Dict[str, str] = {}
        errors: Dict[str, str] = {}

        if not self.plugins_dir.exists():
            logger.warning(
                "Plugins directory not found",
                extra={"plugins_dir": str(self.plugins_dir)},
            )
            return {"loaded": loaded, "errors": errors}

        for item in self.plugins_dir.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                plugin_file = item / "plugin.py"
                if plugin_file.exists():
                    try:
                        plugin = self._load_plugin_from_file(plugin_file, item.name)
                        if plugin:
                            self.plugins[plugin.name] = plugin
                            plugin.on_load()
                            loaded[plugin.name] = str(plugin_file)
                            logger.info(
                                "Plugin loaded successfully",
                                extra={
                                    "plugin_name": plugin.name,
                                    "plugin_file": str(plugin_file),
                                },
                            )
                    except (ImportError, TypeError, AttributeError) as e:
                        errors[item.name] = str(e)
                        logger.error(
                            "Failed to load plugin",
                            extra={"plugin_dir": item.name, "error": str(e)},
                        )

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
        """
        return {name: plugin.metadata() for name, plugin in self.plugins.items()}

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

        # Find and reload
        plugin_dir = self.plugins_dir / name
        plugin_file = plugin_dir / "plugin.py"

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
        then reloads all plugins from disk.

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
        logger.info("All plugins cleared, reloading from disk")
        return self.load_plugins()

    def install_plugin(self, source: str) -> bool:
        """Install a plugin from a URL or path.

        Args:
            source: URL or file path to plugin source.

        Returns:
            True if installation successful, False otherwise.

        Raises:
            NotImplementedError: Feature not yet implemented.
        """
        # TODO: Implement plugin installation from git URL or local path
        raise NotImplementedError("Plugin installation not yet implemented")

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
            # TODO: Remove plugin files
            return True
        return False
