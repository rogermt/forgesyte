### PHASE_17_END_TO_END_DEMO_SCRIPT.md

```markdown
# Phase‑17 End‑to‑End Demo Script

Goal: Show real‑time streaming from browser to pipeline and back.

---

## 1. Start the Server

```bash
uv run uvicorn app.main:app --reload
```

Verify health:

```bash
curl http://localhost:8000/health
```

---

## 2. Confirm a Valid Pipeline

List or confirm a known pipeline_id (e.g. `yolo_ocr`) from existing Phase‑15/16 docs or config.

We’ll use:

```text
pipeline_id = "yolo_ocr"
```

---

## 3. Open the WebSocket (Developer CLI Demo)

Use `websocat` or similar:

```bash
websocat ws://localhost:8000/ws/video/stream?pipeline_id=yolo_ocr
```

You should see the connection established (check logs for JSON “connected” event).

---

## 4. Send a Valid JPEG Frame

In another terminal, run a tiny Python helper:

```python
import websockets
import asyncio

async def main():
    uri = "ws://localhost:8000/ws/video/stream?pipeline_id=yolo_ocr"
    async with websockets.connect(uri) as ws:
        with open("frame.jpg", "rb") as f:
            data = f.read()
        await ws.send(data)
        msg = await ws.recv()
        print("Response:", msg)

asyncio.run(main())
```

Expected response (shape):

```json
{
  "frame_index": 1,
  "result": { ... }
}
```

---

## 5. Trigger an Invalid Frame Error

Change the script to send invalid bytes:

```python
await ws.send(b"not-a-jpeg")
```

Expected response:

```json
{
  "error": "invalid_frame",
  "detail": "Not a valid JPEG image"
}
```

Connection should then close.

---

## 6. Trigger Frame Too Large

Create a synthetic large JPEG:

```python
big = b"\xFF\xD8" + b"0" * (6 * 1024 * 1024) + b"\xFF\xD9"
await ws.send(big)
```

Expected response:

```json
{
  "error": "frame_too_large",
  "detail": "Frame exceeds 5MB"
}
```

---

## 7. Demonstrate Backpressure (Drop)

Temporarily force slow processing (e.g. sleep in pipeline or monkeypatch in dev):

- Send frames in a tight loop.
- Observe responses like:

```json
{ "frame_index": 5, "dropped": true }
```

---

## 8. Demonstrate Slow‑Down Warning

Simulate high drop rate (or configure thresholds low):

Expected response:

```json
{ "warning": "slow_down" }
```

---

## 9. Show Logs and Metrics

- Tail logs: confirm JSON entries for connect, frame_index, dropped, slow_down.
- Hit metrics endpoint (if exposed) and confirm:
  - `stream_sessions_active`
  - `stream_frames_processed`
  - `stream_frames_dropped`
  - `stream_slowdown_signals`

---

## 10. Wrap‑Up

Summarize:

- WebSocket connected with pipeline_id
- Frames validated, processed, and returned
- Errors and backpressure handled via JSON
- Logs and metrics reflect activity
```

---

### PHASE_17_TEST_FIRST_CODING_SEQUENCE.md

```markdown
# Phase‑17 Test‑First Coding Sequence

Goal: Implement Phase‑17 strictly via TDD, staying GREEN at each step.

---

## Step 1 — WebSocket Connect Tests

File: `server/tests/streaming/test_connect.py`

Write tests:

- valid pipeline_id → connect OK
- missing pipeline_id → error invalid_pipeline
- invalid pipeline_id → error invalid_pipeline

Run tests → RED.  
Implement minimal `/ws/video/stream` route + `VideoFilePipelineService.is_valid_pipeline()` until GREEN.

---

## Step 2 — SessionManager Tests

File: `test_session_manager.py`

Tests:

- frame_index increments
- dropped_frames increments
- drop_rate() correct
- thresholds load from env

Run → RED.  
Implement `SessionManager` until GREEN.

---

## Step 3 — Frame Validator Tests

File: `test_frame_validator.py`

Tests:

- valid JPEG passes
- invalid JPEG raises FrameValidationError("invalid_frame", ...)
- oversized frame raises FrameValidationError("frame_too_large", ...)

Run → RED.  
Implement `validate_jpeg()` until GREEN.

---

## Step 4 — Session Integration Tests

File: `test_connect.py` (extend)

Tests:

- SessionManager created on connect
- destroyed on disconnect

Run → RED.  
Wire SessionManager into WebSocket handler until GREEN.

---

## Step 5 — Receive Frames Tests

File: `test_receive_frames.py`

Tests:

- binary frame accepted
- text frame → invalid_message + close
- frame_index increments

Run → RED.  
Implement message receive logic until GREEN.

---

## Step 6 — Validation Integration Tests

Extend `test_receive_frames.py`:

- invalid JPEG → invalid_frame + close
- oversized frame → frame_too_large + close

Run → RED.  
Call `validate_jpeg()` and handle errors until GREEN.

---

## Step 7 — Pipeline Integration Tests

File: `test_pipeline_integration.py`

Tests:

- valid frame → DagPipelineService.run_pipeline called with payload:
  - frame_index
  - image_bytes
- response contains frame_index + result

Use monkeypatch/mocks for DagPipelineService.  
Run → RED.  
Implement `VideoFilePipelineService.run_on_frame()` and call it from handler until GREEN.

---

## Step 8 — Backpressure Drop Tests

File: `test_backpressure_drop.py`

Tests:

- monkeypatch Backpressure.should_drop() → True
- frame → response `{frame_index, dropped: true}`

Run → RED.  
Wire Backpressure + drop logic until GREEN.

---

## Step 9 — Slow‑Down Warning Tests

File: `test_backpressure_slowdown.py`

Tests:

- monkeypatch Backpressure.should_slow_down() → True
- frame → response `{warning: "slow_down"}`

Run → RED.  
Wire slow‑down logic until GREEN.

---

## Step 10 — Error Contract Tests

File: `test_error_handling.py`

Tests:

- invalid_message → `{error, detail}`
- invalid_frame → `{error, detail}`
- frame_too_large → `{error, detail}`
- pipeline_failure → `{error, detail}`
- internal_error → `{error, detail}`

Run → RED.  
Normalize error handling until GREEN.

---

## Step 11 — Logging & Metrics Tests

File: `test_logging_and_metrics.py`

Tests:

- connect/disconnect logs emitted (can assert via logger/mocks)
- Prometheus counters incremented

Run → RED.  
Add logging + metrics until GREEN.

---

## Step 12 — Final Regression

Run full suite:

```bash
pytest
```

Ensure:

- All streaming tests pass
- Existing Phase‑15/16 tests still GREEN
```

