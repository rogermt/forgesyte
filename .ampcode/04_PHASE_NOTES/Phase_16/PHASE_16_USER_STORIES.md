# ⭐ **PHASE‑16 USER STORIES (10 COMMITS)**  
### *Asynchronous Job Queue + Persistent Job State + Worker Execution*

Each story is atomic, testable, and maps to a single commit.

---

## **Story 1 — Job Model + DB Migration**  
**Commit 1 of 10**

**Story:**  
As a backend engineer, I want a persistent job table so that job submissions can be tracked across restarts.

**Acceptance Criteria:**  
- `job` table exists with fields:  
  - `job_id` (UUID, PK)  
  - `status` (pending/running/completed/failed)  
  - `created_at`, `updated_at`  
  - `input_path`, `output_path`  
  - `error_message` (nullable)  
- Migration script created  
- ORM model created  
- No worker logic yet  
- No queue logic yet  

---

## **Story 2 — Object Storage Adapter**  
**Commit 2 of 10**

**Story:**  
As a contributor, I want a storage abstraction so that MP4 files can be saved and retrieved independently of local disk.

**Acceptance Criteria:**  
- `StorageService` interface created  
- Local filesystem implementation created  
- Methods: `save_file()`, `load_file()`, `delete_file()`  
- Deterministic paths: `video_jobs/{job_id}.mp4`  
- Unit tests with temp directories  

---

## **Story 3 — Queue Adapter**  
**Commit 3 of 10**

**Story:**  
As a contributor, I want a queue abstraction so that job IDs can be pushed and popped without binding to a specific backend.

**Acceptance Criteria:**  
- `QueueService` interface created  
- In‑memory implementation created (for dev/test)  
- Methods: `enqueue(job_id)`, `dequeue()`, `size()`  
- No Redis/RabbitMQ yet  
- Unit tests included  

---

## **Story 4 — Job Submission Endpoint**  
**Commit 4 of 10**

**Story:**  
As an API consumer, I want to submit a video for processing and receive a job_id.

**Acceptance Criteria:**  
- `POST /video/submit` implemented  
- Validates MP4  
- Saves file via StorageService  
- Creates job row in DB  
- Pushes job_id to queue  
- Returns `{job_id}`  
- Integration tests included  

---

## **Story 5 — Worker Skeleton**  
**Commit 5 of 10**

**Story:**  
As a worker engineer, I want a worker loop that pulls job IDs and marks jobs as running.

**Acceptance Criteria:**  
- Worker process created  
- Pulls job_id from queue  
- Loads job row  
- Marks job as `running`  
- Logs transitions  
- No pipeline execution yet  
- Unit tests with mock queue + mock DB  

---

## **Story 6 — Worker Executes Phase‑15 Pipeline**  
**Commit 6 of 10**

**Story:**  
As a worker engineer, I want the worker to run the Phase‑15 VideoFilePipelineService on the submitted MP4.

**Acceptance Criteria:**  
- Worker loads MP4 via StorageService  
- Runs VideoFilePipelineService  
- Stores results via StorageService  
- Updates job row: `completed`  
- On exception: `failed` + error_message  
- Integration tests included  

---

## **Story 7 — Job Status Endpoint**  
**Commit 7 of 10**

**Story:**  
As an API consumer, I want to check the status of a job.

**Acceptance Criteria:**  
- `GET /video/status/{job_id}` implemented  
- Returns `{job_id, status, progress}`  
- Progress = 0, 0.5, or 1.0 (coarse only)  
- No frame‑level progress  
- Integration tests included  

---

## **Story 8 — Job Results Endpoint**  
**Commit 8 of 10**

**Story:**  
As an API consumer, I want to retrieve results once the job is completed.

**Acceptance Criteria:**  
- `GET /video/results/{job_id}` implemented  
- Returns `{job_id, results}`  
- 404 if job not completed  
- Integration tests included  

---

## **Story 9 — Governance + CI Enforcement**  
**Commit 9 of 10**

**Story:**  
As a release manager, I want governance rules preventing Phase‑17 concepts.

**Acceptance Criteria:**  
- Forbidden vocabulary updated  
- Path validator updated  
- CI workflow updated  
- Smoke test updated  
- No streaming, no WebSockets, no GPU scheduling  

---


## **Story 10 — Documentation + Rollback Plan**  
**Commit 10 of 10**

**Story:**  
As a new contributor, I want complete Phase‑16 documentation.

**Acceptance Criteria:**  
- Overview, Scope, Architecture, Migration Guide  
- Rollback plan  
- Testing guide  
- Release notes  
- Onboarding guide  

---



  

