# Phase 11 Plugin Registry Fix Plan

**Objective**: Fix registry divergence bug where `/v1/plugins` returns empty despite OCR loaded.

**Status**: Ready to implement
**Estimated**: 2-3 hours
**Blocker**: Yes, for Phase 11 release

---

## Root Cause

Plugin loader and API may be using different registry instances, causing:
- Loader sees: `["ocr"]` (1 plugin)
- API sees: `[]` (0 plugins)
- Silent failure, no error thrown

---

## Implementation Steps

### Step 1: Enforce Singleton Pattern (30 min)

**File**: `server/app/plugins/loader/plugin_registry.py`

**Change**: Prevent direct instantiation, enforce `get_registry()` use

```python
class PluginRegistry:
    _instance: Optional["PluginRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls):
        raise RuntimeError(
            "PluginRegistry is a singleton. Use get_registry() instead."
        )

    @classmethod
    def _create_instance(cls) -> "PluginRegistry":
        """Internal factory for singleton."""
        obj = super().__new__(cls)
        return obj


def get_registry() -> PluginRegistry:
    """Get the global PluginRegistry singleton."""
    if PluginRegistry._instance is None:
        with PluginRegistry._lock:
            if PluginRegistry._instance is None:
                PluginRegistry._instance = PluginRegistry._create_instance()
    return PluginRegistry._instance
```

**Verification**:
```bash
# Should raise RuntimeError
uv run python -c "from app.plugins.loader.plugin_registry import PluginRegistry; PluginRegistry()"

# Should work
uv run python -c "from app.plugins.loader.plugin_registry import get_registry; print(get_registry())"
```

---

### Step 2: Add Startup Self-Audit (45 min)

**File**: `server/app/plugins/loader/startup_audit.py` (NEW)

```python
"""Phase 11 Loader Startup Self-Audit

Ensures:
- Registry not empty after plugin discovery
- All discovered plugins registered
- No plugin missing lifecycle state
"""

import logging
from app.plugins.loader.plugin_registry import get_registry

logger = logging.getLogger(__name__)


def run_startup_audit(discovered_plugins: list[str]) -> None:
    """Verify loader → registry consistency at boot.
    
    Args:
        discovered_plugins: List of plugin names found during discovery
        
    Raises:
        RuntimeError: If PHASE11_STRICT_AUDIT=1 and divergence detected
    """
    registry = get_registry()
    statuses = registry.all_status()
    
    logger.info("=== Phase 11 Startup Audit ===")
    logger.info(f"Discovered: {discovered_plugins}")
    logger.info(f"Registry: {[s.name for s in statuses]}")
    
    # Check 1: Registry not empty when plugins discovered
    if discovered_plugins and len(statuses) == 0:
        msg = (
            "Phase 11 invariant violated: Plugins discovered but registry empty. "
            "Possible causes: wrong singleton, registration failed, wrong instance."
        )
        logger.error(msg)
        _maybe_strict_fail(msg)
    
    # Check 2: All discovered plugins in registry
    missing = [p for p in discovered_plugins if p not in [s.name for s in statuses]]
    if missing:
        msg = f"Phase 11 invariant violated: Missing from registry: {missing}"
        logger.error(msg)
        _maybe_strict_fail(msg)
    
    # Check 3: All plugins have lifecycle state
    for s in statuses:
        if s.state is None:
            msg = f"Phase 11 invariant violated: Plugin '{s.name}' has no state"
            logger.error(msg)
            _maybe_strict_fail(msg)
    
    logger.info("=== Startup Audit Complete ===")


def _maybe_strict_fail(msg: str) -> None:
    """Fail hard in strict mode (dev/CI), log only in production."""
    import os
    if os.getenv("PHASE11_STRICT_AUDIT") == "1":
        raise RuntimeError(msg)
```

**Integration**: `server/app/plugins/loader/__init__.py` or `server/app/main.py`

After plugin loading, call:
```python
from app.plugins.loader.startup_audit import run_startup_audit

discovered = loader.load_all_plugins()
logger.info("Plugins loaded", count=len(discovered), names=discovered)

# TEST-CHANGE (Phase 11): Run loader-startup self-audit
run_startup_audit(discovered)
```

**Verification**:
```bash
# Normal mode (logs warnings)
uv run uvicorn app.main:app

# Strict mode (fails if issue)
PHASE11_STRICT_AUDIT=1 uv run uvicorn app.main:app
```

---

### Step 3: Fix API Endpoint (45 min)

**File**: `server/app/api.py` line ~457

**Current** (broken):
```python
@router.get("/plugins")
async def list_plugins(service: PluginManagementService = Depends(get_plugin_service)):
    plugins = await service.list_plugins()
    # Returns plugin manifests, not health responses
    return [p.model_dump() if hasattr(p, "model_dump") else p for p in plugins]
```

