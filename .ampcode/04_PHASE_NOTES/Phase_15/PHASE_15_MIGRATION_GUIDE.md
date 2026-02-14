# Phase 15 Migration Guide

**Date**: 2026-02-13
**Phase**: 15 - Offline Batch Video Processing
**Status**: FINAL

---

## Overview

This guide helps you migrate from Phase 14 to Phase 15, adding offline batch video processing capabilities to ForgeSyte.

**Scope**: Batch-only (synchronous, no async, no persistence)

---

## What's New in Phase 15

### New Endpoint

- **`POST /video/upload-and-run`**: Upload MP4 file and get frame-by-frame analysis results

### New Service

- **`VideoFilePipelineService`**: Opens MP4, extracts frames, calls DAG pipeline per frame

### New Pipeline

- **`yolo_ocr`**: YOLO detection → OCR text extraction pipeline

### New Tests

- 38 tests covering unit, integration, stress, and fuzz scenarios

### New Governance

- Forbidden vocabulary validation
- CI workflow enforcement
- Rollback plan

---

## Migration Steps

### Step 1: Install Dependencies

Phase 15 adds OpenCV for video I/O and PyYAML for governance validation.

```bash
cd server
uv sync
```

New dependencies:
- `opencv-python-headless` - Video file I/O
- `pyyaml` - YAML configuration parsing
- `types-PyYAML` - Type stubs for PyYAML

### Step 2: Verify Pipeline Exists

Ensure the `yolo_ocr` pipeline exists:

```bash
ls server/app/pipelines/yolo_ocr.json
```

If missing, the pipeline will be created during Phase 15 implementation.

### Step 3: Run Tests

Verify all tests pass:

```bash
cd server
uv run pytest app/tests/video -v
```

Expected: 38 tests PASS

### Step 4: Run Smoke Test

Verify the full integration:

```bash
./scripts/smoke_test_video_batch.sh
```

### Step 5: Start Server

Start the development server:

```bash
cd server
uv run uvicorn app.main:app --reload
```

### Step 6: Test the Endpoint

Upload a video file:

```bash
curl -X POST http://localhost:8000/video/upload-and-run \
  -F "file=@server/app/tests/fixtures/tiny.mp4" \
  -F "pipeline_id=yolo_ocr"
```

Expected response:

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
    ...
  ]
}
```

---

## API Changes

### New Endpoint

**`POST /video/upload-and-run`**

**Request**:
- `file`: MP4 file (multipart/form-data)
- `pipeline_id`: Pipeline ID (string, e.g., "yolo_ocr")

**Response**:
```json
{
  "results": [
    {
      "frame_index": int,
      "result": {
        // Pipeline-specific output
      }
    }
  ]
}
```

**Error Codes**:
- `400`: Invalid file type
- `404`: Pipeline not found
- `422`: Missing required fields

### No Breaking Changes

Phase 15 is additive. All existing Phase 14 endpoints remain unchanged.

---

## Code Changes

### New Files

```
server/app/api/routes/video_file.py                    # Video router
server/app/services/video_file_pipeline_service.py     # Video service
server/app/tests/video/                                # Video tests
  ├── test_video_service.py                            # Unit tests
  ├── test_video_integration.py                        # Integration tests
  ├── stress/
  │   └── test_video_service_1000_frames.py           # Stress tests
  ├── fuzz/
  │   └── test_video_service_mp4_fuzz.py              # Fuzz tests
  └── test_stress_and_fuzz.py                          # Resource cleanup tests
server/app/tests/fixtures/tiny.mp4                     # Test fixture
server/app/tests/fixtures/generate_tiny_mp4.py        # Fixture generator
server/tools/forbidden_vocabulary.yaml                 # Governance patterns
server/tools/validate_video_batch_path.py              # Governance validator
```

### Modified Files

```
server/app/main.py                                      # Added video router
server/pyproject.toml                                   # Added dependencies
```

---

## Migration Checklist

- [ ] Dependencies installed (opencv-python-headless, pyyaml, types-PyYAML)
- [ ] Video router exists (`server/app/api/routes/video_file.py`)
- [ ] Video service exists (`server/app/services/video_file_pipeline_service.py`)
- [ ] Video tests exist (`server/app/tests/video/`)
- [ ] Test fixture exists (`server/app/tests/fixtures/tiny.mp4`)
- [ ] Governance tooling exists (`server/tools/`)
- [ ] CI workflow exists (`.github/workflows/video_batch_validation.yml`)
- [ ] All 38 video tests pass
- [ ] Smoke test passes
- [ ] Server starts without errors
- [ ] `/video/upload-and-run` endpoint works
- [ ] No forbidden vocabulary violations

---

## Common Migration Issues

### Issue: OpenCV import error

**Solution**:
```bash
cd server
uv sync
```

### Issue: Tests fail with "tiny.mp4 not found"

**Solution**: Ensure the fixture exists:
```bash
ls server/app/tests/fixtures/tiny.mp4
```

If missing, regenerate it:
```bash
cd server/app/tests/fixtures
python generate_tiny_mp4.py
```

### Issue: Governance validation fails

**Solution**: Check for forbidden vocabulary:
```bash
cd server
uv run python tools/validate_video_batch_path.py
```

### Issue: CI workflow fails

**Solution**: Ensure all checks pass:
```bash
cd server
uv run pytest -v
uv run pre-commit run --all-files
```

---

## Rollback

If you need to rollback Phase 15, see `PHASE_15_ROLLBACK.md`.

---

## Next Steps

After successful migration:

1. **Read the onboarding guide**: `PHASE_15_ONBOARDING.md`
2. **Read the testing guide**: `PHASE_15_TESTING_GUIDE.md`
3. **Read the governance guide**: `PHASE_15_GOVERNANCE.md`
4. **Run the demo script**: `scripts/demo_video_yolo_ocr.sh`

---

## See Also

- `PHASE_15_OVERVIEW.md` - Feature overview
- `PHASE_15_SCOPE.md` - What's in/out of scope
- `PHASE_15_ONBOARDING.md` - New contributor onboarding
- `PHASE_15_TESTING_GUIDE.md` - Testing procedures
- `PHASE_15_GOVERNANCE.md` - Governance rules
- `PHASE_15_ROLLBACK.md` - Rollback procedures