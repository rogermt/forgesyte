

# ⭐ **PHASE‑16 USER STORIES (FINAL, AUTHORITATIVE)**
### *Asynchronous Job Queue + Persistent Job State + Worker Execution*

Each story is atomic, testable, and maps to one commit.

---

## **Story 1 — Job Model + DB Migration**
**Commit 1 of 10**

### **Story**
As a backend engineer, I want a persistent job table so that job submissions can be tracked across restarts.

### **Acceptance Criteria**
- SQLAlchemy model created at `server/app/models/job.py`
- Alembic migration created at `server/app/migrations/`
- Job table fields:

| Field | Type | Notes |
|-------|------|-------|
| job_id | UUID (PK) | generated server‑side |
| status | enum | pending, running, completed, failed |
| created_at | timestamp | auto |
| updated_at | timestamp | auto |
| pipeline_id | string | required |
| input_path | string | path in object storage |
| output_path | string | path to results JSON |
| error_message | string | nullable |

### **Tests**
- `tests/models/test_job.py`
- 100% passing

### 🚫 **OUT OF SCOPE**
- [ ] `frame_stride` or `max_frames` columns — Phase‑15 synchronous batch concepts, not Phase‑16 async job concepts
- [ ] `progress` column — progress is derived from status, not stored
- [ ] `worker_id` column — distributed worker tracking is Phase 18+
- [ ] `priority` column — job prioritization is future scope
- [ ] Queue logic in this commit
- [ ] Worker logic in this commit
- [ ] Manual table creation — use Alembic migration only
- [ ] Status values beyond the four allowed (pending, running, completed, failed)
- [ ] Phase‑named file (`phase16_job.py`) — use functional name `job.py`

---

## **Story 2 — Object Storage Adapter**
**Commit 2 of 10**

### **Story**
As a contributor, I want a storage abstraction so that MP4 files and results JSON can be saved and retrieved independently of local disk.

### **Acceptance Criteria**
- `StorageService` interface at `server/app/services/storage/base.py`
- Local filesystem implementation at `server/app/services/storage/local_storage.py`
- Deterministic paths:

```
./data/video_jobs/{job_id}.mp4
./data/video_jobs/{job_id}_results.json
```

- Methods:
  - `save_file(src, dest_path)`
  - `load_file(path)`
  - `delete_file(path)`

### **Tests**
- `tests/services/storage/test_local_storage.py`

### 🚫 **OUT OF SCOPE**
- [ ] S3 storage — local filesystem only in Phase‑16
- [ ] Cloud storage adapters of any kind
- [ ] Compression or encoding logic
- [ ] File streaming or chunked uploads
- [ ] File expiry or TTL logic
- [ ] Directory listing or search capabilities
- [ ] Storing results in the database — results go to object storage as JSON files
- [ ] Hardcoded absolute paths — use relative, configurable paths
- [ ] Phase‑prefixed filenames (`phase16_storage.py`)

---

## **Story 3 — Queue Adapter**
**Commit 3 of 10**

### **Story**
As a contributor, I want a queue abstraction so that job IDs can be pushed and popped without binding to a specific backend.

### **Acceptance Criteria**
- `QueueService` interface at `server/app/services/queue/base.py`
- In‑memory implementation at `server/app/services/queue/memory_queue.py`
- Backend: Python `queue.Queue`
- Methods:
  - `enqueue(job_id)`
  - `dequeue()`
  - `size()`

### **Tests**
- `tests/services/queue/test_memory_queue.py`

### 🚫 **OUT OF SCOPE**
- [ ] Redis queue — in‑memory only in Phase‑16
- [ ] RabbitMQ, Celery, or any external queue backend
- [ ] Metadata in the queue payload — strictly `{job_id}` only
- [ ] Priority queue logic
- [ ] Dead‑letter queue logic
- [ ] Queue persistence or durability
- [ ] Queue acknowledgment or visibility timeout
- [ ] Batch enqueue/dequeue operations
- [ ] Queue monitoring or metrics endpoints
- [ ] Job metadata (status, paths, pipeline_id) in the queue message

---

## **Story 4 — Job Submission Endpoint**
**Commit 4 of 10**

### **Story**
As an API consumer, I want to submit a video for processing and receive a job_id.

### **Acceptance Criteria**
- Route: `POST /video/submit`
- Uses FastAPI `UploadFile`
- MP4 validation via **magic bytes** (`ftyp`)
- Saves file via StorageService
- Creates job row with:
  - job_id
  - pipeline_id
  - input_path
  - status = pending
- Enqueues job_id
- Returns:

```json
{ "job_id": "<uuid>" }
```

