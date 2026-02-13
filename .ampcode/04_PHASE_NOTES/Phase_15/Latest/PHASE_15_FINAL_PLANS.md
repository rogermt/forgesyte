# ⭐ Phase 15 — Final Implementation Plans

**Last Updated**: 2026-02-13  
**Status**: Ready for Implementation  
**Timeline**: 20-25 hours (10 commits)

--- 

## Overview

Phase 15 extends Phase 14's single-frame DAG execution to support **offline MP4 processing** using **YOLO + OCR** pipeline only.

**Theme**: "Offline video file processing through named DAG pipelines."

## Scope

- **IN**: MP4 upload, frame extraction, YOLO→OCR DAG per frame, aggregated results
- **OUT**: Job queue, persistence, tracking, ReID, Viz, streaming, async workers

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

## 10-Commit Implementation Plan

**Each commit maps 1:1 to PHASE_15_USER_STORIES.md.**  
**See PHASE_15_USER_STORIES.md for complete acceptance criteria.**

--- 

### COMMIT 1: Pipeline Definition
**Story**: Define `yolo_ocr` pipeline (YOLO→OCR DAG)

**Files to Create/Modify**:
- `server/app/pipelines/yolo_ocr.json` (CREATE)

**Acceptance Criteria** (from Story 1):
- [ ] File exists with 2 nodes: `detect` (yolo.detect_objects), `read` (ocr.extract_text)
- [ ] Exactly 1 edge: detect→read
- [ ] entry_nodes: ["detect"], output_nodes: ["read"]
- [ ] Validator passes: `uv run python server/tools/validate_pipelines.py`
- [ ] No other pipelines modified

**Pre-Commit Test Verification**:
```bash
# Run ALL 4 test suites
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py
```

**DO NOT**:
- Reference reid, track_ids, detect_players, or non-existent plugins
- Add `server/app/pipelines/phase15_pipeline.json` (no phase names in functional dirs)
- Modify other pipelines

**Git Commands**:
```bash
git add server/app/pipelines/yolo_ocr.json
git commit -m "phase15: add yolo_ocr pipeline definition (YOLO → OCR)"
```

--- 

### COMMIT 2: Payload Contract & Scope Rewrite
**Story**: Lock payload contract, rewrite OVERVIEW to batch-only scope

**Files to Create/Modify**:
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_PAYLOAD_YOLO_OCR.md` (CREATE)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_SCOPE.md` (UPDATE)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_OVERVIEW.md` (REWRITE)

**Acceptance Criteria** (from Story 2):
- [ ] Payload doc specifies: `frame_index` (int), `image_bytes` (raw JPEG bytes)
- [ ] Payload doc states: "Do NOT use base64 encoding"
- [ ] Response schema frozen: `{"results": [{"frame_index", "result"}]}`
- [ ] SCOPE.md lists forbidden items: job queue, persistence, tracking, async, streaming
- [ ] OVERVIEW.md rewritten for batch-only scope
- [ ] OVERVIEW.md does NOT mention: job queue, Redis, RabbitMQ, worker, streaming, WebSocket, database, job status, progress polling

**Pre-Commit Test Verification**:
```bash
# Verify no forbidden concepts in OVERVIEW
grep -i -E "job_id|queue|worker|redis|rabbitmq|celery|websocket|streaming|database|sql|postgres" \
  .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_OVERVIEW.md && echo "FAIL" || echo "OK"

