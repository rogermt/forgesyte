# v0.9.7 Engineering Plan — Multi‑Tool Video Execution

## Overview
This plan adds support for running **multiple tools from the same plugin** on a single uploaded video in the Forgesyte server and web-ui, with corresponding plugin updates in forgesyte-plugins.

## Branch Strategy
```bash
# In forgesyte repo
git checkout -b v0.9.7

# In forgesyte-plugins repo
git checkout -b v0.9.7
```

## TDD Workflow
1. Write failing tests (RED)
2. Implement feature (GREEN)
3. Run full pre-commit suite
4. Commit after each phase

## Required Tests (must be GREEN after each phase)

### Forgesyte - Python
```bash
cd /home/rogermt/forgesyte
uv run pre-commit run --all-files          # black/ruff/mypy
cd server && uv run pytest tests/ -v       # all tests
python scripts/scan_execution_violations.py # governance check
```

### Forgesyte - Web-UI (ALL THREE required)
```bash
cd web-ui
npm run lint                               # eslint
npm run type-check                         # tsc --noEmit (MANDATORY)
npm run test -- --run                      # vitest
```

### Forgesyte-Plugins
```bash
cd plugins/forgesyte-yolo-tracker
uv run pre-commit run --all-files
```

---

## Phase Breakdown

### **Phase 1 — API Update for Multi‑Tool Video Submit**

**Files to modify:**
- `server/app/api_routes/routes/video_submit.py`
- `server/app/schemas/video.py` (if exists)

**Tasks:**
1. Change `tool: str = Query(...)` to `tool: List[str] = Query(...)` (like image_submit.py)
2. Accept both `"tools": []` and legacy `"tool": "..."` for backward compatibility
3. If `tool` list has >1 item, set `job_type="video"` but use `tool_list` (JSON) to store tools
4. Validate all tools in list belong to the plugin
5. Validate all tools support video input

**Key insight:** We REUSE `job_type="video"` (not create new "video_multi"). Multi-tool is detected by checking `len(tools) > 1` or presence of `tool_list`.

**Commit:**
```
feat(api): add multi-tool support to /v1/video/submit
```

---

### **Phase 2 — Worker Sequential Execution for Video**

**Files to modify:**
- `server/app/workers/worker.py`

**Tasks:**
1. In `_execute_pipeline()`, detect multi-tool video jobs by checking:
   - `job.job_type == "video"` AND
   - `(job.tool_list is not None)` OR `(isinstance(job.tool, list) and len(job.tool) > 1)`
2. Parse `tools_to_run` from `job.tool_list` JSON for multi-tool, or `[job.tool]` for single-tool
3. Loop through tools sequentially (like image_multi)
4. For each tool:
   - Execute via `plugin_service.run_plugin_tool()` with progress_callback
   - Store results in `results[tool_name] = result`
5. On completion, set `progress=100`

**Progress Calculation:**
- Equal weighting: `tool_weight = 100 / total_tools`
- Global progress = `(completed_tools * tool_weight) + (current_tool_frame_progress * tool_weight)`

**Commit:**
```
feat(worker): implement sequential multi-tool video execution
```

---

### **Phase 3 — Unified Progress Tracking**

**Files to modify:**
- `server/app/workers/worker.py`

**Tasks:**
1. Modify `_update_job_progress()` to accept additional parameters:
   - `current_tool_index` (0-based)
   - `total_tools`
   - `current_tool_frame_progress` (0-100 within current tool)
2. Calculate unified progress:
   ```python
   tool_weight = 100 / total_tools
   global_progress = (current_tool_index * tool_weight) + (current_tool_frame_progress * tool_weight / 100)
   ```
3. Update DB with unified progress every 5% of global progress
4. Ensure final tool reaches 100%

**Commit:**
```
feat(worker): add unified progress tracking for multi-tool video jobs
```

---

### **Phase 4 — Status Endpoint Enhancements**

**Files to modify:**
- `server/app/schemas/job.py`
- `server/app/api_routes/routes/jobs.py`

**Tasks:**
1. Add new fields to `JobResultsResponse`:
   - `current_tool: Optional[str] = None`
   - `tools_total: Optional[int] = None`
   - `tools_completed: Optional[int] = None`
2. In `get_job()` endpoint:
   - Calculate `tools_total` from `tool_list` JSON or single tool
   - Derive `tools_completed` and `current_tool` from progress (for running jobs)
   - Return `progress: None` for old jobs without progress (backward compatible)

