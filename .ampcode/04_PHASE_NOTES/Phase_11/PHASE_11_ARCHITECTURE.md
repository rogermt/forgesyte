# Phase 11 Architecture – Plugin Stability & Health

**Vision:** No plugin failure crashes the server. All failures are observable and recoverable.

---

## System Design

### Data Flow

```
[Client / Web-UI]
      |
      v
[FastAPI Router]
      |
      +---> [/v1/jobs/{id}/run]
      |          |
      |          v
      |     [ToolRunner]
      |          |
      |          v
      |     [PluginSandboxRunner]
      |          |
      |          v
      |     [Plugin.tool() call]
      |          |
      |          +---> {ok: True, result: ...}
      |          |
      |          +---> {ok: False, error: ..., error_type: ...}
      |
      +---> [/v1/plugins]
      |          |
      |          v
      |     [PluginHealthRouter]
      |          |
      |          v
      |     [PluginRegistry.all_states()]
      |          |
      |          v
      |     [LifecycleManager.get_states()]
      |
      +---> [/v1/plugins/{name}/health]
              |
              v
         [PluginHealthRouter]
              |
              v
         [PluginRegistry.get_status(name)]
```

---

## Core Components

### 1. **PluginRegistry**

**Responsibility:** Discover, load, and track all plugins.

**Interface:**

```python
class PluginRegistry:
    def load_plugin(self, name: str) -> bool:
        """Load plugin by name; update state to LOADED/FAILED/UNAVAILABLE."""
        ...

    def get_plugin(self, name: str) -> PluginModule | None:
        """Get loaded plugin instance or None if not available."""
        ...

    def available_plugins(self) -> list[str]:
        """List all LOADED/INITIALIZED plugins (excludes FAILED/UNAVAILABLE)."""
        ...

    def all_plugins(self) -> list[str]:
        """List all plugins regardless of state."""
        ...

    def get_state(self, name: str) -> PluginLifecycleState | None:
        """Query plugin state."""
        ...

    def get_plugin_status(self, name: str) -> PluginStatus | None:
        """Get detailed status including state, reason, metadata."""
        ...
```

**When loaded (app startup):**

```python
registry = PluginRegistry()

for plugin_path in discover_plugins():
    registry.load_plugin(plugin_path)
    # If import fails → state = FAILED, reason = traceback
    # If init fails → state = FAILED, reason = traceback
    # If missing deps → state = UNAVAILABLE, reason = "missing X"
    # If OK → state = LOADED
```

---

### 2. **PluginLifecycleManager**

**Responsibility:** Track state transitions for each plugin.

**States:**

```
LOADED
  ↓ (plugin.initialize() called)
INITIALIZED
  ↓ (first tool execution)
RUNNING
  ↓ (on error during execution)
FAILED
```

Or:

```
UNAVAILABLE ← (missing deps, GPU required but not present)
```

**Never transitions back up** – once FAILED or UNAVAILABLE, stays there (until restart).

**Code:**

```python
class LifecycleManager:
    def __init__(self):
        self._states: dict[str, PluginLifecycleState] = {}

    def set_state(self, name: str, state: PluginLifecycleState) -> None:
        self._states[name] = state

    def get_state(self, name: str) -> PluginLifecycleState | None:
        return self._states.get(name)

    def all_states(self) -> dict[str, PluginLifecycleState]:
        return dict(self._states)


# Singleton instance
lifecycle = LifecycleManager()
```

---

### 3. **DependencyChecker**

**Responsibility:** Pre-flight validation of plugin dependencies.

**Checks:**

- Python package imports (`torch`, `opencv`, etc.)
- System packages (`ffmpeg`, etc.)
- GPU availability (if required)
- Model files (if specified in manifest)

**Code:**

```python
class DependencyChecker:
    def check_dependencies(
        self,
        packages: list[str],
        requires_gpu: bool = False,
        requires_models: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Check if all dependencies are available.

        Returns:
            {
                "available": bool,
                "reason": str | None,  # Error message if not available
                "missing": list[str],
            }
        """
        ...

    def validate_plugin(self, manifest: dict) -> dict[str, Any]:
        """Check all deps declared in plugin manifest."""
        ...
```

**Usage (in PluginLoader):**

