# Phase 15 Progress Tracking

**Last Updated**: 2026-02-13  
**Status**: Ready for Implementation  
**Timeline**: 20-25 hours (10 commits)

---

## Overview

Phase 15 extends Phase 14's single-frame DAG execution to support **offline MP4 processing** using **YOLO + OCR** pipeline only.

**See PHASE_15_PLANS.md for detailed implementation requirements per commit.**

---

## 🔴 MANDATORY Pre-Commit Verification (GATES - ALL MUST BE GREEN BEFORE ANY COMMIT)

### Test Suite Requirements

**ALL 4 suites must be GREEN before committing ANYTHING.**

1. **Server Tests**: `uv run pytest tests/` (all tests pass)
2. **Web-UI Tests**: `npm run test -- --run` (all tests pass)
3. **Execution Governance**: `python scripts/scan_execution_violations.py` (passes)
4. **Plugin/Pipeline Validators**: `python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py` (both pass)

### Failure Policy

- **CRITICAL: NO COMMITS until ALL 4 test suites are GREEN**
- **ANY test failure** = Stop immediately, fix failure, re-run all 4 suites
- **Failure to run tests before commit** = Automatic rollback

---

## Pre-Implementation Baseline

- [x] Verify all server tests pass (GREEN)
- [x] Verify all web-ui tests pass (GREEN)
- [x] Verify execution-ci workflow passes (GREEN)
- [x] Verify governance-ci workflow passes (GREEN)
- [x] Check Phase 14 completion status

---

## 10-Commit Implementation Progress

Each commit maps 1:1 to **PHASE_15_USER_STORIES.md** for complete acceptance criteria.

---

### COMMIT 1: Pipeline Definition ⏳ NOT STARTED
**User Story**: Define `yolo_ocr` pipeline (YOLO→OCR DAG)

**Files**:
- `server/app/pipelines/yolo_ocr.json` (CREATE)

**Acceptance Criteria**:
- [ ] File exists with 2 nodes: `detect` (yolo.detect_objects), `read` (ocr.extract_text)
- [ ] Exactly 1 edge: detect→read
- [ ] entry_nodes: ["detect"], output_nodes: ["read"]
- [ ] Validator passes: `uv run python server/tools/validate_pipelines.py`
- [ ] No other pipelines modified

**Test Verification** (MUST BE GREEN):
```bash
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py
```

**Status**: ⬜ TODO

---

### COMMIT 2: Payload Contract & Scope Rewrite ⏳ NOT STARTED
**User Story**: Lock payload contract, rewrite OVERVIEW to batch-only scope

