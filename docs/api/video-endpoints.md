# Video API Endpoints

## POST /v1/video/submit

Submit a video for asynchronous processing.

### Parameters

- `file` (required): MP4 video file
- `pipeline_id` (optional, default: "ocr_only"): Pipeline to execute
  - `ocr_only`: Extract text only (v0.9.0-alpha)
  - `yolo_ocr`: Object detection + text extraction (v0.9.0-beta)

### Response

```json
{
  "job_id": "uuid-string"
}
```

### Example

```bash
# Alpha: Uses default pipeline (ocr_only)
curl -F "file=@video.mp4" http://localhost:8000/v1/video/submit

# Beta: Explicitly specify yolo_ocr pipeline
curl -F "file=@video.mp4" \
     -F "pipeline_id=yolo_ocr" \
     http://localhost:8000/v1/video/submit
```

## GET /v1/video/status/{job_id}

Get the status of a video processing job.

### Parameters

- `job_id` (required): UUID of the job

### Response

```json
{
  "job_id": "uuid-string",
  "status": "pending" | "running" | "completed" | "failed",
  "progress": 0-100,
  "created_at": "ISO-8601 timestamp",
  "updated_at": "ISO-8601 timestamp"
}
```

### Example

```bash
curl http://localhost:8000/v1/video/status/{job_id}
```

## GET /v1/video/results/{job_id}

Get the results of a completed video processing job.

### Parameters

- `job_id` (required): UUID of the job

### Response

```json
{
  "job_id": "uuid-string",
  "results": {
    "text": "Extracted OCR text...",
    "detections": [
      {
        "label": "person",
        "confidence": 0.95,
        "bbox": [x, y, width, height]
      }
    ]
  },
  "created_at": "ISO-8601 timestamp",
  "updated_at": "ISO-8601 timestamp"
}
```

### Example

```bash
curl http://localhost:8000/v1/video/results/{job_id}
```

## Notes

- All endpoints require authentication via `X-API-Key` header
- Video files are validated to ensure they are valid MP4 format
- Jobs are processed asynchronously; use the status endpoint to poll for completion
- Results are only available when job status is "completed"