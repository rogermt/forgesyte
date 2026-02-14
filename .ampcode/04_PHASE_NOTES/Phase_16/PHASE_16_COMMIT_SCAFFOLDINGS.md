here is the **full Phase‑16 Commit 2–6 scaffolding pack**, rewritten cleanly, with no tool references, no file creation, and no code execution.  
This is pure architectural + implementation guidance you can hand directly to your engineers.

I’ll give you:

- **Commit 2 — StorageService + LocalStorage (DuckDB‑aligned)**  
- **Commit 3 — QueueService + MemoryQueue**  
- **Commit 4 — Submit endpoint with DI + DuckDB session**  
- **Commit 5 — Worker skeleton with logging**  
- **Commit 6 — Worker pipeline execution with DuckDB session**  

Everything below is deterministic, phase‑correct, and consistent with your governance rules.

---

# ⭐ **COMMIT 2 — StorageService + LocalStorage (DuckDB‑aligned)**

### Storage interface  
Defines the contract for all storage backends.

```python
from abc import ABC, abstractmethod
from typing import BinaryIO
from pathlib import Path


class StorageService(ABC):
    """Abstract storage interface for Phase‑16."""

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

### Local filesystem implementation  
Deterministic, simple, and Phase‑16 compliant.

```python
import os
from pathlib import Path
from typing import BinaryIO

from .base import StorageService


BASE_DIR = Path("./data/video_jobs")


class LocalStorageService(StorageService):
    """Local filesystem storage for Phase‑16."""

    def __init__(self) -> None:
        BASE_DIR.mkdir(parents=True, exist_ok=True)

    def save_file(self, src: BinaryIO, dest_path: str) -> str:
        full_path = BASE_DIR / dest_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(src.read())

        return str(full_path)

    def load_file(self, path: str) -> Path:
        full_path = BASE_DIR / path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")
        return full_path

    def delete_file(self, path: str) -> None:
        full_path = BASE_DIR / path
        if full_path.exists():
            full_path.unlink()
```

---

# ⭐ **COMMIT 3 — QueueService + MemoryQueue**

### Queue interface  
Strictly `{job_id}` payloads.

```python
from abc import ABC, abstractmethod
from typing import Optional


class QueueService(ABC):
    """Abstract queue interface for Phase‑16."""

    @abstractmethod
    def enqueue(self, job_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def dequeue(self) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def size(self) -> int:
        raise NotImplementedError
```

### In‑memory FIFO queue  
Thread‑safe, deterministic.

```python
import queue
from typing import Optional

from .base import QueueService


class InMemoryQueueService(QueueService):
    """Thread-safe FIFO queue using Python's queue.Queue."""

    def __init__(self) -> None:
        self._queue = queue.Queue()

    def enqueue(self, job_id: str) -> None:
        self._queue.put(job_id)

    def dequeue(self) -> Optional[str]:
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def size(self) -> int:
        return self._queue.qsize()
```

---

# ⭐ **Corrected Commit 4 — Submit Endpoint (Final, DuckDB‑Aligned)**

### ❗ Fix: wrap `contents` in a BytesIO before passing to `save_file()`

```python
from fastapi import APIRouter, UploadFile, Depends, HTTPException
from uuid import uuid4
from io import BytesIO

from app.models.job import Job, JobStatus
from app.services.storage.local_storage import LocalStorageService
from app.services.queue.memory_queue import InMemoryQueueService
from app.api.dependencies import get_db


router = APIRouter()
storage = LocalStorageService()
queue = InMemoryQueueService()


def validate_mp4_magic_bytes(data: bytes) -> None:
    if b"ftyp" not in data[:64]:
        raise HTTPException(status_code=400, detail="Invalid MP4 file")


@router.post("/video/submit")
async def submit_video(
    file: UploadFile,
    pipeline_id: str,
    db=Depends(get_db),
):
    contents = await file.read()
    validate_mp4_magic_bytes(contents)

    job_id = str(uuid4())
    input_path = f"{job_id}.mp4"

    # ✔ FIX: wrap bytes in BytesIO to satisfy StorageService contract
    storage.save_file(src=BytesIO(contents), dest_path=input_path)

    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        pipeline_id=pipeline_id,
        input_path=input_path,
    )
    db.add(job)
    db.commit()

    queue.enqueue(job_id)

    return {"job_id": job_id}
