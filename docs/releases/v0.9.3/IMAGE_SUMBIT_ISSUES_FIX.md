There it is. Look at `image_submit.py` lines 19-21:

```python
router = APIRouter()
plugin_manager = PluginRegistry()      # ← EMPTY registry!
plugin_service = PluginManagementService(plugin_manager)
```

It creates a **brand new, empty `PluginRegistry()`** at module level. No `.load_plugins()` is ever called on it. So `plugin_manager.get("ocr")` **always returns `None`** → 400 `"Plugin 'ocr' not found"`.

Compare with `main.py:324-332` where the DI factory correctly does:
```python
registry = PluginRegistry()
registry.load_plugins()  # ← this is the missing step
```

**The bug:** `image_submit.py` never loads plugins into its registry. This endpoint has **never worked** — it's not related to your manifest change at all.

**The fix** would be to either:
- Call `registry.load_plugins()` after creating it, or
- Use FastAPI dependency injection (`Depends(create_plugin_management_service)`) like the other endpoints do

Want me to create an issue and fix it?



OK, I've traced the complete flow. Assuming #209 is fixed, here are **3 more bugs** that each independently block the pipeline:


---

### 🔴 Bug #2 — Worker crashes on `json.dumps(OCROutput)`

**File:** `server/app/workers/worker.py:268-269`
```python
result = plugin_service.run_plugin_tool(...)  # returns OCROutput (Pydantic model)
output_data = {"results": result}
output_json = json.dumps(output_data)  # 💥 TypeError: Object of type OCROutput is not JSON serializable
```

`plugin.analyze()` returns an `OCROutput(BaseModel)`. The worker passes it raw to `json.dumps` which can't serialize Pydantic models. Job gets marked `failed`.

---

### 🔴 Bug #3 — `GET /v1/jobs/{job_id}` response has NO `status` field

**File:** `server/app/schemas/job.py:25-36`
```python
class JobResultsResponse(BaseModel):
    job_id: UUID
    results: dict | None
    created_at: datetime
    updated_at: datetime
    # ← no status field!
```

The web-UI's `pollJob` checks `job.status === "done"` — but the server never returns `status`. So `job.status` is always `undefined` → **poll loops for 60s then throws timeout**.

---

### 🔴 Bug #4 — Status enum mismatch (even if status were added)

**Server** (`models/job.py`): `pending`, `running`, **`completed`**, **`failed`**
**Client** (`api/client.ts`): `queued`, `running`, **`done`**, **`error`**

The `pollJob` checks:
```typescript
if (job.status === "done" || job.status === "error")
```

But the server would send `"completed"` / `"failed"` — neither matches → poll still never terminates.

---

### Full chain of failure

```
Upload → Job created ✅
Worker picks up job → runs OCR ✅
Worker serializes result → 💥 json.dumps crash (Bug #2)
Job marked "failed" → Web-UI polls /v1/jobs/{id}
Response has no "status" → 💥 pollJob loops forever (Bug #3)
Even with status → "failed" ≠ "error" → 💥 still loops (Bug #4)
```

Want me to create issues for all 3?





