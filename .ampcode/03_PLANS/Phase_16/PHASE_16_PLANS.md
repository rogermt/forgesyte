# Phase 16 Implementation Plan (CORRECTED)
**Status**: ✅ APPROVED - READY FOR COMMIT 1  
**Date Created**: 2026-02-14  
**Target Completion**: 2026-02-28  
**Duration**: 2 weeks  
**Tech Stack**: DuckDB + SQLAlchemy, Alembic migrations, Python queue.Queue, FastAPI, Local storage (./data/video_jobs/)  
**AUTHORITY**: User Stories + Q&A + Scaffolding (PHASE_16_USER_STORIES.md, PHASE_16_DEV_Q&A_01.md, PHASE_16_COMMIT_SCAFFOLDINGS.md)

---

## Overview

Phase 16 introduces **asynchronous job processing** with:
- A persistent job table (SQLAlchemy ORM + DuckDB) with 8 fields
- A FIFO job queue (Python queue.Queue, in-memory, ephemeral)
- A long-running worker process (single threaded)
- Polling-based status + results APIs
- Local filesystem object storage (./data/video_jobs/)

This transforms the system from synchronous (submit → wait → results) to asynchronous (submit → get job_id → poll for status).

**Key Architecture Decisions (Locked)**:
- **Database**: DuckDB (project already uses it, do NOT introduce SQLite/PostgreSQL)
- **ORM**: SQLAlchemy with shared `Base` from `app/core/database.py`
- **Migrations**: Alembic from scratch (none exists in codebase)
- **Routes**: `server/app/api_routes/routes/` (matches Phase-15 pattern, NOT `api/routes/`)
- **Test DB**: In-memory DuckDB (`duckdb:///:memory:`) for all tests
- **Session Type**: Synchronous (no `AsyncSession`)

---

## 10-Commit Implementation Plan

### **Commit 1: Job Model + DB Migration**
**Goal**: Establish job persistence layer with DuckDB + Alembic  
**Time**: 2-3 hours  
**Owner**: Backend Lead  
**TDD**: Write tests first, then implement  

