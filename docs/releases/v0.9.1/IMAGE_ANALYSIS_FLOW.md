# Image Analysis Flow — End-to-End Trace

**Scenario:** User selects a plugin, selects a tool, uploads an image, gets JSON results back.

**Date:** 2026-02-20

---

## Step-by-Step Flow

### Step 1: User Selects Plugin

**Component:** `web-ui/src/components/PluginSelector.tsx`

On mount, `PluginSelector` calls `apiClient.getPlugins()` which hits:

```
GET /v1/plugins → returns Plugin[] (name, description, version)
```

**API Client:** `web-ui/src/api/client.ts` line 101–109 — `getPlugins()` calls `this.fetch("/plugins")`.

**Server Route:** `server/app/api.py` — `/v1/plugins` endpoint returns plugin metadata from the `PluginRegistry`.

**State:** `App.tsx` stores `selectedPlugin` string. `PluginSelector` auto-selects the first plugin if none selected (line 190–207).

---

### Step 2: User Selects Tool

**Component:** `web-ui/src/components/ToolSelector.tsx`

When a plugin is selected, `ToolSelector` uses the `useManifest` hook to fetch the plugin's manifest:

```
GET /v1/plugins/{pluginId}/manifest → returns PluginManifest (tools array)
```

**Hook:** `web-ui/src/hooks/useManifest.ts` — `useManifest(pluginId)` fetches and caches manifests with 5-minute TTL.

**API Client:** `client.ts` line 219–225 — `getPluginManifest(pluginId)` calls `this.fetch(/plugins/${pluginId}/manifest)`.

**Server Route:** `/v1/plugins/{pluginId}/manifest` returns the manifest JSON from the plugin's `manifest.json` file. Each tool has `id`, `title`, `description`, `inputs`, `outputs`.

**Rendering:** `ToolSelector` displays tools as toggle buttons (line 278–313). Multi-select supported. First selected tool is marked with ★.

**State:** `App.tsx` stores `selectedTools` string array. `handleToolChange` callback updates it (line 242–244).

---

### Step 3: User Clicks Upload Button & Selects Image

**Component:** `App.tsx` line 246–271 — `handleFileUpload`

The file input triggers `handleFileUpload`:

```typescript
const handleFileUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!selectedPlugin) return;
    if (selectedTools.length === 0) return;

    const response = await apiClient.analyzeImage(
        file,
        selectedPlugin,         // e.g. "ocr"
        selectedTools[0]        // e.g. "extract_text"
    );
    const job = await apiClient.pollJob(response.job_id);
    setUploadResult(job);
};
```

**Guard:** Upload is blocked if no plugin or no tool is selected.

---

### Step 4: API Client Sends Request

**File:** `web-ui/src/api/client.ts` line 111–144 — `analyzeImage(file, plugin, tool)`

Builds a `FormData` with the file and sends:

```
POST /v1/analyze?plugin=ocr&tool=extract_text
Content-Type: multipart/form-data
Body: [file binary]
```

The `plugin` and `tool` are query parameters. The file is the form body.

---

### Step 5: Server Receives Request — API Route

**File:** `server/app/api.py` line 123–230 — `analyze_image()`

FastAPI route handler:

1. **Validates** plugin name is non-empty (line 173)
2. **Validates** device parameter if provided (line 180)
3. **Reads** file bytes: `file_bytes = await file.read()` (line 187)
4. **Parses** options JSON string if provided (line 191)
5. **Injects tool** into options: `parsed_options["tool"] = tool` (line 211)
6. **Delegates** to `AnalysisService`:

```python
result = await service.process_analysis_request(
    file_bytes=file_bytes,
    image_url=image_url,
    body_bytes=...,
    plugin=plugin,          # "ocr"
    options=parsed_options,  # {"tool": "extract_text"}
)
```

**Auth:** Requires `X-API-Key` header with "analyze" permission (line 136).

