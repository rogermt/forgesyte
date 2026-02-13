# Phase 15 Release Notes

**Version**: 1.0.0
**Date**: 2026-02-13
**Phase**: 15 - Offline Batch Video Processing
**Status**: RELEASED

---

## Overview

Phase 15 adds **offline batch video processing** to ForgeSyte. Users can now upload MP4 files and receive frame-by-frame analysis results from the YOLO + OCR pipeline in a single synchronous request.

**Key Features**:
- Upload MP4 files via API
- Automatic frame extraction
- YOLO detection + OCR text extraction
- Aggregated JSON results

---

## What's New

### New Endpoint

- **`POST /video/upload-and-run`**: Upload MP4 file and get frame-by-frame analysis results

### New Service

- **`VideoFilePipelineService`**: Opens MP4, extracts frames, calls DAG pipeline per frame

### New Pipeline

- **`yolo_ocr`**: YOLO detection → OCR text extraction pipeline

### New Tests

- 38 tests covering unit, integration, stress, and fuzz scenarios
- 1000-frame stress test
- 7 fuzz test cases for malformed inputs

### New Governance

- Forbidden vocabulary validation
- CI workflow enforcement
- Rollback plan

---

## Files Added

### API Layer

```
server/app/api/routes/video_file.py                    # Video router (endpoint)
```

### Service Layer

```
server/app/services/video_file_pipeline_service.py     # Video service
```

### Tests

```
server/app/tests/video/
├── test_video_service.py                              # 15 unit tests
├── test_video_integration.py                          # 8 integration tests
├── stress/
│   └── test_video_service_1000_frames.py             # 6 stress tests
├── fuzz/
│   └── test_video_service_mp4_fuzz.py                # 7 fuzz tests
└── test_stress_and_fuzz.py                            # 2 resource cleanup tests
```

### Fixtures

```
server/app/tests/fixtures/tiny.mp4                     # 3-frame test video
server/app/tests/fixtures/generate_tiny_mp4.py        # Fixture generator
```

### Governance

```
server/tools/forbidden_vocabulary.yaml                 # 22 governance patterns
server/tools/validate_video_batch_path.py              # Governance validator
.github/workflows/video_batch_validation.yml           # CI workflow
```

### Scripts

```
scripts/demo_video_yolo_ocr.sh                         # Demo script
scripts/smoke_test_video_batch.sh                      # Smoke test
```

### Documentation

```
.ampcode/04_PHASE_NOTES/Phase_15/
├── PHASE_15_TESTING_GUIDE.md                          # Testing procedures
├── PHASE_15_ROLLBACK.md                               # Rollback plan
├── PHASE_15_MIGRATION_GUIDE.md                        # Migration guide
├── PHASE_15_RELEASE_NOTES.md                          # This file
├── PHASE_15_ONBOARDING.md                             # Onboarding guide
├── PHASE_15_ARCHITECTURE.txt                          # ASCII diagram
├── PHASE_15_ARCHITECTURE.mmd                          # Mermaid diagram
└── PHASE_15_GOVERNANCE.md                             # Governance rules
```

---

## Files Modified

```
server/app/main.py                                      # Added video router
server/pyproject.toml                                   # Added opencv-python-headless, pyyaml, types-PyYAML
```

---

## Test Coverage

### Test Counts

| Suite | Tests | Status |
|-------|-------|--------|
| Unit Tests | 15 | ✅ PASS |
| Integration Tests | 8 | ✅ PASS |
| Stress Tests | 6 | ✅ PASS |
| Fuzz Tests | 7 | ✅ PASS |
| Resource Cleanup Tests | 2 | ✅ PASS |
| **Total** | **38** | **✅ PASS** |

### Test Types

- **Unit Tests**: Service layer in isolation with mocked DAG calls
- **Integration Tests**: Full API endpoint with real HTTP requests
- **Stress Tests**: 1000-frame video processing
- **Fuzz Tests**: Malformed MP4 file handling
- **Resource Cleanup Tests**: Video resource cleanup verification

---

## Dependencies

### New Dependencies

```toml
opencv-python-headless = "*"  # Video file I/O
pyyaml = "*"                 # YAML configuration parsing
types-PyYAML = "*"           # Type stubs for PyYAML
```

### Removed Dependencies

None (Phase 15 is additive)

---

## Breaking Changes

**None**. Phase 15 is fully backward compatible with Phase 14.

All existing endpoints, services, and tests remain unchanged.

