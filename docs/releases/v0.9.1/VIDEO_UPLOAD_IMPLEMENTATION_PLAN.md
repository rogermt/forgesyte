# Video Upload Implementation Plan — Make It Work Like Image Upload

**Goal:** User selects plugin → selects tool → uploads video → gets JSON results. Same pattern as image analysis.

**Date:** 2026-02-20

---

## What Image Upload Does Right (That Video Upload Doesn't)

| Step | Image Upload (Working) | Video Upload (Broken) |
|------|----------------------|----------------------|
| Plugin selection | `PluginSelector` → `selectedPlugin` | ❌ Ignored — hardcoded `"ocr_only"` |
| Tool selection | `ToolSelector` → `selectedTools[0]` | ❌ Ignored — no tool param at all |
| API call | `analyzeImage(file, plugin, tool)` | `submitVideo(file, "ocr_only")` — no plugin/tool |
| Server stores | plugin + tool in `options` dict | `pipeline_id="ocr_only"` — no plugin_id, no tool |
| Worker executes | `plugin.run_tool(tool_name, args)` | `VideoPipelineService.run_on_file(pipeline_id, [])` — crash |
| Polling | `pollJob(job_id)` → `/v1/jobs/{id}` | `getVideoJobStatus()` → `/v1/video/status/{id}` (separate endpoint) |
| Results | Same poll endpoint returns result | `getVideoJobResults()` → `/v1/video/results/{id}` (separate endpoint) |

---

## Current Architecture (What Exists)

