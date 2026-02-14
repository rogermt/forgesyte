# Phase 15: Offline Batch Video Processing with YOLO + OCR

**Date**: 2026-02-13  
**Status**: IMPLEMENTATION PHASE  
**Scope**: Batch-only (synchronous, no async)

---

## Executive Summary

Phase 15 adds **offline video file processing** to ForgeSyte. Users can upload an MP4 file and receive frame-by-frame analysis results from the YOLO + OCR pipeline in a single synchronous request.

**In scope**: Video file upload → frame extraction → YOLO detection + OCR → JSON results  
**Out of scope**: Real-time processing, result storage, background execution, state management, visual output

---

## What Problem Does This Solve?

Currently, ForgeSyte processes **single images**. Users want to analyze **entire video files** without manually extracting and uploading frames.

Phase 15 solves this by:
1. Accepting an MP4 file via API
2. Extracting frames automatically
3. Running YOLO detection + OCR on each frame
4. Returning aggregated results

All in **one synchronous request**.

---

## How It Works

### Step 1: Upload MP4

```bash
curl -X POST http://localhost:8000/video/upload-and-run \
  -F "file=@video.mp4" \
  -F "pipeline_id=yolo_ocr"
```

### Step 2: Server Processes Frames

1. OpenCV opens MP4 file
2. Extracts frame 0, 1, 2, ...
3. Encodes each as JPEG bytes
4. Calls DAG pipeline: `{frame_index, image_bytes}`
5. Collects results

### Step 3: Return Aggregated Results

```json
{
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
  ]
}
```

---

## Architecture

### API Layer
- **Endpoint**: `POST /video/upload-and-run`
- **Input**: MP4 file + pipeline_id
- **Output**: JSON with results
- **Errors**: 404 (pipeline not found), 400 (invalid file), 422 (missing fields)

### Service Layer
- **VideoFilePipelineService**: Opens MP4, extracts frames, calls DAG
- **Uses**: OpenCV for video I/O, JPEG encoding
- **Payload**: Per-frame `{frame_index, image_bytes}`

### DAG Layer
- **Pipeline**: `yolo_ocr` (YOLO detection → OCR text extraction)
- **Per frame**: Stateless processing
- **Stateless**: Each frame independent

---

## Key Properties

### Synchronous
- Request blocks until all frames processed
- Single request/response cycle
- Response contains all results

### Stateless
- Frame 0 does not depend on frame 1
- No multi-frame state
- Each frame analyzed independently
- Same input → same output (deterministic)

### Minimal
- One pipeline only: YOLO + OCR
- One endpoint: `/video/upload-and-run`
- One service: `VideoFilePipelineService`
- Single-file scope, focused feature

---

## Example Workflow

```
User uploads tiny.mp4 (3 frames, 320×240)
                ↓
Server extracts frames 0, 1, 2
                ↓
Frame 0 → YOLO detection: [player1, player2]
        → OCR: "SCORE: 2-1"
                ↓
Frame 1 → YOLO detection: [player1, player2, ball]
        → OCR: "SCORE: 2-1"
                ↓
Frame 2 → YOLO detection: [player1, player2]
        → OCR: "HALF TIME"
                ↓
Response: {results: [{frame_index: 0, result: {...}}, ...]}
                ↓
User gets JSON with all 3 frames analyzed
```

---

## What's NOT In This Phase

- ❌ **Real-time updates**: No continuous progress notifications
- ❌ **Background execution**: Synchronous processing only
- ❌ **Result persistence**: No storage or history
- ❌ **Multi-frame state**: Each frame analyzed independently
- ❌ **Visual output**: JSON results only, no video annotation
- ❌ **Multiple pipelines**: Only YOLO + OCR

These are potential **future phases** but **NOT in Phase 15**.

---

## Testing Strategy

### Unit Tests (15+ tests)
- Service layer in isolation
- Mock DAG calls
- Frame extraction, stride, max_frames options
- Error cases (invalid MP4, missing frames)

### Integration Tests
- Happy path: Valid MP4 + yolo_ocr → 200 OK
- Error scenarios: 404, 400, 422 responses

### Stress Tests
- 1000-frame video processed sequentially
- Results in correct order, no gaps

### Fuzz Tests
- Malformed MP4 files handled gracefully
- No crashes, clear error messages

---

## Success Criteria

- ✅ POST /video/upload-and-run accepts MP4 files
- ✅ OpenCV successfully extracts frames
- ✅ Frames processed via YOLO + OCR pipeline
- ✅ Results aggregated in frozen schema: `{results: [...]}`
- ✅ All 4 test suites GREEN after every commit
- ✅ Zero forbidden vocabulary violations
- ✅ Governance rules enforced via CI

---

## Next Steps (Future Phases)

**Phase 16** (potential): Multi-pipeline selection  
**Phase 17** (potential): Background execution with deferred processing  
**Phase 18** (potential): Result persistence and history  

Phase 15 is intentionally **scoped narrow** to prove batch processing works before adding complexity.

---

## See Also

- `PHASE_15_PAYLOAD_YOLO_OCR.md` - Data contract
- `PHASE_15_SCOPE.md` - What's forbidden
- `PHASE_15_PROGRESS.md` - Implementation checklist
- `server/app/pipelines/yolo_ocr.json` - DAG definition
