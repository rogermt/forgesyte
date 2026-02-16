# Phase 17 Plans — Real-Time Streaming Inference

## ⚠️ CRITICAL: TDD MANDATE

**THERE ARE NO EXISTING TEST FAILURES.**

### TDD Workflow for Every Commit:
1. **VERIFY GREEN**: Run full test suite - all tests must pass BEFORE starting
2. **WRITE FAILING TEST**: Write test for new functionality
3. **VERIFY RED**: Run test - it MUST fail
4. **IMPLEMENT CODE**: Write minimal code to make test pass
5. **VERIFY GREEN**: Run full test suite - ALL tests must pass
6. **SAVE TEST LOGS**: Save test output to log file as proof of GREEN status
7. **COMMIT**: Only commit when ALL tests pass and test logs are saved

### Never Commit When:
- Any test is failing
- You haven't run the full test suite
- You've skipped tests without APPROVED comments
- You've used `--no-verify` to bypass hooks
- You haven't saved test logs

---

## Executive Summary

### Purpose
Phase 17 introduces a real-time streaming layer on top of the stable Phase 15/16 batch + async foundations.

### Core Change
- **From**: Jobs (long-running, persistent, asynchronous)
- **To**: Sessions (ephemeral, real-time, stateful per connection)

### Key Deliverables
- WebSocket endpoint: `/ws/video/stream`
- Session manager (one per connection)
- Real-time inference loop (frame → pipeline → result)
- Backpressure (drop frames / slow-down signals)
- Ephemeral results (no persistence, no job table)

### Non-Goals (Explicitly Out of Scope)
- Recording or storing streams
- Historical queries
- Multi-client fan-out
- GPU scheduling
- Distributed workers
- Multi-pipeline DAGs
- Authentication or rate limiting
- Any `/v1/*` endpoint additions (Phase 18 migration)

---

## Architecture Overview

### Components

#### 1. WebSocket Endpoint
- **Path**: `/ws/video/stream`
- **Protocol**: WebSocket (bidirectional)
- **Accepts**: Binary JPEG frames
- **Sends**: JSON inference results
- **Persistence**: None (ephemeral)

#### 2. Session Manager
- **File**: `server/app/services/streaming/session_manager.py`
- **Lifecycle**: Created on connect, destroyed on disconnect
- **State**: In-memory only (no database)
- **Fields**:
  - `session_id` (UUID)
  - `frame_index` (int)
  - `dropped_frames` (int)
  - `last_processed_ts` (float)
  - `backpressure_state` (enum)

#### 3. Frame Validator
- **File**: `server/app/services/streaming/frame_validator.py`
- **Purpose**: Ensure incoming frames are valid JPEG
- **Checks**:
  - JPEG SOI marker (`0xFF 0xD8`)
  - JPEG EOI marker (`0xFF 0xD9`)
  - Size limit (< 5MB)
- **Response**: Raises structured exceptions on failure

#### 4. Real-Time Inference Loop
- **Process per frame**:
  1. Validate frame
  2. Increment frame_index
  3. Apply backpressure logic
  4. Run Phase 15 pipeline
  5. Send result or drop notification
- **No persistence**
- **No queueing**

#### 5. Backpressure Mechanism
- **File**: `server/app/services/streaming/backpressure.py`
- **Strategy**: Drop frames (no queueing)
- **Trigger**: Processing time > frame interval OR dropped_frames > threshold
- **Signals**:
  - Drop: `{ "frame_index": N, "dropped": true }`
  - Slow-down: `{ "warning": "slow_down" }` (when drop rate > 30%)

#### 6. No Database Writes
- **No DuckDB writes**
- **No Alembic migrations**
- **No job table updates**
- **Fully ephemeral**

### Data Flow Diagram

```
Client → WebSocket → Session Manager → Frame Validator → Pipeline → WebSocket → Client
```

### Relationship to Phase 16
- **Phase 16**: Asynchronous jobs, persistent state, worker queue
- **Phase 17**: Real-time sessions, ephemeral state, no queue
- **Coexistence**: They operate independently without interference

---

## Folder Structure

```
server/
└── app/
    ├── api_routes/
    │   └── routes/
    │       └── video_stream.py          # NEW: WebSocket endpoint
    │
    ├── services/
    │   └── streaming/                    # NEW: Streaming services
    │       ├── __init__.py
    │       ├── session_manager.py       # NEW: Per-connection state
    │       ├── frame_validator.py       # NEW: JPEG validation
    │       └── backpressure.py          # NEW: Drop/slow-down logic
    │
    └── __init__.py
```

---

## API Contract

### WebSocket Endpoint: `/ws/video/stream`

#### Connection
```
ws://<host>/ws/video/stream?pipeline_id=<pipeline_id>
```

**Query Parameters:**
- `pipeline_id` (required): ID of the pipeline to use for inference (e.g., `yolo_ocr`)
- Validated via `VideoFilePipelineService.is_valid_pipeline()`
- Connection rejected if invalid or missing

#### Incoming Messages
- **Type**: Binary
- **Format**: JPEG bytes
- **Constraints**:
  - Max size: 5MB
  - Must contain SOI (`0xFF 0xD8`) and EOI (`0xFF 0xD9`)
  - Recommended resolution: 640×480
  - Recommended quality: 0.7-0.8

#### Outgoing Messages

##### Success Response
```json
{
  "frame_index": 42,
  "result": { ... pipeline output ... }
}
```

##### Dropped Frame
```json
{
  "frame_index": 42,
  "dropped": true
}
```

##### Slow-Down Warning
```json
{
  "warning": "slow_down"
}
```

##### Error Response
```json
{
  "error": "invalid_frame",
  "detail": "Not a valid JPEG image"
}
```

or

