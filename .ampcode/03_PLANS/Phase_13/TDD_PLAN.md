# Phase 13 TDD Plan — VideoTracker Multi-Tool Linear Pipelines

## STRICT REQUIREMENTS (Non-Negotiable)

1. ✅ **TDD MANDATORY** - Write tests FIRST, then implement
2. ✅ **MUST BE GREEN BEFORE CODING** - Run ALL tests, lint, typecheck and ensure everything passes BEFORE writing any code
3. ✅ **FIX ALL PRE-EXISTING FAILURES** - No test failures allowed
4. ✅ **NO MAKING UP CODE** - Ask questions if requirements unclear
5. ✅ **NO COMMITTING FAILING TESTS** - Always run tests before commit
6. ✅ **10-COMMIT WORKFLOW** - Follow the 10-commit implementation order exactly

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

## 10-COMMIT IMPLEMENTATION ORDER

Based on PHASE_13_CHECKLIST.md (authoritative sequence):

### COMMIT 1: VideoPipelineService Skeleton
- [ ] Create test: `server/tests/test_video_pipeline_service.py`
- [ ] Test: imports without errors
- [ ] Test: instantiation works
- [ ] Test: `run_pipeline()` and `_validate()` methods exist
- [ ] Create: `server/app/services/video_pipeline_service.py`
- [ ] Service: Class `VideoPipelineService` with stubs

### COMMIT 2: Patch VisionAnalysisService (WebSocket)
- [ ] Create test: `server/tests/test_vision_analysis_pipeline.py`
- [ ] Test: WS frame with `tools[]` executes pipeline
- [ ] Test: validation errors return error frames
- [ ] Modify: `server/app/services/vision_analysis.py`
- [ ] Inject: `VideoPipelineService` in `__init__`
- [ ] Replace: single-tool with pipeline execution
- [ ] Require: `tools[]` in WS frames
- [ ] Remove: fallback logic for Phase 13 path
- [ ] Keep: all existing error handling

### COMMIT 3: REST Pipeline Endpoint
- [ ] Create test: `server/tests/test_pipeline_rest.py`
- [ ] Test: POST `/video/pipeline` works
- [ ] Test: validation errors return 422
- [ ] Test: multi-tool pipeline returns correct result
- [ ] Create: `server/app/schemas/pipeline.py` with `PipelineRequest`
- [ ] Add route: `POST /video/pipeline` in appropriate routes module
- [ ] Wire: endpoint to `VideoPipelineService.run_pipeline()`

### COMMIT 4: Update useVideoProcessor Hook
- [ ] Create test: `web-ui/scripts/test_websocket_hook.py`
- [ ] Test: hook sends `tools[]` in WS frames
- [ ] Modify: `web-ui/src/hooks/useVideoProcessor.ts`
- [ ] Replace: `toolName` param with `tools: string[]`
- [ ] Update: WS frame structure

### COMMIT 5: Patch VideoTracker Component
- [ ] Create test: `web-ui/scripts/test_components.py` (add VideoTracker tests)
- [ ] Test: VideoTracker accepts `tools[]` prop
- [ ] Test: header displays tool list
- [ ] Modify: `web-ui/src/components/VideoTracker.tsx`
- [ ] Replace: `toolName` prop with `tools: string[]`
- [ ] Update: header display to show tools

### COMMIT 6: (Optional) UI Tool Selector
- [ ] Create: `web-ui/src/components/PipelineToolSelector.tsx`
- [ ] Add: `selectedTools: string[]` state to VideoTracker
- [ ] Pass: `selectedTools` to hook instead of hardcoded tools

### COMMIT 7: Add Pipeline Logging
- [ ] Write logging tests
- [ ] Log: `step=0 tool=toolName` for each tool
- [ ] Log: `plugin` ID, `tool_name`, `step` index
- [ ] Log: `args_keys` for debugging

### COMMIT 8: Add Regression Test Suite
- [ ] Create: `server/tests/test_pipeline_regression.py`
- [ ] Test: tools execute in order
- [ ] Test: output of last tool is returned
- [ ] Test: validation edge cases
- [ ] Test: WS + REST integration

### COMMIT 9: Add Plugin Validation Tools
- [ ] Create: `server/scripts/validate_plugin_manifest.py`
- [ ] Validate: manifest ↔ class alignment
- [ ] Validate: tools exist and are callable
- [ ] Validate: tools accept `**payload` and return `dict`

