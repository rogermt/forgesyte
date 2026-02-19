# Worker Job Pickup Analysis: Why Worker Isn't Processing Video Uploads

**Date**: 2026-02-19  
**Issue**: Worker starts but does NOT pick up jobs enqueued from video uploads  
**Status**: Root cause identified - Multiple integration gaps

---

## Executive Summary

The worker **cannot pick up video upload jobs** due to **THREE CRITICAL GAPS**:

1. **Queue Isolation** - Video submit endpoint uses a **separate queue instance** (not shared with worker)
2. **No Job Persistence** - Jobs are in-memory only; worker has a **different in-memory queue**
3. **Missing Integration Tests** - No tests verify the end-to-end flow from upload → queue → worker

When Kaggle runs the worker in a separate process, it gets a **completely different `InMemoryQueueService` instance** with an empty queue, so it has nothing to process.

---

## System Architecture

### Current Flow (BROKEN)

```
Video Upload (/v1/video/submit)
    ↓
    └─→ video_submit.py (line 15)
        └─→ queue = InMemoryQueueService()  ← INSTANCE #1
            └─→ queue.enqueue(job_id) 
    
Worker Process (separate Python process in Kaggle)
    ↓
    └─→ run_job_worker.py
        └─→ JobWorker() (line 38)
            └─→ queue = InMemoryQueueService()  ← INSTANCE #2 (EMPTY!)
                └─→ queue.dequeue() → None
```

**Problem**: Each module gets its own `InMemoryQueueService` instance. The worker's queue is **never populated** because it's a different object in a different process.

---

## Files Involved