```python
check = DependencyChecker()
result = check.validate_plugin(plugin_manifest)

if not result["available"]:
    lifecycle.set_state(plugin_name, PluginLifecycleState.UNAVAILABLE)
    registry._mark_unavailable(plugin_name, result["reason"])
else:
    # Safe to import
```

---

### 4. **PluginLoader v2**

**Responsibility:** Safe import + instantiation with full error handling.

**Code structure:**

```python
class PluginLoader:
    def __init__(self, registry: PluginRegistry, lifecycle: LifecycleManager):
        self.registry = registry
        self.lifecycle = lifecycle

    def load(self, plugin_name: str, plugin_path: str) -> bool:
        """
        Load a plugin safely.

        Returns:
            True if LOADED/INITIALIZED
            False if FAILED/UNAVAILABLE
        """
        try:
            # 1. Validate dependencies
            check = DependencyChecker()
            result = check.validate_plugin(load_manifest(plugin_path))
            if not result["available"]:
                self.lifecycle.set_state(plugin_name, PluginLifecycleState.UNAVAILABLE)
                return False

            # 2. Import module
            module = self._safe_import(plugin_path)
            if module is None:
                self.lifecycle.set_state(plugin_name, PluginLifecycleState.FAILED)
                return False

            # 3. Instantiate
            instance = self._safe_instantiate(module)
            if instance is None:
                self.lifecycle.set_state(plugin_name, PluginLifecycleState.FAILED)
                return False

            # 4. Register
            self.registry.register(plugin_name, instance)
            self.lifecycle.set_state(plugin_name, PluginLifecycleState.LOADED)
            return True

        except Exception as exc:  # noqa: BLE001
            self.lifecycle.set_state(plugin_name, PluginLifecycleState.FAILED)
            return False

    def _safe_import(self, plugin_path: str) -> types.ModuleType | None:
        """Import module; return None on error."""
        try:
            return importlib.import_module(plugin_path)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Import failed for {plugin_path}: {exc}")
            return None

    def _safe_instantiate(self, module: types.ModuleType) -> Any | None:
        """Call module's factory function; return None on error."""
        try:
            return module.create_plugin()
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Instantiation failed: {exc}")
            return None
```

---

### 5. **PluginSandboxRunner**

**Responsibility:** Wrap every plugin function call in a safe try/except.

**Code:**

```python
class PluginSandboxResult:
    def __init__(self, ok: bool, result: Any = None, error: str = None, error_type: str = None):
        self.ok = ok
        self.result = result
        self.error = error
        self.error_type = error_type


def run_plugin_sandboxed(fn: Callable, *args, **kwargs) -> PluginSandboxResult:
    """Run plugin function safely; never raise."""
    try:
        result = fn(*args, **kwargs)
        return PluginSandboxResult(ok=True, result=result)
    except Exception as exc:  # noqa: BLE001
        return PluginSandboxResult(
            ok=False,
            error=str(exc),
            error_type=exc.__class__.__name__,
        )
```

**Integration with ToolRunner:**

```python
@tool_runner.route("/v1/plugins/{plugin_id}/tools/{tool_name}/run", method="POST")
def run_tool(plugin_id: str, tool_name: str, payload: dict):
    plugin = registry.get_plugin(plugin_id)
    if plugin is None:
        return {"ok": False, "error": "Plugin not found"}

    # Get tool function
    tool_fn = getattr(plugin, tool_name, None)
    if tool_fn is None:
        return {"ok": False, "error": "Tool not found"}

    # RUN IN SANDBOX
    result = run_plugin_sandboxed(tool_fn, **payload)

    if result.ok:
        return {"ok": True, "result": result.result}
    else:
        # Update plugin state to FAILED
        lifecycle.set_state(plugin_id, PluginLifecycleState.FAILED)
        return {
            "ok": False,
            "error": result.error,
            "error_type": result.error_type,
        }
```

---

### 6. **PluginHealthRouter**

**Responsibility:** Expose plugin state via HTTP API.

**Endpoints:**

```
GET /v1/plugins
    → Returns list of all plugins with their state

GET /v1/plugins/{name}
    → Returns detailed health for a specific plugin

GET /v1/plugins/{name}/health
    → Same as above (alias)
```

**Response model:**

```python
class PluginHealthResponse(BaseModel):
    name: str
    state: PluginLifecycleState  # "LOADED", "FAILED", etc.
    reason: str | None  # Error message if FAILED
    version: str | None
    uptime: float | None
    last_used: datetime | None
    error_count: int = 0
    success_count: int = 0


class PluginListResponse(BaseModel):
    plugins: list[PluginHealthResponse]
    total: int
    available: int
```

