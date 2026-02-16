

- **Include new items** we decided on  
- **Remove outdated items**  
- **Keep unchanged items intact**  
- **Reflect all the clarifications you just approved**  
- **Stay in the same style and structure**  

So here is the **fully updated, corrected, authoritative Phase‑17 User Story Pack**, with *only* the necessary changes applied — nothing missing, nothing duplicated, nothing silently altered.

Every commit below is now aligned with:

- The correct pipeline API (`run_on_frame`)  
- The correct pipeline selection method (query param)  
- The correct backpressure rules (configurable thresholds)  
- The correct frame size limit (configurable, default 5MB)  
- The correct SessionManager design  
- The correct WebSocket testing pattern  
- The correct Phase‑17 architecture decisions  

- This is last updated based on Q&A in [/home/rogermt/forgesyte/.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_Q&A_03.mdd]
- see also [/home/rogermt/forgesyte/.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_Q&A _01.md], [o [/home/rogermt/forgesyte/.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_Q&A _02.md]]

Let’s lock it in.

---

Roger, here is the **fully updated, corrected, authoritative Phase‑17 User Story Pack**, now amended to reflect **every single clarification** from:

- **PHASE_17_Q&A_01.md**  
- **PHASE_17_Q&A_02.md**  

I’ve **added all new items**, **removed outdated ones**, and **kept all unchanged items intact**.  
Nothing missing. Nothing duplicated. Nothing silently altered.

This is now the **canonical Phase‑17 User Story Pack**.

---

# ⭐ **PHASE‑17 USER STORIES (Commit 1–12, Final Consolidated & Corrected)**  
*Real‑Time Streaming Inference — WebSocket Architecture*

Each story is atomic, testable, and governance‑aligned.

---

# **Commit 1 — WebSocket Router + Endpoint Skeleton**

### Story  
As a backend engineer, I want a WebSocket endpoint skeleton so clients can connect to `/ws/video/stream`.

### Acceptance Criteria  
- File: `server/app/api_routes/routes/video_stream.py`  
- Defines WebSocket route: `/ws/video/stream`  
- Accepts connection, logs connect/disconnect (JSON logs)  
- Extracts `pipeline_id` from query parameters  
- Validates pipeline_id via `VideoFilePipelineService.is_valid_pipeline()`  
- Rejects connection if `pipeline_id` is missing or invalid  
- Uses `websocket.receive()` (binary‑safe)  
- No frame processing yet  
- No session manager yet  

### Out of Scope  
- Frame validation  
- Pipeline execution  
- Backpressure  
- Session state  

---

# **Commit 2 — Session Manager Class**

### Story  
As a streaming engineer, I want a SessionManager so each WebSocket connection has isolated state.

### Acceptance Criteria  
- File: `server/app/services/streaming/session_manager.py`  
- Fields:  
  - `session_id` (UUID)  
  - `pipeline_id`  
  - `frame_index`  
  - `dropped_frames`  
  - `last_processed_ts`  
  - `backpressure_state`  
  - `drop_threshold` (env or default 10%)  
  - `slowdown_threshold` (env or default 30%)  
- Methods:  
  - `increment_frame()`  
  - `mark_drop()`  
  - `drop_rate()`  
  - `should_drop_frame(processing_time_ms)` → delegates to Backpressure  
  - `should_slow_down()` → delegates to Backpressure  
  - `now_ms()` helper for timing  

### Out of Scope  
- Pipeline execution  
- WebSocket integration  

---

# **Commit 3 — Frame Validator**

### Story  
As a contributor, I want a frame validator to ensure incoming frames are valid JPEG.

### Acceptance Criteria  
- File: `server/app/services/streaming/frame_validator.py`  
- Function: `validate_jpeg(frame_bytes: bytes)`  
- Checks:  
  - JPEG SOI marker (`0xFF 0xD8`)  
  - JPEG EOI marker (`0xFF 0xD9`)  
  - Size limit (configurable, default 5MB)  
- Raises `FrameValidationError(code, detail)`  

### Out of Scope  
- MP4 validation  
- Pipeline execution  

---

# **Commit 4 — Integrate SessionManager into WebSocket**

### Story  
As a backend engineer, I want each WebSocket connection to create a SessionManager instance.

### Acceptance Criteria  
- On connect → create SessionManager  
- On disconnect → destroy SessionManager  
- Store session in `websocket.state.session` (FastAPI‑approved pattern)  
- SessionManager receives pipeline_id from query params  

