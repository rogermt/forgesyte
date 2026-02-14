# Phase 16 Progress Tracking (CORRECTED)
**Phase**: 16 - Asynchronous Job Queue + Persistent Job State + Worker Execution  
**Start Date**: 2026-02-14  
**Target Completion**: 2026-02-28  
**Current Status**: ✅ PLAN APPROVED - READY FOR COMMIT 1  
**AUTHORITY**: User Stories + Q&A + Scaffolding (read completely)

---

## Executive Summary

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Commits Completed | 10 | 0 | ⏳ 0% |
| Code Coverage | 80%+ | N/A | ⏳ Pending |
| Tests Passing | 100% (ALL GREEN) | N/A | ⏳ Pending |
| Tests Skipped | 0 | N/A | ⏳ Pending |
| Documentation | 100% | 0% | ⏳ 0% |
| Governance Violations | 0 | 0 | ✅ Clean |

---

## Architectural Decisions (LOCKED - FROM AUTHORITY)

**1. Database Engine**
- ✅ DuckDB (project already uses it, existing instance at `data/foregsyte.duckdb`)
- ❌ NO SQLite
- ❌ NO PostgreSQL
- ❌ NO separate database engine

**2. ORM & Database Setup**
- ✅ SQLAlchemy with shared `Base = declarative_base()` in `app/core/database.py`
- ✅ DuckDB types: `duckdb_types.UUID` (NOT `postgresql.UUID`)
- ❌ NO separate `declarative_base()` per model file
- ❌ NO `AsyncSession`
- Session type: Synchronous `SessionLocal`

**3. Migrations**
- ✅ Alembic from scratch (none exists in codebase)
- Command: `alembic init server/app/migrations`
- Migration file: `app/migrations/versions/<timestamp>_create_job_table.py`
- All migrations use DuckDB types

**4. API Routes Location**
- ✅ `server/app/api_routes/routes/` (matches Phase-15 pattern)
- ❌ NOT `server/app/api/routes/`
- Files:
  - `job_submit.py` (POST /video/submit)
  - `job_status.py` (GET /video/status/{job_id})
  - `job_results.py` (GET /video/results/{job_id})

**5. Test Database**
- ✅ In-memory DuckDB: `duckdb:///:memory:` per test
- ✅ Fixtures create/destroy tables per test
- ❌ NO persistent test DB
- ❌ NO SQLite in tests

**6. Import Pattern**
- ✅ `from app.models.job import Job, JobStatus`
- ✅ Job lives in `server/app/models/job.py`

**7. Job Table Schema**
8 fields (LOCKED):
- job_id: UUID (PK, auto)
- status: Enum (pending, running, completed, failed)
- created_at: DateTime (auto)
- updated_at: DateTime (auto)
- pipeline_id: String (required)
- input_path: String (required)
- output_path: String (nullable)
- error_message: String (nullable)

**8. Queue Implementation**
- ✅ Python `queue.Queue` (in-memory)
- ✅ Payload: `{job_id}` only
- ❌ NO Redis/RabbitMQ in Phase-16
- ❌ NO metadata in queue payload

**9. Storage Paths**
- MP4: `./data/video_jobs/{job_id}.mp4`
- Results: `./data/video_jobs/{job_id}_results.json`

**10. Forbidden Concepts (CI will enforce)**
- ❌ WebSockets
- ❌ Streaming
- ❌ SSE
- ❌ GPU scheduling
- ❌ Distributed workers
- ❌ Frame-level progress
- ❌ `AsyncSession`
- ❌ SQLite
- ❌ Phase-named files in functional code

---

## Commit Progress

### Commit 1: Job Model + DB Migration
**Status**: ⏳ NOT STARTED  
**Owner**: Backend Lead  
**Time Estimate**: 2-3 hours  
**TDD**: Tests first, then implement  

**Files to Create**:
- [ ] `server/app/core/database.py` (DuckDB engine + shared Base)
- [ ] `server/app/models/job.py` (SQLAlchemy Job model)
- [ ] `server/app/migrations/env.py` (Alembic environment, DuckDB-specific)
- [ ] `server/app/migrations/versions/<timestamp>_create_job_table.py`
- [ ] `server/tests/app/conftest.py` (DuckDB fixtures)
- [ ] `server/tests/app/models/test_job.py` (unit tests)

**Tests to Write First**:
- `test_job_defaults()` - Create job, assert pending status
- `test_job_status_enum()` - Test 4 status values
- `test_job_persistence()` - Assert save/load from DuckDB
- `test_job_timestamps()` - Assert auto timestamps

