  
This bundle gives you:

- **A complete Phase‑16 folder structure**  
- **A PR template tailored to the 10‑commit plan**  
- **A Phase‑16 contributor exam**  
- **A Phase‑16 architecture poster**  

Everything is text‑only, deterministic, and aligned with your governance rules.

Let’s build.

---

# ⭐ **PHASE‑16 FOLDER STRUCTURE**  
### *Authoritative directory layout for the entire phase*

```
.ampcode/
└── 04_PHASE_NOTES/
    └── Phase_16/
        ├── 00_OVERVIEW.md
        ├── 01_USER_STORIES.md
        ├── 02_ARCHITECTURE.md
        ├── 03_MIGRATION_GUIDE.md
        ├── 04_ROLLBACK_PLAN.md
        ├── 05_TEST_PLAN.md
        ├── 06_CI_WORKFLOW.md
        ├── 07_RELEASE_NOTES.md
        └── posters/
            └── phase16_architecture_poster.txt

server/
└── app/
    ├── api/
    │   └── routes/
    │       ├── video_submit.py
    │       ├── video_status.py
    │       └── video_results.py
    │
    ├── services/
    │   ├── storage/
    │   │   ├── base.py
    │   │   └── local_storage.py
    │   │
    │   ├── queue/
    │   │   ├── base.py
    │   │   └── in_memory_queue.py
    │   │
    │   └── worker/
    │       ├── worker_loop.py
    │       └── worker_runner.py
    │
    ├── models/
    │   └── job.py
    │
    ├── migrations/
    │   └── 000X_create_job_table.py
    │
    └── tests/
        └── video_jobs/
            ├── test_submit_job.py
            ├── test_job_status.py
            ├── test_job_results.py
            ├── test_worker_state_transitions.py
            ├── test_worker_pipeline_execution.py
            ├── fixtures/
            │   ├── tiny.mp4
            │   ├── make_tiny_mp4.py
            │   └── make_corrupt_mp4.py
            └── conftest.py
```

This structure enforces:

- **Separation of concerns**  
- **Governance boundaries**  
- **Test isolation**  
- **Deterministic behavior**  

---

# ⭐ **PHASE‑16 PR TEMPLATE**  
### *Drop into `.github/pull_request_template.md`*

```
# Phase‑16 Pull Request

## Summary
Describe the purpose of this PR and which Phase‑16 story it implements.

**Story Number:** Commit X of 10  
**Story Title:** <paste from user stories>

---

## Changes
- [ ] Job model / migration
- [ ] StorageService implementation
- [ ] QueueService implementation
- [ ] /video/submit endpoint
- [ ] Worker loop
- [ ] /video/status/{job_id}
- [ ] /video/results/{job_id}
- [ ] Tests (unit / integration / worker)
- [ ] Governance updates
- [ ] Documentation updates

---

## Validation Checklist

### Governance
- [ ] No Phase‑17 concepts (streaming, websockets, GPU scheduling)
- [ ] No forbidden vocabulary
- [ ] No phase‑named files outside `.ampcode/` or `scripts/`

### API
- [ ] /video/submit returns `{job_id}`
- [ ] /video/status returns `{job_id, status, progress}`
- [ ] /video/results returns `{job_id, results}`

### Worker
- [ ] Worker marks job pending → running → completed/failed
- [ ] Worker handles corrupted MP4 safely
- [ ] Worker stores results deterministically

### Tests
- [ ] Unit tests added
- [ ] Integration tests added
- [ ] Worker tests added
- [ ] All tests pass locally

---

## Screenshots / Logs (optional)

---

## Notes for Reviewer
Add any context needed for review.
```

---

# ⭐ **PHASE‑16 CONTRIBUTOR EXAM**  
### *20 questions — must pass before contributing to Phase‑16*

---

## **Section A — Architecture (6 questions)**

1. What are the three new subsystems introduced in Phase‑16?  
2. Why must job submission be asynchronous?  
3. Why must the worker process be separate from the API process?  
4. What is the purpose of the job table?  
5. Why must the queue payload contain only `job_id`?  
6. Why must the worker use the Phase‑15 VideoFilePipelineService?

---

