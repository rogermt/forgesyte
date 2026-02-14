# 🚀 PHASE 16 COMMIT 1 — START HERE

**Branch**: `feature/phase-16`  
**Status**: ✅ PLANNING COMPLETE - READY FOR IMPLEMENTATION  
**Date**: 2026-02-14  
**What to do**: Implement Commit 1 (Job Model + DB Migration) using TDD

---

## STOP — Read These Files First (In Order)

1. ✅ **PHASE_16_PLANS_CORRECTED.md** — Complete implementation plan (10 commits)
2. ✅ **PHASE_16_PROGRESS_CORRECTED.md** — Progress tracking with locked decisions
3. ✅ **PHASE_16_USER_STORIES.md** — Authoritative acceptance criteria for all 10 stories
4. ✅ **PHASE_16_DEV_Q&A_02.md** — Answers to all 14 critical/important/minor questions
5. ✅ **PHASE_16_COMMIT_01.md** — DuckDB-specific code for Commit 1
6. ✅ **PHASE_16_COMMIT_SCAFFOLDINGS.md** — Code templates for Commits 2-10
7. ✅ **PHASE_16_TEST_SUITE.md** — Test patterns and examples

---

## 100% CONFIDENT ANSWERS TO ALL QUESTIONS

### 🔴 Critical (Locked)

| # | Question | Answer | Source |
|---|----------|--------|--------|
| 1 | duckdb_engine package? | `duckdb-engine >= 0.11.0` | Q&A_02:13-25 |
| 2 | Existing SQLAlchemy? | None — create from scratch | Q&A_02:38-54 |
| 3 | FastAPI DI pattern? | Create `get_db()` in Commit 1 | Q&A_02:58-88 |
| 4 | Alembic init path? | `alembic init server/app/migrations` | Q&A_02:92-129 |

### 🟠 Important (Locked)

| # | Question | Answer | Source |
|---|----------|--------|--------|
| 5 | Test fixture location? | Root `tests/conftest.py` | Q&A_02:132-147 |
| 6 | Static or dynamic MP4? | Static first, dynamic fallback | Q&A_02:151-167 |
| 7 | Job.get()/save() methods? | NO — use standard SQLAlchemy | Q&A_02:170-188 |
| 8 | Magic bytes validation? | `b"ftyp" in data[:64]` | Q&A_02:192-207 |
| 9 | Pipeline signature? | `run_on_file(pipeline_id, file_path) -> list[dict]` | Q&A_02:210-228 |
| 10 | Results JSON? | `{"results": [...]}` | Q&A_02:232-248 |

### 🟡 Minor (Locked)

| # | Question | Answer | Source |
|---|----------|--------|--------|
| 11 | error_message length? | No max — unlimited | Q&A_02:251-257 |
| 12 | Queue payload? | UUID string only | Q&A_02:261-274 |
| 13 | Worker entry point? | `python -m app.workers.worker_runner` | Q&A_02:278-291 |
| 14 | DuckDB pooling? | Disable: `poolclass=NullPool` | Q&A_02:294-310 |

---

## COMMIT 1 IMPLEMENTATION (TDD)

### Phase 1: Write Failing Tests First

Create: `server/tests/app/models/test_job.py`

```python
@pytest.mark.unit
def test_job_defaults(session):
    job = Job(pipeline_id="yolo_ocr", input_path="video_jobs/test.mp4")
    session.add(job)
    session.commit()
    
    assert job.job_id is not None
    assert job.status == JobStatus.pending
    assert job.created_at is not None
    assert job.updated_at is not None

@pytest.mark.unit
def test_job_status_enum(session):
    job = Job(pipeline_id="yolo_ocr", input_path="test.mp4", status=JobStatus.running)
    session.add(job)
    session.commit()
    
    assert job.status == JobStatus.running
```

