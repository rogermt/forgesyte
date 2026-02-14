# Phase 16 Implementation Plan
**Status**: ⏳ READY FOR COMMIT 1  
**Date Created**: 2026-02-14  
**Target Completion**: 2026-02-28  
**Duration**: 2 weeks  
**Tech Stack**: SQLAlchemy + Alembic, Python queue.Queue, FastAPI, Local storage (./data/video_jobs/)

---

## Overview

Phase 16 introduces **asynchronous job processing** with:
- A persistent job table (SQLAlchemy) with 8 fields
- A FIFO job queue (Python queue.Queue, in-memory, ephemeral)
- A long-running worker process (single threaded)
- Polling-based status + results APIs
- Local filesystem object storage (./data/video_jobs/)

This transforms the system from synchronous (submit → wait → results) to asynchronous (submit → get job_id → poll for status).

## 6 Architectural Questions (ANSWERED FROM CODEBASE)

1. **SQLAlchemy ORM Setup?**
   - ✅ FINDING: `app/models.py` uses ONLY Pydantic (no SQLAlchemy ORM currently)
   - **DECISION**: Commit 1 will CREATE new `app/models/job.py` with SQLAlchemy ORM + Enum
   - New section in models.py, import as: `from app.models import Job, JobStatus`

2. **Database Connection?**
   - ✅ FINDING: No alembic.ini or migrations/ folder exists
   - **DECISION**: Commit 1 will CREATE Alembic setup from scratch:
     - `alembic init -t async app/migrations`
     - `app/alembic.ini` (configure for SQLite dev, Postgres prod)
     - `app/migrations/versions/` (timestamp-based migration files)

3. **Session Fixture?**
   - ✅ FINDING: conftest.py (618 lines) provides `MockJobStore` and `MockTaskProcessor`, NOT real SQLAlchemy session
   - **DECISION**: Commit 1 tests will use `pytest.mark.asyncio` + in-memory SQLite fixture:
     ```python
     @pytest.fixture
     async def db_session():
         """In-memory SQLite session for unit tests."""
         engine = create_async_engine("sqlite+aiosqlite:///:memory:")
         async with engine.begin() as conn:
             await conn.run_sync(Base.metadata.create_all)
         async_session = AsyncSession(engine)
         yield async_session
         await async_session.close()
     ```

4. **Test Database Location?**
   - ✅ FINDING: Project pattern is "local filesystem for dev" (from AGENTS.md dependency table)
   - **DECISION**:
     - **Unit tests**: In-memory SQLite (`:memory:`) per test, via fixture
     - **Integration tests**: Persistent `data/forgesyte.db` (SQLite, same as dev)
     - **CI**: Uses in-memory SQLite (no persistence needed)
     - **Production**: Postgres (configured in settings, out of scope for Phase 16)

