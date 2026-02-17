Here you go, Roger — four tight Phase‑17 docs, each as its own piece, ready for:

` .ampcode/04_PHASE_NOTES/Phase_17/`

---

### PHASE_17_WEBSOCKET_END_TO_END_FLOW_DIAGRAM.md

```markdown
# Phase‑17 WebSocket End‑to‑End Flow Diagram

## High‑Level Flow

```text
+-------------------+        +---------------------+        +------------------------+
|   Front‑End       |        |   FastAPI App       |        |   Phase‑15 Pipeline    |
| (Browser/Client)  |        | /ws/video/stream    |        |  (DagPipelineService)  |
+---------+---------+        +----------+----------+        +-----------+------------+
          |                             |                               |
          | 1. WebSocket connect        |                               |
          +---------------------------->|                               |
          |                             | 2. Validate pipeline_id       |
          |                             +------------------------------>|
          |                             |                               |
          |                             | 3. Create SessionManager      |
          |                             |    (per connection)           |
          |                             |                               |
          | 4. Send JPEG frame (bytes)  |                               |
          +---------------------------->|                               |
          |                             | 5. validate_jpeg()            |
          |                             |    - size                     |
          |                             |    - SOI/EOI markers          |
          |                             |                               |
          |                             | 6. Backpressure check         |
          |                             |    - should_drop?             |
          |                             |                               |
          |                             | 7a. If drop:                  |
          |                             |    send {frame_index, dropped}|
          |                             |                               |
          |                             | 7b. If process:               |
          |                             |    run_on_frame(pipeline_id,  |
          |                             |                 frame_bytes)   |
          |                             +------------------------------>|
          |                             | 8. Pipeline returns result    |
          |                             |<------------------------------+
          |                             |                               |
          | 9. Send JSON result         |                               |
          |    {frame_index, result}    |                               |
          |<----------------------------+                               |
          |                             |                               |
          | 10. Repeat frames or close  |                               |
          +-----------------------------+                               |
```

## Key Properties

- One SessionManager per WebSocket connection  
- No persistence, no DuckDB writes  
- Backpressure handled per session  
- Pipeline reused from Phase‑15 via `run_on_frame()`
```

---

### PHASE_17_INTEGRATION_TEST_EXAMPLES.md

```markdown
# Phase‑17 Integration Test Examples

These examples use FastAPI's `TestClient` and `websocket_connect`.

---

## 1. Successful Frame Round‑Trip

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_stream_single_valid_frame():
    with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
        frame_bytes = make_valid_jpeg()  # helper in test utils
        ws.send_bytes(frame_bytes)

        msg = ws.receive_json()
        assert "frame_index" in msg
        assert "result" in msg
```

---

## 2. Invalid Pipeline ID

```python
def test_invalid_pipeline_rejected():
    with client.websocket_connect("/ws/video/stream?pipeline_id=does_not_exist") as ws:
        msg = ws.receive_json()
        assert msg["error"] == "invalid_pipeline"
```

---

## 3. Invalid Frame

```python
def test_invalid_frame_closes_connection():
    with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
        ws.send_bytes(b"not-a-jpeg")

        msg = ws.receive_json()
        assert msg["error"] == "invalid_frame"
        # Next receive should fail because connection is closed
        with pytest.raises(Exception):
            ws.receive_json()
```

---

## 4. Oversized Frame

```python
def test_oversized_frame_rejected():
    with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
        big_frame = b"\xFF\xD8" + b"0" * (6 * 1024 * 1024) + b"\xFF\xD9"
        ws.send_bytes(big_frame)

        msg = ws.receive_json()
        assert msg["error"] == "frame_too_large"
```

---

## 5. Backpressure Drop

```python
def test_backpressure_drops_frames(monkeypatch):
    from app.services.streaming.session_manager import SessionManager

    # Force should_drop_frame to always drop
    monkeypatch.setattr(SessionManager, "should_drop_frame", lambda self, ms: True)

    with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
        frame_bytes = make_valid_jpeg()
        ws.send_bytes(frame_bytes)

        msg = ws.receive_json()
        assert msg["dropped"] is True
        assert "frame_index" in msg
```

---

## 6. Slow‑Down Warning

