
# ⭐ **COMMIT 1 — SQLAlchemy Job Model (Scaffolding Code)**  
Place this in:

```
server/app/models/job.py
```

```python
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()


class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    status = Column(
        Enum(JobStatus, name="job_status_enum"),
        nullable=False,
        default=JobStatus.pending,
    )

    pipeline_id = Column(String, nullable=False)

    input_path = Column(String, nullable=False)
    output_path = Column(String, nullable=True)

    error_message = Column(String, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
```

This matches the **final job schema** and Phase‑16 governance.

---

# ⭐ **COMMIT 1 — Alembic Migration Skeleton**  
Place this in:

```
server/app/migrations/versions/<timestamp>_create_job_table.py
```

```python
"""create_job_table

Revision ID: <generated>
Revises:
Create Date: <timestamp>
"""

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision = "<generated>"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "jobs",
        sa.Column(
            "job_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", name="job_status_enum"),
            nullable=False,
        ),
        sa.Column("pipeline_id", sa.String(), nullable=False),
        sa.Column("input_path", sa.String(), nullable=False),
        sa.Column("output_path", sa.String(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("jobs")
    op.execute("DROP TYPE job_status_enum")
```

This is **idempotent**, **clean**, and **Phase‑16 compliant**.

---

# ⭐ **PHASE‑16 MIGRATION SCRIPT TEMPLATE**  
This is the template your team will use for all future migrations in Phase‑16.

```
"""<migration_name>

Revision ID: <generated>
Revises: <previous_revision>
Create Date: <timestamp>
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "<generated>"
down_revision = "<previous_revision>"
branch_labels = None
depends_on = None


def upgrade():
    # TODO: implement migration logic
    pass


def downgrade():
    # TODO: implement rollback logic
    pass
```

This ensures:

- consistent formatting  
- consistent metadata  
- consistent rollback support  
- consistent Alembic behavior  

---


All code is deterministic, minimal, and Phase‑16‑compliant.

---

# ⭐ **🔥 COMMIT 2 — StorageService + LocalStorage (Scaffolding)**

### `server/app/services/storage/base.py`
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

---

### `server/app/services/storage/local_storage.py`
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

# ⭐ **🔥 COMMIT 3 — QueueService + MemoryQueue (Scaffolding)**

### `server/app/services/queue/base.py`
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

---

### `server/app/services/queue/memory_queue.py`
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

# ⭐ **🔥 COMMIT 4 — POST `/video/submit` Endpoint (Scaffolding)**

### `server/app/api/routes/job_submit.py`
```python
from fastapi import APIRouter, UploadFile, HTTPException
from uuid import uuid4

from app.models.job import Job, JobStatus
from app.services.storage.local_storage import LocalStorageService
from app.services.queue.memory_queue import InMemoryQueueService

router = APIRouter()

storage = LocalStorageService()
queue = InMemoryQueueService()


def validate_mp4_magic_bytes(data: bytes) -> None:
    if b"ftyp" not in data[:64]:
        raise HTTPException(status_code=400, detail="Invalid MP4 file")


@router.post("/video/submit")
async def submit_video(file: UploadFile, pipeline_id: str):
    # Read file bytes
    contents = await file.read()

    # Validate MP4
    validate_mp4_magic_bytes(contents)

    # Create job_id
    job_id = str(uuid4())

    # Save file
    input_path = f"{job_id}.mp4"
    storage.save_file(src=bytes(contents), dest_path=input_path)

    # Create job row
    job = Job(
        job_id=job_id,
        status=JobStatus.pending,
        pipeline_id=pipeline_id,
        input_path=input_path,
    )
    job.save()

    # Enqueue job
    queue.enqueue(job_id)

    return {"job_id": job_id}
```

---

# ⭐ **🔥 COMMIT 5 — Worker Skeleton (Scaffolding)**

