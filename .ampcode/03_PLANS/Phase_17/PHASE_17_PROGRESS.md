# Phase 17 Progress Tracking

## Status: 🔒 PLAN LOCKED & APPROVED

**Last Updated**: 2026-02-15

**Implementation Ready**: All Q&A clarifications incorporated, user stories finalized, templates provided.

---

## Implementation Order

1. **Backend First**: Complete all 12 backend commits (Commit 1-12)
2. **Frontend Second**: Complete all 8 frontend commits (FE-1 through FE-8)
3. **Integration Testing**: Verify end-to-end streaming works

---

---

## Backend Commit Progress (12 Commits)

### Commit 1: WebSocket Router + Endpoint Skeleton
- [ ] Write failing tests
  - [ ] WebSocket connection succeeds with valid pipeline_id
  - [ ] WebSocket connection logs connect event (JSON)
  - [ ] WebSocket disconnection logs disconnect event (JSON)
  - [ ] WebSocket connection fails with missing pipeline_id
  - [ ] WebSocket connection fails with invalid pipeline_id
- [ ] Implement minimal endpoint with pipeline_id validation
- [ ] Verify all tests pass
- [ ] Commit

### Commit 2: Session Manager Class
- [ ] Write failing tests
  - [ ] SessionManager creates with correct initial state
  - [ ] `increment_frame()` increments correctly
  - [ ] `mark_drop()` increments correctly
  - [ ] `drop_rate()` calculates correctly
  - [ ] `should_drop_frame()` delegates to Backpressure
  - [ ] `should_slow_down()` delegates to Backpressure
  - [ ] Thresholds load from environment variables
  - [ ] `now_ms()` returns current time in milliseconds
- [ ] Implement SessionManager
- [ ] Verify all tests pass
- [ ] Commit

### Commit 3: Frame Validator
- [ ] Write failing tests
  - [ ] Valid JPEG passes validation
  - [ ] Invalid JPEG (missing SOI) raises FrameValidationError("invalid_frame", ...)
  - [ ] Invalid JPEG (missing EOI) raises FrameValidationError("invalid_frame", ...)
  - [ ] Oversized frame raises FrameValidationError("frame_too_large", ...)
  - [ ] Empty bytes raises FrameValidationError("invalid_frame", ...)
  - [ ] Size limit reads from environment variable
- [ ] Implement validator
- [ ] Verify all tests pass
- [ ] Commit

### Commit 4: Integrate SessionManager into WebSocket
- [ ] Write failing tests
  - [ ] WebSocket connection creates SessionManager
  - [ ] WebSocket connection has unique session_id
  - [ ] WebSocket connection stores pipeline_id in session
  - [ ] WebSocket disconnection destroys SessionManager
- [ ] Implement session lifecycle in endpoint
- [ ] Verify all tests pass
- [ ] Commit

### Commit 5: Receive Binary Frames
- [ ] Write failing tests
  - [ ] WebSocket accepts binary frame
  - [ ] WebSocket rejects text message with invalid_message error
  - [ ] WebSocket closes connection on invalid_message
  - [ ] Receiving frame increments frame_index
- [ ] Implement message handler
- [ ] Verify all tests pass
- [ ] Commit

### Commit 6: Frame Validation Integration
- [ ] Write failing tests
  - [ ] Invalid frame sends error with detail and closes connection
  - [ ] Oversized frame sends error with detail and closes connection
  - [ ] Valid frame does not close connection
- [ ] Integrate validator into message handler
- [ ] Verify all tests pass
- [ ] Commit

### Commit 7: Pipeline Execution Integration
- [ ] Write failing tests
  - [ ] Valid frame returns result from pipeline
  - [ ] Result includes frame_index
  - [ ] Pipeline failure sends error and closes connection
  - [ ] DagPipelineService called with correct payload structure
- [ ] Integrate pipeline execution
- [ ] Verify all tests pass
- [ ] Commit