### **Tests**
- `tests/api/test_job_submit.py`
- Uses fixture: `tests/fixtures/tiny.mp4`

### 🚫 **OUT OF SCOPE**
- [ ] MP4 validation by file extension — use magic bytes only
- [ ] MP4 validation with ffprobe or ffmpeg
- [ ] Returning status, progress, or estimated completion time in the submit response — only `{job_id}`
- [ ] Synchronous processing — submission must be fully async
- [ ] Batch submissions (multiple files per request)
- [ ] Non‑MP4 video formats (MOV, AVI, etc.) in Phase‑16
- [ ] Authentication or authorization logic
- [ ] Rate limiting
- [ ] File size limits beyond reasonable defaults
- [ ] Blocking the HTTP response waiting for worker pickup

---

## **Story 5 — Worker Skeleton**
**Commit 5 of 10**

### **Story**
As a worker engineer, I want a worker loop that pulls job IDs and marks jobs as running.

### **Acceptance Criteria**
- Worker class at `server/app/workers/worker.py`
- Entry point at `server/app/workers/worker_runner.py`
- Methods:
  - `run_once()`
  - `run_forever()`
- Behavior:
  - dequeue job_id
  - load job row
  - mark status → running
  - handle empty queue with sleep/backoff
  - handle SIGINT/SIGTERM gracefully

### **Tests**
- `tests/workers/test_job_worker.py`

### 🚫 **OUT OF SCOPE**
- [ ] Pipeline execution in this commit — skeleton only, no processing
- [ ] Multi‑threaded or multi‑process worker pools
- [ ] Distributed worker coordination
- [ ] GPU scheduling or resource allocation
- [ ] Worker registration or discovery
- [ ] Health check endpoints for the worker
- [ ] Auto‑scaling logic
- [ ] Docker/systemd/supervisor configuration — plain Python entry point only
- [ ] Skipping signal handling — SIGINT and SIGTERM must be handled gracefully
- [ ] Busy‑looping without sleep/backoff when queue is empty

---

## **Story 6 — Worker Executes Phase‑15 Pipeline**
**Commit 6 of 10**

### **Story**
As a worker engineer, I want the worker to run the Phase‑15 VideoFilePipelineService on the submitted MP4.

### **Acceptance Criteria**
- Worker loads MP4 via StorageService
- Calls `VideoFilePipelineService.run_on_file()`
- Saves results JSON to:

```
./data/video_jobs/{job_id}_results.json
```

- Updates job row:
  - output_path
  - status → completed
- On exception:
  - status → failed
  - error_message stored

### **Tests**
- `tests/workers/test_worker_pipeline.py`
- Uses fixture: `tests/fixtures/make_tiny_mp4.py`

### 🚫 **OUT OF SCOPE**
- [ ] Creating a new pipeline service — reuse Phase‑15 `VideoFilePipelineService` exactly
- [ ] Duplicating pipeline execution logic
- [ ] Frame‑level progress callbacks or reporting
- [ ] Real‑time streaming of results
- [ ] Storing results in the database — store as JSON in object storage only
- [ ] Retry logic in this commit — simple success/fail only
- [ ] Timeout logic for pipeline execution
- [ ] Swallowing exceptions silently — always set error_message on failure
- [ ] Leaving job in `running` status if an exception occurs — must transition to `failed`

---

## **Story 7 — Job Status Endpoint**
**Commit 7 of 10**

### **Story**
As an API consumer, I want to check the status of a job.

### **Acceptance Criteria**
- Route: `GET /video/status/{job_id}`
- Returns:

```json
{
  "job_id": "...",
  "status": "...",
  "progress": 0 | 0.5 | 1.0,
  "created_at": "...",
  "updated_at": "..."
}
```

- Progress rules:
  - pending → 0
  - running → 0.5
  - completed/failed → 1.0
- 404 if job not found

### **Tests**
- `tests/api/test_job_status.py`

### 🚫 **OUT OF SCOPE**
- [ ] Frame‑level progress (e.g., "frame 47 of 120") — coarse progress only (0, 0.5, 1.0)
- [ ] Estimated completion time
- [ ] Processing speed or performance metrics
- [ ] WebSocket push notifications
- [ ] Server‑Sent Events (SSE)
- [ ] Long‑polling
- [ ] Storing progress as a database column — derive it from status
- [ ] Returning partial results in the status response
- [ ] Queue position information

---

## **Story 8 — Job Results Endpoint**
**Commit 8 of 10**

### **Story**
As an API consumer, I want to retrieve results once the job is completed.

### **Acceptance Criteria**
- Route: `GET /video/results/{job_id}`
- Returns:

```json
{
  "job_id": "...",
  "results": [...]
}
```

