Roger, you’re about to have a **fully‑armed Phase 15 toolkit** for YOLO+OCR — fixtures, payload contracts, docs, governance, and UI.  
I’ll keep everything tight, atomic, and drop‑in ready so you can paste it straight into your repo.

Below are the **five deliverables** you asked for.

---

# ⭐ 1. Tiny MP4 Fixture Generator  
This creates a **1–3 frame MP4** suitable for tests.

Save as:

```
server/app/tests/fixtures/generate_tiny_mp4.py
```

```python
import cv2
import numpy as np
from pathlib import Path


def generate_tiny_mp4(path: Path, num_frames: int = 3):
    """
    Generate a tiny MP4 file for Phase 15 tests.
    Produces solid-color frames with frame index text.
    """
    width, height = 320, 240
    fps = 5

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))

    for i in range(num_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        cv2.putText(
            frame,
            f"Frame {i}",
            (50, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        writer.write(frame)

    writer.release()


if __name__ == "__main__":
    out = Path(__file__).parent / "tiny.mp4"
    generate_tiny_mp4(out)
    print("Generated:", out)
```

Run once:

```
python server/app/tests/fixtures/generate_tiny_mp4.py
```

This produces:

```
server/app/tests/fixtures/tiny.mp4
```

---

# ⭐ 2. Exact YOLO/OCR Payload Contract  
This is the **canonical payload** your DAG receives per frame.

### Input to YOLO (`detect_objects`)
```json
{
  "frame_index": 0,
  "image_bytes": "<JPEG bytes>"
}
```

### YOLO Output (example)
```json
{
  "detections": [
    { "bbox": [x1, y1, x2, y2], "confidence": 0.92, "class": "text" }
  ]
}
```

### Input to OCR (`extract_text`)
```json
{
  "frame_index": 0,
  "image_bytes": "<JPEG bytes>",
  "detections": [...]
}
```

### OCR Output (example)
```json
{
  "text": "Hello world",
  "regions": [
    { "bbox": [...], "text": "Hello" }
  ]
}
```

### Final DAG Output
```json
{
  "text": "Hello world",
  "regions": [...]
}
```

This is the **Phase‑14‑compatible** contract your tools should follow.

---

# ⭐ 3. Phase‑15 README (drop‑in)  
Save as:

```
server/app/docs/PHASE_15_README.md
```

```markdown
# Phase 15 — MP4 → DAG → Results (YOLO + OCR Edition)

Phase 15 extends the Phase 14 DAG engine to support **offline MP4 processing**.

## Scope

- Upload MP4
- Extract frames
- Run Phase 14 DAG per frame
- Return list of results
- Stateless, synchronous
- No job queue
- No persistence
- No streaming
- No ReID, no tracking, no Viz

## API

### POST /video/upload-and-run

**Request**
- `file`: MP4 (multipart)
- `pipeline_id`: string (e.g. `"yolo_ocr"`)

**Response**
```json
{
  "results": [
    { "frame_index": 0, "result": {...} },
    { "frame_index": 1, "result": {...} }
  ]
}
```

## Pipeline

`server/app/pipelines/yolo_ocr.json`

```
YOLO → OCR
```

## Implementation Components

- `VideoFilePipelineService`
- `/video/upload-and-run` endpoint
- OpenCV frame extraction
- Phase 14 DAG execution

## Testing

- `test_phase15_yolo_ocr.py`
- `fixtures/tiny.mp4`

## Out of Scope (Phase 16+)

- Job queue
- Async workers
- State across frames
- Tracking
- Persistence
- Metrics
- History
```

---

# ⭐ 4. Phase‑15 Governance Checklist  
Save as:

```
server/app/docs/PHASE_15_GOVERNANCE.md
```

```markdown
# Phase 15 Governance Checklist

This checklist ensures Phase 15 stays within scope.

## Pipeline Rules

- [ ] Only Phase 14 DAGs are allowed
- [ ] Pipeline must validate via `validate_pipelines.py`
- [ ] No ReID, Viz, or tracking required
- [ ] YOLO + OCR only for this phase

## API Rules

- [ ] Only one new endpoint: `POST /video/upload-and-run`
- [ ] Must return results synchronously
- [ ] No job IDs
- [ ] No polling endpoints
- [ ] No WebSocket streaming

## Execution Rules

- [ ] Stateless per frame
- [ ] No state accumulation
- [ ] No persistence
- [ ] No database writes
- [ ] No async workers

## Testing Rules

- [ ] Tiny MP4 fixture exists
- [ ] First failing test passes
- [ ] Per-frame results validated

## Out of Scope (Phase 16+)

- Job queue
- Async execution
- State management
- Tracking
- Metrics
- History
- Versioning
```

---

# ⭐ 5. Phase‑15 UI Update (Frontend)  
This is the **minimal UI change** needed to support MP4 upload + pipeline selection.

### Add a new button in your Video page:

```tsx
<input
  type="file"
  accept="video/mp4,video/quicktime"
  onChange={handleVideoUpload}
/>
```

### Add handler:

```tsx
async function handleVideoUpload(e: React.ChangeEvent<HTMLInputElement>) {
  const file = e.target.files?.[0];
  if (!file) return;

  const form = new FormData();
  form.append("file", file);
  form.append("pipeline_id", selectedPipelineId);

  const resp = await fetch("/video/upload-and-run", {
    method: "POST",
    body: form,
  });

  const data = await resp.json();
  setResults(data.results);
}
```

### Add results viewer:

```tsx
{results.map(r => (
  <div key={r.frame_index}>
    <h4>Frame {r.frame_index}</h4>
    <pre>{JSON.stringify(r.result, null, 2)}</pre>
  </div>
))}
```

### No changes needed to PluginSelector  
Because YOLO + OCR already exist.

---

# ⭐ You now have a complete Phase 15 package  
Everything you need to ship:

- Tiny MP4 generator  
- Payload contract  
- README  
- Governance checklist  
- UI integration  

