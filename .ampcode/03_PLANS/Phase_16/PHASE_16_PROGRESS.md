# Phase 16 Progress Tracking
**Phase**: 16 - Asynchronous Job Queue + Persistent Job State + Worker Execution  
**Start Date**: 2026-02-14  
**Target Completion**: 2026-02-28  
**Current Status**: ✅ PLAN APPROVED - READY FOR COMMIT 1  

---

## Executive Summary

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Commits Completed | 10 | 0 | ⏳ 0% |
| Code Coverage | 80%+ | N/A | ⏳ Pending |
| Tests Passing | 100% | N/A | ⏳ Pending |
| Documentation | 100% | 0% | ⏳ 0% |
| Governance Violations | 0 | 0 | ✅ Clean |

---

## Commit Progress

### Commit 1: Job Model + DB Migration
**Status**: ⏳ NOT STARTED  
**Owner**: Backend Lead  
**Time Estimate**: 2-3 hours  
**Dependencies**: None  

**Tasks**:
- [ ] `app/models/job.py` created with SQLAlchemy model
- [ ] Migration file created in `app/migrations/`
- [ ] ORM methods implemented (get_by_id, update_status, save)
- [ ] Unit tests in `tests/models/test_job.py` (100% passing)
- [ ] Migration tested locally

**Acceptance Criteria**:
- [ ] Job table created with correct schema
- [ ] Migration is idempotent
- [ ] No worker/queue logic

**Notes**:
- Job table schema: job_id (UUID PK), status (enum), created_at, updated_at, input_path, output_path, error_message
- Status enum values: pending, running, completed, failed

---

### Commit 2: Object Storage Adapter
**Status**: ⏳ NOT STARTED  
**Owner**: Backend Lead  
**Time Estimate**: 2-3 hours  
**Dependencies**: Commit 1  

**Tasks**:
- [ ] `app/services/storage/base.py` created with StorageService interface
- [ ] `app/services/storage/local_storage.py` created with filesystem implementation
- [ ] Unit tests in `tests/services/storage/test_local_storage.py` (100% passing)
- [ ] Path structure documented: `video_jobs/{job_id}.mp4`

**Acceptance Criteria**:
- [ ] StorageService interface complete
- [ ] save_file(), load_file(), delete_file() working
- [ ] Temp directory cleanup verified
- [ ] Unit tests passing

**Notes**:
- Interface is backend-agnostic (can swap to S3 later)
- Paths are deterministic
- Local implementation uses pathlib

---

### Commit 3: Queue Adapter
**Status**: ⏳ NOT STARTED  
**Owner**: Backend Lead  
**Time Estimate**: 2-3 hours  
**Dependencies**: Commit 1  

**Tasks**:
- [ ] `app/services/queue/base.py` created with QueueService interface
- [ ] `app/services/queue/memory_queue.py` created with in-memory FIFO implementation
- [ ] Unit tests in `tests/services/queue/test_memory_queue.py` (100% passing)
- [ ] Thread-safety verified with concurrent tests

**Acceptance Criteria**:
- [ ] QueueService interface complete
- [ ] enqueue(), dequeue(), size() working
- [ ] FIFO order verified
- [ ] Thread-safe implementation
- [ ] Unit tests passing

**Notes**:
- In-memory for dev/test (Redis migration path documented for future)
- FIFO order critical for determinism
- Thread-safe with locks

---

### Commit 4: Job Submission Endpoint
**Status**: ⏳ NOT STARTED  
**Owner**: Backend Lead + API Engineer  
**Time Estimate**: 3-4 hours  
**Dependencies**: Commits 1, 2, 3  

**Tasks**:
- [ ] `app/api_routes/routes/job_submit.py` created with POST /video/submit
- [ ] File validation (magic bytes) implemented
- [ ] StorageService integration working
- [ ] Job creation in database working
- [ ] Queue enqueue working
- [ ] Request/response schemas created
- [ ] Integration tests in `tests/api/test_job_submit.py` (100% passing)
- [ ] Test fixtures created: `tests/fixtures/tiny.mp4`

