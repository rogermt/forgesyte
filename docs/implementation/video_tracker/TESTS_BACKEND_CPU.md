# Backend Tests: CPU-Only (Fast)

**Files:** 
- `forgesyte/server/tests/api/test_plugins_manifest.py`
- `forgesyte/server/tests/api/test_plugins_run.py`
- `forgesyte/server/tests/services/test_manifest_cache_service.py`

**Purpose:** Test all backend endpoints without GPU/models  
**Speed:** <5 seconds total  
**Status:** Ready to implement  

---

## Overview

All tests use **mocked plugins** (no YOLO models). Focus on:
- Endpoint routing (200, 404, 400)
- Request/response validation
- Error handling
- Cache behavior

---

## Test Files

### 1. test_plugins_manifest.py (GET /plugins/{id}/manifest)

**Location:** `forgesyte/server/tests/api/test_plugins_manifest.py` (NEW)

```python
"""Tests for GET /plugins/{id}/manifest endpoint."""

import json
import pytest
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_manifest_service():
    """Mock the plugin management service."""
    with patch('app.services.plugin_management_service.PluginManagementService') as mock:
        yield mock.return_value


class TestGetPluginManifest:
    """Tests for manifest endpoint."""

    async def test_get_manifest_success(self, client):
        """Test successfully retrieving manifest."""
        expected = {
            "id": "test-plugin",
            "name": "Test Plugin",
            "version": "1.0.0",
            "tools": {
                "detect": {
                    "description": "Detect",
                    "inputs": {"frame_base64": "string"},
                    "outputs": {"detections": "array"}
                }
            }
        }
        
        with patch('app.services.plugin_management_service.PluginManagementService.get_plugin_manifest') as mock_get:
            mock_get.return_value = expected
            
            response = client.get("/v1/plugins/test-plugin/manifest")
            
            assert response.status_code == 200
            assert response.json() == expected

    async def test_get_manifest_not_found(self, client):
        """Test 404 when plugin doesn't exist."""
        with patch('app.services.plugin_management_service.PluginManagementService.get_plugin_manifest') as mock_get:
            mock_get.return_value = None
            
            response = client.get("/v1/plugins/nonexistent/manifest")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    async def test_get_manifest_schema_validation(self, client):
        """Test manifest has required fields."""
        manifest = {
            "id": "yolo-tracker",
            "name": "YOLO Tracker",
            "version": "1.0.0",
            "tools": {
                "player_detection": {
                    "description": "Detect players",
                    "inputs": {"frame_base64": "string"},
                    "outputs": {"detections": "array"}
                }
            }
        }
        
        with patch('app.services.plugin_management_service.PluginManagementService.get_plugin_manifest') as mock_get:
            mock_get.return_value = manifest
            
            response = client.get("/v1/plugins/yolo-tracker/manifest")
            
            assert response.status_code == 200
            result = response.json()
            
            # Verify schema
            assert "id" in result
            assert "tools" in result
            assert "player_detection" in result["tools"]
            
            tool = result["tools"]["player_detection"]
            assert "inputs" in tool
            assert "outputs" in tool
```

### 2. test_plugins_run.py (POST /plugins/{id}/tools/{tool}/run)

**Location:** `forgesyte/server/tests/api/test_plugins_run.py` (NEW)