### Out of Scope  
- Frame processing  
- Backpressure  

---

# **Commit 5 — Receive Binary Frames**

### Story  
As a backend engineer, I want the WebSocket to receive binary frames from the client.

### Acceptance Criteria  
- Accept `bytes` messages only  
- Reject text messages → send `{ "error": "invalid_message" }` and close  
- Increment frame_index  
- Pass frames to validator  

### Out of Scope  
- Pipeline execution  
- Backpressure  

---

# **Commit 6 — Frame Validation Integration**

### Story  
As a backend engineer, I want incoming frames validated before processing.

### Acceptance Criteria  
- Call `validate_jpeg()`  
- On invalid frame → send `{ "error": "invalid_frame" }` and close  
- On oversized frame → send `{ "error": "frame_too_large" }` and close  

### Out of Scope  
- Pipeline execution  

---

# **Commit 7 — Pipeline Execution Integration**

### Story  
As a backend engineer, I want each valid frame processed by the Phase‑15 pipeline.

### Acceptance Criteria  
- Extend `VideoFilePipelineService` with:  
  ```
  run_on_frame(pipeline_id, frame_index, frame_bytes)
  ```  
- Construct Phase‑15 payload:  
  ```json
  {
    "frame_index": N,
    "image_bytes": <raw JPEG bytes>
  }
  ```  
- Call:  
  ```
  DagPipelineService.run_pipeline(pipeline_id, payload)
  ```  
- Return result to client:  
  ```json
  { "frame_index": N, "result": {...} }
  ```  
- Must use the **existing Phase‑15 payload format** (per Q&A_02)  

### Out of Scope  
- Backpressure  
- Multi‑pipeline support  

---

# **Commit 8 — Backpressure (Drop Frames)**

### Story  
As a streaming engineer, I want to prevent overload by dropping frames when processing lags.

### Acceptance Criteria  
- SessionManager delegates to `Backpressure.should_drop()`  
- If drop → increment dropped count  
- Send:  
  ```json
  { "frame_index": N, "dropped": true }
  ```  
- Drop threshold configurable via env (default 10%)  
- Must use `websocket.receive()` timing via `now_ms()`  

### Out of Scope  
- Slow‑down signals  

---

# **Commit 9 — Backpressure (Slow‑Down Signal)**

### Story  
As a streaming engineer, I want to notify clients when they send frames too fast.

### Acceptance Criteria  
- SessionManager delegates to `Backpressure.should_slow_down()`  
- When drop rate exceeds slowdown threshold → send:  
  ```json
  { "warning": "slow_down" }
  ```  
- Slow‑down threshold configurable via env (default 30%)  

### Out of Scope  
- Disconnecting clients  

---

# **Commit 10 — Error Handling + Structured Exceptions**

### Story  
As a contributor, I want consistent error messages for all streaming failures.

### Acceptance Criteria  
- Unified error format:  
  ```json
  { "error": "<code>", "detail": "<message>" }
  ```  
- Covers:  
  - invalid_message  
  - invalid_frame  
  - frame_too_large  
  - pipeline_failure  
  - internal_error  
- No stack traces leaked to client  
- All errors JSON‑safe (per Phase‑16 governance)  

---

# **Commit 11 — Logging + Metrics Hooks**

### Story  
As a maintainer, I want structured logs and metrics for streaming sessions.

### Acceptance Criteria  
- JSON logs using Python logging + JSON formatter  
- Log:  
  - connect/disconnect  
  - pipeline_id  
  - frame_index  
  - dropped frames  
  - slow‑down events  
  - pipeline errors  
- Prometheus metrics exported:  
  - `stream_sessions_active` (Gauge)  
  - `stream_frames_processed` (Counter)  
  - `stream_frames_dropped` (Counter)  
  - `stream_slowdown_signals` (Counter)  
- Prometheus integration introduced in Phase‑17 (per Q&A_02)  

---

# **Commit 12 — Documentation + Rollback Plan**

### Story  
As a contributor, I want complete Phase‑17 documentation.

### Acceptance Criteria  
- Overview  
- Architecture  
- Endpoints  
- Session model  
- Backpressure  
- Performance guide  
- Client guide  
- Test strategy  
- Failure modes  
- Metrics & logging  
- Security notes  
- Future phase links  
- Rollback plan  
- Contributor exam  
- Release notes (internal + public summary)  

---

