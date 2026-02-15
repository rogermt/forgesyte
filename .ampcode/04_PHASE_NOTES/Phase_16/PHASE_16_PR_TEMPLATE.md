

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

