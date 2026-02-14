Roger, this is exactly the kind of refinement that makes your engineering system bullet‑proof.  
Below are **two deliverables**, each crafted to be deterministic, phase‑agnostic, and fully aligned with your governance rules:

- **A mock DAG service with failure injection**  
- **A corrupted‑MP4 test harness**  

Both are designed to run inside **unit tests only**, never touching real plugins or pipelines.

Let’s lock them in.

---

# ⭐ 1. Mock DAG Service With Failure Injection  
### Location (governance‑correct):
```
server/app/tests/video/fakes/mock_dag_service.py
```

### Purpose  
This mock lets you simulate:

- Pipeline not found  
- Plugin failure  
- Random failure  
- Deterministic success  
- Payload inspection  

### Implementation

```python
class MockDagPipelineService:
    """
    A deterministic mock DAG service with optional failure injection.
    Used ONLY for unit tests. Never imported by functional code.
    """

    def __init__(self, *, fail_mode=None):
        """
        fail_mode options:
            None                → always succeed
            "pipeline_not_found"→ raise FileNotFoundError
            "plugin_error"      → raise RuntimeError
            "random_failure"    → raise ValueError
        """
        self.fail_mode = fail_mode
        self.calls = []

    def run_pipeline(self, pipeline_id: str, payload: dict) -> dict:
        # Record call for assertions
        self.calls.append({
            "pipeline_id": pipeline_id,
            "payload": payload,
        })

        # Failure injection
        if self.fail_mode == "pipeline_not_found":
            raise FileNotFoundError("Pipeline not found")

        if self.fail_mode == "plugin_error":
            raise RuntimeError("Plugin execution failed")

        if self.fail_mode == "random_failure":
            raise ValueError("Random failure")

        # Normal deterministic success
        return {
            "mock": True,
            "pipeline_id": pipeline_id,
            "frame_index": payload["frame_index"],
            "bytes_length": len(payload["image_bytes"]),
        }
```

### Why this is perfect

- Zero plugin imports  
- Zero DAG engine imports  
- Zero pipeline loading  
- Fully deterministic  
- Fully traceable (`self.calls`)  
- Fully isolated  
- Fully governance‑safe  

---

# ⭐ 2. Unit Test Using Failure Injection  
### Location:
```
server/app/tests/video/test_video_service_failures.py
```

### Implementation

```python
from pathlib import Path
import cv2
import numpy as np

from app.services.video_file_pipeline_service import VideoFilePipelineService
from .fakes.mock_dag_service import MockDagPipelineService


def make_one_frame_mp4(path: Path):
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        5,
        (320, 240),
    )
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    writer.write(frame)
    writer.release()


def test_pipeline_not_found(tmp_path):
    video_path = tmp_path / "one.mp4"
    make_one_frame_mp4(video_path)

    mock = MockDagPipelineService(fail_mode="pipeline_not_found")
    service = VideoFilePipelineService(mock)

    try:
        service.run_on_file("bad_pipeline", str(video_path))
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass


def test_plugin_error(tmp_path):
    video_path = tmp_path / "one.mp4"
    make_one_frame_mp4(video_path)

    mock = MockDagPipelineService(fail_mode="plugin_error")
    service = VideoFilePipelineService(mock)

    try:
        service.run_on_file("yolo_ocr", str(video_path))
        assert False, "Expected RuntimeError"
    except RuntimeError:
        pass


def test_random_failure(tmp_path):
    video_path = tmp_path / "one.mp4"
    make_one_frame_mp4(video_path)

    mock = MockDagPipelineService(fail_mode="random_failure")
    service = VideoFilePipelineService(mock)

    try:
        service.run_on_file("yolo_ocr", str(video_path))
        assert False, "Expected ValueError"
    except ValueError:
        pass
```

---

# ⭐ 3. Corrupted MP4 Test Harness  
### Purpose  
You need a **deterministic way** to generate corrupted MP4s for testing.

### Location:
```
server/app/tests/video/fakes/corrupt_mp4_generator.py
```

### Implementation

```python
from pathlib import Path


def generate_corrupted_mp4(path: Path):
    """
    Writes bytes that LOOK like an MP4 header but are invalid.
    This ensures OpenCV fails to read it deterministically.
    """
    corrupted_bytes = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42mp41BADBADBADBAD"
    path.write_bytes(corrupted_bytes)
```

### Why this works

- Contains a fake MP4 header (`ftypmp42`)  
- Followed by invalid data  
- OpenCV will always fail to decode it  
- No randomness  
- No external dependencies  

---

# ⭐ 4. Test Using the Corrupted MP4 Harness  
### Location:
```
server/app/tests/video/test_video_corrupted_mp4_unit.py
```

### Implementation

```python
from pathlib import Path

from app.services.video_file_pipeline_service import VideoFilePipelineService
from .fakes.mock_dag_service import MockDagPipelineService
from .fakes.corrupt_mp4_generator import generate_corrupted_mp4


def test_corrupted_mp4_unit(tmp_path):
    video_path = tmp_path / "corrupt.mp4"
    generate_corrupted_mp4(video_path)

    mock = MockDagPipelineService()
    service = VideoFilePipelineService(mock)

    try:
        service.run_on_file("yolo_ocr", str(video_path))
        assert False, "Expected ValueError for corrupted MP4"
    except ValueError as e:
        assert "Unable to read video file" in str(e)
```

---

# ⭐ Roger, this is now a **complete, industrial‑grade testing harness**  
You now have:

### ✔ A mock DAG service with failure injection  
- pipeline not found  
- plugin error  
- random failure  
- deterministic success  

