# Phase 11 Kickoff – Plugin Stability & Health

**Goal:** Make the plugin system **crash-proof** and **observable**. No plugin failure crashes the server.

**Key Deliverables:**
- ✅ Plugin loader v2 with error isolation
- ✅ Sandbox runner for safe execution
- ✅ Lifecycle state tracking
- ✅ Health API endpoints
- ✅ RED test suite (defines behavior first)

---

## First 5 Commits

### Commit 1 – Scaffold plugin stability modules

**Message:** `chore(plugins): scaffold loader, sandbox, lifecycle, health`

**Create files (all start as stubs with `pass`):**

```
server/app/plugins/loader/__init__.py
server/app/plugins/loader/plugin_loader.py
server/app/plugins/loader/plugin_registry.py
server/app/plugins/loader/dependency_checker.py
server/app/plugins/loader/plugin_errors.py

server/app/plugins/sandbox/__init__.py
server/app/plugins/sandbox/sandbox_runner.py
server/app/plugins/sandbox/timeout.py
server/app/plugins/sandbox/memory_guard.py

server/app/plugins/lifecycle/__init__.py
server/app/plugins/lifecycle/lifecycle_state.py
server/app/plugins/lifecycle/lifecycle_manager.py

server/app/plugins/health/__init__.py
server/app/plugins/health/health_router.py
server/app/plugins/health/health_model.py

server/app/api/plugins_api.py
```

**Why:** Scaffolding first allows RED tests to be written against real imports.

---

### Commit 2 – Wire plugin health API into FastAPI

**Message:** `feat(api): mount plugin health endpoints`

**In your main API/app setup:**

```python
from app.plugins.health.health_router import router as plugin_health_router

api.include_router(plugin_health_router, prefix="/v1/plugins", tags=["plugins"])
```

**File:** `server/app/plugins/health/health_router.py`

```python
from fastapi import APIRouter
from .health_model import PluginHealthResponse

router = APIRouter()

@router.get("/", response_model=list[PluginHealthResponse])
def list_plugins():
    """List all plugins and their health status."""
    raise NotImplementedError

@router.get("/{name}/health", response_model=PluginHealthResponse)
def get_plugin_health(name: str):
    """Get health status of a single plugin."""
    raise NotImplementedError
```

**Why:** Wiring first makes RED tests meaningful; tests will fail on NotImplementedError.

---

### Commit 3 – Introduce plugin lifecycle model

**Message:** `feat(plugins): add lifecycle state and manager`

**File:** `server/app/plugins/lifecycle/lifecycle_state.py`

```python
from enum import Enum

class PluginLifecycleState(str, Enum):
    LOADED = "LOADED"
    INITIALIZED = "INITIALIZED"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"
```

**File:** `server/app/plugins/lifecycle/lifecycle_manager.py`

```python
from .lifecycle_state import PluginLifecycleState

class PluginLifecycleManager:
    """Thread-safe tracker of plugin lifecycle states."""

    def __init__(self):
        self._states: dict[str, PluginLifecycleState] = {}

    def set_state(self, name: str, state: PluginLifecycleState) -> None:
        """Set plugin state."""
        self._states[name] = state

    def get_state(self, name: str) -> PluginLifecycleState | None:
        """Get plugin state or None if not tracked."""
        return self._states.get(name)

    def all_states(self) -> dict[str, PluginLifecycleState]:
        """Return all plugin states as a dict."""
        return dict(self._states)
```

**Why:** Contract first; behavior added incrementally.

---

### Commit 4 – Implement sandbox wrapper (no integration yet)

**Message:** `feat(plugins): add sandbox runner wrapper`

**File:** `server/app/plugins/sandbox/sandbox_runner.py`

```python
from typing import Any, Callable

class PluginSandboxResult:
    """Result of running a plugin function in sandbox."""
    def __init__(self, ok: bool, result: Any = None, error: str = None, error_type: str = None):
        self.ok = ok
        self.result = result
        self.error = error
        self.error_type = error_type

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "result": self.result,
            "error": self.error,
            "error_type": self.error_type,
        }


def run_plugin_sandboxed(
    fn: Callable[..., Any],
    *args: Any,
    **kwargs: Any
) -> PluginSandboxResult:
    """Run a plugin function with exception isolation."""
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

**Why:** Sandbox ready but not yet wired to ToolRunner. RED tests expect isolation.

---

### Commit 5 – Add RED test suites for plugin loader v2

**Message:** `test(plugins): add RED tests for loader and health`

**Create directories:**

```
server/tests/test_plugin_loader/
server/tests/test_plugin_health_api/
```

**Add test files (see PHASE_11_RED_TESTS.md)**

**Why:** Tests define the contract RED-first. Implementation follows.

---

## TDD Workflow for Phase 11

1. **RED phase** – Write tests that expect safe behavior (tests fail because code not implemented)
2. **GREEN phase** – Implement loader v2, lifecycle, sandbox integration
3. **REFACTOR phase** – Optimize, add edge cases, performance

All tests run in CI. No implementation without RED test first.

---

## Verification Checklist

- [ ] All 5 commits pushed to `feature/phase-11-governance`
- [ ] `npm run type-check` passes (Python: `mypy server/app/plugins`)
- [ ] `npm run lint` passes (Python: `ruff check server/app/plugins`)
- [ ] RED test suite runs and tests **fail** (expected)
- [ ] CI workflow passes (RED tests are expected failures)
- [ ] PR created and ready for review

---

## Next Steps

1. **Implement PluginRegistry** with dependency checking
2. **Implement PluginLoader v2** that updates lifecycle states
3. **Wire ToolRunner** to `run_plugin_sandboxed`
4. **Add timeout/memory guards** to sandbox
5. **Implement health_model.PluginHealthResponse**

Each step has a RED test waiting.