**Tests Must Pass**:
- ✅ All test_job.py tests GREEN
- ✅ Migration runs: `alembic upgrade head`
- ✅ `data/foregsyte.duckdb` created
- ✅ No governance violations
- ✅ Pre-commit hooks pass

---

### Commit 2: Object Storage Adapter
**Status**: ⏳ NOT STARTED  
**Owner**: Backend Lead  
**Time Estimate**: 2-3 hours  
**Dependencies**: Commit 1  

**Files to Create**:
- [ ] `server/app/services/storage/base.py` (StorageService interface)
- [ ] `server/app/services/storage/local_storage.py` (LocalStorageService)
- [ ] `server/tests/app/services/storage/test_local_storage.py` (unit tests)

**Tests Must Pass**:
- ✅ test_save_file() - File saved correctly
- ✅ test_load_file() - File loaded correctly
- ✅ test_delete_file() - File deleted
- ✅ test_path_structure() - Paths deterministic

---

### Commit 3: Queue Adapter
**Status**: ⏳ NOT STARTED  
**Owner**: Backend Lead  
**Time Estimate**: 2-3 hours  
**Dependencies**: Commit 1  

**Files to Create**:
- [ ] `server/app/services/queue/base.py` (QueueService interface)
- [ ] `server/app/services/queue/memory_queue.py` (InMemoryQueueService)
- [ ] `server/tests/app/services/queue/test_memory_queue.py` (unit tests)

**Tests Must Pass**:
- ✅ test_enqueue() - Job_id enqueued
- ✅ test_dequeue() - Job_id dequeued
- ✅ test_fifo_order() - FIFO order correct
- ✅ test_size() - Queue size correct

---

### Commit 4: Job Submission Endpoint
**Status**: ⏳ NOT STARTED  
**Owner**: Backend Lead + API Engineer  
**Time Estimate**: 3-4 hours  
**Dependencies**: Commits 1, 2, 3  

**Files to Create**:
- [ ] `server/app/api_routes/routes/job_submit.py` (POST /video/submit)
- [ ] `server/tests/fixtures/tiny.mp4` (test fixture)
- [ ] `server/tests/app/api/test_job_submit.py` (integration tests)

**Tests Must Pass**:
- ✅ test_submit_valid_mp4() - Returns job_id
- ✅ test_submit_creates_job() - Job in DB
- ✅ test_submit_saves_file() - File in storage
- ✅ test_submit_enqueues() - Job in queue
- ✅ test_submit_invalid_file() - Rejects non-MP4

---

### Commit 5: Worker Skeleton
**Status**: ⏳ NOT STARTED  
**Owner**: Worker Engineer  
**Time Estimate**: 3-4 hours  
**Dependencies**: Commits 1, 2, 3  

**Files to Create**:
- [ ] `server/app/workers/worker.py` (JobWorker class)
- [ ] `server/app/workers/worker_runner.py` (entry point)
- [ ] `server/tests/app/workers/test_job_worker.py` (unit tests)

**Tests Must Pass**:
- ✅ test_worker_dequeue() - Dequeues job_id
- ✅ test_worker_transition() - Marks running
- ✅ test_worker_empty_queue() - Handles empty
- ✅ test_worker_signals() - SIGINT/SIGTERM handled

---

### Commit 6: Worker Executes Phase-15 Pipeline
**Status**: ⏳ NOT STARTED  
**Owner**: Worker Engineer  
**Time Estimate**: 4-5 hours  
**Dependencies**: Commits 1-5, Phase-15 VideoFilePipelineService  

**Files to Update**:
- [ ] `server/app/workers/worker.py` - Add pipeline execution

**Files to Create**:
- [ ] `server/tests/app/workers/test_worker_pipeline.py` (integration tests)

**Tests Must Pass**:
- ✅ test_worker_loads_mp4() - Loads file
- ✅ test_worker_runs_pipeline() - Calls VideoFilePipelineService
- ✅ test_worker_saves_results() - Results saved as JSON
- ✅ test_worker_completes() - Status → completed
- ✅ test_worker_errors() - Status → failed on exception

---

### Commit 7: Job Status Endpoint
**Status**: ⏳ NOT STARTED  
**Owner**: API Engineer  
**Time Estimate**: 2-3 hours  
**Dependencies**: Commits 1-6  

**Files to Create**:
- [ ] `server/app/api_routes/routes/job_status.py` (GET /video/status/{job_id})
- [ ] `server/tests/app/api/test_job_status.py` (integration tests)

**Tests Must Pass**:
- ✅ test_status_pending() - Returns progress=0
- ✅ test_status_running() - Returns progress=0.5
- ✅ test_status_done() - Returns progress=1.0
- ✅ test_status_not_found() - 404

