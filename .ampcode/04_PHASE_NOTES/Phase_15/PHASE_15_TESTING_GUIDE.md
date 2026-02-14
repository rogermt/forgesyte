# Phase 15 Testing Guide

**Date**: 2026-02-13
**Phase**: 15 - Offline Batch Video Processing
**Status**: FINAL

---

## Overview

This guide documents how to run all tests for Phase 15 video batch processing, including unit tests, integration tests, stress tests, fuzz tests, and the smoke test.

---

## Test Structure

```
server/app/tests/video/
├── test_video_service.py          # Unit tests (15 tests)
├── test_video_integration.py      # Integration tests (8 tests)
├── stress/
│   └── test_video_service_1000_frames.py  # Stress tests (6 tests)
├── fuzz/
│   └── test_video_service_mp4_fuzz.py     # Fuzz tests (7 tests)
└── test_stress_and_fuzz.py        # Resource cleanup tests (2 tests)
```

**Total**: 38 tests (all PASS)

---

## Running Tests

### Prerequisites

```bash
cd server
uv sync  # Ensure dependencies are installed
```

### Run All Video Tests

```bash
cd server
uv run pytest app/tests/video -v
```

### Run Specific Test Suites

```bash
# Unit tests only
uv run pytest app/tests/video/test_video_service.py -v

# Integration tests only
uv run pytest app/tests/video/test_video_integration.py -v

# Stress tests only
uv run pytest app/tests/video/stress/ -v

# Fuzz tests only
uv run pytest app/tests/video/fuzz/ -v

# Resource cleanup tests
uv run pytest app/tests/video/test_stress_and_fuzz.py -v
```

### Run a Single Test

```bash
# Run one specific test
uv run pytest app/tests/video/test_video_service.py::test_process_video_success -v

# Run all tests matching a pattern
uv run pytest app/tests/video -k "process_video" -v
```

---

## Test Descriptions

### Unit Tests (`test_video_service.py`)

Tests the `VideoFilePipelineService` in isolation with mocked DAG calls.

| Test | Description |
|------|-------------|
| `test_process_video_success` | Successful processing of 3-frame video |
| `test_process_video_with_stride` | Frame stride filtering (every 2nd frame) |
| `test_process_video_with_max_frames` | Max frames limit |
| `test_process_video_with_stride_and_max_frames` | Combined stride + max_frames |
| `test_process_video_empty_video` | Empty video (0 frames) |
| `test_process_video_invalid_file` | Invalid/missing MP4 file |
| `test_frame_payload_structure` | Payload has frame_index + image_bytes |
| `test_frame_encoding_jpeg` | Frames encoded as JPEG |
| `test_results_ordered_by_frame_index` | Results in correct order |
| `test_dag_error_propagates` | DAG errors propagate correctly |
| `test_pipeline_not_found` | Pipeline not found error |
| `test_video_release_on_success` | Video resource cleanup on success |
| `test_video_release_on_error` | Video resource cleanup on error |
| `test_frame_index_in_payload` | frame_index included in payload |
| `test_image_bytes_in_payload` | image_bytes included in payload |

### Integration Tests (`test_video_integration.py`)

Tests the full API endpoint with real HTTP requests.

| Test | Description |
|------|-------------|
| `test_upload_and_run_success` | Valid MP4 + yolo_ocr → 200 OK |
| `test_upload_and_run_invalid_file_type` | Wrong file type → 400 |
| `test_upload_and_run_missing_file` | No file uploaded → 422 |
| `test_upload_and_run_missing_pipeline_id` | No pipeline_id → 422 |
| `test_upload_and_run_invalid_pipeline` | Invalid pipeline → 404 |
| `test_upload_and_run_response_structure` | Response has correct schema |
| `test_upload_and_run_empty_video` | Empty MP4 → empty results |
| `test_upload_and_run_yolo_ocr_pipeline` | YOLO + OCR pipeline works |

### Stress Tests (`stress/test_video_service_1000_frames.py`)

Tests large-scale processing with 1000 frames.

| Test | Description |
|------|-------------|
| `test_1000_frames_sequential` | Process all 1000 frames sequentially |
| `test_1000_frames_stride_2` | Process 500 frames (stride 2) |
| `test_1000_frames_max_100` | Process only first 100 frames |
| `test_1000_frames_ordered` | Results ordered by frame_index |
| `test_1000_frames_no_gaps` | No gaps in frame indices |
| `test_1000_frames_no_duplicates` | No duplicate frame indices |