### Commit 8: Backpressure (Drop Frames)
- [ ] Write failing tests
  - [ ] `should_drop_frame()` delegates to Backpressure.should_drop()
  - [ ] Dropped frame sends correct message
  - [ ] Dropped frame does not run pipeline
  - [ ] Dropped frame increments dropped count
  - [ ] Drop threshold reads from environment variable
- [ ] Implement backpressure logic with Backpressure delegation
- [ ] Verify all tests pass
- [ ] Commit

### Commit 9: Backpressure (Slow-Down Signal)
- [ ] Write failing tests
  - [ ] `should_slow_down()` delegates to Backpressure.should_slow_down()
  - [ ] Drop rate > threshold sends slow-down warning
  - [ ] Drop rate < threshold does not send warning
  - [ ] Slowdown threshold reads from environment variable
- [ ] Implement slow-down signal logic with Backpressure delegation
- [ ] Verify all tests pass
- [ ] Commit

### Commit 10: Error Handling + Structured Exceptions
- [ ] Write failing tests
  - [ ] All error responses follow unified format
  - [ ] Invalid frame error includes code and detail
  - [ ] Frame too large error includes code and detail
  - [ ] Invalid message error includes code and detail
  - [ ] Invalid pipeline error includes code and detail
  - [ ] Pipeline failure error includes code and detail
  - [ ] Internal error includes code and detail
- [ ] Implement error response formatting
- [ ] Verify all tests pass
- [ ] Commit

### Commit 11: Logging + Metrics Hooks
- [ ] Write failing tests
  - [ ] Connect event is logged with session_id (JSON)
  - [ ] Disconnect event is logged with session_id (JSON)
  - [ ] Frame processed event is logged (JSON)
  - [ ] Dropped frame event is logged (JSON)
  - [ ] Slow-down event is logged (JSON)
  - [ ] Pipeline error is logged (JSON)
  - [ ] Prometheus counters incremented
  - [ ] Prometheus gauge updated
- [ ] Implement logging + metrics
- [ ] Verify all tests pass
- [ ] Commit

### Commit 12: Documentation + Rollback Plan
- [ ] Verify all existing tests pass
- [ ] Write documentation (no code changes)
  - [ ] PHASE_17_OVERVIEW.md
  - [ ] ARCHITECTURE.md
  - [ ] ENDPOINTS.md
  - [ ] SESSION_MODEL.md
  - [ ] BACKPRESSURE_DESIGN.md
  - [ ] ROLLBACK_PLAN.md
  - [ ] CONTRIBUTOR_EXAM.md
  - [ ] RELEASE_NOTES.md
- [ ] Run full test suite to ensure no regressions
- [ ] Commit documentation

---

## Frontend Commit Progress (8 Commits)

### FE-1: WebSocket Hook Extension (`useWebSocket`)
- [ ] Write failing tests
  - [ ] sendFrame sends binary data
  - [ ] Message parser handles result messages
  - [ ] Message parser handles dropped frame messages
  - [ ] Message parser handles slow-down warnings
  - [ ] Message parser handles error messages
- [ ] Implement useWebSocket extension
- [ ] Verify all tests pass
- [ ] Commit

### FE-2: Realtime Client Integration (`useRealtime` + `RealtimeClient`)
- [ ] Write failing tests
  - [ ] RealtimeClient wraps useWebSocket
  - [ ] connect() calls WebSocket with pipeline_id
  - [ ] disconnect() closes WebSocket
  - [ ] sendFrame() delegates to useWebSocket
  - [ ] State updates on messages
  - [ ] RealtimeContext provides state to children
- [ ] Implement RealtimeClient + useRealtime + RealtimeContext
- [ ] Verify all tests pass
- [ ] Commit

### FE-3: Camera Capture + Streaming (`CameraPreview`)
- [ ] Write failing tests
  - [ ] getUserMedia is called on mount
  - [ ] Frame captured at throttled intervals
  - [ ] Frame converted to JPEG
  - [ ] sendFrame called with JPEG bytes
  - [ ] FPS reduced on slow_down warning
  - [ ] Overlay not updated on dropped frames
- [ ] Implement CameraPreview
- [ ] Verify all tests pass
- [ ] Commit

