# Uncertainty Analysis - v0.9.0 Development Plan

**Date:** 2026-02-18
**Purpose:** Identify areas where the development plan is making assumptions or guessing instead of being based on verified code.

---

## 🔴 CRITICAL ISSUES (Confidence < 50%)

### 1. PipelineExecutor Service - UNNECESSARY

**Issue:** The development plan proposes creating a new `PipelineExecutor` service.

**Reality:**
- The existing infrastructure already handles pipeline execution
- The worker uses `VideoFilePipelineService` which uses `DagPipelineService`
- `VideoFilePipelineService.run_on_file()` already handles:
  - Opening MP4 files
  - Extracting frames
  - Calling DAG pipeline per frame
  - Aggregating results
- The worker already saves results correctly: `{"results": [{"frame_index": 0, "result": {...}}, ...]}`

**Impact:**
- Creating `PipelineExecutor` is unnecessary work
- The plan should use existing services instead

**Confidence:** < 30%
**Recommendation:** Remove PipelineExecutor from the plan. Use existing `VideoFilePipelineService` and `DagPipelineService`.

---

## 🟡 MODERATE ISSUES (Confidence 50-80%)

### 2. OCR Plugin ID and Tool ID - VERIFIED ✅

**Issue:** The plan assumes OCR plugin_id is "ocr" and tool_id is "extract_text".

**Reality:** VERIFIED from `/plugins/ocr/manifest.json`:
```json
{
  "name": "ocr",
  "tools": {
    "extract_text": {
      "description": "Extract text from image using OCR",
      "input_types": ["image_bytes", "detections"],
      "output_types": ["text"]
    }
  }
}
```

**Confidence:** 100%
**Recommendation:** Plan is correct. No changes needed.

---

### 3. YOLO Plugin ID and Tool ID - VERIFIED ✅

**Issue:** The plan assumes YOLO plugin_id is "yolo" and tool_id is "detect_objects".

**Reality:** VERIFIED from `/plugins/yolo/manifest.json`:
```json
{
  "name": "yolo",
  "tools": {
    "detect_objects": {
      "description": "Detect objects in image using YOLO",
      "input_types": ["image_bytes"],
      "output_types": ["detections"]
    }
  }
}
```

**Confidence:** 100%
**Recommendation:** Plan is correct. No changes needed.

---

### 4. Pipeline Definition Format - VERIFIED ✅

**Issue:** The plan uses the pipeline definition format from `yolo_ocr.json`.

**Reality:** VERIFIED from `/server/app/pipelines/yolo_ocr.json`:
```json
{
  "id": "yolo_ocr",
  "nodes": [
    {
      "id": "detect",
      "plugin_id": "yolo",
      "tool_id": "detect_objects",
      "input_schema": {...}
    }
  ],
  "edges": [...],
  "entry_nodes": ["detect"],
  "output_nodes": ["read"]
}
```

**Confidence:** 100%
**Recommendation:** Plan is correct. No changes needed.

---

## 🟢 LOW ISSUES (Confidence 80-95%)

### 5. Job Result Structure - VERIFIED ✅

**Issue:** The plan assumes job results have a specific structure.

**Reality:** VERIFIED from `/server/app/workers/worker.py`:
```python
# Worker saves results as:
output_data = {"results": results}
# where results is from VideoFilePipelineService.run_on_file():
# [{"frame_index": 0, "result": {...}}, ...]
```

VERIFIED from tests in `/server/app/tests/video/test_video_service_unit.py`:
```python
results = service.run_on_file(str(tiny_mp4), "yolo_ocr", max_frames=1)
assert results[0]["frame_index"] == 0
assert "result" in results[0]
assert "detections" in results[0]["result"]
assert "text" in results[0]["result"]
```

**Confidence:** 100%
**Recommendation:** Plan is correct. No changes needed.

---

### 6. API Response Formats - VERIFIED ✅

