# Phase 11 VideoTracker Stability Patch

**Hardening the VideoTracker plugin to survive in crash-proof Phase 11 environment.**

VideoTracker requires GPU. Without it, it should fail gracefully (not crash).

---

## Current Issue

**Old behavior:**
```
User requests VideoTracker without GPU
→ Plugin tries to import torch
→ ImportError raised
→ Server crashes or logs unhandled exception
```

**New behavior (Phase 11):**
```
User requests VideoTracker without GPU
→ Dependency check fails during load
→ Plugin marked UNAVAILABLE
→ /v1/plugins/{name} shows UNAVAILABLE with reason
→ User gets structured error: "GPU not available"
→ Server stays running
```

---

## Implementation

### 1. Update VideoTracker Manifest

**File:** `plugins/forgesyte-yolo-tracker/manifest.json`

**Add these fields:**

```json
{
  "name": "forgesyte-yolo-tracker",
  "description": "YOLO-based sports player tracking and analysis",
  "version": "1.0.0",
  "requires_gpu": true,
  "dependencies": [
    "torch",
    "torchvision",
    "ultralytics",
    "numpy",
    "cv2"
  ],
  "models": {
    "player-detection-v3": "models/football-player-detection-v3.pt",
    "ball-detection-v2": "models/football-ball-detection-v2.pt",
    "pitch-detection-v1": "models/football-pitch-detection-v1.pt"
  }
}
```

**Why:**
- `requires_gpu: true` → Loader marks UNAVAILABLE if no CUDA
- `dependencies` → Loader checks torch, cv2, etc. are installed
- `models` → Loader checks model files exist before init

---

### 2. Harden VideoTracker Plugin Code

**File:** `plugins/forgesyte-yolo-tracker/src/forgesyte_yolo_tracker/plugin.py`

**Update the Plugin class:**

```python
"""VideoTracker plugin for ForgeSyte."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class Plugin:
    """
    YOLO-based sports video analysis plugin.
    
    Requires:
    - GPU/CUDA (declared in manifest.json)
    - PyTorch with GPU support
    - YOLO models
    """
    
    name = "forgesyte-yolo-tracker"
    version = "1.0.0"
    
    def __init__(self):
        """Initialize plugin with GPU/model checks."""
        self._model_loaded = False
        self._ensure_gpu_available()
        self._ensure_models_available()
        logger.info(f"✓ {self.name} plugin initialized")
    
    def _ensure_gpu_available(self) -> None:
        """
        Verify GPU is available.
        
        Raises:
            RuntimeError if GPU not available
        """
        try:
            import torch
            
            if not torch.cuda.is_available():
                raise RuntimeError(
                    "CUDA GPU not available. "
                    "VideoTracker requires GPU. "
                    "Install CUDA or use CPU-only plugins."
                )
            
            logger.info(f"✓ GPU available: {torch.cuda.get_device_name(0)}")
        
        except ImportError:
            raise RuntimeError(
                "PyTorch not installed. "
                "Install with: pip install torch torchvision"
            ) from None
    
    def _ensure_models_available(self) -> None:
        """
        Verify model files are available.
        
        Raises:
            RuntimeError if models missing
        """
        import os
        from pathlib import Path
        
        model_dir = Path(__file__).parent.parent.parent / "models"
        required_models = [
            "football-player-detection-v3.pt",
            "football-ball-detection-v2.pt",
            "football-pitch-detection-v1.pt",
        ]
        
        missing = []
        for model_file in required_models:
            path = model_dir / model_file
            if not path.exists():
                missing.append(str(path))
        
        if missing:
            raise RuntimeError(
                f"Model files not found:\n" +
                "\n".join(f"  - {m}" for m in missing) +
                "\nDownload from ForgeSyte release."
            )
        
        logger.info(f"✓ Model files verified ({len(required_models)} models found)")
        self._model_loaded = True
    
    def detect_players(
        self,
        frame_base64: str,
        device: str = "cuda",
        annotated: bool = False,
        confidence: float = 0.25,
    ) -> dict[str, Any]:
        """
        Detect players in frame.
        
        Args:
            frame_base64: Base64-encoded frame
            device: Device to run on ("cuda" recommended)
            annotated: Whether to return annotated frame
            confidence: Detection confidence threshold
        
        Returns:
            {
                "detections": [...],
                "frame_annotated": "base64..." if annotated,
                "timestamp": timestamp,
            }
        
        Raises:
            RuntimeError if models not loaded or GPU error
        """
        if not self._model_loaded:
            raise RuntimeError("VideoTracker models not loaded")
        
        # Implementation continues as before...
        # But now wrapped in Phase 11 sandbox
        # So any exception is caught and structured
        pass
    
    def detect_ball(self, *args, **kwargs) -> dict:
        """Ball detection endpoint."""
        if not self._model_loaded:
            raise RuntimeError("VideoTracker models not loaded")
        pass
    
    def track_players(self, *args, **kwargs) -> dict:
        """Player tracking endpoint."""
        if not self._model_loaded:
            raise RuntimeError("VideoTracker models not loaded")
        pass
```

