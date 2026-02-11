# PHASE 13 — PLANS (TDD MANDATORY)
**VideoTracker Multi-Tool Linear Pipelines (Single-Plugin)**

## TDD WORKFLOW (REQUIRED - NOT OPTIONAL)

For EVERY commit:
1. ✅ **WRITE TEST FIRST** - Test must FAIL (red)
2. ✅ **RUN TEST** - Verify it fails
3. ✅ **IMPLEMENT CODE** - Make test pass (green)
4. ✅ **RUN TEST** - Verify it passes
5. ✅ **RUN PRE-COMMIT** - All checks pass
6. ✅ **COMMIT** - With passing tests

**NO EXCEPTIONS. NO SHORTCUTS. TESTS FIRST.**

---

## Phase Overview
Phase 13 introduces **linear multi-tool pipelines** for VideoTracker:
- Execute ordered sequences of tools inside a single plugin
- `[ detect_players → track_players → annotate_frames ]`
- Applies to both REST (background jobs) and WebSocket (streaming)
- **No cross-plugin pipelines** - all tools must belong to the same plugin

---

## 5 Key Decisions (Canonical Answers from PHASE_13_NOTES_04.md)

| Question | Final Answer |
|---------|--------------|
| WS frame uses `tools[]` instead of `tool`? | ✅ **YES — mandatory** |
| Inject VideoPipelineService? | ✅ **YES — inject in `__init__`** |
| `selectedTool` → `selectedTools[]`? | ✅ **YES — required** |
| Remove fallback logic? | ✅ **YES for Phase 13 paths** |
| REST endpoint location? | ✅ **Create `routes_pipeline.py`** |

---

## 10 Implementation Questions Answered (from PHASE_13_NOTES_05.md)

| # | Question | Canonical Answer |
|---|----------|-----------------|
| Q1 | Pydantic imports | `from pydantic import BaseModel` (v1) |
| Q1 | Use Field()? | **No** |
| Q2 | Router registration | New `routes_pipeline.py`, `init_pipeline_routes()` |
| Q2 | Use Depends()? | **No** - use constructor injection |
| Q3 | `selectedTool` → `selectedTools[]`? | **Yes** - required |
| Q4 | Remove FALLBACK_TOOL? | **Yes** - from Phase 13 paths |
| Q5 | REST endpoint location | New file: `server/app/routes_pipeline.py` |
| Q6 | `run_pipeline()` async? | **No** - keep sync (`def`) |
| Q7 | useVideoProcessor uses WS? | **Yes** - send WS frames with `tools[]` |
| Q8 | Test location | `server/tests/test_phase13_pipeline.py` |
| Q8 | Test framework | **pytest** |
| Q8 | Mocking | `FakeRegistry` stub class |
| Q9 | Python import paths | `from ..services.video_pipeline_service import VideoPipelineService` |
| Q9 | TypeScript import paths | `import { useVideoProcessor } from "../hooks/useVideoProcessor"` |

---

## Implementation Order (10 Commits) - TDD MANDATORY

