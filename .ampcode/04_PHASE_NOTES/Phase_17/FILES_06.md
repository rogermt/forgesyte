Absolutely, Roger — here are the **four files**, cleanly separated, fully written, and aligned with the Phase‑17 architecture you’ve locked in.  
No overlap, no missing pieces, no silent changes — each file is self‑contained and ready to drop into:

```
.ampcode/04_PHASE_NOTES/Phase_17/
```

Let’s lock them in.

---

# ⭐ FILE 1 — **PHASE_17_IMPLEMENTATION_BLUEPRINT.md**  
### *Commit‑by‑commit implementation plan (12 commits)*

```markdown
# Phase‑17 Implementation Blueprint
Real‑Time Streaming Inference — Commit‑by‑Commit Plan

This blueprint defines the exact implementation sequence for Phase‑17.  
Each commit starts GREEN, ends GREEN, and follows strict TDD.

---

# Commit 1 — WebSocket Router + Endpoint Skeleton
- Create file: `server/app/api_routes/routes/video_stream.py`
- Add route: `/ws/video/stream`
- Extract `pipeline_id` from query params
- Validate pipeline_id using existing registry
- Accept WebSocket connection
- Log connect/disconnect
- No session manager yet
- No frame handling yet

Tests:
- Connect succeeds with valid pipeline_id
- Connect fails with missing/invalid pipeline_id

---

# Commit 2 — SessionManager Class
- Create file: `server/app/services/streaming/session_manager.py`
- Fields:
  - session_id (UUID)
  - frame_index = 0
  - dropped_frames = 0
  - last_processed_ts = None
  - backpressure_state = "normal"
  - drop_threshold (env or default 0.10)
  - slowdown_threshold (env or default 0.30)
- Methods:
  - increment_frame()
  - mark_drop()
  - should_drop_frame(processing_time_ms)

Tests:
- Frame index increments
- Drop logic works
- Thresholds load from env

---

# Commit 3 — Frame Validator
- Create file: `server/app/services/streaming/frame_validator.py`
- Function: `validate_jpeg(frame_bytes)`
- Checks:
  - SOI marker
  - EOI marker
  - Size < STREAM_MAX_FRAME_SIZE_MB (default 5MB)
- Raise structured exceptions

Tests:
- Valid JPEG passes
- Invalid JPEG fails
- Oversized frame fails

---

# Commit 4 — Integrate SessionManager into WebSocket
- On connect → create SessionManager
- Store in `websocket.state.session`
- On disconnect → cleanup

Tests:
- Session created on connect
- Session destroyed on disconnect

---

# Commit 5 — Receive Binary Frames
- Accept only `bytes` messages
- Reject text messages
- Increment frame_index

Tests:
- Binary frame accepted
- Text frame rejected

---

# Commit 6 — Frame Validation Integration
- Call `validate_jpeg()`
- On invalid frame → send error + close
- On oversized frame → send error + close

Tests:
- Invalid frame triggers error
- Oversized frame triggers error

---

# Commit 7 — Pipeline Execution Integration
- Add `run_on_frame(pipeline_id, frame_bytes)` to VideoFilePipelineService
- Call pipeline per frame
- Send:
  ```json
  { "frame_index": N, "result": {...} }
  ```

Tests:
- Valid frame → pipeline called
- Result returned to client

---

# Commit 8 — Backpressure (Drop Frames)
- Use SessionManager.should_drop_frame()
- If drop → send:
  ```json
  { "frame_index": N, "dropped": true }
  ```

Tests:
- Drop logic triggers correctly
- Dropped frames counted

---

# Commit 9 — Backpressure (Slow‑Down Signal)
- If drop rate > slowdown_threshold → send:
  ```json
  { "warning": "slow_down" }
  ```

Tests:
- Slow‑down signal emitted correctly

---

# Commit 10 — Error Handling + Structured Exceptions
- Unified error format:
  ```json
  { "error": "<code>", "detail": "<message>" }
  ```
- Covers:
  - invalid_frame
  - frame_too_large
  - pipeline_failure
  - internal_error

Tests:
- All error types return correct JSON

---

# Commit 11 — Logging + Metrics Hooks
- Log:
  - connect/disconnect
  - pipeline_id
  - frame count
  - dropped frames
  - slow‑down events
  - pipeline errors
- Export metrics

Tests:
- Logs emitted
- Metrics counters increment

---

# Commit 12 — Documentation + Rollback Plan
- Add all Phase‑17 docs
- Rollback = delete streaming folder + route

Tests:
- None (documentation only)
```