**Returns:** `AnalyzeResponse` with `job_id`, `status: "queued"`, `plugin`, `image_size`.

---

### Step 6: AnalysisService — Orchestration

**File:** `server/app/services/analysis_service.py` line 68–151 — `process_analysis_request()`

1. **Acquires image** from the first available source (file > URL > base64 body) via `_acquire_image()` (line 109)
2. **Submits job** to `TaskProcessor`:

```python
job_id = await self.processor.submit_job(
    image_bytes=image_bytes,
    plugin_name=plugin,       # "ocr"
    options=options,           # {"tool": "extract_text"}
)
```

3. **Returns** `{"job_id": "...", "status": "queued", "plugin": "ocr", "image_size": 54321}`

---

### Step 7: TaskProcessor — Background Execution

**File:** `server/app/tasks.py` line 215–468

`TaskProcessor` manages background job lifecycle:

1. **Creates** job record in `JobStore` with status `QUEUED`
2. **Looks up** plugin: `plugin = self.plugin_manager.get(plugin_name)` (line 375)
3. **Extracts** tool name: `tool_name = options.get("tool")` (line 398)
4. **Requires** tool — fails if not provided (line 399–412)
5. **Builds** tool args:

```python
tool_args = {
    "image_bytes": image_bytes,
    "device": options.get("device", "cpu"),
    "options": { ... },
}
```

6. **Executes** in thread pool (non-blocking):

```python
result = await loop.run_in_executor(
    self._executor,
    plugin.run_tool,       # VisionPlugin.run_tool()
    tool_name,             # "extract_text"
    tool_args,             # {"image_bytes": ..., "device": "cpu"}
)
```

7. **Normalises** output via `normalise_output()` (line 436)
8. **Updates** job store: status → `DONE`, stores result + `processing_time_ms`

---

### Step 8: Plugin Execution — run_tool()

**Protocol:** `server/app/protocols.py` line 21–50 — `VisionPlugin.run_tool(tool_name, args)`

Every plugin implements this interface. The plugin receives the tool name and args dict, and routes to the appropriate handler.

**Example (OCR):** `forgesyte-plugins/plugins/ocr/src/forgesyte_ocr/plugin.py`

```python
def run_tool(self, tool_name, args):
    handler = self.tools[tool_name]["handler"]
    return handler(**args)
```

The handler processes the image bytes and returns a JSON-serializable dict.

---

### Step 9: Output Normalisation

**File:** `server/app/schemas/normalisation.py` line 36 — `normalise_output()`

Transforms plugin-specific output into a canonical schema:

- **Non-YOLO plugins** (OCR, etc.): passed through as-is
- **YOLO plugins**: transformed to `{ frames: [{ frame_index, boxes, scores, labels }] }`

Detection uses `plugin_type` from the plugin manifest or falls back to plugin name matching.

---

### Step 10: Client Polls for Result

**File:** `web-ui/src/api/client.ts` line 197–217 — `pollJob(jobId)`

After receiving the `job_id` from step 4, the client polls:

```
GET /v1/jobs/{job_id} → { status, result, ... }
```

Polls every 500ms, timeout 60s. Stops when `status === "done"` or `status === "error"`.

```typescript
while (Date.now() - startTime < timeoutMs) {
    const job = await this.getJob(jobId);
    if (job.status === "done" || job.status === "error") {
        return job;
    }
    await sleep(intervalMs);
}
```

---

### Step 11: JSON Result Displayed

**Component:** `App.tsx` line 261–263

```typescript
const job = await apiClient.pollJob(response.job_id);
setUploadResult(job);     // stores full job with result
setSelectedJob(job);      // shows in job detail panel
```

The result JSON is displayed in the UI job detail view.

---

## Full Sequence Diagram

