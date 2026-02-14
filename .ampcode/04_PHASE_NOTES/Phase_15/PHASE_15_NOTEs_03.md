Absolutely, Roger — with these three final documents, you’ll have a **fully‑armed, contributor‑ready, governance‑aligned Phase 15 package**.  
These are written in the same tone, clarity, and structure as your Phase‑14/15 docs, so they drop straight into `.ampcode/04_PHASE_NOTES/Phase_15/`.

Let’s finish this phase properly.

---

# ⭐ PHASE‑15 MIGRATION GUIDE  
Save as:

```
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_MIGRATION_GUIDE.md
```

```markdown
# Phase 15 Migration Guide  
**MP4 → Frame Extraction → DAG Execution (YOLO + OCR Edition)**

This guide explains how to migrate from Phase 14 (single-frame DAG execution) to Phase 15 (multi-frame MP4 execution) using only the YOLO and OCR plugins.

---

## 1. Preconditions (Phase 14 Complete)

Before starting Phase 15, ensure:

- [x] DAG engine implemented  
- [x] Pipeline registry loading JSON  
- [x] Type validation working  
- [x] YOLO + OCR plugins migrated  
- [x] `yolo_ocr.json` pipeline validates  
- [x] `/pipelines/{id}/run` works for single frames  

---

## 2. New Components Introduced in Phase 15

### 2.1 `VideoFilePipelineService`
- Extracts frames from MP4  
- Builds payloads  
- Calls `DagPipelineService.run_pipeline()`  
- Aggregates results  

### 2.2 `/video/upload-and-run` Endpoint
- Accepts MP4 upload  
- Accepts `pipeline_id`  
- Returns list of per-frame results  

### 2.3 Tiny MP4 Fixture
- Used for integration tests  
- Ensures deterministic behavior  

---

## 3. Migration Steps

### Step 1 — Add `yolo_ocr.json`
Place in `server/app/pipelines/`.

### Step 2 — Add `VideoFilePipelineService`
Place in `server/app/services/`.

### Step 3 — Add `/video/upload-and-run`
Place in `server/app/api/routes/video_file.py`.

### Step 4 — Add Tiny MP4 Fixture
Place in `server/app/tests/fixtures/`.

### Step 5 — Add Integration Tests
Place in `server/app/tests/phase15/`.

### Step 6 — Update Main App
Include the new router.

---

## 4. What Does NOT Change

- No new DAG semantics  
- No new plugin metadata  
- No job queue  
- No persistence  
- No tracking  
- No ReID  
- No Viz  
- No state across frames  

Phase 15 is **purely**:  
**MP4 → frames → DAG → results**

---

## 5. Validation Checklist

- [ ] `validate_plugins.py` passes  
- [ ] `validate_pipelines.py` passes  
- [ ] Integration tests pass  
- [ ] Smoke test passes  
- [ ] Governance boundaries respected  

---

## 6. After Migration

You now support:

- Offline MP4 processing  
- Multi-frame DAG execution  
- YOLO + OCR pipelines  
- Deterministic, stateless results  

This completes Phase 15 MVP.
```

---

# ⭐ PHASE‑15 RELEASE NOTES  
Save as:

```
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_RELEASE_NOTES.md
```

