Roger, here they are — **all four Phase‑17 documents**, written cleanly, coherently, and in the same Phase‑16/17 governance style.  
They’re ready to drop straight into:

```
.ampcode/04_PHASE_NOTES/Phase_17/
```

I’ve made them crisp, visual, and contributor‑friendly — the kind of docs that make a phase feel *finished*.

Let’s lock them in.

---

# ⭐ **PHASE_17_FRONTEND_UI_WIREFRAME.md**  
### *User‑Facing Flow for Upload + Streaming*

```markdown
# Phase‑17 Front‑End UI Wireframe

Phase‑17 introduces two user‑facing workflows:

1. **Async Video Upload (Phase‑16)**
2. **Real‑Time Streaming (Phase‑17)**

This wireframe defines the UI structure for both.

---

# 1. Home Screen

```
+------------------------------------------------+
| Foregsyte Vision Platform                      |
+------------------------------------------------+
| [ Upload Video ]                               |
| [ Live Stream ]                                |
+------------------------------------------------+
```

---

# 2. Upload Video Screen (Phase‑16)

```
+------------------------------------------------+
| Upload Video                                   |
+------------------------------------------------+
| [ Choose File ]  (MP4 only)                    |
|                                                |
| [ Upload ]                                     |
+------------------------------------------------+
| Status: Uploading...                           |
| Progress bar: ████████░░░░░░░░░░░░             |
+------------------------------------------------+
| Job ID: <uuid>                                 |
| Polling status...                              |
+------------------------------------------------+
| Results (when ready):                          |
|  - Detected objects                            |
|  - OCR text                                    |
|  - Timestamps                                  |
+------------------------------------------------+
```

---

# 3. Live Stream Screen (Phase‑17)

```
+------------------------------------------------+
| Live Stream                                    |
+------------------------------------------------+
| [ Start Camera ]                               |
|                                                |
|  +----------------------+   +----------------+ |
|  |  Camera Preview      |   |  Results       | |
|  |  (video element)     |   |  (JSON panel)  | |
|  +----------------------+   +----------------+ |
|                                                |
| [ Start Streaming ] [ Stop Streaming ]         |
+------------------------------------------------+
| FPS: 12   Dropped: 3   Slow‑Down: No          |
+------------------------------------------------+
```

---

# 4. Error States

```
[!] Invalid frame received — stream closed.
[!] Frame too large — reduce resolution.
[!] Slow down — sending frames too fast.
```

---

# 5. Summary

This UI supports both Phase‑16 and Phase‑17 execution models without conflict.
```

---

# ⭐ **PHASE_17_DEVELOPER_ONBOARDING_GUIDE.md**  
### *Everything a new contributor needs to start working on Phase‑17*

```markdown
# Phase‑17 Developer Onboarding Guide

Welcome to Phase‑17 — the real‑time streaming phase.  
This guide gets you productive in under 10 minutes.

---

# 1. What Phase‑17 Is

Phase‑17 adds a WebSocket endpoint for real‑time frame‑level inference.

- No jobs
- No persistence
- No queue
- No DuckDB writes

Everything is ephemeral.

---

# 2. Key Files

```
server/app/api_routes/routes/video_stream.py
server/app/services/streaming/session_manager.py
server/app/services/streaming/frame_validator.py
server/app/services/streaming/backpressure.py
```

---

# 3. How the System Works

```
Client → WebSocket → SessionManager → Validator → Pipeline → Client
```

Each connection = one session.

---

# 4. Running the Server

```
uv run uvicorn app.main:app --reload
```

WebSocket endpoint:

```
ws://localhost:8000/ws/video/stream
```

---

# 5. Sending Frames (Developer Test)

Use a simple Python client:

```python
ws.send(open("frame.jpg", "rb").read())
```

---

# 6. Expected Responses

```json
{ "frame_index": 1, "result": {...} }
```

Errors:

```json
{ "error": "invalid_frame" }
```

Backpressure:

```json
{ "warning": "slow_down" }
```

---

# 7. What Not to Do

- Do not write to DuckDB
- Do not persist sessions
- Do not queue frames
- Do not add `/v1` endpoints (Phase‑18 migration)

---

# 8. Where to Start Contributing

- Frame validator
- Backpressure tuning
- WebSocket integration tests
- Logging & metrics

---

# 9. Rollback

Delete the streaming folder + WebSocket route. No DB changes.

---

# 10. Summary

Phase‑17 is self‑contained, ephemeral, and safe to iterate on.
```

