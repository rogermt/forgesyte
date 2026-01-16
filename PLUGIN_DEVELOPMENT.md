# ForgeSyte Plugin Development Guide

ForgeSyte plugins are Python modules that implement a simple, explicit contract. They allow you to extend the vision capabilities of the ForgeSyte core without modifying the server itself.

---

## Plugin Interface Contract

Plugins must implement the `PluginInterface` protocol defined in `server/app/plugin_loader.py`. This is a structural typing contract (not inheritance-based) that requires these attributes and methods:

### Required Attributes

```python
name: str  # Unique plugin identifier (e.g., "ocr", "motion_detector")
```

### Required Methods

```python
def metadata(self) -> Dict[str, Any]:
    """Return plugin metadata.
    
    Returns:
        Dict with keys:
        - name (str): Plugin name
        - description (str): What the plugin does
        - version (str): Plugin version (semver)
        - inputs (List[str]): Input types (e.g., ["image"])
        - outputs (List[str]): Output types (e.g., ["json", "text"])
        - config_schema (Optional[Dict]): JSON Schema for plugin configuration
        - permissions (Optional[List[str]]): Required permissions
    """

def analyze(
    self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Synchronous analysis method.
    
    Args:
        image_bytes: Raw image bytes (PNG, JPEG, GIF, WebP)
        options: Plugin-specific analysis options
    
    Returns:
        Dict containing analysis results
        
    Raises:
        ValueError: If image format is unsupported
    """

def on_load(self) -> None:
    """Lifecycle hook called when plugin is loaded.
    
    Use this to initialize resources, load models, establish connections.
    """

def on_unload(self) -> None:
    """Lifecycle hook called when plugin is unloaded.
    
    Use this to cleanup resources, save state, close connections.
    """
```

### Optional Methods

Plugins can optionally implement async analysis:

```python
async def analyze_async(
    self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Async analysis method (optional).
    
    If your plugin does I/O or network calls, implement this method.
    The base class provides a default that runs analyze() in a thread pool.
    """
```

---

## Plugin Development Checklist

Use this checklist when developing a new plugin:

### 1. Structure & Setup
- [ ] Create directory: `example_plugins/<plugin_name>/`
- [ ] Create `plugin.py` with class named `Plugin`
- [ ] Plugin class has `name` attribute (lowercase, no spaces)
- [ ] Add `__init__.py` (can be empty)
- [ ] Test plugin can be imported without errors

### 2. Implement Interface
- [ ] `metadata()` returns all required fields
- [ ] `analyze()` accepts `image_bytes` and `options` parameters
- [ ] `analyze()` returns a `Dict[str, Any]`
- [ ] `on_load()` initializes resources if needed
- [ ] `on_unload()` cleans up resources
- [ ] Plugin passes `isinstance(instance, PluginInterface)` check

### 3. Image Validation
- [ ] Plugin validates image bytes (use `BasePlugin.validate_image()` or custom)
- [ ] Plugin handles corrupt/invalid image gracefully
- [ ] Plugin rejects tiny images (< 100 bytes)
- [ ] Plugin supports common formats: PNG, JPEG, GIF, WebP

### 4. Error Handling
- [ ] Plugin raises `ValueError` for invalid inputs
- [ ] Plugin logs errors using Python's `logging` module
- [ ] Plugin handles missing dependencies gracefully
- [ ] Plugin handles concurrent calls safely

### 5. Documentation
- [ ] `metadata()` description clearly states what plugin does
- [ ] Input/output types are documented
- [ ] Configuration options (if any) are documented
- [ ] Any model requirements or setup steps documented

### 6. Testing
- [ ] Plugin can be loaded by `PluginManager`
- [ ] `metadata()` returns valid structure
- [ ] `analyze()` handles valid images
- [ ] `analyze()` handles invalid/corrupt images
- [ ] Concurrent calls don't cause issues
- [ ] `on_load()` and `on_unload()` are called correctly

### 7. Performance
- [ ] Plugin loads models in `on_load()`, not per-call
- [ ] `analyze()` completes within acceptable time (< 10s typical)
- [ ] Memory usage is bounded
- [ ] Thread pool is properly sized for concurrent calls

---

## Plugin Structure

```
example_plugins/
├── ocr/
│   ├── __init__.py
│   └── plugin.py          # Must contain class Plugin
├── motion_detector/
│   ├── __init__.py
│   └── plugin.py
└── my_plugin/
    ├── __init__.py
    └── plugin.py
```

Each plugin directory must contain:
- **plugin.py**: Main plugin implementation
- **__init__.py**: (Optional) Package marker