---

# ⭐ FILE 2 — **PHASE_17_TEST_SUITE_SKELETON.md**  
### *Directory structure + test stubs*

```markdown
# Phase‑17 Test Suite Skeleton

Directory:
```
server/tests/streaming/
    test_connect.py
    test_session_manager.py
    test_frame_validator.py
    test_receive_frames.py
    test_pipeline_integration.py
    test_backpressure_drop.py
    test_backpressure_slowdown.py
    test_error_handling.py
```

---

# test_connect.py
- Connect with valid pipeline_id → success
- Connect with missing pipeline_id → fail
- Connect with invalid pipeline_id → fail

---

# test_session_manager.py
- Frame index increments
- Drop logic works
- Thresholds load from env

---

# test_frame_validator.py
- Valid JPEG passes
- Invalid JPEG fails
- Oversized frame fails

---

# test_receive_frames.py
- Binary frame accepted
- Text frame rejected
- Frame index increments

---

# test_pipeline_integration.py
- Valid frame → pipeline called
- Result returned to client

---

# test_backpressure_drop.py
- Drop triggered when processing too slow
- Dropped frames counted

---

# test_backpressure_slowdown.py
- Slow‑down signal emitted when drop rate > threshold

---

# test_error_handling.py
- invalid_frame → correct JSON
- frame_too_large → correct JSON
- pipeline_failure → correct JSON
- internal_error → correct JSON
```

---

# ⭐ FILE 3 — **PHASE_17_SESSION_MANAGER_TEMPLATE.md**  
### *Clean, ready‑to‑implement class skeleton*

```markdown
# Phase‑17 SessionManager Template

```python
import uuid
import time
import os

class SessionManager:
    def __init__(self, pipeline_id: str):
        self.session_id = str(uuid.uuid4())
        self.pipeline_id = pipeline_id

        self.frame_index = 0
        self.dropped_frames = 0
        self.last_processed_ts = None
        self.backpressure_state = "normal"

        self.drop_threshold = float(os.getenv("STREAM_DROP_THRESHOLD", 0.10))
        self.slowdown_threshold = float(os.getenv("STREAM_SLOWDOWN_THRESHOLD", 0.30))

    def increment_frame(self):
        self.frame_index += 1

    def mark_drop(self):
        self.dropped_frames += 1

    def drop_rate(self):
        if self.frame_index == 0:
            return 0.0
        return self.dropped_frames / self.frame_index

    def should_drop_frame(self, processing_time_ms: float) -> bool:
        if processing_time_ms > 100:  # ~10 FPS threshold
            return True
        if self.drop_rate() > self.drop_threshold:
            return True
        return False
```
```

---

# ⭐ FILE 4 — **PHASE_17_WEBSOCKET_HANDLER_TEMPLATE.md**  
### *Clean, ready‑to‑implement FastAPI WebSocket handler*

```markdown
# Phase‑17 WebSocket Handler Template

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.streaming.session_manager import SessionManager
from app.services.streaming.frame_validator import validate_jpeg
from app.services.video_file_pipeline_service import VideoFilePipelineService

router = APIRouter()

@router.websocket("/ws/video/stream")
async def video_stream(
    websocket: WebSocket,
    pipeline_id: str = Query(...)
):
    await websocket.accept()

    # Validate pipeline_id
    if not VideoFilePipelineService.is_valid_pipeline(pipeline_id):
        await websocket.send_json({"error": "invalid_pipeline"})
        await websocket.close()
        return

    session = SessionManager(pipeline_id)
    pipeline = VideoFilePipelineService()

    try:
        while True:
            message = await websocket.receive()

            if message["type"] != "websocket.receive" or "bytes" not in message:
                await websocket.send_json({"error": "invalid_message"})
                await websocket.close()
                return

            frame_bytes = message["bytes"]
            session.increment_frame()

            # Validate frame
            try:
                validate_jpeg(frame_bytes)
            except Exception as e:
                await websocket.send_json({"error": "invalid_frame", "detail": str(e)})
                await websocket.close()
                return

            # Pipeline execution
            result = pipeline.run_on_frame(pipeline_id, frame_bytes)
            await websocket.send_json({
                "frame_index": session.frame_index,
                "result": result
            })

    except WebSocketDisconnect:
        return
```
```

---

Roger — these four files give you:

- The **implementation plan**  
- The **test suite structure**  
- The **SessionManager class template**  
- The **WebSocket handler template**  



