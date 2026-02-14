# Phase 15 Scope: Offline Batch Video Processing

**Date**: 2026-02-13  
**Status**: FROZEN (Phase 15)

---

## What IS In Scope

✅ **Single synchronous request/response cycle**
- `POST /video/upload-and-run` endpoint
- Upload MP4, get results back in same request
- No background processing

✅ **Frame extraction and processing**
- OpenCV to read MP4
- JPEG encoding per frame
- DAG execution (YOLO + OCR) per frame

✅ **Deterministic output**
- Same input → same results
- Results aggregated and returned as JSON

✅ **Single pipeline: YOLO + OCR**
- `yolo_ocr` pipeline only
- Frame-by-frame processing
- No multi-pipeline orchestration

---

## What is EXPLICITLY OUT OF SCOPE

### ❌ Job Queue / Async Processing

- **NO**: Redis, RabbitMQ, Celery, RQ, Bull
- **NO**: Background workers
- **NO**: Job IDs or job persistence
- **NO**: Delayed/queued execution
- **ONLY**: Synchronous blocking calls

### ❌ Persistence / Database

- **NO**: PostgreSQL, MongoDB, SQLite
- **NO**: Database writes
- **NO**: Job history
- **NO**: Result caching
- **NO**: User sessions or authentication state

### ❌ Streaming / Real-Time

- **NO**: WebSocket connections
- **NO**: Server-sent events (SSE)
- **NO**: Real-time progress updates
- **NO**: Live video processing

### ❌ Tracking / State Management

- **NO**: ReID (re-identification)
- **NO**: Multi-frame tracking
- **NO**: State carried between frames
- **NO**: Player IDs or trajectory tracking
- **ONLY**: Frame-by-frame stateless processing

### ❌ Visualization / Rendering

- **NO**: Annotated video generation
- **NO**: Bounding box overlays
- **NO**: Heatmaps or visual output
- **NO**: Web UI for video playback
- **ONLY**: JSON results

### ❌ Advanced Features

- **NO**: Metrics collection
- **NO**: Execution time tracking
- **NO**: Performance monitoring
- **NO**: Custom parameters per frame
- **NO**: Dynamic pipeline selection

---

## Governance Rules (Non-Negotiable)

| Rule | Consequence |
|------|-------------|
| No phase-named files in functional dirs | Code review rejection |
| No async/await in video service | Architecture violation |
| No database imports in video routes | Execution governance failure |
| No WebSocket in video processing | CI failure |
| Payload must have `frame_index` + raw `image_bytes` | Contract violation |
| Response must be `{results: [...]}` only | Schema regression failure |

---

## Forbidden Vocabulary (Auto-Detected)

The following terms **MUST NOT** appear in functional code:

- `job_id`, `job_queue`, `job_status`
- `worker`, `async_task`, `celery`
- `redis`, `rabbitmq`, `rq`, `bull`
- `database`, `postgres`, `mongodb`, `sql`, `insert_one`, `update_one`
- `track_ids`, `reid`, `reidentification`, `tracking`
- `websocket`, `streaming`, `sse`
- `annotate`, `overlay`, `visualization`
- `phase15`, `phase_15`, `phase-15` (use `video/` instead)

Violations caught by: `scripts/scan_execution_violations.py` + Phase 15 validator

---

## Minimal Implementation

Phase 15 is intentionally **small and focused**:

1. Service layer: Extract frames, call DAG
2. API endpoint: Accept MP4, return results
3. Tests: Unit + integration + stress
4. No extra infrastructure

**Why?** Build confidence in batch processing before adding:
- Multiple pipelines (Phase 16?)
- Async execution (Phase 17?)
- Result persistence (Phase 18?)

---

## Success Criteria

- [x] Single MP4 → results in one request
- [x] YOLO + OCR runs per frame
- [x] No async, queues, or persistence
- [x] Response is frozen schema
- [x] All tests GREEN
- [x] Zero forbidden vocabulary violations
- [x] Governance validator passes

---

## Related Files

- `PHASE_15_PAYLOAD_YOLO_OCR.md` - Data contract
- `PHASE_15_OVERVIEW.md` - Feature description
- `PHASE_15_ARCHITECTURE.txt` - System diagram
- `.github/workflows/video_batch_validation.yml` - CI enforcement
