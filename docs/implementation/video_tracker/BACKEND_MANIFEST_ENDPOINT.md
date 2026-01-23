# Backend: `/plugins/{id}/manifest` Endpoint

**File:** `forgesyte/server/app/api.py`  
**Type:** GET endpoint  
**Purpose:** Return plugin manifest with tool schemas  
**Status:** Ready to implement  

---

## Overview

Exposes plugin manifest (tool names, input/output schemas) so web-ui can discover tools dynamically.

**Request:**
```
GET /v1/plugins/forgesyte-yolo-tracker/manifest
```

**Response:**
```json
{
  "id": "forgesyte-yolo-tracker",
  "name": "YOLO Football Tracker",
  "version": "1.0.0",
  "description": "...",
  "tools": {
    "player_detection": {
      "description": "Detect players in frame",
      "inputs": {
        "frame_base64": "string (base64-encoded JPEG)",
        "device": "string (cpu|cuda)",
        "annotated": "boolean"
      },
      "outputs": {
        "detections": "array<{x1, y1, x2, y2, confidence}>",
        "annotated_frame_base64": "string? (if annotated=true)"
      }
    },
    ...
  }
}
```

---

## Implementation

### 1. Endpoint Code

**Location:** `forgesyte/server/app/api.py` (add after line ~380, after other `/plugins/` endpoints)

```python
@router.get("/plugins/{plugin_id}/manifest")
async def get_plugin_manifest(
    plugin_id: str,
    plugin_service: PluginManagementService = Depends(get_plugin_service),
) -> Dict[str, Any]:
    """Get plugin manifest including tool schemas.
    
    The manifest describes what tools a plugin exposes, their input schemas,
    and output schemas. This enables the web-ui to dynamically discover and
    call tools without hardcoding plugin logic.
    
    Args:
        plugin_id: Plugin ID (e.g., "forgesyte-yolo-tracker")
        plugin_service: Plugin management service (injected)
    
    Returns:
        Manifest dict:
        {
            "id": "forgesyte-yolo-tracker",
            "name": "YOLO Football Tracker",
            "version": "1.0.0",
            "description": "...",
            "tools": {
                "player_detection": {
                    "description": "...",
                    "inputs": {...},
                    "outputs": {...}
                },
                ...
            }
        }
    
    Raises:
        HTTPException(404): Plugin not found or has no manifest
        HTTPException(500): Error reading manifest file
    
    Example:
        GET /v1/plugins/forgesyte-yolo-tracker/manifest
        → 200 OK
        {
            "id": "forgesyte-yolo-tracker",
            "name": "YOLO Football Tracker",
            "tools": { ... }
        }
    """
    try:
        manifest = plugin_service.get_plugin_manifest(plugin_id)
        if not manifest:
            raise HTTPException(
                status_code=404,
                detail=f"Plugin '{plugin_id}' not found or has no manifest"
            )
        return manifest
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting manifest for plugin '{plugin_id}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error reading manifest: {str(e)}"
        )
```

### 2. Service Method

**Location:** `forgesyte/server/app/services/plugin_management_service.py` (add method)

```python
def get_plugin_manifest(self, plugin_id: str) -> Optional[Dict[str, Any]]:
    """Get manifest from a loaded plugin.
    
    Reads the plugin's manifest.json file if available. This is a synchronous
    operation that should be fast (usually <10ms) since manifests are small.
    
    Args:
        plugin_id: Plugin ID
    
    Returns:
        Manifest dict from manifest.json, or None if plugin not found
    
    Raises:
        Exception: If manifest file cannot be read
    """
    plugin = self.get_plugin(plugin_id)
    if not plugin:
        return None
    
    # Try to read manifest.json from plugin module
    try:
        import json
        import sys
        from pathlib import Path
        
        # Get plugin module
        plugin_module_name = plugin.__class__.__module__
        plugin_module = sys.modules.get(plugin_module_name)
        if not plugin_module or not hasattr(plugin_module, '__file__'):
            logger.warning(
                f"Could not locate module for plugin '{plugin_id}': "
                f"{plugin_module_name}"
            )
            return None
        
        # Find manifest.json relative to plugin module
        plugin_dir = Path(plugin_module.__file__).parent
        manifest_path = plugin_dir / "manifest.json"
        
        if not manifest_path.exists():
            logger.warning(
                f"No manifest.json found for plugin '{plugin_id}' "
                f"at {manifest_path}"
            )
            return None
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        logger.debug(
            f"Loaded manifest for plugin '{plugin_id}': "
            f"{len(manifest.get('tools', {}))} tools"
        )
        
        return manifest
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest for '{plugin_id}': {e}")
        raise
    except Exception as e:
        logger.error(
            f"Error reading manifest for plugin '{plugin_id}': {e}"
        )
        raise
```

### 3. Import Statements

**Location:** Top of `forgesyte/server/app/api.py`

Add to existing imports (if not already present):
```python
import json
```

---

## Testing

### Unit Test: CPU-Only

**Location:** `forgesyte/server/tests/api/test_plugins_manifest.py` (NEW FILE)