```python
def test_slow_down_warning_emitted(monkeypatch):
    from app.services.streaming.session_manager import SessionManager

    # Force high drop rate
    monkeypatch.setattr(SessionManager, "drop_rate", lambda self: 0.5)

    with client.websocket_connect("/ws/video/stream?pipeline_id=yolo_ocr") as ws:
        frame_bytes = make_valid_jpeg()
        ws.send_bytes(frame_bytes)

        msg = ws.receive_json()
        assert msg["warning"] == "slow_down"
```
```

---

### PHASE_17_ERROR_CONTRACT_SPEC.md

```markdown
# Phase‑17 Error Contract Specification

All errors must be returned as JSON objects.  
No stack traces, no raw exceptions, no non‑JSON responses.

---

## 1. General Shape

```json
{
  "error": "<code>",
  "detail": "<human-readable message>"
}
```

- `error`: machine‑readable code (snake_case)
- `detail`: human‑readable explanation (safe to show in UI)

---

## 2. Error Codes

### invalid_pipeline
- **When:** `pipeline_id` is missing or not registered
- **Example:**
  ```json
  {
    "error": "invalid_pipeline",
    "detail": "Unknown pipeline_id: yolo_foo"
  }
  ```

### invalid_frame
- **When:** frame is empty or not valid JPEG
- **Example:**
  ```json
  {
    "error": "invalid_frame",
    "detail": "Not a valid JPEG image"
  }
  ```

### frame_too_large
- **When:** frame exceeds configured size limit
- **Example:**
  ```json
  {
    "error": "frame_too_large",
    "detail": "Frame exceeds 5MB"
  }
  ```

### pipeline_failure
- **When:** underlying pipeline throws
- **Example:**
  ```json
  {
    "error": "pipeline_failure",
    "detail": "YOLO inference failed"
  }
  ```

### invalid_message
- **When:** non‑binary or malformed WebSocket message
- **Example:**
  ```json
  {
    "error": "invalid_message",
    "detail": "Expected binary frame payload"
  }
  ```

### internal_error
- **When:** unexpected server error
- **Example:**
  ```json
  {
    "error": "internal_error",
    "detail": "Unexpected error occurred"
  }
  ```

---

## 3. Non‑Error Signals

These are not errors, but part of the contract:

### dropped frame

```json
{
  "frame_index": 42,
  "dropped": true
}
```

### slow‑down warning

```json
{
  "warning": "slow_down"
}
```

---

## 4. Guarantees

- All failures return JSON  
- No raw tracebacks to clients  
- Error codes are stable across versions  
- New error codes must be documented here
```

---

### PHASE_17_DEVELOPER_FAQ.md

```markdown
# Phase‑17 Developer FAQ

A quick reference for engineers working on the streaming layer.

---

## 1. What is Phase‑17?

Phase‑17 adds a real‑time WebSocket endpoint for frame‑level inference:

- `/ws/video/stream`
- One session per connection
- No persistence, no DuckDB writes
- Backpressure instead of queues

---

## 2. How does the client choose a pipeline?

Via query parameter:

```text
/ws/video/stream?pipeline_id=yolo_ocr
```

If the pipeline is invalid, the server returns:

```json
{ "error": "invalid_pipeline", "detail": "Unknown pipeline_id: ..." }
```

---

## 3. How are frames sent?

- As binary JPEG frames
- Recommended: 640×480, quality 0.7–0.8
- Max size: default 5MB (configurable)

---

## 4. What happens if a frame is invalid?

The server responds with:

```json
{ "error": "invalid_frame", "detail": "Not a valid JPEG image" }
```

…and closes the connection.

---

## 5. What is backpressure and how does it work?

Backpressure prevents overload by:

- Dropping frames when processing is too slow
- Emitting `{"warning": "slow_down"}` when drop rate is high

Dropped frames look like:

```json
{ "frame_index": N, "dropped": true }
```

---

## 6. Where is the session state stored?

In `SessionManager`, one instance per WebSocket connection:

- `frame_index`
- `dropped_frames`
- `backpressure_state`
- thresholds from env

No state is persisted after disconnect.

---

## 7. How does the pipeline get called?

Via `VideoFilePipelineService.run_on_frame(pipeline_id, frame_bytes)`, which delegates to the Phase‑15 DAG pipeline.

---

## 8. Are there any database changes?

No.

- No Alembic migrations
- No DuckDB writes
- Rollback is pure code removal

---

## 9. How do I test the WebSocket?

Use FastAPI’s `TestClient.websocket_connect` in `server/tests/streaming/`.

---

## 10. What should I never do in Phase‑17?

- Do not write to DuckDB  
- Do not add `/v1` endpoints  
- Do not persist sessions  
- Do not queue frames  
- Do not bypass the Phase‑15 pipeline  
- Do not return non‑JSON errors
```

