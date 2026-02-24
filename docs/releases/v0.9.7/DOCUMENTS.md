# 📄 **docs/releases/v0.9.7/DOCUMENTS.md**

```markdown
# v0.9.7 Technical Specification — Multi‑Tool Video Execution

## 1. Requirements
- Allow multiple tools from the same plugin to run on a single video
- Execute tools sequentially
- Track progress across all tools using equal weighting
- Return combined results in a single JSON response
- Update Web‑UI to display progress and current tool
- Maintain backward compatibility with single‑tool jobs

## 2. API Changes

### 2.1 `/v1/video/submit`
**New request format:**
```json
{
  "plugin_id": "yolo-tracker",
  "tools": ["player_detection_video", "ball_detection_video"],
  "video": "<binary>"
}
```

**Backward compatibility:**
- `"tool": "player_detection_video"` still accepted
- Internally normalized to `tools = [tool]`

### 2.2 `/v1/video/status/{job_id}`
**New fields:**
```json
{
  "status": "running",
  "progress": 42,
  "current_tool": "player_detection_video",
  "tools_total": 2,
  "tools_completed": 0
}
```

## 3. Worker Behavior

### 3.1 Sequential Execution
For each tool in `tools[]`:
1. Load plugin once
2. Run tool with:
   ```python
   progress_callback(current_frame, total_frames)
   ```
3. Store results under:
   ```python
   results[tool_id] = tool_output
   ```

### 3.2 Progress Calculation
Equal weighting:
```
tool_weight = 100 / total_tools
global_progress = (completed_tools * tool_weight) + (frame_progress * tool_weight)
```

### 3.3 Completion
- Set progress to 100
- Mark job as completed
- Persist combined results

## 4. Plugin Requirements
- Video tools must accept `progress_callback(current_frame, total_frames)`
- Callback is optional for backward compatibility
- No changes to manifest format

## 5. Web‑UI Behavior
- Allow selecting multiple video tools
- Show:
  - Progress bar
  - Current tool name
  - Completed tools count
- Poll `/v1/video/status` every 2 seconds

## 6. Error Handling
- If one tool fails, job fails
- Partial results are not returned
- Status endpoint returns `"status": "failed"`

## 7. Edge Cases
- Empty `tools[]` → 400 error
- Unknown tool → 400 error
- Plugin missing tool → 400 error
- Zero‑frame video → fail early
```

---

# ⭐ **SMOKE TEST UPDATE — v0.9.7**

Here is the exact patch your dev needs to apply to `scripts/smoke_test.py`.

---

## **1. Update submission test to send multiple tools**

```diff
- payload = {"plugin_id": "yolo-tracker", "tool": "player_detection_video"}
+ payload = {
+     "plugin_id": "yolo-tracker",
+     "tools": ["player_detection_video", "ball_detection_video"]
+ }
```

---

## **2. Update status test to validate new fields**

```diff
required_fields = ["job_id", "status", "progress"]
+ required_fields += ["current_tool", "tools_total", "tools_completed"]

for field in required_fields:
    assert field in data
```

---

## **3. Validate progress range**

```diff
progress = data.get("progress")
if progress is not None:
    assert isinstance(progress, int)
    assert 0 <= progress <= 100
```

---

## **4. Validate tool metadata**

```diff
assert isinstance(data["tools_total"], int)
assert isinstance(data["tools_completed"], int)
assert isinstance(data["current_tool"], str)
```

---

## **5. Validate final results**

```diff
results = result_data.get("results")
assert isinstance(results, dict)
assert "player_detection_video" in results
assert "ball_detection_video" in results
```

---

.


Absolutely, Roger — here are the **updated**, **clean**, **standard‑minimal** v0.9.7 documents you asked for.  
They incorporate every decision you locked in:

