# ⭐ PHASE 15 — BOUNDARIES & GAPS

**Where Phase 14 Stops, Phase 15 Begins**

This document defines the exact boundary between Phase 14 and Phase 15 to prevent scope creep and ensure clean phase separation.

---

## Phase 14 Scope (What's IN)

✅ **DAG Pipeline Definition**
- Graph structure (nodes, edges)
- Validation (cycles, types, structure)
- Registry (load from JSON)

✅ **Single-Frame Execution**
- Execute pipeline once
- Return output once
- No state persistence

✅ **REST API**
- POST /pipelines/{id}/run
- GET /pipelines/list
- GET /pipelines/{id}/info

✅ **WebSocket Frame Handler**
- Accept frame, run pipeline, return result
- One frame → one result

✅ **Type Validation**
- Input/output type compatibility
- Prevent mismatched connections

✅ **Tool Metadata**
- input_types, output_types
- capabilities, handler info

---

## Phase 15 Scope (What's OUT of Phase 14)

❌ **Job Queuing** ← PHASE 15
- Multiple pipelines queued
- Async execution tracking
- Job status polling
- Job persistence

❌ **Job Persistence** ← PHASE 15
- Store jobs in database
- Retrieve job history
- Job metadata

❌ **Streaming Execution** ← PHASE 15
- Process video stream frame-by-frame
- Maintain state across frames
- Track object IDs across frames
- Accumulate results

❌ **Pipeline History** ← PHASE 15
- Record all pipeline executions
- Search execution history
- Performance metrics per pipeline

❌ **Performance Metrics** ← PHASE 15
- Execution time per node
- Throughput tracking
- Bottleneck detection

❌ **Pipeline Versioning** ← PHASE 15
- Multiple versions of same pipeline
- Version selection in requests
- Version history

---

## Critical Phase 14 Boundaries

### 1. No Streaming

❌ **WRONG** (Phase 15):
```python
async def stream_pipeline(pipeline_id, video_file):
    """Process entire video, accumulate results."""
    results = []
    for frame in video_file:
        results.append(await run_pipeline(pipeline_id, frame))
    return results
```

✅ **RIGHT** (Phase 14):
```python
async def run_pipeline(pipeline_id, frame):
    """Process single frame, return result."""
    return await service.execute(pipeline, frame)
```

**Why**: Streaming requires job queuing, state management, persistence.

---

### 2. No Job Tracking

❌ **WRONG** (Phase 15):
```python
# REST: Execute and poll for result
POST /pipelines/run → returns job_id
GET /jobs/{job_id} → returns status
```

✅ **RIGHT** (Phase 14):
```python
# REST: Execute synchronously, return result immediately
POST /pipelines/run → returns result directly
```

**Why**: Job tracking requires async backend, database, job manager.

---

### 3. No State Between Frames

❌ **WRONG** (Phase 15):
```python
class PipelineExecutor:
    def __init__(self, pipeline_id):
        self.state = {}  # ❌ Persisted state
        
    async def process_frame(self, frame):
        # Use self.state for tracking
        self.state["previous_detections"] = ...
```

✅ **RIGHT** (Phase 14):
```python
async def execute_pipeline(pipeline, frame):
    # Stateless execution
    # Each call is independent
    return result
```

**Why**: State persistence requires session management, database.

---

### 4. No Database Writes

❌ **WRONG** (Phase 15):
```python
# Store every execution
await db.jobs.insert_one({
    "pipeline_id": pipeline_id,
    "timestamp": now(),
    "result": result
})
```

✅ **RIGHT** (Phase 14):
```python
# Just log and return
logger.info(f"Pipeline {pipeline_id} executed")
return result
```

**Why**: Database writes require schema, migrations, persistence layer.

---

### 5. No Async Job Queue

❌ **WRONG** (Phase 15):
```python
# Queue jobs for background processing
job = await job_manager.submit(pipeline_id, frame)
return {"job_id": job.id}  # Don't wait for result
```

✅ **RIGHT** (Phase 14):
```python
# Execute immediately, return result
result = await service.execute(pipeline, frame)
return result  # Synchronous response
```

**Why**: Job queues require: async workers, job manager, Redis/RabbitMQ.

---

### 6. No Frame Accumulation

❌ **WRONG** (Phase 15):
```python
results = []
for frame in video:
    result = await execute_pipeline(pipeline, frame)
    results.append(result)
return results
```

✅ **RIGHT** (Phase 14):
```python
# Single frame at a time
result = await execute_pipeline(pipeline, frame)
return result
```

**Why**: Accumulation requires streaming architecture, state management.

---

## Exact API Boundary

### Phase 14 REST Endpoints

```
GET  /pipelines/list
     └─ Returns: { pipelines: [...] }

GET  /pipelines/{id}/info
     └─ Returns: { id, name, nodes, edges, ... }

POST /pipelines/{id}/run
     ├─ Input:  { image: "...", options: {...} }
     └─ Returns: { status: "success", output: {...}, execution_time_ms: 425 }

POST /pipelines/validate
     ├─ Input:  { nodes: [...], edges: [...], ... }
     └─ Returns: { valid: true/false, errors: [...] }
```

**What's NOT in Phase 14**:
- GET /jobs/{job_id} ← PHASE 15
- GET /jobs/list ← PHASE 15
- POST /jobs/{job_id}/cancel ← PHASE 15
- GET /pipelines/{id}/history ← PHASE 15
- GET /pipelines/{id}/metrics ← PHASE 15

---

## Exact WebSocket Boundary

### Phase 14 WebSocket Messages

**Send** (from client):
```json
{
  "type": "frame",
  "pipeline_id": "player_tracking_v1",
  "frame_id": "frame_001",
  "image": "base64_data"
}
```