### COMMIT 1: VideoPipelineService Skeleton (TDD)
**TDD Steps:**
1. [ ] Write test: `server/tests/test_video_pipeline_service.py`
2. [ ] Run test → FAIL (class doesn't exist)
3. [ ] Create: `server/app/services/video_pipeline_service.py` with stubs
4. [ ] Run test → PASS
5. [ ] Run pre-commit checks
6. [ ] Commit

**Test File Pattern:**
```python
# server/tests/test_video_pipeline_service.py
import pytest
from app.services.video_pipeline_service import VideoPipelineService

def test_import():
    """Test service can be imported."""
    assert VideoPipelineService is not None

def test_instantiation():
    """Test service can be instantiated with FakeRegistry."""
    from tests.helpers import FakeRegistry
    registry = FakeRegistry(plugin=None)
    service = VideoPipelineService(plugins=registry)
    assert service is not None

def test_run_pipeline_method_exists():
    """Test run_pipeline method exists."""
    from tests.helpers import FakeRegistry
    registry = FakeRegistry(plugin=None)
    service = VideoPipelineService(plugins=registry)
    assert hasattr(service, 'run_pipeline')
    assert callable(service.run_pipeline)

def test_validate_method_exists():
    """Test _validate method exists."""
    from tests.helpers import FakeRegistry
    registry = FakeRegistry(plugin=None)
    service = VideoPipelineService(plugins=registry)
    assert hasattr(service, '_validate')
    assert callable(service._validate)
```

**Implementation:**
```python
# server/app/services/video_pipeline_service.py
import logging
from typing import Any, Dict, List

from ..protocols import PluginRegistry

logger = logging.getLogger(__name__)


class VideoPipelineService:
    """Executes linear multi-tool pipelines for VideoTracker."""

    def __init__(self, plugins: PluginRegistry) -> None:
        """Initialize with plugin registry.
        
        Args:
            plugins: PluginRegistry instance
        """
        self.plugins = plugins

    def run_pipeline(
        self,
        plugin_id: str,
        tools: List[str],
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tools sequentially, chaining outputs.
        
        Args:
            plugin_id: Plugin identifier
            tools: List of tool names to execute in order
            payload: Initial payload dict
            
        Returns:
            Final result dict from last tool
        """
        # TODO: Implement in Commit 7
        pass

    def _validate(self, plugin_id: str, tools: List[str]) -> None:
        """Validate plugin_id and tools[] exist.
        
        Args:
            plugin_id: Plugin identifier
            tools: List of tool names
            
        Raises:
            ValueError: If validation fails
        """
        # TODO: Implement in Commit 4
        pass
```

---

### COMMIT 2: Patch VisionAnalysisService (WebSocket) (TDD)
**TDD Steps:**
1. [ ] Write test: `server/tests/test_vision_analysis_pipeline.py`
2. [ ] Run test → FAIL
3. [ ] Modify: `server/app/services/vision_analysis.py`
4. [ ] Run test → PASS
5. [ ] Run pre-commit checks
6. [ ] Commit

**Test File Pattern:**
```python
# server/tests/test_vision_analysis_pipeline.py
import pytest
from unittest.mock import MagicMock
from app.services.vision_analysis import VisionAnalysisService
from tests.helpers import FakeRegistry, FakePlugin

def test_ws_frame_with_tools_executes_pipeline():
    """Test WS frame with tools[] executes pipeline."""
    # Arrange
    fake_plugin = FakePlugin()
    registry = FakeRegistry(plugin=fake_plugin)
    ws_manager = MagicMock()
    
    service = VisionAnalysisService(plugins=registry, ws_manager=ws_manager)
    
    frame_data = {
        "image_data": "base64encodeddata",
        "tools": ["detect_players", "track_players"],
        "frame_id": "test-frame-1"
    }
    
    # Act
    import asyncio
    asyncio.run(service.handle_frame("client-1", "test-plugin", frame_data))
    
    # Assert
    ws_manager.send_frame_result.assert_called_once()
    call_args = ws_manager.send_frame_result.call_args
    assert call_args[0][1] == "test-frame-1"  # frame_id

def test_ws_frame_missing_tools_returns_error():
    """Test WS frame without tools[] returns error."""
    # Arrange
    registry = FakeRegistry(plugin=None)
    ws_manager = MagicMock()
    
    service = VisionAnalysisService(plugins=registry, ws_manager=ws_manager)
    
    frame_data = {
        "image_data": "base64encodeddata",
        # Missing 'tools'
        "frame_id": "test-frame-1"
    }
    
    # Act
    import asyncio
    asyncio.run(service.handle_frame("client-1", "test-plugin", frame_data))
    
    # Assert
    ws_manager.send_personal.assert_called_once()
    error_call = ws_manager.send_personal.call_args[0][1]
    assert error_call["type"] == "error"
    assert "tools" in error_call["message"]
```

---

### COMMIT 3: REST Pipeline Endpoint (TDD)
**TDD Steps:**
1. [ ] Write test: `server/tests/test_pipeline_rest.py`
2. [ ] Run test → FAIL
3. [ ] Create: `server/app/schemas/pipeline.py`
4. [ ] Create: `server/app/routes_pipeline.py`
5. [ ] Run test → PASS
6. [ ] Run pre-commit checks
7. [ ] Commit

**Test File Pattern:**
```python
# server/tests/test_pipeline_rest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.helpers import FakeRegistry, FakePlugin

def test_post_video_pipeline():
    """Test POST /video/pipeline executes pipeline."""
    # Arrange
    fake_plugin = FakePlugin()
    registry = FakeRegistry(plugin=fake_plugin)
    
    # Override plugin registry
    from app.main import plugin_registry
    original_get = plugin_registry.get
    plugin_registry.get = lambda name: fake_plugin
    
    client = TestClient(app)
```json
{
  "type": "frame",
  "frame_id": "abc123",
  "image_data": "<base64>",
  "plugin_id": "forgesyte-yolo-tracker",
  "tools": ["detect_players", "track_players"]
}
```

### REST Response
```json
{
  "result": { <final tool output> }
}
```

### Tool Chaining Algorithm
```python
result = payload
for idx, tool_name in enumerate(tools):
    result = plugin.run_tool(tool_name, result)
    logger.info(f"step={idx} tool={tool_name}")
return result
```

### VideoPipelineService Signature
```python
from typing import Any, Dict, List
from ..protocols import PluginRegistry

class VideoPipelineService:
    def __init__(self, plugins: PluginRegistry) -> None:
        self.plugins = plugins
    
    def run_pipeline(
        self,
        plugin_id: str,
        tools: List[str],
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tools sequentially, chaining outputs."""
        ...
    
    def _validate(self, plugin_id: str, tools: List[str]) -> None:
        """Validate plugin_id and tools[] exist."""
        ...
```

### Validation Errors (raise `ValueError`)
- Missing `plugin_id`
- Missing `tools[]`
- Empty `tools[]`
- Plugin not found
- Tool not found in plugin manifest

### Plugin Interface
```python
class BasePlugin:
    name: str
    tools: Dict[str, Dict]
    
    def run_tool(self, tool_name: str, args: Dict) -> Dict:
        """Execute a tool and return result dict."""
        ...
```

### Error Handling
- **Validation errors**: Raise `ValueError` (REST returns 422, WS sends error frame)
- **Tool execution errors**: Let exceptions bubble up (WS sends error frame, REST returns 500)
- **Fail-fast**: If tool N fails, tool N+1 is NOT executed

### FakeRegistry Test Mock
```python
class FakeRegistry:
    def __init__(self, plugin):
        self.plugin = plugin
    
    def get(self, plugin_id):
        return self.plugin
    
    def list(self):
        return {plugin_id: {"name": self.plugin.name, "tools": self.plugin.tools}}
```

---

## Architecture

```
[VideoTracker UI]
      |
      v
[useVideoProcessor hook]  ← Replace toolName with tools[]
      |
      v
[WebSocket JSON frame]  ← {type, frame_id, image_data, plugin_id, tools: []}
      |
      v
[VisionAnalysisService]  ← Inject VideoPipelineService in __init__
      |
      v
[VideoPipelineService.run_pipeline]  ← Execute tools sequentially (sync)
      |
      v
[Plugin.run_tool(tool_name, payload)]  ← Each tool returns dict
      |
      v
[Final dict result]
      |
      v
```
POST /video/pipeline
{
  "plugin_id": "...",
  "tools": ["detect_players", "track_players"],
  "payload": {"image_bytes": "..."}
}