### Web-UI
- **`VideoUpload.tsx`** — Standalone component. Has file input + upload button. Hardcodes `"ocr_only"`. Does NOT receive `selectedPlugin` or `selectedTools` props. Self-contained, no connection to sidebar selectors.
- **`App.tsx`** — `VideoUpload` is rendered in `viewMode === "video-upload"` (line 521–523) as `<VideoUpload />` with zero props. The `PluginSelector` and `ToolSelector` are in the sidebar but their state is NOT passed to `VideoUpload`.
- **`client.ts` `submitVideo()`** — Uses XHR (not fetch) for upload progress tracking. Sends `pipeline_id` as query param. No `plugin` or `tool` param.
- **`client.ts` `getVideoJobStatus()`** — Polls `/v1/video/status/{id}` (separate from image's `/v1/jobs/{id}`).
- **`client.ts` `getVideoJobResults()`** — Gets results from `/v1/video/results/{id}`.

### Server
- **`video_submit.py`** — `POST /v1/video/submit?pipeline_id=ocr_only`. Creates Job with `pipeline_id` only. No `plugin_id`, no `tool`.
- **`job_status.py`** — `GET /v1/video/status/{job_id}`. Reads Job from DuckDB, returns status + progress.
- **`job_results.py`** — `GET /v1/video/results/{job_id}`. Reads output JSON from storage.
- **`Job` model** — Has `pipeline_id` (String) and `tools` (String, nullable). No `plugin_id` column.
- **`worker.py`** — Calls `VideoPipelineService.run_on_file(job.pipeline_id, tools)` which expects a real `plugin_id` like `"ocr"`, but gets `"ocr_only"` → crash.
- **`VideoPipelineService`** — Calls `plugins.get(plugin_id)` then `plugin.run_tool(tool_name, args)`. This is the RIGHT execution model — it just never gets the right inputs.

### What Already Works
- `PluginSelector` + `ToolSelector` already load and display correctly
- `VideoPipelineService.run_pipeline()` already calls `plugin.run_tool()` correctly
- The `JobWorker` already picks up pending jobs and runs `_execute_pipeline()`
- Heartbeat is now fixed (Issue #207)
- Storage service saves/loads files correctly
- Job status/results endpoints query DuckDB correctly

---

## The Plan: 5 Changes to Align Video With Image

### Change 1: Pass `selectedPlugin` + `selectedTools` to `VideoUpload`

**File:** `web-ui/src/App.tsx`

Currently (line 521–523):
```tsx
<VideoUpload />
```

Needs:
```tsx
<VideoUpload
  pluginId={selectedPlugin}
  selectedTools={selectedTools}
/>
```

Just pass the existing state down. `PluginSelector` and `ToolSelector` already work.

### Change 2: `VideoUpload` Sends `plugin_id` + `tool` Instead of `pipeline_id`

**File:** `web-ui/src/components/VideoUpload.tsx`

Currently (line 39–42):
```typescript
await apiClient.submitVideo(file, "ocr_only", (p) => setProgress(p));
```

Needs:
- Accept `pluginId` and `selectedTools` as props
- Guard upload if no plugin/tool selected (same as image upload)
- Pass `plugin_id` and `tool` to the API call

### Change 3: `submitVideo()` Sends `plugin_id` + `tool` Query Params

**File:** `web-ui/src/api/client.ts` line 272–311

Currently sends:
```
POST /v1/video/submit?pipeline_id=ocr_only
```

Needs to send:
```
POST /v1/video/submit?plugin_id=ocr&tool=extract_text
```

Signature changes from `submitVideo(file, pipelineId, onProgress)` to `submitVideo(file, pluginId, tool, onProgress)`.

Uses XHR for progress tracking — keep that, just change the query params.

### Change 4: Server Endpoint Accepts `plugin_id` + `tool`, Stores Them in Job

**File:** `server/app/api_routes/routes/video_submit.py`

Currently:
```python
pipeline_id: str = Query(default="ocr_only")
```

Needs:
```python
plugin_id: str = Query(..., description="Plugin ID")
tool: str = Query(..., description="Tool ID")
```

Both required (no defaults). Store them in the Job row. This requires `plugin_id` column on the Job model (from the WORKER_SELECT_TOOL plan).

### Change 5: Worker Uses `job.plugin_id` + `job.tool`

**File:** `server/app/workers/worker.py` line 155–158

Currently:
```python
results = self._pipeline_service.run_on_file(
    str(input_file_path),
    job.pipeline_id,
    json.loads(job.tools) if job.tools else [],
)
```

Needs:
```python
results = self._pipeline_service.run_on_file(
    str(input_file_path),
    job.plugin_id,
    [job.tool],
)
```

Single tool from `job.tool`, wrapped in a list. `VideoPipelineService.run_pipeline()` already iterates over a tools list and calls `plugin.run_tool()` for each.

---

## What Stays The Same (No Changes Needed)

| Component | Why |
|-----------|-----|
| `PluginSelector.tsx` | Already works — fetches plugins, user selects |
| `ToolSelector.tsx` | Already works — fetches manifest, user selects tools |
| `useManifest.ts` | Already works — cached manifest fetch |
| `VideoPipelineService` | Already calls `plugin.run_tool()` correctly |
| `JobWorker.run_once()` | Already picks up pending jobs, marks running, calls `_execute_pipeline` |
| `job_status.py` | Already queries Job from DuckDB |
| `job_results.py` | Already reads output JSON from storage |
| `worker_state.py` / heartbeat | Fixed in Issue #207 |
| Plugin code (OCR, YOLO) | Plugins already implement `run_tool()` |

---

## Job Model Change (Prerequisite)

From `WORKER_SELECT_TOOL_IMPLEMENTATION.md` — the Job model needs a `plugin_id` column:

**File:** `server/app/models/job.py`

```python
pipeline_id = Column(String, nullable=False)
plugin_id = Column(String, nullable=True)    # NEW
tool = Column(String, nullable=True)         # NEW (single tool, replaces tools JSON)
input_path = Column(String, nullable=False)
```

The existing `tools` column (JSON string) can remain for backward compat. The new `tool` column stores the single selected tool. The worker reads `job.tool` for video jobs.

**Note:** `pipeline_id` stays for now — existing tests and the image flow still reference it. It becomes optional for video jobs (which use `plugin_id` + `tool` directly).

---

## Polling Consideration

Video currently has **separate** polling endpoints:
- `GET /v1/video/status/{id}` → `getVideoJobStatus()`
- `GET /v1/video/results/{id}` → `getVideoJobResults()`

Image uses:
- `GET /v1/jobs/{id}` → `getJob()` / `pollJob()`

**Assessment:** The video endpoints (`job_status.py`, `job_results.py`) already work — they query the same `Job` table. The `VideoUpload` component already uses `JobStatus` component (line 82) which calls these endpoints. **No change needed here for v0.9.1.** Unifying the polling endpoints is a future cleanup.

---

## Confidence Assessment

| Area | Confidence | Risk |
|------|-----------|------|
| `App.tsx` — pass props to `VideoUpload` | 99% | None |
| `VideoUpload.tsx` — accept props, guard, send | 99% | None |
| `client.ts` — change `submitVideo()` params | 95% | XHR-based, need to change query params carefully |
| `video_submit.py` — accept `plugin_id` + `tool` | 95% | Drop `DEFAULT_VIDEO_PIPELINE`, both params required |
| `worker.py` — use `job.plugin_id` + `[job.tool]` | 90% | Needs Job model change first. Must handle case where `plugin_id` is None (old jobs) |
| `Job` model — add columns | 90% | DuckDB `create_all()` won't add to existing table. Dev DB must be deleted or `ALTER TABLE` |

---

## Files Changed

| Layer | File | Change |
|-------|------|--------|
| **Web-UI** | `App.tsx` | Pass `pluginId` + `selectedTools` props to `<VideoUpload>` |
| **Web-UI** | `VideoUpload.tsx` | Accept props, guard on selection, send `plugin_id` + `tool` |
| **Web-UI** | `client.ts` | `submitVideo()` signature: `pluginId` + `tool` instead of `pipelineId` |
| **Server** | `video_submit.py` | Query params: `plugin_id` + `tool` (required). Store in Job |
| **Server** | `models/job.py` | Add `plugin_id` and `tool` columns |
| **Server** | `workers/worker.py` | Use `job.plugin_id` and `[job.tool]` in `_execute_pipeline` |

---

## TDD Commit Plan

Each commit is self-contained: write failing tests first, implement to make them pass, run full pre-commit checks before committing.

### Pre-commit checklist (run before EVERY commit)

**Server commits:**
```bash
cd server
uv run ruff check --fix app/ tests/
uv run mypy app/ --no-site-packages
uv run pytest tests/ -v --tb=short
```

**Web-UI commits:**
```bash
cd web-ui
npm run lint
npm run type-check
npm run test -- --run
```

---

### Commit 1: Add `plugin_id` column to Job model

**Scope:** Server only. 1 production file, 1 new test file.

**Existing tests (DO NOT duplicate):**
- `tests/app/models/test_job.py` — tests `pipeline_id`, status, paths, error_message (4 tests)

**TDD Phase 1 — Write failing tests:**

New file: `tests/app/models/test_job_plugin_id.py`
```
test_job_accepts_plugin_id
    - Job(pipeline_id="x", plugin_id="ocr", input_path="x") saves and reads back
test_job_plugin_id_nullable
    - Job(pipeline_id="x", plugin_id=None, input_path="x") saves OK
test_job_plugin_id_persists_through_status_change
    - Create with plugin_id="ocr", update status → plugin_id still "ocr"
```

Run tests → 3 fail (no `plugin_id` column)

**TDD Phase 2 — Implement:**

`server/app/models/job.py` — Add:
```python
plugin_id = Column(String, nullable=True)
```

Run tests → 3 pass

**Pre-commit:** ruff + mypy + full pytest → commit

```
TEST-CHANGE: feat(models): add plugin_id column to Job model

Add nullable plugin_id column for direct plugin selection.
Pipeline_id kept for backward compat.

Added tests/app/models/test_job_plugin_id.py to verify column behavior.
```

---

### Commit 2: Server endpoint accepts `plugin_id` + `tool`

**Scope:** Server only. 1 production file, 1 new test file.

**Existing tests (DO NOT duplicate):**
- `tests/api/routes/test_video_submit.py` — tests status codes + `job_id` response (3 tests). These will need updating (params change from `pipeline_id` to `plugin_id` + `tool`).

**TDD Phase 1 — Write failing tests:**

New file: `tests/api/routes/test_video_submit_plugin_tool.py`
```
test_submit_with_plugin_id_and_tool_returns_200
    - POST /v1/video/submit?plugin_id=ocr&tool=extract_text → 200 + job_id
test_submit_stores_plugin_id_in_job
    - POST with plugin_id=ocr → query Job from DB → plugin_id == "ocr"
test_submit_stores_tool_in_job
    - POST with tool=extract_text → query Job from DB → tools contains extract_text
test_submit_missing_plugin_id_returns_422
    - POST without plugin_id → 422 (required param)
test_submit_missing_tool_returns_422
    - POST without tool → 422 (required param)
```

Run tests → 5 fail

**TDD Phase 2 — Implement:**

`server/app/api_routes/routes/video_submit.py`:
- Change query params from `pipeline_id` (optional) to `plugin_id` + `tool` (both required)
- Store `plugin_id` in Job. Store `tool` in `tools` column as `json.dumps([tool])`
- Keep `pipeline_id` set to `plugin_id` for backward compat with existing worker

**Update existing tests:**
- `test_video_submit.py` — update params from `pipeline_id` to `plugin_id` + `tool`

Run tests → all pass

**Pre-commit:** ruff + mypy + full pytest → commit

```
TEST-CHANGE: feat(api): video submit accepts plugin_id + tool params

Replace pipeline_id query param with required plugin_id and tool.
Server stores both in Job row for worker pickup.

Added tests/api/routes/test_video_submit_plugin_tool.py.
Updated tests/api/routes/test_video_submit.py for new params.
```

---

### Commit 3: Worker uses `job.plugin_id` instead of `job.pipeline_id`

**Scope:** Server only. 1 production file, 1 new test file, 1 existing test update.

**Existing tests (DO NOT duplicate):**
- `tests/app/workers/test_worker.py` — 8 tests. Line 191–194 asserts `run_on_file` called with `"test_pipeline"` (pipeline_id). This assertion needs updating.

**TDD Phase 1 — Write failing tests:**

New file: `tests/app/workers/test_worker_uses_plugin_id.py`
```
test_worker_passes_plugin_id_to_pipeline_service
    - Job(pipeline_id="ocr_only", plugin_id="ocr", tools='["extract_text"]')
    - Assert run_on_file called with "ocr" (not "ocr_only")
test_worker_passes_tool_from_job_to_pipeline_service
    - Job with tools='["extract_text"]'
    - Assert run_on_file called with ["extract_text"]
test_worker_handles_missing_plugin_id_gracefully
    - Job with plugin_id=None (legacy row)
    - Assert job fails with clear error
```

Run tests → 3 fail

**TDD Phase 2 — Implement:**

`server/app/workers/worker.py` line 157 — Change:
```python
job.pipeline_id  →  job.plugin_id or job.pipeline_id
```

Fallback to `pipeline_id` if `plugin_id` is None (backward compat for old jobs).

**Update existing test:**
- `test_worker.py` line 168–173 — add `plugin_id="test_plugin"` to Job fixtures
- `test_worker.py` line 191–194 — assert `run_on_file` called with `"test_plugin"`

Run tests → all pass

**Pre-commit:** ruff + mypy + full pytest → commit

```
TEST-CHANGE: fix(worker): use job.plugin_id for pipeline execution

Worker now reads plugin_id from Job (falls back to pipeline_id for old jobs).
Fixes ValueError: Plugin 'ocr_only' not found.

Added tests/app/workers/test_worker_uses_plugin_id.py.
Updated tests/app/workers/test_worker.py fixtures for plugin_id.
```

---

### Commit 4: Client `submitVideo()` sends `plugin_id` + `tool`

**Scope:** Web-UI only. 1 production file, existing test updates.

**Existing tests (DO NOT duplicate, but DO update):**
- `client.test.ts` `submitVideo` describe block (3 tests) — currently asserts `pipeline_id=ocr_only` in URL

**TDD Phase 1 — Write failing tests:**

Update `client.test.ts` `submitVideo` tests:
```
test "should submit video with plugin_id and tool"
    - Assert URL contains plugin_id=ocr&tool=extract_text
test "should require plugin_id and tool params"
    - Verify both params appear in XHR URL
```

Run tests → fail (signature still uses `pipelineId`)

**TDD Phase 2 — Implement:**

`web-ui/src/api/client.ts` `submitVideo()`:
- Signature: `(file, pluginId, tool, onProgress?)` replaces `(file, pipelineId, onProgress?)`
- URL: `plugin_id=X&tool=Y` replaces `pipeline_id=X`

Run tests → all pass

**Pre-commit:** lint + type-check + vitest → commit

```
TEST-CHANGE: feat(client): submitVideo sends plugin_id + tool

Replace pipelineId param with pluginId and tool.
Server now receives correct plugin/tool for video jobs.

Updated client.test.ts submitVideo tests for new params.
```

---

### Commit 5: `VideoUpload` accepts props, guards on selection

**Scope:** Web-UI only. 1 production file, existing test updates.

**Existing tests (DO NOT duplicate, but DO update):**
- `VideoUpload.test.tsx` — 9 tests. Currently renders `<VideoUpload />` with no props. Need to update for props.

**TDD Phase 1 — Write failing tests:**

Add to `VideoUpload.test.tsx`:
```
test "disables upload when no plugin selected"
    - render(<VideoUpload pluginId={null} selectedTools={[]} />)
    - Upload button disabled or shows "select plugin" message
test "disables upload when no tool selected"
    - render(<VideoUpload pluginId="ocr" selectedTools={[]} />)
    - Upload button disabled
test "passes plugin_id and tool to submitVideo"
    - render(<VideoUpload pluginId="ocr" selectedTools={["extract_text"]} />)
    - Upload file → assert submitVideo called with ("ocr", "extract_text")
```

Run tests → fail (VideoUpload doesn't accept props)

**TDD Phase 2 — Implement:**

`web-ui/src/components/VideoUpload.tsx`:
- Add props interface: `{ pluginId: string | null; selectedTools: string[] }`
- Guard upload on `pluginId` and `selectedTools.length > 0`
- Call `submitVideo(file, pluginId, selectedTools[0], onProgress)`

Update existing tests to pass props.

Run tests → all pass

**Pre-commit:** lint + type-check + vitest → commit

```
TEST-CHANGE: feat(VideoUpload): accept plugin + tool props

VideoUpload now receives pluginId and selectedTools from parent.
Guards upload if no plugin/tool selected.
Passes plugin_id + tool to submitVideo API call.

Updated VideoUpload.test.tsx for new props contract.
```

---

### Commit 6: `App.tsx` passes props to `<VideoUpload>`

**Scope:** Web-UI only. 1 production file. No new tests (type-check validates props).

**Implementation:**

`web-ui/src/App.tsx` line 521–523:
```tsx
<VideoUpload pluginId={selectedPlugin} selectedTools={selectedTools} />
```

**Pre-commit:** lint + type-check + vitest → commit

```
feat(app): wire VideoUpload to plugin/tool selectors

Pass selectedPlugin and selectedTools to VideoUpload component.
Video upload now uses same plugin/tool selection as image upload.
```

---

## Commit Summary

| # | Commit | Layer | New Tests | Updated Tests | Production Files |
|---|--------|-------|-----------|---------------|-----------------|
| 1 | Job model `plugin_id` column | Server | `test_job_plugin_id.py` (3) | — | `models/job.py` |
| 2 | Endpoint `plugin_id` + `tool` | Server | `test_video_submit_plugin_tool.py` (5) | `test_video_submit.py` (3) | `video_submit.py` |
| 3 | Worker uses `plugin_id` | Server | `test_worker_uses_plugin_id.py` (3) | `test_worker.py` (1 fixture update) | `workers/worker.py` |
| 4 | Client sends `plugin_id` + `tool` | Web-UI | — | `client.test.ts` (3) | `client.ts` |
| 5 | VideoUpload accepts props | Web-UI | 3 new in existing file | `VideoUpload.test.tsx` (9 updated) | `VideoUpload.tsx` |
| 6 | App wires props | Web-UI | — | — | `App.tsx` |

**Total:** 6 commits, 14 new tests, ~16 updated tests, 6 production files