5. **Routes Location?**
   - ✅ FINDING: Video routes ALREADY EXIST at `/app/api_routes/routes/video_file_processing.py` (Phase 15)
   - **DECISION**: Commit 4 will ADD `/video/submit`, `/video/status/{job_id}`, `/video/results/{job_id}` to SAME file
   - Path: `app/api_routes/routes/video_file_processing.py` (extend existing router, don't create new file)
   - Import in main.py already exists (line 40, 276)

6. **Import Path?**
   - ✅ FINDING: models.py defines all Pydantic models in one file (no job.py submodule yet)
   - **DECISION**: Follow existing pattern:
     - Define SQLAlchemy Job in: `app/models.py` (new section after Pydantic models)
     - Import as: `from app.models import Job, JobStatus`
     - Section header: `# =============================================================================\n# Phase 16: SQLAlchemy ORM Models\n# =============================================================================`

---

## 10-Commit Implementation Plan

### **Commit 1: Job Model + DB Migration**
**Goal**: Establish job persistence layer  
**Time**: 2-3 hours  
**Owner**: Backend Lead  
**TDD**: Write tests first, then implement

**Phase 1: Write Failing Tests**
- [ ] Create `server/app/tests/models/test_job.py` with test suite:
  - `test_job_creation()` - Assert Job can be instantiated with all fields
  - `test_job_status_enum()` - Assert status has 4 valid values (pending, running, completed, failed)
  - `test_job_default_status_pending()` - Assert default status is pending
  - `test_job_get_by_id()` - Assert can retrieve job by ID from DB
  - `test_job_update_status()` - Assert status can be updated
  - `test_job_save()` - Assert job persists to database
  - `test_job_timestamps_auto()` - Assert created_at, updated_at are auto-managed
  - All tests should **FAIL** (model doesn't exist yet)
- [ ] Run tests: `uv run pytest server/app/tests/models/test_job.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Create Job + JobStatus in `app/models.py` (extend existing file, don't create submodule):
   - Add new section header: `# Phase 16: SQLAlchemy ORM Models`
   - Import: `from sqlalchemy import Column, String, Enum, DateTime, UUID`
   - `JobStatus` enum with 4 values: pending, running, completed, failed
   - `Job` SQLAlchemy Base model with **exact schema**:
     - job_id: UUID (PK, auto-generated, server_default=uuid4)
     - status: Enum (default=pending)
     - pipeline_id: String (required)
     - input_path: String (required)
     - output_path: String (nullable)
     - error_message: String (nullable)
     - created_at: DateTime (auto, server_default=datetime.utcnow)
     - updated_at: DateTime (auto, onupdate=datetime.utcnow)
   - See scaffold code in PHASE_16_COMMIT_SCAFFOLDINGS.md
- [ ] Create Alembic migration (from scratch, Commit 1 creates first migration):
   - `alembic init -t async app/migrations` (if not exists)
   - Create `app/migrations/versions/<timestamp>_create_job_table.py`
   - Use `op.create_table()` with exact column definitions
   - Include UUID enum creation (if needed for target DB)
   - See scaffold code in PHASE_16_COMMIT_SCAFFOLDINGS.md
- [ ] Create `app/core/database.py` (async SQLAlchemy session):
   - AsyncEngine for SQLite dev (sqlite+aiosqlite:///:memory: or data/forgesyte.db)
   - AsyncSession factory
   - See scaffold code
- [ ] Run migration locally: `cd server && alembic upgrade head`
- [ ] Verify table in DB: `sqlite3 data/forgesyte.db ".tables"` (should show 'job')

**Phase 3: Verify Tests Pass**
- [ ] Run tests: `cd server && uv run pytest app/tests/models/test_job.py -v` (expect all ✅)
- [ ] Run with coverage: `cd server && uv run pytest app/tests/models/test_job.py --cov` (target: 80%+)
- [ ] Run pytest markers: `cd server && uv run pytest app/tests/models/test_job.py -m unit -v`
- [ ] Verify migration is idempotent: `alembic downgrade base && alembic upgrade head`

**Phase 4: Pre-Commit Verification (MANDATORY)**
- [ ] `uv run pre-commit run --all-files` ✅ (black, ruff, mypy)
- [ ] `cd server && uv run pytest tests/execution -v` ✅ (governance tests)
- [ ] `python scripts/scan_execution_violations.py` ✅ (no Phase-17 vocabulary)
- [ ] `cd web-ui && npm run type-check` ✅ (if web-ui files touched)
- All 4 checks passing before commit to main

**Acceptance Criteria**:
- [ ] `tests/models/test_job.py` created and all passing
- [ ] Job table created with correct schema
- [ ] Migration script is idempotent
- [ ] ORM model has CRUD methods
- [ ] No worker logic
- [ ] No queue logic
- [ ] All 4 pre-commit checks passing

---

### **Commit 2: Object Storage Adapter**
**Goal**: Decouple MP4 file handling from filesystem  
**Time**: 2-3 hours  
**Owner**: Backend Lead  
**TDD**: Write tests first, then implement

**Phase 1: Write Failing Tests**
- [ ] Create `tests/services/storage/test_local_storage.py`:
  - `test_save_file()` - Assert file is saved and path returned
  - `test_load_file()` - Assert saved file can be retrieved
  - `test_delete_file()` - Assert file can be deleted
  - `test_path_deterministic()` - Assert path is `video_jobs/{name}`
  - `test_temp_cleanup()` - Assert temp files cleaned up
  - All tests should **FAIL** (implementation doesn't exist)
- [ ] Run tests: `uv run pytest tests/services/storage/test_local_storage.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Create `app/services/storage/base.py`:
  - Abstract `StorageService` class
  - Methods: `save_file(src, dest_path)`, `load_file(path)`, `delete_file(path)`
- [ ] Create `app/services/storage/local_storage.py`:
  - Filesystem implementation using pathlib
  - Paths: `video_jobs/{job_id}.mp4`
  - Handles temp directories for tests

**Phase 3: Verify Tests Pass**
- [ ] Run tests: `uv run pytest tests/services/storage/test_local_storage.py -v` (expect all ✅)
- [ ] Run with coverage: `uv run pytest tests/services/storage/ --cov`
- [ ] Target: 100% coverage on storage service

**Phase 4: Pre-Commit Verification**
- [ ] `uv run pre-commit run --all-files` ✅
- [ ] `cd server && uv run pytest tests/execution -v` ✅
- [ ] `python scripts/scan_execution_violations.py` ✅
- [ ] All 4 checks passing before commit

**Acceptance Criteria**:
- [ ] `tests/services/storage/test_local_storage.py` created and all passing
- [ ] StorageService interface created
- [ ] Local filesystem implementation working
- [ ] Deterministic path structure: `video_jobs/{job_id}.mp4`
- [ ] Unit tests passing with 100% coverage
- [ ] All 4 pre-commit checks passing

---

### **Commit 3: Queue Adapter**
**Goal**: Decouple job dispatch from queue backend  
**Time**: 2-3 hours  
**Owner**: Backend Lead  
**TDD**: Write tests first, then implement

**Phase 1: Write Failing Tests**
- [ ] Create `tests/services/queue/test_memory_queue.py`:
  - `test_enqueue()` - Assert job_id is enqueued
  - `test_dequeue()` - Assert job_id is dequeued
  - `test_fifo_order()` - Assert FIFO ordering (3 jobs)
  - `test_dequeue_empty()` - Assert None returned when empty
  - `test_size()` - Assert queue size is correct
  - `test_thread_safety()` - Assert concurrent access is safe
  - All tests should **FAIL**
- [ ] Run tests: `uv run pytest tests/services/queue/test_memory_queue.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Create `app/services/queue/base.py`:
  - Abstract `QueueService` class
  - Methods: `enqueue(job_id)`, `dequeue()`, `size()`
- [ ] Create `app/services/queue/memory_queue.py`:
  - In-memory FIFO implementation using `queue.Queue`
  - Thread-safe with locks
  - Non-blocking dequeue with timeout

**Phase 3: Verify Tests Pass**
- [ ] Run tests: `uv run pytest tests/services/queue/test_memory_queue.py -v` (expect all ✅)
- [ ] Run with coverage: `uv run pytest tests/services/queue/ --cov`
- [ ] Target: 100% coverage on queue service

**Phase 4: Pre-Commit Verification**
- [ ] `uv run pre-commit run --all-files` ✅
- [ ] `cd server && uv run pytest tests/execution -v` ✅
- [ ] `python scripts/scan_execution_violations.py` ✅
- [ ] All 4 checks passing before commit

**Acceptance Criteria**:
- [ ] `tests/services/queue/test_memory_queue.py` created and all passing
- [ ] QueueService interface created
- [ ] In-memory implementation working
- [ ] FIFO ordering verified
- [ ] Thread-safety tested
- [ ] Unit tests passing with 100% coverage
- [ ] All 4 pre-commit checks passing

---

### **Commit 4: Job Submission Endpoint**
**Goal**: API consumers can submit videos  
**Time**: 3-4 hours  
**Owner**: Backend Lead + API Engineer  
**TDD**: Write tests first, then implement

**Phase 1: Write Failing Tests**
- [ ] Create `tests/api/test_job_submit.py`:
  - `test_submit_valid_mp4()` - Assert POST returns job_id
  - `test_submit_creates_job_row()` - Assert job created in DB
  - `test_submit_saves_file()` - Assert MP4 saved to storage
  - `test_submit_enqueues_job()` - Assert job_id enqueued
  - `test_submit_invalid_file()` - Assert rejects non-MP4
  - `test_submit_response_schema()` - Assert response is `{job_id}`
  - All tests should **FAIL**
- [ ] Create `tests/fixtures/tiny.mp4` (small valid MP4 file)
- [ ] Run tests: `uv run pytest tests/api/test_job_submit.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Extend `app/api_routes/routes/video_file_processing.py` (Phase 15 file already exists):
   - Add `JobSubmitRequest` schema (accepts MP4 file upload)
   - Add `JobSubmitResponse` schema with job_id
   - Add `POST /video/submit` endpoint to existing router:
     - Accept MP4 file upload (multipart/form-data)
     - Validate file format (magic bytes: `ftyp`)
     - Save via StorageService to `video_jobs/{job_id}.mp4`
     - Create Job in database (status=pending)
     - Enqueue job_id to queue
     - Return `{job_id}`
   - Note: This extends existing video_file_processing.py, don't create new file
   - Router already imported in main.py (line 40, 276)

**Phase 3: Verify Tests Pass**
- [ ] Run tests: `uv run pytest tests/api/test_job_submit.py -v` (expect all ✅)
- [ ] Run with coverage: `uv run pytest tests/api/test_job_submit.py --cov`
- [ ] Target: 100% coverage on submission endpoint

**Phase 4: Pre-Commit Verification**
- [ ] `uv run pre-commit run --all-files` ✅
- [ ] `cd server && uv run pytest tests/execution -v` ✅
- [ ] `python scripts/scan_execution_violations.py` ✅
- [ ] All 4 checks passing before commit

**Acceptance Criteria**:
- [ ] `tests/api/test_job_submit.py` created and all passing
- [ ] POST /video/submit works end-to-end
- [ ] File validation working (rejects non-MP4)
- [ ] Job created in database with status=pending
- [ ] Job enqueued
- [ ] Client receives `{job_id}`
- [ ] Integration tests passing with 100% coverage
- [ ] All 4 pre-commit checks passing

---

### **Commit 5: Worker Skeleton**
**Goal**: Worker can dequeue and mark jobs as running  
**Time**: 3-4 hours  
**Owner**: Worker Engineer  
**TDD**: Write tests first, then implement

**Phase 1: Write Failing Tests**
- [ ] Create `tests/workers/test_job_worker.py`:
  - `test_worker_dequeue()` - Assert job_id is dequeued
  - `test_worker_status_transition()` - Assert pending → running
  - `test_worker_empty_queue()` - Assert returns False if queue empty
  - `test_worker_job_not_found()` - Assert handles missing job gracefully
  - `test_worker_run_once_returns_bool()` - Assert returns True/False
  - All tests should **FAIL** (worker doesn't exist)
- [ ] Create mock fixtures: mock QueueService, mock DB
- [ ] Run tests: `uv run pytest tests/workers/test_job_worker.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Create `app/workers/worker.py`:
  - `JobWorker` class with constructor (queue, storage, db)
  - `run_once()` - Dequeue job_id, load from DB, mark running, return True/False
  - `run_forever()` - Loop with sleep/backoff
  - Error handling + logging
- [ ] Create `app/workers/worker_runner.py`:
  - Entry point for worker process
  - Initialization (DB, queue, pipeline service)
  - Signal handlers (SIGINT, SIGTERM)
  - Graceful shutdown

**Phase 3: Verify Tests Pass**
- [ ] Run tests: `uv run pytest tests/workers/test_job_worker.py -v` (expect all ✅)
- [ ] Run with coverage: `uv run pytest tests/workers/ --cov`
- [ ] Target: 100% coverage on worker logic

**Phase 4: Pre-Commit Verification**
- [ ] `uv run pre-commit run --all-files` ✅
- [ ] `cd server && uv run pytest tests/execution -v` ✅
- [ ] `python scripts/scan_execution_violations.py` ✅
- [ ] All 4 checks passing before commit

**Acceptance Criteria**:
- [ ] `tests/workers/test_job_worker.py` created and all passing
- [ ] Worker pulls from queue
- [ ] Job status transitions pending → running
- [ ] Worker handles empty queue (sleep/backoff)
- [ ] Signal handlers working
- [ ] Graceful shutdown implemented
- [ ] Unit tests passing with 100% coverage
- [ ] All 4 pre-commit checks passing

---

### **Commit 6: Worker Executes Phase-15 Pipeline**
**Goal**: Worker processes MP4 using VideoFilePipelineService  
**Time**: 4-5 hours  
**Owner**: Worker Engineer  
**TDD**: Write tests first, then implement

**Phase 1: Write Failing Tests**
- [ ] Create `tests/workers/test_worker_pipeline.py`:
  - `test_worker_loads_mp4()` - Assert MP4 loaded from storage
  - `test_worker_calls_pipeline()` - Assert VideoFilePipelineService called
  - `test_worker_saves_results()` - Assert results saved to storage
  - `test_worker_status_completed()` - Assert status → completed on success
  - `test_worker_status_failed()` - Assert status → failed on exception
  - `test_worker_error_message()` - Assert error_message stored
  - `test_results_deterministic()` - Assert JSON output is deterministic
  - All tests should **FAIL**
- [ ] Create fixture: `tests/fixtures/make_tiny_mp4.py` (generate small test MP4)
- [ ] Run tests: `uv run pytest tests/workers/test_worker_pipeline.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Create `app/services/results_serializer.py`:
  - Convert Phase-15 results to deterministic JSON
  - Serialize with sorted keys
- [ ] Update `app/workers/worker.py` `run_once()`:
  - Load MP4 via StorageService
  - Instantiate VideoFilePipelineService
  - Call `run_on_file(file_path, pipeline_id="yolo_ocr")`
  - Serialize results with ResultsSerializer
  - Save to `video_jobs/{job_id}_results.json`
  - Update job: output_path, status → completed
  - On exception: status → failed + error_message
- [ ] Add error handling for transient/permanent errors

**Phase 3: Verify Tests Pass**
- [ ] Run tests: `uv run pytest tests/workers/test_worker_pipeline.py -v` (expect all ✅)
- [ ] Run with coverage: `uv run pytest tests/workers/test_worker_pipeline.py --cov`
- [ ] Target: 100% coverage on pipeline execution

**Phase 4: Pre-Commit Verification**
- [ ] `uv run pre-commit run --all-files` ✅
- [ ] `cd server && uv run pytest tests/execution -v` ✅
- [ ] `python scripts/scan_execution_violations.py` ✅
- [ ] All 4 checks passing before commit

**Acceptance Criteria**:
- [ ] `tests/workers/test_worker_pipeline.py` created and all passing
- [ ] Worker runs VideoFilePipelineService on MP4
- [ ] Results stored deterministically as JSON
- [ ] Job status transitions pending → running → completed
- [ ] Exceptions handled: status → failed + error_message
- [ ] Results match Phase-15 format
- [ ] Integration tests passing with 100% coverage
- [ ] All 4 pre-commit checks passing

---

### **Commit 7: Job Status Endpoint**
**Goal**: Clients can poll job status  
**Time**: 2-3 hours  
**Owner**: API Engineer  
**TDD**: Write tests first, then implement

**Phase 1: Write Failing Tests**
- [ ] Create `tests/api/test_job_status.py`:
  - `test_status_pending()` - Assert status=pending, progress=0
  - `test_status_running()` - Assert status=running, progress=0.5
  - `test_status_completed()` - Assert status=completed, progress=1.0
  - `test_status_failed()` - Assert status=failed, progress=1.0
  - `test_status_response_schema()` - Assert response includes job_id, status, progress, timestamps
  - `test_status_not_found()` - Assert 404 for missing job_id
  - All tests should **FAIL**
- [ ] Run tests: `uv run pytest tests/api/test_job_status.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Extend `app/api_routes/routes/video_file_processing.py` (same file as Commits 4, 8):
   - Add `JobStatusResponse` schema with job_id, status, progress, created_at, updated_at
   - Add `GET /video/status/{job_id}` endpoint to existing router:
     - Load Job from DB (raise 404 if not found)
     - Calculate progress: 0 (pending), 0.5 (running), 1.0 (completed/failed)
     - Return response with all fields

**Phase 3: Verify Tests Pass**
- [ ] Run tests: `uv run pytest tests/api/test_job_status.py -v` (expect all ✅)
- [ ] Run with coverage: `uv run pytest tests/api/test_job_status.py --cov`
- [ ] Target: 100% coverage on status endpoint

**Phase 4: Pre-Commit Verification**
- [ ] `uv run pre-commit run --all-files` ✅
- [ ] `cd server && uv run pytest tests/execution -v` ✅
- [ ] `python scripts/scan_execution_violations.py` ✅
- [ ] All 4 checks passing before commit

**Acceptance Criteria**:
- [ ] `tests/api/test_job_status.py` created and all passing
- [ ] GET /video/status/{job_id} works
- [ ] Progress is coarse (0, 0.5, 1.0)
- [ ] Returns correct status values
- [ ] Returns 404 for missing jobs
- [ ] Response includes all required fields
- [ ] Integration tests passing with 100% coverage
- [ ] All 4 pre-commit checks passing

---

### **Commit 8: Job Results Endpoint**
**Goal**: Clients can retrieve completed results  
**Time**: 2-3 hours  
**Owner**: API Engineer  
**TDD**: Write tests first, then implement

**Phase 1: Write Failing Tests**
- [ ] Create `tests/api/test_job_results.py`:
  - `test_results_completed()` - Assert results returned for completed job
  - `test_results_pending()` - Assert 404 for pending job
  - `test_results_running()` - Assert 404 for running job
  - `test_results_failed()` - Assert 404 for failed job
  - `test_results_not_found()` - Assert 404 for missing job
  - `test_results_response_schema()` - Assert response includes job_id, results, timestamps
  - `test_results_format_matches_phase15()` - Assert results match Phase-15 structure
  - All tests should **FAIL**
- [ ] Run tests: `uv run pytest tests/api/test_job_results.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Extend `app/api_routes/routes/video_file_processing.py` (same file as Commits 4, 7):
   - Add `JobResultsResponse` schema with job_id, results, created_at, updated_at
   - Add `GET /video/results/{job_id}` endpoint to existing router:
     - Load Job from DB (raise 404 if not found)
     - Check status == "completed" (raise 404 if not)
     - Load results from object storage (`video_jobs/{job_id}_results.json`)
     - Return response with all fields

**Phase 3: Verify Tests Pass**
- [ ] Run tests: `uv run pytest tests/api/test_job_results.py -v` (expect all ✅)
- [ ] Run with coverage: `uv run pytest tests/api/test_job_results.py --cov`
- [ ] Target: 100% coverage on results endpoint

**Phase 4: Pre-Commit Verification**
- [ ] `uv run pre-commit run --all-files` ✅
- [ ] `cd server && uv run pytest tests/execution -v` ✅
- [ ] `python scripts/scan_execution_violations.py` ✅
- [ ] All 4 checks passing before commit

**Acceptance Criteria**:
- [ ] `tests/api/test_job_results.py` created and all passing
- [ ] GET /video/results/{job_id} works for completed jobs
- [ ] Returns 404 for pending/running/failed jobs
- [ ] Returns 404 for missing jobs
- [ ] Results match Phase-15 format
- [ ] Response includes all required fields
- [ ] Integration tests passing with 100% coverage
- [ ] All 4 pre-commit checks passing

---

### **Commit 9: Governance + CI Enforcement**
**Goal**: Prevent Phase-17 concepts from entering codebase  
**Time**: 3-4 hours  
**Owner**: DevOps + Release Manager  
**TDD**: Write tests first, then implement

**Phase 1: Write Failing Tests**
- [ ] Create `tests/execution/test_phase16_governance.py`:
  - `test_no_websockets()` - Assert "websocket" not in Phase-16 code
  - `test_no_streaming()` - Assert "streaming" not in Phase-16 code
  - `test_no_gpu_scheduling()` - Assert "gpu_schedule" not in Phase-16 code
  - `test_no_distributed()` - Assert "distributed" not in Phase-16 code
  - `test_governance_scanner_runs()` - Assert governance scanner exits 0
  - All tests should **FAIL** (scanner doesn't exist yet)
- [ ] Run tests: `uv run pytest tests/execution/test_phase16_governance.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Create `server/tools/forbidden_vocabulary_phase16.yaml`:
  - Forbidden terms: websocket, streaming, gpu_schedule, distributed, gpu_worker
  - Allowed terms: job_queue, async, worker, polling
- [ ] Create/update `server/tools/validate_phase16_path.py`:
  - Scan functional code for forbidden vocabulary
  - Report violations with file:line
  - Exit code 0 (clean) or 1 (violations)
- [ ] Create `.github/workflows/phase16_validation.yml`:
  - Runs on every PR to main
  - Step 1: forbidden vocabulary scanner
  - Step 2: plugin registry validator
  - Step 3: pytest suite
  - Blocks merge on failure
- [ ] Update `scripts/smoke_test.py`:
  - Test POST /video/submit → get job_id
  - Test GET /video/status/{job_id} → status updates
  - Test GET /video/results/{job_id} → results retrieved

**Phase 3: Verify Tests Pass**
- [ ] Run tests: `uv run pytest tests/execution/test_phase16_governance.py -v` (expect all ✅)
- [ ] Run governance scanner: `python scripts/scan_execution_violations.py` (expect 0 violations)
- [ ] Run smoke test: `bash scripts/smoke_test.sh` (expect all passing)

**Phase 4: Pre-Commit Verification**
- [ ] `uv run pre-commit run --all-files` ✅
- [ ] `cd server && uv run pytest tests/execution -v` ✅
- [ ] `python scripts/scan_execution_violations.py` ✅
- [ ] All 4 checks passing before commit

**Acceptance Criteria**:
- [ ] `tests/execution/test_phase16_governance.py` created and all passing
- [ ] Forbidden vocabulary scanner working
- [ ] CI workflow enforces governance
- [ ] Smoke test updated and passing
- [ ] No Phase-17 concepts in code
- [ ] Governance tests passing with 100% coverage
- [ ] All 4 pre-commit checks passing

---

### **Commit 10: Documentation + Rollback Plan**
**Goal**: New contributors can understand and onboard to Phase-16  
**Time**: 3-4 hours  
**Owner**: Technical Writer + Release Manager  
**TDD**: Write tests first, then implement

**Phase 1: Write Failing Tests**
- [ ] Create `tests/documentation/test_phase16_docs.py`:
  - `test_overview_exists()` - Assert PHASE_16_OVERVIEW.md exists
  - `test_architecture_exists()` - Assert PHASE_16_ARCHITECTURE.md exists
  - `test_rollback_plan_exists()` - Assert PHASE_16_ROLLBACK_PLAN.md exists
  - `test_endpoints_doc_exists()` - Assert PHASE_16_ENDPOINTS.md exists
  - `test_contributor_exam_exists()` - Assert PHASE_16_CONTRIBUTOR_EXAM.md exists
  - `test_rollback_plan_is_executable()` - Assert rollback steps are clear
  - All tests should **FAIL** (docs don't exist yet)
- [ ] Run tests: `uv run pytest tests/documentation/test_phase16_docs.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Create `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_OVERVIEW.md`
  - Executive summary, architecture diagram, data flow, key decisions
- [ ] Create `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_ARCHITECTURE.md`
  - Component diagrams, integration points, state transitions
- [ ] Create `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_ROLLBACK_PLAN.md`
  - Files to delete: job model, migrations, worker, endpoints
  - Modifications to revert: imports, route registration
  - Step-by-step rollback procedure
  - Verification steps
- [ ] Create `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_ENDPOINTS.md`
  - API specification, request/response examples, error codes
- [ ] Create `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_CONTRIBUTOR_EXAM.md`
  - 20-question exam on architecture, governance, testing
  - Answer key
- [ ] Update `RELEASE_NOTES.md` with Phase-16 entry

**Phase 3: Verify Tests Pass**
- [ ] Run tests: `uv run pytest tests/documentation/test_phase16_docs.py -v` (expect all ✅)
- [ ] Review rollback plan: verify all files/modifications listed
- [ ] Test rollback plan on staging environment (if possible)

**Phase 4: Pre-Commit Verification**
- [ ] `uv run pre-commit run --all-files` ✅
- [ ] `cd server && uv run pytest tests/execution -v` ✅
- [ ] `python scripts/scan_execution_violations.py` ✅
- [ ] All 4 checks passing before commit

**Acceptance Criteria**:
- [ ] `tests/documentation/test_phase16_docs.py` created and all passing
- [ ] All Phase-16 documentation created and linked
- [ ] Rollback plan is executable and tested
- [ ] Rollback plan lists exact files/modifications
- [ ] New contributors can pass exam
- [ ] Release notes updated
- [ ] Documentation tests passing with 100% coverage
- [ ] All 4 pre-commit checks passing

---

## Definition of Done

Phase 16 is complete when:

✅ **Functional**:
- POST /video/submit → get job_id
- GET /video/status/{job_id} → current status
- GET /video/results/{job_id} → completed results
- Worker processes jobs end-to-end

✅ **Tested**:
- Unit tests: job model, queue, storage, worker
- Integration tests: submit → worker → results
- System tests: full lifecycle
- Smoke tests passing

✅ **Governed**:
- No forbidden vocabulary
- CI workflow enforcing rules
- All tests passing
- Pre-commit hooks passing

✅ **Documented**:
- Architecture, scope, endpoints documented
- Rollback plan written
- Release notes updated

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Database migration fails in production | Low | High | Test migration in staging, rollback plan |
| Worker crashes lose jobs | Low | High | Job persistence, idempotency checks |
| Queue fills up | Medium | Medium | Monitor queue size, scale workers |
| Phase-17 concepts leak into code | Medium | High | Governance scanner, code review |
| Test coverage insufficient | Low | Medium | Require 80%+ coverage, governance checks |

---

## Success Metrics

- [ ] All 10 commits merged to main
- [ ] All tests passing (100% green)
- [ ] 0 governance violations
- [ ] Smoke test passing
- [ ] 100% CI passing
- [ ] Documentation complete

---

## Dependencies

| Dependency | Status | Owner | Notes |
|------------|--------|-------|-------|
| Phase-15 VideoFilePipelineService | Complete | Video Team | Used by worker |
| Database infrastructure | Complete | DevOps | SQLite for dev, Postgres for prod |
| Object storage (local/S3) | Complete | DevOps | Local filesystem for dev |
| Queue infrastructure (in-memory/Redis) | Complete | DevOps | In-memory for dev |

---

## Timeline

| Week | Commits | Status |
|------|---------|--------|
| Week 1 (Feb 14-20) | 1-5 | Scheduled |
| Week 2 (Feb 21-27) | 6-10 | Scheduled |
| Week 3 (Feb 28) | Review + Merge | Scheduled |

---

## References

- `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_OVERVIEW.md` - Feature overview
- `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_USER_STORIES.md` - Detailed story breakdown
- `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_GOVERNANCE_RULES.md` - Governance rules
- `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_DEFINITION_OF_DONE.md` - DoD checklist
