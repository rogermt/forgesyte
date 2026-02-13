# Phase 15 Progress Tracking

## Status
**Phase**: Planning
**Started**: Not yet
**Completed**: 0%
**Last Updated**: 2026-02-12

## MANDATORY Pre-Commit Verification (ALL MUST BE GREEN BEFORE ANY COMMIT)
### Test Suite Requirements
1. **Server Tests**: ALL server tests must pass (`uv run pytest tests/`)
2. **Web-UI Tests**: ALL web-ui tests must pass (`npm run test -- --run`)
3. **Execution-CI**: Execution governance must pass (`python scripts/scan_execution_violations.py`)
4. **Governance-CI**: Phase 14 governance must pass (`python tools/validate_plugins.py && python tools/validate_pipelines.py`)

### Failure Policy
- **CRITICAL: NO COMMITS until ALL 4 test suites are GREEN, ANY test failure requires immediate fix**
- **NO COMMITS** until ALL 4 test suites are GREEN
- **ANY test failure** = Immediate fix required, no commits until fixed
- **Failure to run the tests** = Immediate termination

## Pre-Work Verification
- [ ] Verify all server tests pass (GREEN)
- [ ] Verify all web-ui tests pass (GREEN)
- [ ] Verify execution-ci workflow passes (GREEN)
- [ ] Verify governance-ci workflow passes (GREEN)
- [ ] Check Phase 14 completion status

## Implementation Progress

### Phase 1: Pipeline Definition
- [ ] Create `server/app/pipelines/yolo_ocr.json`
- [ ] **Pre-commit**: Run ALL 4 test suites - must be GREEN

### Phase 2: Service Layer
- [ ] Create `server/app/services/video_file_pipeline_service.py`
- [ ] **Pre-commit**: Run ALL 4 test suites - must be GREEN

### Phase 3: API Layer
- [ ] Create `server/app/api/routes/video_file.py`
- [ ] **Pre-commit**: Run ALL 4 test suites - must be GREEN
- [ ] Update `server/app/main.py`
- [ ] **Pre-commit**: Run ALL 4 test suites - must be GREEN

### Phase 4: Testing
- [ ] Create `server/app/tests/fixtures/generate_tiny_mp4.py`
- [ ] **Pre-commit**: Run ALL 4 test suites - must be GREEN
- [ ] Create `server/app/tests/fixtures/tiny.mp4`
- [ ] **Pre-commit**: Run ALL 4 test suites - must be GREEN
- [ ] Create `server/app/tests/video/test_video_upload_and_run.py`
- [ ] **Pre-commit**: Run ALL 4 test suites - must be GREEN
- [ ] Create `server/app/tests/video/test_invalid_pipeline.py`
- [ ] **Pre-commit**: Run ALL 4 test suites - must be GREEN
- [ ] Create `server/app/tests/video/test_invalid_file_type.py`
- [ ] **Pre-commit**: Run ALL 4 test suites - must be GREEN

## Post-Implementation Verification
- [ ] Re-run ALL 4 test suites - must be GREEN
- [ ] Run video integration tests - must pass
- [ ] Run Phase 15 smoke test - must pass

## Definition of Done Checklist
- [ ] ALL 4 test suites GREEN before any commit
- [ ] `POST /video/upload-and-run` accepts MP4 files
- [ ] Rejects invalid file types
- [ ] OpenCV successfully opens MP4
- [ ] Frames extracted sequentially
- [ ] DAG executes YOLO → OCR per frame
- [ ] Response contains aggregated results
- [ ] No job queue
- [ ] No async workers
- [ ] No persistence
- [ ] No tracking/ReID/Viz
- [ ] No streaming
- [ ] Tiny MP4 fixture exists
- [ ] Integration tests pass
- [ ] Smoke test passes
- [ ] ZERO test failures

## Notes
- Phase 15 is intentionally scoped to YOLO + OCR only
- No job queue, persistence, or tracking in this phase
- All governance boundaries must be respected
- **CRITICAL**: NO COMMITS until ALL 4 test suites are GREEN
- **CRITICAL**: ANY test failure requires immediate fix
- **CRITICAL**: Failure to run the tests = Immediate termination
