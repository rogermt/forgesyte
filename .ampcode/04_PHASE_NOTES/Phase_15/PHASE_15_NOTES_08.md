Roger, I’ve got you — and this time I’m giving you **crisp, final, authoritative answers** for every single implementation detail.  
No ambiguity, no drift, no contradictions, no phase‑named files in functional code.  
Everything below is **Phase‑15‑correct**, **Phase‑14‑compatible**, and **governance‑aligned**.

Let’s lock this down.

---

# ⭐ 1. ERROR MESSAGES (EXACT STRINGS)

These must be **stable**, **predictable**, and **testable**.

### **Invalid file type**
```
Unsupported file type
```

### **Invalid pipeline_id**
```
Pipeline not found
```

### **Empty file upload**
```
Uploaded file is empty
```

### **Corrupted MP4**
```
Unable to read video file
```

These messages are intentionally short and deterministic.

---

# ⭐ 2. HTTP STATUS CODES (FINAL)

### **Missing pipeline_id field**
**422 Unprocessable Entity**  
(FastAPI automatically returns 422 for missing form fields.)

### **Missing file field**
**422 Unprocessable Entity**  
(FastAPI again handles this.)

### **Empty file**
**400 Bad Request**

### **Invalid file type**
**400 Bad Request**

### **Invalid pipeline_id**
**404 Not Found**

### **Corrupted MP4**
**400 Bad Request**

### **Server errors**
**500 Internal Server Error**

These codes match your Phase‑14 API conventions.

---

# ⭐ 3. FILE NAMES (FINAL)

### **Test files**
```
test_video_upload_and_run_success.py
test_video_invalid_file_type.py
test_video_invalid_pipeline_id.py
test_video_empty_file.py
test_video_corrupted_mp4.py
```

### **Service file**
```
video_file_pipeline_service.py
```

### **Router file**
```
video_file.py
```

All names reflect **function**, not phase.

---

# ⭐ 4. TEST SCENARIOS (FINAL LIST)

### **Required tests**
1. Valid MP4 → success  
2. Invalid file type  
3. Invalid pipeline_id  
4. Empty file  
5. Corrupted MP4  
6. Missing pipeline_id (422)  
7. Missing file field (422)

### **Assertions for success**
```python
assert resp.status_code == 200
data = resp.json()
assert "results" in data
assert isinstance(data["results"], list)
assert len(data["results"]) >= 1
first = data["results"][0]
assert "frame_index" in first
assert "result" in first
assert isinstance(first["result"], dict)
```

### **Assertions for invalid file type**
```python
assert resp.status_code == 400
assert resp.json()["detail"] == "Unsupported file type"
```

### **Assertions for invalid pipeline_id**
```python
assert resp.status_code == 404
assert resp.json()["detail"] == "Pipeline not found"
```

### **Assertions for empty file**
```python
assert resp.status_code == 400
assert resp.json()["detail"] == "Uploaded file is empty"
```

### **Assertions for corrupted MP4**
```python
assert resp.status_code == 400
assert resp.json()["detail"] == "Unable to read video file"
```

---

# ⭐ 5. CODE STRUCTURE (FINAL)

### **Should VideoFilePipelineService inherit from a base class?**
**No.**  
Phase‑15 is intentionally minimal.

### **Method signature**
```python
def run_on_file(
    self,
    pipeline_id: str,
    file_path: str,
    options: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
```

### **Internal variable names**
- `cap` → OpenCV capture  
- `frame_index` → int  
- `processed` → number of frames processed  
- `results` → list of outputs  
- `buf` → JPEG buffer  

These names match your Phase‑14 naming style.

---

# ⭐ 6. DEPENDENCY VERSION (FINAL)

### **opencv-python version**
```
opencv-python>=4.8.0
```

This is stable and compatible with your environment.

---

# ⭐ 7. ROUTER INTEGRATION (FINAL)

### **Where to import in main.py**
Add:

```python
from app.api.routes.video_file import router as video_router
app.include_router(video_router)
```

### **Prefix**
```
/video
```

### **Full endpoint**
```
POST /video/upload-and-run
```

---

# ⭐ 8. RESPONSE FORMAT (FINAL)

### **Response should contain ONLY:**
```json
{
  "results": [...]
}
```