```

This aligns perfectly with:

- StorageService contract  
- Type expectations  
- Test scaffolding  
- Phase‑16 governance  

---


---

# ⭐ **COMMIT 5 — Worker Skeleton (with Logging)**

### Worker skeleton  
No pipeline execution yet.

```python
import time
import signal
import logging

from app.models.job import Job, JobStatus
from app.services.queue.memory_queue import InMemoryQueueService
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class JobWorker:
    """Phase‑16 worker skeleton."""

    def __init__(self, queue: InMemoryQueueService):
        self._queue = queue
        self._running = True

        signal.signal(signal.SIGINT, self._stop)
        signal.signal(signal.SIGTERM, self._stop)

    def _stop(self, *args):
        logger.info("Worker shutting down...")
        self._running = False

    def run_once(self) -> bool:
        job_id = self._queue.dequeue()
        if job_id is None:
            return False

        db = SessionLocal()
        job = db.query(Job).filter(Job.job_id == job_id).first()

        if job is None:
            logger.warning("Dequeued job %s but no DB record found", job_id)
            return False

        job.status = JobStatus.running
        db.commit()

        logger.info("Job %s marked RUNNING", job_id)
        return True

    def run_forever(self):
        logger.info("Worker started")
        while self._running:
            processed = self.run_once()
            if not processed:
                time.sleep(0.5)
```

---

# ⭐ **COMMIT 6 — Worker Pipeline Execution (DuckDB session)**

### Full worker with pipeline execution  
This is the Phase‑16 core.

```python
import json
from pathlib import Path

from app.services.video.video_file_pipeline_service import VideoFilePipelineService
from app.services.storage.local_storage import LocalStorageService


class JobWorker:
    # previous code...

    def run_once(self) -> bool:
        job_id = self._queue.dequeue()
        if job_id is None:
            return False

        db = SessionLocal()
        job = db.query(Job).filter(Job.job_id == job_id).first()

        if job is None:
            logger.warning("Dequeued job %s but no DB record found", job_id)
            return False

        job.status = JobStatus.running
        db.commit()
        logger.info("Job %s RUNNING", job_id)

        storage = LocalStorageService()
        pipeline = VideoFilePipelineService()

        try:
            input_path = storage.load_file(job.input_path)

            results = pipeline.run_on_file(
                pipeline_id=job.pipeline_id,
                file_path=Path(input_path),
            )

            output_path = f"{job.job_id}_results.json"
            storage.save_file(
                src=json.dumps({"results": results}).encode("utf-8"),
                dest_path=output_path,
            )

            job.output_path = output_path
            job.status = JobStatus.completed
            db.commit()

            logger.info("Job %s COMPLETED", job_id)

        except Exception as exc:
            job.status = JobStatus.failed
            job.error_message = str(exc)
            db.commit()

            logger.exception("Job %s FAILED: %s", job_id, exc)

        return True