Created all 3:
- **[#210](https://github.com/rogermt/forgesyte/issues/210)** — Worker `json.dumps` crash on Pydantic OCROutput
- **[#211](https://github.com/rogermt/forgesyte/issues/211)** — Response missing `status` field → pollJob never terminates
- **[#212](https://github.com/rogermt/forgesyte/issues/212)** — Status enum mismatch (`completed/failed` vs `done/error`)

All 4 bugs (#209→#210→#211→#212) form a dependency chain — each must be fixed for the image upload to work end-to-end.









the full TDD plan:

---

## TDD Plan — Issues #209, #210, #211, #212

### Overview: Two status systems exist

| System | Location | Values |
|--------|----------|--------|
| **DB/Job model** (v0.9.2) | `app/models/job.py` | `pending`, `running`, `completed`, `failed` |
| **Legacy Pydantic** (v0.8) | `app/models_pydantic.py` | `queued`, `running`, `done`, `error`, `not_found` |
| **Web-UI client** | `web-ui/src/api/client.ts` | `queued`, `running`, `done`, `error`, `not_found` |

The web-UI matches the **legacy** enum, but `/v1/jobs/{id}` uses the **DB** model. They're out of sync.

---

### Phase 1: #209 — Empty PluginRegistry in `image_submit.py`

**NEW test** → `server/tests/image/test_image_submit_registry.py`

```
test_image_submit_uses_loaded_registry
  → Verify that plugin_manager has plugins loaded (not empty)
  → Submit with plugin_id=ocr → should NOT get "Plugin 'ocr' not found"
```

**FIX** → `image_submit.py`: Replace module-level `PluginRegistry()` with `Depends()` injection or add `.load_plugins()`.

---

### Phase 2: #210 — Worker `json.dumps` crashes on Pydantic model

**NEW test** → `server/tests/app/workers/test_worker.py`

```
test_worker_handles_pydantic_result
  → Mock run_plugin_tool to return a Pydantic BaseModel (like OCROutput)
  → Verify job completes successfully (not failed)
  → Verify saved JSON is a valid dict, not a serialization error
```

**AMEND existing test** → `test_worker_run_once_saves_results_to_storage`
- Currently mocks `run_plugin_tool` returning a plain `list`. That's why it passes — it never hits the serialization bug.
- Add a parallel test with a Pydantic model return to catch the real scenario.

**FIX** → `worker.py:268`: Add `if hasattr(result, 'model_dump'): result = result.model_dump()` before `json.dumps`.

---

### Phase 3: #211 — Response missing `status` field

**AMEND existing tests** → `server/tests/api/routes/test_jobs_unified.py`

```
test_get_job_pending → add: assert "status" in data; assert data["status"] == "pending"
test_get_job_running → add: assert data["status"] == "running"
test_get_job_completed → add: assert data["status"] == "completed"
test_get_job_failed → add: assert data["status"] == "failed"
```

These currently pass because they **never check `status`**. Adding the assertions makes them fail → TDD red.

**FIX** →
1. `server/app/schemas/job.py` `JobResultsResponse`: Add `status: str` field
2. `server/app/api_routes/routes/jobs.py`: Add `status=job.status.value` to both return paths

---

### Phase 4: #212 — Status enum mismatch (web-UI)

**NEW test** → `web-ui/src/api/client.test.ts`

```
test_pollJob_resolves_on_completed_status
  → Mock fetch to return { status: "completed", results: {...} }
  → Verify pollJob resolves (doesn't timeout)

test_pollJob_resolves_on_failed_status
  → Mock fetch to return { status: "failed", results: null }
  → Verify pollJob resolves
```

**AMEND existing** → `web-ui/src/api/client.ts`
- `Job` interface: Change `status` from `"done"|"error"` to `"completed"|"failed"`
- `pollJob`: Change check from `"done"||"error"` to `"completed"||"failed"`

**AMEND existing** → `web-ui/src/types/plugin.ts` (if Job type is defined there too)

**AMEND existing** → `server/tests/test_models.py`
- `TestJobStatus` asserts `JobStatus.DONE == "done"` etc. — these test the LEGACY Pydantic enum which is still correct for its own use (MCP/WebSocket). Leave as-is unless you want to unify.

---

### Execution Order

```
Phase 1 (#209)  →  write test  →  run (FAIL)  →  fix image_submit.py     →  run (PASS)
Phase 2 (#210)  →  write test  →  run (FAIL)  →  fix worker.py           →  run (PASS)
Phase 3 (#211)  →  amend tests →  run (FAIL)  →  fix schema + jobs.py    →  run (PASS)
Phase 4 (#212)  →  write test  →  run (FAIL)  →  fix client.ts + Job type →  run (PASS)
```

Each phase is independent and mergeable on its own. Phases 1-3 are server-only (Python). Phase 4 is web-UI only (TypeScript). All 4 must be done for end-to-end to work.

Want me to start implementing Phase 1?