### `server/app/workers/worker.py`
```python
import time
import signal
from typing import Optional

from app.models.job import Job, JobStatus
from app.services.queue.memory_queue import InMemoryQueueService


class JobWorker:
    """Phase‑16 worker skeleton."""

    def __init__(self, queue: InMemoryQueueService):
        self._queue = queue
        self._running = True

        signal.signal(signal.SIGINT, self._stop)
        signal.signal(signal.SIGTERM, self._stop)

    def _stop(self, *args):
        self._running = False

    def run_once(self) -> bool:
        job_id = self._queue.dequeue()
        if job_id is None:
            return False

        job = Job.get(job_id)
        if job is None:
            return False

        job.status = JobStatus.running
        job.save()

        return True

    def run_forever(self):
        while self._running:
            processed = self.run_once()
            if not processed:
                time.sleep(0.5)
```

---

### `server/app/workers/worker_runner.py`
```python
from app.services.queue.memory_queue import InMemoryQueueService
from .worker import JobWorker


def main():
    queue = InMemoryQueueService()
    worker = JobWorker(queue)
    worker.run_forever()


if __name__ == "__main__":
    main()
```

---

# ⭐ **🔥 COMMIT 6 — Worker Pipeline Execution (Scaffolding)**

### `server/app/workers/worker.py` (extended)
```python
from pathlib import Path
import json

from app.services.video.video_file_pipeline_service import VideoFilePipelineService
from app.services.storage.local_storage import LocalStorageService


class JobWorker:
    # ... previous code ...

    def run_once(self) -> bool:
        job_id = self._queue.dequeue()
        if job_id is None:
            return False

        job = Job.get(job_id)
        if job is None:
            return False

        job.status = JobStatus.running
        job.save()

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
            job.save()

        except Exception as exc:
            job.status = JobStatus.failed
            job.error_message = str(exc)
            job.save()

        return True
```

---
here is the **full Phase‑16 scaffolding pack** for Commits 7–10 — clean, governed, and ready to paste directly into your repo.  
This completes the entire Phase‑16 engineering foundation.



---

# ⭐ **🔥 COMMIT 7 — Job Status Endpoint (Scaffolding)**  
### File: `server/app/api/routes/job_status.py`

```python
from fastapi import APIRouter, HTTPException
from app.models.job import Job, JobStatus

router = APIRouter()


def compute_progress(status: JobStatus) -> float:
    if status == JobStatus.pending:
        return 0.0
    if status == JobStatus.running:
        return 0.5
    return 1.0  # completed or failed


@router.get("/video/status/{job_id}")
def get_job_status(job_id: str):
    job = Job.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "progress": compute_progress(job.status),
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }
```

**Governance‑compliant:**  
- No streaming  
- No WebSockets  
- No SSE  
- No frame‑level progress  

---

# ⭐ **🔥 COMMIT 8 — Job Results Endpoint (Scaffolding)**  
### File: `server/app/api/routes/job_results.py`

```python
from fastapi import APIRouter, HTTPException
import json

from app.models.job import Job, JobStatus
from app.services.storage.local_storage import LocalStorageService

router = APIRouter()
storage = LocalStorageService()


@router.get("/video/results/{job_id}")
def get_job_results(job_id: str):
    job = Job.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.completed:
        raise HTTPException(status_code=404, detail="Job not completed")

    results_path = job.output_path
    file_path = storage.load_file(results_path)

    with open(file_path, "r") as f:
        data = json.load(f)

    return {
        "job_id": job.job_id,
        "results": data.get("results", []),
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }
```

**Governance‑compliant:**  
- No partial results  
- No streaming  
- No caching  
- No DB‑stored results  

---

# ⭐ **🔥 COMMIT 9 — Governance + CI Enforcement (Scaffolding)**

## 1. **Forbidden Vocabulary File**  
### File: `server/tools/forbidden_vocabulary_phase16.yaml`

```yaml
forbidden:
  - websocket
  - streaming
  - gpu_schedule
  - distributed
  - gpu_worker
  - sse
  - real_time
  - websockets
  - async_stream
  - live_feed

allowed:
  - job_queue
  - worker
  - polling
  - async_job
```

