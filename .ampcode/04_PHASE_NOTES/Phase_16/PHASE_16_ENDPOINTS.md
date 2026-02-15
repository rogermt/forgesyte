# Phase 16 Endpoints

**Date**: 2026-02-13
**Phase**: 16 - Asynchronous Job Queue + Persistent Job State + Worker Execution

---

## API Endpoints

### POST /video/submit

Submit a video file for asynchronous processing.

**Request**:
```
Content-Type: multipart/form-data

file: <mp4_file>
pipeline_id: "yolo_ocr" (form field)
frame_stride: 1 (form field, optional)
max_frames: null (form field, optional)
```

**Response** (200 OK):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid file format or parameters
- `503 Service Unavailable`: Queue or database unavailable

---

### GET /video/status/{job_id}

Get the status of a submitted job.

**Request**:
```
GET /video/status/{job_id}
```

**Response** (200 OK):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 0.42,
  "created_at": "2026-02-13T00:00:00Z",
  "updated_at": "2026-02-13T00:01:00Z"
}
```

**Status Values**:
- `pending`: Job waiting to be processed
- `running`: Worker is processing the job
- `completed`: Job finished successfully
- `failed`: Job encountered an error

**Progress**:
- Optional field
- Float between 0.0 and 1.0
- Estimated completion percentage

**Error Responses**:
- `404 Not Found`: Job not found

---

### GET /video/results/{job_id}

Get the results of a completed job.

**Request**:
```
GET /video/results/{job_id}
```

**Response** (200 OK):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "results": [
    {
      "frame_index": 0,
      "result": {
        "detections": [...],
        "text": "Extracted text"
      }
    },
    {
      "frame_index": 1,
      "result": {...}
    }
  ],
  "created_at": "2026-02-13T00:00:00Z",
  "updated_at": "2026-02-13T00:02:00Z"
}
```

**Error Responses**:
- `404 Not Found`: Job not found or not completed

---

## Request/Response Schemas

### Submit Request Schema

```python
class VideoSubmitRequest:
    pipeline_id: str
    frame_stride: int = 1
    max_frames: Optional[int] = None
```

### Submit Response Schema

```python
class VideoSubmitResponse(BaseModel):
    job_id: UUID
```

### Status Response Schema

```python
class JobStatusResponse(BaseModel):
    job_id: UUID
    status: Literal["pending", "running", "completed", "failed"]
    progress: Optional[float] = None
    created_at: datetime
    updated_at: datetime
```

### Results Response Schema

```python
class JobResultsResponse(BaseModel):
    job_id: UUID
    results: List[FrameResult]
    created_at: datetime
    updated_at: datetime
```

---

## Example Usage

### Submit Job

```bash
curl -X POST http://localhost:8000/video/submit \
  -F "file=@video.mp4" \
  -F "pipeline_id=yolo_ocr"
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Check Status

```bash
curl http://localhost:8000/video/status/550e8400-e29b-41d4-a716-446655440000
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": 0.42,
  "created_at": "2026-02-13T00:00:00Z",
  "updated_at": "2026-02-13T00:01:00Z"
}
```

### Get Results

```bash
curl http://localhost:8000/video/results/550e8400-e29b-41d4-a716-446655440000
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "results": [
    {
      "frame_index": 0,
      "result": {
        "detections": [...],
        "text": "Extracted text"
      }
    }
  ],
  "created_at": "2026-02-13T00:00:00Z",
  "updated_at": "2026-02-13T00:02:00Z"
}
```

---

## Error Handling

### Invalid File Format

Request:
```bash
curl -X POST http://localhost:8000/video/submit \
  -F "file=@document.pdf" \
  -F "pipeline_id=yolo_ocr"
```

Response (400):
```json
{
  "detail": "Invalid file format. Must be MP4, MOV, or AVI."
}
```

### Job Not Found

Request:
```bash
curl http://localhost:8000/video/status/00000000-0000-0000-0000-000000000000000
```

Response (404):
```json
{
  "detail": "Job not found"
}
```

### Job Not Completed

Request:
```bash
curl http://localhost:8000/video/results/550e8400-e29b-41d4-a716-446655440000
```

Response (404):
```json
{
  "detail": "Job not completed"
}
```

---

## See Also

- `PHASE_16_OVERVIEW.md` - Feature overview
- `PHASE_16_ARCHITECTURE.md` - System architecture
- `PHASE_16_SCOPE.md` - What's in/out of scope
- `PHASE_16_WORKER_LIFECYCLE.md` - Worker behavior
- `PHASE_16_TEST_STRATEGY.md` - Testing approach
- `PHASE_16_GOVERNANCE_RULES.md` - Governance rules