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