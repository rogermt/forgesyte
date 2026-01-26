# Plan: Fix Plugin 'yolo-tracker' Not Found Error

## Issue Summary

When pressing play on YOLO Tracker, the server returns:
```
Plugin 'yolo-tracker' not found. Available: []
```

Despite the plugin being successfully loaded (as shown in logs), the `run_plugin_tool` method cannot find it because it uses `registry.list().get(plugin_id)` instead of `registry.get(plugin_id)`.

---

## Information Gathered

1. **Plugin Loading Works**: Logs confirm plugin is loaded successfully:
   - `"Entrypoint plugin loaded successfully", "plugin_name": "yolo-tracker"`
   - `"Plugins loaded successfully", "count": 2, "plugins": ["yolo-tracker", "ocr"]`

2. **Manifest Loading Works**: GET `/v1/plugins/yolo-tracker/manifest` returns 200 OK with 5 tools

3. **Tool Execution Fails**: POST `/v1/plugins/yolo-tracker/tools/player_tracking/run` returns 400 with "Plugin not found"

4. **Bug Location**: `server/app/services/plugin_management_service.py`, method `run_plugin_tool()`

5. **Bug Code**:
   ```python
   plugins_dict = self.registry.list()
   if isinstance(plugins_dict, dict):
       plugin = plugins_dict.get(plugin_id)  # Returns metadata dict, not PluginInterface!
   ```

6. **Expected Code**: Should use `self.registry.get(plugin_id)` which returns the plugin instance

---

## Plan: Detailed Code Update

### File to Edit: `server/app/services/plugin_management_service.py`

#### Change 1: Fix the plugin lookup in `run_plugin_tool()`

**Current Code (lines ~290-310)**:
```python
def run_plugin_tool(
    self,
    plugin_id: str,
    tool_name: str,
    args: Dict[str, Any],
) -> Dict[str, Any]:
    # 1. Find plugin in registry
    plugins_dict = self.registry.list()
    if isinstance(plugins_dict, dict):
        plugin = plugins_dict.get(plugin_id)
    else:
        plugin = next(
            (p for p in plugins_dict if getattr(p, "name", None) == plugin_id),
            None,
        )

    if not plugin:
        available = (
            list(plugins_dict.keys())
            if isinstance(plugins_dict, dict)
            else [getattr(p, "name", "unknown") for p in plugins_dict]
        )
        raise ValueError(
            f"Plugin '{plugin_id}' not found. " f"Available: {available}"
        )
```

**New Code**:
```python
def run_plugin_tool(
    self,
    plugin_id: str,
    tool_name: str,
    args: Dict[str, Any],
) -> Dict[str, Any]:
    # 1. Find plugin in registry
    plugin = self.registry.get(plugin_id)

    if not plugin:
        plugins_dict = self.registry.list()
        available = (
            list(plugins_dict.keys())
            if isinstance(plugins_dict, dict)
            else [getattr(p, "name", "unknown") for p in plugins_dict]
        )
        raise ValueError(
            f"Plugin '{plugin_id}' not found. Available: {available}"
        )
```

---

## Dependent Files to be Edited

| File | Change |
|------|--------|
| `server/app/services/plugin_management_service.py` | Fix `run_plugin_tool()` plugin lookup |

---

## Followup Steps

### 1. Add Integration Test

Create a test that verifies actual plugin lookup works without mocks:

```python
# server/tests/integration/test_plugin_lookup.py
async def test_run_plugin_tool_finds_loaded_plugin(self, client):
    """Verify run_plugin_tool finds plugin via registry.get()"""
    # This test should use a real (not mocked) plugin
    response = await client.post(
        "/v1/plugins/yolo-tracker/tools/player_tracking/run",
        json={"args": {"frame_base64": "test...", "device": "cpu"}},
    )
    assert response.status_code == 200
```

### 2. Verify Existing Tests Pass

Run the existing test suite:
```bash
cd server && python -m pytest tests/integration/test_video_tracker.py -v
```

### 3. Manual Verification

1. Start the server: `python -m app.main`
2. Open the web UI
3. Select "yolo-tracker" plugin
4. Select "player_tracking" tool
5. Press Play button
6. Verify no "Plugin not found" error

---

## Checklist

- [ ] Edit `server/app/services/plugin_management_service.py` to fix plugin lookup
- [ ] Run existing tests to ensure no regressions
- [ ] Add integration test for real plugin lookup
- [ ] Manual verification of the fix

---

## Questions for Confirmation

1. **Should we also fix the error message to show the actual available plugins?** 
   Currently it shows `Available: []` because the dict keys aren't being passed correctly. The fix should show the actual available plugin names.

2. **Should we add logging when a plugin is not found?**
   Currently there's no debug logging for this failure case. Adding it would help with future debugging.

