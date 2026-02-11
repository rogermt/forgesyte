# PHASE 13 — PROGRESS
**VideoTracker Multi-Tool Linear Pipelines (Single-Plugin)**

## TDD WORKFLOW (MANDATORY)

For EVERY commit:
1. ✅ **WRITE TEST FIRST** - Test must FAIL (red)
2. ✅ **RUN TEST** - Verify it fails
3. ✅ **IMPLEMENT CODE** - Make test pass (green)
4. ✅ **RUN TEST** - Verify it passes
5. ✅ **RUN PRE-COMMIT** - All checks pass
6. ✅ **COMMIT** - With passing tests

**NO EXCEPTIONS. NO SHORTCUTS. TESTS FIRST.**

---

## Overall Status: NOT STARTED

## 5 Key Decisions (Canonical Answers)
| Question | Answer |
|---------|--------|
| WS frame uses `tools[]`? | ✅ YES - mandatory |
| Inject VideoPipelineService? | ✅ YES - inject in `__init__` |
| `selectedTool` → `selectedTools[]`? | ✅ YES - required |
| Remove fallback logic? | ✅ YES for Phase 13 paths |
| REST endpoint location? | ✅ YES - `routes_pipeline.py` |

---

## 10-Commit Implementation Order (TDD)

| # | Status | Commit | TDD Status |
|---|--------|--------|------------|
| 1 | ⬜ | VideoPipelineService Skeleton | Test written → Implement |
| 2 | ⬜ | Patch VisionAnalysisService (WS) | Test written → Implement |
| 3 | ⬜ | REST Pipeline Endpoint | Test written → Implement |
| 4 | ⬜ | Update useVideoProcessor Hook | Test written → Implement |
| 5 | ⬜ | Patch VideoTracker Component | Test written → Implement |
| 6 | ⬜ | UI Tool Selector | Test written → Implement |
| 7 | ⬜ | Add Pipeline Logging | Test written → Implement |
| 8 | ⬜ | Add Regression Test Suite | Test written → Implement |
| 9 | ⬜ | Add Plugin Validation Tools | Test written → Implement |
| 10 | ⬜ | Remove Fallback Logic | Test written → Implement |

---

## Current State

### ✅ Files That Exist
| File | Status |
|------|--------|
| `server/app/services/vision_analysis.py` | Class: `VisionAnalysisService(plugins, ws_manager)` |
| `server/app/plugin_loader.py` | Class: `PluginRegistry` with `get()`, `list()` |
| `web-ui/src/hooks/useVideoProcessor.ts` | Params: `videoRef, pluginId, toolName, fps, device, enabled` |
| `web-ui/src/App.tsx` | Uses: `<VideoTracker pluginId={selectedPlugin} toolName={selectedTool} />` |
| `server/tests/helpers.py` | EXISTS - Check contents |

### ❌ Files to Create (Commit 1)
| File | Purpose |
|------|---------|
| `server/app/services/video_pipeline_service.py` | Pipeline executor service |
| `server/app/schemas/pipeline.py` | PipelineRequest model |
| `server/app/routes_pipeline.py` | REST endpoint `POST /video/pipeline` |
| `server/tests/test_video_pipeline_service.py` | Service unit tests |

---

## Progress by Commit (TDD)

### COMMIT 1: VideoPipelineService Skeleton
**Status:** NOT STARTED

