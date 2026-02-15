# Phase 16 Architecture

**Date**: 2026-02-13
**Phase**: 16 - Asynchronous Job Queue + Persistent Job State + Worker Execution

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        PHASE 16 ARCHITECTURE                 │
└──────────────────────────────────────────────────────────────┘

Client
  │
  ▼
POST /video/submit
  │
  ▼
┌──────────────────────────────────────────────────────────────┐
│ FastAPI Router (submit)                                      │
│ - Validates MP4                                               │
│ - Stores file in object store                                 │
│ - Creates job row in DB                                       │
│ - Pushes job_id to queue                                      │
│ - Returns {job_id}                                            │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│ Job Queue (Redis/RabbitMQ/etc.)                              │
│ - FIFO                                                        │
│ - Holds job_id references                                     │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│ Worker Process                                                │
│ - Pull job_id from queue                                      │
│ - Load job metadata from DB                                   │
│ - Download MP4 from object store                              │
│ - Run VideoFilePipelineService (Phase‑15)                     │
│ - Store results in DB                                         │
│ - Mark job as completed                                       │
└───────────────┬──────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│ FastAPI Router (status)                                      │
│ GET /video/status/{job_id}                                   │
│ - Returns {status, progress}                                 │
│                                                              │
│ FastAPI Router (results)                                     │
│ GET /video/results/{job_id}                                  │
│ - Returns final results                                       │
└──────────────────────────────────────────────────────────────┘
```

---

# ⭐ **PHASE‑16 ARCHITECTURE (MERMAID)**

```
flowchart TD

A[POST /video/submit] --> B[Validate MP4]
B --> C[StorageService.save_file]
C --> D[DB: create job row]
D --> E[QueueService.enqueue(job_id)]
E --> F[Return {job_id}]

subgraph Worker
    G[QueueService.dequeue] --> H[DB: load job]
    H --> I[mark job running]
    I --> J[StorageService.load_file]
    J --> K[VideoFilePipelineService]
    K --> L[StorageService.save results]
    L --> M[mark job completed]
end

N[GET /video/status/{job_id}]
O[GET /video/results/{job_id}]
```

---

## Component Breakdown

### 1. API Layer

**Submit Endpoint** (`POST /video/submit`)
- Accepts MP4 file upload
- Validates file format
- Stores MP4 in object storage
- Creates job record in database
- Enqueues job_id
- Returns job_id to client

**Status Endpoint** (`GET /video/status/{job_id}`)
- Retrieves job status from database
- Returns current status (pending/running/completed/failed)
- Returns progress (optional)

**Results Endpoint** (`GET /video/results/{job_id}`)
- Retrieves job results from database
- Returns final results if completed
- Returns 404 if not completed

### 2. Queue Layer

**Job Queue**
- FIFO queue for job_ids
- Backed by Redis (production) or in-memory (dev)
- Worker processes pull from queue
- Supports priority (future)

### 3. Database Layer

**Job Table**
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

### 4. Worker Layer

**Worker Process**
- Long-running daemon process
- Pulls job_ids from queue
- Loads job metadata
- Downloads MP4 from object store
- Executes VideoFilePipelineService (Phase 15)
- Stores results in database
- Updates job status
- Handles errors gracefully

### 5. Object Storage

**MP4 File Storage**
- Stores uploaded MP4 files
- Returns file path for worker
- Supports local filesystem (dev) or S3 (production)

---

## Data Flow

### Job Submission Flow

```
Client uploads MP4
    ↓
FastAPI validates and stores MP4
    ↓
FastAPI creates job record in DB (status: pending)
    ↓
FastAPI pushes job_id to queue
    ↓
FastAPI returns job_id to client
```

### Worker Processing Flow

```
Worker pulls job_id from queue
    ↓
Worker loads job metadata from DB
    ↓
Worker updates job status to running
    ↓
Worker downloads MP4 from object store
    ↓
Worker runs VideoFilePipelineService
    ↓
Worker stores results in DB
    ↓
Worker updates job status to completed
```

### Status Retrieval Flow

```
Client requests status for job_id
    ↓
FastAPI queries DB for job record
    ↓
FastAPI returns status and progress
```

### Results Retrieval Flow

```
Client requests results for job_id
    ↓
FastAPI queries DB for job record
    ↓
If completed: FastAPI returns results
If not completed: FastAPI returns 404
```

---

## State Transitions

```
pending → running → completed
    ↓
  failed