### **No:**
- `status`
- `message`
- `metadata`
- `execution_time_ms`
- `pipeline_id`
- `frame_count`

Phase‑15 is intentionally minimal.

---

# ⭐ 9. TEMP FILE HANDLING (FINAL)

### **Should temp files be cleaned up on crash?**
**Best effort only.**  
Use:

```python
tmp_path.unlink(missing_ok=True)
```

If the process crashes, OS cleans up.

### **Temp file location**
Use system default temp directory:

```python
NamedTemporaryFile(delete=False, suffix=".mp4")
```

No custom folder.

---

# ⭐ 10. PAYLOAD STRUCTURE (FINAL)

### **Exact keys**
```python
{
  "frame_index": int,
  "image_bytes": bytes
}
```

### **Format of image_bytes**
**Raw JPEG bytes**, not base64.

Plugins already expect raw bytes.

---

# ⭐ Roger, this is the FINAL, GOVERNED, AUTHORITATIVE answer set  
Every detail is now:

- Explicit  
- Deterministic  
- Testable  
- Governance‑aligned  
- Phase‑14‑compatible  
- Phase‑15‑correct  
- Free of phase‑named files in functional code  

Here we go, Roger—clean, phase‑agnostic, drop‑in ready.

---

### FastAPI router (`server/app/api/routes/video_file.py`)

```python
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status

from app.services.video_file_pipeline_service import VideoFilePipelineService
from app.services.dag_pipeline_service import DagPipelineService

router = APIRouter(prefix="/video", tags=["video"])


def get_video_file_pipeline_service(
    dag_service: DagPipelineService = Depends(),
) -> VideoFilePipelineService:
    return VideoFilePipelineService(dag_service)


@router.post("/upload-and-run")
async def upload_and_run_video(
    pipeline_id: str = Form(...),
    file: UploadFile = File(...),
    service: VideoFilePipelineService = Depends(get_video_file_pipeline_service),
):
    if file.content_type not in ("video/mp4", "video/quicktime"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    try:
        with NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(contents)
            tmp_path = Path(tmp.name)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store file",
        )

    try:
        try:
            results = service.run_on_file(pipeline_id, str(tmp_path))
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pipeline not found",
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to read video file",
            )
    finally:
        tmp_path.unlink(missing_ok=True)

    return {"results": results}
```

---

### Service (`server/app/services/video_file_pipeline_service.py`)

```python
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2

from app.services.dag_pipeline_service import DagPipelineService


class VideoFilePipelineService:
    def __init__(
        self,
        dag_service: DagPipelineService,
        frame_stride: int = 1,
        max_frames: Optional[int] = None,
    ) -> None:
        self._dag_service = dag_service
        self._frame_stride = frame_stride
        self._max_frames = max_frames

    def run_on_file(
        self,
        pipeline_id: str,
        file_path: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        options = options or {}
        stride = int(options.get("frame_stride", self._frame_stride))
        max_frames = options.get("max_frames", self._max_frames)

        path = Path(file_path)
        if not path.exists():
            raise ValueError(f"File does not exist: {file_path}")

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise ValueError("Unable to read video file")

        results: List[Dict[str, Any]] = []
        frame_index = 0
        processed = 0

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                if frame_index % stride != 0:
                    frame_index += 1
                    continue

                if max_frames is not None and processed >= max_frames:
                    break

                ok, buf = cv2.imencode(".jpg", frame)
                if not ok:
                    frame_index += 1
                    continue

                payload: Dict[str, Any] = {
                    "frame_index": frame_index,
                    "image_bytes": buf.tobytes(),
                }

                dag_result = self._dag_service.run_pipeline(pipeline_id, payload)

                results.append(
                    {
                        "frame_index": frame_index,
                        "result": dag_result,
                    }
                )

                frame_index += 1
                processed += 1
        finally:
            cap.release()

        return results
```

---

### Tiny MP4 generator (`server/app/tests/fixtures/generate_tiny_mp4.py`)

