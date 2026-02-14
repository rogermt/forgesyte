# Phase 16 Implementation Plan
**Status**: NOT STARTED  
**Date Created**: 2026-02-14  
**Target Completion**: 2026-02-28  
**Duration**: 2 weeks  

---

## Overview

Phase 16 introduces **asynchronous job processing** with:
- A persistent job queue
- A job state table (pending → running → completed/failed)
- A long-running worker process
- Polling-based status + results APIs

This transforms the system from synchronous (submit → wait → results) to asynchronous (submit → get job_id → poll for status).

---

## 10-Commit Implementation Plan

### **Commit 1: Job Model + DB Migration**
**Goal**: Establish job persistence layer  
**Time**: 2-3 hours  
**Owner**: Backend Lead  
**TDD**: Write tests first, then implement

**Phase 1: Write Failing Tests**
- [ ] Create `tests/models/test_job.py` with test suite:
  - `test_job_creation()` - Assert Job can be instantiated
  - `test_job_status_enum()` - Assert status has 4 valid values
  - `test_job_get_by_id()` - Assert can retrieve job by ID
  - `test_job_update_status()` - Assert status can be updated
  - `test_job_save()` - Assert job persists to database
  - All tests should **FAIL** (model doesn't exist yet)
- [ ] Run tests: `uv run pytest tests/models/test_job.py -v` (expect failures)
- [ ] Verify failures are test setup issues, not implementation

**Phase 2: Implement Code**
- [ ] Create `app/models/job.py`:
  - `Job` SQLAlchemy model with fields: `job_id` (UUID PK), `status` (enum), `created_at`, `updated_at`, `input_path`, `output_path`, `error_message`
  - Status enum: `pending`, `running`, `completed`, `failed`
  - Methods: `get_by_id()`, `update_status()`, `save()`
- [ ] Create migration file in `app/migrations/`
- [ ] Run migration: `alembic upgrade head`

**Phase 3: Verify Tests Pass**
- [ ] Run tests: `uv run pytest tests/models/test_job.py -v` (expect all ✅)
- [ ] Run with coverage: `uv run pytest tests/models/test_job.py --cov`
- [ ] Target: 100% coverage on model

**Phase 4: Pre-Commit Verification**
- [ ] `uv run pre-commit run --all-files` ✅
- [ ] `cd server && uv run pytest tests/execution -v` ✅
- [ ] `python scripts/scan_execution_violations.py` ✅
- [ ] All 4 checks passing before commit

**Acceptance Criteria**:
- [x] `tests/models/test_job.py` created and all passing
- [x] Job table created with correct schema
- [x] Migration script is idempotent
- [x] ORM model has CRUD methods
- [x] No worker logic
- [x] No queue logic
- [x] All 4 pre-commit checks passing

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
- [x] `tests/services/storage/test_local_storage.py` created and all passing
- [x] StorageService interface created
- [x] Local filesystem implementation working
- [x] Deterministic path structure: `video_jobs/{job_id}.mp4`
- [x] Unit tests passing with 100% coverage
- [x] All 4 pre-commit checks passing

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
- [x] `tests/services/queue/test_memory_queue.py` created and all passing
- [x] QueueService interface created
- [x] In-memory implementation working
- [x] FIFO ordering verified
- [x] Thread-safety tested
- [x] Unit tests passing with 100% coverage
- [x] All 4 pre-commit checks passing

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
- [ ] Create `app/schemas/job_schemas.py`:
  - `JobSubmitRequest` schema
  - `JobSubmitResponse` schema with job_id
- [ ] Create `app/api_routes/routes/job_submit.py`:
  - `POST /video/submit` endpoint
  - Accept MP4 file upload (multipart/form-data)
  - Validate file format (magic bytes: `ftyp`)
  - Save via StorageService
  - Create Job in database (status=pending)
  - Enqueue job_id to queue
  - Return `{job_id}`

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
- [x] `tests/api/test_job_submit.py` created and all passing
- [x] POST /video/submit works end-to-end
- [x] File validation working (rejects non-MP4)
- [x] Job created in database with status=pending
- [x] Job enqueued
- [x] Client receives `{job_id}`
- [x] Integration tests passing with 100% coverage
- [x] All 4 pre-commit checks passing

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
- [x] `tests/workers/test_job_worker.py` created and all passing
- [x] Worker pulls from queue
- [x] Job status transitions pending → running
- [x] Worker handles empty queue (sleep/backoff)
- [x] Signal handlers working
- [x] Graceful shutdown implemented
- [x] Unit tests passing with 100% coverage
- [x] All 4 pre-commit checks passing

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
- [x] `tests/workers/test_worker_pipeline.py` created and all passing
- [x] Worker runs VideoFilePipelineService on MP4
- [x] Results stored deterministically as JSON
- [x] Job status transitions pending → running → completed
- [x] Exceptions handled: status → failed + error_message
- [x] Results match Phase-15 format
- [x] Integration tests passing with 100% coverage
- [x] All 4 pre-commit checks passing

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
- [ ] Create `app/schemas/job_status_schema.py`:
  - `JobStatusResponse` schema with job_id, status, progress, created_at, updated_at
- [ ] Create `app/api_routes/routes/job_status.py`:
  - `GET /video/status/{job_id}` endpoint
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
- [x] `tests/api/test_job_status.py` created and all passing
- [x] GET /video/status/{job_id} works
- [x] Progress is coarse (0, 0.5, 1.0)
- [x] Returns correct status values
- [x] Returns 404 for missing jobs
- [x] Response includes all required fields
- [x] Integration tests passing with 100% coverage
- [x] All 4 pre-commit checks passing

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
- [ ] Create `app/schemas/job_results_schema.py`:
  - `JobResultsResponse` schema with job_id, results, created_at, updated_at
- [ ] Create `app/api_routes/routes/job_results.py`:
  - `GET /video/results/{job_id}` endpoint
  - Load Job from DB (raise 404 if not found)
  - Check status == "completed" (raise 404 if not)
  - Load results from object storage
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
- [x] `tests/api/test_job_results.py` created and all passing
- [x] GET /video/results/{job_id} works for completed jobs
- [x] Returns 404 for pending/running/failed jobs
- [x] Returns 404 for missing jobs
- [x] Results match Phase-15 format
- [x] Response includes all required fields
- [x] Integration tests passing with 100% coverage
- [x] All 4 pre-commit checks passing

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
- [x] `tests/execution/test_phase16_governance.py` created and all passing
- [x] Forbidden vocabulary scanner working
- [x] CI workflow enforces governance
- [x] Smoke test updated and passing
- [x] No Phase-17 concepts in code
- [x] Governance tests passing with 100% coverage
- [x] All 4 pre-commit checks passing

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
- [x] `tests/documentation/test_phase16_docs.py` created and all passing
- [x] All Phase-16 documentation created and linked
- [x] Rollback plan is executable and tested
- [x] Rollback plan lists exact files/modifications
- [x] New contributors can pass exam
- [x] Release notes updated
- [x] Documentation tests passing with 100% coverage
- [x] All 4 pre-commit checks passing

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