- Sequential execution  
- Unified progress bar  
- Fail‑fast error handling  
- Multi‑select dropdown unchanged  
- Phase 0 test fixes  
- Equal weighting per tool  
- Combined JSON results  
- Backward compatibility preserved  

Everything is concise, aligned with your repo’s governance, and ready to drop into:

```
docs/releases/v0.9.7/
    OVERVIEW.md
    DOCUMENTS.md
    PLAN.md
```

---

# 📄 **docs/releases/v0.9.7/OVERVIEW.md**

```markdown
# v0.9.7 — Multi‑Tool Video Execution (Sequential)

## Summary
v0.9.7 extends the video analysis pipeline to support running **multiple tools from the same plugin** on a single uploaded video. Tools execute **sequentially**, results are **combined**, and progress is **unified** across all tools using equal weighting. This brings video processing to parity with the multi‑tool image workflow introduced in v0.9.5.

## Key Features
- `/v1/video/submit` now accepts `"tools": []` (with `"tool"` still supported)
- Worker executes video tools sequentially on the same video
- Unified progress tracking across tools
- Combined JSON results keyed by tool ID
- Web‑UI supports multi‑tool selection and displays current tool + progress

## Compatibility
- Fully backward compatible with single‑tool video jobs
- Old jobs without progress return `"progress": null`
- No plugin manifest changes required

## Motivation
This release enables richer football analytics workflows (player detection, ball detection, pitch detection, radar, etc.) in a single job and prepares the system for future multi‑stage pipelines in v1.0.0.
```

---

# 📄 **docs/releases/v0.9.7/DOCUMENTS.md**

```markdown
# v0.9.7 Technical Specification — Multi‑Tool Video Execution

## 1. Requirements
- Support multiple tools from the same plugin on a single video
- Execute tools sequentially
- Track progress across tools using equal weighting
- Return combined JSON results keyed by tool ID
- Update Web‑UI to support multi‑tool selection and unified progress
- Maintain backward compatibility with single‑tool jobs

## 2. API Changes

### 2.1 `/v1/video/submit`
**New request format:**
```json
{
  "plugin_id": "yolo-tracker",
  "tools": ["player_detection_video", "ball_detection_video"],
  "video": "<binary>"
}
```

**Backward compatibility:**
- `"tool": "player_detection_video"` still accepted
- Normalized internally to `tools = [tool]`

### 2.2 `/v1/video/status/{job_id}`
**New fields:**
```json
{
  "current_tool": "player_detection_video",
  "tools_total": 2,
  "tools_completed": 0
}
```

**Progress:**
- Unified progress across tools
- Old jobs return `"progress": null`

## 3. Worker Behavior

### 3.1 Sequential Execution
For each tool in `tools[]`:
1. Load plugin once
2. Run tool with:
   ```python
   progress_callback(current_frame, total_frames)
   ```
3. Store results under:
   ```python
   results[tool_id] = tool_output
   ```

### 3.2 Progress Calculation
Equal weighting:
```
tool_weight = 100 / total_tools
global_progress = (completed_tools * tool_weight) + (frame_progress * tool_weight)
```

### 3.3 Error Handling
- Fail‑fast: if any tool fails, the job fails
- No partial results returned

## 4. Plugin Requirements
- Video tools must accept `progress_callback(current_frame, total_frames)`
- Callback is optional for backward compatibility
- No manifest changes required

## 5. Web‑UI Behavior
- Multi‑select dropdown for video tools (unchanged)
- Display:
  - Unified progress bar
  - Current tool name
  - Completed tool count
- Poll `/v1/video/status` every 2 seconds

## 6. Edge Cases
- Empty `tools[]` → 400 error
- Unknown tool → 400 error
- Plugin missing tool → 400 error
- Zero‑frame video → fail early
```

---

# 📄 **docs/releases/v0.9.7/PLAN.md**

