# Phase 15: Offline Batch Video Processing

**Status**: Complete (Commits 1-10)  
**Date**: February 2026  
**Scope**: Synchronous MP4 file processing through YOLO+OCR pipeline  

## Overview

Phase 15 implements a single-request/response API for processing MP4 video files frame-by-frame through a frozen YOLO+OCR DAG pipeline.

### Frozen Scope (No async, jobs, persistence, streaming, or tracking)
- ✅ Single synchronous request/response
- ✅ MP4 file upload via multipart form-data
- ✅ Frame extraction with stride and max_frames options
- ✅ JPEG frame encoding as raw bytes (not base64)
- ✅ Per-frame DAG pipeline execution
- ✅ Aggregated results in frozen schema format

## API Contract

### Endpoint
```
POST /v1/video/process
```

### Request
- **Method**: multipart/form-data
- **Parameters**:
  - `file` (required): MP4 video file
  - `pipeline_id` (query, default="yolo_ocr"): Pipeline to execute
  - `frame_stride` (query, default=1): Process every Nth frame
  - `max_frames` (query, default=None): Maximum frames to process

### Response (Frozen Schema)
```json
{
  "results": [
    {
      "frame_index": 0,
      "result": { "detected_objects": [...] }
    },
    {
      "frame_index": 1,
      "result": { "detected_objects": [...] }
    }
  ]
}
```

**Constraints**:
- `results` is array of frame results
- No extra fields allowed
- `frame_index` must be integer
- `result` accepts any dict (pipeline output)

## Architecture

### Service Layer
`VideoFilePipelineService` orchestrates:
1. Open MP4 with OpenCV
2. Extract frames sequentially
3. Encode each frame as JPEG bytes (not base64)
4. Call DAG pipeline with payload: `{frame_index: int, image_bytes: bytes}`
5. Aggregate results

### Router Layer
`/api_routes/routes/video_file_processing.py` handles:
- File upload validation
- Query parameter parsing
- Dependency injection (pipeline registry, plugin manager)
- DAG service instantiation
- Error handling (400, 404, 500, 503)

### Dependency Injection
```python
# Injected from app.state
registry: PipelineRegistryService
plugin_manager: PluginManagementService

# Created dynamically
dag_service = DagPipelineService(registry, plugin_manager)
video_service = VideoFilePipelineService(dag_service)
```

## Implementation Details

### Commit 1-4: Core Service + Tests
- `VideoFilePipelineService`: Frame extraction and aggregation
- `MockDagPipelineService`: Test double with failure injection
- 24 unit tests covering happy path, options, errors, robustness
- `tiny.mp4` fixture (3 frames, 320×240)
- `yolo_ocr.json` pipeline definition

### Commit 5: Router + App Wiring + Registration Test
- Video router registration in main.py
- OpenAPI endpoint registration
- Schema validation tests
- 6 passing router tests

### Commit 6: Integration Tests + 5 Error Scenarios
- Error 1: Missing MP4 file → ValueError
- Error 2: Corrupted MP4 header → ValueError
- Error 3: Pipeline not found → ValueError
- Error 4: Pipeline execution failure → RuntimeError
- Error 5: Frame encoding failure → RuntimeError

### Commit 7: Schema Regression + Golden Snapshot
- Frozen schema snapshots
- Field type validation
- Required fields enforcement
- No extra fields constraint
- Schema serialization tests

### Commit 8: Stress + Fuzz Tests
- Process 30-frame video
- Extreme stride values (1, 999)
- Extreme max_frames (1, 9999)
- Resource cleanup validation
- MockDagPipelineService robustness

### Commit 9: Governance Tooling + CI
- `validate_phase15_video_pipeline.py` script
- Frozen schema contract checker
- Router registration validator
- Raw bytes (no base64) validator
- Service pattern checker
- Test suite runner

### Commit 10: Documentation + Demo
- This document
- Usage examples
- Troubleshooting guide
- Performance characteristics

## Usage Example

### Python Client
```python
import requests
from pathlib import Path

# Prepare video file
video_path = Path("my_video.mp4")

with open(video_path, "rb") as f:
    files = {"file": ("video.mp4", f, "video/mp4")}
    params = {
        "pipeline_id": "yolo_ocr",
        "frame_stride": 2,
        "max_frames": 10,
    }
    
    response = requests.post(
        "http://localhost:8000/v1/video/process",
        files=files,
        params=params,
    )

# Parse response
data = response.json()
for frame_result in data["results"]:
    frame_idx = frame_result["frame_index"]
    result = frame_result["result"]
    print(f"Frame {frame_idx}: {result}")
```

### cURL
```bash
curl -X POST \
  http://localhost:8000/v1/video/process \
  -F "file=@my_video.mp4" \
  -G \
  --data-urlencode "pipeline_id=yolo_ocr" \
  --data-urlencode "frame_stride=2" \
  --data-urlencode "max_frames=10"
```

