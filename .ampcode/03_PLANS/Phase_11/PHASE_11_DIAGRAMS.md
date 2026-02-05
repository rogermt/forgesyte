# Phase 11 Diagrams (Helper Document)

This file helps visualize Phase 11. NOT for approval - just for builder reference.

---

## 1. Plugin Lifecycle State Machine

```
                    ┌─────────────────┐
                    │   UNAVAILABLE   │
                    │  (missing deps) │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     LOADED        │ ◄── plugin.register()
                    │  (initial state)  │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                               │
     ┌────────▼────────┐            ┌────────▼────────┐
     │   INITIALIZED   │            │     FAILED      │
     │  (__init__ ok) │            │  (runtime error)│
     └────────┬────────┘            └─────────────────┘
              │
     ┌────────▼────────┐
     │     RUNNING     │
     │ (tool execution)│
     └────────┬────────┘
              │
     ┌────────▼────────┐
     │   COMPLETED    │ or FAILED
     │   (success)    │
     └─────────────────┘

KEY: All transitions FINAL except INITIALIZED→RUNNING
     FAILED and UNAVAILABLE are terminal states
```

---

## 2. Plugin Loading Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    plugin_loader.load()                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Load manifest.json                                      │
│     - name, version, dependencies, requires_gpu, models    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. DependencyChecker.validate_plugin(manifest)               │
│     - GPU: torch.cuda.is_available() + nvidia-smi         │
│     - Packages: importlib.util.find_spec()                │
│     - Models: read first 16 bytes                          │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
      ┌───────▼───────┐               ┌───────▼───────┐
      │   AVAILABLE   │               │ UNAVAILABLE   │
      │ (all checks   │               │ (missing deps)│
      │  pass)        │               └───────────────┘
      └───────┬───────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Import module (plugin.py)                                │
│     - importlib.util.spec_from_file_location()              │
│     - spec.loader.exec_module()                             │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
      ┌───────▼───────┐               ┌───────▼───────┐
      │   SUCCESS     │               │    FAILED     │
      │ (no ImportErr)│               │ (ImportError) │
      └───────┬───────┘               └───────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Instantiate plugin = module.Plugin()                      │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
      ┌───────▼───────┐               ┌───────▼───────┐
      │   SUCCESS     │               │    FAILED     │
      └───────┬───────┘               └───────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  5. registry.register(name, instance)                        │
│     - state = LOADED                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  6. plugin.validate()                                       │
│     - REQUIRED validation step                              │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
      ┌───────▼───────┐               ┌───────▼───────┐
      │   VALID       │               │    INVALID    │
      │               │               │ (mark FAILED) │
      └───────┬───────┘               └───────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  7. registry.mark_initialized(name)                         │
│     - state = INITIALIZED                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Sandbox Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    ToolRunner.run()                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  1. registry.is_available(plugin_id)?                       │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
      ┌───────▼───────┐               ┌───────▼───────┐
      │    YES        │               │     NO        │
      │ (LOADED/INIT) │               │ (FAILED/UNAV) │
      └───────┬───────┘               └───────┬───────┘
              │                               │
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────────┐
│ 2. registry.mark_       │     │ Return structured error:   │
│    RUNNING(plugin_id)    │     │ {ok: false, error: "...", │
└───────────┬─────────────┘     │        error_type: "..."}   │
            │                   └─────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│  3. run_plugin_sandboxed(plugin.run, **args)                │
│     - try: result = plugin.run(**args)                     │
│     - except Exception as e:                               │
│         result = PluginSandboxResult(                       │
│             ok=False,                                       │
│             error=str(e),                                   │
│             error_type=e.__class__.__name__,                 │
│             traceback=traceback.format_exc()                │
│         )                                                   │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
      ┌───────▼───────┐               ┌───────▼───────┐
      │      OK       │               │    ERROR       │
      │ (result=...)  │               │ (exception)   │
      └───────┬───────┘               └───────┬───────┘
              │                               │
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────────┐
│ 4. registry.            │     │ 4. registry.               │
│    record_success()     │     │    mark_failed(plugin_id,  │
│    return {ok:true,     │     │    result.error)          │
│    result: result}      │     │    record_error()         │
└─────────────────────────┘     │    return {ok:false,        │
                              │    error: "...",             │
                              │    error_type: "..."}        │
                              └─────────────────────────────┘
```

---

## 4. Health API Response Structure

```
PluginHealthResponse {
  name: string           // "ocr", "yolo-tracker", etc.
  state: enum           // LOADED | INITIALIZED | RUNNING | FAILED | UNAVAILABLE
  reason: string|null   // Error message if FAILED/UNAVAILABLE
  version: string|null  // From manifest.json
  uptime_seconds:       // Seconds since loaded
    float|null
  last_used: datetime|null  // Last tool execution timestamp
  success_count: int    // Number of successful executions
  error_count: int      // Number of failed executions
}

