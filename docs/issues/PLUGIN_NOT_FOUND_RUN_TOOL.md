# Issue: Plugin 'yolo-tracker' Not Found Error

## Summary

When pressing the play button on the YOLO Tracker, users receive a `400 Bad Request` error with the message:

```
Plugin 'yolo-tracker' not found. Available: []
```

## Root Cause Analysis

### The Bug Location

**File**: `server/app/services/plugin_management_service.py`  
**Method**: `run_plugin_tool()` (lines ~290-310)

### Problem Description

The `run_plugin_tool` method incorrectly looks up plugins using `self.registry.list().get(plugin_id)` instead of `self.registry.get(plugin_id)`.

The issue is in this code block:

```python
def run_plugin_tool(self, plugin_id: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    # 1. Find plugin in registry
    plugins_dict = self.registry.list()
    if isinstance(plugins_dict, dict):
        plugin = plugins_dict.get(plugin_id)  # <-- BUG: Wrong lookup!
```

### Why This Fails

1. `self.registry.list()` returns: `{"yolo-tracker": {...metadata...}, "ocr": {...}}`
2. `plugins_dict.get("yolo-tracker")` correctly finds the metadata dictionary
3. **BUT** the subsequent code expects `plugin` to be a `PluginInterface` instance, not a dict:
   ```python
   if not plugin:
       # This branch is taken because dict is truthy
   ...
   # 2. Validate tool exists
   if not hasattr(plugin, tool_name) or not callable(getattr(plugin, tool_name)):
       # This fails because dicts don't have tool methods
   ```

### The Logs Confirm the Plugin is Loaded

From the server logs:
```
{"timestamp": "2026-01-26T07:13:22.733316+00:00", "name": "app.plugin_loader", "message": "Entrypoint plugin loaded successfully", "plugin_name": "yolo-tracker", "source": "entrypoint:yolo-tracker"}
{"timestamp": "2026-01-26T07:13:22.831243+00:00", "name": "app.main", "message": "Plugins loaded successfully", "count": 2, "plugins": ["yolo-tracker", "ocr"]}
```

The plugin is successfully loaded but cannot be found when executing tools because of the incorrect lookup.

## Expected Behavior

When `POST /v1/plugins/yolo-tracker/tools/player_tracking/run` is called:
1. Server should find the `yolo-tracker` plugin instance
2. Validate that `player_tracking` tool exists on the plugin
3. Execute the tool and return results

## Actual Behavior

Server returns `400 Bad Request` with:
```
{"detail": "Plugin 'yolo-tracker' not found. Available: []"}
```

## Fix Required

Change the lookup in `run_plugin_tool()` to use `self.registry.get()` which returns the `PluginInterface` instance:

```python
def run_plugin_tool(self, plugin_id: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    # 1. Find plugin in registry
    plugin = self.registry.get(plugin_id)
    
    if not plugin:
        plugins_dict = self.registry.list()
        available = list(plugins_dict.keys()) if isinstance(plugins_dict, dict) else []
        raise ValueError(
            f"Plugin '{plugin_id}' not found. Available: {available}"
        )
```

## Affected Endpoints

- `POST /v1/plugins/{plugin_id}/tools/{tool_name}/run` - All plugin tool execution

## Test Coverage

The integration tests in `server/tests/integration/test_video_tracker.py` use mocks that bypass this bug, so they don't catch this issue. Tests should be added or updated to verify the actual registry lookup works correctly.