**Commit:**
```
feat(api): extend video job status with multi-tool fields
```

---

### **Phase 5 — Web‑UI Tool Selection (Multi‑Tool)**

**Files to modify:**
- `web-ui/src/components/VideoUpload.tsx`
- `web-ui/src/api/client.ts`

**Tasks:**
1. **VideoUpload.tsx:**
   - Change from single `videoTool` to `selectedTools: string[]` state
   - Add multi-select UI (checkboxes or multi-select dropdown)
   - Filter available tools by video input type
   - Allow user to select multiple tools
   - Submit all selected tools to API

2. **client.ts - submitVideo():**
   - Change signature to accept `tools: string | string[]` (like submitImage)
   - Append each tool as separate query param: `?tool=tool1&tool=tool2`

**Commit:**
```
feat(ui): add multi-tool selection for video uploads
```

---

### **Phase 6 — Web‑UI Progress Display**

**Files to modify:**
- `web-ui/src/components/JobStatus.tsx`
- `web-ui/src/api/client.ts` (Job type)

**Tasks:**
1. **Update Job type in client.ts:**
   - Add `current_tool?: string`
   - Add `tools_total?: number`
   - Add `tools_completed?: number`

2. **JobStatus.tsx:**
   - Display current tool name when available
   - Display "Tool X of Y" text
   - Show unified progress bar (already exists)
   - Handle backward compatibility (no current_tool for old jobs)

**Commit:**
```
feat(ui): display unified progress and current tool for video jobs
```

---

### **Phase 7 — Integration Tests**

**Files to create:**
- `server/tests/video/test_multi_tool_video.py`

**Tasks:**
1. Test multi-tool video submission via API
2. Test sequential execution order
3. Test progress calculation (0-100 across tools)
4. Test combined results format
5. Test backward compatibility (single tool still works)
6. Test error handling (one tool fails → job fails)

**Commit:**
```
test: add integration tests for multi-tool video execution
```

---

### **Phase 8 — Documentation & Smoke Test**

**Files to modify:**
- `scripts/smoke_test.py` (if exists)

**Tasks:**
1. Update smoke test to validate multi-tool behavior:
   - Submit multi-tool job
   - Verify progress updates
   - Verify combined results
2. Final documentation review

**Commit:**
```
docs: add v0.9.7 release docs and update smoke test
```

---

### **Phase 9 — Forgesyte-Plugins: Complete Video Tools**

**Files to modify (in forgesyte-plugins repo):**
- Plugin manifest (add video tools)
- Plugin implementation (add tool functions)

**Tasks:**
1. Add remaining video tools:
   - `ball_detection_video`
   - `pitch_detection_video`
   - `radar_video`
   - `tracking_video`
2. Create shared `_run_video_tool` helper for consistency
3. Ensure all tools accept `progress_callback(current_frame, total_frames)`
4. Remove device hardcoding (use worker-provided device)
5. Run pre-commit checks

**Commit:**
```
feat(plugin): implement remaining video tools with shared helper
```

---

## Acceptance Criteria

- [ ] Multiple tools run sequentially on a single video
- [ ] Combined JSON results returned keyed by tool ID
- [ ] Unified progress reflects tool index + frame progress
- [ ] Web-UI displays correct progress and tool names
- [ ] All pre-commit tests pass
- [ ] All Python tests pass (1402+)
- [ ] All Web-UI tests pass (373+)
- [ ] Governance scan passes
- [ ] Backward compatible with single-tool jobs
- [ ] Old jobs return `"progress": null`

---

## Key Design Decisions (from PLUGINS.md)

1. **Job Type:** Reuse `job_type="video"` (DO NOT create "video_multi")
   - Multi-tool detected by: `len(tools) > 1` or presence of `tool_list`

2. **Progress Storage:** Only store `progress` in DB
   - Derive `current_tool`, `tools_total`, `tools_completed` dynamically in status endpoint

3. **Results Format:** Same as image_multi
   ```json
   {
     "plugin_id": "yolo-tracker",
     "tools": {
       "player_detection_video": {...},
       "ball_detection_video": {...}
     }
   }
   ```

4. **Plugin Repo:** Implement remaining 4 video tools
   - ball_detection_video
   - pitch_detection_video
   - radar_video
   - tracking_video