---

## Minimal Plugin Example

```python
from typing import Any, Dict, Optional

class Plugin:
    """Minimal plugin example."""
    
    name = "example"
    version = "0.1.0"
    
    def metadata(self) -> Dict[str, Any]:
        """Return plugin metadata."""
        return {
            "name": self.name,
            "description": "Example plugin that counts pixels",
            "version": self.version,
            "inputs": ["image"],
            "outputs": ["json"]
        }
    
    def analyze(
        self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Count pixels in the image."""
        return {
            "pixel_count": len(image_bytes),
            "format": "bytes"
        }
    
    def on_load(self) -> None:
        """Called when plugin is loaded."""
        print(f"Plugin {self.name} loaded")
    
    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        print(f"Plugin {self.name} unloaded")
```

---

## Using BasePlugin (Recommended)

The `BasePlugin` class provides common functionality:

```python
from app.plugin_loader import BasePlugin
from typing import Any, Dict, Optional

class Plugin(BasePlugin):
    """Plugin using BasePlugin base class."""
    
    name = "my_plugin"
    version = "0.1.0"
    description = "My custom vision plugin"
    
    def metadata(self) -> Dict[str, Any]:
        """Return plugin metadata."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "inputs": ["image"],
            "outputs": ["json"]
        }
    
    def analyze(
        self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze the image."""
        # BasePlugin provides validate_image() helper
        if not self.validate_image(image_bytes):
            raise ValueError("Invalid image format or too small")
        
        # Your analysis logic here
        return {
            "status": "success",
            "result": "analysis_output"
        }
```

BasePlugin provides:
- **ThreadPoolExecutor**: For running sync code asynchronously
- **validate_image()**: Check image format and size
- **on_load/on_unload**: Default implementations with logging
- **analyze_async()**: Automatic thread pool wrapping

---

## Plugin Registry Pattern

The ForgeSyte plugin system uses a **discovery-based registry pattern**. Plugins are discovered automatically from the filesystem, not manually registered.

### How Discovery Works

1. **PluginManager** scans the plugins directory at startup
2. For each subdirectory with a `plugin.py` file:
   - Dynamically imports the module
   - Looks for a `Plugin` class
   - Instantiates it
   - Validates it implements `PluginInterface`
   - Stores in `PluginManager.plugins` dict keyed by `plugin.name`
3. Calls `on_load()` on each loaded plugin

### No Manual Registration Required

Plugins are **automatically registered** by their presence on disk. Just add a new directory with a `plugin.py` file and it will be loaded.

```python
# This is the registry (in PluginManager.plugins)
{
    "ocr": <OCRPlugin instance>,
    "motion_detector": <MotionDetectorPlugin instance>,
    "my_plugin": <MyPlugin instance>
}
```

### Advantages

- **Zero configuration**: Drop plugin in directory, it's loaded
- **Hot reload**: `PluginManager.reload_plugin(name)` restarts a plugin
- **Decoupled**: Core doesn't know about plugins at import time
- **Type safe**: Interface validated at runtime via `isinstance()` check

---

## Testing Your Plugin

### Quick Manual Test

```bash
# Start the server
cd server
uv run fastapi dev app/main.py
```

```bash
# Test with curl
curl -X POST "http://localhost:8000/v1/analyze?plugin=my_plugin" \
     -F "file=@test_image.png"

# Get job status
curl http://localhost:8000/v1/jobs/<job_id>
```

### Programmatic Test

```python
from pathlib import Path
from app.plugin_loader import PluginManager

# Load plugins
pm = PluginManager()
pm.load_plugins()

# Get your plugin
plugin = pm.get("my_plugin")
if plugin:
    # Test metadata
    meta = plugin.metadata()
    print(f"Plugin: {meta['name']} v{meta['version']}")
    
    # Test analysis
    with open("test.png", "rb") as f:
        result = plugin.analyze(f.read())
    print(result)
```

---

## Guidelines

### Code Quality
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write docstrings for public methods
- Keep the `analyze()` method pure (no side effects)

### Resource Management
- Load large models in `on_load()`, not per-call
- Use context managers for file/network resources
- Shutdown thread pools in `on_unload()`
- Avoid storing state in instance variables (make plugins stateless)

### Dependencies
- Keep external dependencies minimal
- Pin versions for reproducibility
- Document any system dependencies (e.g., Tesseract binary)
- Handle missing dependencies gracefully

### Performance
- Optimize for typical image sizes (100KB - 5MB)
- Cache models and resources
- Use thread pools for I/O-heavy operations
- Return results within 10 seconds typical

