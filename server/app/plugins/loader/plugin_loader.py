"""Plugin loader implementation for Phase 11.

Handles plugin discovery and loading with error isolation.
"""

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any, Optional

from .dependency_checker import DependencyChecker
from .plugin_errors import (
    PluginImportError,
    PluginInitError,
    PluginLoadError,
    PluginValidationError,
)
from .plugin_registry import get_registry

logger = logging.getLogger(__name__)


class PluginLoader:
    """
    Loads plugins with comprehensive error handling.

    Implements Phase 11 contract:
    - Check dependencies before loading
    - Isolate import errors
    - Isolate init errors
    - Run validation hook if plugin provides it
    - Never crash the server
    """

    def __init__(self) -> None:
        """Initialize plugin loader."""
        self.registry = get_registry()
        self.dependency_checker = DependencyChecker()

    def load_plugin(
        self,
        plugin_name: str,
        plugin_path: str,
        description: str = "",
        version: str = "",
    ) -> bool:
        """
        Load a plugin from disk.

        Process:
        1. Register plugin as LOADED
        2. Check dependencies
        3. Import module
        4. Instantiate plugin
        5. Run validate() hook
        6. Mark INITIALIZED if successful

        Args:
            plugin_name: Name of the plugin
            plugin_path: Path to plugin.py file
            description: Plugin description (from manifest)
            version: Plugin version (from manifest)

        Returns:
            True if plugin loaded successfully, False otherwise
        """
        try:
            # Step 1: Register as LOADED
            self.registry.register(plugin_name, description, version)
            logger.info(f"Registering plugin: {plugin_name}")

            # Step 2: Check dependencies (GPU, packages, models)
            # For now, skip dependency checking in loader
            # It will be done in DependencyChecker during manifest validation

            # Step 3: Import module
            plugin_module = self._import_plugin_module(plugin_path)

            # Step 4: Instantiate plugin
            plugin_instance = self._instantiate_plugin(plugin_module)

            # Step 5: Run validate() hook
            self._validate_plugin(plugin_instance)

            # Step 6: Store instance and mark INITIALIZED
            self.registry.set_plugin_instance(plugin_name, plugin_instance)
            self.registry.mark_initialized(plugin_name)
            logger.info(f"✓ Plugin loaded and validated: {plugin_name}")

            return True

        except PluginLoadError as e:
            logger.error(f"✗ Plugin load failed: {plugin_name}: {e}")
            self.registry.mark_failed(plugin_name, str(e))
            return False

        except Exception as e:
            error_msg = f"Unexpected error loading plugin: {str(e)}"
            logger.exception(error_msg)
            self.registry.mark_failed(plugin_name, error_msg)
            return False

    def _import_plugin_module(self, plugin_path: str) -> Any:
        """
        Import a plugin module from a file path.

        Args:
            plugin_path: Path to plugin.py

        Returns:
            The imported module

        Raises:
            PluginImportError: If import fails
        """
        try:
            path_obj = Path(plugin_path)

            if not path_obj.exists():
                raise PluginImportError(f"Plugin file not found: {plugin_path}")

            # Import module from file path
            spec = importlib.util.spec_from_file_location("plugin_module", plugin_path)
            if spec is None or spec.loader is None:
                raise PluginImportError(f"Cannot create import spec for: {plugin_path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules["plugin_module"] = module
            spec.loader.exec_module(module)

            return module

        except PluginImportError:
            raise
        except ImportError as e:
            raise PluginImportError(f"Import error: {str(e)}") from e
        except Exception as e:
            raise PluginImportError(f"Module loading failed: {str(e)}") from e

    def _instantiate_plugin(self, plugin_module: Any) -> Any:
        """
        Instantiate the Plugin class from a module.

        Args:
            plugin_module: The imported plugin module

        Returns:
            An instance of the Plugin class

        Raises:
            PluginInitError: If instantiation fails
        """
        try:
            if not hasattr(plugin_module, "Plugin"):
                raise PluginInitError("Plugin module does not define 'Plugin' class")

            plugin_class = plugin_module.Plugin
            plugin_instance = plugin_class()

            return plugin_instance

        except PluginInitError:
            raise
        except Exception as e:
            raise PluginInitError(f"Plugin instantiation failed: {str(e)}") from e

    def _validate_plugin(self, plugin_instance: Any) -> None:
        """
        Call plugin's validate() hook if it exists.

        This is required to detect plugins that init successfully
        but are actually broken (e.g., missing GPU at runtime).

        Args:
            plugin_instance: The plugin instance

        Raises:
            PluginValidationError: If validation fails
        """
        if not hasattr(plugin_instance, "validate"):
            # validate() is optional; if not provided, skip
            logger.debug("Plugin does not implement validate() hook")
            return

        try:
            validate_fn = plugin_instance.validate
            validate_fn()
            logger.debug("✓ Plugin validation passed")

        except Exception as e:
            raise PluginValidationError(f"Plugin validation failed: {str(e)}") from e


# Singleton instance
_loader: Optional[PluginLoader] = None


def get_plugin_loader() -> PluginLoader:
    """Get or create the global plugin loader."""
    global _loader
    if _loader is None:
        _loader = PluginLoader()
    return _loader
