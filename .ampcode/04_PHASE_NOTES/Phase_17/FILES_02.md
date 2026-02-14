Roger — perfect.  
Here is the **clean, unified, final Phase‑17 scaffolding pack**, written exactly the way your Phase‑16 pack was:  
- No code execution  
- No file creation  
- No tools  
- Pure architectural + implementation guidance  
- Deterministic, governed, friction‑free for your engineers  

This includes:

1. **Phase‑17 User Stories (Commit 1–12)** — small, atomic, reviewable  
2. **Phase‑17 Folder Structure** — authoritative  
3. **Phase‑17 WebSocket Scaffolding** — endpoint, flow, validation  
4. **Phase‑17 Session Manager Scaffolding** — lifecycle, fields, API  

Everything below is ready to drop into `.ampcode/04_PHASE_NOTES/Phase_17/`.

---

# ⭐ **PHASE‑17 USER STORIES (Commit 1–12)**  
*Real‑Time Streaming Inference — WebSocket Architecture*

Each story is atomic, testable, and governance‑aligned.

---

# **Commit 1 — WebSocket Router + Endpoint Skeleton**

### Story  
As a backend engineer, I want a WebSocket endpoint skeleton so clients can connect to `/ws/video/stream`.

### Acceptance Criteria  
- File: `server/app/api_routes/routes/video_stream.py`  
- Defines WebSocket route: `/ws/video/stream`  
- Accepts connection, logs connect/disconnect  
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
  - `frame_index`  
  - `dropped_frames`  
  - `last_processed_ts`  
  - `backpressure_state`  
- Methods:  
  - `increment_frame()`  
  - `mark_drop()`  
  - `should_drop_frame()`  

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
  - Reasonable size (< 5MB)  
- Raises structured exceptions  

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
- Store session in WebSocket `state`  

### Out of Scope  
- Frame processing  
- Backpressure  

---

# **Commit 5 — Receive Binary Frames**

### Story  
As a backend engineer, I want the WebSocket to receive binary frames from the client.

### Acceptance Criteria  
- Accept `bytes` messages  
- Reject text messages  
- Pass frames to validator  
- Increment frame_index  

### Out of Scope  
- Pipeline execution  
- Backpressure  

---

# **Commit 6 — Frame Validation Integration**

### Story  
As a backend engineer, I want incoming frames validated before processing.

### Acceptance Criteria  
- Call `validate_jpeg()`  
- On invalid frame → send `{ "error": "invalid_frame" }` and close connection  

### Out of Scope  
- Pipeline execution  

---

# **Commit 7 — Pipeline Execution Integration**

### Story  
As a backend engineer, I want each valid frame processed by the Phase‑15 pipeline.

### Acceptance Criteria  
- Import `VideoFilePipelineService`  
- Call:  
  ```
  pipeline.run_on_frame(pipeline_id, frame_bytes)
  ```  
- Return result to client:  
  ```json
  { "frame_index": N, "result": {...} }
  ```  

### Out of Scope  
- Backpressure  
- Multi‑pipeline support  

---

# **Commit 8 — Backpressure (Drop Frames)**

### Story  
As a streaming engineer, I want to prevent overload by dropping frames when processing lags.

### Acceptance Criteria  
- SessionManager implements `should_drop_frame()`  
- If true → increment dropped count, skip pipeline  
- Send:  
  ```json
  { "frame_index": N, "dropped": true }
  ```  

### Out of Scope  
- Slow‑down signals  

---

# **Commit 9 — Backpressure (Slow‑Down Signal)**

### Story  
As a streaming engineer, I want to notify clients when they send frames too fast.

### Acceptance Criteria  
- When drop rate exceeds threshold → send:  
  ```json
  { "warning": "slow_down" }
  ```  

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
  - invalid frame  
  - pipeline failure  
  - internal errors  

---

# **Commit 11 — Logging + Metrics Hooks**

### Story  
As a maintainer, I want structured logs for streaming sessions.

### Acceptance Criteria  
- Log connect/disconnect  
- Log frame count  
- Log dropped frames  
- Log pipeline errors  

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
- Rollback plan  
- Contributor exam  
- Release notes  

---

# ⭐ **PHASE‑17 FOLDER STRUCTURE (Final)**

```
server/
└── app/
    ├── api_routes/
    │   └── routes/
    │       └── video_stream.py
    │
    ├── services/
    │   └── streaming/
    │       ├── session_manager.py
    │       ├── frame_validator.py
    │       ├── backpressure.py
    │       └── __init__.py
    │
    └── __init__.py

.ampcode/
└── 04_PHASE_NOTES/
    └── Phase_17/
        ├── PHASE_17_OVERVIEW.md
        ├── ARCHITECTURE.md
        ├── ENDPOINTS.md
        ├── SESSION_MODEL.md
        ├── NON_GOALS.md
        ├── ROLLBACK_PLAN.md
        ├── CONTRIBUTOR_EXAM.md
        └── RELEASE_NOTES.md
```

---

# ⭐ **PHASE‑17 WEBSOCKET SCAFFOLDING (Final)**

This is the architectural guidance for the endpoint.

### File: `video_stream.py`

- Accept WebSocket connection  
- Create SessionManager  
- Loop:  
  - Receive bytes  
  - Validate JPEG  
  - Increment frame index  
  - Apply backpressure  
  - Run pipeline  
  - Send result  
- On disconnect → cleanup  

### Message Flow

```
Client → binary frame → validator → session manager → pipeline → result → client
```

### Error Flow

```
invalid frame → send error → close connection
```

---

# ⭐ **PHASE‑17 SESSION MANAGER SCAFFOLDING (Final)**

### File: `session_manager.py`

### Responsibilities  
- Track per‑connection state  
- Frame index  
- Dropped frames  
- Backpressure thresholds  
- Timing metrics  

### Methods  
- `increment_frame()`  
- `mark_drop()`  
- `should_drop_frame()`  
- `record_processing_time()`  

### No persistence  
- All state is in‑memory  
- Destroyed on disconnect  

---