# Run ALL 4 test suites
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py
```

**DO NOT**:
- Put payload contract in docs/ (belongs in .ampcode/04_PHASE_NOTES/Phase_15/)
- Leave old OVERVIEW.md with job queue references
- Add execution_time_ms, status, or metadata to payload contract

**Git Commands**:
```bash
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_PAYLOAD_YOLO_OCR.md
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_SCOPE.md
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_OVERVIEW.md
git commit -m "phase15: lock payload contract and rewrite overview to batch-only scope"
```

--- 

### COMMIT 3: OpenCV Dependency + Test Fixtures + Corrupt Harness
**Story**: Add opencv-python dep, generate tiny.mp4 fixture, create corrupted MP4 generator

**Files to Create/Modify**:
- `server/pyproject.toml` (MODIFY - add opencv-python-headless)
- `server/app/tests/fixtures/generate_tiny_mp4.py` (CREATE)
- `server/app/tests/fixtures/tiny.mp4` (CREATE - binary, committed)
- `server/app/tests/video/__init__.py` (CREATE - empty)
- `server/app/tests/video/fakes/__init__.py` (CREATE - empty)
- `server/app/tests/video/fakes/corrupt_mp4_generator.py` (CREATE)

**Acceptance Criteria** (from Story 3):
- [ ] opencv-python-headless added to dependencies
- [ ] generate_tiny_mp4.py exists and generates 3-frame MP4 (320×240)
- [ ] tiny.mp4 committed (not generated at test time)
- [ ] corrupt_mp4_generator.py creates fake header + invalid data
- [ ] OpenCV VideoCapture fails on corrupted file (isOpened() == False)
- [ ] All existing tests still pass

**Pre-Commit Test Verification**:
```bash
# Verify tiny.mp4 has 3 frames
python -c "
import cv2
cap = cv2.VideoCapture('server/app/tests/fixtures/tiny.mp4')
count = 0
while cap.read()[0]: count += 1
cap.release()
assert count == 3, f'Expected 3 frames, got {count}'
print('OK: 3 frames')
"

# Verify corrupt file fails
python -c "
from server.app.tests.video.fakes.corrupt_mp4_generator import generate_corrupted_mp4
from pathlib import Path
import cv2, tempfile
p = Path(tempfile.mktemp(suffix='.mp4'))
generate_corrupted_mp4(p)
cap = cv2.VideoCapture(str(p))
assert not cap.isOpened(), 'Corrupt file should not open'
cap.release()
p.unlink()
print('OK: corrupt mp4 rejected')
"

# Run ALL 4 test suites
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py
```

**DO NOT**:
- Use opencv-python with GUI on CI (use headless)
- Generate tiny.mp4 dynamically (commit it)
- Use phase-named directories (video/ not phase15/)
- Use random bytes for corrupt generator

**Git Commands**:
```bash
git add server/pyproject.toml
git add server/app/tests/fixtures/generate_tiny_mp4.py
git add server/app/tests/fixtures/tiny.mp4
git add server/app/tests/video/__init__.py
git add server/app/tests/video/fakes/__init__.py
git add server/app/tests/video/fakes/corrupt_mp4_generator.py
git commit -m "phase15: add opencv dep, tiny mp4 fixture, and corrupted mp4 generator"
```

--- 

### COMMIT 4: VideoFilePipelineService + Mock DAG + Pure Unit Tests
**Story**: Implement service layer with pure unit tests (no real plugins)

**Files to Create**:
- `server/app/services/video_file_pipeline_service.py` (CREATE)
- `server/app/tests/video/fakes/mock_dag_service.py` (CREATE)
- `server/app/tests/video/test_video_service_unit.py` (CREATE)

**Acceptance Criteria** (from Story 4):

*Service*:
- [ ] Constructor accepts dag_service, optional frame_stride (default 1), optional max_frames (default None)
- [ ] run_on_file(pipeline_id, file_path, options) returns list of {frame_index, result}
- [ ] Raises ValueError("Unable to read video file") if OpenCV cannot open
- [ ] Encodes frames as JPEG raw bytes via cv2.imencode(".jpg", frame)
- [ ] Payload per frame: {frame_index: int, image_bytes: bytes}
- [ ] Calls dag_service.run_pipeline(pipeline_id, payload) per frame
- [ ] Respects frame_stride (only process frames where index % stride == 0)
- [ ] Respects max_frames (stops after N processed frames)
- [ ] stride <= 0 treated as 1
- [ ] cap.release() called in finally block (never leaked)

*Mock DAG*:
- [ ] mock_dag_service.py exists at server/app/tests/video/fakes/
- [ ] Supports fail_mode: None (success), "pipeline_not_found", "plugin_error"
- [ ] Records all calls in self.calls for assertions
- [ ] "pipeline_not_found" raises FileNotFoundError("Pipeline not found")
- [ ] "plugin_error" raises RuntimeError("Plugin execution failed")

*Unit Tests*:
- [ ] 15+ tests covering: stride variants, max_frames, error cases, payload validation
- [ ] Tests use MockDagPipelineService (never real plugins)
- [ ] Test: tiny.mp4 (3 frames) → 3 results [0,1,2]
- [ ] Test: stride=2 → 2 results [0,2]
- [ ] Test: stride=3 → 1 result [0]
- [ ] Test: stride=0 treated as stride=1 → 3 results
- [ ] Test: max_frames=1 → 1 result
- [ ] Test: max_frames=2 → 2 results
- [ ] Test: nonexistent file → ValueError
- [ ] Test: corrupted MP4 → ValueError("Unable to read video file")
- [ ] Test: mock fail_mode="pipeline_not_found" → FileNotFoundError
- [ ] Test: payload contains frame_index (int), image_bytes (bytes)
- [ ] Test: mock.calls length matches processed frames

**Pre-Commit Test Verification**:
```bash
# Run video service unit tests
uv run pytest server/app/tests/video/test_video_service_unit.py -v

