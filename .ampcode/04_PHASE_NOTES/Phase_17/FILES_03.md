Roger, I’ve got you — here is the **full Phase‑17 hardening pack**, written in the same clean, governed, Phase‑16 style, and fully aligned with the architecture you’ve already locked in.

This gives you **eight new documents**, each one ready to drop into:

```
.ampcode/04_PHASE_NOTES/Phase_17/
```

I’ve written them so they feel like part of the same system:  
deterministic, contributor‑friendly, and future‑proof.

Let’s lock them in.

---

# ⭐ **PHASE_17_CLIENT_GUIDE.md**  
### *Front‑End Integration for Upload + Streaming*

```markdown
# Phase‑17 Client Guide — Upload + Real‑Time Streaming

Phase‑17 introduces two client‑facing execution models:

1. **Async Video Upload (Phase‑16)**
2. **Real‑Time Streaming (Phase‑17)**

This guide explains how front‑end clients interact with both.

---

# 1. Async Video Upload (Phase‑16)

## Endpoint
```
POST /v1/video/submit
```

## Flow
1. User selects an MP4 file.
2. Front‑end uploads via multipart/form‑data.
3. Server returns `{ job_id }`.
4. Front‑end polls:
   ```
   GET /v1/video/status/{job_id}
   ```
5. When status = `completed`, fetch results:
   ```
   GET /v1/video/results/{job_id}
   ```

## Front‑End Responsibilities
- Validate file type (MP4).
- Show upload progress.
- Poll status every 1–2 seconds.
- Display results when ready.

---

# 2. Real‑Time Streaming (Phase‑17)

## Endpoint
```
ws://<host>/ws/video/stream
```

## Flow
1. Front‑end opens WebSocket.
2. Captures frames from `<video>` or `<canvas>`.
3. Encodes each frame as JPEG (binary).
4. Sends frames at a controlled rate (10–30 FPS).
5. Receives:
   ```json
   { "frame_index": N, "result": {...} }
   ```
6. Renders results in real time.

---

# 3. Frame Encoding (Front‑End)

### Recommended
- Use `<canvas>` to extract frames.
- Use `canvas.toBlob("image/jpeg", 0.8)`.

### Constraints
- Max frame size: 5MB
- Recommended resolution: 640×480
- Recommended FPS: 10–15

---

# 4. Handling Backpressure

Server may send:
```json
{ "warning": "slow_down" }
```

Front‑end must:
- Reduce FPS
- Reduce resolution
- Or pause briefly

If server sends:
```json
{ "dropped": true }
```
The frame was skipped — continue streaming.

---

# 5. Error Handling

Server may send:
```json
{ "error": "invalid_frame" }
```

Front‑end must:
- Stop sending frames
- Close WebSocket
- Show error to user

---

# 6. When to Use Upload vs Streaming

| Use Case | Mode |
|----------|------|
| Full video analysis | Async upload |
| Real‑time camera feed | Streaming |
| Low latency | Streaming |
| High accuracy | Upload |
| Long videos | Upload |

---

# 7. Example WebSocket Client (Pseudocode)

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/video/stream");

ws.binaryType = "arraybuffer";

ws.onopen = () => startStreaming();
ws.onmessage = (msg) => handleResult(JSON.parse(msg.data));
ws.onerror = () => stopStreaming();
ws.onclose = () => stopStreaming();
```

---

# 8. Summary

Phase‑17 introduces a stable, predictable client contract for real‑time inference.  
Front‑end developers now have two clear paths: upload or stream.
```

---

# ⭐ **PHASE_17_PERFORMANCE_GUIDE.md**

```markdown
# Phase‑17 Performance Guide

Phase‑17 introduces real‑time constraints.  
This guide defines expected performance characteristics.

---

# 1. Latency Targets

| Stage | Target |
|-------|--------|
| Frame validation | < 2 ms |
| Pipeline inference | < 30 ms |
| WebSocket send | < 5 ms |
| Total round‑trip | < 40 ms |

---

# 2. Recommended Client Settings

- Resolution: **640×480**
- JPEG quality: **0.7–0.8**
- FPS: **10–15**
- Max frame size: **5MB**

---

# 3. Server Throughput

- Single session: 10–20 FPS
- Multiple sessions: depends on CPU
- Backpressure triggers when:
  - Processing time > frame interval
  - Dropped frames exceed threshold

---

# 4. Memory Footprint

- Session object: < 50KB
- No persistence
- No queueing of frames

---

# 5. Stress Testing

Test with:
- 30 FPS input
- 1080p frames
- Rapid connect/disconnect
- Invalid frames
- Oversized frames

---

# 6. Scaling Notes

