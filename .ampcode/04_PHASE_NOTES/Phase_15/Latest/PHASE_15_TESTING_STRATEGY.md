Absolutely, Roger — here are **all three deliverables**, clean, sharp, and fully aligned with your Phase‑15 governance model.  
Everything is **text‑only**, repo‑ready, and safe to paste into `.ampcode/04_PHASE_NOTES/Phase_15/`.

No deviations.  
No scope drift.  
Just the exact artifacts you asked for.

---

# ⭐ **1. DIAGRAM — Boundary Between Unit, Integration, and System Tests**  
### *ASCII architecture of the Phase‑15 test layers*

```
┌──────────────────────────────────────────────────────────────┐
│                PHASE‑15 TEST BOUNDARY DIAGRAM                │
└──────────────────────────────────────────────────────────────┘

                          TEST PYRAMID
                          (High → Low)
                                 ▲
                                 │
                                 │
                     ┌──────────────────────┐
                     │   SYSTEM TESTS       │
                     │  (Phase‑16+, future) │
                     │  • Full stack        │
                     │  • Workers/queues    │
                     │  • Persistence       │
                     └──────────────────────┘
                                 ▲
                                 │
                                 │
                     ┌──────────────────────┐
                     │  INTEGRATION TESTS   │
                     │  Commit 6, 7, 8      │
                     │  • FastAPI endpoint  │
                     │  • Temp file I/O     │
                     │  • OpenCV decoding   │
                     │  • DAG execution     │
                     │  • HTTP codes        │
                     │  • Golden snapshot   │
                     │  • Stress + fuzz     │
                     └──────────────────────┘
                                 ▲
                                 │
                                 │
                     ┌──────────────────────┐
                     │     UNIT TESTS       │
                     │  Commit 4 + 5        │
                     │  • Pure service      │
                     │  • Mock DAG only     │
                     │  • No filesystem     │
                     │  • No OpenCV decode  │
                     │  • Router registered │
                     └──────────────────────┘
                                 ▲
                                 │
                                 │
                     ┌──────────────────────┐
                     │     CODEBASE         │
                     └──────────────────────┘
```

**Key boundary:**  
- **Commit 4 & 5 = UNIT**  
- **Commit 6, 7, 8 = INTEGRATION**  
- **System tests do not exist in Phase‑15** (reserved for Phase‑16 job queue architecture).

---

# ⭐ **2. PHASE‑15 TEST PYRAMID**  
### *The official hierarchy of test types for Phase‑15*

```
                     ▲
                     │
            ┌───────────────────┐
            │   SYSTEM TESTS    │   (Phase‑16+ only)
            └───────────────────┘
                     ▲
                     │
            ┌───────────────────┐
            │ INTEGRATION TESTS │   Commit 6–8
            │  - Router E2E     │
            │  - OpenCV decode  │
            │  - DAG execution  │
            │  - HTTP codes     │
            │  - Golden snapshot│
            │  - Stress/Fuzz    │
            └───────────────────┘
                     ▲
                     │
            ┌───────────────────┐
            │    UNIT TESTS     │   Commit 4–5
            │  - Pure service   │
            │  - Mock DAG       │
            │  - Router wiring  │
            └───────────────────┘
                     ▲
                     │
            ┌───────────────────┐
            │     CODEBASE      │
            └───────────────────┘
```

**Interpretation:**  
- The **base** is unit tests (fast, deterministic).  
- The **middle** is integration tests (slower, full stack).  
- The **top** is system tests (not part of Phase‑15).  

---

# ⭐ **3. MAPPING OF EVERY TEST FILE TO ITS CATEGORY**  
### *A complete classification of all Phase‑15 test files*

---

## **UNIT TESTS (Commit 4 & 5)**  
These tests use **MockDagPipelineService**, no OpenCV decode, no real file I/O.

```
server/app/tests/video/test_video_service_unit.py
server/app/tests/video/fakes/mock_dag_service.py
server/app/tests/video/test_video_router_registered.py
```

**Purpose:**  
- Validate service logic  
- Validate router registration  
- Validate stride/max_frames  
- Validate error propagation  
- Validate payload structure  

---