```
User                    Web-UI                      Server API              AnalysisService         TaskProcessor           Plugin
 │                        │                            │                        │                       │                    │
 │  1. Page loads         │                            │                        │                       │                    │
 │ ──────────────────────>│                            │                        │                       │                    │
 │                        │  GET /v1/plugins           │                        │                       │                    │
 │                        │ ──────────────────────────>│                        │                       │                    │
 │                        │  Plugin[] response         │                        │                       │                    │
 │                        │ <──────────────────────────│                        │                       │                    │
 │  2. Select plugin      │                            │                        │                       │                    │
 │ ──────────────────────>│                            │                        │                       │                    │
 │                        │  GET /v1/plugins/{id}/manifest                      │                       │                    │
 │                        │ ──────────────────────────>│                        │                       │                    │
 │                        │  PluginManifest (tools)    │                        │                       │                    │
 │                        │ <──────────────────────────│                        │                       │                    │
 │  3. Select tool        │                            │                        │                       │                    │
 │ ──────────────────────>│  (local state only)        │                        │                       │                    │
 │                        │                            │                        │                       │                    │
 │  4. Upload image       │                            │                        │                       │                    │
 │ ──────────────────────>│                            │                        │                       │                    │
 │                        │  POST /v1/analyze?plugin=ocr&tool=extract_text      │                       │                    │
 │                        │ ──────────────────────────>│                        │                       │                    │
 │                        │                            │  process_analysis_request()                    │                    │
 │                        │                            │ ──────────────────────>│                       │                    │
 │                        │                            │                        │  submit_job()         │                    │
 │                        │                            │                        │ ─────────────────────>│                    │
 │                        │                            │                        │  job_id               │                    │
 │                        │                            │                        │ <─────────────────────│                    │
 │                        │                            │  {job_id, status:queued}│                       │                    │
 │                        │  {job_id}                  │ <──────────────────────│                       │                    │
 │                        │ <──────────────────────────│                        │                       │                    │
 │                        │                            │                        │    (background)       │                    │
 │                        │                            │                        │                       │  run_in_executor   │
 │                        │                            │                        │                       │ ──────────────────>│
 │                        │                            │                        │                       │                    │ run_tool()
 │                        │                            │                        │                       │  result dict       │
 │                        │                            │                        │                       │ <──────────────────│
 │                        │                            │                        │                       │  normalise_output()│
 │                        │                            │                        │                       │  store result      │
 │                        │                            │                        │                       │  status → DONE     │
 │  5. Poll               │                            │                        │                       │                    │
 │                        │  GET /v1/jobs/{job_id}     │                        │                       │                    │
 │                        │ ──────────────────────────>│                        │                       │                    │
 │                        │  {status:done, result:{...}}                        │                       │                    │
 │                        │ <──────────────────────────│                        │                       │                    │
 │  6. Display result     │                            │                        │                       │                    │
 │ <──────────────────────│                            │                        │                       │                    │
```

---

## Services & Components Summary

| Layer | Component | File | Role |
|-------|-----------|------|------|
| **Web-UI** | `PluginSelector` | `web-ui/src/components/PluginSelector.tsx` | Fetches plugin list, dropdown selection |
| **Web-UI** | `ToolSelector` | `web-ui/src/components/ToolSelector.tsx` | Fetches manifest, tool toggle buttons |
| **Web-UI** | `useManifest` | `web-ui/src/hooks/useManifest.ts` | Manifest fetch + 5-min TTL cache |
| **Web-UI** | `App.tsx` | `web-ui/src/App.tsx` | Orchestrates state, file upload handler |
| **Web-UI** | `apiClient` | `web-ui/src/api/client.ts` | HTTP client — `analyzeImage()`, `pollJob()`, `getPlugins()`, `getPluginManifest()` |
| **Server** | API Route | `server/app/api.py` | `POST /v1/analyze` — validates, parses, delegates |
| **Server** | `AnalysisService` | `server/app/services/analysis_service.py` | Acquires image bytes, submits to TaskProcessor |
| **Server** | `TaskProcessor` | `server/app/tasks.py` | Background thread pool, calls `plugin.run_tool()` |
| **Server** | `normalise_output` | `server/app/schemas/normalisation.py` | Canonical schema transform (YOLO → frames/boxes) |
| **Server** | `VisionPlugin` protocol | `server/app/protocols.py` | `run_tool(tool_name, args)` contract |
| **Plugin** | OCR plugin | `forgesyte-plugins/plugins/ocr/.../plugin.py` | `run_tool()` → handler → JSON result |

