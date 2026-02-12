Absolutely, Roger — here is the **canonical Phase 15 “first failing test”** that drives the entire MP4‑upload feature from **red → green**.

This test is intentionally minimal, atomic, and forces the backend to implement:

- MP4 upload endpoint  
- Frame extraction  
- Per‑frame DAG execution  
- Returning a list of results  

It does **not** require async jobs, ffmpeg, or any heavy machinery yet.  
It is the smallest possible test that proves Phase 15 exists.

---

# ⭐ Phase 15 — First Failing Test  
Save as:

```
server/app/tests/test_phase15_first.py
```

This test uses a tiny MP4 fixture (1–3 frames).  
You can generate one with OpenCV or store a 1‑frame MP4 in `tests/fixtures/`.

```python
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from server.app.main import app  # your FastAPI entrypoint


@pytest.fixture
def tiny_mp4(tmp_path: Path):
    """
    A tiny MP4 file (1–3 frames). 
    You can commit a real file under tests/fixtures/tiny.mp4.
    """
    fixture = Path(__file__).parent / "fixtures" / "tiny.mp4"
    assert fixture.exists(), "Missing tiny.mp4 fixture"
    return fixture


def test_phase15_upload_and_run_pipeline(tiny_mp4):
    client = TestClient(app)

    # Phase 14 pipeline must already exist:
    #   n1: yolo.detect_players
    #   n2: reid.track_ids
    #
    # Phase 15: run this pipeline on an uploaded MP4.
    with tiny_mp4.open("rb") as f:
        resp = client.post(
            "/video/upload-and-run",
            files={"file": ("tiny.mp4", f, "video/mp4")},
            data={"pipeline_id": "player_tracking_v1"},
        )

    # Phase 15 MVP: synchronous processing
    assert resp.status_code == 200
    data = resp.json()

    # Must return a list of per-frame results
    assert "results" in data
    results = data["results"]
    assert isinstance(results, list)
    assert len(results) >= 1  # at least one frame processed

    # Each frame result must contain:
    #   - frame_index
    #   - result (output of DAG)
    first = results[0]
    assert "frame_index" in first
    assert "result" in first
    assert isinstance(first["result"], dict)
```

---

# ⭐ What This Test Forces You to Implement

This single test drives the entire Phase 15 MVP:

### 1. New endpoint  
```
POST /video/upload-and-run
```

### 2. Multipart upload handling  
- `file` (MP4)  
- `pipeline_id`  

### 3. Frame extraction  
- Use OpenCV or ffmpeg  
- Extract at least 1 frame  

### 4. DAG execution per frame  
```
dag_service.run_pipeline(pipeline_id, payload)
```

### 5. Return per‑frame results  
```json
{
  "results": [
    { "frame_index": 0, "result": {...} },
    { "frame_index": 1, "result": {...} }
  ]
}
```

### 6. No async jobs yet  
This is synchronous MVP.

---

# ⭐ What This Test Does *Not* Require (keeps Phase 15 small)

- No job queue  
- No progress tracking  
- No video export  
- No WebSocket integration  
- No UI changes yet  
- No sampling options  
- No batching  
- No GPU acceleration  

This is the smallest possible slice that proves:

**“Upload MP4 → run DAG → return per‑frame results.”**

---

