# Phase 8 Context Checkpoint — For Next Chat

**Status:** Step 1 Schema Foundation in progress  
**Branch:** `feature/phase8-metrics-foundation`  
**Last Commit:** `0ce708e` — Phase 8 Step 1: DuckDB metrics schema foundation  

---

## What's Done ✅

### Step 1: DuckDB Schema Foundation
- ✅ `server/app/observability/duckdb/schema.sql` created (4 tables: job_metrics, plugin_metrics, overlay_metrics, device_usage)
- ✅ `server/tests/observability/test_metrics_schema.py` (5 tests, all passing)
- ✅ `duckdb>=1.0.0` added to `server/pyproject.toml`
- ✅ Module structure created: `server/app/observability/`, `server/tests/observability/`

---

## What's Next (APPROVED PLAN) 🚀

### Remaining Step 1 Tasks (BEFORE Step 2):
1. Create `server/app/observability/duckdb/load_schema.py`
   - Loads schema.sql at DB initialization
   - Idempotent, safe for tests + startup
   - Per: PHASE_8_NOTES_02.md:1721-1745

2. Create `scripts/ci/test_schema_drift.py`
   - CI guardrail: compares `.ampcode` spec ↔ runtime schema
   - Fail if drift detected
   - Per: PHASE_8_NOTES_02.md:1751-1785

3. Create `.ampcode/04_PHASE_NOTES/Phase_8/PHASE_8_METRICS_SCHEMA.sql`
   - Canonical governance spec
   - Must match runtime schema exactly
   - Per: PHASE_8_NOTES_02.md:1529

### Step 2: Structured Logging (AFTER Step 1 complete)
**Approved approach:**
- ✔ Unit tests first (mock job pipeline)
- ✔ Then integration tests (real pipeline)
- ✔ LogCapture as standalone class (not fixture)
- ✔ Import directly in tests as context manager

**Files to create (per PHASE_8_NOTES_02.md:2138+):**
- `server/app/logging/context.py` — job_id context var
- `server/app/logging/filters.py` — JobContextFilter
- `server/app/logging/capture.py` — LogCapture test helper
- `server/tests/observability/test_job_logging_context.py` — Step 2 tests (7 edge cases)

**Edge cases to test:**
1. Concurrent jobs don't mix IDs
2. Plugin logs include job_id + plugin name
3. Device fallback logs include correlation IDs
4. Error logs include job_id + context
5. Async context preserves job_id
6. Multiple tools share same job_id
7. Missing job_id fails (strict mode)

---

## Key Architecture Decisions

**Two-layer schema model:**
- `.ampcode/04_PHASE_NOTES/Phase_8/PHASE_8_METRICS_SCHEMA.sql` = governance spec
- `server/app/observability/duckdb/schema.sql` = runtime implementation
- CI compares both to detect drift

**Logging context:**
- ContextVar-based job_id propagation
- Filter injected into logging config
- LogCapture captures logs for assertions in tests

**TDD approach:**
- Never skip foundation (load_schema.py + drift checker)
- Unit tests before integration tests
- No code until test fails first

---

## Current Branch Status
```bash
git checkout feature/phase8-metrics-foundation
# Tests passing: 5/5 schema tests
# Ready to add: load_schema.py, test_schema_drift.py, governance spec
```

---

## Commands Needed
```bash
cd /home/rogermt/forgesyte/server

# Run metrics schema tests
uv run pytest tests/observability/test_metrics_schema.py -v

# Full test suite (should still pass)
uv run pytest tests/ -v

# Lint + type check
uv run ruff check app/
uv run mypy app/
```

---

## Next Chat Starting Point

1. **Confirm ready to proceed with Step 1 completion** (load_schema.py, test_schema_drift.py, governance spec)
2. **Write failing test for load_schema.py** (test that DB can be initialized from schema)
3. **Implement + commit Step 1**
4. Then proceed to Step 2 logging (unit tests first)

**Do NOT start logging code** until Step 1 is 100% complete with CI guardrails in place.