- 404 if:
  - job not found
  - job not completed

### **Tests**
- `tests/api/test_job_results.py`

### 🚫 **OUT OF SCOPE**
- [ ] Partial results for in‑progress jobs
- [ ] Results for failed jobs — 404 only
- [ ] Pagination of results
- [ ] Result filtering or search
- [ ] Result download as file (e.g., CSV export)
- [ ] Processing time or performance metrics in the results response
- [ ] Changing the Phase‑15 output format — results must match exactly
- [ ] Caching results in memory — always load from object storage
- [ ] Result expiry or TTL

---

## **Story 9 — Governance + CI Enforcement**
**Commit 9 of 10**

### **Story**
As a release manager, I want governance rules preventing Phase‑17 concepts from leaking into Phase‑16.

### **Acceptance Criteria**
- Create:
  - `forbidden_vocabulary_phase16.yaml`
  - `validate_phase16_path.py`
  - `.github/workflows/phase16_validation.yml`
- Forbidden terms:
  - websocket
  - streaming
  - gpu_schedule
  - distributed
  - gpu_worker
  - sse (server‑sent events)
  - real_time
- Smoke test updated:
  - submit → status → results

### **Tests**
- Governance tests must pass
- CI must block violations

### 🚫 **OUT OF SCOPE**
- [ ] Skipping forbidden vocabulary scanning — must run on every PR
- [ ] Allowing Phase‑17 vocabulary in functional code (WebSocket, streaming, SSE, GPU scheduling, distributed)
- [ ] Phase‑named files in functional directories (e.g., `phase16_worker.py` in `server/app/`)
- [ ] Governance documentation in functional directories — keep in `.ampcode/04_PHASE_NOTES/Phase_16/`
- [ ] Making governance checks optional or soft‑fail — must block merge
- [ ] Governance exceptions or bypass mechanisms
- [ ] Skipping the smoke test in CI
- [ ] Allowing pre‑commit hooks to be disabled

---

## **Story 10 — Documentation + Rollback Plan**
**Commit 10 of 10**

### **Story**
As a new contributor, I want complete Phase‑16 documentation so I can understand, contribute to, and if necessary roll back the entire phase.

### **Acceptance Criteria**
- Create/update:
  - Overview
  - Architecture
  - Endpoints
  - Migration Guide
  - Rollback Plan
  - Contributor Exam
  - Release Notes
- Rollback plan must be executable
- All links verified

### **Tests**
- All documentation files exist
- All cross‑references valid

### 🚫 **OUT OF SCOPE**
- [ ] Leaving the rollback plan as a stub — must list every file to remove and every migration to revert
- [ ] Referencing Phase‑17 features as if they exist
- [ ] Speculative architecture for future phases
- [ ] Skipping the contributor exam — must be complete with answer key
- [ ] Broken cross‑reference links between documents
- [ ] Documenting features that were not implemented
- [ ] TODO items — Phase‑16 documentation must be complete as‑is
- [ ] Mixing Phase‑16 docs with earlier phase docs — keep in `Phase_16/` directory only

---

# ⭐ **GLOBAL OUT OF SCOPE — APPLIES TO ALL STORIES**

These rules apply to **every single commit** across Phase‑16:

| # | Item | Consequence |
|---|------|-------------|
| G1 | WebSockets | PR rejected, CI failure |
| G2 | Server‑Sent Events (SSE) | PR rejected, CI failure |
| G3 | Real‑time streaming | PR rejected, CI failure |
| G4 | GPU scheduling | PR rejected, CI failure |
| G5 | Distributed worker coordination | PR rejected, CI failure |
| G6 | Multi‑pipeline DAG orchestration | PR rejected, CI failure |
| G7 | Frame‑level progress tracking | PR rejected, code review rejection |
| G8 | Metadata in queue payloads beyond `{job_id}` | Schema violation |
| G9 | Job status values beyond the four allowed | Schema violation |
| G10 | Phase‑prefixed filenames in functional directories | Governance violation |
| G11 | Redis, RabbitMQ, Celery, or external queue backends | Architecture violation |
| G12 | S3 or cloud storage | Architecture violation |
| G13 | Authentication, authorization, or rate limiting | Scope violation |
| G14 | Job cancellation, job chaining, or job dependencies | Scope violation |
| G15 | Worker auto‑scaling or load balancing | Scope violation |
| G16 | Changing the Phase‑15 pipeline output format | Regression violation |
| G17 | Skipping tests — every commit must have passing tests | Quality gate failure |
| G18 | Committing without running governance validator | Process violation |
| G19 | Docker, systemd, or container orchestration | Scope violation |
| G20 | Monitoring, alerting, or observability infrastructure | Scope violation |