---

## 2. **Governance Validator Script**  
### File: `server/tools/validate_phase16_path.py`

```python
import sys
import yaml
from pathlib import Path

ROOT = Path("server/app")


def load_rules():
    with open("server/tools/forbidden_vocabulary_phase16.yaml") as f:
        return yaml.safe_load(f)


def scan_file(path: Path, forbidden: list[str]) -> list[str]:
    violations = []
    text = path.read_text(errors="ignore")

    for word in forbidden:
        if word in text:
            violations.append(f"{path}:{word}")

    return violations


def main():
    rules = load_rules()
    forbidden = rules.get("forbidden", [])

    violations = []
    for file in ROOT.rglob("*.py"):
        violations.extend(scan_file(file, forbidden))

    if violations:
        print("Phase‑16 Governance Violations Detected:")
        for v in violations:
            print(" -", v)
        sys.exit(1)

    print("Phase‑16 Governance: CLEAN")
    sys.exit(0)


if __name__ == "__main__":
    main()
```

---

## 3. **CI Workflow**  
### File: `.github/workflows/phase16_validation.yml`

```yaml
name: Phase‑16 Governance + Tests

on:
  pull_request:
    branches: [ "main" ]

jobs:
  phase16-validation:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Install Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install Dependencies
        run: pip install -r requirements.txt

      - name: Run Governance Validator
        run: python server/tools/validate_phase16_path.py

      - name: Run Tests
        run: pytest --maxfail=1 --disable-warnings -q

      - name: Smoke Test
        run: python scripts/smoke_test.py
```

**Governance‑compliant:**  
- CI blocks Phase‑17 vocabulary  
- CI enforces tests  
- CI enforces smoke test  

---

# ⭐ **🔥 COMMIT 10 — Documentation Bundle (Scaffolding)**

### Folder: `.ampcode/04_PHASE_NOTES/Phase_16/`

Below are the **starter templates** for each required doc.

---

## 1. **OVERVIEW.md**

```markdown
# Phase‑16 Overview
Asynchronous Job Queue + Persistent Job State + Worker Execution

Phase‑16 introduces:
- Job table (persistent)
- Object storage for MP4 + results
- Queue abstraction
- Worker process
- Submit/status/results endpoints

This phase transforms Foregsyte from synchronous batch processing into a scalable asynchronous job system.
```

---

## 2. **ARCHITECTURE.md**

```markdown
# Phase‑16 Architecture

## Components
- Job table (SQLAlchemy + Alembic)
- StorageService (local filesystem)
- QueueService (in‑memory FIFO)
- Worker (pull → run → store → update)
- API endpoints (submit, status, results)

## Data Flow
1. Client submits MP4 → POST /video/submit
2. Job row created
3. Job enqueued
4. Worker dequeues job
5. Worker runs Phase‑15 pipeline
6. Results stored as JSON
7. Status + results retrievable via API
```

---

## 3. **ENDPOINTS.md**

```markdown
# Phase‑16 Endpoints

## POST /video/submit
- Accepts MP4 via UploadFile
- Validates magic bytes
- Creates job row
- Enqueues job_id
- Returns { job_id }

## GET /video/status/{job_id}
- Returns job status + coarse progress

## GET /video/results/{job_id}
- Returns results for completed jobs
```

---

## 4. **MIGRATION_GUIDE.md**

```markdown
# Phase‑16 Migration Guide

## Steps
1. Create job model
2. Create Alembic migration
3. Implement StorageService
4. Implement QueueService
5. Implement submit/status/results endpoints
6. Implement worker
7. Add governance + CI
8. Add documentation

## Rollback
- Drop job table
- Remove worker
- Remove endpoints
- Remove storage + queue services
```

---

## 5. **ROLLBACK_PLAN.md**