---

## API Endpoints Involved

| Method | Endpoint | Purpose | Called By |
|--------|----------|---------|-----------|
| `GET` | `/v1/plugins` | List available plugins | `PluginSelector` on mount |
| `GET` | `/v1/plugins/{id}/manifest` | Get plugin tools/schema | `ToolSelector` via `useManifest` |
| `POST` | `/v1/analyze?plugin=X&tool=Y` | Submit image for analysis | `App.tsx` → `analyzeImage()` |
| `GET` | `/v1/jobs/{job_id}` | Poll job status/result | `App.tsx` → `pollJob()` |

---

## Key Design Decisions

1. **Tool is a query param, not in the body** — `?tool=extract_text` appended to `/v1/analyze` URL
2. **Job-based async** — upload returns `job_id` immediately, client polls for result
3. **Thread pool execution** — `run_in_executor` keeps plugin CPU work off the event loop
4. **First tool wins** — `selectedTools[0]` is sent even if multiple tools are selected (line 259)
5. **Manifest caching** — 5-minute TTL in `useManifest` to avoid repeated fetches
6. **Output normalisation** — YOLO output is canonicalised, OCR is passed through as-is



QUESTIONS
## Questions:

1. **Database migration strategy**: The plan mentions that DuckDB `create_all()` won't add columns to existing tables. Should I:
   - Delete the dev database and let it recreate with the new schema?
   - Or create an Alembic migration script?
   - Or manually run `ALTER TABLE` commands?

2. **PluginService**: The `VIDEO_UPLOAD.md` spec mentions creating a `PluginService` wrapper class, but the implementation plan doesn't include it. The `VideoPipelineService` already calls `plugin.run_tool()` correctly. Should I:
   - Create a `PluginService` as per VIDEO_UPLOAD.md?
   - Or skip it and use `VideoPipelineService` directly (as the plan suggests)?

3. **Worker tests**: The plan references `tests/worker/test_worker.py` but this file doesn't exist. Should I:
   - Create this test file?
   - Or follow the existing test patterns (e.g., in `tests/video/` or `tests/app/workers/`)?

4. **Tool storage**: The plan proposes adding a new `tool` column (single string), while VIDEO_UPLOAD.md suggests storing it in the existing `tools` column as JSON. Which approach should I use?

5. **Backward compatibility**: The plan suggests keeping `pipeline_id` and falling back to it when `plugin_id` is None. Is this required, or can I fully migrate to `plugin_id` + `tool`?

6. **Polling endpoints**: The plan says video uses separate endpoints (`/v1/video/status/{id}`, `/v1/video/results/{id}`) and no change is needed. Should I keep these separate, or unify them with the image polling endpoint (`/v1/jobs/{id}`)?


You’re asking exactly the right questions—let’s go straight down the list and make the architecture consistent with what you actually have.

---

### 1. Database migration strategy

**Use an Alembic migration script.**

- **Don’t** rely on `create_all()`—it won’t add columns to existing tables.
- **Don’t** manually `ALTER TABLE` in prod; that’s what Alembic is for.
- **Dev-only:** you *can* delete the dev DB to speed things up, but still keep a proper Alembic migration for everyone else.

**Verdict:**  
Write an Alembic migration that:

- Adds `plugin_id` and `tool`
- Backfills or deletes old rows as needed
- Drops `pipeline_id` / `tools` if you’re fully moving off pipelines

---

### 2. PluginService vs VideoPipelineService

You already have a `VideoPipelineService` that calls `plugin.run_tool()` correctly.

**Given that:**

