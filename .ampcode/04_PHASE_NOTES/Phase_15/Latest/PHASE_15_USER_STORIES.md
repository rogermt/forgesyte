

Save as:

```
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_USER_STORIES.md
```

```markdown
# Phase 15 — User Stories & Acceptance Criteria (Final)
**10 Stories, 1 per Commit, mapped to the Delivery Plan**
**Incorporates governance review feedback**

Each story follows the format:
- **Story**: As a [role], I want [capability], so that [value].
- **Acceptance Criteria**: Testable conditions that must ALL pass before the commit is merged.
- **Files**: Exact paths to create/modify.
- **Git**: Exact staging and commit commands.
- **Verify**: Commands the developer must run before committing.
- **DO NOT**: Explicit anti-patterns from the failed previous attempt.

---

## Story 1 — Pipeline Definition
**Commit 1 of 10**

### Story
As a **pipeline operator**, I want a `yolo_ocr` pipeline definition that chains YOLO object detection into OCR text extraction, so that the video batch endpoint has a valid DAG to execute per frame.

### Acceptance Criteria
- [ ] File `server/app/pipelines/yolo_ocr.json` exists
- [ ] JSON contains exactly 2 nodes: `detect` (yolo.detect_objects) and `read` (ocr.extract_text)
- [ ] JSON contains exactly 1 edge: `detect → read`
- [ ] `entry_nodes` is `["detect"]`
- [ ] `output_nodes` is `["read"]`
- [ ] `uv run python server/tools/validate_pipelines.py` passes with `yolo_ocr... OK`
- [ ] `uv run python server/tools/validate_plugins.py` still passes (no regression)
- [ ] No other pipelines are modified

### Files
```
server/app/pipelines/yolo_ocr.json  (create)
```

### Git
```bash
git add server/app/pipelines/yolo_ocr.json
git commit -m "phase15: add yolo_ocr pipeline definition (YOLO → OCR)"
```

### Verify
```bash
uv run python server/tools/validate_pipelines.py
uv run python server/tools/validate_plugins.py
```

### DO NOT
- Do not reference `reid`, `track_ids`, `detect_players`, or any plugin that does not exist
- Do not add `server/app/pipelines/phase15_pipeline.json` (no phase names in functional dirs)
- Do not modify `echo_pipeline.json`

---

## Story 2 — Payload Contract & Scope Boundaries
**Commit 2 of 10**

### Story
As a **contributor**, I want a locked payload contract and an accurate scope document, so that I know exactly what data flows between frames and what is forbidden in Phase 15.

### Acceptance Criteria
- [ ] `PHASE_15_PAYLOAD_YOLO_OCR.md` exists in `.ampcode/04_PHASE_NOTES/Phase_15/`
- [ ] Payload doc specifies exactly 2 fields: `frame_index` (int) and `image_bytes` (raw JPEG bytes)
- [ ] Payload doc explicitly states: "Do NOT use base64 encoding"
- [ ] Payload doc states response schema is frozen to `{"results": [{"frame_index", "result"}]}`
- [ ] `PHASE_15_SCOPE.md` lists all forbidden items (job queue, persistence, tracking, async, streaming)
- [ ] `PHASE_15_OVERVIEW.md` is **rewritten** to describe batch-only scope
- [ ] `PHASE_15_OVERVIEW.md` does NOT mention: job queue, Redis, RabbitMQ, worker pool, streaming, WebSocket, database schema, job status, progress polling
- [ ] No files created in `server/app/` or `server/tools/` by this commit

### Files
```
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_PAYLOAD_YOLO_OCR.md  (create)
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_SCOPE.md             (update)
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_OVERVIEW.md           (rewrite)
```

### Git
```bash
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_PAYLOAD_YOLO_OCR.md
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_SCOPE.md
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_OVERVIEW.md
git commit -m "phase15: lock payload contract and rewrite overview to batch-only scope"
```

### Verify
```bash
# Confirm overview no longer contains forbidden concepts:
grep -i -E "job_id|queue|worker|redis|rabbitmq|celery|websocket|streaming|database|sql|postgres" \
  .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_OVERVIEW.md && echo "FAIL: forbidden concepts found" || echo "OK"
