# ⭐ PHASE 15 — COMMON MISTAKES
## *Anti-Patterns to Avoid During Implementation*

### ❌ 1. Implicit Pipeline Selection
**Mistake**: Assuming a default pipeline if `pipeline_id` is missing.
**Correction**: Return `422 Unprocessable Entity`. Explicit > Implicit.

### ❌ 2. Base64 Encoding
**Mistake**: Encoding frames as Base64 strings in the payload.
**Correction**: Use raw `bytes`. Base64 adds 33% overhead and CPU cost.

### ❌ 3. Phase-Named Files
**Mistake**: Naming files `phase15_router.py` or `test_phase15.py`.
**Correction**: Use functional names: `video_file.py`, `test_video_upload.py`.
**Exception**: Scripts in `scripts/` can be phase-named (e.g. `smoke_test_phase15.sh`).

### ❌ 4. Job Queue Creep
**Mistake**: Returning a `job_id` for polling.
**Correction**: Return the full results list synchronously. Phase 15 is Batch MVP.

### ❌ 5. Missing Temp File Cleanup
**Mistake**: Creating a temp file but failing to delete it on error.
**Correction**: Use `try...finally` blocks with `.unlink(missing_ok=True)`.

### ❌ 6. State Leakage
**Mistake**: Storing detections from Frame 1 to use in Frame 2.
**Correction**: Every frame is an island. No accumulation, no tracking.

### ❌ 7. Testing with Real Plugins
**Mistake**: Unit tests importing `yolo` or `ocr` plugins.
**Correction**: Use `MockDagPipelineService` only. Real plugins are for E2E tests only (if needed) or manual demo.

### ❌ 8. Async Definitions
**Mistake**: Defining `def run_on_file` as `async def`.
**Correction**: `run_on_file` should be synchronous (blocking) for OpenCV operations. The *router* can be async if it awaits the file read, but the service logic is CPU-bound.

### ❌ 9. Ignoring 422 Errors
**Mistake**: Writing tests that only check 400 and 404, missing 422 (validation).
**Correction**: Explicitly test missing fields to ensure FastAPI validation is active.

### ❌ 10. Golden Snapshot on Real Models
**Mistake**: Generating `golden_output.json` using the real YOLO model.
**Correction**: Generate it using the **Mock DAG**. Real models are non-deterministic (float drift) and make regression tests flaky.

---