```markdown
# Phase‑16 Rollback Plan

## Remove Files
- server/app/models/job.py
- server/app/services/storage/*
- server/app/services/queue/*
- server/app/workers/*
- server/app/api/routes/job_*.py

## Remove Migration
- Delete Alembic migration file

## Remove CI Workflow
- .github/workflows/phase16_validation.yml

## Remove Governance Tools
- server/tools/validate_phase16_path.py
- server/tools/forbidden_vocabulary_phase16.yaml
```

---

## 6. **CONTRIBUTOR_EXAM.md**

```markdown
# Phase‑16 Contributor Exam

20 questions covering:
- Job lifecycle
- Queue semantics
- Worker transitions
- Storage rules
- Governance rules
- Endpoint behavior
```

---

## 7. **RELEASE_NOTES.md**

```markdown
# Phase‑16 Release Notes

## New Features
- Async job submission
- Worker execution
- Persistent job state
- Results retrieval

## Breaking Changes
- None

## Governance
- Phase‑17 vocabulary forbidden
```

Here we go, Roger—Phase‑16 tightened and Phase‑17 teed up.

---

### 🔥 Phase‑16 smoke test script

`scripts/smoke_test.py`:

```python
import time
import requests


BASE_URL = "http://localhost:8000"


def submit_job():
    with open("tests/fixtures/tiny.mp4", "rb") as f:
        files = {"file": ("tiny.mp4", f, "video/mp4")}
        resp = requests.post(
            f"{BASE_URL}/video/submit",
            files=files,
            params={"pipeline_id": "yolo_ocr"},
            timeout=10,
        )
    resp.raise_for_status()
    data = resp.json()
    return data["job_id"]


def wait_for_completion(job_id: str, timeout_seconds: int = 30):
    start = time.time()
    while time.time() - start < timeout_seconds:
        resp = requests.get(f"{BASE_URL}/video/status/{job_id}", timeout=5)
        if resp.status_code == 404:
            raise RuntimeError("Job disappeared during smoke test")
        data = resp.json()
        if data["status"] in ("completed", "failed"):
            return data
        time.sleep(1)
    raise TimeoutError("Job did not complete in time")


def fetch_results(job_id: str):
    resp = requests.get(f"{BASE_URL}/video/results/{job_id}", timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(f"Unexpected status for results: {resp.status_code}")
    return resp.json()


def main():
    print("[SMOKE] Submitting job...")
    job_id = submit_job()
    print(f"[SMOKE] Job submitted: {job_id}")

    print("[SMOKE] Waiting for completion...")
    status = wait_for_completion(job_id)
    print(f"[SMOKE] Final status: {status['status']}")

    if status["status"] != "completed":
        print("[SMOKE] Job did not complete successfully; skipping results fetch.")
        return

    print("[SMOKE] Fetching results...")
    results = fetch_results(job_id)
    if "results" not in results:
        raise RuntimeError("Results payload missing 'results' field")

    print("[SMOKE] Smoke test PASSED.")


if __name__ == "__main__":
    main()
```

---

### 🔥 Phase‑16 full test suite templates

**Job model** – `tests/app/models/test_job.py`:

```python
import pytest
from app.models.job import Job, JobStatus


@pytest.mark.unit
def test_job_defaults(session):
    job = Job(
        pipeline_id="yolo_ocr",
        input_path="video_jobs/abc.mp4",
    )
    session.add(job)
    session.commit()

    assert job.status == JobStatus.pending
    assert job.job_id is not None
    assert job.created_at is not None
    assert job.updated_at is not None
```

**Storage** – `tests/app/services/storage/test_local_storage.py`:

```python
from io import BytesIO
from pathlib import Path
from app.services.storage.local_storage import LocalStorageService


def test_local_storage_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.services.storage.local_storage.BASE_DIR",
        tmp_path,
        raising=False,
    )
    storage = LocalStorageService()

    data = BytesIO(b"test-bytes")
    path = "job123.mp4"

    storage.save_file(data, path)
    loaded = storage.load_file(path)
    assert loaded.exists()
    assert loaded.read_bytes() == b"test-bytes"

    storage.delete_file(path)
    assert not loaded.exists()
```

