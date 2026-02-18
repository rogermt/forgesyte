# Plan Conflict Resolution - v0.9.0

**Date:** 2026-02-18
**Purpose:** Resolve conflicts between DOCUMENTS.md and CODE_AND_TEST_SKELETON.md based on actual codebase analysis.

---

## 🔴 CRITICAL CONFLICT DETECTED

### Conflict: PipelineExecutor Service

**DOCUMENTS.md says:**
- ❌ NO PipelineExecutor service
- ✅ Use existing VideoFilePipelineService and DagPipelineService
- ✅ JSON pipeline definitions (ocr_only.json, yolo_ocr.json)
- ✅ Worker calls existing VideoFilePipelineService.run_on_file()

**CODE_AND_TEST_SKELETON.md says:**
- ✅ CREATE PipelineExecutor service (section 1.2)
- ✅ Wire PipelineExecutor into worker (section 1.3)
- ✅ Hardcoded Python pipeline logic

**ACTUAL CODE shows:**
- ✅ Worker already uses `_pipeline_service.run_on_file()` (Protocol)
- ✅ VideoFilePipelineService already exists and uses DagPipelineService
- ✅ Pipeline definitions are already in JSON format (yolo_ocr.json)
- ✅ DagPipelineService loads JSON pipeline definitions

---

## 📊 VERIFICATION FROM ACTUAL CODE

### Worker Implementation (`/server/app/workers/worker.py`)
```python
def _execute_pipeline(self, job: Job, db) -> bool:
    # Verify storage and pipeline services are available
    if not self._storage or not self._pipeline_service:
        job.status = JobStatus.failed
        return False

    # Execute pipeline on video file
    results = self._pipeline_service.run_on_file(
        str(input_file_path),
        job.pipeline_id,
    )
```

**Confidence:** 100% - Worker already uses pipeline service protocol

### VideoFilePipelineService (`/server/app/services/video_file_pipeline_service.py`)
```python
class VideoFilePipelineService:
    def __init__(self, dag_service: DagPipelineService) -> None:
        self.dag_service = dag_service

    def run_on_file(
        self,
        mp4_path: str,
        pipeline_id: str,
        frame_stride: int = 1,
        max_frames: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        # Opens MP4, extracts frames, calls DAG pipeline per frame
        result = self.dag_service.run_pipeline(pipeline_id, payload)
```

**Confidence:** 100% - VideoFilePipelineService already exists

### Pipeline Definition (`/server/app/pipelines/yolo_ocr.json`)
```json
{
  "id": "yolo_ocr",
  "nodes": [
    {
      "id": "detect",
      "plugin_id": "yolo",
      "tool_id": "detect_objects"
    },
    {
      "id": "read",
      "plugin_id": "ocr",
      "tool_id": "extract_text"
    }
  ],
  "edges": [{"from_node": "detect", "to_node": "read"}]
}
```

**Confidence:** 100% - Pipeline definitions are already JSON

---

## ✅ RESOLUTION: FOLLOW DOCUMENTS.md

**DOCUMENTS.md is CORRECT.** The infrastructure already exists and uses:
1. VideoFilePipelineService (Phase 15)
2. DagPipelineService (Phase 16)
3. JSON pipeline definitions
4. Worker already wired to use these services

**CODE_AND_TEST_SKELETON.md is INCORRECT** for sections 1.2 and 1.3:
- ❌ Do NOT create PipelineExecutor service
- ❌ Do NOT add hardcoded Python pipeline logic
- ✅ Use existing VideoFilePipelineService and DagPipelineService
- ✅ Create JSON pipeline definitions instead

---

## 📝 UPDATED PLAN (Based on DOCUMENTS.md)

### Backend Changes (v0.9.0-alpha)

**Commit B1:** Make `pipeline_id` optional in `/v1/video/submit`
- Modify endpoint to accept optional `pipeline_id` with default "ocr_only"

**Commit B2:** Create `ocr_only.json` pipeline definition
- Add JSON file to `/server/app/pipelines/`
- Define OCR-only pipeline declaratively

**Commit B3:** Update API documentation
- Document the new optional `pipeline_id` parameter

**Total Backend Commits:** 3 (not 5)

### Frontend Changes (v0.9.0-alpha)

**Commits F1-F12:** (unchanged from DOCUMENTS.md)
- VideoUpload component
- JobStatus component
- JobResults component
- API client methods
- Integration tests

**Total Frontend Commits:** 12

### Integration & Release (v0.9.0-alpha)

**Commits 13-15:** (unchanged from DOCUMENTS.md)
- Integration tests
- Documentation update
- Tag v0.9.0-alpha

**Total Integration Commits:** 3

---

## 🎯 FINAL COMMIT COUNT (Following DOCUMENTS.md)

| Phase | Backend | Frontend | Integration | Total |
|-------|---------|----------|-------------|-------|
| **Alpha** | 3 | 12 | 3 | **18** |
| **Beta** | 2 | 1 | 3 | **6** |
| **Final** | 0 | 0 | 2 | **2** |
| **TOTAL** | **5** | **13** | **8** | **26** |

**vs. DOCUMENTS.md:** 28 commits
**vs. My Previous Plan:** 14 commits
**vs. CODE_AND_TEST_SKELETON.md:** 16 commits (incorrect approach)

---

## 📊 CONFIDENCE LEVELS

| Area | Confidence | Source |
|------|-----------|--------|
| Use existing VideoFilePipelineService | 100% | Verified from actual code |
| Use existing DagPipelineService | 100% | Verified from actual code |
| JSON pipeline definitions | 100% | Verified from yolo_ocr.json |
| Worker already uses pipeline service | 100% | Verified from worker.py |
| Create PipelineExecutor service | 0% | ❌ INCORRECT - infrastructure exists |
| Hardcoded Python pipeline logic | 0% | ❌ INCORRECT - use JSON instead |

---

## ✅ CORRECTED APPROACH

### What to DO:
1. ✅ Make `pipeline_id` optional in `/v1/video/submit`
2. ✅ Create `ocr_only.json` pipeline definition
3. ✅ Create frontend components (VideoUpload, JobStatus, JobResults)
4. ✅ Add API client methods
5. ✅ Write integration tests
6. ✅ Run ALL 5 CI workflows before each commit

### What NOT to DO:
1. ❌ Do NOT create PipelineExecutor service
2. ❌ Do NOT add hardcoded Python pipeline logic
3. ❌ Do NOT modify VideoFilePipelineService
4. ❌ Do NOT modify DagPipelineService
5. ❌ Do NOT modify worker (it already works)

---

## 🎯 NEXT STEPS

1. Update DEVELOPMENT_PLAN.md to match DOCUMENTS.md exactly
2. Remove all references to PipelineExecutor service
3. Emphasize JSON pipeline definitions
4. Update commit counts to 26 total (not 14)
5. Ensure all commits include TDD and CI workflow requirements

---

**Conclusion:** DOCUMENTS.md is the correct source of truth. The infrastructure already exists and uses JSON pipeline definitions. No new services needed.