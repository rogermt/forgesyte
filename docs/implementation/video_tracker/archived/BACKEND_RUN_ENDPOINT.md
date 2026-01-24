# Backend: `/plugins/{id}/tools/{tool}/run` Endpoint

**File:** `forgesyte/server/app/api.py`  
**Type:** POST endpoint  
**Purpose:** Execute a plugin tool directly (synchronous) with frame data  
**Status:** Ready to implement  

---

## Overview

Executes a plugin tool immediately and returns JSON result. Used for real-time video frame processing.

**Request:**
```
POST /v1/plugins/forgesyte-yolo-tracker/tools/player_detection/run
{
  "args": {
    "frame_base64": "iVBORw0KGgo...",
    "device": "cpu",
    "annotated": false
  }
}
```

**Response:**
```json
{
  "tool_name": "player_detection",
  "plugin_id": "forgesyte-yolo-tracker",
  "result": {
    "detections": [
      {"x1": 100, "y1": 200, "x2": 150, "y2": 350, "confidence": 0.92},
      ...
    ]
  },
  "processing_time_ms": 42
}
```

---

## Implementation

### 1. Data Models

**Location:** `forgesyte/server/app/models.py` (add to file)

```python
from pydantic import BaseModel, Field
from typing import Dict, Any

class PluginToolRunRequest(BaseModel):
    """Request to run a plugin tool."""
    
    args: Dict[str, Any] = Field(
        ...,
        description="Tool arguments (matches manifest input schema)",
        example={
            "frame_base64": "iVBORw0KGgo...",
            "device": "cpu",
            "annotated": False
        }
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "args": {
                    "frame_base64": "base64_encoded_image",
                    "device": "cpu",
                    "annotated": False
                }
            }
        }


class PluginToolRunResponse(BaseModel):
    """Response from running a plugin tool."""
    
    tool_name: str = Field(
        ...,
        description="Name of the executed tool"
    )
    
    plugin_id: str = Field(
        ...,
        description="ID of the plugin"
    )
    
    result: Dict[str, Any] = Field(
        ...,
        description="Tool execution result (matches manifest output schema)"
    )
    
    processing_time_ms: int = Field(
        ...,
        description="Time spent in tool execution (milliseconds)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "tool_name": "player_detection",
                "plugin_id": "forgesyte-yolo-tracker",
                "result": {
                    "detections": [
                        {"x1": 100, "y1": 200, "x2": 150, "y2": 350, "confidence": 0.92}
                    ]
                },
                "processing_time_ms": 42
            }
        }
```

### 2. Endpoint Code

**Location:** `forgesyte/server/app/api.py` (add after manifest endpoint, ~line 400)

```python
import time  # Add to imports at top

@router.post("/plugins/{plugin_id}/tools/{tool_name}/run", response_model=PluginToolRunResponse)
async def run_plugin_tool(
    plugin_id: str,
    tool_name: str,
    request: PluginToolRunRequest,
    plugin_service: PluginManagementService = Depends(get_plugin_service),
) -> PluginToolRunResponse:
    """Execute a plugin tool directly (synchronous).
    
    Runs a specified tool from a plugin with the provided arguments.
    This is a synchronous endpoint used for real-time frame processing.
    For batch/video processing, use the async job endpoints instead.
    
    Args:
        plugin_id: Plugin ID (e.g., "forgesyte-yolo-tracker")
        tool_name: Tool name (e.g., "player_detection")
        request: Tool execution request with arguments
        plugin_service: Plugin management service (injected)
    
    Returns:
        PluginToolRunResponse with:
        - tool_name: Name of executed tool
        - plugin_id: Plugin ID
        - result: Tool output (dict, matches manifest output schema)
        - processing_time_ms: Execution time
    
    Raises:
        HTTPException(400): Invalid arguments or plugin execution failed
        HTTPException(404): Plugin or tool not found
        HTTPException(500): Unexpected error
    
    Example:
        POST /v1/plugins/forgesyte-yolo-tracker/tools/player_detection/run
        {
            "args": {
                "frame_base64": "iVBORw0KGgo...",
                "device": "cpu",
                "annotated": false
            }
        }
        → 200 OK
        {
            "tool_name": "player_detection",
            "plugin_id": "forgesyte-yolo-tracker",
            "result": {"detections": [...]},
            "processing_time_ms": 42
        }
    """
    try:
        # Record start time
        start_time = time.time()
        
        # Execute tool
        logger.debug(
            f"Executing tool '{tool_name}' on plugin '{plugin_id}' "
            f"with {len(request.args)} args"
        )
        
        result = plugin_service.run_plugin_tool(
            plugin_id=plugin_id,
            tool_name=tool_name,
            args=request.args
        )
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Log successful execution
        logger.info(
            f"Tool execution successful: {plugin_id}/{tool_name} "
            f"({processing_time_ms}ms)"
        )
        
        return PluginToolRunResponse(
            tool_name=tool_name,
            plugin_id=plugin_id,
            result=result,
            processing_time_ms=processing_time_ms
        )
        
    except ValueError as e:
        # Plugin/tool not found or validation error
        logger.warning(f"Tool execution validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except TimeoutError as e:
        # Tool execution timed out
        logger.error(f"Tool execution timeout: {e}")
        raise HTTPException(
            status_code=408,
            detail=f"Tool execution timed out: {str(e)}"
        )
    
    except Exception as e:
        # Unexpected error
        logger.error(
            f"Unexpected error executing tool '{tool_name}' "
            f"on plugin '{plugin_id}': {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Tool execution failed: {str(e)}"
        )
```