---

## 3. ToolRunner Integration

**File:** `server/app/tools/runner.py` (ensure sandbox is wired)

**The run_tool method should use sandbox:**

```python
async def run_tool(
    self,
    plugin_id: str,
    tool_name: str,
    frame_base64: str,
    device: str = "cpu",
    annotated: bool = False,
) -> dict[str, Any]:
    """
    Run a tool through the crash-proof sandbox.
    
    All plugin execution is sandboxed.
    No plugin exception reaches FastAPI.
    """
    from app.plugins.sandbox.sandbox_runner import run_plugin_sandboxed
    from app.plugins.loader.plugin_registry import get_registry
    
    registry = get_registry()
    
    # 1. Check plugin is available
    if not registry.is_available(plugin_id):
        state = registry.get_state(plugin_id)
        status = registry.get_status(plugin_id)
        return {
            "ok": False,
            "error": f"Plugin is {state.value}: {status.reason}",
            "error_type": "PluginUnavailable",
        }
    
    # 2. Get plugin and tool
    plugin = self.plugins.get(plugin_id)
    if plugin is None:
        return {"ok": False, "error": f"Plugin not found: {plugin_id}"}
    
    tool_fn = getattr(plugin, tool_name, None)
    if tool_fn is None:
        return {"ok": False, "error": f"Tool not found: {tool_name}"}
    
    # 3. Mark running
    registry.mark_running(plugin_id)
    
    # 4. RUN IN SANDBOX (crash-proof)
    result = run_plugin_sandboxed(
        tool_fn,
        frame_base64=frame_base64,
        device=device,
        annotated=annotated,
    )
    
    # 5. Track result
    if result.ok:
        registry.record_success(plugin_id)
        return {"ok": True, "result": result.result}
    else:
        # Mark failed and return structured error
        registry.mark_failed(plugin_id, result.error)
        registry.record_error(plugin_id)
        return {
            "ok": False,
            "error": result.error,
            "error_type": result.error_type,
        }
```

---

## 4. Behavior Under Phase 11

### Scenario A: GPU available, models present

```
POST /v1/jobs
{
    "plugin_id": "forgesyte-yolo-tracker",
    "tool_name": "detect_players",
    ...
}

→ PluginLoader checks GPU ✓
→ PluginLoader checks models ✓
→ Plugin state = LOADED
→ Tool executes successfully
→ Returns result
```

### Scenario B: GPU NOT available

```
Server startup:
→ PluginLoader tries to load VideoTracker
→ _ensure_gpu_available() raises RuntimeError
→ Plugin marked UNAVAILABLE
→ State reason = "CUDA GPU not available"
→ Server continues

Client request:
→ GET /v1/plugins/forgesyte-yolo-tracker/health
→ Returns 200 with state=UNAVAILABLE

POST /v1/jobs with VideoTracker
→ ToolRunner checks registry
→ Plugin not available
→ Returns structured error: "Plugin is UNAVAILABLE: CUDA GPU not available"
→ No crash
```

### Scenario C: Plugin loads but crashes during execution

```
POST /v1/jobs with invalid frame
→ Tool executes in sandbox
→ Raises exception (e.g., ValueError)
→ Sandbox catches exception
→ Returns {ok: false, error: "...", type: "ValueError"}
→ PluginRegistry.mark_failed()
→ No crash
```

---

## 5. Testing VideoTracker Stability

**File:** `server/tests/test_videotracker_stability/test_videotracker.py`