```

### DO NOT
- Do not put the payload contract in `docs/` or `server/app/docs/` — it is a phase governance doc
- Do not leave the old OVERVIEW.md intact — it describes job queues and must be fully rewritten
- Do not add `execution_time_ms`, `status`, or `metadata` to the payload contract

---

## Story 3 — OpenCV Dependency + Test Fixtures + Corrupt Harness
**Commit 3 of 10**

### Story
As a **test engineer**, I want deterministic test assets (a valid tiny MP4 and a corrupted MP4 generator), and the OpenCV dependency installed, so that all subsequent tests have reliable, repeatable inputs.

### Acceptance Criteria
- [ ] `server/pyproject.toml` includes `opencv-python-headless` (or `opencv-python`) in dependencies
- [ ] `generate_tiny_mp4.py` exists at `server/app/tests/fixtures/generate_tiny_mp4.py`
- [ ] Running the generator produces a valid MP4 at `server/app/tests/fixtures/tiny.mp4`
- [ ] `tiny.mp4` is committed (not generated at test time)
- [ ] `tiny.mp4` has exactly 3 frames at 320×240 resolution
- [ ] `corrupt_mp4_generator.py` exists at `server/app/tests/video/fakes/corrupt_mp4_generator.py`
- [ ] Corrupt generator writes bytes with a fake ftyp header followed by invalid data
- [ ] OpenCV `VideoCapture` fails to open the corrupted file (returns `isOpened() == False`)
- [ ] All existing tests still pass (`uv run pytest -q`)

### Files
```
server/pyproject.toml                                          (modify)
server/app/tests/fixtures/generate_tiny_mp4.py                 (create)
server/app/tests/fixtures/tiny.mp4                             (create — committed binary)
server/app/tests/video/__init__.py                             (create — empty)
server/app/tests/video/fakes/__init__.py                       (create — empty)
server/app/tests/video/fakes/corrupt_mp4_generator.py          (create)
```

### Git
```bash
git add server/pyproject.toml
git add server/app/tests/fixtures/generate_tiny_mp4.py
git add server/app/tests/fixtures/tiny.mp4
git add server/app/tests/video/__init__.py
git add server/app/tests/video/fakes/__init__.py
git add server/app/tests/video/fakes/corrupt_mp4_generator.py
git commit -m "phase15: add opencv dep, tiny mp4 fixture, and corrupted mp4 generator"
```

### Verify
```bash
# Confirm tiny.mp4 has 3 frames:
python -c "
import cv2
cap = cv2.VideoCapture('server/app/tests/fixtures/tiny.mp4')
count = 0
while cap.read()[0]: count += 1
cap.release()
assert count == 3, f'Expected 3 frames, got {count}'
print('OK: 3 frames')
"

# Confirm corrupt file fails to open:
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
print('OK: corrupt mp4 rejected by OpenCV')
"