**Acceptance Criteria**:
- [ ] POST /video/submit accepts MP4 files
- [ ] File validation rejects invalid formats
- [ ] Job created in database with correct fields
- [ ] Job_id enqueued
- [ ] Response returns `{job_id}`
- [ ] Integration tests passing

**Notes**:
- File validation uses magic bytes, not extension
- tiny.mp4 fixture must be valid MP4
- Error responses documented

---

### Commit 5: Worker Skeleton
**Status**: ⏳ NOT STARTED  
**Owner**: Worker Engineer  
**Time Estimate**: 3-4 hours  
**Dependencies**: Commits 1, 2, 3  

**Tasks**:
- [ ] `app/workers/worker.py` created with JobWorker class
- [ ] `run_once()` method dequeues job and marks as running
- [ ] `run_forever()` method implements loop with backoff
- [ ] `app/workers/worker_runner.py` created with entry point
- [ ] Signal handlers (SIGINT, SIGTERM) implemented
- [ ] Graceful shutdown working
- [ ] Unit tests in `tests/workers/test_job_worker.py` (100% passing)
- [ ] Integration tests for startup/shutdown

**Acceptance Criteria**:
- [ ] Worker pulls job_id from queue
- [ ] Job status transitions pending → running
- [ ] Worker handles empty queue (sleep/backoff)
- [ ] Signal handlers working
- [ ] Graceful shutdown implemented
- [ ] Unit/integration tests passing

**Notes**:
- Uses mock queue/DB in tests
- Sleep/backoff prevents busy-waiting
- Signal handlers ensure clean shutdown

---

### Commit 6: Worker Executes Phase-15 Pipeline
**Status**: ⏳ NOT STARTED  
**Owner**: Worker Engineer  
**Time Estimate**: 4-5 hours  
**Dependencies**: Commits 1-5, Phase-15 VideoFilePipelineService  

**Tasks**:
- [ ] Worker.run_once() updated to load MP4 from storage
- [ ] VideoFilePipelineService instantiated and called
- [ ] Results captured and serialized to JSON
- [ ] Results stored via StorageService to `video_jobs/{job_id}_results.json`
- [ ] Job updated: output_path, status → completed
- [ ] Exception handling: status → failed, error_message stored
- [ ] `app/services/results_serializer.py` created for deterministic JSON
- [ ] Integration tests in `tests/workers/test_worker_pipeline.py` (100% passing)
- [ ] Fixture script: `tests/fixtures/make_tiny_mp4.py`

**Acceptance Criteria**:
- [ ] Worker runs VideoFilePipelineService on MP4
- [ ] Results stored deterministically as JSON
- [ ] Job status transitions pending → running → completed
- [ ] Exceptions handled: status → failed + error_message
- [ ] Integration tests passing
- [ ] Results match Phase-15 format

**Notes**:
- Pipeline_id hardcoded as "yolo_ocr" (configurable in later phases)
- Results serialization must be deterministic
- Error handling covers transient + permanent errors

---

### Commit 7: Job Status Endpoint
**Status**: ⏳ NOT STARTED  
**Owner**: API Engineer  
**Time Estimate**: 2-3 hours  
**Dependencies**: Commits 1-6  

**Tasks**:
- [ ] `app/api_routes/routes/job_status.py` created with GET /video/status/{job_id}
- [ ] Status response schema created
- [ ] Progress calculation: 0 (pending), 0.5 (running), 1.0 (completed/failed)
- [ ] 404 handling for missing jobs
- [ ] Integration tests in `tests/api/test_job_status.py` (100% passing)
- [ ] All four status values tested

**Acceptance Criteria**:
- [ ] GET /video/status/{job_id} returns job status
- [ ] Progress is coarse: 0, 0.5, 1.0 (no frame-level granularity)
- [ ] Returns 404 for missing jobs
- [ ] Response includes: job_id, status, progress, created_at, updated_at
- [ ] Integration tests passing