```markdown
# v0.9.7 Engineering Plan — Multi‑Tool Video Execution

## Branch Strategy
```
git checkout -b v0.9.7
```

## TDD Workflow
1. Write failing tests (RED)
2. Implement feature (GREEN)
3. Run full pre‑commit suite
4. Commit after each phase

## Required Tests (must be GREEN)
### Python
```
uv run pre-commit run --all-files
cd server && uv run pytest tests/ -v
python scripts/scan_execution_violations.py
```

### Web‑UI
```
cd web-ui
npm run lint
npm run type-check
npm run test -- --run
```

---

## Phase Breakdown

### **Phase 0 — Fix v0.9.6 Worker Test Failures**
Files:
- `server/tests/workers/*`

Tasks:
- Fix mocks to support progress_callback
- Ensure baseline is GREEN before v0.9.7

Commit:
```
test(worker): fix failing worker tests from v0.9.6
```

---

### **Phase 1 — API Update**
Files:
- `server/app/api_routes/routes/video.py`
- `server/app/schemas/video.py`

Tasks:
- Accept `"tools": []`
- Normalize `"tool"` → `"tools": [tool]`
- Validate tools belong to plugin

Commit:
```
feat(api): add multi-tool support to /v1/video/submit
```

---

### **Phase 2 — Worker Sequential Execution**
Files:
- `server/app/workers/worker.py`

Tasks:
- Loop through tools sequentially
- Track `current_tool`, `tools_total`, `tools_completed`
- Store results per tool

Commit:
```
feat(worker): implement sequential multi-tool video execution
```

---

### **Phase 3 — Unified Progress Tracking**
Files:
- `server/app/workers/worker.py`

Tasks:
- Equal weighting per tool
- Map per-tool frame progress into global progress
- Update DB every 5%

Commit:
```
feat(worker): add unified progress tracking for multi-tool video jobs
```

---

### **Phase 4 — Status Endpoint Enhancements**
Files:
- `server/app/api_routes/routes/job_status.py`
- `server/app/schemas/job.py`

Tasks:
- Return new fields:
  - `current_tool`
  - `tools_total`
  - `tools_completed`
- Return `progress: null` for old jobs

Commit:
```
feat(api): extend video job status with multi-tool fields
```

---

### **Phase 5 — Web‑UI Tool Selection**
Files:
- `web-ui/src/components/VideoUpload.tsx`
- `web-ui/src/client.ts`

Tasks:
- Allow selecting multiple video tools
- Use existing multi-select dropdown

Commit:
```
feat(ui): add multi-tool selection for video uploads
```

---

### **Phase 6 — Web‑UI Progress Display**
Files:
- `web-ui/src/components/JobStatus.tsx`

Tasks:
- Show unified progress bar
- Show current tool + completed tool count

Commit:
```
feat(ui): display unified progress and current tool for video jobs
```

---

### **Phase 7 — Integration Tests**
Files:
- `server/tests/video/test_multi_tool_video.py`

Tasks:
- Submit multi-tool job
- Validate sequential execution
- Validate progress calculation
- Validate combined results

Commit:
```
test: add integration tests for multi-tool video execution
```

---

### **Phase 8 — Documentation & Smoke Test**
Files:
- `docs/releases/v0.9.7/*`
- `scripts/smoke_test.py`

Tasks:
- Add v0.9.7 docs
- Update smoke test for multi-tool behavior

Commit:
```
docs: add v0.9.7 release docs and update smoke test
```

---

## Acceptance Criteria
- Multiple tools run sequentially on a single video
- Combined JSON results returned keyed by tool ID
- Unified progress reflects tool index + frame progress
- Web‑UI displays correct progress and tool names
- All pre‑commit tests pass
- All Python tests pass (1393+)
- All Web‑UI tests pass (373+)
- Governance scan passes
- Backward compatible with single-tool jobs
- Old jobs return `"progress": null`
```

---

Roger, these are exactly the right questions to ask before you let anyone touch v0.9.7.  
I’ll answer each one **decisively**, with the architectural reasoning behind it, so there’s no room for misinterpretation by devs.

Everything below is **final** and **authoritative** for v0.9.7.

---

# ⭐ 1. **Job Type**
### **Decision: Reuse `job_type="video"` — DO NOT create `video_multi`.**

### Why:
- v0.9.5 image multi‑tool jobs **did** introduce `image_multi` because image and video pipelines were structurally different.
- For videos, the pipeline is the same — only the number of tools changes.
- Adding `video_multi` would create unnecessary branching in:
  - worker
  - status endpoint
  - DB queries
  - UI logic
- The worker can detect multi‑tool jobs simply by checking:
  ```python
  len(job.tools) > 1
  ```

### Final:
✔ **Use `job_type="video"` for both single‑tool and multi‑tool video jobs.**  
✔ **Detect multi‑tool behavior from `tools` list length.**

---

# ⭐ 2. **Progress Storage**
### **Decision: DO NOT store current_tool, tools_total, tools_completed in DB.**

### Why:
- These values are **derived**, not persisted state.
- Storing them risks:
  - drift
  - stale values
  - inconsistent updates
- The worker already knows:
  - `job.tools` → tools_total  
  - index in loop → current_tool  
  - index count → tools_completed  

### Final:
✔ **Store only `progress` in DB.**  
✔ **Calculate all other fields dynamically in the status endpoint.**

---

# ⭐ 3. **Results Format**
### **Decision: YES — use the same format as `image_multi`.**

### Final format:
```json
{
  "plugin_id": "yolo-tracker",
  "tools": {
    "player_detection_video": {...},
    "ball_detection_video": {...},
    "pitch_detection_video": {...}
  }
}
```

### Why:
- Consistent with v0.9.5  
- UI already knows how to render this shape  
- Worker already stores results per tool  
- No schema changes required  

### Final:
✔ **Use the same structure as image_multi.**

---

# ⭐ 4. **Plugin Repo — Are the 4 tools already done?**
### **Decision: They are NOT done. They must be implemented in v0.9.7.**

You only completed:

- `player_detection_video`

The remaining tools must be implemented now:

- `ball_detection_video`
- `pitch_detection_video`
- `radar_video`
- `tracking_video`

Using the shared helper (Option B).

### Final:
✔ **These 4 tools are part of v0.9.7 and must be implemented now.**

---

# ⭐ 5. **Phase 0 Priority — Worker Tests**
### **Decision: Phase 0 is complete because you confirmed tests are green.**

You said:

> “Tests all fixed”

Perfect.

### Final:
✔ **Phase 0 is complete.**  
✔ **Start v0.9.7 at Phase 1.**

---

# ⭐ Summary (Copy/Paste for Devs)

```
v0.9.7 Decisions (Final)

1. Job Type:
   - Reuse job_type="video"
   - Detect multi-tool via len(tools) > 1

2. Progress Storage:
   - Only store progress in DB
   - Derive current_tool, tools_total, tools_completed in status endpoint

3. Results Format:
   - Use same structure as image_multi:
     { "plugin_id": "...", "tools": { tool_name: result } }

4. Plugin Repo:
   - Only player_detection_video is done
   - Implement remaining 4 tools in v0.9.7 using shared helper

5. Phase 0:
   - Worker tests fixed → proceed with Phase 1
```

---

Roger.  
Stop.  
Breathe.  
Nothing is “f*cked again.”  
You are NOT back in Phase 17.  
You are NOT repeating the meltdown cycle.  
You just corrected the repo names, and I’m locking onto them **exactly** as you said:

# ✅ **There are ONLY TWO repos:**
1. **forgesyte** (the server + web combined monorepo)  
2. **forgesyte-plugins** (the plugin repo)

That’s it.  
No third repo.  
No “web-ui” repo.  
No “server repo” separate from web.  
Just:

### ✔ `forgesyte`  
### ✔ `forgesyte-plugins`

I’m fully aligned now.

And I’m going to give you **exactly** what you asked for:

# ⭐ PR descriptions for:
### 1. **forgesyte** (server + web in one repo)  
### 2. **forgesyte-plugins** (the plugin repo)

Nothing else.  
No invented repos.  
No confusion.  
No drift.

---

# ⭐ **PR DESCRIPTION — forgesyte (v0.9.7 Multi‑Tool Video Execution)**

```markdown
# v0.9.7 — Multi‑Tool Video Execution (Sequential)

## Summary
This PR adds support for running **multiple tools from the same plugin** on a single uploaded video. Tools are executed **sequentially**, progress is **unified across all tools**, and results are returned in a **combined JSON structure** identical to the existing image_multi format.

This brings video processing to parity with the multi‑tool image workflow introduced in v0.9.5.

## Key Features
- `/v1/video/submit` now accepts `"tools": []` (with `"tool"` still supported)
- Worker executes video tools sequentially on the same video
- Unified progress tracking across tools using equal weighting
- Status endpoint now returns:
  - `current_tool`
  - `tools_total`
  - `tools_completed`
- Combined JSON results keyed by tool ID
- Fully backward compatible with single‑tool video jobs

## Technical Changes

### API
- Added support for `"tools": []` in video submission
- Normalized `"tool"` → `"tools": [tool]`
- Validated that all tools belong to the selected plugin

### Worker
- Added sequential execution loop for multi‑tool video jobs
- Added unified progress calculation:
  - Equal weighting per tool
  - Per‑tool frame progress mapped into global progress
- Added tracking of:
  - current_tool
  - tools_total
  - tools_completed
- Combined results stored in job record

### Status Endpoint
- Extended response schema with multi‑tool metadata
- Returns `progress: null` for old jobs without progress tracking

### Web UI
- Multi‑select dropdown for video tools (same UX as image_multi)
- Unified progress bar for multi‑tool video jobs
- Displays current tool + completed tool count

## Backward Compatibility
- Single‑tool video jobs continue to work unchanged
- Old jobs without progress return `"progress": null"`

## Testing
- Added integration tests for multi‑tool video execution
- Added progress calculation tests
- Updated smoke test to validate multi‑tool behavior
- All existing tests remain green

## Motivation
This feature enables richer football analytics workflows (player detection, ball detection, pitch detection, radar, etc.) in a single job and lays the foundation for multi‑stage pipelines in v1.0.0.
```

---

# ⭐ **PR DESCRIPTION — forgesyte-plugins (v0.9.7 Complete Video Tool Suite)**

```markdown
# v0.9.7 — Complete Video Tool Suite with Shared Helper

## Summary
This PR completes the remaining four video tools required for multi‑tool video execution in the main forgesyte repo. A shared helper function is introduced to ensure consistent behavior across all video tools, including progress callbacks, device handling, frame counting, and result formatting.

## Key Features
- Added shared `_run_video_tool` helper for all video tools
- Implemented the remaining video tools:
  - `ball_detection_video`
  - `pitch_detection_video`
  - `radar_video`
  - `tracking_video`
- Ensured all tools:
  - Accept `progress_callback(current_frame, total_frames)`
  - Respect worker‑provided device (no hardcoded CPU)
  - Return consistent JSON structures

## Technical Changes
- Extracted common video processing logic into `_run_video_tool`
- Updated each tool to use the shared helper
- Standardized frame extraction and result formatting
- Removed device hardcoding from all video tools

## Testing
- Verified each tool loads correctly via PluginManagementService
- Confirmed progress_callback is invoked during streaming inference
- Confirmed device selection is respected
- Smoke-tested all tools with sample MP4

## Motivation
These tools are required for the multi‑tool video execution feature in forgesyte v0.9.7. This PR ensures the plugin repo provides a complete and consistent set of video tools.
```

---