**Files**:
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_PAYLOAD_YOLO_OCR.md` (CREATE)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_SCOPE.md` (UPDATE)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_OVERVIEW.md` (REWRITE)

**Acceptance Criteria**:
- [ ] Payload doc specifies: `frame_index` (int), `image_bytes` (raw JPEG bytes)
- [ ] Payload doc states: "Do NOT use base64 encoding"
- [ ] Response schema frozen: `{"results": [{"frame_index", "result"}]}`
- [ ] SCOPE.md lists forbidden items: job queue, persistence, tracking, async, streaming
- [ ] OVERVIEW.md rewritten for batch-only scope
- [ ] OVERVIEW.md does NOT mention: job queue, Redis, RabbitMQ, worker, streaming, WebSocket, database, job status, progress polling

**Test Verification** (MUST BE GREEN):
```bash
grep -i -E "job_id|queue|worker|redis|rabbitmq|celery|websocket|streaming|database|sql|postgres" \
  .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_OVERVIEW.md && echo "FAIL" || echo "OK"
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py
```

**Status**: ⬜ TODO

---

### COMMIT 3: OpenCV + Fixtures + Corrupt Harness ⏳ NOT STARTED
**User Story**: Add opencv-python dep, generate tiny.mp4 fixture, create corrupted MP4 generator

**Files**:
- `server/pyproject.toml` (MODIFY)
- `server/app/tests/fixtures/generate_tiny_mp4.py` (CREATE)
- `server/app/tests/fixtures/tiny.mp4` (CREATE - binary)
- `server/app/tests/video/__init__.py` (CREATE)
- `server/app/tests/video/fakes/__init__.py` (CREATE)
- `server/app/tests/video/fakes/corrupt_mp4_generator.py` (CREATE)

**Acceptance Criteria**:
- [ ] opencv-python-headless added to dependencies
- [ ] generate_tiny_mp4.py exists and generates 3-frame MP4 (320×240)
- [ ] tiny.mp4 committed (not generated at test time)
- [ ] corrupt_mp4_generator.py creates fake header + invalid data
- [ ] OpenCV VideoCapture fails on corrupted file (isOpened() == False)
- [ ] All existing tests still pass

**Test Verification** (MUST BE GREEN):
```bash
python -c "
import cv2
cap = cv2.VideoCapture('server/app/tests/fixtures/tiny.mp4')
count = 0
while cap.read()[0]: count += 1
cap.release()
assert count == 3, f'Expected 3 frames, got {count}'
print('OK: 3 frames')
"
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py
```

**Status**: ⬜ TODO

---

### COMMIT 4: VideoFilePipelineService + Mock DAG + Unit Tests ⏳ NOT STARTED
**User Story**: Implement service layer with pure unit tests (no real plugins)

**Files**:
- `server/app/services/video_file_pipeline_service.py` (CREATE)
- `server/app/tests/video/fakes/mock_dag_service.py` (CREATE)
- `server/app/tests/video/test_video_service_unit.py` (CREATE)

**Acceptance Criteria**:
- [ ] VideoFilePipelineService class with run_on_file() method
- [ ] Frame extraction using OpenCV, JPEG encoding
- [ ] Payload: {frame_index: int, image_bytes: bytes}
- [ ] DAG calls per frame via dag_service.run_pipeline()
- [ ] Supports frame_stride and max_frames options
- [ ] Raises ValueError("Unable to read video file") on OpenCV failure
- [ ] cap.release() in finally block (no leaks)
- [ ] MockDagPipelineService with fail_mode support (None, "pipeline_not_found", "plugin_error")
- [ ] 15+ unit tests covering: stride, max_frames, error cases, payload validation
- [ ] Tests use only mock DAG (no real plugins)

**Test Verification** (MUST BE GREEN):
```bash
uv run pytest server/app/tests/video/test_video_service_unit.py -v
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py
```

**Status**: ⬜ TODO

---

### COMMIT 5: Router + App Wiring + Registration Test ⏳ NOT STARTED
**User Story**: Create API endpoint, wire into FastAPI app

**Files**:
- `server/app/api/routes/video_file.py` (CREATE)
- `server/app/main.py` (MODIFY)
- `server/app/tests/video/test_video_route_registration.py` (CREATE)

**Acceptance Criteria**:
- [ ] POST /video/upload-and-run endpoint exists
- [ ] Accepts multipart/form-data: file (MP4), pipeline_id
- [ ] Validates content-type (video/mp4, video/quicktime)
- [ ] Returns {results: [{frame_index, result}]} (frozen schema)
- [ ] 404 for invalid pipeline_id
- [ ] 400 for invalid file type / corrupted MP4
- [ ] 422 for missing form fields
- [ ] server/app/main.py includes video_file.router with prefix /video
- [ ] Registration test verifies endpoint exists and is callable

**Test Verification** (MUST BE GREEN):
```bash
uv run pytest server/app/tests/video/test_video_route_registration.py -v
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py
```

**Status**: ⬜ TODO

---

### COMMIT 6: Integration Tests + Full Error Coverage ⏳ NOT STARTED
**User Story**: Integration tests for happy path + 5 error scenarios

**Files**:
- `server/app/tests/video/test_video_upload_and_run.py` (CREATE)
- `server/app/tests/video/test_video_error_pipeline_not_found.py` (CREATE)
- `server/app/tests/video/test_video_error_invalid_file_type.py` (CREATE)
- `server/app/tests/video/test_video_error_missing_fields.py` (CREATE)
- `server/app/tests/video/test_video_error_corrupted_mp4.py` (CREATE)

**Acceptance Criteria**:
- [ ] Happy path: Valid MP4 + yolo_ocr pipeline → 200 OK
- [ ] Response contains "results" key with list of {frame_index, result}
- [ ] At least 1 frame processed
- [ ] Error: Invalid pipeline_id → 404
- [ ] Error: Non-MP4 file → 400
- [ ] Error: Missing pipeline_id field → 422
- [ ] Error: Missing file field → 422
- [ ] Error: Corrupted MP4 → 400

**Test Verification** (MUST BE GREEN):
```bash
uv run pytest server/app/tests/video/test_video_*.py -v
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py
```

**Status**: ⬜ TODO

---

### COMMIT 7: Schema Regression Guard + Golden Snapshot ⏳ NOT STARTED
**User Story**: Freeze response schema, add golden snapshot regression test

**Files**:
- `server/app/tests/video/test_video_schema_regression.py` (CREATE)
- `server/app/tests/video/golden/__init__.py` (CREATE)
- `server/app/tests/video/golden/golden_output.json` (CREATE)
- `server/app/tests/video/test_video_golden_snapshot.py` (CREATE)

**Acceptance Criteria**:
- [ ] Schema regression test asserts top-level keys only: ["results"]
- [ ] Schema test asserts item keys only: ["frame_index", "result"]
- [ ] No extra fields allowed (metadata, status, job_id, etc.)
- [ ] golden_output.json created with mock DAG output (tiny.mp4 + yolo_ocr)
- [ ] Golden snapshot test verifies deterministic behavior
- [ ] Snapshot regeneration procedure documented
- [ ] Snapshot does NOT depend on system time, random values, or environment

**Test Verification** (MUST BE GREEN):
```bash
uv run pytest server/app/tests/video/test_video_schema_regression.py -v
uv run pytest server/app/tests/video/test_video_golden_snapshot.py -v
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py
```

**Status**: ⬜ TODO

---

### COMMIT 8: Stress + Fuzz Test Suites ⏳ NOT STARTED
**User Story**: 1000-frame stress test + 4+ fuzz cases (malformed MP4)

**Files**:
- `server/app/tests/video/stress/__init__.py` (CREATE)
- `server/app/tests/video/stress/test_video_service_1000_frames.py` (CREATE)
- `server/app/tests/video/fuzz/__init__.py` (CREATE)
- `server/app/tests/video/fuzz/test_video_service_mp4_fuzz.py` (CREATE)

**Acceptance Criteria**:
- [ ] Stress test generates 1000-frame MP4 in tmp_path
- [ ] Process with MockDagPipelineService (no real plugins)
- [ ] Assert len(results) == 1000
- [ ] Assert results[0]["frame_index"] == 0
- [ ] Assert results[-1]["frame_index"] == 999
- [ ] Assert all indices sequential, no gaps, no duplicates
- [ ] Passes within 30 seconds
- [ ] Fuzz test covers 4+ cases: random bytes (128B, 1KB), header-only MP4, truncated MP4
- [ ] For each fuzz case: returns 0 results OR raises ValueError (never crash/hang)
- [ ] Deterministic or fixed-seed inputs (no flaky tests)

**Test Verification** (MUST BE GREEN):
```bash
uv run pytest server/app/tests/video/stress/ -v
uv run pytest server/app/tests/video/fuzz/ -v
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py
```

**Status**: ⬜ TODO

---

### COMMIT 9: Governance Tooling + CI + Smoke Test ⏳ NOT STARTED
**User Story**: Add forbidden vocabulary validator, CI enforcement, smoke test script

**Files**:
- `server/tools/forbidden_vocabulary.yaml` (CREATE)
- `server/tools/validate_video_batch_path.py` (CREATE)
- `.github/workflows/video_batch_validation.yml` (CREATE)
- `scripts/smoke_test_video_batch.sh` (CREATE - executable)

**Acceptance Criteria**:
- [ ] forbidden_vocabulary.yaml contains regex patterns for: job_id, queue, worker, celery, rq, redis, rabbitmq, database, sql, postgres, mongodb, insert_one, update_one, reid, tracking, track_ids, metrics, execution_time_ms, websocket, streaming
- [ ] Patterns use word boundaries (\b)
- [ ] validate_video_batch_path.py loads terms from YAML (not hardcoded)
- [ ] Scans video-related functional files
- [ ] Scans for phase-named files (phase15, phase_15, phase-15) in server/app/, server/tools/
- [ ] Exits 0 on pass, 1 on violation
- [ ] Currently passes with zero violations
- [ ] CI workflow: .github/workflows/video_batch_validation.yml
- [ ] Triggers on PRs to main that touch server/**, scripts/**, or server/tools/**
- [ ] Runs in order: validate_plugins → validate_pipelines → validate_video_batch_path → pytest
- [ ] smoke_test_video_batch.sh is executable (chmod +x)
- [ ] Runs 4 steps: validate_plugins → validate_pipelines → validate_video_batch_path → pytest video tests
- [ ] Uses set -e to exit on first failure
- [ ] Prints clear pass message at end

**Test Verification** (MUST BE GREEN):
```bash
uv run python server/tools/validate_video_batch_path.py
chmod +x scripts/smoke_test_video_batch.sh
./scripts/smoke_test_video_batch.sh
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py
```

**Status**: ⬜ TODO

---

### COMMIT 10: Documentation + Demo Script + Rollback Plan ⏳ NOT STARTED
**User Story**: Complete onboarding, demo script, formal rollback plan

**Files**:
- `scripts/demo_video_yolo_ocr.sh` (CREATE - executable)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_TESTING_GUIDE.md` (CREATE)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ROLLBACK.md` (CREATE)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_MIGRATION_GUIDE.md` (UPDATE)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_RELEASE_NOTES.md` (UPDATE)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ONBOARDING.md` (UPDATE)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ARCHITECTURE.txt` (CREATE)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ARCHITECTURE.mmd` (CREATE)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_GOVERNANCE.md` (UPDATE)

**Acceptance Criteria**:
- [ ] demo_video_yolo_ocr.sh executable (chmod +x)
- [ ] Calls POST /video/upload-and-run with tiny.mp4 + yolo_ocr
- [ ] Prints first frame result as formatted JSON
- [ ] Works against running local server (http://localhost:8000)
- [ ] PHASE_15_ROLLBACK.md lists exact files to remove and modifications to revert
- [ ] PHASE_15_TESTING_GUIDE.md documents all test procedures
- [ ] PHASE_15_MIGRATION_GUIDE.md matches batch-only scope
- [ ] PHASE_15_RELEASE_NOTES.md accurate file list + test counts
- [ ] PHASE_15_ONBOARDING.md does NOT reference job queues, streaming, persistence
- [ ] PHASE_15_ARCHITECTURE.txt (ASCII diagram)
- [ ] PHASE_15_ARCHITECTURE.mmd (Mermaid diagram)
- [ ] PHASE_15_GOVERNANCE.md lists forbidden vocabulary + placement rules
- [ ] All docs in .ampcode/04_PHASE_NOTES/Phase_15/ (not in functional dirs)

**Test Verification** (MUST BE GREEN):
```bash
grep -r -i -E "job_id|queue|worker|redis|websocket|streaming|database|postgres|celery" \
  .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ONBOARDING.md \
  .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_MIGRATION_GUIDE.md \
  .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_OVERVIEW.md \
  && echo "FAIL" || echo "OK"