**Phase 1: Write Failing Tests**
- [ ] Create `server/tests/app/models/test_job.py` with test suite:
   - `test_job_defaults()` - Assert Job with pending status, auto UUIDs
   - `test_job_status_enum()` - Assert 4 status values work
   - `test_job_persistence()` - Assert job saves/loads from DuckDB
   - `test_job_timestamps_auto()` - Assert created_at, updated_at auto-set
   - All tests **FAIL** (model + DB don't exist yet)
- [ ] Run tests: `cd server && uv run pytest tests/app/models/test_job.py -v` (expect all failures)

**Phase 2: Implement Code**
- [ ] Create `server/app/core/database.py`:
   - Shared `Base = declarative_base()`
   - DuckDB engine: `duckdb:///data/foregsyte.duckdb`
   - SessionLocal sessionmaker (synchronous, NOT async)
   - See scaffold in PHASE_16_COMMIT_01.md
- [ ] Create `server/app/models/job.py`:
   - Import shared `Base` from `app.core.database`
   - `JobStatus` enum: pending, running, completed, failed
   - `Job` SQLAlchemy model with exact 8 fields (see user stories)
   - Use `duckdb_types.UUID` (NOT PostgreSQL UUID)
   - See scaffold in PHASE_16_COMMIT_01.md
- [ ] Initialize Alembic: `cd server && alembic init app/migrations`
- [ ] Create migration file: `app/migrations/versions/<timestamp>_create_job_table.py`
   - Use `duckdb_types.UUID` (NOT PostgreSQL)
   - Create jobs table with exact schema
   - See scaffold in PHASE_16_COMMIT_01.md
- [ ] Add DuckDB test fixtures to `server/tests/app/conftest.py`:
   - `test_engine` fixture: in-memory DuckDB
   - `session` fixture: creates tables, yields session
   - See scaffold in PHASE_16_COMMIT_01.md

**Phase 3: Verify Tests Pass**
- [ ] Run failing tests: `cd server && uv run pytest tests/app/models/test_job.py -v` (expect all failures)
- [ ] Run migration: `cd server && alembic upgrade head`
- [ ] Verify `data/foregsyte.duckdb` created
- [ ] Run tests again: `cd server && uv run pytest tests/app/models/test_job.py -v` (expect all ✅)
- [ ] Run with coverage: `cd server && uv run pytest tests/app/models/test_job.py --cov=app.models` (target: 80%+)
- [ ] Verify migration idempotent: `alembic downgrade base && alembic upgrade head`

**Phase 4: Pre-Commit Verification (MANDATORY)**
- [ ] `uv run pre-commit run --all-files` ✅ (black, ruff, mypy)
- [ ] `cd server && uv run pytest tests/execution -v` ✅ (governance tests)
- [ ] `python scripts/scan_execution_violations.py` ✅ (no Phase-17 vocabulary)
- [ ] `cd server && uv run pytest tests/ -v --tb=short` ✅ (full suite green)

**Acceptance Criteria**:
- [ ] `tests/app/models/test_job.py` created and ALL tests passing (not skipped)
- [ ] Job table created in DuckDB with correct 8-field schema
- [ ] Migration is idempotent (can upgrade/downgrade)
- [ ] `app/core/database.py` provides shared Base
- [ ] No separate `declarative_base()` in `job.py`
- [ ] DuckDB types used (NOT PostgreSQL)
- [ ] No `AsyncSession`
- [ ] All 4 pre-commit checks passing
- [ ] Zero governance violations

---

### **Commit 2: Object Storage Adapter**
**Goal**: Decouple MP4 file handling from filesystem  
**Time**: 2-3 hours  
**Owner**: Backend Lead  
**TDD**: Write tests first, then implement  

**Phase 1: Write Failing Tests**
- [ ] Create `server/tests/app/services/storage/test_local_storage.py`:
   - `test_save_file()` - Assert file saved and path returned
   - `test_load_file()` - Assert saved file retrievable
   - `test_delete_file()` - Assert file can be deleted
   - `test_path_structure()` - Assert paths deterministic: `video_jobs/{name}`
   - All tests **FAIL** (implementation doesn't exist)
- [ ] Run tests: `cd server && uv run pytest tests/app/services/storage/test_local_storage.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Create `server/app/services/storage/base.py`:
   - Abstract `StorageService` class
   - Methods: `save_file(src, dest_path)`, `load_file(path)`, `delete_file(path)`
   - See scaffold in PHASE_16_COMMIT_SCAFFOLDINGS.md
- [ ] Create `server/app/services/storage/local_storage.py`:
   - Filesystem implementation using pathlib
   - Paths: `video_jobs/{job_id}.mp4`, `video_jobs/{job_id}_results.json`
   - See scaffold in PHASE_16_COMMIT_SCAFFOLDINGS.md

**Phase 3: Verify Tests Pass**
- [ ] Run tests: `cd server && uv run pytest tests/app/services/storage/test_local_storage.py -v` (expect all ✅)
- [ ] Run with coverage: `cd server && uv run pytest tests/app/services/storage/ --cov=app.services.storage`
- [ ] Target: 100% coverage

**Phase 4: Pre-Commit Verification**
- [ ] `uv run pre-commit run --all-files` ✅
- [ ] `cd server && uv run pytest tests/execution -v` ✅
- [ ] `python scripts/scan_execution_violations.py` ✅
- [ ] All 4 checks passing

**Acceptance Criteria**:
- [ ] `tests/app/services/storage/test_local_storage.py` created and all passing
- [ ] StorageService interface complete
- [ ] Local filesystem implementation working
- [ ] Deterministic paths: `video_jobs/{job_id}.mp4`
- [ ] Unit tests 100% coverage

---

### **Commit 3: Queue Adapter**
**Goal**: Decouple job dispatch from queue backend  
**Time**: 2-3 hours  
**Owner**: Backend Lead  
**TDD**: Write tests first, then implement  

**Phase 1: Write Failing Tests**
- [ ] Create `server/tests/app/services/queue/test_memory_queue.py`:
   - `test_enqueue()` - Assert job_id enqueued
   - `test_dequeue()` - Assert job_id dequeued
   - `test_fifo_order()` - Assert FIFO ordering
   - `test_dequeue_empty()` - Assert None when empty
   - `test_size()` - Assert queue size correct
   - All tests **FAIL**
- [ ] Run tests: `cd server && uv run pytest tests/app/services/queue/test_memory_queue.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Create `server/app/services/queue/base.py`:
   - Abstract `QueueService` class
   - Methods: `enqueue(job_id)`, `dequeue()`, `size()`
   - See scaffold in PHASE_16_COMMIT_SCAFFOLDINGS.md
- [ ] Create `server/app/services/queue/memory_queue.py`:
   - In-memory FIFO using `queue.Queue`
   - Thread-safe with locks
   - Non-blocking dequeue with timeout
   - See scaffold in PHASE_16_COMMIT_SCAFFOLDINGS.md

**Phase 3: Verify Tests Pass**
- [ ] Run tests: `cd server && uv run pytest tests/app/services/queue/test_memory_queue.py -v` (expect all ✅)
- [ ] Target: 100% coverage

**Phase 4: Pre-Commit Verification**
- [ ] All 4 checks passing

**Acceptance Criteria**:
- [ ] `tests/app/services/queue/test_memory_queue.py` created and all passing
- [ ] QueueService interface complete
- [ ] In-memory FIFO implementation
- [ ] FIFO order verified
- [ ] 100% coverage

---

### **Commit 4: Job Submission Endpoint**
**Goal**: API consumers can submit videos  
**Time**: 3-4 hours  
**Owner**: Backend Lead + API Engineer  
**TDD**: Write tests first, then implement  

**Phase 1: Write Failing Tests**
- [ ] Create `server/tests/app/api/test_job_submit.py`:
   - `test_submit_valid_mp4()` - Assert POST returns job_id
   - `test_submit_creates_job_row()` - Assert job created in DB
   - `test_submit_saves_file()` - Assert MP4 saved to storage
   - `test_submit_enqueues_job()` - Assert job_id enqueued
   - `test_submit_invalid_file()` - Assert rejects non-MP4
   - All tests **FAIL**
- [ ] Create fixture: `server/tests/fixtures/tiny.mp4` (small valid MP4 file, or use `make_tiny_mp4.py` to generate)
- [ ] Run tests: `cd server && uv run pytest tests/app/api/test_job_submit.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Create route file: `server/app/api_routes/routes/job_submit.py`:
   - `POST /video/submit` endpoint
   - Accept MP4 file upload (multipart/form-data)
   - Validate file format via magic bytes (`ftyp`, NOT extension)
   - Save via StorageService
   - Create Job in database (status=pending)
   - Enqueue job_id to queue
   - Return `{job_id}`
   - See scaffold in PHASE_16_COMMIT_SCAFFOLDINGS.md
- [ ] Register router in `server/app/main.py`:
   - Include router with prefix `/v1` (or appropriate)
   - Ensure route is `/video/submit`
- [ ] Add DuckDB TestClient fixture if not exists
   - API tests must use in-memory DuckDB (`duckdb:///:memory:`)

**Phase 3: Verify Tests Pass**
- [ ] Run tests: `cd server && uv run pytest tests/app/api/test_job_submit.py -v` (expect all ✅)
- [ ] Run with coverage: target 100%

**Phase 4: Pre-Commit Verification**
- [ ] All 4 checks passing

**Acceptance Criteria**:
- [ ] POST /video/submit works end-to-end
- [ ] File validation rejects non-MP4 (magic bytes)
- [ ] Job created in database (status=pending)
- [ ] Job enqueued
- [ ] Client receives `{job_id}`
- [ ] 100% coverage

---

### **Commit 5: Worker Skeleton**
**Goal**: Worker can dequeue and mark jobs as running  
**Time**: 3-4 hours  
**Owner**: Worker Engineer  
**TDD**: Write tests first, then implement  

**Phase 1: Write Failing Tests**
- [ ] Create `server/tests/app/workers/test_job_worker.py`:
   - `test_worker_dequeue()` - Assert job_id dequeued
   - `test_worker_status_transition()` - Assert pending → running
   - `test_worker_empty_queue()` - Assert False if queue empty
   - `test_worker_signal_handling()` - Assert SIGINT/SIGTERM handled
   - All tests **FAIL**
- [ ] Run tests: `cd server && uv run pytest tests/app/workers/test_job_worker.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Create `server/app/workers/worker.py`:
   - JobWorker class with DuckDB session dependency
   - `run_once()` - dequeue, mark running, return bool
   - `run_forever()` - loop with backoff/sleep
   - Signal handlers (SIGINT, SIGTERM)
   - See scaffold in PHASE_16_COMMIT_SCAFFOLDINGS.md
- [ ] Create `server/app/workers/worker_runner.py`:
   - Entry point: `python -m app.workers.worker_runner`
   - Instantiates JobWorker + queue
   - Calls `run_forever()`

**Phase 3: Verify Tests Pass**
- [ ] All tests passing

**Phase 4: Pre-Commit Verification**
- [ ] All 4 checks passing

**Acceptance Criteria**:
- [ ] Worker dequeues job_id
- [ ] Job status transitions pending → running
- [ ] Handles empty queue (sleep/backoff)
- [ ] SIGINT/SIGTERM handled gracefully
- [ ] All tests passing

---

### **Commit 6: Worker Executes Phase-15 Pipeline**
**Goal**: Worker processes MP4 using VideoFilePipelineService  
**Time**: 4-5 hours  
**Owner**: Worker Engineer  
**TDD**: Write tests first, then implement  

**Phase 1: Write Failing Tests**
- [ ] Create `server/tests/app/workers/test_worker_pipeline.py`:
   - `test_worker_loads_mp4()` - Assert MP4 loaded
   - `test_worker_calls_pipeline()` - Assert VideoFilePipelineService called
   - `test_worker_saves_results()` - Assert results saved to storage
   - `test_worker_status_completed()` - Assert status → completed
   - `test_worker_error_handling()` - Assert status → failed on exception
   - All tests **FAIL**
- [ ] Use fixture: `server/tests/fixtures/tiny.mp4` (or generate via `make_tiny_mp4.py`)
- [ ] Run tests: `cd server && uv run pytest tests/app/workers/test_worker_pipeline.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Update `server/app/workers/worker.py`:
   - In `run_once()`, after marking running:
   - Load MP4 via StorageService
   - Call `VideoFilePipelineService.run_on_file(pipeline_id, file_path)`
   - Save results JSON to `video_jobs/{job_id}_results.json`
   - Update job: `output_path`, `status → completed`
   - On exception: `status → failed`, store `error_message`
   - See scaffold in PHASE_16_TEST_SUITE.md

**Phase 3: Verify Tests Pass**
- [ ] All tests passing

**Phase 4: Pre-Commit Verification**
- [ ] All 4 checks passing

**Acceptance Criteria**:
- [ ] Worker runs VideoFilePipelineService
- [ ] Results stored as JSON in object storage
- [ ] Job transitions pending → running → completed/failed
- [ ] Exceptions handled: status → failed + error_message
- [ ] All tests passing

---

### **Commit 7: Job Status Endpoint**
**Goal**: Clients can poll job status  
**Time**: 2-3 hours  
**Owner**: API Engineer  
**TDD**: Write tests first, then implement  

**Phase 1: Write Failing Tests**
- [ ] Create `server/tests/app/api/test_job_status.py`:
   - `test_status_pending()` - Assert pending=0, running=0.5, done=1.0
   - `test_status_response_schema()` - Assert job_id, status, progress, timestamps
   - `test_status_not_found()` - Assert 404
   - All tests **FAIL**
- [ ] Run tests: `cd server && uv run pytest tests/app/api/test_job_status.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Create route file: `server/app/api_routes/routes/job_status.py`:
   - `GET /video/status/{job_id}`
   - Load Job from DB (raise 404 if not found)
   - Calculate progress: pending=0.0, running=0.5, done/failed=1.0
   - Return JSON with job_id, status, progress, timestamps
   - See scaffold in PHASE_16_COMMIT_SCAFFOLDINGS.md
- [ ] Register router in `server/app/main.py`

**Phase 3: Verify Tests Pass**
- [ ] All tests passing

**Phase 4: Pre-Commit Verification**
- [ ] All 4 checks passing

**Acceptance Criteria**:
- [ ] GET /video/status/{job_id} works
- [ ] Progress coarse (0, 0.5, 1.0)
- [ ] 404 for missing jobs
- [ ] All fields returned

---

### **Commit 8: Job Results Endpoint**
**Goal**: Clients can retrieve completed results  
**Time**: 2-3 hours  
**Owner**: API Engineer  
**TDD**: Write tests first, then implement  

**Phase 1: Write Failing Tests**
- [ ] Create `server/tests/app/api/test_job_results.py`:
   - `test_results_completed()` - Assert results for done job
   - `test_results_pending()` - Assert 404 for pending
   - `test_results_not_found()` - Assert 404 for missing
   - All tests **FAIL**
- [ ] Run tests: `cd server && uv run pytest tests/app/api/test_job_results.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Create route file: `server/app/api_routes/routes/job_results.py`:
   - `GET /video/results/{job_id}`
   - Load Job from DB (raise 404 if not found)
   - Check status == "completed" (raise 404 if not)
   - Load results from object storage
   - Return JSON with job_id, results, timestamps
   - See scaffold in PHASE_16_COMMIT_SCAFFOLDINGS.md
- [ ] Register router in `server/app/main.py`

**Phase 3: Verify Tests Pass**
- [ ] All tests passing

**Phase 4: Pre-Commit Verification**
- [ ] All 4 checks passing

**Acceptance Criteria**:
- [ ] GET /video/results/{job_id} works for done jobs
- [ ] 404 for pending/failed
- [ ] Results match Phase-15 format

---

### **Commit 9: Governance + CI Enforcement**
**Goal**: Prevent Phase-17 concepts from entering codebase  
**Time**: 3-4 hours  
**Owner**: DevOps + Release Manager  
**TDD**: Write tests first, then implement  

**Phase 1: Write Failing Tests**
- [ ] Create `server/tests/execution/test_phase16_governance.py`:
   - `test_no_forbidden_vocabulary()` - Assert no websocket/streaming/etc in code
   - `test_governance_scanner_runs()` - Assert scanner exits 0
   - All tests **FAIL** (tools don't exist yet)
- [ ] Run tests: `cd server && uv run pytest tests/execution/test_phase16_governance.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Create `server/tools/forbidden_vocabulary_phase16.yaml`:
   - Forbidden: websocket, streaming, gpu_schedule, distributed, gpu_worker, sse, real_time
   - See scaffold in PHASE_16_COMMIT_SCAFFOLDINGS.md
- [ ] Create `server/tools/validate_phase16_path.py`:
   - Scan functional code for forbidden vocabulary
   - Report violations with file:line
   - Exit 0 (clean) or 1 (violations)
   - See scaffold in PHASE_16_COMMIT_SCAFFOLDINGS.md
- [ ] Create `.github/workflows/phase16_validation.yml`:
   - Runs on PR to main
   - Steps: governance check → plugin validator → pytest → smoke test
   - Blocks merge on failure
   - See scaffold in PHASE_16_COMMIT_SCAFFOLDINGS.md
- [ ] Update `scripts/smoke_test.py`:
   - Test POST /video/submit → get job_id
   - Test GET /video/status/{job_id} → status updates
   - Test GET /video/results/{job_id} → results retrieved
   - See scaffold in PHASE_16_TEST_SUITE.md

**Phase 3: Verify Tests Pass**
- [ ] Run governance tests: `cd server && uv run pytest tests/execution/test_phase16_governance.py -v` (expect all ✅)
- [ ] Run governance scanner: `python server/tools/validate_phase16_path.py` (expect 0 violations)
- [ ] Run smoke test: `bash scripts/smoke_test.py` (expect all passing)

**Phase 4: Pre-Commit Verification**
- [ ] All 4 checks passing

**Acceptance Criteria**:
- [ ] Governance tests passing
- [ ] Forbidden vocabulary scanner working
- [ ] CI workflow enforcing governance
- [ ] Smoke test updated and passing
- [ ] No Phase-17 concepts in code

---

### **Commit 10: Documentation + Rollback Plan**
**Goal**: New contributors understand Phase-16 completely  
**Time**: 3-4 hours  
**Owner**: Technical Writer + Release Manager  
**TDD**: Write tests first, then implement  

**Phase 1: Write Failing Tests**
- [ ] Create `server/tests/documentation/test_phase16_docs.py`:
   - `test_overview_exists()` - Assert PHASE_16_OVERVIEW.md exists
   - `test_rollback_plan_exists()` - Assert rollback plan exists
   - `test_endpoints_doc_exists()` - Assert endpoints doc exists
   - All tests **FAIL** (docs don't exist yet)
- [ ] Run tests: `cd server && uv run pytest tests/documentation/test_phase16_docs.py -v` (expect failures)

**Phase 2: Implement Code**
- [ ] Create `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_OVERVIEW.md`
- [ ] Create `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_ARCHITECTURE.md`
- [ ] Create `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_ENDPOINTS.md`
- [ ] Create `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_ROLLBACK_PLAN.md`:
   - Revert Alembic migration
   - Remove `server/app/core/database.py`
   - Remove all Phase-16 route files
   - Remove `server/app/workers/`
   - Remove `server/app/services/storage/`
   - Remove `server/app/services/queue/`
   - Remove `server/app/models/job.py`
   - Remove `duckdb_engine` from dependencies if no other code uses it
- [ ] Create `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_CONTRIBUTOR_EXAM.md`
   - 20-question exam on architecture, governance, testing
   - Answer key
- [ ] Update `RELEASE_NOTES.md` with Phase-16 entry

**Phase 3: Verify Tests Pass**
- [ ] All documentation tests passing
- [ ] All links verified

**Phase 4: Pre-Commit Verification**
- [ ] All 4 checks passing

**Acceptance Criteria**:
- [ ] All Phase-16 documentation created
- [ ] Rollback plan is executable
- [ ] New contributors can pass exam
- [ ] Release notes updated

---

## Definition of Done

Phase 16 is complete when:

✅ **Functional**:
- POST /video/submit → get job_id
- GET /video/status/{job_id} → current status
- GET /video/results/{job_id} → completed results
- Worker processes jobs end-to-end

✅ **Tested**:
- ALL tests GREEN (not skipped)
- Unit tests: job model, queue, storage, worker
- Integration tests: submit → worker → results
- System tests: full lifecycle
- Smoke test passing

✅ **Governed**:
- No forbidden vocabulary
- CI workflow enforcing rules
- All tests passing
- Pre-commit hooks passing

✅ **Documented**:
- Architecture documented
- Endpoints documented
- Rollback plan written
- Release notes updated

---

## Success Metrics

- [ ] All 10 commits merged to main
- [ ] All tests passing (100% green, ZERO skipped)
- [ ] 0 governance violations
- [ ] Smoke test passing
- [ ] 100% CI passing
- [ ] Documentation complete

---

## Timeline

| Week | Commits | Status |
|------|---------|--------|
| Week 1 (Feb 14-20) | 1-5 | Scheduled |
| Week 2 (Feb 21-27) | 6-10 | Scheduled |
| Week 3 (Feb 28) | Review + Merge | Scheduled |

---

## Key Authority Documents

- `PHASE_16_USER_STORIES.md` - Definitive acceptance criteria per commit
- `PHASE_16_DEV_Q&A_01.md` - Architectural decisions locked
- `PHASE_16_COMMIT_SCAFFOLDINGS.md` - Code templates (ready to paste)
- `PHASE_16_COMMIT_01.md` - DuckDB-specific Commit 1 details
- `PHASE_16_TEST_SUITE.md` - Test patterns and examples
- `PHASE_16_GOVERNANCE_RULES.md` - Forbidden/required concepts
