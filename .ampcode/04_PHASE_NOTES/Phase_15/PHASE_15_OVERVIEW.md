# ⭐ PHASE 15 — OVERVIEW

**Job-Based Queuing & Streaming for Cross-Plugin DAG Pipelines**

## Vision

Phase 15 transforms the system from:

- **Phase 14**: *Single-frame pipeline execution, synchronous, stateless*

into  

- **Phase 15**: *Multi-frame job queuing, asynchronous, with state management*

This is the moment pipelines become **scalable workflows**, not just one-off tools.

---

## What Phase 15 Adds

### From Single-Frame to Streaming

**Before (Phase 14)**:
```
User uploads image
    ↓
POST /pipelines/run
    ↓
Wait for result (blocking)
    ↓
Return result
```

**After (Phase 15)**:
```
User uploads video
    ↓
POST /jobs with { pipeline_id, video_url }
    ↓
Returns { job_id }  (immediate, non-blocking)
    ↓
Client polls GET /jobs/{job_id}
    ↓
Stream processes frame-by-frame
    ↓
Results accumulate
    ↓
Client retrieves full results
```

---

## Core Capabilities

### 1. Job Queue
- Submit pipelines for execution
- Track job status (queued, running, completed, failed)
- Persistent storage
- Job history

### 2. Async Execution
- Background job workers
- Multiple jobs running in parallel
- No blocking the HTTP server

### 3. Video Streaming
- Process video frame-by-frame
- State maintained across frames
- Detections/tracks accumulated

### 4. Results Persistence
- Store job results in database
- Query historical executions
- Analytics on past runs

### 5. Performance Metrics
- Execution time per node
- Throughput per pipeline
- Bottleneck detection

---

## Key Components

### Job Manager
Manages job lifecycle:
- Submit job
- Track status
- Retrieve result
- Store history

### Job Worker
Executes jobs asynchronously:
- Dequeue job
- Execute pipeline
- Update status
- Store results

### Job Database
Persistent storage:
- Jobs table
- Results table
- Metrics table
- History table

### State Manager
Maintains state across frames:
- Object IDs across time
- Detection history
- Tracking data

---

## Example: Video Analysis

**Request**:
```json
POST /jobs
{
  "pipeline_id": "player_tracking_v1",
  "video_url": "https://example.com/game.mp4",
  "options": { "stride": 5 }
}
```

**Response** (immediate):
```json
{
  "job_id": "job_abc123",
  "status": "queued"
}
```

**Later** - Client polls:
```
GET /jobs/job_abc123
→ { status: "processing", progress: 0.25 }

GET /jobs/job_abc123
→ { status: "processing", progress: 0.50 }

GET /jobs/job_abc123
→ { status: "completed", result: { frames: [...] } }
```

---

## Architecture

```
User Request
    ↓
HTTP Server (FastAPI)
    ↓
Job Manager (receive)
    ├── Validate job
    ├── Store in database
    └── Enqueue
    ↓
Job Queue (Redis/RabbitMQ)
    ↓
Job Workers (background tasks)
    ├── Dequeue job
    ├── Load pipeline
    ├── Initialize state
    ├── Process stream frame-by-frame
    │   ├── Execute pipeline
    │   ├── Accumulate results
    │   ├── Update state
    │   └── Save intermediate results
    ├── Finalize results
    └── Store in database
    ↓
Client Polling
    ├── GET /jobs/{job_id}
    └── Retrieve results
```

---

## New Concepts

### Job
A complete execution request:
```
{
  "job_id": "job_abc123",
  "pipeline_id": "player_tracking_v1",
  "source": "https://example.com/video.mp4",
  "status": "completed",
  "created_at": "2026-02-12T10:30:45Z",
  "completed_at": "2026-02-12T10:35:20Z",
  "result": { ... }
}
```

### Job Status
- `queued` — Waiting to execute
- `running` — Currently executing
- `completed` — Done successfully
- `failed` — Error occurred

### State Context
Data persistent across frames:
```python
{
  "previous_detections": [...],
  "track_ids": {...},
  "frame_count": 125,
  "duration_ms": 5000
}
```

### Results Accumulation
Collecting outputs across frames:
```python
{
  "frames": [
    { "frame_id": 0, "detections": [...] },
    { "frame_id": 1, "detections": [...] },
    ...
  ],
  "summary": {
    "total_frames": 150,
    "total_detections": 1250,
    "average_confidence": 0.92
  }
}
```

---

## Governance Principle

**Same as Phase 14: Everything explicit, nothing implicit.**

Additional rules for Phase 15:

- No default job priorities
- No automatic job cleanup
- No implicit state
- Job IDs are immutable
- Results are immutable
- Metrics are accurate

---

## Use Cases Phase 15 Enables

### 1. Batch Video Analysis
Submit 100 videos → Get results when ready

### 2. Live Video Feeds
Process RTMP/RTSP streams with persistence

### 3. Historical Analysis
Re-analyze old videos, track improvements

### 4. Performance Optimization
Identify slow pipelines, optimize bottlenecks

### 5. Audit Trail
Query who ran what, when, with what results

---

## Database Schema Preview

### Jobs Table
```sql
CREATE TABLE jobs (
    job_id VARCHAR PRIMARY KEY,
    pipeline_id VARCHAR NOT NULL,
    source_url VARCHAR,
    status VARCHAR,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message VARCHAR,
    INDEX (pipeline_id, created_at)
);
```

### Results Table
```sql
CREATE TABLE job_results (
    job_id VARCHAR PRIMARY KEY,
    pipeline_id VARCHAR,
    frame_count INT,
    output_json JSON,
    created_at TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
);
```

### Metrics Table
```sql
CREATE TABLE job_metrics (
    job_id VARCHAR,
    pipeline_id VARCHAR,
    node_id VARCHAR,
    execution_time_ms INT,
    timestamp TIMESTAMP,
    INDEX (pipeline_id, timestamp)
);
```

---

## Timeline

Expected implementation: **40-50 hours** (10 commits)

```
Commit 1:  Job models & database schema
Commit 2:  Job manager service
Commit 3:  Job worker (background tasks)
Commit 4:  Job REST endpoints
Commit 5:  Job WebSocket streaming
Commit 6:  State management
Commit 7:  Results accumulation
Commit 8:  Performance metrics
Commit 9:  Job history queries
Commit 10: Full integration tests
```

---

## Success Criteria

✅ Can submit pipeline job  
✅ Can poll job status  
✅ Can process video stream  
✅ Can accumulate results  
✅ Can query history  
✅ Can analyze metrics  
✅ 1300+ tests passing  
✅ 85%+ coverage  

---

## Phase 14 Dependencies

Phase 15 **requires** Phase 14 to be complete:

- ✅ Pipeline models (Phase 14)
- ✅ DAG validation (Phase 14)
- ✅ REST endpoints (Phase 14)
- ✅ Type checking (Phase 14)

Phase 15 **builds on** these to add:

- ➕ Job queuing
- ➕ Async execution
- ➕ State management
- ➕ Persistence

---

## Hard Boundaries (Not in Phase 15)

❌ Pipeline versioning → **Phase 16**  
❌ A/B testing frameworks → **Phase 17**  
❌ Advanced scheduling → **Phase 18**  
❌ Distributed execution → **Phase 19**  

Phase 15 is specifically about queuing and streaming, nothing more.

---

## Next Phase (Phase 16)

Once Phase 15 locked:
- Pipeline versioning (v1, v2, v3)
- Version selection in jobs
- Automatic version detection
- Rollback capabilities