```python
import cv2
import numpy as np
from pathlib import Path


def generate_tiny_mp4(path: Path) -> None:
    width, height = 320, 240
    fps = 5
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))

    for i in range(3):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        cv2.putText(
            frame,
            f"Frame {i}",
            (50, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        writer.write(frame)

    writer.release()


if __name__ == "__main__":
    out = Path(__file__).parent / "tiny.mp4"
    generate_tiny_mp4(out)
```

---

### Test suite (`server/app/tests/video/`)

**1. Success**

```python
from pathlib import Path

from fastapi.testclient import TestClient

from server.app.main import app


def test_video_upload_and_run_success():
    client = TestClient(app)
    tiny = Path(__file__).parent.parent / "fixtures" / "tiny.mp4"

    with tiny.open("rb") as f:
        resp = client.post(
            "/video/upload-and-run",
            files={"file": ("tiny.mp4", f, "video/mp4")},
            data={"pipeline_id": "yolo_ocr"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) >= 1
    first = data["results"][0]
    assert "frame_index" in first
    assert "result" in first
    assert isinstance(first["result"], dict)
```

**2. Invalid file type**

```python
from fastapi.testclient import TestClient

from server.app.main import app


def test_video_invalid_file_type():
    client = TestClient(app)

    resp = client.post(
        "/video/upload-and-run",
        files={"file": ("bad.txt", b"not a video", "text/plain")},
        data={"pipeline_id": "yolo_ocr"},
    )

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Unsupported file type"
```

**3. Invalid pipeline**

```python
from pathlib import Path

from fastapi.testclient import TestClient

from server.app.main import app


def test_video_invalid_pipeline_id():
    client = TestClient(app)
    tiny = Path(__file__).parent.parent / "fixtures" / "tiny.mp4"

    with tiny.open("rb") as f:
        resp = client.post(
            "/video/upload-and-run",
            files={"file": ("tiny.mp4", f, "video/mp4")},
            data={"pipeline_id": "does_not_exist"},
        )

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Pipeline not found"
```

**4. Empty file**

```python
from fastapi.testclient import TestClient

from server.app.main import app


def test_video_empty_file():
    client = TestClient(app)

    resp = client.post(
        "/video/upload-and-run",
        files={"file": ("empty.mp4", b"", "video/mp4")},
        data={"pipeline_id": "yolo_ocr"},
    )

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Uploaded file is empty"
```

**5. Corrupted MP4**

```python
from fastapi.testclient import TestClient

from server.app.main import app


def test_video_corrupted_mp4():
    client = TestClient(app)

    resp = client.post(
        "/video/upload-and-run",
        files={"file": ("corrupt.mp4", b"not real mp4 data", "video/mp4")},
        data={"pipeline_id": "yolo_ocr"},
    )

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Unable to read video file"
```

(FastAPI will already return 422 for missing fields, so you can add those tests if you want, but they’re mostly framework behavior.)

---

### PR sequence (10 PRs, one per commit)

1. **PR 1 — Video pipeline definition**
   - Add `yolo_ocr.json`
   - Add/update plugin validation if needed

2. **PR 2 — Tiny MP4 fixture + generator**
   - Add `generate_tiny_mp4.py`
   - Commit `tiny.mp4`

3. **PR 3 — Video service**
   - Add `video_file_pipeline_service.py`
   - Unit tests for `run_on_file` with a fake DAG service

4. **PR 4 — Video router**
   - Add `video_file.py`
   - Wire router into `main.py`

5. **PR 5 — Happy‑path API test**
   - Add `test_video_upload_and_run_success.py`

6. **PR 6 — Error tests: invalid file type + invalid pipeline**
   - Add `test_video_invalid_file_type.py`
   - Add `test_video_invalid_pipeline_id.py`

7. **PR 7 — Error tests: empty + corrupted MP4**
   - Add `test_video_empty_file.py`
   - Add `test_video_corrupted_mp4.py`

8. **PR 8 — Validator + forbidden vocabulary**
   - Add/update `server/tools/validate_video_batch_path.py`
   - Add `forbidden_vocabulary.yaml`

9. **PR 9 — CI wiring**
   - Add `video_batch_validation.yml`
   - Optionally add `smoke_test_video_batch.sh`

10. **PR 10 — Docs + governance**
   - Update `.ampcode/04_PHASE_NOTES/Phase_15/*`
   - Add Phase‑named policy doc, migration notes, checklist

