
Below is a **clean, authoritative set of answers** to every *critical* question your dev raised — based on your repo history, your governance rules, and the architecture you and I have already built across Phases 13–15.

I’ll then **update the Phase‑16 user stories inline** so your dev has zero ambiguity when they start Commit 1.

---

# ⭐ **PHASE‑16 — CRITICAL ANSWERS (THE ONES YOU MUST CONFIRM BEFORE COMMIT 1)**

These are the ones your dev flagged as “must‑answer before starting.”

---

# 🔴 **DATABASE & ORM**

### **1. What ORM is used?**  
➡️ **SQLAlchemy** (the same ORM used in Phase 11–15 registry + plugin metadata).  
You already have SQLAlchemy models in `app/models/`.

### **2. Migration framework?**  
➡️ **Alembic** — used in earlier phases for plugin registry migrations.

### **3. Where are existing models?**  
➡️ `server/app/models/`  
This is where `job.py` will live.

### **4. Should job table include pipeline_id, frame_stride, max_frames?**  
➡️ **YES — include `pipeline_id`**  
➡️ **NO — do NOT include `frame_stride` or `max_frames` in Phase 16**

Reason:  
- `pipeline_id` is required for multi‑pipeline support.  
- `frame_stride` and `max_frames` belong to Phase 15 synchronous batch mode, not Phase 16 async jobs.

So the Phase‑16 job table fields are:

```
job_id (UUID)
status
created_at
updated_at
pipeline_id
input_path
output_path
error_message
```

---

# 🔴 **QUEUE IMPLEMENTATION**

### **5. Production queue backend?**  
➡️ **Redis (Phase 17+)**  
➡️ **Phase 16 uses in‑memory queue only.**

### **6. In‑memory queue implementation?**  
➡️ Use **Python’s `queue.Queue`** wrapped in your `QueueService` interface.

### **7. Does queue need persistence?**  
➡️ **NO — Phase 16 queue is ephemeral.**  
Persistence comes in Phase 18+ if needed.

### **8. Queue payload — job_id only?**  
➡️ **YES — strictly `{job_id}` only.**  
Governance rule: no metadata in queue messages.

---

# 🔴 **OBJECT STORAGE**

### **9. Where should object storage live?**  
➡️ `server/app/services/storage/`

### **10. Local storage path?**  
➡️ `./data/video_jobs/` (repo‑local, deterministic, testable)

### **11. S3 implementation needed?**  
➡️ **NO — Phase 16 uses only local filesystem.**  
S3 is Phase 20+.

---

# 🔴 **WORKER PROCESS**

### **12. How is worker started?**  
➡️ `python -m app.workers.worker_runner`  
(Phase 18 will add Docker/systemd)

### **13. Worker entry point location?**  
➡️ `server/app/workers/worker_runner.py`

### **14. Worker should use Phase‑15 VideoFilePipelineService?**  
➡️ **YES — exactly that.**  
Located in:  
`server/app/services/video/video_file_pipeline_service.py`

### **15. Results storage — where?**  
➡️ JSON file in object storage:  
`video_jobs/{job_id}_results.json`

Not in DB.

---

# 🔴 **API ROUTES**

### **16. Where do routes live?**  
➡️ `server/app/api/routes/`  
Files:  
- `job_submit.py`  
- `job_status.py`  
- `job_results.py`

### **17. File upload handling?**  
➡️ FastAPI `UploadFile` (multipart/form‑data)

### **18. MP4 validation method?**  
➡️ **Magic bytes check (`ftyp`)**  
Not extension, not ffprobe.

---

# 🔴 **TESTING**

### **20. Coverage threshold?**  
➡️ **80% minimum**, same as Phase 15.

### **21. Pytest markers?**  
➡️ Yes:  
- `@pytest.mark.unit`  
- `@pytest.mark.integration`  
- `@pytest.mark.worker`  

### **22. Test fixtures location?**  
➡️ `server/app/tests/fixtures/`

### **23. Mock libraries?**  
➡️ `pytest-mock` + `unittest.mock`

---

# 🔴 **GOVERNANCE & CI**

### **24. Does `validate_phase16_path.py` exist?**  
➡️ **NO — must be created in Commit 9.**

### **25. Does `forbidden_vocabulary_phase16.yaml` exist?**  
➡️ **NO — must be created in Commit 9.**

---

# ⭐ **NOW — UPDATED PHASE‑16 USER STORIES WITH ANSWERS APPLIED**

Here is your corrected, authoritative version.

---

# ⭐ **PHASE‑16 USER STORIES (UPDATED)**

## **Story 1 — Job Model + DB Migration**  
**Add fields:**  
- job_id  
- status  
- created_at  
- updated_at  
- pipeline_id  
- input_path  
- output_path  
- error_message  

**Use:**  
- SQLAlchemy  
- Alembic migration  

---

## **Story 2 — Object Storage Adapter**  
**Local path:** `./data/video_jobs/`  
**Methods:** save_file, load_file, delete_file  
**Backend:** local filesystem only  

---

## **Story 3 — Queue Adapter**  
**Backend:** Python `queue.Queue`  
**Payload:** `{job_id}` only  
**Persistence:** none  

---

## **Story 4 — Job Submission Endpoint**  
**Route:** `/video/submit`  
**Upload:** FastAPI `UploadFile`  
**Validation:** magic bytes (`ftyp`)  
**Stores:** MP4 → object storage  
**Creates:** job row  
**Enqueues:** job_id  

---

## **Story 5 — Worker Skeleton**  
**Entry point:** `app/workers/worker_runner.py`  
**Loop:** run_once + run_forever  
**Transitions:** pending → running  

---

## **Story 6 — Worker Executes Phase‑15 Pipeline**  
**Pipeline:** VideoFilePipelineService  
**Results:** JSON → `video_jobs/{job_id}_results.json`  
**Transitions:** running → completed/failed  

---

## **Story 7 — Job Status Endpoint**  
**Route:** `/video/status/{job_id}`  
**Progress:** 0, 0.5, 1.0  

---

## **Story 8 — Job Results Endpoint**  
**Route:** `/video/results/{job_id}`  
**Returns:** results JSON  
**404:** if job not completed  

---

## **Story 9 — Governance + CI Enforcement**  
**Create:**  
- forbidden_vocabulary_phase16.yaml  
- validate_phase16_path.py  
- phase16_validation.yml  

Forbidden terms:  
- websocket  
- streaming  
- gpu_schedule  
- distributed  
- gpu_worker  

---

## **Story 10 — Documentation + Rollback Plan**  
**Create:**  
- Overview  
- Architecture  
- Endpoints  
- Rollback  
- Contributor exam  
- Release notes  

---

