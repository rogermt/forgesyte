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

**Tasks**:
- [ ] Create `app/models/job.py`:
  - `Job` SQLAlchemy model
  - Fields: `job_id` (UUID PK), `status` (enum), `created_at`, `updated_at`, `input_path`, `output_path`, `error_message`
  - Status enum: `pending`, `running`, `completed`, `failed`
- [ ] Create migration file in `app/migrations/`
- [ ] Add ORM methods: `get_by_id()`, `update_status()`, `save()`
- [ ] Unit tests for model in `tests/models/test_job.py`
- [ ] Verify migration runs cleanly

**Acceptance Criteria**:
- [x] Job table created with correct schema
- [x] Migration script is idempotent
- [x] ORM model has CRUD methods
- [x] No worker logic
- [x] No queue logic

---

### **Commit 2: Object Storage Adapter**
**Goal**: Decouple MP4 file handling from filesystem  
**Time**: 2-3 hours  
**Owner**: Backend Lead  

**Tasks**:
- [ ] Create `app/services/storage/base.py`:
  - Abstract `StorageService` class
  - Methods: `save_file(src, dest_path)`, `load_file(path)`, `delete_file(path)`
- [ ] Create `app/services/storage/local_storage.py`:
  - Filesystem implementation
  - Paths: `video_jobs/{job_id}.mp4`
  - Handles temp directories for tests
- [ ] Unit tests in `tests/services/storage/test_local_storage.py`
  - Test save/load/delete
  - Test temp directory cleanup
- [ ] Document interface requirements

**Acceptance Criteria**:
- [x] StorageService interface created
- [x] Local filesystem implementation working
- [x] Deterministic path structure
- [x] Unit tests passing

---

### **Commit 3: Queue Adapter**
**Goal**: Decouple job dispatch from queue backend  
**Time**: 2-3 hours  
**Owner**: Backend Lead  

**Tasks**:
- [ ] Create `app/services/queue/base.py`:
  - Abstract `QueueService` class
  - Methods: `enqueue(job_id)`, `dequeue()`, `size()`
- [ ] Create `app/services/queue/memory_queue.py`:
  - In-memory FIFO implementation (for dev/test)
  - Thread-safe with locks
- [ ] Unit tests in `tests/services/queue/test_memory_queue.py`
  - Test enqueue/dequeue
  - Test FIFO order
  - Test thread safety
- [ ] Document Redis/RabbitMQ migration path (for future)

**Acceptance Criteria**:
- [x] QueueService interface created
- [x] In-memory implementation working
- [x] FIFO ordering verified
- [x] Unit tests passing

---

### **Commit 4: Job Submission Endpoint**
**Goal**: API consumers can submit videos  
**Time**: 3-4 hours  
**Owner**: Backend Lead + API Engineer  

**Tasks**:
- [ ] Create `app/api_routes/routes/job_submit.py`:
  - `POST /video/submit` endpoint
  - Accept MP4 file upload
  - Validate file format (magic bytes)
  - Save via StorageService
  - Create Job in database
  - Enqueue job_id
  - Return `{job_id}`
- [ ] Create request/response schemas in `app/schemas/`
- [ ] Integration tests in `tests/api/test_job_submit.py`
  - Test valid MP4 submission
  - Test invalid file rejection
  - Test job row creation
  - Test queue enqueue
- [ ] Add fixtures: `tests/fixtures/tiny.mp4` (small valid MP4)

**Acceptance Criteria**:
- [x] POST /video/submit works end-to-end
- [x] File validation working
- [x] Job created in database
- [x] Job enqueued
- [x] Client receives job_id

---

### **Commit 5: Worker Skeleton**
**Goal**: Worker can dequeue and mark jobs as running  
**Time**: 3-4 hours  
**Owner**: Worker Engineer  

**Tasks**:
- [ ] Create `app/workers/worker.py`:
  - `JobWorker` class
  - Constructor: takes QueueService, StorageService, DB connection
  - `run_once()` method:
    - Dequeue job_id
    - Load job from DB
    - Mark status → `running`
    - Return True if processed, False if queue empty
  - `run_forever()` method: loop with sleep/backoff
- [ ] Create `app/workers/worker_runner.py`:
  - Entry point for worker process
  - Initialization logic
  - Signal handling for graceful shutdown
  - Logging setup
- [ ] Unit tests in `tests/workers/test_job_worker.py`:
  - Test dequeue + status transition
  - Test mock queue/DB
  - Test error handling
- [ ] Integration tests for worker startup/shutdown

**Acceptance Criteria**:
- [x] Worker pulls from queue
- [x] Job status transitions pending → running
- [x] Worker handles empty queue
- [x] Signal handlers working
- [x] Unit tests passing

---

### **Commit 6: Worker Executes Phase-15 Pipeline**
**Goal**: Worker processes MP4 using VideoFilePipelineService  
**Time**: 4-5 hours  
**Owner**: Worker Engineer  

**Tasks**:
- [ ] Update `app/workers/worker.py` `run_once()`:
  - Load MP4 via StorageService
  - Instantiate VideoFilePipelineService
  - Call `run_on_file(file_path, pipeline_id="yolo_ocr")`
  - Capture results
  - Save results via StorageService to `video_jobs/{job_id}_results.json`
  - Update job: `output_path`, status → `completed`
  - On exception: status → `failed`, `error_message`