## **Section B — Job Lifecycle (6 questions)**

7. What are the four valid job statuses?  
8. What triggers the transition from pending → running?  
9. What triggers the transition from running → completed?  
10. What triggers the transition from running → failed?  
11. What happens if the worker crashes mid‑job?  
12. Why must results be stored in object storage instead of memory?

---

## **Section C — API Behavior (4 questions)**

13. What does `POST /video/submit` return?  
14. When does `GET /video/status/{job_id}` return 404?  
15. When does `GET /video/results/{job_id}` return 404?  
16. Why must progress be coarse (0, 0.5, 1.0)?

---

## **Section D — Governance & Testing (4 questions)**

17. Name two Phase‑17 concepts forbidden in Phase‑16.  
18. Why must the worker tests use a mock queue?  
19. Why must integration tests simulate a full job lifecycle?  
20. Why must the rollback plan remove the job table?

---

If you want, I can generate the **answer key** too.

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

---

Here we go, Roger — the **Phase‑16 deep pack**: answers, state machine, clean interfaces, and a concrete worker implementation.

---

### Phase‑16 contributor exam — answer key

**1. What are the three new subsystems introduced in Phase‑16?**  
Job queue, job table (persistence), worker process.

**2. Why must job submission be asynchronous?**  
Because processing can be long‑running; we can’t block HTTP requests and must decouple client from execution time.

**3. Why must the worker process be separate from the API process?**  
To avoid blocking, allow independent scaling, and prevent heavy workloads from impacting API latency.

**4. What is the purpose of the job table?**  
To persist job state (status, paths, errors) across restarts and allow status/results queries.

**5. Why must the queue payload contain only `job_id`?**  
To keep messages small, deterministic, and avoid duplicating state that already lives in the DB.

**6. Why must the worker use the Phase‑15 VideoFilePipelineService?**  
To reuse the existing, tested batch pipeline and avoid duplicating business logic.

**7. What are the four valid job statuses?**  
`pending`, `running`, `completed`, `failed`.

**8. What triggers the transition from pending → running?**  
The worker dequeues the job and starts processing it.

**9. What triggers the transition from running → completed?**  
The worker finishes processing successfully and stores results.

**10. What triggers the transition from running → failed?**  
The worker encounters an unrecoverable error and records `error_message`.

**11. What happens if the worker crashes mid‑job?**  
The job remains `pending` or `running` (depending on when it crashed) and can be retried or inspected; no status is silently changed.

**12. Why must results be stored in object storage instead of memory?**  
To survive process restarts, support large payloads, and decouple storage from worker memory.

**13. What does `POST /video/submit` return?**  
A JSON object containing `{ "job_id": "<uuid>" }`.

**14. When does `GET /video/status/{job_id}` return 404?**  
When the job_id does not exist in the job table.

**15. When does `GET /video/results/{job_id}` return 404?**  
When the job_id does not exist, or the job is not yet `completed`.

**16. Why must progress be coarse (0, 0.5, 1.0)?**  
To avoid frame‑level tracking complexity and keep Phase‑16 simple and deterministic.

**17. Name two Phase‑17 concepts forbidden in Phase‑16.**  
WebSockets, real‑time streaming, GPU scheduling, distributed workers (any two).

**18. Why must the worker tests use a mock queue?**  
To make tests deterministic, fast, and independent of real queue infrastructure.

**19. Why must integration tests simulate a full job lifecycle?**  
To verify that submit → worker → status → results all work together as designed.

**20. Why must the rollback plan remove the job table?**  
Because Phase‑16 introduces it; rollback must restore a pure Phase‑15 state with no leftover schema.

---

### Phase‑16 worker state machine diagram

```text
────────────────────────────────────────
        PHASE‑16 WORKER STATE MACHINE
────────────────────────────────────────

States:
  PENDING   → job created, not yet picked up
  RUNNING   → worker is processing
  COMPLETED → worker finished successfully
  FAILED    → worker encountered unrecoverable error

Transitions:

  (submit job)
      └─> PENDING

  (worker dequeues job_id)
      PENDING ──> RUNNING

  (pipeline succeeds)
      RUNNING ──> COMPLETED

  (pipeline fails)
      RUNNING ──> FAILED

  (worker crash)
      PENDING or RUNNING remain unchanged
      (external recovery / retry policy decides next step)
```