# Run ALL 4 test suites
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py
```

**DO NOT**:
- Use real YOLO/OCR plugins in tests
- Skip payload type validation
- Forget cap.release() in finally block

**Git Commands**:
```bash
git add server/app/services/video_file_pipeline_service.py
git add server/app/tests/video/fakes/mock_dag_service.py
git add server/app/tests/video/test_video_service_unit.py
git commit -m "phase15: implement VideoFilePipelineService with pure unit tests and mock DAG"
```

--- 

### COMMIT 5: Router + App Wiring + Registration Test
**Story**: Create API endpoint, wire into FastAPI app

**Files to Create/Modify**:
- `server/app/api/routes/video_file.py` (CREATE)
- `server/app/main.py` (MODIFY - include router)
- `server/app/tests/video/test_video_route_registration.py` (CREATE)

**Acceptance Criteria** (from Story 5):

*Router*:
- [ ] POST /video/upload-and-run endpoint exists
- [ ] Accepts multipart/form-data: file (MP4), pipeline_id
- [ ] Validates content-type (video/mp4, video/quicktime)
- [ ] Manages temp file storage
- [ ] Returns {results: [{frame_index, result}]} (frozen schema)
- [ ] 404 for invalid pipeline_id
- [ ] 400 for invalid file type / corrupted MP4
- [ ] 422 for missing form fields

*App Wiring*:
- [ ] server/app/main.py includes video_file.router
- [ ] Router prefix: /video
- [ ] Tags: ["video"]

*Registration Test*:
- [ ] Test verifies endpoint exists and is callable
- [ ] Test does NOT call real plugins

**Pre-Commit Test Verification**:
```bash
# Run registration test
uv run pytest server/app/tests/video/test_video_route_registration.py -v

# Run ALL 4 test suites
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py
```

**DO NOT**:
- Hardcode file paths (use pathlib)
- Forget error handling (404, 400, 422)
- Use blocking I/O without proper async/await

**Git Commands**:
```bash
git add server/app/api/routes/video_file.py
git add server/app/main.py
git add server/app/tests/video/test_video_route_registration.py
git commit -m "phase15: add video upload router and FastAPI app wiring"
```

--- 

### COMMIT 6: Integration Tests + Full Error Coverage
**Story**: Integration tests for happy path + 5 error scenarios

**Files to Create**:
- `server/app/tests/video/test_video_upload_and_run.py` (CREATE)
- `server/app/tests/video/test_video_error_pipeline_not_found.py` (CREATE)
- `server/app/tests/video/test_video_error_invalid_file_type.py` (CREATE)
- `server/app/tests/video/test_video_error_missing_fields.py` (CREATE)
- `server/app/tests/video/test_video_error_corrupted_mp4.py` (CREATE)

**Acceptance Criteria** (from Story 6):

*Happy Path*:
- [ ] Valid MP4 + yolo_ocr pipeline → 200 OK
- [ ] Response contains "results" key
- [ ] results is list of {frame_index, result}
- [ ] At least 1 frame processed

*Error Cases*:
- [ ] Invalid pipeline_id → 404 FileNotFoundError
- [ ] Non-MP4 file → 400 Bad Request
- [ ] Missing pipeline_id field → 422 Unprocessable Entity
- [ ] Missing file field → 422 Unprocessable Entity
- [ ] Corrupted MP4 → 400 Bad Request

**Pre-Commit Test Verification**:
```bash
# Run all integration tests
uv run pytest server/app/tests/video/test_video_*.py -v