- [ ] Create `app/services/results_serializer.py`:
  - Convert Phase-15 results to JSON
  - Ensure deterministic output
- [ ] Integration tests in `tests/workers/test_worker_pipeline.py`:
  - Test full job → completion
  - Test failure handling
  - Verify results storage
- [ ] Add fixture: `tests/fixtures/make_tiny_mp4.py` (generate test MP4)

**Acceptance Criteria**:
- [x] Worker runs VideoFilePipelineService
- [x] Results stored deterministically
- [x] Job status transitions correctly
- [x] Errors captured and stored
- [x] Integration tests passing

---

### **Commit 7: Job Status Endpoint**
**Goal**: Clients can poll job status  
**Time**: 2-3 hours  
**Owner**: API Engineer  

**Tasks**:
- [ ] Create `app/api_routes/routes/job_status.py`:
  - `GET /video/status/{job_id}` endpoint
  - Load Job from database
  - Return `{job_id, status, progress, created_at, updated_at}`
  - Progress: 0 (pending), 0.5 (running), 1.0 (completed/failed)
  - Return 404 if job not found
- [ ] Add status schema to `app/schemas/`
- [ ] Integration tests in `tests/api/test_job_status.py`
  - Test status transitions
  - Test progress values
  - Test 404 behavior
  - Test all four statuses

**Acceptance Criteria**:
- [x] GET /video/status/{job_id} works
- [x] Progress is coarse (0, 0.5, 1.0)
- [x] Returns correct status values
- [x] 404 handling working

---

### **Commit 8: Job Results Endpoint**
**Goal**: Clients can retrieve completed results  
**Time**: 2-3 hours  
**Owner**: API Engineer  

**Tasks**:
- [ ] Create `app/api_routes/routes/job_results.py`:
  - `GET /video/results/{job_id}` endpoint
  - Load Job from database
  - Check status == "completed"
  - Load results from object storage
  - Return `{job_id, results, created_at, updated_at}`
  - Return 404 if job not found OR not completed
- [ ] Add results schema to `app/schemas/`
- [ ] Integration tests in `tests/api/test_job_results.py`
  - Test retrieval of completed job
  - Test 404 for pending job
  - Test 404 for missing job
  - Test error response

**Acceptance Criteria**:
- [x] GET /video/results/{job_id} works for completed jobs
- [x] Returns 404 for pending/running jobs
- [x] Returns 404 for missing jobs
- [x] Results match Phase-15 format

---

### **Commit 9: Governance + CI Enforcement**
**Goal**: Prevent Phase-17 concepts from entering codebase  
**Time**: 3-4 hours  
**Owner**: DevOps + Release Manager  

**Tasks**:
- [ ] Update `server/tools/forbidden_vocabulary_phase16.yaml`:
  - Add forbidden terms: `websocket`, `streaming`, `gpu_schedule`, `distributed`, `gpu_worker`
  - Add allowed terms: `job_queue`, `async`, `worker`, `polling`
- [ ] Create/update `server/tools/validate_phase16_path.py`:
  - Scan functional code for forbidden vocabulary
  - Exit code 0 if clean, 1 if violations found
  - Report violations with file:line
- [ ] Create `.github/workflows/phase16_validation.yml`:
  - Runs on every PR to main
  - Step 1: Run forbidden vocabulary scanner
  - Step 2: Validate plugin registry
  - Step 3: Run full pytest suite
  - Blocks merge if any step fails
- [ ] Update smoke test in `scripts/smoke_test.py`:
  - Test job submission
  - Test job status polling
  - Test job results retrieval
- [ ] Document governance rules in `.ampcode/04_PHASE_NOTES/Phase_16/`

**Acceptance Criteria**:
- [x] Forbidden vocabulary scanner working
- [x] CI workflow enforces governance
- [x] Smoke test updated
- [x] No Phase-17 concepts in code

---

### **Commit 10: Documentation + Rollback Plan**
**Goal**: New contributors can understand and onboard to Phase-16  
**Time**: 3-4 hours  
**Owner**: Technical Writer + Release Manager  

**Tasks**:
- [ ] Create `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_OVERVIEW.md`
  - Executive summary
  - Architecture diagram (text)
  - Data flow
  - Key decisions
- [ ] Create `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_ARCHITECTURE.md`
  - Component diagrams
  - Integration points
  - State transitions
- [ ] Create `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_ROLLBACK_PLAN.md`:
  - List files to delete (job model, migrations, etc.)
  - List modifications to revert (endpoint removal)
  - Step-by-step rollback procedure
  - Verification steps
- [ ] Create `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_ENDPOINTS.md`
  - API specification
  - Request/response examples
  - Error codes
- [ ] Create `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_CONTRIBUTOR_EXAM.md`
  - 20-question exam for contributors
  - Tests understanding of architecture, governance, testing
- [ ] Create `RELEASE_NOTES.md` entry for Phase-16

**Acceptance Criteria**:
- [x] All documentation created
- [x] Rollback plan is executable
- [x] New contributors can pass exam
- [x] Release notes updated

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
