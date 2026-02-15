# Phase 16 Scope

**Date**: 2026-02-13
**Phase**: 16 - Asynchronous Job Queue + Persistent Job State + Worker Execution

---

## What IS In Scope

✅ **Job Queue**
- FIFO queue for job_ids
- Redis (production) or in-memory (dev)
- Simple queue payload: `{job_id}`

✅ **Job Persistence**
- Job table in database
- Job status tracking
- Job metadata storage
- Results storage

✅ **Worker Process**
- Long-running daemon process
- Pulls jobs from queue
- Processes jobs using Phase 15 VideoFilePipelineService
- Updates job status in database
- Handles errors gracefully

✅ **API Endpoints**
- `POST /video/submit` - Submit job
- `GET /video/status/{job_id}` - Get job status
- `GET /video/results/{job_id}` - Get job results

✅ **Object Storage**
- MP4 file storage
- Local filesystem (dev) or S3 (production)
- File path references in job table

✅ **Polling Pattern**
- Client polls for status
- Client polls for results
- No push notifications

---

## What is EXPLICITLY OUT OF SCOPE

### ❌ Real-Time Streaming

- **NO**: WebSockets
- **NO**: Server-Sent Events (SSE)
- **NO**: Real-time progress updates
- **NO**: Live video processing

**Reason**: Real-time streaming is Phase 17 scope

### ❌ Frame-Level Progress

- **NO**: Frame-by-frame progress reporting
- **NO**: Progress callbacks per frame
- **NO**: Granular progress updates
- **NO**: Frame-level status updates

**Reason**: Too much overhead for Phase 16

### ❌ GPU Scheduling

- **NO**: GPU-specific worker scheduling
- **NO**: GPU resource allocation
- **NO**: GPU queue prioritization
- **NO**: GPU worker pools

**Reason**: GPU scheduling is future scope

### ❌ Distributed Workers

- **NO**: Multi-machine worker coordination
- **NO**: Distributed lock management
- **NO**: Cross-machine state synchronization
- **NO**: Worker discovery protocols

**Reason**: Distributed systems are Phase 17+ scope

### ❌ Multi-Pipeline Orchestration

- **NO**: Dynamic pipeline selection per frame
- **NO**: Multi-pipeline DAG execution
- **NO**: Pipeline composition
- **NO**: Pipeline dependencies

**Reason**: Multi-pipeline orchestration is future scope

### ❌ Advanced Features

- **NO**: Job priorities
- **NO**: Job dependencies
- **NO**: Job chaining
- **NO**: Batch job submission
- **NO**: Job cancellation
- **NO**: Job retry configuration
- **NO**: Dead-letter queue
- **NO**: Job scheduling policies
- **NO**: Worker load balancing
- **NO**: Worker auto-scaling

**Reason**: These are future phases

---

## Governance Rules (Non-Negotiable)

| Rule | Consequence |
|------|-------------|
| No frame-level progress | Code review rejection |
| No real-time streaming | Architecture violation |
| No WebSockets | CI failure |
| No GPU scheduling | CI failure |
| No distributed workers | CI failure |
| No multi-pipeline orchestration | CI failure |
| Queue payload must be `{job_id}` only | Schema violation |
| Job status must be one of 4 values | Schema violation |
| Results must match Phase 15 format | Schema regression failure |

---

## Minimal Implementation

Phase 16 is intentionally **focused** on proving async job processing works:

1. Job submission → queue → worker → database → results
2. Simple FIFO queue
3. Single worker process
4. Basic polling pattern
5. No advanced features

**Why?** Build confidence in async processing before adding:
- Real-time streaming (Phase 17)
- Distributed workers (Phase 18)
- GPU scheduling (Phase 19)
- Multi-pipeline orchestration (Phase 20)

---

## Success Criteria

- [x] Submit job → get job_id
- [x] Worker processes job asynchronously
- [x] Job status retrievable via API
- [x] Results retrievable via API
- [x] Job state persists across restarts
- [ ] No forbidden vocabulary violations
- [ ] Governance rules enforced via CI

---

## Related Files

- `PHASE_16_OVERVIEW.md` - Feature overview
- `PHASE_16_ARCHITECTURE.md` - System diagram
- `PHASE_16_DEFINITION_OF_DONE.md` - Completion criteria
- `PHASE_16_ENDPOINTS.md` - API specification
- `PHASE_16_WORKER_LIFECYCLE.md` - Worker behavior
- `PHASE_16_TEST_STRATEGY.md` - Testing procedures
- `PHASE_16_GOVERNANCE_RULES.md` - Governance rules