```json
{
  "error": "frame_too_large",
  "detail": "Frame exceeds 5MB"
}
```

or

```json
{
  "error": "invalid_pipeline",
  "detail": "Unknown pipeline_id: yolo_foo"
}
```

or

```json
{
  "error": "invalid_message",
  "detail": "Expected binary frame payload"
}
```

or

```json
{
  "error": "pipeline_failure",
  "detail": "YOLO inference failed"
}
```

or

```json
{
  "error": "internal_error",
  "detail": "Unexpected error occurred"
}
```

#### Close Conditions
- Client disconnects
- Server detects invalid frame
- Server detects frame too large
- Server detects pipeline failure
- Server detects overload (optional)

#### Session Lifecycle
```
connect → stream frames → receive results → disconnect → session destroyed
```

---

## Environment Variable Configuration

### Backpressure Thresholds

| Variable | Default | Description |
|----------|---------|-------------|
| `STREAM_DROP_THRESHOLD` | `0.10` | Drop frames when drop rate exceeds 10% |
| `STREAM_SLOWDOWN_THRESHOLD` | `0.30` | Send slow-down warning when drop rate exceeds 30% |

### Frame Size Limit

| Variable | Default | Description |
|----------|---------|-------------|
| `STREAM_MAX_FRAME_SIZE_MB` | `5` | Maximum frame size in megabytes |

### Session Limits

| Variable | Default | Description |
|----------|---------|-------------|
| `STREAM_MAX_SESSIONS` | `10` | Recommended maximum concurrent sessions (not enforced) |

### Configuration Notes

- All thresholds are configurable via environment variables
- Defaults provide deterministic behavior for testing
- Contributors can tune thresholds for different hardware
- No hard session limits enforced in code (Phase 17)
- Phase 18+ may add enforced limits

---

## User Stories (12 Commits - TDD Approach)

### Commit 1: WebSocket Router + Endpoint Skeleton

**Story**: As a backend engineer, I want a WebSocket endpoint skeleton so clients can connect to `/ws/video/stream`.

**Acceptance Criteria**:
- File: `server/app/api_routes/routes/video_stream.py`
- Defines WebSocket route: `/ws/video/stream`
- Accepts connection, logs connect/disconnect (JSON structured logs)
- Extracts `pipeline_id` from query parameters
- Validates pipeline_id via `VideoFilePipelineService.is_valid_pipeline()`
- Rejects connection if `pipeline_id` is missing or invalid
- Uses `websocket.receive()` (binary-safe API)
- No frame processing yet
- No session manager yet

**Out of Scope**:
- Frame validation
- Pipeline execution
- Backpressure
- Session state

**TDD Approach**:
1. Write test: WebSocket connection succeeds with valid pipeline_id
2. Write test: WebSocket connection logs connect event (JSON)
3. Write test: WebSocket disconnection logs disconnect event (JSON)
4. Write test: WebSocket connection fails with missing pipeline_id
5. Write test: WebSocket connection fails with invalid pipeline_id
6. Implement minimal endpoint with pipeline_id validation
7. Verify all tests pass
8. Commit

**Test File**: `server/tests/streaming/test_connect.py`

---

### Commit 2: Session Manager Class

**Story**: As a streaming engineer, I want a SessionManager so each WebSocket connection has isolated state.

**Acceptance Criteria**:
- File: `server/app/services/streaming/session_manager.py`
- Fields:
  - `session_id` (UUID)
  - `pipeline_id` (str) - from query params
  - `frame_index` (int, starts at 0)
  - `dropped_frames` (int, starts at 0)
  - `last_processed_ts` (float | None)
  - `backpressure_state` (enum: normal, warning, critical)
  - `drop_threshold` (float, from env or default 0.10)
  - `slowdown_threshold` (float, from env or default 0.30)
- Methods:
  - `increment_frame()` → increments frame_index
  - `mark_drop()` → increments dropped_frames
  - `drop_rate()` → returns float (dropped / frame_index)
  - `should_drop_frame(processing_time_ms)` → delegates to Backpressure class
  - `should_slow_down()` → delegates to Backpressure class
  - `now_ms()` → static helper for timing

**Out of Scope**:
- Pipeline execution
- WebSocket integration

**TDD Approach**:
1. Write test: SessionManager creates with correct initial state
2. Write test: `increment_frame()` increments correctly
3. Write test: `mark_drop()` increments correctly
4. Write test: `drop_rate()` calculates correctly
5. Write test: `should_drop_frame()` delegates to Backpressure
6. Write test: `should_slow_down()` delegates to Backpressure
7. Write test: Thresholds load from environment variables
8. Write test: `now_ms()` returns current time in milliseconds
9. Implement SessionManager
10. Verify all tests pass
11. Commit

**Test File**: `server/tests/streaming/test_session_manager.py`

---

### Commit 3: Frame Validator

**Story**: As a contributor, I want a frame validator to ensure incoming frames are valid JPEG.

**Acceptance Criteria**:
- File: `server/app/services/streaming/frame_validator.py`
- Function: `validate_jpeg(frame_bytes: bytes) -> None`
- Checks:
  - JPEG SOI marker (`0xFF 0xD8`)
  - JPEG EOI marker (`0xFF 0xD9`)
  - Size limit (configurable via `STREAM_MAX_FRAME_SIZE_MB`, default 5MB)
- Raises `FrameValidationError(code, detail)`:
  - `code`: "invalid_frame" or "frame_too_large"
  - `detail`: Human-readable message

**Out of Scope**:
- MP4 validation
- Pipeline execution