# Run ALL 4 test suites
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py
```

**DO NOT**:
- Mock the response (use real service + mock DAG)
- Skip any error scenario
- Use real plugins

**Git Commands**:
```bash
git add server/app/tests/video/test_video_upload_and_run.py
git add server/app/tests/video/test_video_error_pipeline_not_found.py
git add server/app/tests/video/test_video_error_invalid_file_type.py
git add server/app/tests/video/test_video_error_missing_fields.py
git add server/app/tests/video/test_video_error_corrupted_mp4.py
git commit -m "phase15: add integration tests with full error coverage"
```

--- 

### COMMIT 7: Schema Regression Guard + Golden Snapshot
**Story**: Freeze response schema, add golden snapshot regression test

**Files to Create**:
- `server/app/tests/video/test_video_schema_regression.py` (CREATE)
- `server/app/tests/video/golden/__init__.py` (CREATE - empty)
- `server/app/tests/video/golden/golden_output.json` (CREATE)
- `server/app/tests/video/test_video_golden_snapshot.py` (CREATE)

**Acceptance Criteria** (from Story 7):

*Schema Regression Test*:
- [ ] Assert top-level keys only: ["results"]
- [ ] Assert item keys only: ["frame_index", "result"]
- [ ] No extra fields (metadata, status, job_id, etc.)

*Golden Snapshot*:
- [ ] golden_output.json created with mock DAG output (tiny.mp4 + yolo_ocr)
- [ ] Test verifies deterministic behavior
- [ ] Snapshot regeneration procedure documented (see docstring)
- [ ] Snapshot does NOT depend on system time, random values, or environment

**Pre-Commit Test Verification**:
```bash
# Run schema and golden tests
uv run pytest server/app/tests/video/test_video_schema_regression.py -v
uv run pytest server/app/tests/video/test_video_golden_snapshot.py -v

# Run ALL 4 test suites
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py
```

**DO NOT**:
- Generate golden_output.json with real YOLO/OCR (use mock DAG)
- Add pipeline_id, status, execution_time_ms to golden output
- Skip documenting regeneration rule

**Git Commands**:
```bash
git add server/app/tests/video/test_video_schema_regression.py
git add server/app/tests/video/golden/__init__.py
git add server/app/tests/video/golden/golden_output.json
git add server/app/tests/video/test_video_golden_snapshot.py
git commit -m "phase15: freeze response schema and add golden snapshot regression test"
```

--- 

### COMMIT 8: Stress + Fuzz Test Suites
**Story**: 1000-frame stress test + 4+ fuzz cases (malformed MP4)

**Files to Create**:
- `server/app/tests/video/stress/__init__.py` (CREATE - empty)
- `server/app/tests/video/stress/test_video_service_1000_frames.py` (CREATE)
- `server/app/tests/video/fuzz/__init__.py` (CREATE - empty)
- `server/app/tests/video/fuzz/test_video_service_mp4_fuzz.py` (CREATE)

**Acceptance Criteria** (from Story 8):

*Stress Test*:
- [ ] Generate 1000-frame MP4 in tmp_path
- [ ] Process with MockDagPipelineService
- [ ] Assert len(results) == 1000
- [ ] Assert results[0]["frame_index"] == 0
- [ ] Assert results[-1]["frame_index"] == 999
- [ ] Assert all indices sequential, no gaps, no duplicates
- [ ] Passes within 30 seconds

*Fuzz Test*:
- [ ] Test 4+ cases: random bytes (128B, 1KB), header-only MP4, truncated MP4
- [ ] For each case: returns 0 results OR raises ValueError (never crash/hang)
- [ ] Use MockDagPipelineService
- [ ] Deterministic or fixed-seed inputs (no flaky tests)

**Pre-Commit Test Verification**:
```bash
# Run stress tests
uv run pytest server/app/tests/video/stress/ -v

# Run fuzz tests
uv run pytest server/app/tests/video/fuzz/ -v

