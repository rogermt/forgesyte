"""Plugin discovery and management system."""

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
    """Protocol defining the plugin contract."""

    name: str

    def metadata(self) -> Dict[str, Any]:
        """Return plugin metadata."""
        ...

    def analyze(
        self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze an image and return results."""
        ...

    def on_load(self) -> None:
        """Called when plugin is loaded."""
        ...

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        ...


class BasePlugin(ABC):
    """Base class for plugins with common functionality."""

    name: str = "base"
    version: str = "1.0.0"
    description: str = "Base plugin"

    def __init__(self) -> None:
        """Initialize the plugin with executor for async operations."""
        self._executor = ThreadPoolExecutor(max_workers=2)

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Return plugin metadata."""
        pass

    @abstractmethod
    def analyze(
        self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Synchronous analysis - override this."""
        pass

    async def analyze_async(
        self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Async wrapper for analysis."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, self.analyze, image_bytes, options or {}
        )

    def on_load(self) -> None:
        """Called when plugin is loaded."""
        logger.info(f"Plugin {self.name} loaded")

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        logger.info(f"Plugin {self.name} unloaded")
        self._executor.shutdown(wait=False)

    def validate_image(self, image_bytes: bytes) -> bool:
        """Basic image validation."""
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
    """Manages plugin discovery, loading, and lifecycle."""

    def __init__(self, plugins_dir: Optional[str] = None) -> None:
        """Initialize the plugin manager.

        Args:
            plugins_dir: Optional path to plugins directory.
                        Defaults to example_plugins.
        """
        if plugins_dir is None:
            # Default to example_plugins directory outside of server
            self.plugins_dir = Path(__file__).parent.parent.parent / "example_plugins"
        else:
            self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, PluginInterface] = {}
        self._watchers: list[Any] = []

    def load_plugins(
        self,
    ) -> Dict[str, Dict[str, str]]:
        """Load all plugins from the plugins directory."""
        loaded: Dict[str, str] = {}
        errors: Dict[str, str] = {}

        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
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
                            logger.info(f"Loaded plugin: {plugin.name}")
                    except Exception as e:
                        errors[item.name] = str(e)
                        logger.error(f"Failed to load plugin {item.name}: {e}")

        return {"loaded": loaded, "errors": errors}

    def _load_plugin_from_file(
        self, plugin_file: Path, module_name: str
    ) -> Optional[PluginInterface]:
        """Load a single plugin from a file.

        Args:
            plugin_file: Path to plugin.py file
            module_name: Name for the dynamically loaded module

        Returns:
            Plugin instance if successful, None otherwise

        Raises:
            ImportError: If module spec cannot be loaded
            TypeError: If plugin class doesn't implement PluginInterface
            AttributeError: If no Plugin class found in module
        """
        spec = importlib.util.spec_from_file_location(
            f"vision_plugins.{module_name}", plugin_file
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {plugin_file}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        # Look for Plugin class
        if hasattr(module, "Plugin"):
            plugin_class = module.Plugin
            instance = plugin_class()

            if isinstance(instance, PluginInterface):
                return instance
            else:
                raise TypeError("Plugin class does not implement PluginInterface")

        raise AttributeError("No Plugin class found in module")

    def get(self, name: str) -> Optional[PluginInterface]:
        """Get a plugin by name."""
        return self.plugins.get(name)

    def list(self) -> Dict[str, Dict[str, Any]]:
        """List all plugins with their metadata."""
        return {name: plugin.metadata() for name, plugin in self.plugins.items()}

    def reload_plugin(self, name: str) -> bool:
        """Reload a specific plugin."""
        if name in self.plugins:
            plugin = self.plugins[name]
            if plugin:  # Extra check to satisfy mypy
                plugin.on_unload()
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
                    return True
            except Exception as e:
                logger.error(f"Failed to reload plugin {name}: {e}")

        return False

    def reload_all(self) -> Dict[str, Dict[str, str]]:
        """Reload all plugins."""
        # Unload existing
        for plugin in self.plugins.values():
            try:
                plugin.on_unload()
            except Exception as e:
                logger.error(f"Error unloading {plugin.name}: {e}")

        self.plugins.clear()
        return self.load_plugins()

    def install_plugin(self, source: str) -> bool:
        """Install a plugin from a URL or path."""
        # TODO: Implement plugin installation from git URL or local path
        raise NotImplementedError("Plugin installation not yet implemented")

    def uninstall_plugin(self, name: str) -> bool:
        """Uninstall a plugin."""
        if name in self.plugins:
            self.plugins[name].on_unload()
            del self.plugins[name]
            # TODO: Remove plugin files
            return True
        return False