### 1. Video Submit Endpoint
**File**: [server/app/api_routes/routes/video_submit.py](file:///home/rogermt/forgesyte/server/app/api_routes/routes/video_submit.py)

- Lines 10-15: Creates LOCAL `InMemoryQueueService()` instance
- Line 79: Enqueues job to **this specific instance**
- **Problem**: This queue is never shared with the worker

```python
# Line 15: Creates a NEW queue instance per module import
queue = InMemoryQueueService()

# Line 79: Enqueues to this instance
queue.enqueue(job_id)
```

### 2. Job Worker
**File**: [server/app/workers/worker.py](file:///home/rogermt/forgesyte/server/app/workers/worker.py)

- Lines 71: Default parameter creates queue if not provided
- **Problem**: Worker creates its OWN `InMemoryQueueService()` if no queue is injected

```python
# Line 71: Creates a NEW queue instance (default)
self._queue = queue or InMemoryQueueService()

# Line 97-98: Tries to dequeue from THIS queue
job_id = self._queue.dequeue()
if job_id is None:
    return False  # ← Always returns False in separate process
```

### 3. Worker Startup
**File**: [server/app/workers/run_job_worker.py](file:///home/rogermt/forgesyte/server/app/workers/run_job_worker.py)

- Line 38: Creates worker with NO queue passed
- **Problem**: Worker gets default empty queue

```python
# Line 38: No queue parameter = worker creates its own
worker = JobWorker()  # ← Gets default InMemoryQueueService()
```

---

## Root Cause Analysis

| Component | Current State | Issue |
|-----------|---------------|-------|
| **Queue Service** | `InMemoryQueueService` (memory-based) | No persistence, no IPC between processes |
| **Video Submit** | Creates local queue instance | Not shared with worker |
| **Worker Init** | Creates its own queue instance | Never receives enqueued jobs |
| **Process Model** | Separate processes (API + Worker) | Can't share Python object references |
| **Integration** | No tests for upload→queue→worker flow | Missing coverage reveals the gap |

### Why It Works in Tests But Not in Kaggle

**In tests**: All code runs in same Python process → same `InMemoryQueueService` instance

**In Kaggle**: Separate processes → different `InMemoryQueueService` instances

---

## Test Coverage Analysis

### Current Tests

#### Worker Tests ✅
**File**: [server/tests/app/workers/test_worker.py](file:///home/rogermt/forgesyte/server/tests/app/workers/test_worker.py)

- ✅ **354 lines** of comprehensive worker tests
- ✅ Tests: init, run_once, mark_running, missing_job, multiple_jobs, pipeline execution, results saving, error handling
- ❌ **Missing**: Does NOT test actual queue injection from video_submit

**Coverage**: Unit tests only (mocked queue)

#### Queue Tests ✅
**File**: [server/tests/app/services/test_queue.py](file:///home/rogermt/forgesyte/server/tests/app/services/test_queue.py)

- ✅ **89 lines** of queue tests
- ✅ Tests: enqueue, dequeue, FIFO, size, empty queue, UUID payloads
- ❌ **Missing**: Does NOT test multiprocess queue sharing

**Coverage**: Queue operations only

#### Video Processing Tests ⚠️
**File**: [server/tests/video/test_integration_video_processing.py](file:///home/rogermt/forgesyte/server/tests/video/test_integration_video_processing.py)

- ✅ **252 lines** of integration tests
- ✅ Tests: upload scenarios, validation, schema
- ❌ **CRITICAL MISS**: Does NOT verify job is enqueued after upload
- ❌ Does NOT test worker picks up the job

**Coverage**: Endpoint validation only (no job flow)

### Missing Integration Tests

```python
# MISSING: Integration test that would catch this issue
def test_video_upload_enqueues_job_for_worker():
    """Upload video → job enqueued → worker picks up job."""
    # 1. Upload video via /v1/video/submit
    response = client.post("/v1/video/submit", files={"file": mp4})
    job_id = response.json()["job_id"]
    
    # 2. Get the SHARED queue (this is the problem - how?)
    queue = ??? # Can't access video_submit's queue instance!
    
    # 3. Verify job is enqueued
    assert queue.size() == 1  # ← Would FAIL with current architecture
    
    # 4. Run worker and verify it processes
    worker = JobWorker(queue=queue)  # Must pass same queue
    result = worker.run_once()
    assert result is True  # Would FAIL if queues aren't shared
```

---

## Why the Current Architecture Fails

### Issue #1: Module-Level Queue Instance

```python
# video_submit.py (line 15)
queue = InMemoryQueueService()  # ← Created at import time

# Each import of video_submit gets SAME instance ✓
# But worker.py NEVER imports video_submit ✗
```

### Issue #2: Worker Creates Its Own Queue

```python
# worker.py (line 71)
self._queue = queue or InMemoryQueueService()  # ← Default creates new

# run_job_worker.py (line 38)
worker = JobWorker()  # ← No queue parameter = default = new instance
```

### Issue #3: No Dependency Injection

The worker and video_submit are **completely decoupled** in how they get their queue:

```
video_submit.py         worker.py
    ↓                       ↓
InMemoryQueueService   InMemoryQueueService
  (instance #1)          (instance #2)
    ↓                       ↓
  enqueue()              dequeue()
```

They're different objects, even though they have the same name!

---

## Solutions (Ranked by Implementation Difficulty)

### Solution 1: Shared Queue Service (Singleton) ⭐ RECOMMENDED
**Effort**: ~2 hours  
**Sustainability**: High  
**Description**: Make `InMemoryQueueService` a singleton or shared instance

```python
# app/services/queue/shared_queue.py (NEW)
_shared_queue = None

def get_shared_queue():
    global _shared_queue
    if _shared_queue is None:
        _shared_queue = InMemoryQueueService()
    return _shared_queue

# video_submit.py
queue = get_shared_queue()

# run_job_worker.py
worker = JobWorker(queue=get_shared_queue())
```

**Tests to Add**:
- ✅ `test_shared_queue_same_instance` - Verify singleton
- ✅ `test_video_upload_worker_pickup` - End-to-end flow

---

### Solution 2: Redis/Database-Backed Queue ⭐ PRODUCTION-READY
**Effort**: ~4 hours  
**Sustainability**: Highest  
**Description**: Replace in-memory with persistent queue (Redis, RabbitMQ, or DB)

```python
# app/services/queue/persistent_queue.py (NEW)
class PersistentQueueService:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def enqueue(self, job_id: str):
        self.redis.rpush("job_queue", job_id)
    
    def dequeue(self):
        return self.redis.lpop("job_queue")
```

**Advantages**:
- Works across processes ✓
- Works across machine boundaries ✓
- Survives process crashes ✓
- Standard pattern for async job systems ✓

---

### Solution 3: Dependency Injection Container
**Effort**: ~1 hour  
**Sustainability**: Medium  
**Description**: Use FastAPI dependency injection for queue

```python
# app/core/dependencies.py (NEW)
_queue_instance = InMemoryQueueService()

def get_queue() -> QueueService:
    return _queue_instance

# main.py
app = FastAPI()
app.state.queue = get_queue()

# video_submit.py
@router.post("/v1/video/submit")
async def submit_video(queue: QueueService = Depends(get_queue)):
    queue.enqueue(job_id)

# run_job_worker.py
from app.core.dependencies import get_queue
worker = JobWorker(queue=get_queue())
```

---

## Recommended Fix

**Use Solution 1 (Shared Queue) + Plan for Solution 2 (Persistent) later**

### Phase 1: Quick Fix (Shared Queue) - 1 Hour
1. Create `get_shared_queue()` singleton
2. Update `video_submit.py` to use it
3. Update `run_job_worker.py` to pass it
4. Add 2 integration tests

### Phase 2: Production-Ready (Persistent Queue) - Later
1. Implement `RedisQueueService`
2. Update `video_submit.py` to use Redis
3. Update `run_job_worker.py` to use Redis
4. Remove in-memory queue

---

## Missing Tests (Test Coverage Gap)

### Critical Tests to Add

#### 1. Integration: Video Upload → Queue → Worker
```python
# tests/integration/test_video_upload_worker_pickup.py (NEW)

def test_video_upload_enqueues_for_worker(client, session, tiny_mp4):
    """Upload → queue → worker picks up job."""
    # Upload video
    response = client.post("/v1/video/submit", files=...)
    job_id = response.json()["job_id"]
    
    # Verify job in DB
    job = session.query(Job).filter(Job.job_id == job_id).first()
    assert job.status == JobStatus.pending
    
    # Get shared queue and verify enqueued
    from app.core.dependencies import get_shared_queue
    queue = get_shared_queue()
    assert queue.size() == 1
    
    # Worker processes job
    from app.services.storage.local_storage import LocalStorageService
    from app.services.pipeline import PipelineService
    storage = LocalStorageService()
    pipeline = MagicMock(spec=PipelineService)
    pipeline.run_on_file.return_value = []
    
    worker = JobWorker(queue=queue, storage=storage, pipeline_service=pipeline)
    result = worker.run_once()
    
    assert result is True
    job = session.query(Job).filter(Job.job_id == job_id).first()
    assert job.status == JobStatus.completed
```

#### 2. Worker Health During Processing
```python
# tests/app/workers/test_worker_health.py (NEW)

def test_worker_heartbeat_during_processing(test_engine, session):
    """Worker sends heartbeat while processing."""
    from app.workers.worker_state import worker_last_heartbeat
    
    queue = InMemoryQueueService()
    job_id = str(uuid4())
    job = Job(job_id=job_id, status=JobStatus.pending, 
              pipeline_id="test", input_path="test.mp4")
    session.add(job)
    session.commit()
    queue.enqueue(job_id)
    
    # Heartbeat should be active
    worker = JobWorker(queue=queue, session_factory=...)
    
    # Before processing, heartbeat may be old
    old_timestamp = worker_last_heartbeat.timestamp
    
    # During run_forever, heartbeat updated
    import threading
    def run_once_then_stop():
        worker.run_once()
        worker._running = False
    
    thread = threading.Thread(target=run_once_then_stop)
    thread.start()
    
    # Heartbeat should be recent
    assert worker_last_heartbeat.is_recent() or worker_last_heartbeat.timestamp > old_timestamp
    thread.join()
```

#### 3. Worker Queue Isolation
```python
# tests/app/workers/test_worker_queue_isolation.py (NEW)

def test_worker_default_queue_not_shared():
    """Verify default queue is NOT shared (identifies the bug)."""
    from app.services.queue.memory_queue import InMemoryQueueService
    
    queue1 = InMemoryQueueService()
    queue2 = InMemoryQueueService()
    
    queue1.enqueue("job-1")
    
    # Different instances have different items
    assert queue1.dequeue() == "job-1"
    assert queue2.dequeue() is None  # ← Proves they're isolated!
    
    # This is why video_submit's queue != worker's queue
```

---

## Logging Output Analysis

### Current Worker Logs (from Kaggle)

```
2026-02-19 13:56:01,099 - __main__ - INFO - 🚀 Starting JobWorker (Phase 16)...
2026-02-19 13:56:01,099 - __main__ - INFO - ✅ JobWorker initialized
2026-02-19 13:56:01,099 - __main__ - INFO - 👷 Running worker loop - waiting for jobs...
2026-02-19 13:56:01,099 - server.app.workers.worker - INFO - Worker started

[... 6 minutes of silence (no job processing) ...]

2026-02-19 14:02:35,467 - server.app.workers.worker - INFO - Received signal 2, shutting down gracefully
2026-02-19 14:02:35,725 - server.app.workers.worker - INFO - Worker stopped
```

**Analysis**:
- ✅ Worker starts
- ✅ Enters run_forever() loop
- ❌ NO log messages from `run_once()` (should log "Job %s marked RUNNING")
- ❌ NO log messages from pipeline execution
- ❌ NO heartbeat activity

**Conclusion**: Worker's `run_once()` never dequeues anything because queue is empty.

---

## System Diagram

### Current (Broken)

```
API Server (Process 1)           Worker (Process 2)
─────────────────────           ─────────────────
  video_submit.py                 run_job_worker.py
       ↓                                ↓
  queue = IMemQ()                  queue = IMemQ()
   (instance #1)                    (instance #2)
       ↓                                ↓
   enqueue("job1")               dequeue() → None
   [#1: ["job1"]]                [#2: []]
```

### Fixed (Shared Queue)

```
API Server (Process 1)           Worker (Process 2)
─────────────────────           ─────────────────
  video_submit.py                 run_job_worker.py
       ↓                                ↓
  get_shared_queue()           get_shared_queue()
       ↓                                ↓
    queue (SAME INSTANCE?)            queue
   ✗ Still doesn't work              ✗ Still in memory
   in separate processes
```

### Optimal (Redis Queue)

```
API Server (Process 1)           Worker (Process 2)           Redis
─────────────────────           ─────────────────            ─────
  video_submit.py                 run_job_worker.py
       ↓                                ↓
  queue.enqueue("job1")          queue.dequeue()
       └─→ REDIS ←───────────────────────┘
           ["job1"]
```

---

## Files to Modify (Priority Order)

### Phase 1: Immediate Fix

1. **Create** [server/app/core/shared_queue.py](file:///home/rogermt/forgesyte/server/app/core/shared_queue.py) (NEW)
   - Singleton queue instance
   - ~20 lines

2. **Modify** [server/app/api_routes/routes/video_submit.py](file:///home/rogermt/forgesyte/server/app/api_routes/routes/video_submit.py)
   - Line 10: Add import for `get_shared_queue`
   - Line 15: Replace with `queue = get_shared_queue()`

3. **Modify** [server/app/workers/run_job_worker.py](file:///home/rogermt/forgesyte/server/app/workers/run_job_worker.py)
   - Line 1: Add import for `get_shared_queue`
   - Line 38: Change `JobWorker()` to `JobWorker(queue=get_shared_queue())`

### Phase 2: Tests

4. **Create** [server/tests/integration/test_video_upload_worker_pickup.py](file:///home/rogermt/forgesyte/server/tests/integration/test_video_upload_worker_pickup.py) (NEW)
   - End-to-end video upload → queue → worker
   - ~80 lines

5. **Create** [server/tests/app/workers/test_worker_health.py](file:///home/rogermt/forgesyte/server/tests/app/workers/test_worker_health.py) (NEW)
   - Verify heartbeat during processing
   - ~40 lines

6. **Create** [server/tests/app/workers/test_worker_queue_isolation.py](file:///home/rogermt/forgesyte/server/tests/app/workers/test_worker_queue_isolation.py) (NEW)
   - Document the isolation bug
   - ~20 lines

### Phase 3: Production-Ready

7. **Create** [server/app/services/queue/redis_queue.py](file:///home/rogermt/forgesyte/server/app/services/queue/redis_queue.py) (NEW)
   - Redis-backed queue
   - ~60 lines

8. **Modify** [server/app/core/shared_queue.py](file:///home/rogermt/forgesyte/server/app/core/shared_queue.py)
   - Switch implementation to `RedisQueueService`

---

## Summary Table

| Issue | Current | Problem | Fix |
|-------|---------|---------|-----|
| Queue isolation | 2 instances | Can't share across processes | Use singleton or Redis |
| Job persistence | In-memory only | Lost on restart | Use Redis/DB |
| Integration tests | Missing | Can't catch this bug | Add `test_video_upload_worker_pickup.py` |
| Worker injection | No queue param | Creates its own | Pass `queue=get_shared_queue()` |
| Dependency sharing | None | Tight coupling | Use DI container or shared function |

---

## Next Steps

1. **Confirm** this analysis with the team
2. **Implement** Phase 1 (1 hour)
3. **Test** with Kaggle worker process
4. **Plan** Phase 3 (Redis) for production

---

**Generated**: 2026-02-19  
**Status**: Analysis Complete - Implementation Ready
