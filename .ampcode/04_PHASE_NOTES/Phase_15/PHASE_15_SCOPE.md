Absolutely, Roger — let’s lock this down properly.  
You now have Phase 15 fully implemented, fully documented, and fully governed.  
The last two documents you asked for — **SCOPE** and **Definition of Done** — are the capstone pieces that make Phase 15 airtight and unambiguous.

Below are the **final, authoritative versions**, rewritten to match the *updated Phase‑15 scope* (YOLO + OCR, offline MP4 batch execution, no job queue, no async, no persistence, no tracking).

These are ready to drop into:

```
.ampcode/04_PHASE_NOTES/Phase_15/
```

---

# ⭐ PHASE 15 — SCOPE DOCUMENT  
Save as:

```
PHASE_15_SCOPE.md
```

```markdown
# Phase 15 — Scope Document  
**Offline MP4 → Multi‑Frame DAG Execution (YOLO + OCR Edition)**

## Purpose

Phase 15 extends the Phase 14 DAG engine to support **multi-frame execution** from offline MP4 files.  
This phase does *not* introduce job queues, async workers, persistence, tracking, or streaming.

The goal is to enable:

**“Upload MP4 → Extract Frames → Run YOLO → Run OCR → Return Per‑Frame Results.”**

---

## In Scope (Allowed in Phase 15)

### 1. MP4 Upload Support
- Accept MP4 files via `POST /video/upload-and-run`
- Validate file type

### 2. Frame Extraction
- Use OpenCV to read frames
- Support optional:
  - `frame_stride`
  - `max_frames`

### 3. Per‑Frame DAG Execution
- For each frame:
  - Build payload `{image_bytes, frame_index}`
  - Execute Phase‑14 DAG (`yolo_ocr`)
  - Collect results

### 4. Aggregated Results
Return:
```json
{
  "results": [
    { "frame_index": 0, "result": {...} }
  ]
}
```

### 5. New Components
- `VideoFilePipelineService`
- `/video/upload-and-run` endpoint
- Tiny MP4 fixture
- Phase‑15 integration tests
- Phase‑15 smoke test
- Phase‑15 documentation

---

## Out of Scope (Explicitly Forbidden in Phase 15)

### ❌ Job Queue
No:
- `POST /jobs`
- `GET /jobs/{id}`
- Background workers
- Redis/RabbitMQ

### ❌ Async Execution
No:
- Async workers
- Non-blocking job submission
- Parallel job execution

### ❌ Persistence
No:
- Database writes
- Job history
- Stored results
- Metrics tables

### ❌ Tracking / ReID / Viz
No:
- ReID plugin
- Tracking state
- Viz overlays

### ❌ State Across Frames
No:
- Accumulated detections
- Track IDs
- Temporal context

### ❌ Streaming
No:
- WebSocket streaming
- Live video feeds
- Incremental results

### ❌ New DAG Semantics
No:
- New node types
- New edge types
- New pipeline metadata

---

## Dependencies

Phase 15 requires Phase 14 to be complete:

- DAG engine  
- Pipeline validation  
- Type checking  
- Plugin metadata  
- YOLO + OCR plugins migrated  

---

## Summary

Phase 15 is a **minimal, governed extension** of Phase 14:

**Offline MP4 → Multi‑Frame DAG Execution → YOLO + OCR → JSON Results**

Nothing more.
```

---
