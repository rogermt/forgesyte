# Phase 15 Implementation Plans

## Overview
Phase 15 extends Phase 14's single-frame DAG execution to support **offline MP4 processing** using **YOLO + OCR** pipeline only.

## Scope
- **IN**: MP4 upload, frame extraction, YOLO→OCR DAG per frame, aggregated results
- **OUT**: Job queue, persistence, tracking, ReID, Viz, streaming

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

## Implementation Tasks

### Phase 1: Pipeline Definition
1. Create `server/app/pipelines/yolo_ocr.json`
   - Define YOLO → OCR DAG
   - Ensure type compatibility
   - Validate with `validate_pipelines.py`
   - **Pre-commit**: Run ALL 4 test suites - must be GREEN

### Phase 2: Service Layer
2. Create `server/app/services/video_file_pipeline_service.py`
   - `VideoFilePipelineService` class
   - Frame extraction using OpenCV
   - Per-frame DAG execution via `DagPipelineService`
   - Results aggregation
   - Support for `frame_stride` and `max_frames` options
   - **Pre-commit**: Run ALL 4 test suites - must be GREEN

### Phase 3: API Layer
3. Create `server/app/api/routes/video_file.py`
   - `POST /video/upload-and-run` endpoint
   - Multipart file upload handling
   - Pipeline_id validation
   - Content-type validation (MP4/QuickTime)
   - Temp file management
   - Error handling
   - **Pre-commit**: Run ALL 4 test suites - must be GREEN

4. Update `server/app/main.py`
   - Include `video_file.router`
   - **Pre-commit**: Run ALL 4 test suites - must be GREEN

### Phase 4: Testing
5. Create `server/app/tests/fixtures/generate_tiny_mp4.py`
   - Generate 1-3 frame MP4 fixture
   - Solid-color frames with frame index text
   - **Pre-commit**: Run ALL 4 test suites - must be GREEN

6. Create `server/app/tests/fixtures/tiny.mp4`
   - Pre-generated test fixture
   - **Pre-commit**: Run ALL 4 test suites - must be GREEN

7. Create `server/app/tests/video/test_video_upload_and_run.py`
   - Integration test for MP4 upload and run
   - Validate response format
   - Validate per-frame results
   - **Pre-commit**: Run ALL 4 test suites - must be GREEN

8. Create `server/app/tests/video/test_invalid_pipeline.py`
   - Test invalid pipeline_id handling
   - **Pre-commit**: Run ALL 4 test suites - must be GREEN

9. Create `server/app/tests/video/test_invalid_file_type.py`
   - Test invalid file type handling
   - **Pre-commit**: Run ALL 4 test suites - must be GREEN

## Post-Implementation Verification
- [ ] Re-run ALL 4 test suites - must be GREEN
- [ ] Run video integration tests - must pass
- [ ] Run Phase 15 smoke test - must pass

## Success Criteria
✅ ALL 4 test suites GREEN before any commit
✅ `POST /video/upload-and-run` works
✅ YOLO→OCR pipeline validates and executes
✅ Per-frame DAG execution works
✅ Results aggregated correctly
✅ ZERO test failures

## Timeline
15-20 hours (7-10 commits per PHASE_15_COMMITS.md)

## References
- `PHASE_15_SCOPE.md` - Scope boundaries
- `PHASE_15_DEFINITION_OF_DONE.md` - Definition of done
- `PHASE_15_FIRST_FAILING_TEST.md` - First failing test
- `PHASE_15_FORBIDDEN_VOCAB.md` - Forbidden vocabulary and governance rules
- `PHASE_15_NOTES_01.md` - Tiny MP4 generator, payload contract, README, governance
- `PHASE_15_NOTES_02.md` - Integration tests, architecture, PR template
- `PHASE_15_NOTEs_03.md` - Migration guide, release notes, onboarding
- `PHASE_15_NOTES_04.md` - Architecture diagram, demo script, project board
- `PHASE_15_OCR_&_YOLO_JSON.md` - Valid YOLO+OCR pipeline examples
- `PHASE_15_OVERVIEW.md` - High-level overview
- `PHASE_15_SPEC.md` - MP4 upload spec
- `PHAASE_15_PR_GITHUB_SEQUENCE.md` - PR sequence
- `PHASE_15_COMMITS.md` - Commit strategy
