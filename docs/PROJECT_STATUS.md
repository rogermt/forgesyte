# Project Status Report

**Generated**: 2024  
**Purpose**: Document findings about endpoint implementation and testing gaps

---

## Executive Summary

The endpoint `/v1/plugins/${pluginId}/tools/${toolName}/run` exists and handles tool execution for plugins, but integration tests are heavily mocked and do not test real plugin loading.

---

## Endpoint Implementation

### Location
- **File**: `server/app/api.py`
- **Function**: `run_plugin_tool()` (line 472)
- **Route**: `POST /plugins/{plugin_id}/tools/{tool_name}/run`

### Architecture
The endpoint delegates to the service layer:
```
api.run_plugin_tool() → PluginManagementService.run_plugin_tool() → registry.get(plugin_id) → getattr(plugin, tool_name)
```

### Plugin-Agnostic Design
The endpoint handler has **NO plugin-type-specific conditions**. It uses dynamic dispatch:
- `registry.get(plugin_id)` - finds ANY registered plugin
- `getattr(plugin, tool_name)` - gets ANY tool method

This is designed to work with any plugin that:
1. Is registered in the PluginRegistry
2. Has callable methods matching tool names

---

## Hardcoded Plugin References

### Found in Codebase

| File | Line | Reference | Type |
|------|------|-----------|------|
| `server/app/main.py` | 361 | `motion_detector` | WebSocket default param |
| `server/app/services/health_check.py` | - | `ocr_plugin` | Hardcoded in fixture |
| `server/app/services/vision_analysis.py` | - | `ocr_plugin` | Hardcoded |
| `server/tests/test_main.py` | - | `motion_detector`, `ocr` | Test fixtures |
| `server/app/mcp/adapter.py` | - | `ocr`, `motion` | Documentation examples |

### Impact
These hardcoded references mean the system was designed around specific plugins (OCR, motion_detector) and may not be fully generic.

---

## Test Coverage Analysis

### Integration Tests are Heavily Mocked

**File**: `server/tests/integration/test_video_tracker.py`

```python
@pytest.fixture(autouse=True)
def mock_tool_execution():
    mock_result = {"detections": [...]}
    with patch(
        "app.services.plugin_management_service.PluginManagementService.run_plugin_tool",
        return_value=mock_result,
    ):
        yield
```

**Problem**: All tests mock `run_plugin_tool()` at the service layer, bypassing:
- Actual plugin loading via entry points
- Real tool method invocation
- Plugin registration verification

### File: `server/tests/api/test_plugins_run_tool.py`

All tests use `@patch` on `PluginManagementService.run_plugin_tool`:
- `test_run_plugin_tool_success` - mocked
- `test_run_plugin_tool_not_found` - mocked
- `test_run_plugin_tool_invalid_args` - mocked
- `test_run_plugin_tool_timeout` - mocked
- `test_run_plugin_tool_unexpected_error` - mocked
- `test_run_plugin_tool_response_schema` - mocked

### File: `server/tests/test_plugin_loader.py`

Entry points are mocked:
```python
monkeypatch.setattr("app.plugin_loader.entry_points", lambda group: [mock_ep])
```

---

## What is NOT Tested

1. ❌ Real entry point plugin loading
2. ❌ Plugin discovery from installed packages
3. ❌ YOLO tracker integration with real models
4. ❌ Error handling for missing/wrong plugin names with real registry
5. ❌ Error handling for missing tool methods on real plugins
6. ❌ Plugin registration verification

---

## YOLO Tracker Plugin Configuration

**Entry Point** (`../forgesyte-plugins/plugins/forgesyte-yolo-tracker/pyproject.toml`):
```toml
[project.entry-points."forgesyte.plugins"]
yolo-tracker = "forgesyte_yolo_tracker.plugin:Plugin"
```

**Plugin Class** (`plugin.py`):
- `name = "yolo-tracker"`
- Tools: `player_detection`, `player_tracking`, `ball_detection`, `pitch_detection`, `radar`
- Inherits from nothing (not BasePlugin)

**Note**: Plugin does not extend `BasePlugin` from `server/app/plugin_loader.py`.

---

## MCP Adapter Limitation

The MCP adapter (`server/app/mcp/adapter.py`) only creates endpoints for `/v1/analyze?plugin=xxx`:
```python
invoke_endpoint: str = f"{self.base_url}/v1/analyze?plugin={plugin_name}"
```

This means **YOLO tracker tools are NOT exposed via MCP** - they only work via REST endpoint.

---

## Recommendations

### 1. Add Real Integration Tests
Create tests that:
- Install YOLO tracker as a development dependency
- Load plugins via entry points (not mocked)
- Test actual tool execution with real plugin

### 2. Remove Hardcoded Plugin References
- Make WebSocket plugin parameter truly dynamic
- Remove hardcoded `ocr_plugin` from health checks

### 3. Verify Plugin Registration
Add tests that:
- List all registered plugins
- Verify expected plugins are loaded
- Test error messages with available plugin names

### 4. Test BasePlugin Inheritance
Verify that plugins extending `BasePlugin` work correctly vs standalone plugin classes.

---

## Files to Review

- `server/app/api.py` - Endpoint handlers
- `server/app/services/plugin_management_service.py` - Plugin tool execution
- `server/app/plugin_loader.py` - Plugin loading and registration
- `server/app/main.py` - Application initialization
- `server/tests/integration/test_video_tracker.py` - Integration tests
- `server/tests/api/test_plugins_run_tool.py` - API endpoint tests

