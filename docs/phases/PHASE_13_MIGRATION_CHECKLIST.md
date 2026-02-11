# Phase 13 Migration Checklist — VideoTracker Multi‑Tool Pipelines

Use this checklist to migrate the codebase to Phase 13.  
Complete each section before moving to the next.

---

## Pre-Migration Verification

Before starting, ensure:

- [ ] You have read PHASE_13_FOLDER_STRUCTURE.md
- [ ] You have read PHASE_13_PR_TEMPLATE.md
- [ ] You have read PHASE_13_DEV_ONBOARDING.md
- [ ] All Phase 12 tests pass
- [ ] Main branch is up to date
- [ ] No uncommitted changes

---

## Phase 1: UI Migration

### State Management
- [ ] Add `selectedTools: string[]` state to App.tsx
- [ ] Replace single `selectedTool: string` with array
- [ ] Ensure `selectedTools` can be empty during plugin switch
- [ ] Ensure `selectedTools` is populated after plugin loads

### Component Updates
- [ ] Create `web-ui/src/components/VideoTracker/PipelineToolSelector.tsx`
- [ ] Accept `pluginId`, `selectedTools`, `onToolsChange`
- [ ] Render tool list with checkboxes (multi-select)
- [ ] Validate: only tools from same plugin
- [ ] Validate: no empty selection after plugin loads
- [ ] Add visual indicator: "X tools selected"

### VideoTracker Updates
- [ ] Update `VideoTracker.tsx` to use `selectedTools` (array)
- [ ] Remove single tool selector logic
- [ ] Replace with PipelineToolSelector component
- [ ] Pass `selectedTools` to REST endpoint

### Hook Updates (useWebSocket)
- [ ] Update `sendFrame()` signature to accept `tools: string[]`
- [ ] Update WebSocket payload to include:
  ```json
  {
    "plugin_id": "...",
    "tools": ["t1", "t2", "t3"],
    "image_data": "..."
  }
  ```
- [ ] Remove any `default_tool` fallback
- [ ] Ensure error if `tools` is empty

### API Updates
- [ ] Create `web-ui/src/api/videoPipeline.ts`
- [ ] Add function: `sendPipelineRequest(plugin_id, tools, payload)`
- [ ] Add function: `validatePipeline(plugin_id, tools)`
- [ ] Return error if tools from different plugins

### Type Updates
- [ ] Create `web-ui/src/types/pipeline.ts`
- [ ] Define `Pipeline` interface:
  ```typescript
  interface Pipeline {
    plugin_id: string;
    tools: string[];
  }
  ```
- [ ] Define `PipelineRequest` interface
- [ ] Define `PipelineResponse` interface

### UI Testing
- [ ] Create test for PipelineToolSelector
- [ ] Create test for multi-select validation
- [ ] Create test for WebSocket payload format
- [ ] Verify no silent fallbacks
- [ ] `npm run test -- --run` passes
- [ ] `npm run lint` passes
- [ ] `npm run type-check` passes

---

## Phase 2: Server Service Migration

### VideoPipelineService (NEW)
- [ ] Create `server/app/services/video_pipeline_service.py`
- [ ] Implement `execute_pipeline(plugin_id, tools, payload)`
- [ ] Implement `validate_pipeline(plugin_id, tools)`
- [ ] Implement ordered execution (tool 1 → 2 → 3)
- [ ] Implement error handling (invalid pipeline, tool failure)
- [ ] Implement logging (step index, tool name)

```python
class VideoPipelineService:
    async def execute_pipeline(self, plugin_id: str, tools: List[str], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ordered pipeline of tools."""
        # Validate pipeline
        # Execute each tool in order
        # Log each step
        # Return final output
    
    async def validate_pipeline(self, plugin_id: str, tools: List[str]) -> bool:
        """Validate pipeline structure."""
        # Check plugin exists
        # Check all tools exist
        # Check all tools in same plugin
        # Return True/False
```

### VisionAnalysisService (UPDATED)
- [ ] Update `process_analysis_request()` to accept `tools: List[str]`
- [ ] Update WebSocket frame handling to use pipeline
- [ ] Remove fallback to default tool
- [ ] Remove fallback to first tool
- [ ] Ensure empty tools list is rejected

### Pipeline Models (NEW)
- [ ] Create `server/app/models/pipeline_models.py`
- [ ] Define `PipelineRequest` model:
  ```python
  class PipelineRequest(BaseModel):
      plugin_id: str
      tools: List[str]
      payload: Dict[str, Any]
  ```