### FE-4: Realtime Overlay Rendering (`RealtimeOverlay`)
- [ ] Write failing tests
  - [ ] Subscribes to RealtimeContext
  - [ ] Renders bounding boxes from result
  - [ ] Renders labels from result
  - [ ] Renders confidence scores from result
  - [ ] Renders frame index
- [ ] Implement RealtimeOverlay
- [ ] Verify all tests pass
- [ ] Commit

### FE-5: Pipeline Selection (`PipelineSelector`)
- [ ] Write failing tests
  - [ ] Loads pipeline list from API
  - [ ] Renders pipeline options
  - [ ] On selection, disconnects old connection
  - [ ] On selection, connects with new pipeline_id
  - [ ] Shows error on invalid_pipeline
- [ ] Implement PipelineSelector
- [ ] Verify all tests pass
- [ ] Commit

### FE-6: Error Handling UI (`ErrorBanner`)
- [ ] Write failing tests
  - [ ] Subscribes to RealtimeContext errors
  - [ ] Renders error message
  - [ ] Maps error codes to user-friendly messages
  - [ ] Retry button calls reconnect
  - [ ] Banner dismisses on success
- [ ] Implement ErrorBanner
- [ ] Verify all tests pass
- [ ] Commit

### FE-7: Debug / Metrics Panel (`ConfigPanel` or `StreamDebugPanel`)
- [ ] Write failing tests
  - [ ] Reads metrics from RealtimeContext
  - [ ] Displays current FPS
  - [ ] Displays dropped frame rate
  - [ ] Displays slow-down warnings count
  - [ ] Displays connection status
  - [ ] Toggleable visibility
- [ ] Implement Debug Panel
- [ ] Verify all tests pass
- [ ] Commit

### FE-8: MP4 Upload Fallback (Existing `useVideoProcessor`)
- [ ] Write failing tests
  - [ ] MP4 upload succeeds
  - [ ] Job list renders results
  - [ ] Progress bar updates
  - [ ] Run all existing MP4 upload tests
- [ ] Verify no regressions
- [ ] Commit

---

## Test Coverage Progress

### Backend Unit Tests
- [ ] Frame Validator: 100% coverage
- [ ] Session Manager: 100% coverage
- [ ] Backpressure: 100% coverage

### Backend Integration Tests
- [ ] WebSocket Endpoint: 100% coverage
- [ ] Pipeline Integration: All scenarios covered

### Frontend Unit Tests
- [ ] useWebSocket: 100% coverage
- [ ] RealtimeClient: 100% coverage
- [ ] useRealtime: 100% coverage
- [ ] CameraPreview: 100% coverage
- [ ] RealtimeOverlay: 100% coverage
- [ ] PipelineSelector: 100% coverage
- [ ] ErrorBanner: 100% coverage
- [ ] ConfigPanel: 100% coverage

### Load Tests
- [ ] Performance targets verified

---

## Documentation Progress

- [ ] Overview document
- [ ] Architecture document
- [ ] Endpoints document
- [ ] Session model document
- [ ] Backpressure design document
- [ ] Rollback plan document
- [ ] Contributor exam document
- [ ] Release notes document (internal + public summary)

---

## Pre-Commit Verification Checklist

### Backend (Before each commit)
```bash
# 1. Run execution governance scanner (repo root)
python scripts/scan_execution_violations.py
# Result: ✅ PASS / ❌ FAIL

# 2. Run all tests and save log
cd server && uv run pytest tests/ -v --tb=short > /tmp/phase17_backend_commit_<N>.log 2>&1
# Result: ✅ PASS / ❌ FAIL

# 3. Verify test log shows all tests passed
grep -q "passed" /tmp/phase17_backend_commit_<N>.log
# Result: ✅ PASS / ❌ FAIL

# 4. Run pre-commit hooks
cd server && uv run pre-commit run --all-files
# Result: ✅ PASS / ❌ FAIL
```

**All four MUST PASS before committing.**
**Test log MUST be saved as proof of GREEN status.**

