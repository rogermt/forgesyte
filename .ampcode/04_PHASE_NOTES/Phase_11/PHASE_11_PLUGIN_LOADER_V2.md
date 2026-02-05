# Phase 11 Plugin Loader v2 – Full Implementation

**Production-ready PluginLoader v2 with error isolation and dependency checking.**

Implement these files in order. All code is tested against PHASE_11_GREEN_TESTS.md.

---

## 1. Plugin Errors

**File:** `server/app/plugins/loader/plugin_errors.py`

```python
"""Plugin loading error types."""


class PluginError(Exception):
    """Base exception for plugin-related errors."""
    pass


class PluginLoadError(PluginError):
    """Error during plugin loading."""
    pass


class PluginImportError(PluginLoadError):
    """Error importing plugin module."""
    pass


class PluginInitError(PluginLoadError):
    """Error initializing plugin."""
    pass


class PluginDependencyError(PluginLoadError):
    """Error validating plugin dependencies."""
    pass
```

---

## 2. Dependency Checker

**File:** `server/app/plugins/loader/dependency_checker.py`

```python
"""Check plugin dependencies before loading."""

import importlib.util
import logging
from typing import Any

logger = logging.getLogger(__name__)


class DependencyChecker:
    """Validate plugin dependencies."""
    
    def __init__(self):
        self._cuda_available = self._check_cuda()
    
    def _check_cuda(self) -> bool:
        """Check if CUDA (GPU) is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def check_dependencies(
        self,
        packages: list[str] | None = None,
        requires_gpu: bool = False,
        requires_models: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Check if all plugin dependencies are available.
        
        Args:
            packages: List of Python packages to check
            requires_gpu: Whether plugin requires CUDA GPU
            requires_models: Dict of model name → path to check
        
        Returns:
            {
                "available": bool,
                "reason": str | None,  # Error message if not available
                "missing": list[str],  # Missing packages/deps
            }
        """
        missing = []
        
        # Check Python packages
        if packages:
            for package in packages:
                if not self._check_package(package):
                    missing.append(package)
        
        # Check GPU requirement
        if requires_gpu and not self._cuda_available:
            return {
                "available": False,
                "reason": "Plugin requires GPU/CUDA but CUDA not available (check torch.cuda.is_available())",
                "missing": ["cuda"],
            }
        
        # Check model files
        if requires_models:
            missing_models = self._check_models(requires_models)
            missing.extend(missing_models)
        
        if missing:
            return {
                "available": False,
                "reason": f"Missing dependencies: {', '.join(missing)}",
                "missing": missing,
            }
        
        return {
            "available": True,
            "reason": None,
            "missing": [],
        }
    
    def _check_package(self, package_name: str) -> bool:
        """Check if a Python package is installed."""
        # Handle submodules (e.g., "torch.cuda")
        root_package = package_name.split(".")[0]
        spec = importlib.util.find_spec(root_package)
        return spec is not None
    
    def _check_models(self, models: dict[str, str]) -> list[str]:
        """Check if model files exist."""
        import os
        
        missing = []
        for name, path in models.items():
            if not os.path.exists(path):
                missing.append(f"{name} (path: {path})")
        
        return missing
    
    def validate_plugin_manifest(self, manifest: dict) -> dict[str, Any]:
        """
        Validate plugin using its manifest.json.
        
        Expected manifest keys:
            - dependencies: list of Python packages
            - requires_gpu: bool
            - models: dict of {name: path}
        """
        packages = manifest.get("dependencies", [])
        requires_gpu = manifest.get("requires_gpu", False)
        models = manifest.get("models", {})
        
        return self.check_dependencies(
            packages=packages,
            requires_gpu=requires_gpu,
            requires_models=models,
        )
```

---

## 3. Plugin Loader v2 – Core Implementation

**File:** `server/app/plugins/loader/plugin_loader.py`