Phase‑17 is CPU‑bound.  
GPU scheduling arrives in Phase‑18+.
```

---

# ⭐ **PHASE_17_TEST_STRATEGY.md**

```markdown
# Phase‑17 Test Strategy

Phase‑17 introduces a new execution model requiring dedicated tests.

---

# 1. Unit Tests

## Frame Validator
- Valid JPEG
- Invalid JPEG
- Oversized frame

## Session Manager
- Frame index increments
- Dropped frame logic
- Backpressure thresholds

---

# 2. Integration Tests

## WebSocket
- Connect / disconnect
- Send valid frame
- Send invalid frame
- Receive results
- Backpressure behavior

---

# 3. Pipeline Integration Tests
- Frame → pipeline → result
- Pipeline error propagation

---

# 4. Load Tests
- 30 FPS input
- Multiple sessions
- Backpressure activation

---

# 5. Failure‑Mode Tests
- Invalid frame
- Oversized frame
- Pipeline crash
- Client disconnect
- Server overload
```

---

# ⭐ **PHASE_17_BACKPRESSURE_DESIGN.md**

```markdown
# Phase‑17 Backpressure Design

Backpressure prevents overload during real‑time streaming.

---

# 1. Drop‑Frame Algorithm

If:
- processing_time > frame_interval  
OR  
- dropped_frames > threshold  

Then:
- Drop frame
- Increment dropped count
- Send:
  ```json
  { "frame_index": N, "dropped": true }
  ```

---

# 2. Slow‑Down Signal

If drop rate > 30%:
```json
{ "warning": "slow_down" }
```

Client must reduce FPS.

---

# 3. No Queueing

Phase‑17 does **not** queue frames.  
Queueing breaks real‑time guarantees.

---

# 4. Session‑Level Metrics
- dropped_frames
- frame_index
- processing_time
- backpressure_state
```

---

# ⭐ **PHASE_17_FAILURE_MODES.md**

```markdown
# Phase‑17 Failure Modes

This document defines all expected failure conditions.

---

# 1. Invalid Frame
Response:
```json
{ "error": "invalid_frame" }
```
Connection closes.

---

# 2. Oversized Frame
Response:
```json
{ "error": "frame_too_large" }
```
Connection closes.

---

# 3. Pipeline Error
Response:
```json
{ "error": "pipeline_failure" }
```
Connection closes.

---

# 4. Backpressure Overload
Response:
```json
{ "warning": "slow_down" }
```

---

# 5. Client Disconnect
- Session destroyed
- No persistence

---

# 6. Server Overload
- Drop frames
- Slow‑down signals
- Optional disconnect
```

---

# ⭐ **PHASE_17_METRICS_AND_LOGGING.md**

```markdown
# Phase‑17 Metrics & Logging

Real‑time systems require strong observability.

---

# 1. Metrics

## Session Metrics
- sessions_active
- frames_processed
- frames_dropped
- slow_down_signals

## Performance Metrics
- avg_processing_time
- max_processing_time
- pipeline_errors

---

# 2. Logging

Log:
- Connect / disconnect
- Frame count
- Dropped frames
- Pipeline errors
- Backpressure events

Format:
```json
{
  "event": "frame_processed",
  "session_id": "...",
  "frame_index": 42,
  "processing_ms": 28
}
```
```

---

# ⭐ **PHASE_17_SECURITY_NOTES.md**

```markdown
# Phase‑17 Security Notes

Phase‑17 introduces a new attack surface: WebSockets.

---

# 1. Frame Size Limits
- Reject frames > 5MB
- Prevent memory exhaustion

---

# 2. Rate Limits (Future)
- Phase‑17 does not enforce rate limits
- Phase‑18+ may add them

---

# 3. Timeouts
- Idle timeout: 30s
- Hard session timeout: 10 minutes

---

# 4. No Persistence
- Reduces attack surface
- No stored data to exfiltrate

---

# 5. Input Validation
- JPEG validation required
- Reject malformed frames
```

---

# ⭐ **PHASE_17_FUTURE_PHASE_LINKS.md**

```markdown
# Phase‑17 Future Phase Links

Phase‑17 is a stepping stone toward more advanced execution models.

---

# Phase‑18 — Namespace Migration + Stabilization
- Move from `/v1/*` → unversioned endpoints
- Introduce `/health`
- Harden CI
- Prepare for v1.0.0 release

---

# Phase‑19 — GPU Scheduling
- GPU worker pool
- Frame batching
- CUDA pipeline integration

---

# Phase‑20 — Distributed Workers
- Multi‑node execution
- Load balancing
- Distributed session routing

---

# Phase‑21 — Multi‑Pipeline DAGs
- Complex inference graphs
- Parallel execution
```

---