### COMMIT 10: Remove Fallback Logic (Final Cleanup)
- [ ] Write tests verifying no fallback
- [ ] Remove: warnings about missing `tool`
- [ ] Remove: defaulting to `"default"`
- [ ] Remove: `FALLBACK_TOOL` usage in WS frames

---

## CONCRETE SPECIFICATIONS

### PipelineRequest Model (REST)
```python
class PipelineRequest(BaseModel):
    plugin_id: str
    tools: List[str]
    payload: Dict[str, Any]
```

### WebSocket Frame Structure
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
class VideoPipelineService:
    def __init__(self, plugin_registry: PluginRegistry):
        self.plugin_registry = plugin_registry
    
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

### Plugin Interface (from PHASE_13_PLUGIN_TEMPLATE.md)
```python
class Plugin:
    id: str
    name: str
    tools: Dict[str, str]  # {tool_name: method_name}
    
    def tool_name(self, **payload) -> dict:
        """Accept **payload, return dict."""
        ...
```

### Error Handling
- **Validation errors**: Raise `ValueError` (REST returns 422)
- **Tool execution errors**: Let exceptions bubble up (WS sends error frame, REST returns 500)
- **Fail-fast**: If tool N fails, tool N+1 is NOT executed

---

## FILES TO CREATE

### Server - Create
| File | Purpose |
|------|---------|
| `server/app/services/video_pipeline_service.py` | Pipeline executor service |
| `server/app/schemas/pipeline.py` | PipelineRequest model |
| `server/tests/test_video_pipeline_service.py` | Service unit tests |
| `server/tests/test_vision_analysis_pipeline.py` | WS integration tests |
| `server/tests/test_pipeline_rest.py` | REST endpoint tests |
| `server/tests/test_pipeline_regression.py` | Regression tests |
| `server/scripts/validate_plugin_manifest.py` | Plugin validator CLI |

### Web UI - Create
| File | Purpose |
|------|---------|
| `web-ui/src/components/PipelineToolSelector.tsx` | Tool selector (optional) |

---

## FILES TO MODIFY

### Server - Modify
| File | Change |
|------|--------|
| `server/app/services/vision_analysis.py` | Inject VideoPipelineService, require tools[], remove fallback |
| `server/app/api.py` or `server/app/routes_*.py` | Add `POST /video/pipeline` endpoint |
| `server/app/tasks.py` | Remove fallback logic |

### Web UI - Modify
| File | Change |
|------|--------|
| `web-ui/src/hooks/useVideoProcessor.ts` | Replace `toolName` with `tools[]` |
| `web-ui/src/components/VideoTracker.tsx` | Replace `toolName` prop with `tools[]`, update header |
| `web-ui/src/App.tsx` | Update VideoTracker usage to pass `tools[]` |

---

## PHASE 13 ARCHITECTURE

```
[VideoTracker UI]
      |
      v
[useVideoProcessor hook]
      |
      v
[WebSocket JSON frame: {type, frame_id, image_data, plugin_id, tools: []}]
      |
      v
[VisionAnalysisService.handle_frame]
      |
      v
[VideoPipelineService.run_pipeline(plugin_id, tools, payload)]
      |
      v
[Plugin.run_tool(tool_name, payload)]
      |
      v
[Final dict result]
      |
      v
[ws_manager.send_frame_result]
      |
      v
[VideoTracker receives result, draws overlay]
```

---

## REFERENCE DOCUMENTS

| Document | Path |
|----------|------|
| PHASE_13_CHECKLIST.md | `.ampcode/04_PHASE_NOTES/Phase_13/PHASE_13_CHECKLIST.md` |
| PHASE_13_NOTES_01.md | `.ampcode/04_PHASE_NOTES/Phase_13/PHASE_13_NOTES_01.md` |
| PHASE_13_NOTES_02.md | `.ampcode/04_PHASE_NOTES/Phase_13/PHASE_13_NOTES_02.md` |
| PHASE_13_NOTES_03.md | `.ampcode/04_PHASE_NOTES/Phase_13/PHASE_13_NOTES_03.md` |
| PHASE_13_PLUGIN_TEMPLATE.md | `.ampcode/04_PHASE_NOTES/Phase_13/PHASE_13_PLUGIN_TEMPLATE.md` |

---

## APPROVAL REQUIRED

Before proceeding, confirm:

- [ ] All 6 strict requirements are understood
- [ ] Pre-commit checklist will be run before each commit
- [ ] 10-commit order will be followed exactly
- [ ] TDD methodology will be used (tests first)
- [ ] No code will be made up without clarification

**Ready to start? Reply "APPROVED" to begin COMMIT 1.**