### Logging
- Use Python's `logging` module, not print()
- Log at INFO level for milestones, DEBUG for details
- Log errors with full context
- Avoid logging sensitive data

---

## Common Patterns

### Pattern: Lazy Model Loading

```python
class Plugin(BasePlugin):
    name = "ml_plugin"
    
    def __init__(self):
        super().__init__()
        self._model = None
    
    def on_load(self):
        super().on_load()
        self._model = load_my_model()  # Load once at startup
    
    def analyze(self, image_bytes, options=None):
        # Model already loaded, reuse it
        return self._model.predict(image_bytes)
    
    def on_unload(self):
        if self._model:
            self._model.cleanup()
        super().on_unload()
```

### Pattern: Configuration Options

```python
class Plugin(BasePlugin):
    name = "configurable_plugin"
    
    def metadata(self):
        return {
            "name": self.name,
            "description": "Plugin with configurable thresholds",
            "inputs": ["image"],
            "outputs": ["json"],
            "config_schema": {
                "type": "object",
                "properties": {
                    "threshold": {"type": "number", "default": 0.5},
                    "max_results": {"type": "integer", "default": 10}
                }
            }
        }
    
    def analyze(self, image_bytes, options=None):
        options = options or {}
        threshold = options.get("threshold", 0.5)
        max_results = options.get("max_results", 10)
        
        # Use options in analysis
        return {"threshold": threshold, "max_results": max_results}
```

### Pattern: Async I/O

```python
import asyncio
from app.plugin_loader import BasePlugin

class Plugin(BasePlugin):
    name = "async_plugin"
    
    async def analyze_async(self, image_bytes, options=None):
        # Can use await here
        result = await self._fetch_remote_analysis(image_bytes)
        return result
    
    async def _fetch_remote_analysis(self, image_bytes):
        # Your async code here
        await asyncio.sleep(1)
        return {"status": "success"}
    
    # BasePlugin provides fallback to sync analyze()
    def analyze(self, image_bytes, options=None):
        raise NotImplementedError("Use analyze_async instead")
```

---

## Troubleshooting

### Plugin Not Loading

**Error**: `No Plugin class found in module`
- **Check**: Does your plugin.py have a `class Plugin` at module level?
- **Check**: Is the file in the correct directory: `example_plugins/<name>/plugin.py`?

**Error**: `Plugin class does not implement PluginInterface`
- **Check**: Does your class have all required methods: `metadata()`, `analyze()`, `on_load()`, `on_unload()`?
- **Check**: Method signatures must match exactly (parameter types and names)

### Plugin Not Found at Runtime

**Error**: `Plugin 'my_plugin' not found`
- **Check**: Is `plugin.name` set correctly?
- **Check**: Did you call `PluginManager.load_plugins()` before accessing plugins?
- **Check**: Is your plugin installed via `pip install`? Plugins are loaded via entry-points only.

### Image Validation Errors

**Error**: `Invalid image format or too small`
- **Check**: Is your test image at least 100 bytes?
- **Check**: Does it start with a valid image header (JPEG, PNG, GIF, WebP)?
- **Use**: `validate_image()` from BasePlugin to validate

---

## API Reference

### PluginInterface (Protocol)

Located in `server/app/plugin_loader.py`

```python
@runtime_checkable
class PluginInterface(Protocol):
    name: str
    def metadata(self) -> Dict[str, Any]: ...
    def analyze(self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]: ...
    def on_load(self) -> None: ...
    def on_unload(self) -> None: ...
```

### BasePlugin (Class)

Located in `server/app/plugin_loader.py`

```python
class BasePlugin(ABC):
    name: str
    version: str
    description: str
    
    def validate_image(self, image_bytes: bytes) -> bool: ...
    async def analyze_async(self, image_bytes: bytes, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]: ...
    def on_load(self) -> None: ...
    def on_unload(self) -> None: ...
```

### PluginManager

Located in `server/app/plugin_loader.py`

```python
class PluginManager:
    def __init__(self) -> None: ...
    def load_plugins(self) -> Dict[str, Dict[str, str]]: ...
    def get(self, name: str) -> Optional[PluginInterface]: ...
    def list(self) -> Dict[str, Dict[str, Any]]: ...
    def reload_plugin(self, name: str) -> bool: ...
    def reload_all(self) -> Dict[str, Dict[str, str]]: ...
```

**Note**: Plugins are discovered via Python entry-points (`forgesyte.plugins` group). Install plugins with `pip install` to make them available.

---

## See Also

- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture and plugin role
- [README.md](./README.md) - Project overview
- [example_plugins/](./example_plugins/) - Example implementations