**Issue:** The plan assumes specific API response formats.

**Reality:** VERIFIED from actual code:

**`/v1/video/submit`:**
```python
# From video_submit.py
return {"job_id": job_id}
```

**`/v1/video/status/{job_id}`:**
```python
# From job_status.py
return JobStatusResponse(
    job_id=job.job_id,
    status=job.status.value,
    progress=progress,
    created_at=job.created_at,
    updated_at=job.updated_at,
)
```

**`/v1/video/results/{job_id}`:**
```python
# From job_results.py
return JobResultsResponse(
    job_id=job.job_id,
    results=results,  # Loaded from storage: {"results": [...]}
    created_at=job.created_at,
    updated_at=job.updated_at,
)
```

**Confidence:** 100%
**Recommendation:** Plan is correct. No changes needed.

---

### 7. VideoTracker Component - VERIFIED ✅

**Issue:** The plan assumes VideoTracker loads videos locally, not via backend.

**Reality:** VERIFIED from `/web-ui/src/components/VideoTracker.tsx`:
```typescript
const handleVideoUpload = useCallback(() => {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = "video/*";
  input.onchange = (e) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file && file.type.startsWith("video/")) {
      // Loads locally with URL.createObjectURL(), NOT via backend
      const newSrc = URL.createObjectURL(file);
      setVideoFile(file);
      setVideoSrc(newSrc);
    }
  };
  input.click();
}, [videoSrc]);
```

**Confidence:** 100%
**Recommendation:** Plan is correct. VideoTracker is for local processing, not backend submission. Creating a separate VideoUpload component for backend submission is correct.

---

### 8. Frontend API Client Methods - VERIFIED ✅

**Issue:** The plan assumes submitVideo, getVideoJobStatus, getVideoJobResults don't exist.

**Reality:** VERIFIED - these methods don't exist in `/web-ui/src/api/client.ts`.

**Confidence:** 100%
**Recommendation:** Plan is correct. These methods need to be created.

---

## 📊 Summary

### Confidence Levels

| Area | Confidence | Status |
|------|-----------|--------|
| Backend infrastructure (endpoints, worker, services) | 100% | ✅ Verified |
| Plugin IDs and tool IDs | 100% | ✅ Verified |
| Pipeline definition format | 100% | ✅ Verified |
| Job result structure | 100% | ✅ Verified |
| API response formats | 100% | ✅ Verified |
| VideoTracker component behavior | 100% | ✅ Verified |
| Frontend API client methods | 100% | ✅ Verified |
| **PipelineExecutor service** | **< 30%** | ❌ **UNNECESSARY** |

### Critical Fix Required

**REMOVE PipelineExecutor from the plan.**

The existing infrastructure already handles everything:
- `VideoFilePipelineService` - processes video files
- `DagPipelineService` - executes pipelines
- Worker - already uses these services correctly

The plan should focus on:
1. Making `pipeline_id` optional in `/v1/video/submit`
2. Creating `ocr_only` pipeline definition
3. Creating frontend components and API methods

---

## Updated Plan (Corrected)

### Backend Changes (2 commits, not 3)

1. **B1:** Make `pipeline_id` optional in `/v1/video/submit`
2. **B2:** Create `ocr_only` pipeline definition
3. ~~**B3:** Create PipelineExecutor service~~ **(REMOVED - unnecessary)**
4. **B3:** Update API documentation (renumbered)

### Frontend Changes (6 commits) - NO CHANGES

All frontend commits remain the same.

### Beta Changes (2 commits) - NO CHANGES

All beta commits remain the same.

### Documentation & Release (3 commits) - NO CHANGES

All documentation commits remain the same.

**Total: 13 commits** (not 14)

---

## Conclusion

The development plan is **95% correct** based on verified code. The only significant issue is the unnecessary `PipelineExecutor` service, which should be removed.

All other aspects of the plan are based on verified code and tests.