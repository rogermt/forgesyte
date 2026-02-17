# Phase 16 Governance Rules

**Date**: 2026-02-13
**Phase**: 16 - Asynchronous Job Queue + Persistent Job State + Worker Execution

---

## Overview

Phase 16 introduces stateful job processing with queues and workers. This governance document defines what is allowed and what is forbidden to prevent scope creep.

---

## Forbidden Concepts (Phase 17+)

The following concepts are **FORBIDDEN** in Phase 16:

### Real-Time Streaming

- ❌ WebSockets
- ❌ Server-Sent Events (SSE)
- ❌ Real-time progress updates
- ❌ Live video processing

**Reason**: Real-time streaming is Phase 17 scope

### Frame-Level Progress

- ❌ Frame-by-frame progress reporting
- ❌ Progress callbacks per frame
- ❌ Granular progress updates

**Reason**: Too much overhead for Phase 16

### GPU Scheduling

- ❌ GPU-specific worker scheduling
- ❌ GPU resource allocation
- ❌ GPU queue prioritization

**Reason**: GPU scheduling is future scope

### Distributed Workers

- ❌ Multi-machine worker coordination
- ❌ Distributed lock management
- ❌ Cross-machine state synchronization

**Reason**: Distributed systems are Phase 17+ scope

### Multi-Pipeline Orchestration

- ❌ Dynamic pipeline selection per frame
- ❌ Multi-pipeline DAG execution
- ❌ Pipeline composition

**Reason**: Multi-pipeline orchestration is future scope

---

## Required Concepts (Phase 16)

### Job Queue

- ✅ FIFO queue for job_ids
- ✅ Redis (production) or in-memory (dev)
- ✅ Simple queue payload: `{job_id}`

### Job State

- ✅ Job table with status field
- ✅ Status transitions: pending → running → completed/failed
- ✅ Created/updated timestamps

### Worker Process

- ✅ Long-running daemon process
- ✅ Pulls jobs from queue
- ✅ Processes jobs using Phase 15 VideoFilePipelineService
- ✅ Updates job status in database

### Object Storage

- ✅ MP4 file storage
- ✅ Local filesystem (dev) or S3 (production)
- ✅ File path references in job table

### Polling Pattern

- ✅ Client polls for status
- ✅ Client polls for results
- ✅ No push notifications

---

## Placement Rules

### Functional Code

**Rule**: Phase 16 code goes in functional directories, not phase-named directories.

**Correct**:
```
server/app/api_routes/routes/job_submission.py
server/app/services/job_queue_service.py
server/app/workers/video_worker.py
server/app/tests/jobs/
```

**Incorrect**:
```
server/app/api_routes/routes/phase16_job.py
server/app/services/phase16_queue.py
server/app/tests/phase16/
```

### Documentation

**Rule**: Phase 16 documentation goes in `.ampcode/04_PHASE_NOTES/Phase_16/`, not in functional directories.

**Correct**:
```
.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_OVERVIEW.md
.ampcode/04_PHASE_NOTES/Phase_16/PHASE_16_ARCHITECTURE.md
```

**Incorrect**:
```
server/app/docs/phase16_overview.md
```

---

## Schema Rules

### Job Table Schema

```sql
CREATE TABLE jobs (
    job_id UUID PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    input_path TEXT NOT NULL,
    output_path TEXT,
    error_message TEXT,
    pipeline_id TEXT NOT NULL,
    frame_stride INTEGER DEFAULT 1,
    max_frames INTEGER
);
```

**Rules**:
- ✅ Only 4 status values allowed
- ✅ No additional status fields
- ✅ No progress field (that's Phase 17)

### Queue Payload Schema

```json
{
  "job_id": "uuid"
}
```

**Rules**:
- ✅ Only job_id in payload
- ✅ No additional metadata
- ✅ Deterministic structure

---

## API Response Rules

### Submit Response

```json
{
  "job_id": "uuid"
}
```

**Rules**:
- ✅ Only job_id returned
- ✅ No status or progress
- ✅ No estimated completion time

### Status Response

```json
{
  "job_id": "uuid",
  "status": "pending|running|completed|failed",
  "progress": 0.5,
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

**Rules**:
- ✅ Progress is optional
- ✅ Progress is float between 0.0 and 1.0
- ✅ No frame-level details

### Results Response

```json
{
  "job_id": "uuid",
  "results": [...],
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

**Rules**:
- ✅ Results match Phase 15 output format
- ✅ No additional metadata
- ✅ No processing time or performance metrics

---

## Enforcement

### Forbidden Vocabulary Scanner

**File**: `server/tools/validate_vovabulary.py `

**Purpose**: Scan Phase 16 functional code for forbidden concepts

**Usage**:
```bash
cd server
uv run python tools/validate_vovabulary.py 
```

**Exit Codes**:
- `0`: No violations found
- `1`: Violations found

### CI Workflow

**File**: `.github/workflows/phase16_validation.yml`

**Purpose**: Enforce Phase 16 governance on every PR

**Triggers**:
- Pull requests to `main`
- Pushes to `main`

**Steps**:
1. Validate plugins
2. Validate pipelines
3. Validate Phase 16 path (governance check)
4. Run pytest

**Failure**: Block PR merge if any step fails

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

## Checklist

Before committing Phase 16 code:

- [ ] No forbidden vocabulary in functional code
- [ ] No phase-named files in functional directories
- [ ] All functional code in appropriate directories
- [ ] All phase docs in `.ampcode/04_PHASE_NOTES/Phase_16/`
- [ ] All tests pass
- [ ] Pre-commit hooks pass
- [ ] Governance validator passes
- [ ] CI workflow passes

---

## See Also

- `PHASE_16_SCOPE.md` - What's in/out of scope
- `PHASE_16_ROLLBACK.md` - Rollback procedures
- `server/tools/forbidden_vocabulary_phase16.yaml` - Forbidden patterns
- `server/tools/validate_phase16_path.py` - Governance validator
- `.github/workflows/phase16_validation.yml` - CI workflow