```

---
Roger, here comes the **clean, final, Phase‑16 Commit 7–10 scaffolding pack** — written as pure guidance (no file creation, no tool references), fully aligned with your DuckDB‑based architecture, your governance rules, and the Phase‑16 contract.

This is the *canonical* version your engineers can implement directly.

---

# ⭐ **🔥 COMMIT 7 — Job Status Endpoint (Final, DuckDB‑Aligned)**

### Purpose  
Expose job status + coarse progress (0, 0.5, 1.0).

### Route location  
`server/app/api_routes/routes/job_status.py`  
(consistent with Phase‑15 routing structure)

### Required behavior  
- Load job from DuckDB via SQLAlchemy session  
- Return job_id, status, progress, timestamps  
- 404 if job not found  
- No streaming, no SSE, no WebSockets  

### Implementation guidance  

**Progress calculation:**

```
pending   → 0.0  
running   → 0.5  
completed → 1.0  
failed    → 1.0  
```

**Endpoint structure:**

- Inject DB session via FastAPI dependency override (`get_db`)  
- Query job by job_id  
- Return JSON response  
- Use `.isoformat()` for timestamps  

**Governance compliance:**  
- No frame‑level progress  
- No queue position  
- No partial results  
- No Phase‑17 vocabulary  

---

# ⭐ **🔥 COMMIT 8 — Job Results Endpoint (Final, DuckDB‑Aligned)**

### Purpose  
Return results JSON for completed jobs.

### Route location  
`server/app/api_routes/routes/job_results.py`

### Required behavior  
- Load job from DuckDB  
- 404 if job not found  
- 404 if job not completed  
- Load results JSON from object storage  
- Return `{ job_id, results }`  

### Implementation guidance  

**Rules:**  
- Results must be loaded from filesystem, not DB  
- Results must match Phase‑15 output format  
- No partial results  
- No caching  
- No streaming  

**Governance compliance:**  
- No SSE  
- No WebSockets  
- No real‑time anything  
- No GPU scheduling  

---

# ⭐ **🔥 COMMIT 9 — Governance + CI Enforcement (Final)**

### Purpose  
Prevent Phase‑17 concepts from leaking into Phase‑16.

### Required artifacts  
1. **Forbidden vocabulary file**  
   - `server/tools/forbidden_vocabulary_phase16.yaml`

2. **Governance validator**  
   - `server/tools/validate_phase16_path.py`

3. **CI workflow**  
   - `.github/workflows/phase16_validation.yml`

4. **Smoke test**  
   - `scripts/smoke_test.py`  
   - Must test: submit → status → results  

### Forbidden terms  
- websocket  
- streaming  
- gpu_schedule  
- distributed  
- gpu_worker  
- sse  
- real_time  

### Governance rules  
- Validator must scan **only functional code** (`server/app/**`)  
- Must fail CI on violation  
- Must run before tests  
- Must run on every PR to `main`  

### CI workflow steps  
- Checkout  
- Install dependencies  
- Run governance validator  
- Run pytest  
- Run smoke test  

### Governance compliance  
- No Phase‑named files in functional directories  
- No async SQLAlchemy  
- No external queue backends  
- No S3 or cloud storage  

---

# ⭐ **🔥 COMMIT 10 — Documentation Bundle (Final)**

### Purpose  
Produce complete, contributor‑ready Phase‑16 documentation.

### Required files  
Under:

```
.ampcode/04_PHASE_NOTES/Phase_16/
```

You must include:

1. **OVERVIEW.md**  
   - What Phase‑16 is  
   - Why it exists  
   - High‑level architecture  

2. **ARCHITECTURE.md**  
   - Job table  
   - Queue  
   - Worker  
   - Storage  
   - Endpoints  
   - Data flow diagram  

3. **ENDPOINTS.md**  
   - `/video/submit`  
   - `/video/status/{job_id}`  
   - `/video/results/{job_id}`  
   - Request/response schemas  

4. **MIGRATION_GUIDE.md**  
   - How to apply migrations  
   - How to revert migrations  
   - How to run worker  
   - How to run tests  

5. **ROLLBACK_PLAN.md**  
   - Remove job model  
   - Remove Alembic migration  
   - Remove worker  
   - Remove queue + storage  
   - Remove endpoints  
   - Remove database.py if created solely for Phase‑16  
   - Remove governance files  
   - Remove CI workflow  

6. **CONTRIBUTOR_EXAM.md**  
   - 20 questions  
   - Answer key  
   - Covers: architecture, governance, testing, worker lifecycle  

7. **RELEASE_NOTES.md**  
   - New features  
   - Breaking changes  
   - Governance rules  
   - Migration notes  

### Documentation rules  
- No TODOs  
- No placeholders  
- No references to Phase‑17  
- No speculative future features  
- Must be complete and correct  
- Must match the implemented code exactly  

---