**Fixed** (Phase 11):
```python
@router.get("/plugins")
async def list_plugins() -> List[Dict[str, Any]]:
    """List all plugins with health status (Phase 11).
    
    Returns flat list of PluginHealthResponse dicts.
    """
    from .plugins.loader.plugin_registry import get_registry
    
    # Use registry directly, not service (which returns manifests)
    registry = get_registry()
    plugins = registry.list_all()  # Returns PluginHealthResponse objects
    
    logger.debug("Plugins listed", extra={"count": len(plugins)})
    
    # Convert to dicts for JSON response
    return [
        plugin.model_dump() if hasattr(plugin, "model_dump") else plugin
        for plugin in plugins
    ]
```

**Key changes**:
- Use `registry.list_all()` not `service.list_plugins()`
- Return health responses, not manifests
- Direct registry access (singleton-enforced)

**Verification**:
```bash
# Should return list of health dicts
curl http://127.0.0.1:8000/v1/plugins | jq .

# Should show Phase 11 fields:
# [
#   {
#     "name": "ocr",
#     "state": "INITIALIZED",
#     "description": "...",
#     "reason": null,
#     "success_count": 0,
#     ...
#   }
# ]
```

---

### Step 4: Add Debug Logging (30 min)

**File**: `server/app/main.py` after plugin loading

```python
def log_registry_state() -> None:
    """Debug: Print registry contents at startup."""
    from app.plugins.loader.plugin_registry import get_registry
    
    registry = get_registry()
    statuses = registry.all_status()
    
    logger.info("=== Phase 11 Registry State ===")
    logger.info(f"Total plugins: {len(statuses)}")
    for s in statuses:
        logger.info(f"  - {s.name}: {s.state.value if s.state else 'NO_STATE'}")
    logger.info("===============================")


# Call in lifespan startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    log_registry_state()
    yield
    # Shutdown
```

**Output** (normal):
```
=== Phase 11 Registry State ===
Total plugins: 1
  - ocr: INITIALIZED
===============================
```

**Output** (broken):
```
=== Phase 11 Registry State ===
Total plugins: 0
===============================
ERROR: Phase 11 invariant violated...
```

---

## Testing Checklist

### Unit Tests
- [ ] Test singleton enforcement (raises on direct instantiation)
- [ ] Test `get_registry()` always returns same instance
- [ ] Test startup audit detects missing plugins
- [ ] Test startup audit detects empty registry

### Integration Tests
- [ ] Start server, verify OCR loads
- [ ] Call `/v1/plugins`, verify 1 item returned
- [ ] Verify returned item has all 10 Phase 11 fields
- [ ] Verify state is one of: LOADED, INITIALIZED, RUNNING, FAILED, UNAVAILABLE

### Audit Script Test
```bash
python scripts/audit_plugins.py --url http://127.0.0.1:8000
# Should show: Found 1 plugin(s)
# Should NOT show: No plugins loaded warning
```

### E2E Test
```bash
# Full test suite
uv run pytest tests/ -v --tb=short
# Should pass all 49 tests
```

---

## Commit Message

```
TEST-CHANGE (Phase 11): Fix plugin registry divergence bug

Enforce singleton pattern to prevent multiple registry instances.
Add startup self-audit to detect loader → registry inconsistency.
Fix API endpoint to use registry.list_all() for health responses.
Add debug logging to print registry state at boot.

Fixes:
- /v1/plugins returning empty despite OCR loaded
- Silent registry divergence failures
- Audit script showing 0 plugins

Tests:
- Singleton enforcement test
- Startup audit consistency checks
- E2E: 49 passing tests
- Audit script validation
```

---

## Rollback Plan

If issues arise:
1. Revert singleton enforcement (keep allow `PluginRegistry()` again)
2. Keep audit logging (low risk)
3. Keep debug output (low risk)
4. Revert API endpoint to use `service.list_plugins()`

Commits are independent, can rollback individually.

---

## Phase 11 Contract Impact

✅ **FIXED**:
- `/v1/plugins` returns flat list
- Each item has 10 required fields
- State enum validation
- Null handling for optional fields

✅ **ENFORCED**:
- Singleton registry (prevents divergence)
- Startup audit (catches issues early)
- Debug logging (root-cause diagnosis)

---

## Files Changed

| File | Lines | Type |
|------|-------|------|
| `server/app/plugins/loader/plugin_registry.py` | ~20 | Modify (singleton) |
| `server/app/plugins/loader/startup_audit.py` | ~60 | NEW |
| `server/app/api.py` | ~15 | Modify (use registry) |
| `server/app/main.py` | ~15 | Modify (call audit + logging) |
| `server/tests/plugins/test_registry_singleton.py` | ~30 | NEW |
| `server/tests/plugins/test_startup_audit.py` | ~40 | NEW |

**Total**: ~195 lines of code + tests

---

## Success Criteria

- ✅ Singleton pattern enforced
- ✅ Startup audit passes with 1 plugin found
- ✅ `/v1/plugins` returns list with 1 item
- ✅ Item has all 10 Phase 11 fields
- ✅ Audit script shows: Found 1 plugin(s)
- ✅ All 49 tests pass
- ✅ No regressions in other endpoints
