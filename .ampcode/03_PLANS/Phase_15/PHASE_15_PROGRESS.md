# Phase 15 Progress Tracking

## Status
**Phase**: Implementation
**Started**: 2026-02-13
**Completed**: 0%
**Last Updated**: 2026-02-13

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
- [x] Verify all server tests pass (GREEN)
- [x] Verify all web-ui tests pass (GREEN)
- [x] Verify execution-ci workflow passes (GREEN)
- [x] Verify governance-ci workflow passes (GREEN)
- [x] Check Phase 14 completion status

## Implementation Progress (10 Commits)

### COMMIT 1: Pipeline Definition
**User Story**: Pipeline Definition
- [ ] Create `server/app/pipelines/yolo_ocr.json`
- [ ] Validate with `validate_pipelines.py`
- [ ] **Pre-commit**: Run ALL 4 test suites - must be GREEN

### COMMIT 2: Payload Contract & Scope Boundaries
**User Story**: Payload Contract & Scope Boundaries
- [ ] Define payload contract: `{frame_index, image_bytes}`
- [ ] Document scope boundaries (forbidden items)
- [ ] Response schema: `{results: [{frame_index, result}]}`
- [ ] **Pre-commit**: Run ALL 4 test suites - must be GREEN

### COMMIT 3: OpenCV Dependency + Test Fixtures + Corrupt Harness
**User Story**: OpenCV Dependency + Test Fixtures + Corrupt Harness
- [ ] Add opencv-python to dependencies
- [ ] Create `server/app/tests/fixtures/generate_tiny_mp4.py`
- [ ] Generate `server/app/tests/fixtures/tiny.mp4`
- [ ] Create corrupt MP4 generator for error testing
- [ ] **Pre-commit**: Run ALL 4 test suites - must be GREEN

### COMMIT 4: VideoFilePipelineService + Mock DAG + Pure Unit Tests
**User Story**: VideoFilePipelineService + Mock DAG + Pure Unit Tests
- [ ] Create `server/app/services/video_file_pipeline_service.py`
- [ ] Create mock DAG service for unit testing
- [ ] Create pure unit tests (no plugins)
- [ ] **Pre-commit**: Run ALL 4 test suites - must be GREEN

### COMMIT 5: Router + App Wiring + Registration Test
**User Story**: Router + App Wiring + Registration Test
- [ ] Create `server/app/api/routes/video_file.py`
- [ ] Update `server/app/main.py` to include video_file.router
- [ ] Create registration test
- [ ] **Pre-commit**: Run ALL 4 test suites - must be GREEN

### COMMIT 6: Integration Tests + Full Error Coverage
**User Story**: Integration Tests + Full Error Coverage
- [ ] Create `server/app/tests/video/test_video_upload_and_run.py`
- [ ] Create `server/app/tests/video/test_video_error_pipeline_not_found.py`
- [ ] Create `server/app/tests/video/test_video_error_invalid_file_type.py`
- [ ] Create `server/app/tests/video/test_video_error_missing_fields.py`
- [ ] Create `server/app/tests/video/test_video_error_corrupted_mp4.py`
- [ ] **Pre-commit**: Run ALL 4 test suites - must be GREEN

### COMMIT 7: Schema Regression Guard + Golden Snapshot
**User Story**: Schema Regression Guard + Golden Snapshot
- [ ] Create schema regression test
- [ ] Create golden snapshot test
- [ ] Commit golden_output.json
- [ ] **Pre-commit**: Run ALL 4 test suites - must be GREEN

### COMMIT 8: Stress + Fuzz Test Suites
**User Story**: Stress + Fuzz Test Suites
- [ ] Create stress test (1000-frame test)
- [ ] Create fuzz test
- [ ] **Pre-commit**: Run ALL 4 test suites - must be GREEN

### COMMIT 9: Governance Tooling + CI + Smoke Test
**User Story**: Governance Tooling + CI + Smoke Test
- [ ] Update forbidden_vocabulary.yaml with Phase 15 rules
- [ ] Create governance validator script
- [ ] Create `scripts/smoke_test_video_batch.sh`
- [ ] **Pre-commit**: Run ALL 4 test suites - must be GREEN

### COMMIT 10: Documentation + Demo Script + Rollback Plan
**User Story**: Documentation + Demo Script + Rollback Plan
- [ ] Update Phase 15 Overview to batch-only scope
- [ ] Create demo script for local testing
- [ ] Document rollback plan
- [ ] Final smoke test verification
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

## Governance Rules (Non-Negotiable)
1. **No phase-named files in functional directories** - Use `video/`, not `phase15/`
2. **No job queue** - Synchronous processing only
3. **No async workers** - Blocking execution
4. **No persistence** - No database writes
5. **No tracking/ReID** - Stateless per frame
6. **No streaming** - Batch processing only
7. **No state across frames** - Each frame independent
8. **Payload must have**: frame_index + image_bytes (raw JPEG, not base64)
9. **Response schema**: {results: [{frame_index, result}]} - frozen, no extra fields

## Notes
- Phase 15 is intentionally scoped to YOLO + OCR only
- No job queue, persistence, or tracking in this phase
- All governance boundaries must be respected
- **CRITICAL**: NO COMMITS until ALL 4 test suites are GREEN
- **CRITICAL**: ANY test failure requires immediate fix
- **CRITICAL**: Failure to run the tests = Immediate termination