**Performance**: All tests complete in <30 seconds.

### Fuzz Tests (`fuzz/test_video_service_mp4_fuzz.py`)

Tests malformed MP4 files for graceful error handling.

| Test | Description |
|------|-------------|
| `test_fuzz_128b_random` | 128 bytes random data |
| `test_fuzz_1kb_random` | 1KB random data |
| `test_fuzz_header_only` | MP4 header only (truncated) |
| `test_fuzz_truncated` | Truncated MP4 file |
| `test_fuzz_empty` | Empty file |
| `test_fuzz_zeros` | All zeros |
| `test_fuzz_exception_safety` | Exception safety during processing |

**Expected Behavior**: All cases return `[]` or raise `ValueError` (no crashes/hangs).

### Resource Cleanup Tests (`test_stress_and_fuzz.py`)

Tests that video resources are properly released.

| Test | Description |
|------|-------------|
| `test_video_resource_cleanup_after_stress` | Cleanup after 1000-frame test |
| `test_video_resource_cleanup_after_fuzz` | Cleanup after fuzz tests |

---

## Smoke Test

The smoke test runs the full test suite with `--maxfail=1` to catch any failures early.

```bash
./scripts/smoke_test_video_batch.sh
```

The smoke test runs:
1. Validate plugins
2. Validate pipelines
3. Validate video batch path (governance check)
4. Run pytest with `--maxfail=1`

**Note**: The smoke test gracefully reports the pre-existing `test_response_schema_structure` failure in `test_router_registration.py` (from Commit 7). This is expected and not part of Phase 15 scope.

---

## Golden Snapshot Regeneration

Golden snapshots are stored in `.ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_GOLDEN_BUNDLE/`.

### When to Regenerate

Regenerate golden snapshots **only** when:
1. The YOLO model version changes
2. The OCR model version changes
3. The pipeline definition (`yolo_ocr.json`) changes
4. The fixture `tiny.mp4` changes

**DO NOT regenerate** for:
- Code refactoring that doesn't change output
- Test infrastructure changes
- Documentation updates

### Regeneration Procedure

1. **Backup existing golden bundle**:
   ```bash
   cp -r .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_GOLDEN_BUNDLE \
          .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_GOLDEN_BUNDLE.backup
   ```

2. **Run golden snapshot test**:
   ```bash
   cd server
   uv run pytest app/tests/video/test_video_integration.py::test_upload_and_run_yolo_ocr_pipeline -v
   ```

3. **If test fails due to output changes**:
   - Review the diff to ensure changes are intentional
   - Update the golden snapshot file with new output
   - Document the reason for the change in commit message

4. **Commit changes**:
   ```bash
   git add .ampcode/04_PHASE_NOTES/Phase_15/PHASE_15_GOLDEN_BUNDLE/
   git commit -m "test(golden): regenerate snapshots for model version X.Y.Z"
   ```

### Golden Snapshot Files

```
PHASE_15_GOLDEN_BUNDLE/
├── yolo_ocr_tiny.mp4.output.json  # Expected output for tiny.mp4
└── README.md                       # Metadata about the snapshot
```

---

## Test Coverage

Phase 15 achieves comprehensive test coverage:

- **Unit tests**: 15 tests covering all service methods
- **Integration tests**: 8 tests covering all API endpoints
- **Stress tests**: 6 tests covering large-scale processing
- **Fuzz tests**: 7 tests covering malformed inputs
- **Resource tests**: 2 tests covering cleanup

**Total**: 38 tests, 100% PASS

---

## Common Issues

### Issue: Tests fail with "Module not found"

**Solution**:
```bash
cd server
uv sync
```

### Issue: Tests fail with "YOLO plugin not found"

**Solution**: This is expected in CPU-only dev environments. The smoke test gracefully handles this.

### Issue: Golden snapshot test fails

**Solution**: Follow the regeneration procedure above. Only regenerate if model/pipeline changed.

### Issue: Stress tests timeout

**Solution**: Ensure OpenCV is properly installed and can read MP4 files.

---

## CI Integration

All tests run automatically in CI via:
- `.github/workflows/ci.yml` - Main CI workflow
- `.github/workflows/video_batch_validation.yml` - Phase 15 governance workflow

Both workflows must pass before merging to `main`.

---

## See Also

- `PHASE_15_SCOPE.md` - What's in/out of scope
- `PHASE_15_GOVERNANCE.md` - Governance rules
- `scripts/smoke_test_video_batch.sh` - Smoke test script