## Testing

### Run All Video Tests
```bash
cd server
uv run pytest app/tests/video/ -v
```

### Run Specific Test Suite
```bash
# Unit tests (service layer)
uv run pytest app/tests/video/test_video_service_unit.py -v

# Router registration tests
uv run pytest app/tests/video/test_router_registration.py -v

# Integration tests (with errors)
uv run pytest app/tests/video/test_integration_video_processing.py -v

# Schema regression tests
uv run pytest app/tests/video/test_schema_regression.py -v

# Stress and fuzz tests
uv run pytest app/tests/video/test_stress_and_fuzz.py -v
```

### Governance Validation
```bash
# Run all governance checks
python scripts/validate_phase15_video_pipeline.py
```

## Performance Characteristics

### Bottlenecks
1. **Frame extraction**: Sequential OpenCV `cap.read()`
2. **JPEG encoding**: cv2.imencode() per frame
3. **DAG execution**: Per-frame pipeline latency
4. **Memory**: Video file loaded + frame buffers

### Optimization Notes
- Frame stride reduces pipeline calls
- max_frames prevents processing entire video
- Raw bytes (not base64) reduce memory overhead
- VideoCapture released in finally block (resource cleanup)

## Error Handling

### HTTP Status Codes
| Status | Condition |
|--------|-----------|
| 200 | Success |
| 400 | Invalid file format or parameters |
| 404 | Pipeline not found |
| 500 | Pipeline execution failed |
| 503 | Registry or plugin manager unavailable |

### Error Propagation
1. File validation errors → HTTP 400
2. Pipeline not found → HTTP 404
3. Pipeline execution errors → HTTP 500
4. Missing dependencies → HTTP 503

## Frozen Constraints (Never Change)

### Payload Contract
```python
payload = {
    "frame_index": int,        # 0-based frame number
    "image_bytes": bytes,      # Raw JPEG bytes (NOT base64)
}
```

### Response Schema (No Extra Fields)
```python
{
    "results": [
        {
            "frame_index": int,
            "result": dict,  # Any pipeline output
        }
    ]
}
```

### Forbidden Changes
- ❌ No async/await
- ❌ No job queue
- ❌ No persistence
- ❌ No WebSocket streaming
- ❌ No tracking across frames
- ❌ No base64 encoding (must use raw bytes)
- ❌ No extra response fields

## Files Modified/Created

### Service Layer
- `app/services/video_file_pipeline_service.py` (Commit 1-4)

### Router Layer
- `app/api_routes/routes/video_file_processing.py` (Commit 5)

### Tests
- `app/tests/video/test_video_service_unit.py` (Commit 1-4)
- `app/tests/video/test_router_registration.py` (Commit 5)
- `app/tests/video/test_integration_video_processing.py` (Commit 6)
- `app/tests/video/test_schema_regression.py` (Commit 7)
- `app/tests/video/test_stress_and_fuzz.py` (Commit 8)

### Governance & Documentation
- `scripts/validate_phase15_video_pipeline.py` (Commit 9)
- `docs/design/PHASE_15_VIDEO_PIPELINE.md` (Commit 10)

### Dependencies Added
- `opencv-python-headless` (for frame extraction)

### App Registration
- `app/main.py`: Include video router in FastAPI app

## Validation Checklist

Before each commit:
```bash
# 1. Run all video tests
uv run pytest app/tests/video/ -v

# 2. Run governance validation
python scripts/validate_phase15_video_pipeline.py

# 3. Check code quality
uv run ruff check app/api_routes/routes/video_file_processing.py
uv run mypy app/api_routes/routes/video_file_processing.py

# 4. Full test suite (once, before final commit)
uv run pytest tests/ -v
```

## Next Steps (Phase 16+)

After Phase 15:
- [ ] Async endpoint variant (if needed)
- [ ] Job-based processing for large videos
- [ ] Streaming response (WebSocket)
- [ ] Multi-pipeline support
- [ ] GPU optimization

## Troubleshooting

### 400: "Invalid file format"
- Ensure file is MP4, MOV, or AVI
- Check file isn't corrupted
- Verify MIME type in upload

### 404: "Pipeline not found"
- Check pipeline_id matches registered pipeline
- Verify `yolo_ocr.json` exists in `/app/pipelines/`
- Ensure plugins (YOLO, OCR) are loaded

### 500: "Pipeline execution failed"
- Check plugin logs for detailed errors
- Verify frame format (raw JPEG bytes)
- Check pipeline DAG definition

### 503: "Registry not available"
- Ensure app initialization complete
- Check app.state.pipeline_registry exists
- Verify PluginManagementService initialized

## References

- **AGENTS.md**: Project conventions and commands
- **ARCHITECTURE.md**: Overall system architecture
- **DAG Pipeline**: `docs/design/execution-architecture.md`
- **Plugin System**: `PLUGIN_DEVELOPMENT.md`