```python
"""Tests for GET /plugins/{id}/manifest endpoint."""

import json
import pytest
from unittest.mock import MagicMock, patch

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_plugin():
    """Create a mock plugin with manifest."""
    plugin = MagicMock()
    plugin.__class__.__module__ = "test_plugin_module"
    return plugin


def test_get_plugin_manifest_success(client, mock_plugin):
    """Test successfully retrieving plugin manifest."""
    # Mock the service to return a valid manifest
    expected_manifest = {
        "id": "test-plugin",
        "name": "Test Plugin",
        "version": "1.0.0",
        "description": "A test plugin",
        "tools": {
            "detect": {
                "description": "Detect objects",
                "inputs": {"frame_base64": "string"},
                "outputs": {"detections": "array"}
            }
        }
    }
    
    with patch('app.services.plugin_management_service.PluginManagementService.get_plugin_manifest') as mock_get:
        mock_get.return_value = expected_manifest
        
        response = client.get("/v1/plugins/test-plugin/manifest")
        
        assert response.status_code == 200
        assert response.json() == expected_manifest


def test_get_plugin_manifest_not_found(client):
    """Test 404 when plugin doesn't exist."""
    with patch('app.services.plugin_management_service.PluginManagementService.get_plugin_manifest') as mock_get:
        mock_get.return_value = None
        
        response = client.get("/v1/plugins/nonexistent/manifest")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_get_plugin_manifest_invalid_json(client):
    """Test 500 when manifest.json is invalid."""
    with patch('app.services.plugin_management_service.PluginManagementService.get_plugin_manifest') as mock_get:
        # Simulate invalid JSON error
        mock_get.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        response = client.get("/v1/plugins/bad-plugin/manifest")
        
        assert response.status_code == 500


def test_get_plugin_manifest_schema(client):
    """Test that manifest follows expected schema."""
    expected_manifest = {
        "id": "yolo-tracker",
        "name": "YOLO Tracker",
        "version": "1.0.0",
        "tools": {
            "player_detection": {
                "description": "Detect players",
                "inputs": {
                    "frame_base64": "string",
                    "device": "string",
                    "annotated": "boolean"
                },
                "outputs": {
                    "detections": "array",
                    "annotated_frame_base64": "string?"
                }
            }
        }
    }
    
    with patch('app.services.plugin_management_service.PluginManagementService.get_plugin_manifest') as mock_get:
        mock_get.return_value = expected_manifest
        
        response = client.get("/v1/plugins/yolo-tracker/manifest")
        
        assert response.status_code == 200
        manifest = response.json()
        
        # Verify schema
        assert "id" in manifest
        assert "tools" in manifest
        assert "player_detection" in manifest["tools"]
        
        tool = manifest["tools"]["player_detection"]
        assert "description" in tool
        assert "inputs" in tool
        assert "outputs" in tool
```

**Run tests:**
```bash
cd forgesyte/server
uv run pytest tests/api/test_plugins_manifest.py -v
```

---

## Integration Test: GPU (Optional)

**Location:** `forgesyte/server/tests/integration/test_video_manifest.py`

```python
"""Integration tests for manifest endpoint with real plugins."""

import os
import pytest

RUN_MODEL_TESTS = os.getenv("RUN_MODEL_TESTS", "0") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_MODEL_TESTS,
    reason="Requires YOLO model (set RUN_MODEL_TESTS=1)"
)


@pytest.mark.asyncio
async def test_manifest_for_yolo_tracker(client):
    """Test retrieving real YOLO tracker manifest."""
    response = client.get("/v1/plugins/forgesyte-yolo-tracker/manifest")
    
    assert response.status_code == 200
    manifest = response.json()
    
    # Check expected tools are present
    expected_tools = [
        "player_detection",
        "player_tracking",
        "ball_detection",
        "pitch_detection",
        "radar"
    ]
    
    for tool_name in expected_tools:
        assert tool_name in manifest["tools"]
        tool = manifest["tools"][tool_name]
        assert "inputs" in tool
        assert "outputs" in tool
        assert "frame_base64" in tool["inputs"]
```

**Run (on Kaggle GPU):**
```bash
cd forgesyte/server
RUN_MODEL_TESTS=1 uv run pytest tests/integration/test_video_manifest.py -v
```

---

## How to Verify

1. **Run unit tests (CPU, fast):**
   ```bash
   uv run pytest tests/api/test_plugins_manifest.py -v
   ```

2. **Test manually (if server is running):**
   ```bash
   curl http://localhost:8000/v1/plugins/forgesyte-yolo-tracker/manifest | jq .
   ```

3. **Check output format:**
   - Has `id`, `name`, `version`, `description`
   - Has `tools` dict with tool names
   - Each tool has `inputs`, `outputs`, `description`

---

## Dependencies

- `json` (built-in)
- `pathlib` (built-in)
- Existing: `HTTPException`, `logger`

---

## Related Files

- [BACKEND_CACHE_SERVICE.md](./BACKEND_CACHE_SERVICE.md) — Cache manifest for performance
- [BACKEND_RUN_ENDPOINT.md](./BACKEND_RUN_ENDPOINT.md) — Execute tools from manifest
- [COMPONENT_TOOL_SELECTOR.md](./COMPONENT_TOOL_SELECTOR.md) — Web-UI uses manifest