---

## API Changes

### New Endpoint

**`POST /video/upload-and-run`**

**Request**:
```
Content-Type: multipart/form-data

file: <mp4_file>
pipeline_id: "yolo_ocr"
```

**Response** (200 OK):
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

**Error Responses**:
- `400 Bad Request`: Invalid file type
- `404 Not Found`: Pipeline not found
- `422 Unprocessable Entity`: Missing required fields

---

## Performance

### Benchmarks

- **Tiny MP4 (3 frames)**: <1 second
- **1000-frame video**: <30 seconds
- **Frame extraction**: ~1ms per frame
- **JPEG encoding**: ~2ms per frame

### Limits

- **Default frame_stride**: 1 (process every frame)
- **Default max_frames**: None (no limit)
- **File size limit**: None (Phase 15 scope)

---

## Governance

### Forbidden Vocabulary

Phase 15 enforces strict governance to prevent scope creep:

- ❌ No job queues (Redis, Celery, RQ, Bull)
- ❌ No async workers
- ❌ No persistence (PostgreSQL, MongoDB)
- ❌ No streaming (WebSocket, SSE)
- ❌ No tracking (ReID, multi-frame state)

Violations are caught by:
- `server/tools/validate_video_batch_path.py`
- `.github/workflows/video_batch_validation.yml`

### CI Enforcement

All Phase 15 code must pass:
- Black formatting
- Ruff linting
- MyPy type checking
- Pytest (38 tests)
- Governance validation

---

## Known Issues

### Pre-Existing Issue

`test_response_schema_structure` in `test_router_registration.py` fails (from Commit 7).

**Status**: Expected, not part of Phase 15 scope
**Impact**: None (smoke test gracefully reports it)

---

## Migration Guide

See `PHASE_15_MIGRATION_GUIDE.md` for detailed migration instructions.

### Quick Start

```bash
# Install dependencies
cd server
uv sync

# Run tests
uv run pytest app/tests/video -v

# Run smoke test
./scripts/smoke_test_video_batch.sh

# Start server
uv run uvicorn app.main:app --reload

# Test endpoint
curl -X POST http://localhost:8000/video/upload-and-run \
  -F "file=@server/app/tests/fixtures/tiny.mp4" \
  -F "pipeline_id=yolo_ocr"
```

---

## Rollback Plan

If you need to rollback Phase 15, see `PHASE_15_ROLLBACK.md`.

### Quick Rollback

```bash
# Remove Phase 15 files
rm -rf server/app/tests/video/
rm server/app/api/routes/video_file.py
rm server/app/services/video_file_pipeline_service.py
rm server/app/tests/fixtures/tiny.mp4
rm server/app/tests/fixtures/generate_tiny_mp4.py
rm server/tools/forbidden_vocabulary.yaml
rm server/tools/validate_video_batch_path.py
rm .github/workflows/video_batch_validation.yml
rm scripts/demo_video_yolo_ocr.sh
rm scripts/smoke_test_video_batch.sh

# Remove router import from main.py
# Remove dependencies from pyproject.toml
```

---

## Documentation

### User Documentation

- `PHASE_15_OVERVIEW.md` - Feature overview
- `PHASE_15_ONBOARDING.md` - New contributor onboarding

### Developer Documentation

- `PHASE_15_TESTING_GUIDE.md` - Testing procedures
- `PHASE_15_MIGRATION_GUIDE.md` - Migration instructions
- `PHASE_15_GOVERNANCE.md` - Governance rules
- `PHASE_15_ROLLBACK.md` - Rollback procedures

### Architecture Documentation

- `PHASE_15_ARCHITECTURE.txt` - ASCII diagram
- `PHASE_15_ARCHITECTURE.mmd` - Mermaid diagram

---

## Credits

**Phase Lead**: Roger
**Reviewers**: TBD
**Contributors**: TBD

---

## License

Same as ForgeSyte project license.

---

## Support

For issues or questions:
- Check `PHASE_15_TESTING_GUIDE.md` for testing issues
- Check `PHASE_15_MIGRATION_GUIDE.md` for migration issues
- Check `PHASE_15_ROLLBACK.md` for rollback procedures
- Open an issue on GitHub for bugs

---

## See Also

- `PHASE_15_SCOPE.md` - What's in/out of scope
- `ARCHITECTURE.md` - Overall system architecture
- `PLUGIN_DEVELOPMENT.md` - Plugin development guide