### Frontend (Before each commit)
```bash
# 1. Run linter and save log
cd web-ui && npm run lint > /tmp/phase17_frontend_commit_FE<N>_lint.log 2>&1
# Result: ✅ PASS / ❌ FAIL

# 2. Run type check and save log
cd web-ui && npm run type-check > /tmp/phase17_frontend_commit_FE<N>_typecheck.log 2>&1
# Result: ✅ PASS / ❌ FAIL

# 3. Run tests and save log
cd web-ui && npm run test -- --run > /tmp/phase17_frontend_commit_FE<N>_test.log 2>&1
# Result: ✅ PASS / ❌ FAIL

# 4. Verify all logs show success
grep -q "passed" /tmp/phase17_frontend_commit_FE<N>_lint.log
grep -q "passed" /tmp/phase17_frontend_commit_FE<N>_typecheck.log
grep -q "passed" /tmp/phase17_frontend_commit_FE<N>_test.log
# Result: ✅ PASS / ❌ FAIL
```

**All four MUST PASS before committing.**
**All test logs MUST be saved as proof of GREEN status.**

---

## TDD Compliance Log

### Backend Commits

#### Commit 1
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test log to `/tmp/phase17_backend_commit_01.log`
- [ ] Committed

#### Commit 2
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test log to `/tmp/phase17_backend_commit_02.log`
- [ ] Committed

#### Commit 3
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test log to `/tmp/phase17_backend_commit_03.log`
- [ ] Committed

#### Commit 4
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test log to `/tmp/phase17_backend_commit_04.log`
- [ ] Committed

#### Commit 5
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test log to `/tmp/phase17_backend_commit_05.log`
- [ ] Committed

#### Commit 6
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test log to `/tmp/phase17_backend_commit_06.log`
- [ ] Committed

#### Commit 7
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test log to `/tmp/phase17_backend_commit_07.log`
- [ ] Committed

#### Commit 8
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test log to `/tmp/phase17_backend_commit_08.log`
- [ ] Committed

#### Commit 9
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test log to `/tmp/phase17_backend_commit_09.log`
- [ ] Committed

#### Commit 10
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test log to `/tmp/phase17_backend_commit_10.log`
- [ ] Committed

#### Commit 11
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test log to `/tmp/phase17_backend_commit_11.log`
- [ ] Committed

#### Commit 12
- [ ] Verified GREEN before starting
- [ ] Wrote documentation (no code changes)
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test log to `/tmp/phase17_backend_commit_12.log`
- [ ] Committed

### Frontend Commits

#### FE-1
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test logs:
  - [ ] `/tmp/phase17_frontend_commit_FE1_lint.log`
  - [ ] `/tmp/phase17_frontend_commit_FE1_typecheck.log`
  - [ ] `/tmp/phase17_frontend_commit_FE1_test.log`
- [ ] Committed

#### FE-2
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test logs:
  - [ ] `/tmp/phase17_frontend_commit_FE2_lint.log`
  - [ ] `/tmp/phase17_frontend_commit_FE2_typecheck.log`
  - [ ] `/tmp/phase17_frontend_commit_FE2_test.log`
- [ ] Committed

#### FE-3
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test logs:
  - [ ] `/tmp/phase17_frontend_commit_FE3_lint.log`
  - [ ] `/tmp/phase17_frontend_commit_FE3_typecheck.log`
  - [ ] `/tmp/phase17_frontend_commit_FE3_test.log`
- [ ] Committed

#### FE-4
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test logs:
  - [ ] `/tmp/phase17_frontend_commit_FE4_lint.log`
  - [ ] `/tmp/phase17_frontend_commit_FE4_typecheck.log`
  - [ ] `/tmp/phase17_frontend_commit_FE4_test.log`
- [ ] Committed

#### FE-5
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test logs:
  - [ ] `/tmp/phase17_frontend_commit_FE5_lint.log`
  - [ ] `/tmp/phase17_frontend_commit_FE5_typecheck.log`
  - [ ] `/tmp/phase17_frontend_commit_FE5_test.log`
- [ ] Committed

