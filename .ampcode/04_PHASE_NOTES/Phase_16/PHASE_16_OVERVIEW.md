
# ⭐ **PHASE 16 — OVERVIEW**  
### *Asynchronous Job Queue + Persistent Job State + Worker Execution*

Phase‑16 introduces the **first stateful subsystem** in the video‑processing pipeline.  
Unlike Phase‑15 (pure batch, stateless, synchronous), Phase‑16 adds:

- A **job queue**  
- A **persistent job table**  
- A **worker process**  
- A **job status API**  
- A **job result retrieval API**

This phase transforms the system from “upload MP4 → get results immediately” into:

1. **Submit job**  
2. **Receive job_id**  
3. **Poll job status**  
4. **Retrieve results when ready**

This is the foundation for large videos, long‑running pipelines, and distributed processing.

---

# ⭐ **PHASE 16 — ARCHITECTURE (TEXT‑ONLY DIAGRAM)**

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

# ⭐ **PHASE 16 — SCOPE**

### **In‑scope**
- Job queue (Redis, RabbitMQ, or in‑memory for dev)
- Job table (SQLite/Postgres)
- Worker process
- Job submission endpoint
- Job status endpoint
- Job results endpoint
- Object storage for MP4 files
- Retry logic
- Dead‑letter queue (optional)

### **Out‑of‑scope**
- Real‑time streaming  
- WebSockets  
- Progress bars with frame‑level granularity  
- Distributed workers  
- GPU scheduling  
- Multi‑pipeline orchestration  

---

# ⭐ **PHASE 16 — DATA MODEL**

### **Job Table**
```
job_id: UUID (PK)
status: enum("pending", "running", "failed", "completed")
created_at: timestamp
updated_at: timestamp
input_path: string (object store path)
output_path: string (object store path)
error_message: string (nullable)
```

### **Queue Payload**
```
{ "job_id": "<uuid>" }
```

### **Status Response**
```
{
  "job_id": "...",
  "status": "running",
  "progress": 0.42
}
```

### **Results Response**
```
{
  "job_id": "...",
  "results": [...]
}
```

---

# ⭐ **PHASE 16 — ENDPOINTS**

### **POST /video/submit**
- Accepts MP4 upload  
- Stores file  
- Creates job row  
- Pushes job_id to queue  
- Returns `{job_id}`  

### **GET /video/status/{job_id}**
- Returns job status  
- Returns progress (optional)  

### **GET /video/results/{job_id}**
- Returns final results  
- 404 if job not completed  

---

# ⭐ **PHASE 16 — WORKER LIFECYCLE**

```
loop:
    job_id = queue.pop()
    mark job as running
    load MP4 from object store
    run VideoFilePipelineService
    store results
    mark job as completed
```

Error handling:

- On failure → mark job as failed  
- On worker crash → job stays pending  
- On repeated failure → move to dead‑letter queue  

---

# ⭐ **PHASE 16 — TEST STRATEGY**

### **Unit Tests**
- Job model  
- Queue adapter  
- Worker logic (mocking pipeline service)  
- Status/result endpoints  

### **Integration Tests**
- Submit job → job row created  
- Worker processes job → results stored  
- Status transitions: pending → running → completed  
- Failed job behavior  

### **System Tests**
- Full end‑to‑end job lifecycle  
- Queue + DB + worker + API  

---

# ⭐ **PHASE 16 — GOVERNANCE RULES**

### **Forbidden in Phase‑16**
- Frame‑level progress reporting  
- Real‑time streaming  
- WebSockets  
- GPU scheduling  
- Distributed workers  
- Multi‑pipeline DAG orchestration  

### **Required**
- Deterministic queue payload  
- Deterministic job state transitions  
- No schema drift  
- No Phase‑17 concepts  

---

# ⭐ **PHASE 16 — DEFINITION OF DONE**

- All endpoints implemented  
- Worker runs end‑to‑end  
- Queue + DB + object store integrated  
- Full test suite passes  
- Governance validator updated  
- Smoke test updated  
- Rollback plan written  
- Architecture diagrams updated  
- Release notes updated  

---