Run: `cd server && uv run pytest tests/app/models/test_job.py -v`  
Expected: ALL FAIL (model doesn't exist yet)

### Phase 2: Add duckdb-engine to pyproject.toml

```toml
dependencies = [
    # ... existing ...
    "duckdb-engine>=0.11.0",
]
```

### Phase 3: Implement Code

Create: `server/app/core/database.py`
- `Base = declarative_base()`
- `engine = create_engine("duckdb:///data/foregsyte.duckdb", future=True, poolclass=NullPool)`
- `SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)`
- See: PHASE_16_COMMIT_01.md lines 70-89

Create: `server/app/models/job.py`
- Import: `from app.core.database import Base`
- JobStatus enum: pending, running, completed, failed
- Job model with 8 fields (see PHASE_16_COMMIT_01.md lines 4-58)
- Use `duckdb_types.UUID` (NOT postgresql.UUID)

Initialize Alembic:
```bash
cd server
alembic init server/app/migrations
```

Create migration: `server/app/migrations/versions/<timestamp>_create_job_table.py`
- See: PHASE_16_COMMIT_01.md lines 151-194

Create test fixtures: `tests/conftest.py` (ADD to existing)
- `test_engine` fixture (in-memory DuckDB)
- `session` fixture (yields session, closes after)
- See: PHASE_16_COMMIT_01.md lines 206-229

### Phase 4: Run Tests

```bash
cd server
uv run pytest tests/app/models/test_job.py -v
```

Expected: ALL ✅ PASS

### Phase 5: Run Migration

```bash
cd server
alembic upgrade head
```

Verify: `data/foregsyte.duckdb` created

### Phase 6: Pre-Commit Verification

```bash
# All 4 must PASS
uv run pre-commit run --all-files      # black/ruff/mypy
cd server && uv run pytest tests/ -v   # all tests GREEN
python scripts/scan_execution_violations.py
cd server && uv run pytest tests/execution -v
```

### Phase 7: Commit

```bash
git add .
git commit -m "Phase-16 Commit 1: Initialize DuckDB + SQLAlchemy + Alembic, add Job model

- Added DuckDB engine and shared Base in app/core/database.py
- Initialized Alembic migration environment
- Added Job SQLAlchemy model using DuckDB UUID + Enum types
- Created first Alembic migration for jobs table
- Added DuckDB test fixtures (in-memory)
- Added Job model unit tests
- Verified governance compliance (no Phase-17 vocabulary)

All tests GREEN. All pre-commit checks passing."
```

---

## KEY FILES TO LOOK AT

| File | Purpose | Lines |
|------|---------|-------|
| PHASE_16_PLANS_CORRECTED.md | Full 10-commit plan | All |
| PHASE_16_USER_STORIES.md | Story 1 acceptance criteria | 10-67 |
| PHASE_16_COMMIT_01.md | DuckDB-specific code | 1-327 |
| PHASE_16_DEV_Q&A_02.md | All Q&A answers | 1-329 |
| server/pyproject.toml | Add duckdb-engine | Dependencies |

---

## FORBIDDEN IN COMMIT 1

❌ AsyncSession  
❌ PostgreSQL types  
❌ SQLite  
❌ Job.get() / Job.save() methods  
❌ Separate declarative_base() per file  
❌ Phase-named files  
❌ WebSockets/streaming/GPU  

---

## SUCCESS CRITERIA

- [ ] All tests in `tests/app/models/test_job.py` GREEN
- [ ] `data/foregsyte.duckdb` created
- [ ] Migration runs idempotent
- [ ] All pre-commit checks passing
- [ ] Zero governance violations
- [ ] Ready for Commit 2

---

## BRANCH INFO

```
Branch: feature/phase-16
Remote: origin/feature/phase-16
Status: Pushed and ready
```

---

## NEXT STEPS (After Commit 1)

1. Commit 2: Object Storage Adapter (StorageService + LocalStorage)
2. Commit 3: Queue Adapter (QueueService + InMemoryQueue)
3. Commit 4: Job Submission Endpoint (POST /video/submit)
4. ... (see PHASE_16_PLANS_CORRECTED.md for full list)

---

**Good luck. You've got all the answers. No guessing. Pure facts from authority.**
