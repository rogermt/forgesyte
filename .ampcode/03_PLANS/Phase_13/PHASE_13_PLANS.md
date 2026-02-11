# PHASE 13 — FINAL IMPLEMENTATION PLAN (LOCKED)

**VideoTracker Multi-Tool Linear Pipelines (Single-Plugin)**

---

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

## CANONICAL ANSWERS (7 Questions Answered)

| # | Question | Final Answer |
|---|----------|--------------|
| 1 | `protocols.py` PluginRegistry | Exists; methods: `get(plugin_id)`, `list()` |
| 2 | `main.py` router registration | `app.include_router(init_pipeline_routes(plugin_registry))` |
| 3 | `tests/helpers.py` | FakeRegistry MUST be created; FakePlugin pattern exists |
| 4 | `useVideoProcessor.ts` | Sends WS frames; must send `tools[]` |
| 5 | `plugin_management_service` | Do NOT use; use `plugin.run_tool()` |
| 6 | `FALLBACK_TOOL` | Exists at top of file; remove fallback logic only |
| 7 | WS error handling | Error frame = `{type:"error", message, frame_id}` |

---

## 10-COMMIT WORKFLOW

| # | Commit | Status |
|---|--------|--------|
| 1 | VideoPipelineService skeleton | Test → Code |
| 2 | REST endpoint /video/pipeline | Test → Code |
| 3 | Wire pipeline into VisionAnalysisService | Test → Code |
| 4 | Add validation stubs | Test → Code |
| 5 | UI state for selectedTools[] | Test → Code |
| 6 | Send pipeline via REST + WS | Test → Code |
| 7 | Implement pipeline execution | Test → Code |
| 8 | Add pipeline logging | Test → Code |
| 9 | Add Phase 13 tests | Test → Code |
| 10 | Remove fallback logic | Test → Code |

---

## FILE CHANGES SUMMARY

### Server — Create
| File | Purpose |
|------|---------|
| `server/app/services/video_pipeline_service.py` | Pipeline executor |
| `server/app/routes_pipeline.py` | REST endpoint |
| `server/app/schemas/pipeline.py` | PipelineRequest model |
| `server/tests/test_video_pipeline_service.py` | Service unit tests |
| `server/tests/test_pipeline_rest.py` | REST endpoint tests |
| `server/tests/test_vision_analysis_pipeline.py` | WS integration tests |
| `server/tests/helpers.py` | FakeRegistry (create if not exists) |

### Server — Modify
| File | Change |
|------|--------|
| `server/app/services/vision_analysis.py` | Inject VideoPipelineService, require `tools[]`, remove fallback |
| `server/app/main.py` | Register: `app.include_router(init_pipeline_routes(plugin_registry))` |

### UI — Create
| File | Purpose |
|------|---------|
| `web-ui/src/components/PipelineToolSelector.tsx` | Tool selector component |

### UI — Modify
| File | Change |
|------|--------|
| `web-ui/src/hooks/useVideoProcessor.ts` | Replace `toolName` with `tools[]` |
| `web-ui/src/components/VideoTracker.tsx` | Replace `toolName` prop with `tools[]`, update header |
| `web-ui/src/App.tsx` | Replace `selectedTool` with `selectedTools[]` |

---

## CONCRETE IMPLEMENTATIONS

### 1. VideoPipelineService (Commit 1)

```python
# server/app/services/video_pipeline_service.py
import logging
from typing import Any, Dict, List

from ..protocols import PluginRegistry

logger = logging.getLogger(__name__)


class VideoPipelineService:
    """Executes linear, single-plugin tool pipelines for Phase 13."""

    def __init__(self, plugins: PluginRegistry) -> None:
        self.plugins = plugins

    def run_pipeline(
        self,
        plugin_id: str,
        tools: List[str],
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run a linear pipeline of tools for a single plugin."""
        self._validate(plugin_id, tools)

        plugin = self.plugins.get(plugin_id)
        result: Dict[str, Any] = payload

        for idx, tool_name in enumerate(tools):
            logger.info(
                "Video pipeline step",
                extra={
                    "plugin": plugin_id,
                    "tool": tool_name,
                    "step": idx,
                },
            )

            step_payload = dict(result)
            result = plugin.run_tool(tool_name, step_payload)

            if not isinstance(result, dict):
                raise ValueError(
                    f"Tool '{tool_name}' in plugin '{plugin_id}' "
                    f"returned non-dict result of type {type(result)}"
                )

        return result

    def _validate(self, plugin_id: str, tools: List[str]) -> None:
        if not plugin_id:
            raise ValueError("Pipeline missing 'plugin_id'")

        if not tools:
            raise ValueError("Pipeline must contain at least one tool")

        plugin = self.plugins.get(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_id}' not found")
```

