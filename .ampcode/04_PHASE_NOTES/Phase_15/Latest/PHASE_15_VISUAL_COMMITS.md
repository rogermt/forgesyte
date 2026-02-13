# ⭐ PHASE 15 — VISUAL COMMITS
## *A Visual Guide to the 10-Step Implementation Strategy*

This document visualizes the exact state of the repo after each commit.

---

### 🟢 COMMIT 1: Pipeline Definition
**Goal**: Establish the DAG.
```
server/app/pipelines/
 └── yolo_ocr.json  (NEW: "detect" -> "read")
```
*Verification*: `validate_pipelines.py` passes.

---

### 🟢 COMMIT 2: Scope & Contracts
**Goal**: Lock boundaries.
```
.ampcode/04_PHASE_NOTES/Phase_15/
 ├── PHASE_15_PAYLOAD_YOLO_OCR.md (NEW: frame_index + image_bytes)
 ├── PHASE_15_SCOPE.md            (UPDATE: Forbidden items list)
 └── PHASE_15_OVERVIEW.md         (REWRITE: Batch-only)
```
*Verification*: grep for forbidden terms in overview.

---

### 🟢 COMMIT 3: Test Assets
**Goal**: Deterministic inputs.
```
server/app/tests/fixtures/
 ├── generate_tiny_mp4.py         (NEW)
 └── tiny.mp4                     (NEW: 3 frames, 320x240)
server/app/tests/video/fakes/
 └── corrupt_mp4_generator.py     (NEW)
server/pyproject.toml             (UPDATE: opencv-python-headless)
```
*Verification*: `generate_tiny_mp4.py` runs, `tiny.mp4` opens in cv2.

---

### 🟢 COMMIT 4: Service Layer (Pure)
**Goal**: Core logic without external deps.
```
server/app/services/
 └── video_file_pipeline_service.py (NEW: Logic)
server/app/tests/video/fakes/
 └── mock_dag_service.py            (NEW: Mock)
server/app/tests/video/
 └── test_video_service_unit.py     (NEW: 15+ unit tests)
```
*Verification*: Unit tests pass (100% coverage of service).

---

### 🟢 COMMIT 5: Router & Wiring
**Goal**: Expose HTTP endpoint.
```
server/app/api/routes/
 └── video_file.py                  (NEW: POST /upload-and-run)
server/app/main.py                  (UPDATE: include_router)
server/app/tests/video/
 └── test_video_router_registered.py(NEW)
```
*Verification*: Endpoint appears in `app.routes`.

---

### 🟢 COMMIT 6: Integration & Errors
**Goal**: End-to-end correctness.
```
server/app/tests/video/
 ├── test_video_upload_and_run.py        (NEW: Happy path)
 ├── test_video_error_invalid_type.py    (NEW: 400)
 ├── test_video_error_pipeline_404.py    (NEW: 404)
 ├── test_video_error_corrupt_file.py    (NEW: 400)
 └── test_video_error_missing_fields.py  (NEW: 422)
```
*Verification*: Integration tests pass with real router + mock DAG.

---

### 🟢 COMMIT 7: Regression Guards
**Goal**: Freeze API contract.
```
server/app/tests/video/golden/
 └── golden_output.json                  (NEW)
server/app/tests/video/
 ├── test_video_schema_regression.py     (NEW: Keys check)
 └── test_video_golden_snapshot.py       (NEW: Snapshot check)
```
*Verification*: Snapshot matches exact JSON output.

---

### 🟢 COMMIT 8: Hardening
**Goal**: Reliability.
```
server/app/tests/video/stress/
 └── test_video_service_1000_frames.py   (NEW)
server/app/tests/video/fuzz/
 └── test_video_service_mp4_fuzz.py      (NEW: Malformed inputs)
```
*Verification*: Stress test < 30s, Fuzz tests don't crash.

---

### 🟢 COMMIT 9: Governance
**Goal**: Prevent Phase 16 creep.
```
server/tools/
 ├── forbidden_vocabulary.yaml           (NEW: Regex list)
 └── validate_video_batch_path.py        (NEW: Scanner)
.github/workflows/
 └── video_batch_validation.yml          (NEW: CI)
scripts/
 └── smoke_test_video_batch.sh           (NEW: Dev tool)
```
*Verification*: CI passes, smoke test passes.

---

### 🟢 COMMIT 10: Documentation
**Goal**: Handoff.
```
scripts/
 └── demo_video_yolo_ocr.sh              (NEW)
.ampcode/04_PHASE_NOTES/Phase_15/
 ├── PHASE_15_TESTING_GUIDE.md           (NEW)
 ├── PHASE_15_ROLLBACK.md                (NEW)
 ├── PHASE_15_MIGRATION_GUIDE.md         (UPDATE)
 ├── PHASE_15_ARCHITECTURE.mmd           (NEW)
 └── ... (Release notes, etc.)
```
*Verification*: Docs exist, demo script runs.

---