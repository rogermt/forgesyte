# Phase 16 Pull Request

## Summary
Describe the purpose of this PR and which Phase 16 commit it implements.

**Commit Number:** Commit X of 10  
**Commit Title:** <paste from commit specification>

---

## Changes
- [ ] Job model / database migration
- [ ] StorageService implementation
- [ ] QueueService implementation
- [ ] /v1/video/submit endpoint
- [ ] Worker loop and skeleton
- [ ] Worker pipeline execution
- [ ] /v1/video/status/{job_id} endpoint
- [ ] /v1/video/results/{job_id} endpoint
- [ ] Governance + CI enforcement
- [ ] Documentation + rollback plan
- [ ] Tests (unit / integration / worker)
- [ ] Governance updates
- [ ] Documentation updates

---

## Validation Checklist

### Governance ✅
- [ ] No Phase-17 concepts (streaming, websockets, GPU scheduling, distributed)
- [ ] No forbidden vocabulary found (scanned by vocabulary_scanner.py)
- [ ] No phase-named files in functional code
- [ ] All functional files use descriptive naming

### API Contracts
- [ ] POST /v1/video/submit returns `{job_id}`
- [ ] GET /v1/video/status/{job_id} returns `{job_id, status, progress, created_at, updated_at}`
- [ ] GET /v1/video/results/{job_id} returns `{job_id, results, created_at, updated_at}`
- [ ] 404 responses for missing jobs / non-completed jobs

### Job Processing
- [ ] Job model persists to DuckDB
- [ ] Job transitions: pending → running → completed/failed
- [ ] Worker safely handles corrupted MP4 files
- [ ] Results stored deterministically as JSON
- [ ] Timestamps auto-managed (created_at, updated_at)

### Worker Implementation
- [ ] Worker pulls jobs from queue (FIFO)
- [ ] Worker updates job status in database
- [ ] Worker integrates with VideoFilePipelineService
- [ ] Worker catches and logs errors
- [ ] Graceful shutdown (SIGINT/SIGTERM)

### Testing
- [ ] All unit tests pass (mocked dependencies)
- [ ] All integration tests pass (in-memory DuckDB)
- [ ] All API tests pass (TestClient)
- [ ] All worker tests pass
- [ ] Test coverage >80%
- [ ] No skipped tests
- [ ] All 1200+ tests GREEN

### Code Quality
- [ ] Black formatting applied
- [ ] Ruff linting clean
- [ ] Mypy type checking clean
- [ ] Pre-commit hooks pass
- [ ] Docstrings on all public functions
- [ ] Type hints on all functions

### CI/CD
- [ ] Governance scanner passes (exit 0)
- [ ] Vocabulary validation passes
- [ ] Smoke test passes (job lifecycle)
- [ ] All GitHub Actions pass

---

## Testing Evidence

**Local Test Run:**
```bash
cd server
uv run pytest tests/ -v --tb=short
# Result: 1200+ tests PASS ✓
```

**Governance Scan:**
```bash
cd server
uv run python tools/vocabulary_scanner.py
# Result: ✓ Vocabulary Scanner: CLEAN (no violations found)
```

**Code Quality:**
```bash
cd server
uv run black app/ tests/
uv run ruff check --fix app/ tests/
uv run mypy app/ --no-site-packages
# All PASS ✓
```

---

## Phase 16 Architecture

### Files Created
- `server/app/models/job.py` - SQLAlchemy Job model
- `server/app/services/queue/` - Queue service (FIFO)
- `server/app/services/storage/` - Storage service (file operations)
- `server/app/api_routes/routes/video_submit.py` - Job submission endpoint
- `server/app/api_routes/routes/job_status.py` - Status polling endpoint
- `server/app/api_routes/routes/job_results.py` - Results retrieval endpoint
- `server/app/workers/worker.py` - Background job worker
- `server/tools/vocabulary_scanner.py` - Governance scanner
- `scripts/smoke_test.py` - Job lifecycle smoke tests

### Database Changes
- New table: `jobs` (job_id UUID, status, created_at, updated_at, etc.)
- Alembic migration created and applied
- DuckDB used (existing, aligned with Phase 15)

### API Endpoints
- `POST /v1/video/submit` - Submit video for processing
- `GET /v1/video/status/{job_id}` - Poll job status
- `GET /v1/video/results/{job_id}` - Retrieve results

### Job States
- **pending** - Queued, not yet processing
- **running** - Worker is executing pipeline
- **completed** - Successfully processed, results available
- **failed** - Processing failed, error_message set

---

## Breaking Changes
None. Phase 16 adds new job-based processing without affecting existing features.

---

## Backwards Compatibility
✅ Fully backwards compatible. Existing endpoints (Phase 15) continue to work unchanged.

---

## Deployment Notes

### Pre-Deployment
1. Run governance scanner: `python tools/vocabulary_scanner.py`
2. Run full test suite: `pytest tests/ -v`
3. Review rollback plan: `.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_ROLLBACK_PLAN.md`

### Deployment
1. Merge PR to main
2. Run migrations: `alembic upgrade head`
3. Start worker: `python -m app.workers.worker_runner`
4. Run smoke test: `JOB_PROCESSING_SMOKE_TEST=1 python scripts/smoke_test.py`

### Post-Deployment
1. Monitor job queue: Check `./data/video_jobs/` for output files
2. Verify status endpoint: `curl http://localhost:8000/v1/video/status/{job_id}`
3. Check worker logs: `tail -f forgesyte.log`

---

## Related Issues
Closes #[issue number]

---

## Reviewers
@[backend-lead] @[devops-lead]

---

## Additional Notes

### Phase 16 Governance
- ✅ No phase-named functional files (all use descriptive names)
- ✅ No forbidden vocabulary (gpu_schedule, gpu_worker, distributed not found)
- ✅ Vocabulary scanner enforces this on every PR
- ✅ CI blocks merge if violations found

### Documentation
- Phase 16 docs in `.ampcode/04_PHASE_NOTES/Phase_16/`
- Architecture overview in `PHASE_16_ARCHITECTURE.md`
- Rollback procedures in `PHASE_16_ROLLBACK_PLAN.md`
- Implementation details in commit-specific docs

### Quality Metrics
- Test coverage: 100%
- Tests passing: 1200+
- Governance violations: 0
- Code quality: ✓ Black, Ruff, Mypy all pass