---

### 2. REST Endpoint (Commit 2)

```python
# server/app/schemas/pipeline.py
from pydantic import BaseModel
from typing import Any, Dict, List


class PipelineRequest(BaseModel):
    plugin_id: str
    tools: List[str]
    payload: Dict[str, Any]
```

```python
# server/app/routes_pipeline.py
from fastapi import APIRouter
from typing import Any, Dict, List

from ..protocols import PluginRegistry
from ..services.video_pipeline_service import VideoPipelineService
from ..schemas.pipeline import PipelineRequest


def init_pipeline_routes(plugins: PluginRegistry) -> APIRouter:
    """Initialize pipeline routes with dependency injection."""
    pipeline_service = VideoPipelineService(plugins)
    router = APIRouter()

    @router.post("/video/pipeline")
    async def run_video_pipeline(req: PipelineRequest) -> Dict[str, Any]:
        """Execute a linear pipeline of tools for a single plugin."""
        result = pipeline_service.run_pipeline(
            plugin_id=req.plugin_id,
            tools=req.tools,
            payload=req.payload,
        )
        return {"result": result}

    return router
```

---

### 3. VisionAnalysisService Patch (Commit 3)

**Add import at top:**
```python
from .video_pipeline_service import VideoPipelineService
```

**Add in `__init__`:**
```python
self.pipeline_service = VideoPipelineService(plugins)
```

**Replace single-tool execution (remove this):**
```python
tool_name = data.get("tool")
if not tool_name:
    logger.warning("WebSocket frame missing 'tool', defaulting to '%s'", FALLBACK_TOOL)
    tool_name = FALLBACK_TOOL
result = active_plugin.run_tool(
    tool_name,
    {"image_bytes": image_bytes, "options": data.get("options", {})},
)
```

**With this:**
```python
tools = data.get("tools")
if not tools:
    raise ValueError("WebSocket frame missing 'tools' field")

payload = {
    "image_bytes": image_bytes,
    "options": data.get("options", {}),
    "frame_id": frame_id,
}

result = self.pipeline_service.run_pipeline(
    plugin_id=plugin_name,
    tools=tools,
    payload=payload,
)
```

---

### 4. FakeRegistry Helper (Commit 1)

```python
# server/tests/helpers.py
from typing import Any, Dict, Optional


class FakePlugin:
    """Fake plugin for testing."""

    def __init__(self):
        self.id = "test-plugin"
        self.name = "Test Plugin"
        self.tools = {
            "detect_players": "detect_players",
            "track_players": "track_players",
            "annotate_frame": "annotate_frame",
        }

    def run_tool(self, tool_name: str, args: Dict) -> Dict:
        """Execute a tool and return result."""
        return {"tool": tool_name, "step_completed": tool_name, **args}


class FakeRegistry:
    """Fake plugin registry for testing."""

    def __init__(self, plugin: Optional[FakePlugin] = None):
        self._plugin = plugin

    def get(self, plugin_id: str) -> Optional[FakePlugin]:
        """Get a plugin by name."""
        return self._plugin

    def list(self) -> Dict[str, Dict[str, Any]]:
        """List all plugins."""
        if self._plugin:
            return {
                self._plugin.id: {
                    "name": self._plugin.name,
                    "tools": self._plugin.tools,
                }
            }
        return {}
```

---

### 5. UI Changes (Commits 4-6)

**useVideoProcessor.ts - WS frame:**
```ts
sendJsonMessage({
  type: "frame",
  frame_id,
  image_data,
  plugin_id: pluginId,
  tools,  // Replace: toolName
});
```

**VideoTracker.tsx - Props:**
```ts
export interface VideoTrackerProps {
  pluginId: string;
  tools: string[];  // Replace: toolName
}
```

**VideoTracker.tsx - Header:**
```tsx
Plugin: <strong>{pluginId}</strong> | Tools: <strong>{tools.join(", ")}</strong>
```

**App.tsx - State:**
```ts
const [selectedTools, setSelectedTools] = useState<string[]>([]);
// Replace: selectedTool
```

---

### 6. WebSocket Frame Structure (Confirmed)