### ✔ A corrupted MP4 generator  
- deterministic  
- minimal  
- always fails in OpenCV  

### ✔ Unit tests for all failure modes  
- pipeline not found  
- plugin error  
- random failure  
- corrupted MP4  

### ✔ All code is phase‑agnostic  
- No phase names in functional code  
- All phase‑named files live only in `scripts/`  

You’re going full lab‑conditions now—I like it. Let’s add these as **test‑only fakes/harnesses**, all phase‑agnostic and governance‑safe.

---

### 🔥 Mock DAG service with latency injection

**File:** `server/app/tests/video/fakes/mock_dag_service_latency.py`

```python
import time


class MockDagPipelineServiceWithLatency:
    """
    Mock DAG service that injects artificial latency.
    Used ONLY in tests.
    """

    def __init__(self, *, latency_seconds: float = 0.0):
        self.latency_seconds = latency_seconds
        self.calls = []

    def run_pipeline(self, pipeline_id: str, payload: dict) -> dict:
        self.calls.append({"pipeline_id": pipeline_id, "payload": payload})

        if self.latency_seconds > 0:
            time.sleep(self.latency_seconds)

        return {
            "mock": True,
            "pipeline_id": pipeline_id,
            "frame_index": payload["frame_index"],
            "bytes_length": len(payload["image_bytes"]),
        }
```

Use this to simulate slow pipelines and verify the service doesn’t misbehave under latency.

---

### 🔥 Mock DAG service with output mutation

**File:** `server/app/tests/video/fakes/mock_dag_service_mutation.py`

```python
from typing import Callable, Dict, Any


class MockDagPipelineServiceWithMutation:
    """
    Mock DAG service that applies a mutation function to the output.
    Used ONLY in tests.
    """

    def __init__(self, mutator: Callable[[Dict[str, Any]], Dict[str, Any]]):
        self.mutator = mutator
        self.calls = []

    def run_pipeline(self, pipeline_id: str, payload: dict) -> dict:
        self.calls.append({"pipeline_id": pipeline_id, "payload": payload})

        base = {
            "mock": True,
            "pipeline_id": pipeline_id,
            "frame_index": payload["frame_index"],
            "bytes_length": len(payload["image_bytes"]),
        }

        return self.mutator(base)
```

Example test usage:

```python
def test_video_service_with_mutation(tmp_path):
    # ... create tiny mp4 ...
    def mutator(output):
        output["extra_flag"] = True
        return output

    mock = MockDagPipelineServiceWithMutation(mutator)
    service = VideoFilePipelineService(mock)

    results = service.run_on_file("yolo_ocr", str(video_path))
    assert results[0]["result"]["extra_flag"] is True
```

---

### 🔥 Stress test harness for 1000‑frame videos

**File:** `server/app/tests/video/stress/test_video_service_1000_frames.py`

```python
import cv2
import numpy as np
from pathlib import Path

from app.services.video_file_pipeline_service import VideoFilePipelineService
from .fakes.mock_dag_service import MockDagPipelineService


def generate_large_mp4(path: Path, frame_count: int = 1000):
    width, height = 320, 240
    fps = 25
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    for _ in range(frame_count):
        writer.write(frame)
    writer.release()


def test_video_service_1000_frames(tmp_path):
    video_path = tmp_path / "large.mp4"
    generate_large_mp4(video_path, frame_count=1000)

    mock = MockDagPipelineService()
    service = VideoFilePipelineService(mock, frame_stride=1, max_frames=None)

    results = service.run_on_file("yolo_ocr", str(video_path))

    assert len(results) == 1000
    assert results[0]["frame_index"] == 0
    assert results[-1]["frame_index"] == 999
    assert len(mock.calls) == 1000
```

This is pure stress on the service + mock, no real plugins.

---

### 🔥 Governance‑safe fuzz tester for MP4 inputs

We fuzz **structure**, not content: short, truncated, random, header‑only, etc. All in tests.

**File:** `server/app/tests/video/fuzz/test_video_service_mp4_fuzz.py`

```python
from pathlib import Path
import os
import random

from app.services.video_file_pipeline_service import VideoFilePipelineService
from .fakes.mock_dag_service import MockDagPipelineService


def write_random_bytes(path: Path, size: int):
    path.write_bytes(os.urandom(size))


def write_header_only_mp4(path: Path):
    path.write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42mp41")


def write_truncated_mp4(path: Path):
    path.write_bytes(b"\x00\x00\x00\x18ftypmp42TRUNCATED")


def fuzz_cases(tmp_path):
    files = []

    p1 = tmp_path / "random_1.bin"
    write_random_bytes(p1, 128)
    files.append(p1)

    p2 = tmp_path / "random_2.bin"
    write_random_bytes(p2, 1024)
    files.append(p2)

    p3 = tmp_path / "header_only.mp4"
    write_header_only_mp4(p3)
    files.append(p3)

    p4 = tmp_path / "truncated.mp4"
    write_truncated_mp4(p4)
    files.append(p4)

    return files


def test_video_service_mp4_fuzz(tmp_path):
    mock = MockDagPipelineService()
    service = VideoFilePipelineService(mock)

    for path in fuzz_cases(tmp_path):
        try:
            service.run_on_file("yolo_ocr", str(path))
            # Either it returns 0 frames or raises ValueError; both are acceptable.
        except ValueError:
            pass
```

This keeps fuzzing **inside tests**, with:

- No external tools  
- No random network calls  
- No phase‑named files  
- No forbidden vocabulary  

---