---

### Commit 8: Job Results Endpoint
**Status**: ⏳ NOT STARTED  
**Owner**: API Engineer  
**Time Estimate**: 2-3 hours  
**Dependencies**: Commits 1-7  

**Files to Create**:
- [ ] `server/app/api_routes/routes/job_results.py` (GET /video/results/{job_id})
- [ ] `server/tests/app/api/test_job_results.py` (integration tests)

**Tests Must Pass**:
- ✅ test_results_done() - Returns results
- ✅ test_results_pending() - 404
- ✅ test_results_not_found() - 404

---

### Commit 9: Governance + CI Enforcement
**Status**: ⏳ NOT STARTED  
**Owner**: DevOps + Release Manager  
**Time Estimate**: 3-4 hours  
**Dependencies**: Commits 1-8  

**Files to Create**:
- [ ] `server/tools/forbidden_vocabulary_phase16.yaml`
- [ ] `server/tools/validate_phase16_path.py`
- [ ] `.github/workflows/phase16_validation.yml`
- [ ] `scripts/smoke_test.py` (updated)
- [ ] `server/tests/execution/test_phase16_governance.py`

**Tests Must Pass**:
- ✅ test_no_forbidden_vocabulary() - No Phase-17 words
- ✅ test_governance_scanner_runs() - Scanner exits 0
- ✅ test_smoke_test_passes() - Full lifecycle works

---

### Commit 10: Documentation + Rollback Plan
**Status**: ⏳ NOT STARTED  
**Owner**: Technical Writer + Release Manager  
**Time Estimate**: 3-4 hours  
**Dependencies**: Commits 1-9  

**Files to Create**:
- [ ] `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_OVERVIEW.md`
- [ ] `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_ARCHITECTURE.md`
- [ ] `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_ENDPOINTS.md`
- [ ] `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_ROLLBACK_PLAN.md`
- [ ] `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_CONTRIBUTOR_EXAM.md`
- [ ] `RELEASE_NOTES.md` (updated)
- [ ] `server/tests/documentation/test_phase16_docs.py`

**Tests Must Pass**:
- ✅ test_overview_exists()
- ✅ test_rollback_plan_exists()
- ✅ test_all_links_valid()

---

## Test Strategy (FROM AUTHORITY)

**Unit Tests**:
- Use mocks for external dependencies
- Use in-memory DuckDB (`duckdb:///:memory:`)
- Run fast, no I/O

**Integration Tests**:
- Use in-memory DuckDB fixtures
- Test full component flow
- Create/destroy tables per test

**API Tests**:
- Use TestClient with DuckDB override
- Mock external services if needed
- Test HTTP contract

**Worker Tests**:
- Mock queue + storage in unit tests
- Use in-memory DB in integration tests
- Test full pipeline execution

**All Tests Must**:
- ✅ Pass (GREEN)
- ✅ Never be skipped
- ✅ Cover 80%+ of code
- ✅ Verify contracts, not implementation

---

## Known Issues

| Issue | Status | Notes |
|-------|--------|-------|
| None yet | — | —  |

---

## Blockers

| Blocker | Status | Mitigation |
|---------|--------|-----------|
| Phase-15 VideoFilePipelineService | ✅ Ready | Already exists |
| DuckDB | ✅ Ready | Already in use |
| SQLAlchemy | ✅ Ready | In dependencies |
| Alembic | ✅ Ready | Can init from scratch |

---

## Lessons Learned

(To be updated as work progresses)

---

## Retrospective Notes

(To be updated at phase completion)

---

## Last Updated

**Date**: 2026-02-14  
**By**: AI Assistant (after reading ALL authority documents)  
**Status**: ✅ APPROVED - All 6 questions answered, all decisions locked

---

## References

**Authority Documents** (read completely):
- `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_USER_STORIES.md` - Definitive acceptance criteria
- `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_DEV_Q&A_01.md` - Architectural decisions
- `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_COMMIT_SCAFFOLDINGS.md` - Code templates
- `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_COMMIT_01.md` - DuckDB-specific details
- `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_TEST_SUITE.md` - Test patterns
- `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_GOVERNANCE_RULES.md` - Forbidden/required
- `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_SCOPE.md` - In/out of scope

**Project Files**:
- `server/pyproject.toml` - Dependencies (SQLAlchemy, Alembic, DuckDB engine)
- `AGENTS.md` - Project conventions (TDD, pre-commit, all tests pass)
- `server/tests/conftest.py` - Existing fixtures (extend with DuckDB)