# Run ALL 4 test suites
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py
```

**DO NOT**:
- Use real YOLO/OCR plugins
- Use non-deterministic random seeds
- Allow unhandled exception types other than ValueError
- Skip sequential-index assertion

**Git Commands**:
```bash
git add server/app/tests/video/stress/__init__.py
git add server/app/tests/video/stress/test_video_service_1000_frames.py
git add server/app/tests/video/fuzz/__init__.py
git add server/app/tests/video/fuzz/test_video_service_mp4_fuzz.py
git commit -m "phase15: add 1000-frame stress test and mp4 fuzz test suite"
```

--- 

### COMMIT 9: Governance Tooling + CI + Smoke Test
**Story**: Add forbidden vocabulary validator, CI enforcement, smoke test script

**Files to Create/Modify**:
- `server/tools/forbidden_vocabulary.yaml` (CREATE)
- `server/tools/validate_video_batch_path.py` (CREATE)
- `.github/workflows/video_batch_validation.yml` (CREATE)
- `scripts/smoke_test_video_batch.sh` (CREATE - executable)

**Acceptance Criteria** (from Story 9):

*Forbidden Vocabulary YAML*:
- [ ] Regex patterns for: job_id, queue, worker, celery, rq, redis, rabbitmq, database, sql, postgres, mongodb, insert_one, update_one, reid, tracking, track_ids, metrics, execution_time_ms, websocket, streaming
- [ ] Patterns use word boundaries (\b)

*Path Validator Script*:
- [ ] Loads terms from forbidden_vocabulary.yaml (not hardcoded)
- [ ] Scans video-related functional files
- [ ] Scans for phase-named files (phase15, phase_15, phase-15) in server/app/, server/tools/
- [ ] Exits 0 on pass, 1 on violation
- [ ] Currently passes with zero violations on all Phase-15 code

*CI Workflow*:
- [ ] Triggers on PRs to main that touch server/**, scripts/**, or server/tools/**
- [ ] Runs in order: validate_plugins → validate_pipelines → validate_video_batch_path → pytest (full suite)
- [ ] File: .github/workflows/video_batch_validation.yml

*Smoke Test Script*:
- [ ] scripts/smoke_test_video_batch.sh (executable, chmod +x)
- [ ] Runs exactly these 4 steps in order:
  1. uv run python server/tools/validate_plugins.py
  2. uv run python server/tools/validate_pipelines.py
  3. uv run python server/tools/validate_video_batch_path.py
  4. uv run pytest server/app/tests/video -q --maxfail=1
- [ ] Uses set -e to exit on first failure
- [ ] Prints clear pass message at end
- [ ] Exits 0 only if all 4 steps pass

**Pre-Commit Test Verification**:
```bash
# Run validator
uv run python server/tools/validate_video_batch_path.py

# Make smoke test executable
chmod +x scripts/smoke_test_video_batch.sh

# Run smoke test
./scripts/smoke_test_video_batch.sh

# Run ALL 4 test suites
uv run pytest tests/
npm run test -- --run
python scripts/scan_execution_violations.py
python server/tools/validate_plugins.py && python server/tools/validate_pipelines.py
```

**DO NOT**:
- Put smoke test inside server/ (scripts/ is correct)
- Hardcode forbidden terms (load from YAML)
- Skip path-placement check (phase-named files)
- Name CI workflow phase15.yml (use video_batch_validation.yml)

**Git Commands**:
```bash
git add server/tools/forbidden_vocabulary.yaml
git add server/tools/validate_video_batch_path.py
git add .github/workflows/video_batch_validation.yml
git add scripts/smoke_test_video_batch.sh
git commit -m "phase15: add governance validator, CI enforcement, and smoke test script"
```

--- 

### COMMIT 10: Documentation + Demo Script + Rollback Plan
**Story**: Complete onboarding, demo script, formal rollback plan

**Files to Create/Update**:
- `scripts/demo_video_yolo_ocr.sh` (CREATE - executable)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_TESTING_GUIDE.md` (CREATE)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ROLLBACK.md` (CREATE)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_MIGRATION_GUIDE.md` (UPDATE)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_RELEASE_NOTES.md` (UPDATE)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ONBOARDING.md` (UPDATE)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ARCHITECTURE.txt` (CREATE - ASCII)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ARCHITECTURE.mmd` (CREATE - Mermaid)
- `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_GOVERNANCE.md` (UPDATE)

**Acceptance Criteria** (from Story 10):