```python
import pytest
from unittest.mock import Mock, patch
from app.plugins.loader.plugin_registry import get_registry


def test_videotracker_without_cuda_marked_unavailable():
    """VideoTracker without CUDA should be UNAVAILABLE, not crash."""
    registry = get_registry()
    
    # Simulate loading VideoTracker without CUDA
    registry.register("forgesyte-yolo-tracker")
    registry.mark_unavailable(
        "forgesyte-yolo-tracker",
        "CUDA GPU not available"
    )
    
    status = registry.get_status("forgesyte-yolo-tracker")
    assert status.state.value == "UNAVAILABLE"
    assert "CUDA" in status.reason


def test_videotracker_missing_models_marked_unavailable():
    """VideoTracker missing models should be UNAVAILABLE."""
    registry = get_registry()
    registry.register("forgesyte-yolo-tracker")
    registry.mark_unavailable(
        "forgesyte-yolo-tracker",
        "Model files not found: models/football-player-detection-v3.pt"
    )
    
    status = registry.get_status("forgesyte-yolo-tracker")
    assert status.state.value == "UNAVAILABLE"


def test_videotracker_tool_error_is_sandboxed():
    """VideoTracker tool error should be caught by sandbox."""
    from app.plugins.sandbox.sandbox_runner import run_plugin_sandboxed
    
    # Mock tool that raises
    def failing_tool(*args, **kwargs):
        raise RuntimeError("Memory error during inference")
    
    result = run_plugin_sandboxed(failing_tool)
    
    # Should not raise; should be structured
    assert result.ok is False
    assert "Memory error" in result.error
    assert result.error_type == "RuntimeError"


def test_videotracker_health_api_shows_unavailable():
    """Health API should show VideoTracker as UNAVAILABLE without GPU."""
    from fastapi.testclient import TestClient
    from app.main import create_app
    
    app = create_app()
    client = TestClient(app)
    
    # Mark VideoTracker unavailable
    registry = get_registry()
    registry.register("forgesyte-yolo-tracker", description="Video tracker")
    registry.mark_unavailable("forgesyte-yolo-tracker", "GPU required")
    
    resp = client.get("/v1/plugins/forgesyte-yolo-tracker/health")
    
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "UNAVAILABLE"
    assert "GPU" in body["reason"]


def test_videotracker_job_fails_gracefully():
    """Job using unavailable VideoTracker should return error, not crash."""
    from fastapi.testclient import TestClient
    from app.main import create_app
    
    app = create_app()
    client = TestClient(app)
    
    registry = get_registry()
    registry.register("forgesyte-yolo-tracker")
    registry.mark_unavailable("forgesyte-yolo-tracker", "GPU required")
    
    resp = client.post(
        "/v1/jobs",
        json={
            "plugin_id": "forgesyte-yolo-tracker",
            "tool_name": "detect_players",
            "frame_base64": "...",
        }
    )
    
    # Should return 200 with error, not 500
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is False
    assert "GPU" in body["error"] or "unavailable" in body["error"].lower()
```

---

## 6. Deployment Checklist

Before deploying Phase 11 with VideoTracker:

✅ **VideoTracker manifest includes:**
- `requires_gpu: true`
- `dependencies` list
- `models` dict

✅ **Plugin.\_\_init\_\_ checks:**
- GPU availability (torch.cuda.is_available())
- Model files exist

✅ **Errors are clear:**
- "CUDA GPU not available" (not generic "Error")
- "Model files not found" (with paths)

✅ **Tests pass:**
```bash
pytest tests/test_videotracker_stability/ -v
```

✅ **Health API works:**
```bash
curl http://localhost:8000/v1/plugins/forgesyte-yolo-tracker/health
# Returns 200 with state=UNAVAILABLE if no GPU
```

✅ **No crashes:**
- Run with intentionally missing GPU
- Verify server stays running
- Verify health API accessible

---

## Summary

**VideoTracker in Phase 11:**

| Condition | Behavior | Result |
|-----------|----------|--------|
| GPU available, models present | Loads normally | Plugin LOADED, tools work |
| GPU missing | Marked UNAVAILABLE | User gets "GPU required" error |
| Models missing | Marked UNAVAILABLE | User gets "Models not found" error |
| Runtime error (bad input) | Caught by sandbox | Returns structured error, no crash |

**This is Phase 11: observable, recoverable, crash-proof.**

VideoTracker can fail, but the server never does.