**Receive** (from server):
```json
{
  "type": "result",
  "frame_id": "frame_001",
  "status": "success",
  "output": {...},
  "execution_time_ms": 425
}
```

**What's NOT in Phase 14**:
- Job status updates ← PHASE 15
- Stream start/stop messages ← PHASE 15
- Accumulated results ← PHASE 15
- State checkpoint messages ← PHASE 15

---

## Data Model Boundaries

### Phase 14 Models

```python
class Pipeline(BaseModel):
    id: str
    name: str
    nodes: List[PipelineNode]
    edges: List[PipelineEdge]
    entry_nodes: List[str]
    output_nodes: List[str]

class PipelineExecutionResult(BaseModel):
    status: str
    output: Dict
    execution_time_ms: float
    node_logs: List[Dict]
```

**What's NOT in Phase 14**:
```python
class Job(BaseModel):  # ← PHASE 15
    job_id: str
    pipeline_id: str
    status: str
    submitted_at: datetime
    completed_at: Optional[datetime]
    result: Optional[Dict]
    error: Optional[str]

class PipelineMetrics(BaseModel):  # ← PHASE 15
    pipeline_id: str
    execution_count: int
    average_time_ms: float
    slowest_node_id: str
```

---

## Configuration Boundaries

### Phase 14 Configuration

```python
# app/config.py
PIPELINES_DIR = "app/pipelines"  # Where pipeline JSON lives
MAX_PIPELINE_NODES = 100
MAX_EXECUTION_TIME_MS = 60000
```

**What's NOT in Phase 14**:
```python
# ← PHASE 15
JOB_QUEUE_URL = "redis://localhost:6379"
DB_CONNECTION_STRING = "postgresql://..."
JOB_RETENTION_DAYS = 30
MAX_CONCURRENT_JOBS = 10
```

---

## Testing Boundaries

### Phase 14 Tests

```python
# tests/pipelines/test_pipeline_execution.py
async def test_single_frame_execution():
    """Execute pipeline once, get result."""
    
# tests/pipelines/test_pipeline_validation.py
def test_rejects_cycles():
    """Validate pipeline structure."""
    
# tests/pipelines/test_pipeline_endpoints.py
async def test_rest_run_endpoint():
    """POST /pipelines/{id}/run works."""
```

**What's NOT in Phase 14**:
```python
# ← PHASE 15
async def test_job_queue():
    """Jobs can be queued and polled."""
    
async def test_streaming_execution():
    """Video stream is processed frame by frame."""
    
async def test_pipeline_metrics():
    """Performance metrics are tracked."""
```

---

## Feature Checklist: What Stays OUT

| Feature | Phase | Status |
|---------|-------|--------|
| Single frame execution | 14 | ✅ IN |
| DAG validation | 14 | ✅ IN |
| Type checking | 14 | ✅ IN |
| REST API | 14 | ✅ IN |
| WebSocket support | 14 | ✅ IN |
| **Job queuing** | **15** | ❌ OUT |
| **Async execution** | **15** | ❌ OUT |
| **Job persistence** | **15** | ❌ OUT |
| **Video streaming** | **15** | ❌ OUT |
| **State management** | **15** | ❌ OUT |
| **Performance metrics** | **15** | ❌ OUT |
| **Pipeline history** | **15** | ❌ OUT |
| **Pipeline versioning** | **15** | ❌ OUT |

---

## The Clean Handoff

### Phase 14 Guarantees

✅ Single pipeline execution works  
✅ Multiple frames can be sent sequentially  
✅ Each frame gets independent result  
✅ No frame affects another  
✅ Stateless execution  

### What Phase 15 Will Add

➕ Queue multiple frames  
➕ Track job progress  
➕ Persist results  
➕ Accumulate across frames  
➕ Performance analytics  

### The Boundary

**Phase 14 = Single Frame**  
**Phase 15 = Multiple Frames with State**

---

## Why This Boundary?

### Phase 14 Complexity
- DAG validation: **HARD**
- Cross-plugin execution: **HARD**
- Type checking: **MEDIUM**
- Single frame execution: **EASY**

### Phase 15 Complexity
- Job queuing: **HARD**
- State management: **HARD**
- Persistence: **MEDIUM**
- Streaming: **EASY** (once Phase 14 works)

**Decision**: Keep Phase 14 focused on pipeline mechanics, let Phase 15 handle scaling.

---

## Phase 14 Definition of Done

✅ One frame → One result (guaranteed)  
✅ Multiple frames work sequentially (each independent)  
✅ Validate before execute (always)  
✅ Type contracts enforced (always)  
✅ REST API functional (always)  
✅ WebSocket support works (always)  
✅ 85%+ test coverage (always)  
✅ Zero state across calls (always)  

**NOT** in Definition of Done:
- Queuing systems
- Persistence layers
- Streaming architectures
- State tracking
- Performance metrics

---

## Red Flags for Scope Creep

If you see these during Phase 14, they belong in Phase 15:

🚨 "We need to store job results" → PHASE 15  
🚨 "We need to track job status" → PHASE 15  
🚨 "We need to process video streams" → PHASE 15  
🚨 "We need to track state between frames" → PHASE 15  
🚨 "We need async job workers" → PHASE 15  
🚨 "We need performance metrics" → PHASE 15  
🚨 "We need to accumulate results" → PHASE 15  

If someone suggests one of these: **"That's Phase 15. Phase 14 is single-frame only."**

---

## Summary

**Phase 14**: Transform single-plugin to multi-plugin DAG execution  
**Phase 15**: Transform single-frame to multi-frame with state/queuing

**The boundary is clear**: Frame-level execution vs. Job-level management

**No ambiguity**: If it requires queuing, persistence, or state → Phase 15