*Demo Script*:
- [ ] scripts/demo_video_yolo_ocr.sh executable (chmod +x)
- [ ] Calls POST /video/upload-and-run with tiny.mp4 + yolo_ocr
- [ ] Prints first frame result as formatted JSON
- [ ] Works against running local server (http://localhost:8000)

*Rollback Plan*:
- [ ] PHASE_15_ROLLBACK.md exists
- [ ] Lists exact files to remove (router, service, tests, fixtures, tooling, workflow, pipeline)
- [ ] Lists exact modifications to revert (main.py, pyproject.toml)
- [ ] States "Phase-14 DAG engine remains untouched"

*Testing Guide*:
- [ ] PHASE_15_TESTING_GUIDE.md documents: unit tests, integration tests, stress, fuzz, smoke test
- [ ] Documents golden snapshot regeneration procedure

*Other Docs*:
- [ ] PHASE_15_MIGRATION_GUIDE.md matches batch-only scope
- [ ] PHASE_15_RELEASE_NOTES.md accurate file list + test counts
- [ ] PHASE_15_ONBOARDING.md does NOT reference job queues, streaming, persistence
- [ ] PHASE_15_ARCHITECTURE.txt (ASCII diagram)
- [ ] PHASE_15_ARCHITECTURE.mmd (Mermaid diagram)
- [ ] PHASE_15_GOVERNANCE.md lists forbidden vocabulary + placement rules
- [ ] All docs in .ampcode/04_PHASE_NOTES/Phase_15/ (not in functional dirs)

**Pre-Commit Test Verification**:
```bash
# Verify no forbidden concepts in docs
grep -r -i -E "job_id|queue|worker|redis|websocket|streaming|database|postgres|celery" \
  .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ONBOARDING.md \
  .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_MIGRATION_GUIDE.md \
  .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_OVERVIEW.md \
  && echo "FAIL" || echo "OK"

# Verify demo script is executable
test -x scripts/demo_video_yolo_ocr.sh && echo "OK" || echo "FAIL"

# Final full suite
uv run pytest -q
./scripts/smoke_test_video_batch.sh
```

**DO NOT**:
- Put docs inside server/app/docs/ (use .ampcode/)
- Leave old OVERVIEW.md with job queue/streaming content
- Omit rollback plan (governance requirement)
- Forget chmod +x on demo script

**Git Commands**:
```bash
git add scripts/demo_video_yolo_ocr.sh
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_TESTING_GUIDE.md
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ROLLBACK.md
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_MIGRATION_GUIDE.md
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_RELEASE_NOTES.md
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ONBOARDING.md
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ARCHITECTURE.txt
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ARCHITECTURE.mmd
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_GOVERNANCE.md
git commit -m "phase15: finalize documentation, demo script, and rollback plan"
```

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

## Timeline

**20-25 hours** (10 commits)

**Estimated breakdown**:
- Commits 1-2: 1 hour (planning docs)
- Commit 3: 1 hour (OpenCV + fixtures)
- Commit 4: 3 hours (service + 15 unit tests)
- Commit 5: 1.5 hours (router + wiring)
- Commit 6: 2.5 hours (5 integration test files)
- Commit 7: 1.5 hours (schema regression + golden)
- Commit 8: 3 hours (stress + fuzz suites)
- Commit 9: 2 hours (governance tooling + CI + smoke)
- Commit 10: 3.5 hours (documentation + demo + rollback)

--- 

## References

**Core Documents** (read first):
- PHASE_15_USER_STORIES.md (acceptance criteria source of truth)
- PHASE_15_DEFINITION_OF_DONE.md (completion checklist)
- PHASE_15_FIRST_FAILING_TEST.md (test-driven starting point)
- PHASE_15_SPEC.md (MP4 upload specification)
- PHASE_15_SCOPE.md (governance boundaries)

**Governance Documents**:
- PHASE_15_FORBIDDEN_VOCAB.md (Q&A on implementation details)
- PHASE_15_OVERVIEW.md (high-level overview — rewritten in Commit 2)
- PHASE_15_OCR_&_YOLO_JSON.md (valid pipeline examples)

**Planning Documents**:
- PHASE_15_COMMITS.md (commit strategy)
- PHASE_15_NOTES_01-09.md (detailed notes)

**After Implementation**:
- PHASE_15_TESTING_GUIDE.md (testing procedures — Commit 10)
- PHASE_15_ROLLBACK.md (rollback procedures — Commit 10)
- PHASE_15_MIGRATION_GUIDE.md (migration guide — Commit 10)
- PHASE_15_ARCHITECTURE.txt / .mmd (architecture diagrams — Commit 10)