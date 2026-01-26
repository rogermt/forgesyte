# TODO: Fix Plugin 'yolo-tracker' Not Found Error

## Issue
Error: Plugin 'yolo-tracker' not found. Available: []

## Root Cause
`run_plugin_tool()` uses `registry.list().get(plugin_id)` instead of `registry.get(plugin_id)`

## Plan
- [x] Create TODO.md to track progress
- [x] Edit `server/app/services/plugin_management_service.py` to fix plugin lookup
- [x] Run existing tests to ensure no regressions (11/11 passed)
- [x] Add TDD test for `run_plugin_tool()` to verify fix (5 new tests, 15/16 passed)
- [x] Fix 6 failing E2E tests (timeouts)
- [x] Commit all changes

## Status: ✅ COMPLETED

### Changes Made

**File: `server/app/services/plugin_management_service.py`**

Changed plugin lookup from:
```python
plugins_dict = self.registry.list()
if isinstance(plugins_dict, dict):
    plugin = plugins_dict.get(plugin_id)
else:
    plugin = next(...)
```

To:
```python
plugin = self.registry.get(plugin_id)
```

### Tests Added
- `test_run_plugin_tool_success_sync` ✓
- `test_run_plugin_tool_plugin_not_found` ✓
- `test_run_plugin_tool_tool_not_found` ✓
- `test_run_plugin_tool_get_returns_instance_not_metadata` ✓
- `test_run_plugin_tool_success_async` ✓ (async event loop issue fixed)

### E2E Test Fixes
- Fixed 6 timeout-related test failures by adding `waitFor` with 10s timeout