**TDD Approach**:
1. Write test: Valid JPEG passes validation
2. Write test: Invalid JPEG (missing SOI) raises FrameValidationError("invalid_frame", ...)
3. Write test: Invalid JPEG (missing EOI) raises FrameValidationError("invalid_frame", ...)
4. Write test: Oversized frame raises FrameValidationError("frame_too_large", ...)
5. Write test: Empty bytes raises FrameValidationError("invalid_frame", ...)
6. Write test: Size limit reads from environment variable
7. Implement validator
8. Verify all tests pass
9. Commit

**Test File**: `server/tests/streaming/test_frame_validator.py`

---

### Commit 4: Integrate SessionManager into WebSocket

**Story**: As a backend engineer, I want each WebSocket connection to create a SessionManager instance.

**Acceptance Criteria**:
- On connect → create SessionManager with pipeline_id from query params
- On disconnect → destroy SessionManager
- Store session in `websocket.state.session` (FastAPI-approved pattern)
- SessionManager receives pipeline_id

**Out of Scope**:
- Frame processing
- Backpressure

**TDD Approach**:
1. Write test: WebSocket connection creates SessionManager
2. Write test: WebSocket connection has unique session_id
3. Write test: WebSocket connection stores pipeline_id in session
4. Write test: WebSocket disconnection destroys SessionManager
5. Implement session lifecycle in endpoint
6. Verify all tests pass
7. Commit

**Test File**: `server/tests/streaming/test_connect.py` (extend existing)

---

### Commit 5: Receive Binary Frames

**Story**: As a backend engineer, I want the WebSocket to receive binary frames from the client.

**Acceptance Criteria**:
- Accept `bytes` messages only
- Reject text messages → send `{ "error": "invalid_message", "detail": "Expected binary frame payload" }` and close
- Pass frames to validator
- Increment frame_index

**Out of Scope**:
- Pipeline execution
- Backpressure

**TDD Approach**:
1. Write test: WebSocket accepts binary frame
2. Write test: WebSocket rejects text message with invalid_message error
3. Write test: WebSocket closes connection on invalid_message
4. Write test: Receiving frame increments frame_index
5. Implement message handler
6. Verify all tests pass
7. Commit

**Test File**: `server/tests/streaming/test_receive_frames.py`

---

### Commit 6: Frame Validation Integration

**Story**: As a backend engineer, I want incoming frames validated before processing.

**Acceptance Criteria**:
- Call `validate_jpeg()` on each frame
- On invalid frame → send `{ "error": "invalid_frame", "detail": "<message>" }` and close connection
- On oversized frame → send `{ "error": "frame_too_large", "detail": "<message>" }` and close connection

**Out of Scope**:
- Pipeline execution

**TDD Approach**:
1. Write test: Invalid frame sends error with detail and closes connection
2. Write test: Oversized frame sends error with detail and closes connection
3. Write test: Valid frame does not close connection
4. Integrate validator into message handler
5. Verify all tests pass
6. Commit

**Test File**: `server/tests/streaming/test_receive_frames.py` (extend existing)

---

### Commit 7: Pipeline Execution Integration

**Story**: As a backend engineer, I want each valid frame processed by the Phase 15 pipeline.

**Acceptance Criteria**:
- Extend `VideoFilePipelineService` with `run_on_frame(pipeline_id, frame_index, frame_bytes)`
- Construct Phase-15 payload:
  ```json
  {
    "frame_index": N,
    "image_bytes": <raw JPEG bytes>
  }
  ```
- Call `DagPipelineService.run_pipeline(pipeline_id, payload)`
- Return result to client:
  ```json
  { "frame_index": N, "result": {...} }
  ```

**Out of Scope**:
- Backpressure
- Multi-pipeline support

**TDD Approach**:
1. Write test: Valid frame returns result from pipeline
2. Write test: Result includes frame_index
3. Write test: Pipeline failure sends error and closes connection
4. Write test: DagPipelineService called with correct payload structure
5. Integrate pipeline execution
6. Verify all tests pass
7. Commit

**Test File**: `server/tests/streaming/test_pipeline_integration.py`

---

### Commit 8: Backpressure (Drop Frames)

**Story**: As a streaming engineer, I want to prevent overload by dropping frames when processing lags.

**Acceptance Criteria**:
- SessionManager delegates to `Backpressure.should_drop()`
- Drop threshold configurable via `STREAM_DROP_THRESHOLD` (default 0.10)
- If drop → increment dropped count, skip pipeline
- Send: `{ "frame_index": N, "dropped": true }`

**Out of Scope**:
- Slow-down signals

**TDD Approach**:
1. Write test: `should_drop_frame()` delegates to Backpressure.should_drop()
2. Write test: Dropped frame sends correct message
3. Write test: Dropped frame does not run pipeline
4. Write test: Dropped frame increments dropped count
5. Write test: Drop threshold reads from environment variable
6. Implement backpressure logic with Backpressure delegation
7. Verify all tests pass
8. Commit

**Test File**: `server/tests/streaming/test_backpressure_drop.py`

---

### Commit 9: Backpressure (Slow-Down Signal)

**Story**: As a streaming engineer, I want to notify clients when they send frames too fast.

**Acceptance Criteria**:
- SessionManager delegates to `Backpressure.should_slow_down()`
- Slow-down threshold configurable via `STREAM_SLOWDOWN_THRESHOLD` (default 0.30)
- When drop rate exceeds threshold → send: `{ "warning": "slow_down" }`

**Out of Scope**:
- Disconnecting clients

**TDD Approach**:
1. Write test: `should_slow_down()` delegates to Backpressure.should_slow_down()
2. Write test: Drop rate > threshold sends slow-down warning
3. Write test: Drop rate < threshold does not send warning
4. Write test: Slowdown threshold reads from environment variable
5. Implement slow-down signal logic with Backpressure delegation
6. Verify all tests pass
7. Commit

**Test File**: `server/tests/streaming/test_backpressure_slowdown.py`

---