```python
"""Tests for POST /plugins/{id}/tools/{tool}/run endpoint."""

import pytest
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.asyncio


class TestRunPluginTool:
    """Tests for tool execution endpoint."""

    async def test_run_tool_success(self, client):
        """Test successfully running a tool."""
        expected_result = {
            "detections": [
                {"x1": 100, "y1": 200, "x2": 150, "y2": 350, "confidence": 0.92}
            ]
        }
        
        with patch('app.services.plugin_management_service.PluginManagementService.run_plugin_tool') as mock_run:
            mock_run.return_value = expected_result
            
            response = client.post(
                "/v1/plugins/test-plugin/tools/detect/run",
                json={"args": {"frame_base64": "test_data", "device": "cpu"}}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            assert result["tool_name"] == "detect"
            assert result["plugin_id"] == "test-plugin"
            assert result["result"] == expected_result
            assert "processing_time_ms" in result

    async def test_run_tool_plugin_not_found(self, client):
        """Test 400 when plugin not found."""
        with patch('app.services.plugin_management_service.PluginManagementService.run_plugin_tool') as mock_run:
            mock_run.side_effect = ValueError("Plugin 'nonexistent' not found")
            
            response = client.post(
                "/v1/plugins/nonexistent/tools/detect/run",
                json={"args": {"frame_base64": "test"}}
            )
            
            assert response.status_code == 400

    async def test_run_tool_tool_not_found(self, client):
        """Test 400 when tool not found."""
        with patch('app.services.plugin_management_service.PluginManagementService.run_plugin_tool') as mock_run:
            mock_run.side_effect = ValueError("Tool 'nonexistent' not found")
            
            response = client.post(
                "/v1/plugins/test-plugin/tools/nonexistent/run",
                json={"args": {"frame_base64": "test"}}
            )
            
            assert response.status_code == 400

    async def test_run_tool_invalid_args(self, client):
        """Test 400 with invalid arguments."""
        with patch('app.services.plugin_management_service.PluginManagementService.run_plugin_tool') as mock_run:
            mock_run.side_effect = TypeError("Missing required argument: frame_base64")
            
            response = client.post(
                "/v1/plugins/test-plugin/tools/detect/run",
                json={"args": {"invalid": "args"}}
            )
            
            assert response.status_code == 400

    async def test_run_tool_timeout(self, client):
        """Test 408 when tool times out."""
        with patch('app.services.plugin_management_service.PluginManagementService.run_plugin_tool') as mock_run:
            mock_run.side_effect = TimeoutError("Tool execution exceeded timeout")
            
            response = client.post(
                "/v1/plugins/test-plugin/tools/detect/run",
                json={"args": {"frame_base64": "test"}}
            )
            
            assert response.status_code == 408

    async def test_run_tool_response_schema(self, client):
        """Test response follows expected schema."""
        expected_result = {"detections": [], "track_ids": []}
        
        with patch('app.services.plugin_management_service.PluginManagementService.run_plugin_tool') as mock_run:
            mock_run.return_value = expected_result
            
            response = client.post(
                "/v1/plugins/yolo-tracker/tools/player_tracking/run",
                json={"args": {"frame_base64": "test", "device": "cpu"}}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # Verify response schema
            assert result["tool_name"] == "player_tracking"
            assert result["plugin_id"] == "yolo-tracker"
            assert isinstance(result["result"], dict)
            assert isinstance(result["processing_time_ms"], int)
            assert result["processing_time_ms"] >= 0
```

### 3. test_manifest_cache_service.py

See [BACKEND_CACHE_SERVICE.md](./BACKEND_CACHE_SERVICE.md) for full test file.

---

## Running Tests

**Run all backend CPU tests:**
```bash
cd forgesyte/server

# Run just CPU tests
uv run pytest tests/api/test_plugins_manifest.py tests/api/test_plugins_run.py -v

# Or run with coverage
uv run pytest tests/api/test_plugins*.py --cov=app --cov-report=term-missing
```

**Expected output:**
```
tests/api/test_plugins_manifest.py::TestGetPluginManifest::test_get_manifest_success PASSED
tests/api/test_plugins_manifest.py::TestGetPluginManifest::test_get_manifest_not_found PASSED
tests/api/test_plugins_run.py::TestRunPluginTool::test_run_tool_success PASSED
...
======================== 12 passed in 2.34s ========================
```

---

## What These Tests Cover

✅ Endpoint routing (200, 400, 404, 408, 500)  
✅ Request validation (required fields, types)  
✅ Response schema (correct structure, types)  
✅ Error messages (clear, actionable)  
✅ Mocked plugin execution (no GPU)  
✅ Cache behavior (hit, miss, expire)  

❌ Not covered (GPU tests):
- Real YOLO model execution
- Actual frame processing
- Real plugin loading

---

## Related Files

- [BACKEND_MANIFEST_ENDPOINT.md](./BACKEND_MANIFEST_ENDPOINT.md) — Endpoint code
- [BACKEND_RUN_ENDPOINT.md](./BACKEND_RUN_ENDPOINT.md) — Endpoint code
- [BACKEND_CACHE_SERVICE.md](./BACKEND_CACHE_SERVICE.md) — Cache implementation
- [TESTS_BACKEND_GPU.md](./TESTS_BACKEND_GPU.md) — GPU integration tests