### 3. Service Method

**Location:** `forgesyte/server/app/services/plugin_management_service.py` (add method)

```python
import asyncio
import time

def run_plugin_tool(
    self,
    plugin_id: str,
    tool_name: str,
    args: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute a plugin tool with given arguments.
    
    Finds the plugin, locates the tool function, validates arguments,
    and executes the tool. Handles both sync and async tool functions.
    
    Args:
        plugin_id: Plugin ID
        tool_name: Tool function name (must exist as method on plugin)
        args: Tool arguments (dict, should match manifest input schema)
    
    Returns:
        Tool result dict (should match manifest output schema)
    
    Raises:
        ValueError: Plugin/tool not found, or validation error
        TimeoutError: Tool execution exceeded timeout
        Exception: Tool execution failed
    """
    
    # 1. Validate plugin exists
    plugin = self.get_plugin(plugin_id)
    if not plugin:
        raise ValueError(
            f"Plugin '{plugin_id}' not found. "
            f"Available: {[p.name for p in self._plugins.values()]}"
        )
    
    logger.debug(f"Found plugin: {plugin}")
    
    # 2. Validate tool exists
    if not hasattr(plugin, tool_name) or not callable(getattr(plugin, tool_name)):
        available_tools = [
            attr for attr in dir(plugin)
            if not attr.startswith('_') and callable(getattr(plugin, attr))
        ]
        raise ValueError(
            f"Tool '{tool_name}' not found in plugin '{plugin_id}'. "
            f"Available: {available_tools}"
        )
    
    logger.debug(f"Found tool: {plugin}.{tool_name}")
    
    # 3. Get tool function
    tool_func = getattr(plugin, tool_name)
    
    # 4. Execute tool (handle async/sync)
    try:
        if asyncio.iscoroutinefunction(tool_func):
            # Async tool: run in executor with timeout
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    asyncio.wait_for(
                        tool_func(**args),
                        timeout=30.0  # 30-second timeout per frame
                    )
                )
            finally:
                loop.close()
        else:
            # Sync tool: call directly
            result = tool_func(**args)
        
        logger.debug(f"Tool returned result with keys: {list(result.keys()) if isinstance(result, dict) else 'unknown'}")
        
        return result
    
    except asyncio.TimeoutError:
        raise TimeoutError(f"Tool '{tool_name}' execution exceeded 30 second timeout")
    
    except TypeError as e:
        # Argument mismatch
        raise ValueError(
            f"Invalid arguments for tool '{tool_name}': {e}. "
            f"Check manifest input schema."
        )
    
    except Exception as e:
        # Tool execution error
        logger.error(f"Tool '{tool_name}' execution failed: {e}", exc_info=True)
        raise Exception(f"Tool execution error: {str(e)}")
```

### 4. Import Statements

**Location:** Top of `forgesyte/server/app/api.py`

Add to existing imports:
```python
import time
from .models import PluginToolRunRequest, PluginToolRunResponse
```

---

## Testing

See [TESTS_BACKEND_CPU.md](./TESTS_BACKEND_CPU.md) for comprehensive test suite.

---

## Performance Expectations

| Device | Time/Frame | FPS | Notes |
|--------|-----------|-----|-------|
| CPU | 100–500ms | 2–10 | Acceptable for real-time |
| GPU | 20–100ms | 10–50 | Great performance |

---

## Error Handling

| Status | Reason | Example |
|--------|--------|---------|
| 400 | Bad arguments or validation error | frame_base64 missing |
| 404 | Plugin or tool not found | Typo in plugin_id or tool_name |
| 408 | Timeout (>30s) | Model inference too slow |
| 500 | Unexpected error | Model loading failure |

---

## Related Files

- [BACKEND_MANIFEST_ENDPOINT.md](./BACKEND_MANIFEST_ENDPOINT.md) — Tool schema discovery
- [BACKEND_CACHE_SERVICE.md](./BACKEND_CACHE_SERVICE.md) — Cache manifest
- [TESTS_BACKEND_CPU.md](./TESTS_BACKEND_CPU.md) — Complete test suite
- [HOOK_USE_VIDEO_PROCESSOR.md](./HOOK_USE_VIDEO_PROCESSOR.md) — Web-UI calls this endpoint