```python
"""Plugin Loader v2 with error isolation and lifecycle tracking."""

import importlib
import json
import logging
import types
from pathlib import Path
from typing import Any, Optional

from .dependency_checker import DependencyChecker
from .plugin_errors import PluginLoadError, PluginImportError, PluginInitError
from .plugin_registry import PluginRegistry
from ..lifecycle.lifecycle_state import PluginLifecycleState

logger = logging.getLogger(__name__)


class PluginLoader:
    """
    Safe plugin loader with full error isolation.
    
    Guarantees:
    - Loading a broken plugin never crashes the server
    - All errors are captured and logged
    - Plugin state is tracked throughout lifecycle
    """
    
    def __init__(self, registry: PluginRegistry):
        self.registry = registry
        self.dependency_checker = DependencyChecker()
    
    def load_from_path(self, plugin_path: Path) -> bool:
        """
        Load a plugin from a filesystem path.
        
        Expects path structure:
            /path/to/plugin/
            ├── manifest.json
            ├── plugin.py
            └── ...
        
        Returns:
            True if successfully loaded
            False if loading failed (state tracked in registry)
        """
        try:
            # Load manifest
            manifest_path = plugin_path / "manifest.json"
            if not manifest_path.exists():
                logger.error(f"Plugin manifest not found: {manifest_path}")
                return False
            
            with open(manifest_path) as f:
                manifest = json.load(f)
            
            plugin_name = manifest.get("name", plugin_path.name)
            description = manifest.get("description", "")
            version = manifest.get("version", "unknown")
            
            # Register in registry (initial state)
            self.registry.register(
                name=plugin_name,
                description=description,
            )
            
            # Step 1: Check dependencies
            if not self._check_dependencies(plugin_name, manifest):
                return False
            
            # Step 2: Import module
            module = self._safe_import(plugin_name, plugin_path)
            if module is None:
                return False
            
            # Step 3: Instantiate plugin
            plugin_instance = self._safe_instantiate(plugin_name, module)
            if plugin_instance is None:
                return False
            
            # Step 4: Register as initialized
            self.registry.mark_initialized(plugin_name)
            logger.info(f"✓ Loaded plugin: {plugin_name} ({version})")
            return True
        
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Unexpected error loading plugin: {exc}", exc_info=True)
            return False
    
    def _check_dependencies(self, name: str, manifest: dict) -> bool:
        """
        Check plugin dependencies.
        
        Returns:
            True if all dependencies available
            False if any missing (plugin marked UNAVAILABLE)
        """
        result = self.dependency_checker.validate_plugin_manifest(manifest)
        
        if not result["available"]:
            self.registry.mark_unavailable(name, result["reason"])
            logger.warning(
                f"⊘ Plugin UNAVAILABLE: {name}\n  Reason: {result['reason']}"
            )
            return False
        
        return True
    
    def _safe_import(self, name: str, plugin_path: Path) -> Optional[types.ModuleType]:
        """
        Safely import a plugin module.
        
        Returns:
            Module if successful
            None if import failed (plugin marked FAILED)
        """
        try:
            # Import the plugin.py module
            plugin_file = plugin_path / "plugin.py"
            if not plugin_file.exists():
                raise ImportError(f"plugin.py not found in {plugin_path}")
            
            # Use importlib to load the module
            spec = importlib.util.spec_from_file_location(
                f"plugin_{name}",
                plugin_file,
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not create module spec for {plugin_file}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            logger.debug(f"✓ Imported plugin module: {name}")
            return module
        
        except Exception as exc:  # noqa: BLE001
            reason = f"ImportError: {exc.__class__.__name__}: {exc}"
            self.registry.mark_failed(name, reason)
            logger.error(f"✗ Plugin FAILED: {name}\n  {reason}")
            return None
    
    def _safe_instantiate(self, name: str, module: types.ModuleType) -> Optional[Any]:
        """
        Safely instantiate a plugin.
        
        Expects module to have:
            class Plugin:
                def __init__(self):
                    ...
        
        Returns:
            Plugin instance if successful
            None if instantiation failed (plugin marked FAILED)
        """
        try:
            # Get the Plugin class
            Plugin = getattr(module, "Plugin", None)
            if Plugin is None:
                raise AttributeError(f"No 'Plugin' class found in module")
            
            # Instantiate
            instance = Plugin()
            
            logger.debug(f"✓ Instantiated plugin: {name}")
            return instance
        
        except Exception as exc:  # noqa: BLE001
            reason = f"InitError: {exc.__class__.__name__}: {exc}"
            self.registry.mark_failed(name, reason)
            logger.error(f"✗ Plugin FAILED: {name}\n  {reason}")
            return None
    
    def load_all_from_directory(self, plugins_dir: Path) -> int:
        """
        Load all plugins from a directory.
        
        Args:
            plugins_dir: Directory containing plugin subdirectories
        
        Returns:
            Number of successfully loaded plugins
        """
        loaded = 0
        
        if not plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {plugins_dir}")
            return 0
        
        # Each subdirectory is a plugin
        for plugin_path in sorted(plugins_dir.iterdir()):
            if not plugin_path.is_dir():
                continue
            
            if (plugin_path / "manifest.json").exists():
                if self.load_from_path(plugin_path):
                    loaded += 1
        
        logger.info(f"Loaded {loaded} plugins from {plugins_dir}")
        return loaded
```