#### FE-6
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test logs:
  - [ ] `/tmp/phase17_frontend_commit_FE6_lint.log`
  - [ ] `/tmp/phase17_frontend_commit_FE6_typecheck.log`
  - [ ] `/tmp/phase17_frontend_commit_FE6_test.log`
- [ ] Committed

#### FE-7
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test logs:
  - [ ] `/tmp/phase17_frontend_commit_FE7_lint.log`
  - [ ] `/tmp/phase17_frontend_commit_FE7_typecheck.log`
  - [ ] `/tmp/phase17_frontend_commit_FE7_test.log`
- [ ] Committed

#### FE-8
- [ ] Verified GREEN before starting
- [ ] Wrote FAILING test
- [ ] Verified RED (test failed)
- [ ] Implemented code
- [ ] Verified GREEN (all tests pass)
- [ ] Saved test logs:
  - [ ] `/tmp/phase17_frontend_commit_FE8_lint.log`
  - [ ] `/tmp/phase17_frontend_commit_FE8_typecheck.log`
  - [ ] `/tmp/phase17_frontend_commit_FE8_test.log`
- [ ] Committed

---

## Notes

### Critical Reminders
- **THERE ARE NO EXISTING TEST FAILURES**
- **START GREEN, STAY GREEN**
- **NEVER COMMIT WHEN ANY TEST IS FAILING**
- **NEVER SKIP TESTS WITHOUT APPROVED COMMENTS**
- **NEVER USE --no-verify TO BYPASS HOOKS**
- **NEVER COMMIT WITHOUT SAVING TEST LOGS AS PROOF OF GREEN STATUS**

### Test Log Verification
Every commit MUST have corresponding test logs saved to prove GREEN status:
- Backend: `/tmp/phase17_backend_commit_01.log` through `commit_12.log`
- Frontend: `/tmp/phase17_frontend_commit_FE1_lint.log`, `_typecheck.log`, `_test.log` through `FE8`

Test logs MUST contain:
- Full test command output
- Test results showing all tests passed
- No failures, no errors
- Timestamp of test run

Commit messages MUST reference test logs as proof of compliance with TDD mandate.

### TDD Workflow
1. **VERIFY GREEN**: Run full test suite - all tests must pass BEFORE starting
2. **WRITE FAILING TEST**: Write test for new functionality
3. **VERIFY RED**: Run test - it MUST fail
4. **IMPLEMENT CODE**: Write minimal code to make test pass
5. **VERIFY GREEN**: Run full test suite - ALL tests must pass
6. **SAVE TEST LOGS**: Save test output to log file as proof of GREEN status
7. **COMMIT**: Only commit when ALL tests pass and test logs are saved

---

## Overall Progress

**Backend Commits Completed**: 0/12
**Frontend Commits Completed**: 0/8
**Total Commits Completed**: 0/20
**Backend Test Coverage**: 0%
**Frontend Test Coverage**: 0%
**Documentation**: 0%
**Status**: 🔒 PLAN LOCKED & APPROVED

---

## Test Log Archive

### Backend Test Logs
All backend commit test logs will be saved to:
```
/tmp/phase17_backend_commit_01.log
/tmp/phase17_backend_commit_02.log
...
/tmp/phase17_backend_commit_12.log
```

### Frontend Test Logs
All frontend commit test logs will be saved to:
```
/tmp/phase17_frontend_commit_FE1_lint.log
/tmp/phase17_frontend_commit_FE1_typecheck.log
/tmp/phase17_frontend_commit_FE1_test.log
...
/tmp/phase17_frontend_commit_FE8_lint.log
/tmp/phase17_frontend_commit_FE8_typecheck.log
/tmp/phase17_frontend_commit_FE8_test.log
```

### Log Archive Location
After Phase 17 completion, all test logs will be archived to:
```
.ampcode/04_PHASE_NOTES/Phase_17/test_logs/
```

### Log Verification
Each commit message will reference the corresponding test logs:
```
Commit 1: WebSocket Router + Endpoint Skeleton

Tests passed: 1206 passed, 10 warnings
Test logs:
- /tmp/phase17_backend_commit_01.log
```

This provides auditable proof that all tests passed before each commit.