### Commit 10: Error Handling + Structured Exceptions

**Story**: As a contributor, I want consistent error messages for all streaming failures.

**Acceptance Criteria**:
- Unified error format:
  ```json
  { "error": "<code>", "detail": "<message>" }
  ```
- Covers:
  - `invalid_message`
  - `invalid_frame`
  - `frame_too_large`
  - `invalid_pipeline`
  - `pipeline_failure`
  - `internal_error`
- No stack traces leaked to client
- All errors JSON-safe (per Phase-16 governance)

**Out of Scope**:
- Authentication errors (Phase 18+)

**TDD Approach**:
1. Write test: All error responses follow unified format
2. Write test: Invalid frame error includes code and detail
3. Write test: Frame too large error includes code and detail
4. Write test: Invalid message error includes code and detail
5. Write test: Invalid pipeline error includes code and detail
6. Write test: Pipeline failure error includes code and detail
7. Write test: Internal error includes code and detail
8. Implement error response formatting
9. Verify all tests pass
10. Commit

**Test File**: `server/tests/streaming/test_error_handling.py`

---

### Commit 11: Logging + Metrics Hooks

**Story**: As a maintainer, I want structured logs and metrics for streaming sessions.

**Acceptance Criteria**:
- JSON logs using Python logging + JSON formatter
- Log:
  - connect/disconnect with session_id
  - pipeline_id
  - frame_index
  - dropped frames
  - slow-down events
  - pipeline errors
- Prometheus metrics exported:
  - `stream_sessions_active` (Gauge)
  - `stream_frames_processed` (Counter)
  - `stream_frames_dropped` (Counter)
  - `stream_slowdown_signals` (Counter)
- Prometheus integration introduced in Phase 17

**TDD Approach**:
1. Write test: Connect event is logged with session_id (JSON)
2. Write test: Disconnect event is logged with session_id (JSON)
3. Write test: Frame processed event is logged (JSON)
4. Write test: Dropped frame event is logged (JSON)
5. Write test: Slow-down event is logged (JSON)
6. Write test: Pipeline error is logged (JSON)
7. Write test: Prometheus counters incremented
8. Write test: Prometheus gauge updated
9. Implement logging + metrics
10. Verify all tests pass
11. Commit

**Test File**: `server/tests/streaming/test_logging_and_metrics.py`

---

### Commit 12: Documentation + Rollback Plan

**Story**: As a contributor, I want complete Phase 17 documentation.

**Acceptance Criteria**:
- Overview document
- Architecture document
- Endpoints document
- Session model document
- Backpressure design document
- Rollback plan document
- Contributor exam document
- Release notes document

**TDD Approach**:
1. Verify all existing tests pass
2. Write documentation (no code changes)
3. Run full test suite to ensure no regressions
4. Commit documentation

**Documentation Files**:
- `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_OVERVIEW.md`
- `.ampcode/04_PHASE_NOTES/Phase_17/ARCHITECTURE.md`
- `.ampcode/04_PHASE_NOTES/Phase_17/ENDPOINTS.md`
- `.ampcode/04_PHASE_NOTES/Phase_17/SESSION_MODEL.md`
- `.ampcode/04_PHASE_NOTES/Phase_17/BACKPRESSURE_DESIGN.md`
- `.ampcode/04_PHASE_NOTES/Phase_17/ROLLBACK_PLAN.md`
- `.ampcode/04_PHASE_NOTES/Phase_17/CONTRIBUTOR_EXAM.md`
- `.ampcode/04_PHASE_NOTES/Phase_17/RELEASE_NOTES.md`

---

## Frontend User Stories (8 Commits - TDD Approach)

### FE-1: WebSocket Hook Extension (`useWebSocket`)

**Story**: As a frontend engineer, I want a WebSocket hook that can send binary JPEG frames and receive streaming inference results.

**Acceptance Criteria**:
- File: `web-ui/src/hooks/useWebSocket.ts`
- Adds support for:
  - `sendFrame(bytes: Uint8Array | ArrayBuffer): void`
  - Handling messages:
    - `{ "frame_index": N, "result": {...} }`
    - `{ "frame_index": N, "dropped": true }`
    - `{ "warning": "slow_down" }`
    - `{ "error": "<code>", "detail": "<message>" }`
- Exposes state:
  - `status: "connecting" | "connected" | "disconnected"`
  - `lastResult`
  - `droppedFrames`
  - `slowDownWarnings`
- Uses backend URL: `ws://<host>/ws/video/stream?pipeline_id=<id>`

**Out of Scope**:
- FPS throttling
- Camera capture
- Overlay rendering

**TDD Approach**:
1. Write test: sendFrame sends binary data
2. Write test: Message parser handles result messages
3. Write test: Message parser handles dropped frame messages
4. Write test: Message parser handles slow-down warnings
5. Write test: Message parser handles error messages
6. Implement useWebSocket extension
7. Verify all tests pass
8. Commit

**Test File**: `web-ui/src/hooks/useWebSocket.test.ts`

---

### FE-2: Realtime Client Integration (`useRealtime` + `RealtimeClient`)

**Story**: As a frontend engineer, I want a high-level realtime client that orchestrates WebSocket, FPS throttling, and result handling.

**Acceptance Criteria**:
- Files:
  - `web-ui/src/realtime/RealtimeClient.ts`
  - `web-ui/src/realtime/useRealtime.ts`
  - `web-ui/src/realtime/RealtimeContext.tsx`
- Responsibilities:
  - Wraps `useWebSocket`
  - Uses `FPSThrottler` from `web-ui/src/utils/FPSThrottler.ts`
  - Provides:
    - `connect(pipelineId: string)`
    - `disconnect()`
    - `sendFrame(bytes: Uint8Array)`
    - `state: { status, lastResult, droppedFrames, slowDownWarnings }`