```json
{
  "type": "frame",
  "frame_id": "abc123",
  "image_data": "<base64>",
  "plugin_id": "forgesyte-yolo-tracker",
  "tools": ["detect_players", "track_players"]
}
```

**Error Frame:**
```json
{
  "type": "error",
  "message": "WebSocket frame missing 'tools' field",
  "frame_id": "abc123"
}
```

---

## TEST PATTERNS (TDD)

### Commit 1 Test: VideoPipelineService
```python
# server/tests/test_video_pipeline_service.py
import pytest
from app.services.video_pipeline_service import VideoPipelineService
from tests.helpers import FakeRegistry, FakePlugin


def test_import():
    assert VideoPipelineService is not None


def test_instantiation():
    registry = FakeRegistry(plugin=None)
    service = VideoPipelineService(plugins=registry)
    assert service is not None


def test_run_pipeline_method_exists():
    registry = FakeRegistry(plugin=None)
    service = VideoPipelineService(plugins=registry)
    assert hasattr(service, 'run_pipeline')


def test_validate_method_exists():
    registry = FakeRegistry(plugin=None)
    service = VideoPipelineService(plugins=registry)
    assert hasattr(service, '_validate')
```

### Commit 2 Test: REST Endpoint
```python
# server/tests/test_pipeline_rest.py
from fastapi.testclient import TestClient
from app.main import app
from tests.helpers import FakeRegistry, FakePlugin


def test_post_video_pipeline():
    fake_plugin = FakePlugin()
    registry = FakeRegistry(plugin=fake_plugin)

    # Override registry
    from app.main import plugin_registry
    original_get = plugin_registry.get
    plugin_registry.get = lambda name: fake_plugin

    client = TestClient(app)
    response = client.post("/video/pipeline", json={
        "plugin_id": "test-plugin",
        "tools": ["detect_players"],
        "payload": {"test": "data"}
    })

    assert response.status_code == 200
    assert "result" in response.json()

    plugin_registry.get = original_get
```

### Commit 3 Test: WS Integration
```python
# server/tests/test_vision_analysis_pipeline.py
import pytest
from unittest.mock import MagicMock
from app.services.vision_analysis import VisionAnalysisService
from tests.helpers import FakeRegistry, FakePlugin


def test_ws_frame_with_tools_executes_pipeline():
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

    ws_manager.send_frame_result.assert_called_once()


def test_ws_frame_missing_tools_returns_error():
    registry = FakeRegistry(plugin=None)
    ws_manager = MagicMock()

    service = VisionAnalysisService(plugins=registry, ws_manager=ws_manager)

    frame_data = {
        "image_data": "base64encodeddata",
        "frame_id": "test-frame-1"
    }

    import asyncio
    asyncio.run(service.handle_frame("client-1", "test-plugin", frame_data))

    ws_manager.send_personal.assert_called_once()
    error_call = ws_manager.send_personal.call_args[0][1]
    assert error_call["type"] == "error"
    assert "tools" in error_call["message"]
```

---

## PRE-COMMIT CHECKLIST (Run Before Each Commit)

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

## VALIDATION RULES (Non-Negotiable)

- `plugin_id` must exist
- `tools[]` must be non-empty
- All tools must exist in the plugin manifest
- All tools must belong to the same plugin
- Server must reject cross-plugin pipelines

---

## OUT OF SCOPE (Do NOT Implement)

- Cross-plugin pipelines
- Parallel pipelines
- Conditional branching
- Tool graphs (DAGs)
- Tool parameter UIs
- Tool-specific UI panels
- Model selection
- Timeline scrubbing
- Video export
- Heatmaps, analytics, charts

---

## REFERENCE DOCUMENTS

| Document | Purpose |
|----------|---------|
| PHASE_13_NOTES_01.md | Developer specs + examples |
| PHASE_13_NOTES_02.md | Implementation patches |
| PHASE_13_NOTES_03.md | Plugin dev guide + troubleshooting |
| PHASE_13_NOTES_04.md | 5 Key decisions |
| PHASE_13_NOTES_05.md | 10 Implementation Q&A |
| PHASE_13_NOTES_06.md | 7 Final questions answered |
| PHASE_13_TESTS.md | Acceptance tests |
| PHASE_13_CHECKLIST.md | Implementation + review checklist |
| PHASE_13_ARCHITECTURE.md | ASCII diagrams |

---

**PLAN LOCKED. READY FOR APPROVAL.**

Reply `"APPROVED"` to begin Commit 1: VideoPipelineService skeleton with TDD.