**Router code:**

```python
from fastapi import APIRouter, HTTPException
from app.plugins.health.health_model import PluginHealthResponse, PluginListResponse

router = APIRouter(prefix="/v1/plugins", tags=["plugins"])


@router.get("/", response_model=PluginListResponse)
def list_plugins(registry: PluginRegistry, lifecycle: LifecycleManager):
    """List all plugins and their health status."""
    plugins = []
    for name in registry.all_plugins():
        state = lifecycle.get_state(name)
        plugins.append(PluginHealthResponse(name=name, state=state))

    return PluginListResponse(
        plugins=plugins,
        total=len(plugins),
        available=len([p for p in plugins if p.state in ["LOADED", "INITIALIZED", "RUNNING"]]),
    )


@router.get("/{name}/health", response_model=PluginHealthResponse)
def get_plugin_health(name: str, registry: PluginRegistry, lifecycle: LifecycleManager):
    """Get health status of a single plugin."""
    state = lifecycle.get_state(name)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")

    status = registry.get_plugin_status(name)
    return PluginHealthResponse(
        name=name,
        state=state,
        reason=status.reason if status else None,
    )
```

---

## Initialization Sequence

### On App Startup

```python
# 1. Create managers
lifecycle = LifecycleManager()
registry = PluginRegistry(lifecycle)
loader = PluginLoader(registry, lifecycle)

# 2. Discover plugins
plugin_paths = discover_plugins_from_manifests()

# 3. Load each plugin (safe)
for plugin_path in plugin_paths:
    loader.load(plugin_path.name, str(plugin_path))
    # Failures are silent; state is tracked

# 4. Log results
available = [p for p in registry.all_plugins() if lifecycle.get_state(p) == "LOADED"]
failed = [p for p in registry.all_plugins() if lifecycle.get_state(p) == "FAILED"]
unavailable = [p for p in registry.all_plugins() if lifecycle.get_state(p) == "UNAVAILABLE"]

logger.info(f"✓ Loaded {len(available)} plugins")
logger.warning(f"✗ Failed to load {len(failed)} plugins")
logger.warning(f"✗ Unavailable (missing deps) {len(unavailable)} plugins")

# 5. Mount health API
app.include_router(health_router)
```

---

## Error Handling Philosophy

### Rule 1: Never Crash the Server

- **Catch everything** – Even `KeyboardInterrupt` is caught and logged (then re-raised)
- **Return structured error** – Never expose stack traces to clients
- **Update state** – Plugin marked FAILED so admins know

### Rule 2: Make Failures Observable

- **State is queryable** – `/v1/plugins` shows all states
- **Error reason is included** – "Missing CUDA" vs "ImportError: no module named X"
- **Logs are detailed** – Full traceback in server logs, structured error in API response

### Rule 3: No Silent Failures

- **Every plugin has a state** – LOADED/FAILED/UNAVAILABLE/etc.
- **Health API is always reachable** – Even if plugin failed
- **Metrics tracked** – success/error counts per plugin

---

## Testing Strategy

### RED Tests (Phase 11a)

- `test_plugin_import_failure_does_not_crash_server`
- `test_plugin_init_failure_marked_failed`
- `test_missing_dependency_marks_plugin_unavailable`
- `test_list_plugins_returns_health`
- `test_failed_plugin_health_is_reported`
- `test_sandbox_runner_never_raises`

### GREEN Tests (Phase 11b)

- Implementation passes all RED tests

### REFACTOR Tests (Phase 11c)

- Edge cases: timeout, memory limits, concurrent plugin loading
- Performance: bulk plugin operations
- Recovery: plugin restart/reload

---

## Success Criteria

✅ **No plugin crash ever crashes server**  
✅ **Every plugin has queryable state**  
✅ **Failed plugins are visible in `/v1/plugins`**  
✅ **Health API never returns 500**  
✅ **Error reasons are useful (not generic)**  
✅ **All RED tests pass**

---

## Deployment Checklist

- [ ] All RED tests pass
- [ ] Integration with ToolRunner complete
- [ ] Health API wired in main app
- [ ] Logging covers all error paths
- [ ] Performance tested (100+ plugins)
- [ ] PR reviewed and merged