- Integrates with `RealtimeContext.tsx` to provide context to components

**Out of Scope**:
- Camera capture
- Overlay rendering
- Error UI

**TDD Approach**:
1. Write test: RealtimeClient wraps useWebSocket
2. Write test: connect() calls WebSocket with pipeline_id
3. Write test: disconnect() closes WebSocket
4. Write test: sendFrame() delegates to useWebSocket
5. Write test: State updates on messages
6. Write test: RealtimeContext provides state to children
7. Implement RealtimeClient + useRealtime + RealtimeContext
8. Verify all tests pass
9. Commit

**Test Files**:
- `web-ui/tests/realtime/realtime_client.spec.tsx`
- `web-ui/src/realtime/useRealtime.test.ts`

---

### FE-3: Camera Capture + Streaming (`CameraPreview`)

**Story**: As a user, I want the UI to capture webcam frames and stream them to the backend in real time.

**Acceptance Criteria**:
- File: `web-ui/src/components/CameraPreview.tsx`
- Uses `getUserMedia()` to access webcam
- Renders `<video>` and `<canvas>`
- At a target FPS (10-15), captures a frame:
  - Draws video to canvas
  - Converts to JPEG (`canvas.toBlob("image/jpeg", quality)`)
  - Sends bytes via `useRealtime().sendFrame(...)`
- Reacts to:
  - `warning: "slow_down"` → reduces FPS via `FPSThrottler`
  - `dropped: true` → does not update overlay for that frame

**Out of Scope**:
- Overlay rendering
- Error handling UI
- Pipeline selection

**TDD Approach**:
1. Write test: getUserMedia is called on mount
2. Write test: Frame captured at throttled intervals
3. Write test: Frame converted to JPEG
4. Write test: sendFrame called with JPEG bytes
5. Write test: FPS reduced on slow_down warning
6. Write test: Overlay not updated on dropped frames
7. Implement CameraPreview
8. Verify all tests pass
9. Commit

**Test File**: `web-ui/src/components/CameraPreview.test.tsx`

---

### FE-4: Realtime Overlay Rendering (`RealtimeOverlay`)

**Story**: As a user, I want to see inference results overlaid on the video in real time.

**Acceptance Criteria**:
- File: `web-ui/src/components/RealtimeOverlay.tsx`
- Uses:
  - `BoundingBoxOverlay.tsx`
  - `web-ui/src/utils/drawDetections.ts`
- Renders:
  - Bounding boxes
  - Labels
  - Confidence scores
  - Frame index
- Subscribes to realtime results from `RealtimeContext`

**Out of Scope**:
- Camera capture
- Error handling UI
- Debug panel

**TDD Approach**:
1. Write test: Subscribes to RealtimeContext
2. Write test: Renders bounding boxes from result
3. Write test: Renders labels from result
4. Write test: Renders confidence scores from result
5. Write test: Renders frame index
6. Implement RealtimeOverlay
7. Verify all tests pass
8. Commit

**Test Files**:
- `web-ui/src/components/RealtimeOverlay.test.tsx`
- `web-ui/src/components/OverlayRenderer.test.tsx`

---

### FE-5: Pipeline Selection (`PipelineSelector`)

**Story**: As a user, I want to choose which pipeline to run for streaming.

**Acceptance Criteria**:
- File: `web-ui/src/components/PipelineSelector.tsx`
- Uses existing pipeline metadata from `web-ui/src/api/pipelines.ts`
- On selection change:
  - Calls `realtime.disconnect()`
  - Calls `realtime.connect(newPipelineId)`
- Shows error banner if backend returns `invalid_pipeline`

**Out of Scope**:
- Camera capture
- Overlay rendering
- Debug panel

**TDD Approach**:
1. Write test: Loads pipeline list from API
2. Write test: Renders pipeline options
3. Write test: On selection, disconnects old connection
4. Write test: On selection, connects with new pipeline_id
5. Write test: Shows error on invalid_pipeline
6. Implement PipelineSelector
7. Verify all tests pass
8. Commit

**Test File**: `web-ui/src/components/PipelineSelector.test.tsx`

---

### FE-6: Error Handling UI (`ErrorBanner`)

**Story**: As a user, I want clear error messages when streaming fails.

**Acceptance Criteria**:
- File: `web-ui/src/components/ErrorBanner.tsx`
- Displays messages for:
  - `invalid_pipeline`
  - `invalid_frame`
  - `frame_too_large`
  - `invalid_message`
  - `pipeline_failure`
  - `internal_error`
- Integrates with `RealtimeContext` to read last error
- Provides "Retry" / "Reconnect" actions

**Out of Scope**:
- Camera capture
- Overlay rendering
- Debug panel

**TDD Approach**:
1. Write test: Subscribes to RealtimeContext errors
2. Write test: Renders error message
3. Write test: Maps error codes to user-friendly messages
4. Write test: Retry button calls reconnect
5. Write test: Banner dismisses on success
6. Implement ErrorBanner
7. Verify all tests pass
8. Commit

**Test File**: `web-ui/src/components/ErrorBanner.test.tsx`

---

### FE-7: Debug / Metrics Panel (`ConfigPanel` or `StreamDebugPanel`)

**Story**: As a developer, I want a debug panel to inspect streaming performance.

**Acceptance Criteria**:
- File: `web-ui/src/components/ConfigPanel.tsx` (or `StreamDebugPanel.tsx`)
- Shows:
  - Current FPS (from `FPSThrottler` / internal state)
  - Dropped frame rate
  - Slow-down warnings count
  - WebSocket connection status
- Toggleable via a small button or config switch

**Out of Scope**:
- Camera capture
- Overlay rendering
- Error handling