**TDD Steps:**
1. [ ] Write test: `server/tests/test_video_pipeline_service.py`
2. [ ] Run test → FAIL (class doesn't exist)
3. [ ] Create: `server/app/services/video_pipeline_service.py` with stubs
4. [ ] Run test → PASS
5. [ ] Pre-commit checks:
   - [ ] Server tests pass
   - [ ] Black lint pass
   - [ ] Ruff lint pass
   - [ ] MyPy pass
6. [ ] Commit: `"feat(phase13): add VideoPipelineService skeleton"`

**Test Content:**
```python
# server/tests/test_video_pipeline_service.py
import pytest
from app.services.video_pipeline_service import VideoPipelineService

def test_import():
    """Test service can be imported."""
    assert VideoPipelineService is not None

def test_instantiation():
    """Test service can be instantiated."""
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
        self.plugins = plugins

    def run_pipeline(
        self,
        plugin_id: str,
        tools: List[str],
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tools sequentially, chaining outputs."""
        pass

    def _validate(self, plugin_id: str, tools: List[str]) -> None:
        """Validate plugin_id and tools[] exist."""
        pass
```

---

### COMMIT 2: Patch VisionAnalysisService (WebSocket)
**Status:** NOT STARTED

**TDD Steps:**
1. [ ] Write test: `server/tests/test_vision_analysis_pipeline.py`
2. [ ] Run test → FAIL
3. [ ] Modify: `server/app/services/vision_analysis.py`
4. [ ] Run test → PASS
5. [ ] Pre-commit checks
6. [ ] Commit

**Test Content:**
```python
# server/tests/test_vision_analysis_pipeline.py
import pytest
from unittest.mock import MagicMock
from app.services.vision_analysis import VisionAnalysisService
from tests.helpers import FakeRegistry, FakePlugin

def test_ws_frame_with_tools_executes_pipeline():
    """Test WS frame with tools[] executes pipeline."""
    fake_plugin = FakePlugin()
    registry = FakeRegistry(plugin=fake_plugin)
    ws_manager = MagicMock()
    
    service = VisionAnalysisService(plugins=registry, ws_manager=ws_manager)
    
    frame_data = {
        "image_data": "base64encodeddata",
        "tools": ["detect_players", "track_players"],
        "frame_id": "test-frame-1"
    }
    
    import asyncio
    asyncio.run(service.handle_frame("client-1", "test-plugin", frame_data))
    
---

### COMMIT 4: Update useVideoProcessor Hook
**Status:** NOT STARTED

**Tasks:**
- [ ] Create test: `web-ui/scripts/test_websocket_hook.py`
- [ ] Modify `web-ui/src/hooks/useVideoProcessor.ts`:
  - [ ] **REPLACE** param:
    ```typescript
    // OLD:
    toolName: string,
    
    // NEW:
    tools: string[],
    ```
  - [ ] **UPDATE** guard:
    ```typescript
    if (!pluginId || !tools || tools.length === 0) {
      console.error("Frame processing aborted: pluginId or tools missing", {...});
      return;
    }
    ```
  - [ ] **UPDATE** WS frame in `runTool()` call:
    ```typescript
    // Send tools[] instead of toolName
    ```
- [ ] Tests verify: hook sends `tools[]` in WS frames
- [ ] Run pre-commit checks (eslint, etc.)
- [ ] Commit

---

### COMMIT 5: Patch VideoTracker Component
**Status:** NOT STARTED

**Tasks:**
- [ ] Create test: `web-ui/scripts/test_components.py` (add VideoTracker tests)
- [ ] Modify `web-ui/src/components/VideoTracker.tsx`:
  - [ ] **REPLACE** interface:
    ```typescript
    // OLD:
    export interface VideoTrackerProps {
      pluginId: string;
      toolName: string;
    }
    
    // NEW:
    export interface VideoTrackerProps {
      pluginId: string;
      tools: string[];
    }
    ```
  - [ ] **REPLACE** props destructuring:
    ```typescript
    // OLD:
    export function VideoTracker({ pluginId, toolName }: VideoTrackerProps) {...}
    
    // NEW:
    export function VideoTracker({ pluginId, tools }: VideoTrackerProps) {...}
    ```
  - [ ] **UPDATE** header display:
    ```typescript
    // OLD:
    Plugin: <strong>{pluginId}</strong> | Tool: <strong>{toolName}</strong>
    
    // NEW:
    Plugin: <strong>{pluginId}</strong> | Tools: <strong>{tools.join(", ")}</strong>
    ```
  - [ ] **UPDATE** `useVideoProcessor` call:
    ```typescript
    // Pass tools[] instead of toolName
    ```
- [ ] Tests verify: props accepted, header displays tools
- [ ] Run pre-commit checks
- [ ] Commit

---

### COMMIT 6: (Optional) UI Tool Selector
**Status:** NOT STARTED (Optional)

**Tasks:**
- [ ] Create `web-ui/src/components/PipelineToolSelector.tsx`
- [ ] Modify `web-ui/src/App.tsx`:
  - [ ] **REPLACE** state:
    ```typescript
    // OLD:
    const [selectedTool, setSelectedTool] = useState<string>("");
    
    // NEW:
    const [selectedTools, setSelectedTools] = useState<string[]>([]);
    ```
  - [ ] **UPDATE** VideoTracker usage:
    ```typescript
    // OLD:
    <VideoTracker pluginId={selectedPlugin} toolName={selectedTool} />
    
    // NEW:
    <VideoTracker pluginId={selectedPlugin} tools={selectedTools} />
    ```
- [ ] Tests verify: selector works, state updates
- [ ] Run pre-commit checks
- [ ] Commit

---

### COMMIT 7: Add Pipeline Logging
**Status:** NOT STARTED

**Tasks:**
- [ ] Modify `VideoPipelineService.run_pipeline()`:
  ```python
  result = payload
  for idx, tool_name in enumerate(tools):
      logger.info(
          "Running pipeline step",
          extra={
              "step": idx,
              "tool": tool_name,
              "plugin_id": plugin_id,
              "args_keys": list(payload.keys()),
          }
      )
      result = plugin.run_tool(tool_name, result)
  return result
  ```
- [ ] Tests verify: logs contain correct information
- [ ] Run pre-commit checks
- [ ] Commit

---

### COMMIT 8: Add Regression Test Suite
**Status:** NOT STARTED

**Tasks:**
- [ ] Create `server/tests/test_pipeline_regression.py`:
  - [ ] Test: tools execute in order
  - [ ] Test: output of last tool is returned
  - [ ] Test: validation edge cases:
    - Missing plugin_id → ValueError
    - Missing tools[] → ValueError
    - Empty tools[] → ValueError
    - Plugin not found → ValueError
    - Tool not found → ValueError
  - [ ] Test: WS + REST integration
- [ ] Tests pass
- [ ] Run pre-commit checks
- [ ] Commit

---

### COMMIT 9: Add Plugin Validation Tools
**Status:** NOT STARTED

**Tasks:**
- [ ] Create `server/scripts/validate_plugin_manifest.py`:
  ```python
  """
  Phase-13 Plugin Manifest Validator
  
  Usage:
      python validate_plugin_manifest.py path.to.plugin:ClassName
  """
  import importlib
  import inspect
  from typing import Any, Dict
  
  def validate_plugin(plugin) -> Dict[str, Any]:
      # Validate: manifest ↔ class alignment
      # Validate: tools exist and are callable
      # Validate: tools accept **payload and return dict
      ...
  ```
- [ ] Tests verify: validator catches common issues
- [ ] Run pre-commit checks
- [ ] Commit

---

### COMMIT 10: Remove Fallback Logic (Final Cleanup)
**Status:** NOT STARTED

**Tasks:**
- [ ] Create test: verify no fallback exists
- [ ] Modify `vision_analysis.py`:
  - [ ] Remove: `FALLBACK_TOOL = "default"` constant
  - [ ] Remove: all fallback code paths
  - [ ] Remove: warnings about missing `tool`
- [ ] Modify `tasks.py` (if exists):
  - [ ] Remove: "first tool" fallback
- [ ] Tests verify: fallback logic completely removed
- [ ] Run pre-commit checks
- [ ] Commit with message: `"feat(phase13): remove fallback logic, enforce explicit tools"`

---

## Source of Truth Documents

| Document | Purpose |
|----------|---------|
| `PHASE_13_PLANS.md` | Authoritative plan with all specifications |
| `PHASE_13_CHECKLIST.md` | Apply-in-this-order checklist |
| `PHASE_13_NOTES_01.md` | Developer specifications |
| `PHASE_13_NOTES_02.md` | Integration specs |
| `PHASE_13_NOTES_03.md` | Plugin developer pack, troubleshooting |
| `PHASE_13_NOTES_04.md` | **Canonical answers to 5 key questions** |
| `PHASE_13_PLUGIN_TEMPLATE.md` | Example plugin code |
| `TDD_PLAN.md` | TDD methodology |

---

## STRICT REQUIREMENTS (Non-Negotiable)

1. ✅ **TDD MANDATORY** - Write tests FIRST, then implement
2. ✅ **MUST BE GREEN BEFORE CODING** - Run ALL tests, lint, typecheck before writing code
3. ✅ **FIX ALL PRE-EXISTING FAILURES** - No test failures allowed
4. ✅ **NO MAKING UP CODE** - Ask questions if requirements unclear
5. ✅ **NO COMMITTING FAILING TESTS** - Always run tests before commit
6. ✅ **10-COMMIT WORKFLOW** - Follow the 10-commit implementation order exactly

---

## Pre-Commit Checklist (Run Before Each Commit)

| # | Check | Command |
|---|-------|---------|
| 1 | Server tests pass | `cd server && uv run pytest -q` |
| 2 | Web-UI tests pass | `cd web-ui && npm install && npm test` |
| 3 | Black lint pass | `cd server && black --check .` |
| 4 | Ruff lint pass | `cd server && ruff check .` |
| 5 | MyPy typecheck pass | `cd server && mypy .` |
| 6 | ESLint pass | `cd web-ui && npx eslint src --ext ts,tsx --max-warnings=0` |
| 7 | No skipped tests | Verify no `it.skip`, `describe.skip`, `test.skip` |

---

## Notes

- **Commit 1 is NOT done** - `video_pipeline_service.py` does not exist
- Each commit must pass pre-commit checklist before proceeding
- Tests must be written BEFORE implementation (TDD)
- Progress tracker updated after each commit

---

## Last Updated
PHASE_13_PROGRESS.md and PHASE_13_PLANS.md are now the single source of truth.
Reference documents in `.ampcode/04_PHASE_NOTES/Phase_13/` are supporting documents.