## **INTEGRATION TESTS (Commit 6)**  
These tests exercise the **real endpoint**, **real OpenCV**, **real temp files**, and **real DAG execution**.

```
server/app/tests/video/test_video_upload_and_run_success.py
server/app/tests/video/test_video_invalid_file_type.py
server/app/tests/video/test_video_invalid_pipeline_id.py
server/app/tests/video/test_video_empty_file.py
server/app/tests/video/test_video_corrupted_mp4.py
server/app/tests/video/test_video_missing_fields_422.py
```

**Purpose:**  
- Validate HTTP codes  
- Validate corrupted MP4 handling  
- Validate empty file handling  
- Validate pipeline-not-found  
- Validate content-type enforcement  

---

## **REGRESSION TESTS (Commit 7)**  
These tests freeze the schema and output.

```
server/app/tests/video/test_video_schema_regression.py
server/app/tests/video/golden/golden_output.json
server/app/tests/video/test_video_golden_snapshot.py
```

**Purpose:**  
- Prevent Phase‑16 creep  
- Freeze response schema  
- Freeze output behavior  

---

## **STRESS & FUZZ TESTS (Commit 8)**  
These tests validate robustness and performance.

```
server/app/tests/video/stress/test_video_service_1000_frames.py
server/app/tests/video/fuzz/test_video_service_mp4_fuzz.py
```

**Purpose:**  
- Validate no memory leaks  
- Validate sequential frame indices  
- Validate safe handling of malformed MP4s  

---

## **FIXTURE GENERATORS (Commit 3)**  
Not tests, but test infrastructure.

```
server/app/tests/fixtures/generate_tiny_mp4.py
server/app/tests/fixtures/tiny.mp4
server/app/tests/video/fakes/corrupt_mp4_generator.py
```

---

# ⭐ **Summary Table**

```
CATEGORY           | TEST FILES
───────────────────|──────────────────────────────────────────────
UNIT               | test_video_service_unit.py
                   | test_video_router_registered.py
                   | mock_dag_service.py

INTEGRATION        | test_video_upload_and_run_success.py
                   | test_video_invalid_file_type.py
                   | test_video_invalid_pipeline_id.py
                   | test_video_empty_file.py
                   | test_video_corrupted_mp4.py
                   | test_video_missing_fields_422.py

REGRESSION         | test_video_schema_regression.py
                   | test_video_golden_snapshot.py
                   | golden_output.json

STRESS             | test_video_service_1000_frames.py

FUZZ               | test_video_service_mp4_fuzz.py

FIXTURES           | tiny.mp4
                   | generate_tiny_mp4.py
                   | corrupt_mp4_generator.py
```

### Phase‑15 test strategy document

**Goal:**  
Guarantee that the `/video/upload-and-run` endpoint, `VideoFilePipelineService`, and `yolo_ocr` pipeline behave deterministically, remain stateless, and never drift into Phase‑16 scope (queues, persistence, tracking).

---

#### 1. Test layers

- **Unit tests (Commit 4–5):**
  - **Scope:** Service logic and router wiring.
  - **Characteristics:**  
    - Use `MockDagPipelineService` only.  
    - No real plugins, no real network, no real filesystem dependencies.  
    - No OpenCV decode of real files.
  - **Objectives:**  
    - Validate frame iteration, `frame_stride`, `max_frames`.  
    - Validate payload shape `{frame_index, image_bytes}`.  
    - Validate error propagation (`ValueError`, `FileNotFoundError`, `RuntimeError`).  
    - Validate router registration in `main.py`.

- **Integration tests (Commit 6):**
  - **Scope:** Full request path through FastAPI, temp file, OpenCV, service, and DAG.
  - **Characteristics:**  
    - Use real `tiny.mp4` and corrupted MP4 fixture.  
    - Exercise real `VideoFilePipelineService` and router.
  - **Objectives:**  
    - Validate 200/400/404/422 behavior.  
    - Validate content-type enforcement.  
    - Validate corrupted/empty file handling.