---

### Phase‑16 storage + queue adapter interfaces

You can drop these into `server/app/services/storage/base.py` and `server/app/services/queue/base.py`.

**`storage/base.py`**

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO


class StorageService(ABC):
    """Abstract storage interface for Phase‑16 job files."""

    @abstractmethod
    def save_file(self, src: BinaryIO, dest_path: str) -> str:
        """Save a file-like object to storage. Returns the stored path."""
        raise NotImplementedError

    @abstractmethod
    def load_file(self, path: str) -> Path:
        """Return a local filesystem path to the stored file."""
        raise NotImplementedError

    @abstractmethod
    def delete_file(self, path: str) -> None:
        """Delete a stored file, if it exists."""
        raise NotImplementedError
```

**`queue/base.py`**

```python
from abc import ABC, abstractmethod
from typing import Optional


class QueueService(ABC):
    """Abstract queue interface for Phase‑16 job dispatch."""

    @abstractmethod
    def enqueue(self, job_id: str) -> None:
        """Push a job_id onto the queue."""
        raise NotImplementedError

    @abstractmethod
    def dequeue(self) -> Optional[str]:
        """Pop the next job_id from the queue, or None if empty."""
        raise NotImplementedError

    @abstractmethod
    def size(self) -> int:
        """Return the approximate number of items in the queue."""
        raise NotImplementedError
```

---

### Phase‑16 example worker implementation

A minimal, deterministic worker loop using those interfaces and the Phase‑15 service.

```python
"""
Phase‑16 worker loop.

Pulls job_ids from QueueService, loads job metadata,
runs VideoFilePipelineService, and updates job status.
"""

from typing import Optional
from pathlib import Path

from server.app.services.queue.base import QueueService
from server.app.services.storage.base import StorageService
from server.app.models.job import Job, JobStatus
from server.app.services.video.video_file_pipeline_service import VideoFilePipelineService


class JobWorker:
    def __init__(
        self,
        queue: QueueService,
        storage: StorageService,
        pipeline_service: VideoFilePipelineService,
    ) -> None:
        self._queue = queue
        self._storage = storage
        self._pipeline_service = pipeline_service

    def _load_job(self, job_id: str) -> Optional[Job]:
        return Job.get(job_id)  # however your ORM fetches by PK

    def _mark_status(self, job: Job, status: JobStatus, error_message: str | None = None) -> None:
        job.status = status
        if error_message is not None:
            job.error_message = error_message
        job.save()

    def run_once(self) -> bool:
        """Process a single job if available. Returns True if a job was processed."""
        job_id = self._queue.dequeue()
        if job_id is None:
            return False

        job = self._load_job(job_id)
        if job is None:
            # Job not found; nothing to do
            return False

        self._mark_status(job, JobStatus.RUNNING)

        try:
            input_path = self._storage.load_file(job.input_path)
            results = self._pipeline_service.run_on_file(
                pipeline_id="yolo_ocr",  # or job.pipeline_id if you add it
                file_path=Path(input_path),
            )

            # Save results (e.g., JSON) via storage
            output_path = f"video_jobs/{job.job_id}_results.json"
            self._storage.save_file(
                src=self._results_to_bytes(results),
                dest_path=output_path,
            )

            job.output_path = output_path
            self._mark_status(job, JobStatus.COMPLETED)

        except Exception as exc:  # noqa: BLE001
            self._mark_status(job, JobStatus.FAILED, error_message=str(exc))

        return True

    def run_forever(self) -> None:
        """Simple loop; in production you’d add sleep/backoff."""
        while True:
            processed = self.run_once()
            if not processed:
                break  # or sleep/backoff

    @staticmethod
    def _results_to_bytes(results) -> bytes:
        import json

        return json.dumps({"results": results}).encode("utf-8")
```

This worker:

- Uses the Phase‑15 `VideoFilePipelineService`  
- Reads from `QueueService`  
- Reads/writes via `StorageService`  
- Updates `Job` status deterministically  
- Produces a `results` JSON compatible with your existing schema  