```

**pending**: Job created, waiting for worker
**running**: Worker processing job
**completed**: Worker finished successfully
**failed**: Worker encountered error

---

## Error Handling

### Worker Errors

- **Transient errors**: Retry job (configurable retries)
- **Permanent errors**: Mark job as failed with error message
- **Worker crash**: Job stays pending, will be picked up by next worker

### Queue Errors

- **Queue full**: Return 503 Service Unavailable
- **Queue unavailable**: Return 503 Service Unavailable

### Database Errors

- **Connection lost**: Retry with backoff
- **Constraint violation**: Return 400 Bad Request

---

## Deployment Architecture

### Development Environment

```
┌──────────────────────────────────────────────────────────────┐
│ Single Machine                                               │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  API     │  │  Queue    │  │  Worker   │  │  DB       │  │
│  │  Server  │  │(in-memory)│  │ Process  │  │ (SQLite)  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                              │
│  ┌──────────┐                                                │
│  │  Object  │                                                │
│  │  Store   │                                                │
│  │ (local)  │                                                │
│  └──────────┘                                                │
└──────────────────────────────────────────────────────────────┘
```

### Production Environment

```
┌──────────────────────────────────────────────────────────────┐
│ Distributed System                                           │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  API     │  │  Queue    │  │  Workers  │  │  DB       │  │
│  │  Server  │  │ (Redis)   │  │ (multiple)│  │(Postgres) │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                              │
│  ┌──────────┐                                                │
│  │  Object  │                                                │
│  │  Store   │                                                │
│  │  (S3)    │                                                │
│  └──────────┘                                                │
└──────────────────────────────────────────────────────────────┘
```

---

## Key Properties

### Asynchronous

- Client submits job and gets job_id immediately
- Worker processes job in background
- Client polls for status/results

### Persistent

- Job state stored in database
- Survives server restarts
- Results available for retrieval

### Fault-Tolerant

- Worker crashes don't lose jobs
- Jobs can be retried
- Failed jobs can be debugged

### Scalable

- Multiple workers can process jobs concurrently
- Queue can handle backlog
- Database can be scaled independently

---

## Dependencies

### New Dependencies

- **Redis** (production) or **in-memory queue** (dev)
- **Database**: SQLite (dev) or PostgreSQL (production)
- **Object Storage**: Local filesystem (dev) or S3 (production)

### Existing Dependencies

- **Phase 15**: VideoFilePipelineService, OpenCV
- **Phase 14**: DAG pipeline engine

---

# ⭐ **PHASE‑16 ARCHITECTURE POSTER**  
### *ASCII poster for repo root or docs*

```
──────────────────────────────────────────────────────────────
                    PHASE‑16 ARCHITECTURE POSTER
──────────────────────────────────────────────────────────────

                ASYNCHRONOUS VIDEO PROCESSING PIPELINE
                ---------------------------------------

1. SUBMIT JOB
   POST /video/submit
   - Validate MP4
   - Save file to storage
   - Create job row (pending)
   - Enqueue job_id
   - Return {job_id}

2. WORKER LOOP
   dequeue job_id
   load job row
   mark running
   load MP4 from storage
   run VideoFilePipelineService
   save results
   mark completed

3. STATUS
   GET /video/status/{job_id}
   → {job_id, status, progress}

4. RESULTS
   GET /video/results/{job_id}
   → {job_id, results}

──────────────────────────────────────────────────────────────
GOVERNANCE RULES
──────────────────────────────────────────────────────────────
- No streaming
- No WebSockets
- No GPU scheduling
- No distributed workers
- No Phase‑17 concepts
- Deterministic queue payloads
- Deterministic worker transitions

──────────────────────────────────────────────────────────────
TESTING PYRAMID
──────────────────────────────────────────────────────────────
- Unit: job model, queue, storage, worker transitions
- Integration: submit → worker → status → results
- System: full lifecycle with real queue + DB

──────────────────────────────────────────────────────────────
```

## See Also

- `PHASE_16_OVERVIEW.md` - Feature overview
- `PHASE_16_SCOPE.md` - What's in/out of scope
- `PHASE_16_DEFINITION_OF_DONE.md` - Completion criteria
- `PHASE_16_ENDPOINTS.md` - API specification
- `PHASE_16_WORKER_LIFECYCLE.md` - Worker behavior
- `PHASE_16_TEST_STRATEGY.md` - Testing approach
- `PHASE_16_GOVERNANCE_RULES.md` - Governance rules