**TDD Approach**:
1. Write test: Reads metrics from RealtimeContext
2. Write test: Displays current FPS
3. Write test: Displays dropped frame rate
4. Write test: Displays slow-down warnings count
5. Write test: Displays connection status
6. Write test: Toggleable visibility
7. Implement Debug Panel
8. Verify all tests pass
9. Commit

**Test File**: `web-ui/src/components/ConfigPanel.test.tsx`

---

### FE-8: MP4 Upload Fallback (Existing `useVideoProcessor`)

**Story**: As a user, I want to upload MP4 files when I can't stream live video.

**Acceptance Criteria**:
- Files:
  - `web-ui/src/hooks/useVideoProcessor.ts`
  - `web-ui/src/components/JobList.tsx`
  - `web-ui/src/components/ProgressBar.tsx`
- Confirm:
  - MP4 upload path still works with Phase-15 backend
  - No regressions introduced by Phase-17 changes
- No WebSocket changes required

**Out of Scope**:
- WebSocket streaming
- Camera capture
- Real-time overlays

**TDD Approach**:
1. Write test: MP4 upload succeeds
2. Write test: Job list renders results
3. Write test: Progress bar updates
4. Run all existing MP4 upload tests
5. Verify no regressions
6. Commit

**Test Files**:
- `web-ui/src/hooks/useVideoProcessor.test.ts`
- `web-ui/src/components/JobList.test.tsx`

---

## Backpressure Design

### Drop-Frame Algorithm

```python
def should_drop_frame(session: SessionManager) -> bool:
    # Condition 1: Processing too slow
    if session.processing_time > frame_interval:
        return True
    
    # Condition 2: Drop rate too high
    total_frames = session.frame_index + session.dropped_frames
    if total_frames > 0:
        drop_rate = session.dropped_frames / total_frames
        if drop_rate > 0.10:  # 10% threshold
            return True
    
    return False
```

### Slow-Down Signal

```python
def should_send_slow_down(session: SessionManager) -> bool:
    total_frames = session.frame_index + session.dropped_frames
    if total_frames > 0:
        drop_rate = session.dropped_frames / total_frames
        if drop_rate > 0.30:  # 30% threshold
            return session.slow_down_sent == False
    
    return False
```

### No Queueing Policy

**Phase 17 does NOT queue frames.**

Queueing breaks real-time guarantees. If frames arrive faster than processing, they are dropped.

---

## Test Strategy

### Unit Tests

#### Frame Validator Tests
- Valid JPEG passes
- Invalid JPEG (missing SOI) fails
- Invalid JPEG (missing EOI) fails
- Oversized frame fails
- Empty bytes fails

#### Session Manager Tests
- Creates with correct initial state
- `increment_frame()` works correctly
- `mark_drop()` works correctly
- `should_drop_frame()` logic correct
- `should_send_slow_down()` logic correct

#### Backpressure Tests
- Drop when processing slow
- Drop when drop rate high
- Send slow-down when drop rate > 30%
- Send slow-down only once

### Integration Tests

#### WebSocket Tests
- Connect / disconnect
- Send valid frame
- Send invalid frame
- Receive results
- Backpressure behavior
- Error handling

#### Pipeline Integration Tests
- Frame → pipeline → result
- Pipeline error propagation

### Load Tests

#### Performance Tests
- 30 FPS input
- Multiple sessions
- Backpressure activation

### Failure-Mode Tests

#### Error Scenarios
- Invalid frame
- Oversized frame
- Pipeline crash
- Client disconnect
- Server overload

---

## Performance Targets

### Latency Targets

| Stage | Target |
|-------|--------|
| Frame validation | < 2 ms |
| Pipeline inference | < 30 ms |
| WebSocket send | < 5 ms |
| Total round-trip | < 40 ms |

### Recommended Client Settings

- Resolution: **640×480**
- JPEG quality: **0.7–0.8**
- FPS: **10–15**
- Max frame size: **5MB**

### Server Throughput

- Single session: 10–20 FPS
- Multiple sessions: depends on CPU
- Backpressure triggers when:
  - Processing time > frame interval
  - Dropped frames exceed threshold

### Memory Footprint

- Session object: < 50KB
- No persistence
- No queueing of frames

---

## Security Considerations

### Frame Size Limits
- Reject frames > 5MB
- Prevent memory exhaustion

### Input Validation
- JPEG validation required
- Reject malformed frames
- Reject oversized frames

### No Persistence
- Reduces attack surface
- No stored data to exfiltrate

### Timeouts (Future)
- Idle timeout: 30s
- Hard session timeout: 10 minutes

### Rate Limits (Future)
- Phase 17 does not enforce rate limits
- Phase 18+ may add them

---

## Rollback Plan

### Remove WebSocket Endpoint
- Delete `server/app/api_routes/routes/video_stream.py`

### Remove Session Manager
- Delete `server/app/services/streaming/session_manager.py`

### Remove Frame Validator
- Delete `server/app/services/streaming/frame_validator.py`

### Remove Backpressure Logic
- Delete `server/app/services/streaming/backpressure.py`

### Remove Streaming Package
- Delete `server/app/services/streaming/__init__.py`

### Remove Tests
- Delete `server/tests/api/test_video_stream.py`
- Delete `server/tests/services/streaming/`

### Remove Documentation
- Delete `.ampcode/04_PHASE_NOTES/Phase_17/`

### No Database Changes
- No Alembic migrations to revert
- No DuckDB schema changes
- No job table changes

**Rollback is purely code removal.**

---

## Migration to Phase 18

### Phase 18 Changes

#### Namespace Migration
From:
```
/v1/video/*
/v1/health
```

To:
```
/video/*
/health
```

#### Stabilization
- CI hardening
- Forbidden vocabulary enforcement
- Documentation consolidation
- Release preparation for v1.0.0