---

### PHASE_17_DEVELOPER_ONBOARDING_WALKTHROUGH.md

```markdown
# Phase‑17 Developer Onboarding Walkthrough

This is a narrative walkthrough to get a new contributor productive on Phase‑17.

---

## 1. Mental Model

Phase‑17 = “live frames over WebSocket”:

- Client sends JPEG frames
- Server validates + runs Phase‑15 pipeline
- Server returns JSON results per frame
- No persistence, no jobs, no queues

---

## 2. Key Files

- `server/app/api_routes/routes/video_stream.py`
- `server/app/services/streaming/session_manager.py`
- `server/app/services/streaming/frame_validator.py`
- `server/app/services/streaming/backpressure.py`
- `server/app/services/video_file_pipeline_service.py` (with `run_on_frame()`)

Tests:

- `server/tests/streaming/…`

Docs:

- `.ampcode/04_PHASE_NOTES/Phase_17/*.md`

---

## 3. How a Request Flows

1. Client connects to `/ws/video/stream?pipeline_id=yolo_ocr`
2. Server validates pipeline_id
3. SessionManager created for this connection
4. Client sends JPEG frame (bytes)
5. Frame validated (size + JPEG markers)
6. Backpressure checked (drop or process)
7. If process:
   - payload `{frame_index, image_bytes}` built
   - DagPipelineService.run_pipeline() called
   - result sent back as JSON
8. If drop:
   - `{frame_index, dropped: true}` sent
9. If overloaded:
   - `{warning: "slow_down"}` sent

---

## 4. How to Run and Poke It

Start server:

```bash
uv run uvicorn app.main:app --reload
```

Use a small Python script or browser client to:

- Connect with pipeline_id
- Send a frame
- Observe JSON response

---

## 5. Where to Start Coding

If you’re new to the codebase:

1. Read `PHASE_17_FINAL_CONSOLIDATED_SPEC.md`
2. Read `PHASE_17_USER_STORIES.md`
3. Start with tests in `server/tests/streaming/`:
   - `test_connect.py`
   - `test_session_manager.py`
   - `test_frame_validator.py`

Follow the **test‑first sequence**:

- Make one test fail (RED)
- Implement minimal code
- Make it pass (GREEN)
- Refactor if needed

---

## 6. Common Gotchas

- Don’t bypass Phase‑15: always use `run_on_frame()` → DAG pipeline.
- Don’t return non‑JSON errors: always `{error, detail}`.
- Don’t write to DB: Phase‑17 is fully ephemeral.
- Don’t add `/v1` endpoints: that’s Phase‑18 territory.
- Don’t mix streaming tests with legacy WebSocket tests: use `server/tests/streaming/`.

---

## 7. How to Know You’re “Done”

You’re done when:

- All Phase‑17 tests pass
- No existing tests are broken
- Logs show structured JSON entries for streaming
- Metrics show activity for:
  - sessions_active
  - frames_processed
  - frames_dropped
  - slow_down_signals
- The demo script runs cleanly end‑to‑end

---

## 8. If You’re Unsure

Ask yourself:

- Am I reusing Phase‑15 correctly?
- Am I respecting the error contract?
- Am I keeping everything ephemeral?
- Would rollback be just “delete streaming code”?

If yes to all, you’re aligned with Phase‑17.
```