- **Regression tests (Commit 7):**
  - **Scope:** Response schema and output stability.
  - **Characteristics:**  
    - Schema freeze test.  
    - Golden snapshot comparison.
  - **Objectives:**  
    - Prevent new fields (`job_id`, `status`, `metadata`) from appearing.  
    - Detect any change in output structure or semantics.

- **Stress & fuzz tests (Commit 8):**
  - **Scope:** Performance and robustness.
  - **Characteristics:**  
    - 1000‑frame synthetic MP4.  
    - Deterministic malformed MP4 inputs.
  - **Objectives:**  
    - Ensure no memory leaks or frame skips.  
    - Ensure malformed inputs never crash or hang.

---

#### 2. Test data strategy

- **Fixtures:**
  - `tiny.mp4` (3 frames, 320×240) committed to repo.
  - Corrupted MP4 generated with deterministic fake header.
- **Determinism:**
  - No random seeds without fixing them.
  - Golden snapshot generated from mock DAG, not real models.

---

#### 3. Governance in tests

- No phase‑named test files.  
- No forbidden vocabulary in test code.  
- Tests must not introduce Phase‑16 concepts (queues, persistence, tracking).

---

### Phase‑15 test coverage matrix

| Area                         | Test Type      | Files                                                                 |
|------------------------------|----------------|-----------------------------------------------------------------------|
| Service frame logic          | Unit           | `test_video_service_unit.py`                                          |
| Service error propagation    | Unit           | `test_video_service_unit.py`                                          |
| Router registration          | Unit           | `test_video_router_registered.py`                                     |
| Endpoint happy path          | Integration    | `test_video_upload_and_run_success.py`                                |
| Invalid content type         | Integration    | `test_video_invalid_file_type.py`                                     |
| Empty file                   | Integration    | `test_video_empty_file.py`                                            |
| Corrupted MP4                | Integration    | `test_video_corrupted_mp4.py`                                         |
| Missing pipeline             | Integration    | `test_video_invalid_pipeline_id.py`                                   |
| Missing form fields (422)    | Integration    | `test_video_missing_fields_422.py`                                    |
| Schema freeze (top-level)    | Regression     | `test_video_schema_regression.py`                                     |
| Schema freeze (item-level)   | Regression     | `test_video_schema_regression.py`                                     |
| Golden output stability      | Regression     | `test_video_golden_snapshot.py`, `golden_output.json`                 |
| 1000‑frame performance       | Stress         | `test_video_service_1000_frames.py`                                   |
| Malformed MP4 robustness     | Fuzz           | `test_video_service_mp4_fuzz.py`                                      |
| Fixture correctness          | Infra/Fixture  | `generate_tiny_mp4.py`, `tiny.mp4`, `corrupt_mp4_generator.py`        |

---

### Phase‑15 CI pipeline diagram (text‑only)

```text
┌──────────────────────────────────────────────────────────────┐
│                 PHASE‑15 CI PIPELINE (VIDEO BATCH)           │
└──────────────────────────────────────────────────────────────┘

Trigger:
  - PR to main
  - Changes in: server/**, server/tools/**, scripts/**

Steps (in order):

1) Install dependencies
   - uv sync / pip install
   - Ensure OpenCV and test deps available

2) Plugin validation
   - uv run python server/tools/validate_plugins.py
   - Fails if any plugin is invalid

3) Pipeline validation
   - uv run python server/tools/validate_pipelines.py
   - Fails if any pipeline (including yolo_ocr) is invalid

4) Governance validation
   - uv run python server/tools/validate_video_batch_path.py
   - Fails on:
       • forbidden vocabulary (job_id, queue, redis, tracking, etc.)
       • phase‑named files in server/app/** or server/tools/**

5) Test suite (video scope)
   - uv run pytest server/app/tests/video -q
   - Runs:
       • Unit tests
       • Integration tests
       • Regression tests
       • Stress/fuzz (if not marked separate)

6) (Optional) Full test suite
   - uv run pytest -q
   - Ensures Phase‑15 changes don’t break other areas

Outcome:
  - CI passes only if:
      • Plugins valid
      • Pipelines valid
      • Governance clean
      • All video tests pass
```

If you want, I can also turn this into a `.mmd` Mermaid diagram snippet for your Phase‑15 architecture docs.