```markdown
# Phase 15 Release Notes  
**Offline MP4 Processing via YOLO + OCR DAG Pipeline**

Release Date: TBD  
Author: Roger

---

## Overview

Phase 15 introduces the ability to upload MP4 files and run them through existing Phase 14 DAG pipelines. This release focuses exclusively on the `yolo_ocr` pipeline and does not include tracking, ReID, Viz, or job queues.

---

## New Features

### 1. MP4 Upload Endpoint
```
POST /video/upload-and-run
```
- Accepts MP4 files  
- Accepts `pipeline_id`  
- Returns per-frame results  

### 2. Frame Extraction
- Uses OpenCV  
- Supports optional `frame_stride` and `max_frames`  

### 3. Per-Frame DAG Execution
- Each frame is processed independently  
- Stateless execution  
- Uses existing Phase 14 DAG engine  

### 4. Aggregated Results
Response format:
```json
{
  "results": [
    { "frame_index": 0, "result": {...} },
    { "frame_index": 1, "result": {...} }
  ]
}
```

---

## Added Components

- `VideoFilePipelineService`
- `video_file.py` router
- `yolo_ocr.json` pipeline
- Tiny MP4 fixture generator
- Phase 15 integration tests
- Phase 15 smoke test script
- Phase 15 governance checklist

---

## Fixed / Improved

- Improved plugin validation for video workflows  
- Added explicit payload contract for YOLO + OCR  
- Ensured strict Phase 14 boundaries remain intact  

---

## Known Limitations (Intentional)

- No job queue  
- No async workers  
- No persistence  
- No tracking  
- No ReID  
- No Viz  
- No streaming  
- No state across frames  

These are reserved for Phase 16+.

---

## Summary

Phase 15 completes the transition from single-frame DAG execution to multi-frame MP4 processing while maintaining strict statelessness and governance boundaries.
```

---

# ⭐ PHASE‑15 ONBOARDING GUIDE FOR CONTRIBUTORS  
Save as:

```
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ONBOARDING.md
```

```markdown
# Phase 15 Onboarding Guide  
**For New Contributors**

Welcome to Phase 15! This guide explains everything you need to know to work on the MP4 → DAG → Results pipeline.

---

## 1. What Phase 15 Is

Phase 15 adds support for:

- Uploading MP4 files  
- Extracting frames  
- Running each frame through a Phase 14 DAG  
- Returning aggregated results  

This phase uses **YOLO + OCR only**.

---

## 2. What Phase 15 Is NOT

Phase 15 does *not* include:

- Job queue  
- Async workers  
- Persistence  
- Tracking  
- ReID  
- Viz  
- Streaming  
- State across frames  

If you see these, they belong to Phase 16+.

---

## 3. Key Files to Know

### Pipelines
```
server/app/pipelines/yolo_ocr.json
```

### Services
```
server/app/services/video_file_pipeline_service.py
```

### API
```
server/app/api/routes/video_file.py
```

### Tests
```
server/app/tests/phase15/
server/app/tests/fixtures/tiny.mp4
```

### Docs
```
PHASE_15_README.md
PHASE_15_GOVERNANCE.md
PHASE_15_MIGRATION_GUIDE.md
PHASE_15_ARCHITECTURE.txt
```

---

## 4. Running Phase 15 Locally

### Step 1 — Generate tiny.mp4
```
python server/app/tests/fixtures/generate_tiny_mp4.py
```

### Step 2 — Run smoke test
```
./scripts/smoke_test_phase15.sh
```

### Step 3 — Run full test suite
```
uv run pytest
```

---

## 5. How the System Works

### 1. Client uploads MP4  
### 2. Backend saves it to temp file  
### 3. OpenCV extracts frames  
### 4. Each frame becomes a DAG payload  
### 5. YOLO runs → OCR runs  
### 6. Results aggregated and returned  

---

## 6. Contributor Rules

- Do not add new DAG semantics  
- Do not add new plugin types  
- Do not add persistence  
- Do not add async workers  
- Do not add tracking  
- Keep everything stateless  
- Keep everything synchronous  
- Keep everything explicit  

---

## 7. When to Ask for Help

Ask if you see:

- State across frames  
- Job IDs  
- Queues  
- Tracking  
- ReID  
- Viz  
- Database writes  

These are **Phase 16+** topics.

---

## 8. Welcome Aboard

Phase 15 is intentionally small, clean, and governed.  
Once you understand the flow:

**MP4 → frames → DAG → results**

you’re ready to contribute.
```

---

# ⭐ Final Confirmation  
With these three documents, plus everything we built earlier, you now have:

- A complete Phase‑15 implementation  
- A complete Phase‑15 test suite  
- A complete Phase‑15 governance package  
- A complete Phase‑15 contributor onboarding experience  
- A complete Phase‑15 documentation set  

You are fully equipped to ship Phase 15.



Just say the word.