**Notes**:
- Progress is coarse to prevent Phase-17 scope creep
- Status values: pending, running, completed, failed
- Timestamps are ISO format

---

### Commit 8: Job Results Endpoint
**Status**: ⏳ NOT STARTED  
**Owner**: API Engineer  
**Time Estimate**: 2-3 hours  
**Dependencies**: Commits 1-7  

**Tasks**:
- [ ] `app/api_routes/routes/job_results.py` created with GET /video/results/{job_id}
- [ ] Results response schema created
- [ ] Status check: only return results if status == "completed"
- [ ] 404 handling: missing job or not completed
- [ ] Integration tests in `tests/api/test_job_results.py` (100% passing)

**Acceptance Criteria**:
- [ ] GET /video/results/{job_id} returns results for completed jobs
- [ ] Returns 404 if job not found
- [ ] Returns 404 if job not completed
- [ ] Results match Phase-15 output format
- [ ] Response includes: job_id, results, created_at, updated_at
- [ ] Integration tests passing

**Notes**:
- Results are loaded from object storage, not database
- 404 response covers both missing jobs + pending jobs
- Results format unchanged from Phase-15

---

### Commit 9: Governance + CI Enforcement
**Status**: ⏳ NOT STARTED  
**Owner**: DevOps + Release Manager  
**Time Estimate**: 3-4 hours  
**Dependencies**: Commits 1-8  

**Tasks**:
- [ ] Update `server/tools/forbidden_vocabulary_phase16.yaml`:
  - Add forbidden terms: websocket, streaming, gpu_schedule, distributed, gpu_worker
  - Add allowed terms: job_queue, async, worker, polling
- [ ] Create/update `server/tools/validate_phase16_path.py`:
  - Scan functional code for forbidden vocabulary
  - Report violations with file:line
  - Exit code 0 (clean) or 1 (violations)
- [ ] Create `.github/workflows/phase16_validation.yml`:
  - Runs on PR to main
  - Steps: forbidden vocabulary scanner → plugin validator → pytest
  - Blocks merge on failure
- [ ] Update smoke test `scripts/smoke_test.py`:
  - Test POST /video/submit
  - Test GET /video/status/{job_id}
  - Test GET /video/results/{job_id}
- [ ] Document governance rules

**Acceptance Criteria**:
- [ ] Forbidden vocabulary scanner working
- [ ] CI workflow enforcing governance
- [ ] Smoke test updated and passing
- [ ] 0 governance violations in code

**Notes**:
- Governance rules prevent Phase-17 concepts leaking in
- CI workflow blocks PRs that violate rules
- Smoke test validates end-to-end functionality

---

### Commit 10: Documentation + Rollback Plan
**Status**: ⏳ NOT STARTED  
**Owner**: Technical Writer + Release Manager  
**Time Estimate**: 3-4 hours  
**Dependencies**: Commits 1-9  

**Tasks**:
- [ ] `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_OVERVIEW.md` created
- [ ] `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_ARCHITECTURE.md` created
- [ ] `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_ROLLBACK_PLAN.md` created
  - Lists files to delete
  - Lists modifications to revert
  - Step-by-step rollback procedure
- [ ] `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_ENDPOINTS.md` created
- [ ] `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_CONTRIBUTOR_EXAM.md` created
  - 20-question exam
  - Covers architecture, governance, testing
- [ ] `RELEASE_NOTES.md` entry created

**Acceptance Criteria**:
- [ ] All Phase-16 documentation created
- [ ] Rollback plan is executable and tested
- [ ] New contributors can pass exam
- [ ] Release notes updated
- [ ] Documentation links verified

**Notes**:
- Rollback plan lists exact files/modifications for safe revert
- Contributor exam ensures knowledge transfer
- Release notes document breaking changes (if any)

---

## Testing Summary

