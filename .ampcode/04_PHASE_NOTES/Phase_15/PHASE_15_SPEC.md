### Phase 15 — MP4 upload spec on top of the DAG engine

**Theme:** “Offline video file processing through named DAG pipelines.”

#### 1. High-level behavior

- User uploads an MP4 (or MOV) file.
- User selects a named pipeline (Phase 14 DAG).
- Backend:
  - extracts frames from the video,
  - feeds each frame (or sampled frames) into the DAG pipeline,
  - aggregates results,
  - returns a structured result (JSONL, per-frame list, or summary).

No streaming, no WebSocket—this is **batch**.

---

#### 2. New API surface

**Backend**

- `POST /video/upload-and-run`
  - multipart/form-data:
    - `file`: MP4
    - `pipeline_id`: string
    - `options` (optional): JSON (sampling rate, max frames, etc.)
  - Response:
    - `{ "job_id": "...", "status": "queued" }` (if async), or
    - `{ "results": [...] }` (if synchronous for small files).

- Optional:
  - `GET /video/jobs/{job_id}` → status + results.

**UI**

- “Upload video” button in VideoTracker.
- Pipeline selector (Phase 14) reused.
- Progress indicator (if async).
- Simple results view (per-frame detections/tracks).

---

#### 3. Backend architecture

New service: `VideoFilePipelineService` (or similar):

```python
class VideoFilePipelineService:
    def __init__(self, dag_service: DagPipelineService):
        self._dag_service = dag_service

    def run_on_file(
        self,
        pipeline_id: str,
        file_path: str,
        options: dict | None = None,
    ) -> list[dict]:
        """Extract frames, run DAG per frame, return list of results."""
        ...
```

Responsibilities:

- Open video (OpenCV/ffmpeg).
- Iterate frames (with optional sampling).
- For each frame:
  - build `payload = {"frame_index": i, "image_bytes": ...}` (or ndarray).
  - call `dag_service.run_pipeline(pipeline_id, payload)`.
- Collect results into a list:
  - `[{ "frame_index": i, "result": {...} }, ...]`.

No new DAG logic—just **reusing Phase 14**.

---

#### 4. Storage and performance

Phase 15 can be scoped in two modes:

- **MVP (synchronous)**:
  - Small videos only.
  - Process in request thread.
  - Return full results in one response.

- **Production (async)**:
  - Store file to disk or object storage.
  - Enqueue job (Celery/RQ/etc.).
  - `POST /video/upload-and-run` returns `job_id`.
  - `GET /video/jobs/{job_id}` returns status + results.

You can explicitly keep Phase 15 MVP as synchronous and defer job system to Phase 16+.

---

#### 5. Governance for Phase 15

- No new pipeline semantics:
  - Must use existing Phase 14 DAGs.
- No implicit pipeline selection:
  - `pipeline_id` is required.
- No guessing frame sampling:
  - `options` must be explicit (e.g. `{"frame_stride": 5}`).
- No UI DAG editor:
  - Still just named pipeline selection.
- No video export / rendering:
  - Results are JSON only (overlays, MP4 export can be Phase 16+).

---