---

# ⭐ **PHASE_17_API_CONTRACT_POSTER.md**  
### *One‑page canonical reference for engineers*

```markdown
# Phase‑17 API Contract Poster

This poster defines the **canonical Phase‑17 API**.

---

# 1. WebSocket Endpoint

```
/ws/video/stream
```

Protocol: WebSocket  
Direction: Bidirectional  
Persistence: None  
State model: Per‑connection session

---

# 2. Incoming Messages

Binary JPEG frames.

Constraints:
- Max 5MB
- Must contain JPEG SOI/EOI markers
- Recommended 640×480

---

# 3. Outgoing Messages

## Success
```json
{
  "frame_index": <int>,
  "result": { ... }
}
```

## Dropped Frame
```json
{
  "frame_index": <int>,
  "dropped": true
}
```

## Slow‑Down Signal
```json
{
  "warning": "slow_down"
}
```

## Error
```json
{
  "error": "<code>"
}
```

---

# 4. Session Lifecycle

```
connect → stream frames → receive results → disconnect → session destroyed
```

No persistence.

---

# 5. Forbidden in Phase‑17

- No `/v1` endpoints added
- No database writes
- No job queue integration
- No multi‑client fan‑out
- No GPU scheduling
- No distributed workers

---

# 6. Related Phases

- Phase‑16: async jobs
- Phase‑18: namespace migration
```

---

# ⭐ **PHASE_17_TO_PHASE_18_MIGRATION_BLUEPRINT.md**  
### *How Phase‑17 transitions into Phase‑18 cleanly*

```markdown
# Phase‑17 → Phase‑18 Migration Blueprint

Phase‑18 is the stabilization + namespace‑migration phase.  
This blueprint defines how to transition cleanly.

---

# 1. What Phase‑18 Changes

### Namespace Migration
From:
```
/v1/video/*
/v1/health
```

To:
```
/video/*
/health
```

### Stabilization
- CI hardening
- Forbidden vocabulary enforcement
- Documentation consolidation
- Release preparation for v1.0.0

---

# 2. Migration Steps

## Step 1 — Introduce New Endpoints (Parallel)
Add:
- `/video/submit`
- `/video/status/{job_id}`
- `/video/results/{job_id}`
- `/health`

Keep `/v1/*` active.

---

## Step 2 — Update Tests
- Duplicate tests for new endpoints
- Keep `/v1` tests running

---

## Step 3 — Update CI
- Health check → `/health`
- Smoke tests → `/video/*`

---

## Step 4 — Update Front‑End
- Upload → `/video/submit`
- Poll → `/video/status/{job_id}`

---

## Step 5 — Deprecation Window
Log warnings for `/v1/*`.

---

## Step 6 — Remove `/v1/*`
Only after:
- All tests migrated
- All clients migrated
- CI stable

---

# 3. What Phase‑18 Does NOT Change

- Phase‑17 WebSocket endpoint stays the same
- Session model unchanged
- No GPU scheduling
- No distributed workers

---

# 4. Release Target

Phase‑18 concludes with:

```
Foregsyte v1.0.0
```

Namespace stabilized.  
Docs consolidated.  
CI hardened.  
Public‑ready.

---

# 5. Summary

Phase‑17 builds the streaming layer.  
Phase‑18 stabilizes the platform and prepares for release.
```

---

# ⭐ Roger — Phase‑17 is now *fully* documented and future‑proof.

You now have:

- UI wireframes  
- Developer onboarding  
- API contract poster  
- Migration blueprint  

