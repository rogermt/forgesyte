# Implementation Plan

## Overview

This plan addresses the "Invalid JSON from tool" error when pressing the PLAY button on the VideoTracker with yolo-tracker plugin. The error manifests as repeated 500 Internal Server Errors from `/v1/plugins/yolo-tracker/tools/player_detection/run`. The root causes include plugin name mismatches, insufficient server-side logging, and error handling gaps in the tool execution pipeline.

After thorough investigation of the codebase, the following root causes were identified:

### CRITICAL: Plugin Name Mismatch Between Manifest and Plugin Class

**OCR Plugin (working correctly):**
- `manifest.json`: `"id": "ocr"`, `"name": "ocr"`
- `Plugin.name`: `"ocr"`
- ✅ Consistent - lookup works

**yolo-tracker Plugin (broken):**
- `manifest.json`: `"id": "forgesyte-yolo-tracker"`, `"name": "forgesyte-yolo-tracker"`
- `Plugin.name`: `"yolo-tracker"`
- ❌ **MISMATCH causes plugin lookup failure!**

**Error flow:**
1. Frontend sends `pluginId: "yolo-tracker"` (from `Plugin.name`)
2. `run_plugin_tool()` calls `registry.get("yolo-tracker")`
3. Registry has key `"forgesyte-yolo-tracker"` (from manifest.json id)
4. Lookup returns `None` → raises `ValueError("Plugin 'yolo-tracker' not found")`
5. HTTPException returns plain text "Plugin 'yolo-tracker' not found" (not JSON!)
6. Frontend fails to parse as JSON → "Invalid JSON from tool"

### Secondary Issues

2. **Insufficient Server-Side Logging in Tool Execution:**
   - The `run_plugin_tool()` function in `plugin_management_service.py` lacks detailed logging
   - No logging of incoming requests, argument validation, or tool execution outcomes
   - Makes debugging 500 errors extremely difficult

3. **Missing Error Handling in JSON Response:**
   - When tool execution fails, the server may return non-JSON or malformed JSON
   - The frontend's `runTool.ts` catches this as "Invalid JSON from tool"
   - No structured error response is returned to the client

4. **No Request Validation Logging:**
   - Arguments passed to tools aren't logged
   - Frame processing parameters aren't visible in logs
   - Makes it impossible to verify what data reached the server

## Types

No new types need to be added. The existing types in `server/app/models.py` are sufficient.

## Files

### New Files to be Created

1. **`server/app/services/tool_execution_logger.py`** (NEW)
   - Purpose: Centralized logging utilities for tool execution
   - Contains structured logging functions for request/response tracking

2. **`server/tests/unit/test_tool_execution_logging.py`** (NEW)
   - Purpose: Unit tests for the new logging utilities

### Existing Files to be Modified

1. **`server/app/services/plugin_management_service.py`**
   - Changes:
     - Add detailed logging to `run_plugin_tool()` method
     - Log incoming arguments with sanitization for large payloads
     - Add try/except with structured error logging
     - Ensure consistent JSON response format even on error

2. **`server/app/api.py`**
   - Changes:
     - Add request logging to `run_plugin_tool()` endpoint
     - Log response status and processing time
     - Add structured error logging for exceptions

3. **`web-ui/src/utils/runTool.ts`**
   - Changes:
     - Add more detailed error logging for debugging
     - Log the actual response text when JSON parsing fails
     - Improve error messages to include response preview

### Files to be Deleted
- None

### Configuration File Updates
- None required

## Functions

### New Functions to be Created

1. **`tool_execution_logger.py::log_tool_request()`**
   - File: `server/app/services/tool_execution_logger.py`
   - Signature: `def log_tool_request(plugin_id: str, tool_name: str, args: Dict[str, Any]) -> None`
   - Purpose: Log tool execution request with sanitized arguments

2. **`tool_execution_logger.py::log_tool_response()`**
   - File: `server/app/services/tool_execution_logger.py`
   - Signature: `def log_tool_response(plugin_id: str, tool_name: str, result: Any, duration_ms: int) -> None`
   - Purpose: Log successful tool execution response

3. **`tool_execution_logger.py::log_tool_error()`**
   - File: `server/app/services/tool_execution_logger.py`
   - Signature: `def log_tool_error(plugin_id: str, tool_name: str, error: Exception, args: Dict[str, Any]) -> None`
   - Purpose: Log tool execution errors with full context

### Modified Functions

1. **`PluginManagementService.run_plugin_tool()`**
   - Current file: `server/app/services/plugin_management_service.py`
   - Required changes:
     - Add `logger.debug()` call at start with plugin_id, tool_name, arg count
     - Add `logger.debug()` call after finding plugin and tool
     - Add try/except with `logger.exception()` for all error cases
     - Ensure error responses follow consistent schema: `{"success": false, "error": "message"}`
     - Add processing time logging

2. **`run_plugin_tool()` endpoint in `api.py`**
   - Current file: `server/app/api.py`
   - Required changes:
     - Add logging of request arrival with endpoint details
     - Add logging of response status and timing
     - Wrap entire execution in try/except with structured error logging

### Removed Functions
- None

## Classes

### Modified Classes

1. **`PluginManagementService`**
   - File: `server/app/services/plugin_management_service.py`
   - Changes:
     - Add logging module import
     - Modify `run_plugin_tool()` method to include comprehensive logging

## Dependencies

### New Packages
- None required (using existing `logging` module)

### Package Version Changes
- None

## Testing

### Test File Requirements

1. **`server/tests/unit/test_tool_execution_logging.py`** (NEW)
   - Test `log_tool_request()` sanitizes large payloads
   - Test `log_tool_response()` formats correctly
   - Test `log_tool_error()` captures exception context

2. **Modify `server/tests/integration/test_video_tracker.py`**
   - Add assertions to verify logging output format
   - Ensure logs are written during test execution

### Existing Test Modifications
- `server/tests/api/test_plugins_run_tool.py`: Add logging verification

### Validation Strategies
- Run integration tests with `RUN_MODEL_TESTS=1`
- Verify logs appear in `forgesyte.log`
- Test error cases produce structured error responses

## Implementation Order

1. **Step 1:** Create `server/app/services/tool_execution_logger.py` with logging utilities
2. **Step 2:** Add logging to `run_plugin_tool()` in `plugin_management_service.py`
3. **Step 3:** Add request/response logging to `run_plugin_tool()` endpoint in `api.py`
4. **Step 4:** Improve error logging in `web-ui/src/utils/runTool.ts`
5. **Step 5:** Create `server/tests/unit/test_tool_execution_logging.py`
6. **Step 6:** Run tests to validate implementation
7. **Step 7:** Test end-to-end with video tracker to verify fix

## Success Criteria

- All tool execution requests are logged with plugin_id, tool_name, and argument summary
- All tool execution responses are logged with result keys and processing time
- All errors produce structured JSON responses with error details
- Frontend no longer shows "Invalid JSON from tool" for recoverable errors
- Server logs provide sufficient information to debug future issues without code changes