test -x scripts/demo_video_yolo_ocr.sh && echo "OK" || echo "FAIL"
uv run pytest -q
./scripts/smoke_test_video_batch.sh
```

**Status**: ⬜ TODO

---

## 📋 Governance Rules (Non-Negotiable)

1. **No phase-named files in functional directories** — Use `video/`, not `phase15/`
2. **No job queue** — Synchronous processing only
3. **No async workers** — Blocking execution
4. **No persistence** — No database writes
5. **No tracking/ReID** — Stateless per frame
6. **No streaming** — Batch processing only
7. **No state across frames** — Each frame independent
8. **Payload must have**: `frame_index` (int) + `image_bytes` (raw JPEG, not base64)
9. **Response schema frozen**: `{results: [{frame_index, result}]}` — no extra fields
10. **All 4 test suites GREEN** before every commit

---

## ✅ Post-Implementation Verification

After all 10 commits:

```bash
# Re-run ALL 4 test suites
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py

# Run phase-15 specific tests
uv run pytest server/app/tests/video/ -v

# Run smoke test
./scripts/smoke_test_video_batch.sh

# Verify demo works (requires running server on port 8000)
./scripts/demo_video_yolo_ocr.sh
```

---

## Definition of Done Checklist

- [ ] All 10 commits pushed to feature/phase-15-job-queuing branch
- [ ] ALL 4 test suites GREEN after every commit
- [ ] POST /video/upload-and-run accepts MP4 files ✅
- [ ] Rejects invalid file types ✅
- [ ] OpenCV opens MP4 successfully ✅
- [ ] Frames extracted sequentially ✅
- [ ] DAG executes YOLO → OCR per frame ✅
- [ ] Response contains aggregated results ✅
- [ ] No job queue, async, persistence, tracking ✅
- [ ] No streaming, ReID, Viz ✅
- [ ] Tiny MP4 fixture exists (3 frames, 320×240) ✅
- [ ] Unit tests pass (15+ tests) ✅
- [ ] Integration tests pass (happy path + 5 error cases) ✅
- [ ] Stress test passes (1000 frames) ✅
- [ ] Fuzz test passes (4+ malformed cases) ✅
- [ ] Smoke test passes ✅
- [ ] Governance validator passes (zero violations) ✅
- [ ] ZERO skipped tests (or with explicit APPROVED comments) ✅

---

## Notes

- Phase 15 is intentionally scoped to **YOLO + OCR only** (offline MP4 processing)
- No job queue, persistence, or tracking in this phase
- All governance boundaries must be respected
- **CRITICAL**: NO COMMITS until ALL 4 test suites are GREEN
- **CRITICAL**: ANY test failure requires immediate fix
- **CRITICAL**: Failure to run the tests = Immediate termination
- See **PHASE_15_PLANS.md** for detailed implementation requirements per commit
- See **PHASE_15_USER_STORIES.md** for complete acceptance criteria