# Existing tests still pass:
uv run pytest -q
```

### DO NOT
- Do not use `opencv-python` with GUI support on CI — prefer `opencv-python-headless`
- Do not generate `tiny.mp4` dynamically in tests — commit it
- Do not place fixtures in `server/app/tests/phase15/` or any phase-named directory
- Do not use random bytes for the corrupt generator — use deterministic fake header

---

## Story 4 — VideoFilePipelineService + Mock DAG + Pure Unit Tests
**Commit 4 of 10**

### Story
As a **backend developer**, I want a `VideoFilePipelineService` that extracts frames from an MP4 file and runs each through a DAG pipeline, and I want pure unit tests that verify this logic without loading real YOLO/OCR plugins.

### Acceptance Criteria

#### Service
- [ ] `video_file_pipeline_service.py` exists at `server/app/services/`
- [ ] Constructor accepts `dag_service`, optional `frame_stride` (default 1), optional `max_frames` (default None)
- [ ] `run_on_file(pipeline_id, file_path, options)` returns `[{"frame_index": int, "result": dict}, ...]`
- [ ] Opens file with `cv2.VideoCapture`; raises `ValueError("Unable to read video file")` if `not isOpened()`
- [ ] Encodes each frame as JPEG raw bytes via `cv2.imencode(".jpg", frame)`
- [ ] Payload per frame is exactly `{"frame_index": int, "image_bytes": bytes}`
- [ ] Calls `dag_service.run_pipeline(pipeline_id, payload)` per frame
- [ ] Respects `frame_stride`: only processes frames where `frame_index % stride == 0`
- [ ] Respects `max_frames`: stops after N processed frames
- [ ] `stride <= 0` treated as 1
- [ ] `cap.release()` called in `finally` block (never leaked)

#### Mock DAG
- [ ] `mock_dag_service.py` exists at `server/app/tests/video/fakes/`
- [ ] Supports `fail_mode` parameter: `None` (success), `"pipeline_not_found"`, `"plugin_error"`
- [ ] Records all calls in `self.calls` list for assertion
- [ ] `"pipeline_not_found"` raises `FileNotFoundError("Pipeline not found")`
- [ ] `"plugin_error"` raises `RuntimeError("Plugin execution failed")`

#### Unit Tests
- [ ] `test_video_service_unit.py` exists at `server/app/tests/video/`
- [ ] Tests use `MockDagPipelineService` — never real plugins
- [ ] Test: tiny.mp4 (3 frames) → 3 results with indices [0, 1, 2]
- [ ] Test: stride=2 → 2 results at indices [0, 2]
- [ ] Test: stride=3 → 1 result at index [0]
- [ ] Test: stride=100 → 1 result at index [0]
- [ ] Test: stride > total frames → still returns index 0 only
- [ ] Test: stride=0 treated as stride=1 → 3 results
- [ ] Test: max_frames=1 → 1 result
- [ ] Test: max_frames=2 → 2 results
- [ ] Test: max_frames > total frames → returns all 3
- [ ] Test: stride=2 + max_frames=1 → 1 result at index [0]
- [ ] Test: nonexistent file path → `ValueError`
- [ ] Test: text file (not video) → `ValueError`
- [ ] Test: corrupted MP4 (using corrupt generator) → `ValueError("Unable to read video file")`
- [ ] Test: mock fail_mode="pipeline_not_found" → `FileNotFoundError`
- [ ] Test: mock fail_mode="plugin_error" → `RuntimeError`
- [ ] Test: payload contains `frame_index` key (int type)
- [ ] Test: payload contains `image_bytes` key (bytes type)
- [ ] Test: `mock.calls` length matches number of processed frames
- [ ] All tests pass: `uv run pytest server/app/tests/video/test_video_service_unit.py -v`

### Files
```
server/app/services/video_file_pipeline_service.py       (create)
server/app/tests/video/fakes/mock_dag_service.py         (create)
server/app/tests/video/test_video_service_unit.py        (create)
```

### Git
```bash
git add server/app/services/video_file_pipeline_service.py
git add server/app/tests/video/fakes/mock_dag_service.py
git add server/app/tests/video/test_video_service_unit.py
git commit -m "phase15: implement VideoFilePipelineService with pure unit tests and mock DAG"
```

### Verify
```bash
uv run pytest server/app/tests/video/test_video_service_unit.py -v
uv run pytest -q  # full suite still passes
```

### DO NOT
- Do not import real YOLO or OCR plugins in unit tests
- Do not name the service `phase15_video_service.py`
- Do not use `DagPipelineService = Depends()` — follow your codebase's instantiation pattern
- Do not carry state between frames — each frame is independent
- Do not add `execution_time_ms` or `status` to the result dict

---

## Story 5 — Router + App Wiring + Registration Test
**Commit 5 of 10**

### Story
As an **API consumer**, I want a `POST /video/upload-and-run` endpoint registered in the FastAPI application, so that I can upload an MP4 and receive per-frame pipeline results.

### Acceptance Criteria

#### Router
- [ ] `video_file.py` exists at `server/app/api/routes/`
- [ ] Endpoint: `POST /video/upload-and-run`
- [ ] Accepts multipart form: `file` (UploadFile, required) + `pipeline_id` (Form string, required)
- [ ] Validates `file.content_type` in `{"video/mp4", "video/quicktime"}`
- [ ] Reads file bytes; rejects empty upload with 400 `"Uploaded file is empty"`
- [ ] Saves to `NamedTemporaryFile(delete=False, suffix=".mp4")`
- [ ] Calls `VideoFilePipelineService.run_on_file(pipeline_id, tmp_path)`
- [ ] Maps `FileNotFoundError` → 404 `"Pipeline not found"`
- [ ] Maps `ValueError` → 400 `"Unable to read video file"`
- [ ] Cleanup: `tmp_path.unlink(missing_ok=True)` in `finally` block — always runs
- [ ] Returns exactly `{"results": [...]}` — no other top-level keys

#### App Wiring
- [ ] `server/app/main.py` includes the video router
- [ ] Router prefix is `/video`

#### Registration Test
- [ ] `test_video_router_registered.py` exists at `server/app/tests/video/`
- [ ] Test creates `TestClient(app)` and asserts `/video/upload-and-run` is in the route list
- [ ] Test passes: `uv run pytest server/app/tests/video/test_video_router_registered.py -v`

### Files
```
server/app/api/routes/video_file.py                      (create)
server/app/main.py                                       (modify — add router include)
server/app/tests/video/test_video_router_registered.py   (create)
```

### Git
```bash
git add server/app/api/routes/video_file.py
git add server/app/main.py
git add server/app/tests/video/test_video_router_registered.py
git commit -m "phase15: add /video/upload-and-run router, wire into app, verify registration"
```

### Verify
```bash
uv run pytest server/app/tests/video/test_video_router_registered.py -v
uv run pytest -q  # full suite
```

### DO NOT
- Do not name the router `phase15_router.py`
- Do not add `pipeline_id` to the response — response is exactly `{"results": [...]}`
- Do not add `status`, `metadata`, or `job_id` to the response
- Do not forget the `finally` block for temp file cleanup
- Do not use `async` background tasks — endpoint is synchronous

---

## Story 6 — Integration Tests + Full Error Coverage
**Commit 6 of 10**

### Story
As a **QA engineer**, I want integration tests that prove the endpoint works end-to-end with `tiny.mp4` AND that every error path returns the correct HTTP status code and detail message, so that API consumers can rely on stable error behavior.

### Acceptance Criteria

#### Success Path
- [ ] Upload `tiny.mp4` with `pipeline_id=yolo_ocr` → HTTP 200
- [ ] Response contains `"results"` key
- [ ] `results` is a list with length ≥ 1
- [ ] Each item contains exactly `"frame_index"` (int) and `"result"` (dict)

#### Error Paths (each with exact detail string assertion)
- [ ] Invalid content type (`text/plain`) → 400 + `"Unsupported file type"`
- [ ] Empty file (0 bytes, `video/mp4`) → 400 + `"Uploaded file is empty"`
- [ ] Corrupted MP4 (fake header bytes, `video/mp4`) → 400 + `"Unable to read video file"`
- [ ] Nonexistent pipeline (`"does_not_exist"`) → 404 + `"Pipeline not found"`
- [ ] Missing `pipeline_id` form field → 422 (FastAPI validation error)
- [ ] Missing `file` form field → 422 (FastAPI validation error)

#### All Tests
- [ ] All 8+ tests pass: `uv run pytest server/app/tests/video/test_video_*.py -v`
- [ ] All existing Phase-14 tests still pass

### Files
```
server/app/tests/video/test_video_upload_and_run_success.py  (create)
server/app/tests/video/test_video_invalid_file_type.py       (create)
server/app/tests/video/test_video_invalid_pipeline_id.py     (create)
server/app/tests/video/test_video_empty_file.py              (create)
server/app/tests/video/test_video_corrupted_mp4.py           (create)
server/app/tests/video/test_video_missing_fields_422.py      (create)
```

### Git
```bash
git add server/app/tests/video/test_video_upload_and_run_success.py
git add server/app/tests/video/test_video_invalid_file_type.py
git add server/app/tests/video/test_video_invalid_pipeline_id.py
git add server/app/tests/video/test_video_empty_file.py
git add server/app/tests/video/test_video_corrupted_mp4.py
git add server/app/tests/video/test_video_missing_fields_422.py
git commit -m "phase15: add integration tests and router-level error tests (200/400/404/422)"
```

### Verify
```bash
uv run pytest server/app/tests/video/ -v
uv run pytest -q  # full suite
```

### DO NOT
- Do not assert on response body structure beyond `{"results": [...]}` and `{"frame_index", "result"}`
- Do not skip the 422 tests — the previous attempt missed these entirely
- Do not use random/dynamic file content — all inputs must be deterministic
- Do not name tests `test_phase15_*.py`

---

## Story 7 — Schema Regression Guard + Golden Snapshot
**Commit 7 of 10**

### Story
As a **governance maintainer**, I want a schema regression guard that mechanically prevents Phase-16 creep (new fields like `job_id`, `status`, `metadata` appearing in the response), and a golden snapshot that proves output is deterministic, so that the response contract is immutable until explicitly changed.

### Acceptance Criteria

#### Schema Regression Guard
- [ ] `test_video_schema_regression.py` exists at `server/app/tests/video/`
- [ ] Test calls the endpoint with `tiny.mp4` + `yolo_ocr` pipeline
- [ ] Test asserts: `set(data.keys()) == {"results"}`
- [ ] Test asserts: for each item, `set(item.keys()) == {"frame_index", "result"}`
- [ ] Test has a docstring or comment stating its purpose: "Prevent Phase-16 creep — no job_id, status, metadata, or execution_time_ms allowed"
- [ ] Test passes

#### Golden Snapshot
- [ ] `golden_output.json` exists at `server/app/tests/video/golden/`
- [ ] `golden_output.json` was generated using `MockDagPipelineService` only (deterministic), **never** from real YOLO/OCR model runtime
- [ ] `test_video_golden_snapshot.py` exists at `server/app/tests/video/`
- [ ] Test compares endpoint output against `golden_output.json`
- [ ] Test header contains the regeneration rule as a docstring:
  > "REGENERATION RULE: If pipeline behavior changes intentionally, regenerate golden_output.json using the mock DAG service only. Never generate from real model runtime. Document the reason for regeneration in the commit message."
- [ ] Test passes

### Files
```
server/app/tests/video/test_video_schema_regression.py   (create)
server/app/tests/video/golden/__init__.py                (create — empty)
server/app/tests/video/golden/golden_output.json         (create)
server/app/tests/video/test_video_golden_snapshot.py     (create)
```

### Git
```bash
git add server/app/tests/video/test_video_schema_regression.py
git add server/app/tests/video/golden/__init__.py
git add server/app/tests/video/golden/golden_output.json
git add server/app/tests/video/test_video_golden_snapshot.py
git commit -m "phase15: freeze response schema and add golden snapshot regression test"
```

### Verify
```bash
uv run pytest server/app/tests/video/test_video_schema_regression.py -v
uv run pytest server/app/tests/video/test_video_golden_snapshot.py -v
```

### DO NOT
- Do not generate `golden_output.json` by calling real YOLO/OCR — use mock DAG output only
- Do not add `pipeline_id`, `status`, or `execution_time_ms` to the golden output
- Do not skip documenting the regeneration rule in the test docstring
- Do not allow the golden snapshot to depend on system time, random values, or environment

---

## Story 8 — Stress + Fuzz Test Suites
**Commit 8 of 10**

### Story
As a **reliability engineer**, I want a stress test (1000 frames) and a fuzz test (malformed MP4 inputs) that prove the service handles high volume without memory leaks or crashes and gracefully rejects garbage input, so that the system is hardened before release.

### Acceptance Criteria

#### Stress Test
- [ ] `test_video_service_1000_frames.py` exists at `server/app/tests/video/stress/`
- [ ] Test generates a 1000-frame MP4 at 320×240 in a `tmp_path` fixture
- [ ] Test uses `MockDagPipelineService` (not real plugins)
- [ ] Test asserts: `len(results) == 1000`
- [ ] Test asserts: `results[0]["frame_index"] == 0`
- [ ] Test asserts: `results[-1]["frame_index"] == 999`
- [ ] Test asserts: `len(mock.calls) == 1000`
- [ ] Test asserts: all indices are sequential with no gaps and no duplicates
- [ ] Test passes within a reasonable time (< 30 seconds)

#### Fuzz Test
- [ ] `test_video_service_mp4_fuzz.py` exists at `server/app/tests/video/fuzz/`
- [ ] Test covers at minimum 4 cases: random bytes (128B), random bytes (1KB), header-only MP4, truncated MP4
- [ ] For each fuzz case: service either returns 0 results OR raises `ValueError` — never crashes, never hangs, never raises an unhandled exception type
- [ ] Test uses `MockDagPipelineService`
- [ ] All fuzz cases use deterministic or fixed-seed inputs (no flaky tests)
- [ ] Test passes

### Files
```
server/app/tests/video/stress/__init__.py                      (create — empty)
server/app/tests/video/stress/test_video_service_1000_frames.py (create)
server/app/tests/video/fuzz/__init__.py                        (create — empty)
server/app/tests/video/fuzz/test_video_service_mp4_fuzz.py     (create)
```

### Git
```bash
git add server/app/tests/video/stress/__init__.py
git add server/app/tests/video/stress/test_video_service_1000_frames.py
git add server/app/tests/video/fuzz/__init__.py
git add server/app/tests/video/fuzz/test_video_service_mp4_fuzz.py
git commit -m "phase15: add 1000-frame stress test and mp4 fuzz test suite"
```

### Verify
```bash
uv run pytest server/app/tests/video/stress/ -v
uv run pytest server/app/tests/video/fuzz/ -v
```

### DO NOT
- Do not use real YOLO/OCR plugins in stress/fuzz tests
- Do not use non-deterministic random seeds without fixing them (use `os.urandom` with fixed size, or hardcoded bytes)
- Do not allow any fuzz case to cause an unhandled exception type other than `ValueError`
- Do not skip the sequential-index assertion in the stress test — ordering bugs are real

---

## Story 9 — Governance Tooling + CI + Smoke Test
**Commit 9 of 10**

### Story
As a **release manager**, I want automated governance enforcement (forbidden vocabulary scanner + file placement validator) running in CI on every PR, and a one-command smoke test for developers, so that Phase-16 concepts cannot leak into the codebase.

### Acceptance Criteria

#### Forbidden Vocabulary
- [ ] `forbidden_vocabulary.yaml` exists at `server/tools/`
- [ ] Contains regex patterns for at minimum: `job_id`, `queue`, `worker`, `celery`, `rq`, `redis`, `rabbitmq`, `database`, `sql`, `postgres`, `mongodb`, `insert_one`, `update_one`, `reid`, `tracking`, `track_ids`, `metrics`, `execution_time_ms`, `websocket`, `streaming`
- [ ] Patterns use word boundaries (`\b`)

#### Path Validator
- [ ] `validate_video_batch_path.py` exists at `server/tools/`
- [ ] Loads terms from `forbidden_vocabulary.yaml` (not hardcoded)
- [ ] Scans video-related functional files (service, router, tests) for forbidden terms
- [ ] Scans `server/app/`, `server/tools/` for phase-named files (containing "phase15", "phase_15", "phase-15")
- [ ] Exits 0 on pass, exits 1 on any violation
- [ ] Currently passes on all Phase-15 code with zero warnings

#### CI Workflow
- [ ] `video_batch_validation.yml` exists at `.github/workflows/`
- [ ] Triggers on PRs to `main` that touch `server/**`, `scripts/**`, or `server/tools/**`
- [ ] Runs in order: validate_plugins → validate_pipelines → validate_video_batch_path → pytest (full suite)

#### Smoke Test
- [ ] `smoke_test_video_batch.sh` exists at `scripts/`
- [ ] Is executable (`chmod +x`)
- [ ] Runs exactly these 4 steps in this order:
  1. `uv run python server/tools/validate_plugins.py`
  2. `uv run python server/tools/validate_pipelines.py`
  3. `uv run python server/tools/validate_video_batch_path.py`
  4. `uv run pytest server/app/tests/video -q --maxfail=1`
- [ ] Uses `set -e` to exit on first failure
- [ ] Prints a clear pass message at the end
- [ ] Exits 0 only if all 4 steps pass

### Files
```
server/tools/forbidden_vocabulary.yaml                   (create)
server/tools/validate_video_batch_path.py                (create)
.github/workflows/video_batch_validation.yml             (create)
scripts/smoke_test_video_batch.sh                        (create)
```

### Git
```bash
git add server/tools/forbidden_vocabulary.yaml
git add server/tools/validate_video_batch_path.py
git add .github/workflows/video_batch_validation.yml
git add scripts/smoke_test_video_batch.sh
git commit -m "phase15: add governance validator, CI enforcement, and smoke test script"
```

### Verify
```bash
uv run python server/tools/validate_video_batch_path.py
chmod +x scripts/smoke_test_video_batch.sh
./scripts/smoke_test_video_batch.sh
```

### DO NOT
- Do not put `smoke_test_video_batch.sh` inside `server/` — scripts go in `scripts/`
- Do not hardcode forbidden terms in the Python validator — load from YAML
- Do not skip the path-placement check (phase-named files in functional dirs)
- Do not name the CI workflow `phase15.yml` — use `video_batch_validation.yml` (functional name)

---

## Story 10 — Documentation + Demo Script + Rollback Plan
**Commit 10 of 10**

### Story
As a **new contributor**, I want complete onboarding documentation, a working demo script, and a formal rollback plan, so that I can understand the system, see it work, and know how to safely revert it if needed.

### Acceptance Criteria

#### Demo Script
- [ ] `demo_video_yolo_ocr.sh` exists at `scripts/`
- [ ] Is executable (`chmod +x`)
- [ ] Calls `POST /video/upload-and-run` with `tiny.mp4` + `yolo_ocr`
- [ ] Prints the first frame result as formatted JSON
- [ ] Works against a running local server (`http://localhost:8000`)

#### Rollback Plan
- [ ] `PHASE_15_ROLLBACK.md` exists in `.ampcode/04_PHASE_NOTES/Phase_15/`
- [ ] Explicitly states the purpose: "Restore repo to Phase-14-compatible state"
- [ ] Lists exact files to remove:
  - Router (`server/app/api/routes/video_file.py`)
  - Service (`server/app/services/video_file_pipeline_service.py`)
  - All video tests (`server/app/tests/video/`)
  - Fixtures (`server/app/tests/fixtures/tiny.mp4`, `generate_tiny_mp4.py`)
  - Governance tooling (`forbidden_vocabulary.yaml`, `validate_video_batch_path.py`)
  - CI workflow (`video_batch_validation.yml`)
  - Pipeline (`yolo_ocr.json` — optional, mark as such)
- [ ] Lists exact modifications to revert:
  - Remove router include from `server/app/main.py`
  - Remove `opencv-python-headless` from `server/pyproject.toml`
- [ ] States: "Phase-14 DAG engine remains untouched"

#### Testing Guide
- [ ] `PHASE_15_TESTING_GUIDE.md` exists
- [ ] Documents how to run: unit tests, integration tests, stress tests, fuzz tests
- [ ] Documents how to run smoke test
- [ ] Documents golden snapshot regeneration procedure (must match Story 7 regeneration rule)

#### Other Docs (all in `.ampcode/04_PHASE_NOTES/Phase_15/`)
- [ ] `PHASE_15_MIGRATION_GUIDE.md` exists and matches batch-only scope
- [ ] `PHASE_15_RELEASE_NOTES.md` exists with accurate file list and test counts
- [ ] `PHASE_15_ONBOARDING.md` exists and does NOT reference job queues, streaming, or persistence
- [ ] `PHASE_15_ARCHITECTURE.txt` exists (ASCII diagram matching the infographic)
- [ ] `PHASE_15_ARCHITECTURE.mmd` exists (Mermaid diagram)
- [ ] `PHASE_15_DEFINITION_OF_DONE.md` exists and matches this story set
- [ ] `PHASE_15_GOVERNANCE.md` exists and lists all forbidden vocabulary + placement rules
- [ ] All docs are in `.ampcode/04_PHASE_NOTES/Phase_15/` (not in functional dirs)

### Files
```
scripts/demo_video_yolo_ocr.sh                                           (create)
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_TESTING_GUIDE.md               (create)
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ROLLBACK.md                    (create)
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_MIGRATION_GUIDE.md             (update)
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_RELEASE_NOTES.md               (update)
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ONBOARDING.md                  (update)
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ARCHITECTURE.txt               (create)
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ARCHITECTURE.mmd               (create)
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_DEFINITION_OF_DONE.md          (update)
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_GOVERNANCE.md                  (update)
```

### Git
```bash
git add scripts/demo_video_yolo_ocr.sh
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_TESTING_GUIDE.md
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ROLLBACK.md
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_MIGRATION_GUIDE.md
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_RELEASE_NOTES.md
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ONBOARDING.md
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ARCHITECTURE.txt
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ARCHITECTURE.mmd
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_DEFINITION_OF_DONE.md
git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_GOVERNANCE.md
git commit -m "phase15: finalize documentation, demo script, and rollback plan"
```

### Verify
```bash
# Confirm no forbidden concepts in onboarding/migration/overview docs:
grep -r -i -E "job_id|queue|worker|redis|websocket|streaming|database|postgres|celery" \
  .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ONBOARDING.md \
  .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_MIGRATION_GUIDE.md \
  .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_OVERVIEW.md \
  && echo "FAIL: forbidden concepts found in docs" || echo "OK: docs are clean"

# Confirm demo script is executable:
test -x scripts/demo_video_yolo_ocr.sh && echo "OK" || echo "FAIL: not executable"

# Final full suite:
uv run pytest -q
./scripts/smoke_test_video_batch.sh
```

### DO NOT
- Do not put any docs inside `server/app/docs/` — phase docs go in `.ampcode/`
- Do not leave the old OVERVIEW.md with job queue/streaming/persistence content
- Do not omit the rollback plan — it is a governance requirement
- Do not forget to make the demo script executable (`chmod +x`)
- Do not reference `DagPipelineService` in docs if that class does not exist in the codebase
```