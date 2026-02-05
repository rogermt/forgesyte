# Bug: `/v1/plugins` endpoint returns empty list despite OCR loaded

## Status
🔴 **OPEN** - Phase 11 blocker

## Symptoms

Server logs confirm plugin loaded:
```
"Plugins loaded successfully", "count": 1, "plugins": ["ocr"]
```

But API returns empty list:
```bash
$ curl http://127.0.0.1:8000/v1/plugins
[]
```

Audit script confirms discrepancy:
```bash
$ python scripts/audit_plugins.py --url http://127.0.0.1:8000
✓ Found 0 plugin(s)  ← WRONG: should be 1
```

## Root Cause Analysis

**Registry Divergence Bug**: Plugin loader and API are using different registry instances.

### Hypothesis Locations

1. **`server/app/plugins/loader/plugin_registry.py`**
   - Singleton getter may not be enforced
   - Multiple `PluginRegistry()` instances possible
   - Registry reachable via multiple code paths

2. **`server/app/api.py` line ~457**
   - `list_plugins()` may call wrong method
   - `registry.list()` returns dict, not list
   - May need to extract values from dict and convert

3. **`server/app/plugin_loader/__init__.py`**
   - Plugin discovery path may differ from registry path
   - Loader may instantiate its own registry
   - Loader → registry registration may not complete

## Phase 11 Contract Violation

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Registry is singleton | ❓ Unknown | Need singleton test |
| All plugins registered | ❌ NO | Audit shows 0 plugins |
| All plugins visible in API | ❌ NO | `/v1/plugins` returns `[]` |
| Lifecycle state set for all | ❌ NO | No state tracking visible |

## Reproduction Steps

```bash
cd server

# Start server (OCR plugin auto-loads)
uv run uvicorn app.main:app --reload

# In another terminal:
uv run python ../scripts/audit_plugins.py --url http://127.0.0.1:8000
# Expected: Found 1 plugin(s)
# Actual: Found 0 plugin(s)
```

## Impact

- ❌ Phase 11 API contract broken
- ❌ Web-UI cannot enumerate plugins
- ❌ Audit script fails
- ⚠️ Silent failure (no error, just empty list)
- 🔴 BLOCKS Phase 11 release

## Fix Plan

See: [PHASE_11_PLUGIN_REGISTRY_FIX.md](../plans/Phase_11/PHASE_11_PLUGIN_REGISTRY_FIX.md)

### Quick Summary

1. **Enforce singleton pattern** in `plugin_registry.py`
   - Prevent `PluginRegistry()` instantiation
   - Force use of `get_registry()`
   
2. **Add startup self-audit**
   - Verify registry ≠ empty when plugins discovered
   - Log loader → registry consistency
   - Fail hard in dev/CI if divergence detected

3. **Fix API endpoint**
   - Use `registry.list_all()` instead of `registry.list()`
   - Return flat list of health responses (Phase 11 contract)

4. **Add debug logging**
   - Print registry contents at boot
   - Print API response shape
   - Enable root-cause diagnosis

## Testing Strategy

- ✅ Unit: Singleton enforcement test
- ✅ Integration: Audit script against local server
- ✅ E2E: Full Phase 11 test suite (49 tests)

## Related

- Issue #139: Phase 11 Governance  
- Thread: T-019c2e77-a20e-777a-8215-d6a94acafcaa (Commit 8)
- Notes: PHASE_11_Notes_05.md