### Migration Steps

#### Step 1: Introduce New Endpoints (Parallel)
- Add `/video/submit`
- Add `/video/status/{job_id}`
- Add `/video/results/{job_id}`
- Add `/health`
- Keep `/v1/*` active

#### Step 2: Update Tests
- Duplicate tests for new endpoints
- Keep `/v1` tests running

#### Step 3: Update CI
- Health check → `/health`
- Smoke tests → `/video/*`

#### Step 4: Update Front-End
- Upload → `/video/submit`
- Poll → `/video/status/{job_id}`

#### Step 5: Deprecation Window
- Log warnings for `/v1/*`

#### Step 6: Remove `/v1/*`
- Only after all tests migrated
- Only after all clients migrated
- Only after CI stable

### What Phase 18 Does NOT Change

- Phase 17 WebSocket endpoint stays the same
- Session model unchanged
- No GPU scheduling
- No distributed workers

### Release Target

Phase 18 concludes with:
```
ForgeSyte v1.0.0
```

- Namespace stabilized
- Docs consolidated
- CI hardened
- Public-ready

---

## Progress Tracking

### Backend Commit Checklist

- [ ] Commit 1: WebSocket Router + Endpoint Skeleton
- [ ] Commit 2: Session Manager Class
- [ ] Commit 3: Frame Validator
- [ ] Commit 4: Integrate SessionManager into WebSocket
- [ ] Commit 5: Receive Binary Frames
- [ ] Commit 6: Frame Validation Integration
- [ ] Commit 7: Pipeline Execution Integration
- [ ] Commit 8: Backpressure (Drop Frames)
- [ ] Commit 9: Backpressure (Slow-Down Signal)
- [ ] Commit 10: Error Handling + Structured Exceptions
- [ ] Commit 11: Logging + Metrics Hooks
- [ ] Commit 12: Documentation + Rollback Plan

### Frontend Commit Checklist

- [ ] FE-1: WebSocket Hook Extension (`useWebSocket`)
- [ ] FE-2: Realtime Client Integration (`useRealtime` + `RealtimeClient`)
- [ ] FE-3: Camera Capture + Streaming (`CameraPreview`)
- [ ] FE-4: Realtime Overlay Rendering (`RealtimeOverlay`)
- [ ] FE-5: Pipeline Selection (`PipelineSelector`)
- [ ] FE-6: Error Handling UI (`ErrorBanner`)
- [ ] FE-7: Debug / Metrics Panel (`ConfigPanel` or `StreamDebugPanel`)
- [ ] FE-8: MP4 Upload Fallback (Existing `useVideoProcessor`)

### Test Coverage Requirements

- [ ] Frame Validator: 100% coverage
- [ ] Session Manager: 100% coverage
- [ ] Backpressure: 100% coverage
- [ ] WebSocket Endpoint: 100% coverage
- [ ] Integration Tests: All scenarios covered
- [ ] Load Tests: Performance targets verified

### Documentation Checklist

- [ ] Overview document
- [ ] Architecture document
- [ ] Endpoints document
- [ ] Session model document
- [ ] Backpressure design document
- [ ] Rollback plan document
- [ ] Contributor exam document
- [ ] Release notes document

### Pre-Commit Verification

Before each commit, run:

```bash
# 1. Run execution governance scanner (repo root)
python scripts/scan_execution_violations.py

# 2. Run all tests
cd server && uv run pytest tests/ -v --tb=short

# 3. Run pre-commit hooks
cd server && uv run pre-commit run --all-files
```

**All three MUST PASS before committing.**

### Test Run Logging (MANDATORY)

**Every commit MUST include saved test run logs as proof of GREEN status.**

#### Backend Test Logs
Before each commit, save test output to log file:

```bash
# Run all tests and save output
cd server && uv run pytest tests/ -v --tb=short > /tmp/phase17_backend_commit_<commit_number>.log 2>&1

# Verify log shows all tests passed
grep -q "passed" /tmp/phase17_backend_commit_<commit_number>.log
```

Log file naming convention:
- `/tmp/phase17_backend_commit_01.log`
- `/tmp/phase17_backend_commit_02.log`
- ...
- `/tmp/phase17_backend_commit_12.log`

#### Frontend Test Logs
Before each commit, save test output to log file:

```bash
# Run lint and save output
cd web-ui && npm run lint > /tmp/phase17_frontend_commit_<commit_number>_lint.log 2>&1

# Run type check and save output
cd web-ui && npm run type-check > /tmp/phase17_frontend_commit_<commit_number>_typecheck.log 2>&1

# Run tests and save output
cd web-ui && npm run test -- --run > /tmp/phase17_frontend_commit_<commit_number>_test.log 2>&1
```

Log file naming convention:
- `/tmp/phase17_frontend_commit_FE1_lint.log`
- `/tmp/phase17_frontend_commit_FE1_typecheck.log`
- `/tmp/phase17_frontend_commit_FE1_test.log`
- ...

#### Log Requirements
Each log file MUST contain:
- Full test command output
- Test results showing all tests passed
- No failures, no errors
- Timestamp of test run

#### Commit Message Requirement
Each commit message MUST reference test logs:

```
Commit 1: WebSocket Router + Endpoint Skeleton

Tests passed: 1206 passed, 10 warnings
Test logs:
- /tmp/phase17_backend_commit_01.log
```

#### Log Retention
- Keep all test logs until Phase 17 is complete
- Archive logs in `.ampcode/04_PHASE_NOTES/Phase_17/test_logs/` after completion

---

---

## Success Criteria

Phase 17 is complete when:

### Backend (12 commits)
1. ✅ All 12 backend commits are completed
2. ✅ All backend tests pass (100% coverage on new code)
3. ✅ WebSocket endpoint accepts connections
4. ✅ Frames are validated and processed
5. ✅ Backpressure drops frames correctly
6. ✅ Slow-down signals sent correctly
7. ✅ Errors are handled consistently
8. ✅ Logging captures all events
9. ✅ Prometheus metrics exported
10. ✅ No existing backend tests are broken
11. ✅ Backend CI workflow passes

### Frontend (8 commits)
12. ✅ All 8 frontend commits are completed
13. ✅ All frontend tests pass (100% coverage on new code)
14. ✅ WebSocket hook sends binary frames
15. ✅ Realtime client orchestrates streaming
16. ✅ Camera preview captures and streams frames
17. ✅ Realtime overlay renders detections
18. ✅ Pipeline selector switches pipelines
19. ✅ Error banner displays errors
20. ✅ Debug panel shows metrics
21. ✅ MP4 upload still works (no regressions)
22. ✅ No existing frontend tests are broken
23. ✅ Frontend CI workflow passes

### Documentation
24. ✅ Documentation is complete
25. ✅ Rollback plan is documented

### Integration
26. ✅ End-to-end streaming works from browser to backend
27. ✅ Full CI workflow passes (backend + frontend)

### Test Log Verification
28. ✅ All 20 commits have saved test logs proving GREEN status
29. ✅ Backend test logs archived to `.ampcode/04_PHASE_NOTES/Phase_17/test_logs/`
30. ✅ Frontend test logs archived to `.ampcode/04_PHASE_NOTES/Phase_17/test_logs/`
31. ✅ Each commit message references test logs
32. ✅ Test logs show all tests passed with no failures

---

## Approval Required

**This plan is LOCKED and APPROVED for implementation.**

All Q&A clarifications have been incorporated:
- Q&A_01: WebSocket implementation, pipeline API, backpressure thresholds
- Q&A_02: Metrics system, pipeline payload, logging format, test directory
- Q&A_03: DagPipelineService signature, Prometheus integration, WebSocket APIs

### Implementation Order
1. **Backend First**: Complete all 12 backend commits (Commit 1-12)
2. **Frontend Second**: Complete all 8 frontend commits (FE-1 through FE-8)
3. **Integration Testing**: Verify end-to-end streaming works

### TDD Workflow for Each Commit
1. Verify GREEN (all tests pass)
2. Write FAILING test
3. Verify RED (test fails)
4. Implement code
5. Verify GREEN (all tests pass)
6. Commit

**Never commit when any test is failing.**

---

## Phase 17 Reference Documents

### Planning Documents
- `.ampcode/03_PLANS/Phase_17/PHASE_17_PLANS.md` (this document)
- `.ampcode/03_PLANS/Phase_17/PHASE_17_PROGRESS.md`

### Q&A Documents
- `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_Q&A _01.md`
- `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_Q&A_02.md`
- `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_Q&A_03.md`

### User Stories
- `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_BACKEND_USER_STORIES.md`
- `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_FRONTEND_USER_STORIES`

### Implementation Templates
- `.ampcode/04_PHASE_NOTES/Phase_17/FILES_06.md` (SessionManager, Backpressure, Pipeline templates)
- `.ampcode/04_PHASE_NOTES/Phase_17/FILES_07.md` (Integration test examples, Error contract, Developer FAQ)
- `.ampcode/04_PHASE_NOTES/Phase_17/FILES_08.md` (End-to-end flow, Test suite skeleton)
- `.ampcode/04_PHASE_NOTES/Phase_17/FILES_09.md` (Demo script, Test-first sequence, Onboarding)
- `.ampcode/04_PHASE_NOTES/Phase_17/FILES_FRONTEND_01.md` (Frontend architecture, Git diff plan, Integration tests)

---

## Quick Reference

### Backend Files
- `server/app/api_routes/routes/video_stream.py` (WebSocket endpoint)
- `server/app/services/streaming/session_manager.py`
- `server/app/services/streaming/frame_validator.py`
- `server/app/services/streaming/backpressure.py`
- `server/app/services/video_file_pipeline_service.py` (extended with `run_on_frame()`)

### Backend Tests
- `server/tests/streaming/test_connect.py`
- `server/tests/streaming/test_session_manager.py`
- `server/tests/streaming/test_frame_validator.py`
- `server/tests/streaming/test_receive_frames.py`
- `server/tests/streaming/test_pipeline_integration.py`
- `server/tests/streaming/test_backpressure_drop.py`
- `server/tests/streaming/test_backpressure_slowdown.py`
- `server/tests/streaming/test_error_handling.py`
- `server/tests/streaming/test_logging_and_metrics.py`

### Frontend Files
- `web-ui/src/hooks/useWebSocket.ts` (extended)
- `web-ui/src/realtime/RealtimeClient.ts`
- `web-ui/src/realtime/useRealtime.ts`
- `web-ui/src/realtime/RealtimeContext.tsx`
- `web-ui/src/components/CameraPreview.tsx`
- `web-ui/src/components/RealtimeOverlay.tsx`
- `web-ui/src/components/PipelineSelector.tsx`
- `web-ui/src/components/ErrorBanner.tsx`
- `web-ui/src/components/ConfigPanel.tsx`

### Frontend Tests
- `web-ui/src/hooks/useWebSocket.test.ts`
- `web-ui/tests/realtime/realtime_client.spec.tsx`
- `web-ui/src/realtime/useRealtime.test.ts`
- `web-ui/src/components/CameraPreview.test.tsx`
- `web-ui/src/components/RealtimeOverlay.test.tsx`
- `web-ui/src/components/PipelineSelector.test.tsx`
- `web-ui/src/components/ErrorBanner.test.tsx`
- `web-ui/src/components/ConfigPanel.test.tsx`
