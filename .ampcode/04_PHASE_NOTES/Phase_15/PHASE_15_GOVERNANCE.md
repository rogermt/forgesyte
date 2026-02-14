# Phase 15 Governance

**Date**: 2026-02-13
**Phase**: 15 - Offline Batch Video Processing
**Status**: FINAL

---

## Overview

Phase 15 enforces strict governance to prevent scope creep and ensure the implementation stays within the defined batch-only scope.

**Core Principle**: Phase 15 is minimal, focused, and batch-only. No job queues, no async, no persistence, no streaming.

---

## Forbidden Vocabulary

The following terms **MUST NOT** appear in Phase 15 functional code:

### Phase 16: Job Queue Concepts

| Pattern | Reason |
|---------|--------|
| `job_id` | Phase 16 concept (job tracking) |
| `queue` | Phase 16 concept (job queuing) |
| `worker` | Phase 16 concept (distributed workers) |

### Job Queue Libraries

| Pattern | Reason |
|---------|--------|
| `celery` | Job queue library (Phase 16 only) |
| `rq` | RQ job queue library (Phase 16 only) |
| `redis` | Redis (Phase 16 only) |
| `rabbitmq` | RabbitMQ (Phase 16 only) |

### Database Concepts (Phase 16+)

| Pattern | Reason |
|---------|--------|
| `database` | Database persistence (Phase 16 only) |
| `sql` | SQL queries (Phase 16 only) |
| `postgres` | PostgreSQL (Phase 16 only) |
| `mongodb` | MongoDB (Phase 16 only) |
| `insert_one` | Database operations (Phase 16 only) |
| `update_one` | Database operations (Phase 16 only) |

### YOLO Tracker Concepts

| Pattern | Reason |
|---------|--------|
| `reid` | Re-identification tracking (not in Phase 15) |
| `tracking` | Player tracking (not in Phase 15 scope) |
| `track_ids` | Track IDs (not in Phase 15 scope) |

### Metrics/Observability Concepts

| Pattern | Reason |
|---------|--------|
| `metrics` | Metrics tracking (future phase) |
| `execution_time_ms` | Execution metrics (future phase) |

### Real-Time Streaming (Phase 17+)

| Pattern | Reason |
|---------|--------|
| `websocket` | WebSocket (Phase 17 real-time only) |
| `streaming` | Streaming (Phase 17 real-time only) |

### File Naming

| Pattern | Reason |
|---------|--------|
| `phase15`, `phase_15`, `phase-15` | Use functional names (e.g., `video/`) |

---

## Governance Enforcement

### 1. Code Validator

**File**: `server/tools/validate_video_batch_path.py`

**Purpose**: Scan functional code for forbidden vocabulary

**Usage**:
```bash
cd server
uv run python tools/validate_video_batch_path.py
```

**Exit Codes**:
- `0`: No violations found
- `1`: Violations found

**Scanned Directories**:
- `server/app/api/routes/`
- `server/app/services/`
- `server/app/tests/video/`

### 2. CI Workflow

**File**: `.github/workflows/video_batch_validation.yml`

**Purpose**: Enforce governance on every PR to `main`

**Triggers**:
- Pull requests to `main`
- Pushes to `main`

**Steps**:
1. Validate plugins
2. Validate pipelines
3. Validate video batch path (governance check)
4. Run pytest

**Failure**: Block PR merge if any step fails

### 3. Pre-Commit Hooks

**File**: `.pre-commit-config.yaml`

**Purpose**: Enforce code quality before commit

**Checks**:
- Black formatting
- Ruff linting
- MyPy type checking
- ESLint (web-ui)
- Pytest

**Usage**:
```bash
cd server
uv run pre-commit run --all-files
```

---

## Placement Rules

### Functional Code

**Rule**: Functional code goes in functional directories, not phase-named directories.

**Correct**:
```
server/app/api/routes/video_file.py
server/app/services/video_file_pipeline_service.py
server/app/tests/video/
```

**Incorrect**:
```
server/app/api/routes/phase15_video.py
server/app/services/phase15_service.py
server/app/tests/phase15/
server/app/tests/phase_15/
```

### Documentation

**Rule**: Phase documentation goes in `.ampcode/04_PHASE_NOTES/Phase_15/`, not in functional directories.

**Correct**:
```
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_OVERVIEW.md
.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_ARCHITECTURE.md
```

**Incorrect**:
```
server/app/docs/phase15_overview.md
server/app/docs/PHASE_15.md
```

### Tests

**Rule**: Tests go in functional directories named after what they test.

**Correct**:
```
server/app/tests/video/
```

**Incorrect**:
```
server/app/tests/phase15/
server/app/tests/phase_15/
server/app/tests/phase15_tests/
```

---

## Scope Boundaries

### In Scope (Phase 15)

✅ Single synchronous request/response cycle
✅ Frame extraction and processing
✅ YOLO + OCR pipeline
✅ Aggregated JSON results
✅ Batch-only processing
✅ Stateless per-frame execution

### Out of Scope (Future Phases)

❌ Job queues (Redis, Celery, RQ, Bull)
❌ Async workers
❌ Database persistence (PostgreSQL, MongoDB)
❌ Real-time streaming (WebSocket, SSE)
❌ Multi-frame tracking (ReID, track_ids)
❌ Visual output (bounding boxes, annotations)
❌ Metrics collection
❌ Multiple pipelines

---

## Consequences of Violations

### Code Review

- **Violation**: Reject PR with explanation
- **Fix**: Remove forbidden vocabulary or refactor to stay in scope

### CI/CD

- **Violation**: Workflow fails, blocks merge
- **Fix**: Fix violations and re-run CI

### Pre-Commit

- **Violation**: Hook fails, blocks commit
- **Fix**: Fix violations and re-run pre-commit

---

## Governance Checklist

Before committing Phase 15 code:

- [ ] No forbidden vocabulary in functional code
- [ ] No phase-named files in functional directories
- [ ] All functional code in appropriate directories
- [ ] All phase docs in `.ampcode/04_PHASE_NOTES/Phase_15/`
- [ ] All tests pass (38 tests)
- [ ] Pre-commit hooks pass
- [ ] Governance validator passes
- [ ] CI workflow passes

---

## Exceptions

No exceptions. Governance rules are non-negotiable for Phase 15.

If you need a feature that requires forbidden vocabulary:
1. Document the use case
2. Discuss with maintainers
3. Create a new phase for that feature
4. Implement in the new phase

---

## Monitoring

### Violation Detection

Violations are detected by:
1. `server/tools/validate_video_batch_path.py`
2. `.github/workflows/video_batch_validation.yml`
3. Pre-commit hooks

### Violation Tracking

All violations are tracked in:
- CI workflow logs
- Pre-commit hook output
- Code review comments

### Violation Resolution

Violations must be resolved before:
- Committing code
- Merging PRs
- Releasing to production

---

## See Also

- `PHASE_15_SCOPE.md` - What's in/out of scope
- `PHASE_15_ROLLBACK.md` - Rollback procedures
- `server/tools/forbidden_vocabulary.yaml` - Forbidden patterns
- `server/tools/validate_video_batch_path.py` - Governance validator
- `.github/workflows/video_batch_validation.yml` - CI workflow