- [ ] Define `PipelineResponse` model
- [ ] Define `PipelineStep` model (for logging)

### Pipeline Logging (NEW)
- [ ] Create `server/app/utils/logging/pipeline_logging.py`
- [ ] Add logger: `logger.info("Pipeline step executed", extra={"step": 0, "tool": "t1", "duration_ms": 100})`
- [ ] Log each step: index, tool name, duration
- [ ] Log errors with step context
- [ ] Never log passwords or secrets

### Routes (NEW)
- [ ] Create `server/app/routes_video.py`
- [ ] Add POST `/video/pipeline` endpoint
- [ ] Accept JSON body: `{ "plugin_id": "...", "tools": [...], "payload": {...} }`
- [ ] Validate pipeline before execution
- [ ] Call VideoPipelineService
- [ ] Return annotated frame (or error)

### Server Testing
- [ ] Create `server/tests/test_video_pipeline_rest.py`
  - [ ] Test valid pipeline execution
  - [ ] Test invalid plugin_id (404)
  - [ ] Test invalid tool (404)
  - [ ] Test tools from different plugins (400)
  - [ ] Test empty tools array (400)
  - [ ] Test ordered execution
- [ ] Create `server/tests/test_video_pipeline_ws.py`
  - [ ] Test WebSocket frame with plugin_id + tools
  - [ ] Test WebSocket with empty tools (error)
  - [ ] Test WebSocket frame validation
- [ ] Create `server/tests/test_pipeline_validation.py`
  - [ ] Test validate_pipeline() function
  - [ ] Test all edge cases
- [ ] `pytest tests/` passes
- [ ] Coverage >80%

---

## Phase 3: Governance Migration

### Pipeline Rules (NEW)
- [ ] Create `docs/governance/pipeline_rules.md`
- [ ] Document allowed pipeline operations
- [ ] Document forbidden operations (cross-plugin, cycles, etc.)
- [ ] Document tool contract requirements
- [ ] Document logging requirements
- [ ] Document validation requirements

### Update Contributor Guide
- [ ] Update `CONTRIBUTING.md` to mention Phase 13
- [ ] Link to PHASE_13_FOLDER_STRUCTURE.md
- [ ] Link to PHASE_13_PR_TEMPLATE.md
- [ ] Link to PHASE_13_DEV_ONBOARDING.md

---

## Phase 4: Cleanup & Finalization

### Remove Phase 12 Artifacts
- [ ] Remove `selectedTool: string` from App.tsx state (if not already done)
- [ ] Remove single tool fallback from tasks.py
- [ ] Remove ToolSelector component (if replaced by PipelineToolSelector)
- [ ] Update tests that relied on single tool

### Validation Suite
- [ ] Run full test suite:
  ```bash
  cd server && uv run pytest tests/ -v
  cd /home/rogermt/forgesyte && uv run pre-commit run --all-files
  cd web-ui && npm run lint && npm run type-check && npm run test -- --run
  ```
- [ ] All tests pass
- [ ] All lint passes
- [ ] All type-checks pass

### Documentation
- [ ] Update README.md to mention Phase 13 pipelines
- [ ] Add Phase 13 to ARCHITECTURE.md
- [ ] Update ROADMAP.md to mark Phase 13 complete
- [ ] Create PHASE_13_RELEASE_NOTES.md

### Git & GitHub
- [ ] All PRs merged to main
- [ ] No outstanding Phase 13 branches
- [ ] Update GitHub release notes
- [ ] Mark Phase 13 as complete

---

## Completion Checklist

When all above steps are complete:

- [ ] UI sends `plugin_id + tools[]` format
- [ ] Server validates `plugin_id + tools[]`
- [ ] No silent fallbacks to default tool
- [ ] No cross-plugin pipelines possible
- [ ] Logging shows each pipeline step
- [ ] All tests pass
- [ ] All lint passes
- [ ] All type-checks pass
- [ ] Docs are complete
- [ ] Phase 13 locked in repo structure

---

## Rollback Plan (If Needed)

If Phase 13 migration fails at any point:

1. Create branch: `git checkout -b rollback/phase13`
2. Revert to Phase 12: `git revert <commit>`
3. Document failure reason in `docs/phases/PHASE_13_ROLLBACK.md`
4. Merge rollback PR
5. Post-mortem: identify why Phase 13 failed

---

## Sign-Off

- [ ] Lead developer: Checklist reviewed
- [ ] QA: All tests pass
- [ ] Tech lead: Phase 13 governance complete
- [ ] Product: Feature ready for production

**Phase 13 is now LOCKED.**