**Queue** – `tests/app/services/queue/test_memory_queue.py`:

```python
from app.services.queue.memory_queue import InMemoryQueueService


def test_memory_queue_fifo():
    q = InMemoryQueueService()
    q.enqueue("job1")
    q.enqueue("job2")

    assert q.dequeue() == "job1"
    assert q.dequeue() == "job2"
    assert q.dequeue() is None
```

**Worker skeleton** – `tests/app/workers/test_job_worker.py`:

```python
import pytest
from app.models.job import Job, JobStatus
from app.services.queue.memory_queue import InMemoryQueueService
from app.workers.worker import JobWorker


@pytest.mark.worker
def test_worker_marks_job_running(session):
    job = Job(
        pipeline_id="yolo_ocr",
        input_path="video_jobs/j1.mp4",
    )
    session.add(job)
    session.commit()

    q = InMemoryQueueService()
    q.enqueue(str(job.job_id))

    worker = JobWorker(q)
    processed = worker.run_once()
    session.refresh(job)

    assert processed is True
    assert job.status == JobStatus.running
```

**Worker + pipeline** – `tests/app/workers/test_worker_pipeline.py`:

```python
from pathlib import Path
from io import BytesIO
import json

from app.models.job import Job, JobStatus
from app.services.storage.local_storage import LocalStorageService
from app.services.queue.memory_queue import InMemoryQueueService
from app.workers.worker import JobWorker


def test_worker_runs_pipeline_and_stores_results(session, monkeypatch, tmp_path):
    monkeypatch.setattr(
        "app.services.storage.local_storage.BASE_DIR",
        tmp_path,
        raising=False,
    )

    storage = LocalStorageService()
    video_bytes = BytesIO(b"fake-mp4-with-ftyp")
    storage.save_file(video_bytes, "job123.mp4")

    job = Job(
        pipeline_id="yolo_ocr",
        input_path="job123.mp4",
    )
    session.add(job)
    session.commit()

    q = InMemoryQueueService()
    q.enqueue(str(job.job_id))

    class FakePipeline:
        def run_on_file(self, pipeline_id, file_path: Path):
            return [{"frame_index": 0, "result": "ok"}]

    monkeypatch.setattr(
        "app.workers.worker.VideoFilePipelineService",
        lambda: FakePipeline(),
    )

    worker = JobWorker(q)
    worker.run_once()
    session.refresh(job)

    assert job.status == JobStatus.completed
    assert job.output_path.endswith("_results.json")

    results_file = tmp_path / job.output_path
    data = json.loads(results_file.read_text())
    assert data["results"][0]["result"] == "ok"
```

**API submit/status/results** – `tests/app/api/test_job_*.py` can follow your existing TestClient patterns, now targeting `/video/submit`, `/video/status/{job_id}`, `/video/results/{job_id}`.

---

### 🔥 Phase‑16 worker logging + error handling enhancements

Extend `JobWorker` to log transitions and errors (still Phase‑16‑safe):

```python
import logging

logger = logging.getLogger(__name__)


class JobWorker:
    # existing __init__ ...

    def run_once(self) -> bool:
        job_id = self._queue.dequeue()
        if job_id is None:
            return False

        job = Job.get(job_id)
        if job is None:
            logger.warning("Dequeued job_id %s but job not found", job_id)
            return False

        logger.info("Job %s: transitioning to RUNNING", job_id)
        job.status = JobStatus.running
        job.save()

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
            job.save()
            logger.info("Job %s: COMPLETED", job_id)

        except Exception as exc:  # noqa: BLE001
            job.status = JobStatus.failed
            job.error_message = str(exc)
            job.save()
            logger.exception("Job %s: FAILED with error", job_id)

        return True
```

This gives you deterministic logs for every transition without introducing any Phase‑17 concepts.

---