### Unit Tests
| Module | Status | Coverage | Notes |
|--------|--------|----------|-------|
| Job model | ⏳ Pending | — | `tests/models/test_job.py` |
| StorageService | ⏳ Pending | — | `tests/services/storage/` |
| QueueService | ⏳ Pending | — | `tests/services/queue/` |
| Worker logic | ⏳ Pending | — | `tests/workers/test_job_worker.py` |
| API endpoints | ⏳ Pending | — | `tests/api/test_job_*.py` |

### Integration Tests
| Test | Status | Notes |
|------|--------|-------|
| Submit job → job created | ⏳ Pending | `test_job_submit.py` |
| Worker → job completed | ⏳ Pending | `test_worker_pipeline.py` |
| Status endpoint | ⏳ Pending | `test_job_status.py` |
| Results endpoint | ⏳ Pending | `test_job_results.py` |
| Full lifecycle | ⏳ Pending | End-to-end test |

### Governance Tests
| Test | Status | Notes |
|------|--------|-------|
| Forbidden vocabulary | ⏳ Pending | `validate_phase16_path.py` |
| CI workflow | ⏳ Pending | `.github/workflows/phase16_validation.yml` |
| Smoke test | ⏳ Pending | `scripts/smoke_test.py` |

---

## Known Issues

| Issue | Status | Owner | Notes |
|-------|--------|-------|-------|
| None yet | — | — | None |

---

## Blockers

| Blocker | Status | Mitigation |
|---------|--------|-----------|
| Phase-15 VideoFilePipelineService | ✅ Ready | Already implemented |
| Database infrastructure | ✅ Ready | SQLite available |
| Object storage | ✅ Ready | Local filesystem available |

---

## Lessons Learned

(To be updated as work progresses)

---

## Retrospective Notes

(To be updated at phase completion)

---

## References

- `PHASE_16_PLANS.md` - Detailed implementation plan
- `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_USER_STORIES.md` - User stories
- `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_DEFINITION_OF_DONE.md` - DoD criteria
- `AGENTS.md` - Project commands and conventions

---

## Architectural Decisions (APPROVED)

**1. SQLAlchemy + Models.py**
- Define Job + JobStatus in `app/models.py` (extend existing file, don't create submodule)
- Import: `from app.models import Job, JobStatus`
- Section header: `# Phase 16: SQLAlchemy ORM Models`

**2. Database + Migrations**
- Create Alembic from scratch: `alembic init -t async app/migrations`
- Create `app/core/database.py` for AsyncEngine + AsyncSession
- Test DB: In-memory SQLite per test (`:memory:`)
- Dev DB: Persistent SQLite (`data/forgesyte.db`)
- Prod DB: Postgres (out of scope for Phase 16)

**3. Session Fixture**
- Add async fixture to conftest.py: `db_session()` creates in-memory SQLite
- Use `@pytest.mark.asyncio` for async test methods
- Fixture uses `AsyncSession` + `create_async_engine`

**4. Routes Location**
- Extend EXISTING file: `app/api_routes/routes/video_file_processing.py`
- DO NOT create new files for job_submit.py, job_status.py, job_results.py
- Commits 4, 7, 8 all add endpoints to SAME router
- Router already imported in main.py (line 40, 276)

**5. Storage Paths**
- MP4 files: `video_jobs/{job_id}.mp4`
- Results JSON: `video_jobs/{job_id}_results.json`

**6. All Answers from Codebase**
- ✅ Confirmed conftest.py exists with MockJobStore/MockTaskProcessor
- ✅ Confirmed models.py uses Pydantic (no SQLAlchemy currently)
- ✅ Confirmed video_file_processing.py exists (Phase 15)
- ✅ Confirmed no alembic.ini or migrations/ folder
- ✅ Confirmed AGENTS.md specifies "local filesystem for dev"

---

## Last Updated

**Date**: 2026-02-14  
**By**: AI Assistant  
**Status**: ✅ APPROVED - All 6 architectural questions answered from codebase