PluginListResponse {
  plugins: PluginHealthResponse[]
  total: int            // All plugins
  available: int        // LOADED/INITIALIZED/RUNNING
  failed: int          // FAILED
  unavailable: int      // UNAVAILABLE
}
```

---

## 5. RWLock Usage Pattern

```python
from threading import RWLock

class PluginRegistry:
    def __init__(self):
        self._lock = RWLock()
        self._plugins: dict[str, PluginMetadata] = {}
    
    # READ operations - use reader lock
    def get_status(self, name: str) -> PluginHealthResponse | None:
        with self._lock.reader_lock():
            if name not in self._plugins:
                return None
            return self._plugins[name].to_health_response()
    
    def list_all(self) -> list[PluginHealthResponse]:
        with self._lock.reader_lock():
            return [p.to_health_response() for p in self._plugins.values()]
    
    def is_available(self, name: str) -> bool:
        with self._lock.reader_lock():
            if name not in self._plugins:
                return False
            state = self._plugins[name].state
            return state in {State.LOADED, State.INITIALIZED, State.RUNNING}
    
    # WRITE operations - use writer lock
    def register(self, name: str, ...):
        with self._lock.writer_lock():
            self._plugins[name] = PluginMetadata(...)
    
    def mark_failed(self, name: str, reason: str):
        with self._lock.writer_lock():
            if name in self._plugins:
                self._plugins[name].state = State.FAILED
                self._plugins[name].reason = reason
                self._plugins[name].error_count += 1
    
    def mark_running(self, name: str):
        with self._lock.writer_lock():
            if name in self._plugins:
                self._plugins[name].state = State.RUNNING
                self._plugins[name].last_used = datetime.utcnow()
```

---

## 6. File Structure Tree

```
server/app/plugins/
├── loader/
│   ├── __init__.py
│   ├── plugin_loader.py         # Main loader with validate()
│   ├── plugin_registry.py       # RWLock-based, thread-safe
│   ├── dependency_checker.py     # GPU (torch+nvidia-smi)
│   │                              # Models (read bytes)
│   └── plugin_errors.py          # PluginError, PluginLoadError...
├── sandbox/
│   ├── __init__.py
│   ├── sandbox_runner.py        # run_plugin_sandboxed()
│   ├── timeout.py               # 60s default
│   └── memory_guard.py           # 1GB default
├── lifecycle/
│   ├── __init__.py
│   ├── lifecycle_state.py        # Enum: LOADED, INITIALIZED...
│   └── lifecycle_manager.py      # State transitions
└── health/
    ├── __init__.py
    ├── health_model.py          # PluginHealthResponse
    └── health_router.py          # /v1/plugins, /v1/plugins/{name}/health

tests/
├── test_plugin_loader/
│   ├── test_import_failures.py
│   ├── test_init_failures.py
│   ├── test_dependency_checker.py
│   └── test_registry_state.py
├── test_plugin_sandbox/
│   ├── test_sandbox_runner.py
│   ├── test_timeout.py
│   └── test_memory_guard.py
├── test_plugin_health_api/
│   ├── test_list_plugins.py
│   └── test_plugin_health.py
├── test_tool_runner/
│   └── test_sandbox_integration.py
└── test_videotracker_stability/
    └── test_*.py
```

---

## 7. Commit Timeline

```
Week 1-2:
  ┌─────────────────────────────────────────┐
  │ Commit 1: Scaffold modules (stubs)        │
  │ Commit 2: Wire Health API                │
  │ Commit 3: PluginRegistry (RWLock)        │
  └─────────────────────────────────────────┘

Week 2-3:
  ┌─────────────────────────────────────────┐
  │ Commit 4: PluginSandboxRunner            │
  │ Commit 5: Wire ToolRunner to sandbox     │
  │ Commit 6: Add metrics (counts, uptime)   │
  └─────────────────────────────────────────┘

Week 3-4:
  ┌─────────────────────────────────────────┐
  │ Commit 7: Timeout/Memory guards          │
  │ Commit 8: Final tests, governance        │
  └─────────────────────────────────────────┘
```

---

## 8. Error Message Template

```
GPU Missing:
"CUDA GPU not available. Check torch.cuda.is_available() or nvidia-smi."

Package Missing:
"ImportError: No module named 'torch'. Install with: pip install torch"

Model Missing:
"Model file not found: models/player-detection.pt. Download from ForgeSyte releases."

Model Corrupted:
"Model file truncated or corrupted: models/player-detection.pt. Re-download."

Timeout:
"Plugin execution timed out after 60s. Increase timeout in manifest if needed."

Memory:
"Plugin exceeded 1GB memory limit. Reduce model size or increase limit."
```

---

## Summary

This diagram file helps visualize:
1. Lifecycle states and transitions
2. Plugin loading flow with checks
3. Sandbox execution pattern
4. Health API structure
5. RWLock usage
6. File structure
7. Commit timeline
8. Error messages

Reference this while building PLANS.md and PROGRESS.md.