- If `VideoPipelineService` already encapsulates “get plugin + call run_tool”, a separate `PluginService` wrapper is optional.
- The only reason to introduce `PluginService` is to share logic between image + video paths in a clean way.

**Verdict:**

- If `VideoPipelineService` is already the single place that does `plugin.run_tool(...)` for video, **you can skip PluginService** for now and use `VideoPipelineService` directly in the worker.
- If you want long‑term cleanliness, you can later refactor both image + video to use a shared `PluginService`, but that’s a refactor, not a blocker.

---

### 3. Worker tests location

The plan referencing `tests/worker/test_worker.py` is aspirational, not canonical.

You should follow your **existing test layout**.

**Verdict:**

- **Don’t** feel bound to `tests/worker/test_worker.py` if it doesn’t exist.
- **Do** create tests alongside similar ones—e.g. `tests/video/test_worker.py` or `tests/app/workers/test_video_worker.py`, matching your current structure.

Pick the directory where other background/worker tests live and mirror that.

---

### 4. Tool storage: column vs JSON

You have two competing ideas:

- **New `tool` column (string)**  
- **Reuse `tools` JSON column (array)**

Given your actual flow:

- A **single tool** is selected for video (and image) in the Discoveries UI.
- The worker only needs **one tool name**, not an array or pipeline.

**Verdict:**

- Use a **single `tool` string column**.
- You can deprecate `tools` JSON if it was only for the old pipeline idea.
- This keeps the job model simple: `plugin_id`, `tool`, `input_path`.

---

### 5. Backward compatibility with pipeline_id

You asked if you should:

- Keep `pipeline_id` and fall back when `plugin_id` is `NULL`, or  
- Fully migrate to `plugin_id + tool`.

Given where you’re going:

- Pipelines are not part of the new video architecture.
- Image already uses plugin + tool.
- Pipelines were a dead‑end for this path.

**Verdict:**

- If you don’t have real production dependence on `pipeline_id` for video, **fully migrate** to `plugin_id + tool` and drop `pipeline_id` from the video path.
- If there are old jobs in prod that still use `pipeline_id`, you can:
  - Keep `pipeline_id` only for historical rows, but **don’t use it for new jobs**.
  - Migration can set `plugin_id`/`tool` for new rows and ignore old ones.

Short version: **new video work should not depend on `pipeline_id` at all.**

---

### 6. Polling endpoints: separate vs unified

Current situation:

- Video: `/v1/video/status/{id}`, `/v1/video/results/{id}`  
- Image: `/v1/jobs/{id}`

Your new job model (`plugin_id`, `tool`, `status`, `output_path`) is generic and works for both.

**Verdict:**

- Long‑term clean design: **unify on `/v1/jobs/{id}`** for both image and video.
- Short‑term pragmatic approach:
  - If the video endpoints are already wired into the UI and used in prod, you can:
    - Keep them as thin wrappers that internally call the same job lookup logic as `/v1/jobs/{id}`, or
    - Gradually migrate the frontend to `/v1/jobs/{id}` and then deprecate the video‑specific ones.

If you’re already touching the frontend for video upload, this is a good moment to standardize on `/v1/jobs/{id}` and stop multiplying endpoints.

---

### Quick summary 

- **DB:** Use Alembic migration; add `plugin_id` + `tool`; drop `pipeline_id`/`tools` for new video work. There is no need for backward compatability there is no official release yet so you can effectiveley start from scratch. This will change once we release v1.0.0 but this is for v.0.9.1.

- **Service:** It’s fine to use `VideoPipelineService` directly; `PluginService` is optional refactor, not required.
- **Tests:** Follow existing test layout; create a new worker test file where similar tests live.
- **Tool storage:** Use a single `tool` string column, not JSON.
- **Backward compat:** New video jobs should use `plugin_id + tool` only; `pipeline_id` is legacy.
- **Polling:** Prefer unified `/v1/jobs/{id}`; keep video endpoints only as thin wrappers or deprecate them.