---

## 4. Integration: App Startup

**File:** `server/app/main.py` (patch)

**Add to `create_app()` function:**

```python
def create_app() -> FastAPI:
    """Create FastAPI application with Phase 11 plugin loading."""
    app = FastAPI(title="ForgeSyte")
    
    # ... existing setup ...
    
    # Phase 11: Load plugins
    from app.plugins.loader.plugin_loader import PluginLoader
    from app.plugins.loader.plugin_registry import get_registry
    from pathlib import Path
    
    registry = get_registry()
    loader = PluginLoader(registry)
    
    # Load plugins from standard location
    plugins_dir = Path(__file__).parent.parent.parent / "plugins"
    
    try:
        loaded = loader.load_all_from_directory(plugins_dir)
        logger.info(f"✓ Phase 11: Plugin loader initialized ({loaded} plugins loaded)")
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Plugin loading error: {exc}", exc_info=True)
        # Don't crash server; continue with reduced plugin set
    
    # Mount health API
    from app.plugins.health.health_router import router as health_router
    app.include_router(health_router, tags=["plugins"])
    
    return app
```

---

## 5. Logging Configuration

**File:** `server/app/plugins/loader/__init__.py`

```python
"""Plugin loader module."""

import logging

logger = logging.getLogger("app.plugins.loader")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

__all__ = [
    "PluginLoader",
    "PluginRegistry",
    "DependencyChecker",
]
```

---

## 6. Testing Plugin Loader

**Run these tests to verify implementation:**

```bash
cd server

# All plugin loader tests
pytest tests/test_plugin_loader/ -v

# All dependency checker tests
pytest tests/test_plugin_loader/test_dependency_checker.py -v

# All health API tests
pytest tests/test_plugin_health_api/ -v

# Full integration
pytest tests/test_plugin_loader/ tests/test_plugin_health_api/ -v --tb=short
```

---

## 7. Verification Checklist

After implementing PluginLoader v2:

✅ **Import failures are caught**
```python
# Broken plugin doesn't crash server
registry.get_status("broken_plugin").state == "FAILED"
```

✅ **Init failures are caught**
```python
# Plugin that raises in __init__ is marked FAILED
registry.get_status("bad_init").state == "FAILED"
```

✅ **Missing deps are marked UNAVAILABLE**
```python
# GPU plugin without GPU is marked UNAVAILABLE
registry.get_status("gpu_plugin").state == "UNAVAILABLE"
```

✅ **Health API works**
```bash
curl http://localhost:8000/v1/plugins
curl http://localhost:8000/v1/plugins/ocr/health
```

✅ **All GREEN tests pass**
```bash
pytest tests/test_plugin_loader/ -v
pytest tests/test_plugin_health_api/ -v
```

---

## Troubleshooting

### Issue: Plugin not loading

Check:
1. Manifest exists at `plugin/manifest.json`
2. `plugin.py` exists and has `class Plugin`
3. Dependencies are installable

### Issue: "Plugin marked FAILED" but reason unclear

Check logs:
```bash
grep "Plugin FAILED" server.log
```

Reason should include:
- ImportError if import failed
- InitError if __init__ failed
- Missing package name if dependency missing

### Issue: Health API not returning failed plugin

Check registry is being used:
```python
from app.plugins.loader.plugin_registry import get_registry
registry = get_registry()
print(registry.list_all())
```

---

This is Phase 11 PluginLoader v2: **deterministic, safe, observable.**

Implement and test carefully. All GREEN tests should pass.
