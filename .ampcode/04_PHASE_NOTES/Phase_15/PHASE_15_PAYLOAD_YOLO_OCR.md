# Phase 15 Payload Contract: YOLO + OCR Pipeline

**Date**: 2026-02-13  
**Status**: FROZEN (Phase 15)

---

## Overview

This document specifies the exact data contract between the API endpoint (`POST /video/upload-and-run`) and the DAG pipeline execution layer.

All data flows through this contract. **No deviations allowed.**

---

## Input Payload Per Frame

Each frame processed by the pipeline receives:

```json
{
  "frame_index": 0,
  "image_bytes": "<raw JPEG binary data>"
}
```

### Field Specifications

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `frame_index` | `int` | Sequential frame number (0-indexed) | `0`, `1`, `2`, ... |
| `image_bytes` | `bytes` | Raw JPEG binary data (NOT base64) | Binary blob |

### CRITICAL: Raw Bytes, NOT Base64

**DO NOT ENCODE AS BASE64.**

- ❌ WRONG: `"image_bytes": "iVBORw0KGgo..."`
- ✅ CORRECT: Raw binary passed to DAG pipeline

The DAG pipeline expects raw JPEG bytes for efficient OpenCV processing.

---

## Output: Pipeline Result Per Frame

Each frame produces:

```json
{
  "frame_index": 0,
  "result": {
    "detections": [...],
    "text": "Extracted text",
    ...other fields from yolo_ocr DAG
  }
}
```

### Result Structure

- `frame_index`: (int) Same as input frame_index
- `result`: (dict) Output from YOLO + OCR pipeline
  - Contents depend on DAG definition (yolo_ocr.json)
  - YOLO outputs `detections` array
  - OCR outputs `text` string

---

## Final API Response

```json
{
  "results": [
    {
      "frame_index": 0,
      "result": {...YOLO+OCR output...}
    },
    {
      "frame_index": 1,
      "result": {...YOLO+OCR output...}
    }
  ]
}
```

### Response Constraints

- ✅ Top-level key: `results` only
- ✅ Array of frame results
- ✅ Each item contains `frame_index` and `result`
- ❌ NO extra fields: `job_id`, `status`, `metadata`, `timestamp`, etc.

---

## Payload Flow (Example)

```
MP4 File (tiny.mp4, 3 frames)
  ↓
Frame 0 extracted → {frame_index: 0, image_bytes: b'...JPEG...'}
  ↓ (passed to yolo_ocr DAG)
  ↓
{frame_index: 0, result: {detections: [...], text: "..."})}
  ↓
[Same for frames 1, 2]
  ↓
Final response: {results: [{frame_index: 0, ...}, {frame_index: 1, ...}, ...]}
```

---

## Key Guarantees

1. **Frame Ordering**: Results always in order (frame_index 0, 1, 2, ...)
2. **No Gaps**: If frames 0-2 extracted, all 3 present in results
3. **No Duplicates**: Each frame appears exactly once
4. **Raw Bytes**: `image_bytes` is never base64 encoded
5. **Deterministic**: Same input → same output (no randomness)

---

## No State Across Frames

Each frame is processed **independently**:
- Frame 0 result does NOT depend on frame 1
- No context carried between frames
- Each frame isolated: detections, text, etc. are frame-specific

---

## Related Files

- `server/app/services/video_file_pipeline_service.py` - Implements payload creation
- `server/app/api/routes/video_file.py` - Returns response with frozen schema
- `server/app/pipelines/yolo_ocr.json` - DAG definition
