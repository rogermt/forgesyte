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
- WebSocket endpoint: `/ws/video/stream` ✅ COMPLETE
- Session manager (one per connection) ✅ COMPLETE
- Real-time inference loop (frame → pipeline → result) ✅ COMPLETE
- Backpressure (drop frames / slow-down signals) ✅ COMPLETE
- Ephemeral results (no persistence, no job table) ✅ COMPLETE
- Frontend client integration 🚀 READY TO START

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

## Current Status

**Backend**: 12/12 commits completed (100%) ✅  
**Frontend**: 0/8 commits completed (0%) - READY TO START 🚀  
**Documentation**: 100% complete  
**Total Progress**: 12/20 commits (60%)

### What's Complete ✅
- All backend WebSocket streaming infrastructure
- Session management
- Frame validation
- Pipeline integration
- Backpressure mechanism
- Error handling
- Logging and metrics
- All documentation

### What's Next 🚀
- Frontend WebSocket client integration
- Camera capture and streaming
- Real-time overlay rendering
- Pipeline selection UI
- Error handling UI
- Debug/metrics panel
- MP4 upload fallback verification

---

## Architecture Overview

### Components

#### 1. WebSocket Endpoint ✅
- **Path**: `/ws/video/stream`
- **Protocol**: WebSocket (bidirectional)
- **Accepts**: Binary JPEG frames
- **Sends**: JSON inference results
- **Persistence**: None (ephemeral)

#### 2. Session Manager ✅
- **File**: `server/app/services/streaming/session_manager.py`
- **Lifecycle**: Created on connect, destroyed on disconnect
- **State**: In-memory only (no database)
- **Fields**:
  - `session_id` (UUID)
  - `frame_index` (int)
  - `dropped_frames` (int)
  - `last_processed_ts` (float)
  - `backpressure_state` (enum)

#### 3. Frame Validator ✅
- **File**: `server/app/services/streaming/frame_validator.py`
- **Purpose**: Ensure incoming frames are valid JPEG
- **Checks**:
  - JPEG SOI marker (`0xFF 0xD8`)
  - JPEG EOI marker (`0xFF 0xD9`)
  - Size limit (< 5MB)
- **Response**: Raises structured exceptions on failure

#### 4. Real-Time Inference Loop ✅
- **Process per frame**:
  1. Validate frame
  2. Increment frame_index
  3. Apply backpressure logic
  4. Run Phase 15 pipeline
  5. Send result or drop notification
- **No persistence**
- **No queueing**

#### 5. Backpressure Mechanism ✅
- **File**: `server/app/services/streaming/backpressure.py`
- **Strategy**: Drop frames (no queueing)
- **Trigger**: Processing time > frame interval OR dropped_frames > threshold
- **Signals**:
  - Drop: `{ "frame_index": N, "dropped": true }`
  - Slow-down: `{ "warning": "slow_down" }` (when drop rate > 30%)

#### 6. No Database Writes ✅
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

## Backend User Stories (12 Commits - ALL COMPLETE ✅)

### Commit 1: WebSocket Router + Endpoint Skeleton ✅
- File: `server/app/api_routes/routes/video_stream.py`
- WebSocket route: `/ws/video/stream`
- Pipeline_id validation
- JSON structured logging
- **Status**: Complete (5/5 tests passing)

### Commit 2: Session Manager Class ✅
- File: `server/app/services/streaming/session_manager.py`
- Per-connection state management
- Frame tracking
- Drop rate calculation
- **Status**: Complete (9/9 tests passing)

### Commit 3: Frame Validator ✅
- File: `server/app/services/streaming/frame_validator.py`
- JPEG SOI/EOI marker validation
- Size limit enforcement
- Structured exceptions
- **Status**: Complete (6/6 tests passing)

### Commit 4: Integrate SessionManager into WebSocket ✅
- Session lifecycle management
- Unique session_id per connection
- **Status**: Complete (4/4 tests passing)

### Commit 5: Receive Binary Frames ✅
- Binary frame acceptance
- Text message rejection
- **Status**: Complete (4/4 tests passing)

### Commit 6: Frame Validation Integration ✅
- Frame validation in message handler
- Error responses
- **Status**: Complete (3/3 tests passing)

### Commit 7: Pipeline Execution Integration ✅
- Phase-15 pipeline integration
- Payload construction
- Result handling
- **Status**: Complete (4/4 tests passing)

### Commit 8: Backpressure (Drop Frames) ✅
- Drop decision logic
- Dropped frame notifications
- **Status**: Complete (5/5 tests passing)

### Commit 9: Backpressure (Slow-Down Signal) ✅
- Slow-down warning logic
- Threshold-based signaling
- **Status**: Complete (4/4 tests passing)

### Commit 10: Error Handling + Structured Exceptions ✅
- Unified error format
- All error codes covered
- JSON-safe responses
- **Status**: Complete (7/7 tests passing)

### Commit 11: Logging + Metrics Hooks ✅
- JSON structured logging
- Prometheus metrics
- Session tracking
- **Status**: Complete (8/8 tests passing)

### Commit 12: Documentation + Rollback Plan ✅
- Complete documentation set
- Rollback procedures
- **Status**: Complete (60/60 tests passing)

---

## Frontend User Stories (8 Commits - READY TO START 🚀)

### ✅ All Frontend User Stories Fully Specified

All 8 frontend user stories have been fully specified with:
- Complete acceptance criteria
- Concrete implementation details from Q&A
- Code skeletons with exact file paths and API signatures
- Test skeletons for all components

**Reference Documents**:
- User Stories: `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_FRONTEND_USER_STORIES`
- Q&A Clarifications: `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_FE_Q&A_01.md`
- Code Skeletons: `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_CODE_SKELETONS.md`

### FE-1: WebSocket Hook Extension (`useWebSocket`) 🚀

**Story**: As a frontend engineer, I want a WebSocket hook that can send binary JPEG frames and receive streaming inference results.

**Acceptance Criteria**:
- File: `web-ui/src/hooks/useWebSocket.ts`
- **Extends existing hook** (not create new)
- Adds support for:
  - `sendFrame(bytes: Uint8Array | ArrayBuffer): void`
  - Handling messages:
    - `{ "frame_index": N, "result": {...} }`
    - `{ "frame_index": N, "dropped": true }`
    - `{ "warning": "slow_down" }`
    - `{ "error": "<code>", "detail": "<message>" }`
- Exposes state:
  - `status: "connecting" | "connected" | "disconnected"`
  - `lastResult: StreamingResultPayload | null`
  - `droppedFrames: number` (count)
  - `slowDownWarnings: number` (count)
  - `lastError: StreamingErrorPayload | null`
- Uses backend URL: `ws://<host>/ws/video/stream?pipeline_id=<id>`
- Uses shared types from `src/realtime/types.ts`
- Message detection via key-based parsing

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

**Implementation Details**:
- Extend existing `useWebSocket` hook
- Add `handleMessage` with key-based detection
- Add `sendFrame` that sends binary data
- State fields: `lastResult`, `droppedFrames`, `slowDownWarnings`, `lastError`

---

### FE-2: Realtime Client Integration (`useRealtime` + `RealtimeClient`) 🚀

**Story**: As a frontend engineer, I want a high-level realtime client that orchestrates WebSocket, FPS throttling, and result handling.

**Acceptance Criteria**:
- Files:
  - `web-ui/src/realtime/RealtimeClient.ts`
  - `web-ui/src/realtime/useRealtime.ts`
  - `web-ui/src/realtime/RealtimeContext.tsx`
- **Extends existing** `RealtimeClient` (no new client)
  - Adds `sendFrame(bytes: Uint8Array): void`
  - Uses `useWebSocket` under the hood
- `useRealtime` provides:
  - `connect(pipelineId: string)`
  - `disconnect()`
  - `sendFrame(bytes: Uint8Array)`
  - `state: { status, lastResult, droppedFrames, slowDownWarnings, lastError }`
- **Extends existing** `RealtimeContext` with streaming fields
- Integrates `FPSThrottler` for FPS control:
  - Initial FPS: **15**
  - On `slow_down`: reduce to **5 FPS** via `throttler.setMaxFps(5)`
- Uses `requestAnimationFrame` + `FPSThrottler` for capture loop

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

**Implementation Details**:
- Extend existing `RealtimeClient` with `sendFrame()` method
- Extend existing `RealtimeContext` with streaming state fields
- Use `requestAnimationFrame` loop with `FPSThrottler.throttle()`
- FPS values: 15 FPS initial, 5 FPS on `slow_down`

---

### FE-3: Camera Capture + Streaming (`CameraPreview`) 🚀

**Story**: As a user, I want the UI to capture webcam frames and stream them to the backend in real time.

**Acceptance Criteria**:
- File: `web-ui/src/components/CameraPreview.tsx`
- Uses `navigator.mediaDevices.getUserMedia` to access webcam
- Renders `<video>` and `<canvas>`
- Uses `requestAnimationFrame` + `FPSThrottler` to control FPS (start at 15 FPS)
- For each frame:
  - Draws video to canvas
  - Converts to JPEG via `canvas.toBlob("image/jpeg", 0.8)`
  - Converts blob to `Uint8Array`:
    ```typescript
    canvas.toBlob(async (blob) => {
      if (!blob) return;
      const arrayBuffer = await blob.arrayBuffer();
      const uint8Array = new Uint8Array(arrayBuffer);
      sendFrame(uint8Array);
    }, "image/jpeg", 0.8);
    ```
  - Calls `realtime.sendFrame(uint8Array)`
- Reacts to `slow_down` by reducing FPS via `throttler.setMaxFps(5)`
- Does not update overlay for frames marked as dropped

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

**Implementation Details**:
- Binary conversion: `canvas.toBlob()` → `arrayBuffer` → `Uint8Array`
- Use `FPSThrottler.throttle()` in `requestAnimationFrame` loop
- Frame index stored in `lastResult.frame_index`
- FPS throttling: 15 FPS initial, 5 FPS on `slow_down`

---

### FE-4: Realtime Overlay Rendering (`RealtimeOverlay`) 🚀

**Story**: As a user, I want to see inference results overlaid on the video in real time.

**Acceptance Criteria**:
- File: `web-ui/src/components/RealtimeOverlay.tsx`
- Uses:
  - `BoundingBoxOverlay.tsx`
  - `web-ui/src/utils/drawDetections.ts`
  - `RealtimeContext`
- Defines `Detection` type and converter in `src/realtime/types.ts`:
  ```typescript
  export type Detection = {
    x: number;
    y: number;
    width: number;
    height: number;
    label: string;
    confidence?: number;
  };

  export function toDetections(result: any): Detection[] {
    if (!result || !Array.isArray(result.detections)) return [];
    return result.detections.map((d: any) => ({
      x: d.x,
      y: d.y,
      width: d.w,
      height: d.h,
      label: d.label,
      confidence: d.score,
    }));
  }
  ```
- Assumes backend returns:
  ```json
  {
    "result": {
      "detections": [
        { "x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4, "label": "person", "score": 0.92 }
      ]
    }
  }
  ```
- Converts backend `result` into `Detection[]` and passes to overlay renderer
- Displays `frame_index` as a small label in the corner of the overlay

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

**Implementation Details**:
- Backend format: `{ result: { detections: [{x, y, w, h, label, score}] } }`
- Converter: `toDetections()` maps `w`→`width`, `h`→`height`, `score`→`confidence`
- Frame index displayed as small label in corner

---

### FE-5: Pipeline Selection (`PipelineSelector`) 🚀

**Story**: As a user, I want to choose which pipeline to run for streaming.

**Acceptance Criteria**:
- File: `web-ui/src/components/PipelineSelector.tsx`
- **Reuses existing dropdown UI** (no redesign)
- Uses pipeline metadata from `web-ui/src/api/pipelines.ts`
- On selection change:
  - Calls `realtime.disconnect()`
  - Calls `realtime.connect(newPipelineId)`
- If backend returns `invalid_pipeline`, `RealtimeContext` sets `lastError`, and `ErrorBanner` displays it
- Uses existing `ErrorBanner` in main layout

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

**Implementation Details**:
- Keep existing dropdown UI
- Error banner integration via `RealtimeContext`
- Connect/disconnect on selection change

---

### FE-6: Error Handling UI (`ErrorBanner`) 🚀

**Story**: As a user, I want clear error messages when streaming fails.

**Acceptance Criteria**:
- File: `web-ui/src/components/ErrorBanner.tsx`
- Uses `RealtimeContext` to read `lastError` (`{ code, detail }`)
- Maps error codes to user-friendly messages:
  ```typescript
  const ERROR_MESSAGES: Record<string, string> = {
    invalid_pipeline: "The selected pipeline is not available.",
    invalid_frame: "The video frame could not be processed.",
    frame_too_large: "The video frame is too large.",
    invalid_message: "The server received an unexpected message.",
    pipeline_failure: "The pipeline failed while processing your video.",
    internal_error: "An internal error occurred. Please try again.",
  };
  ```
- Provides a single "Retry"/"Reconnect" action that:
  - Clears error
  - Reconnects with current pipeline
- Error structure: `{ code: string; detail: string }`

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

**Implementation Details**:
- All 6 error codes mapped to user-friendly messages
- Error structure: `{ code: string; detail: string }`
- Single Retry button that clears error and reconnects

---

### FE-7: Debug / Metrics Panel (`StreamDebugPanel`) 🚀

**Story**: As a developer, I want a debug panel to inspect streaming performance and connection state.

**Acceptance Criteria**:
- File: `web-ui/src/components/StreamDebugPanel.tsx` (new component)
- Uses `RealtimeContext` to read:
  - `status`
  - `droppedFrames`
  - `slowDownWarnings`
  - `lastResult` (for frame_index)
- Maintains simple metrics in `useRealtime`:
  - `framesSent`
  - `startTime` → derive approximate FPS = `framesSent / elapsedSeconds`
  - Dropped frame rate = `droppedFrames / framesSent`
- Panel shows:
  - Connection status
  - Approx FPS
  - Dropped frame count and rate
  - Slow-down warnings count
- Toggle button (e.g. "Debug") in main layout to show/hide panel

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

**Test File**: `web-ui/src/components/StreamDebugPanel.test.tsx`

**Implementation Details**:
- New component: `StreamDebugPanel.tsx`
- Metrics: FPS = `framesSent / elapsedSeconds`, drop rate = `droppedFrames / framesSent`
- Toggle button: Small "Debug" button in main layout

---

### FE-8: MP4 Upload Fallback (Existing `useVideoProcessor`) 🚀

**Story**: As a user, I want to upload MP4 files when I can't stream live video.

**Acceptance Criteria**:
- Files:
  - `web-ui/src/hooks/useVideoProcessor.ts`
  - `web-ui/src/components/JobList.tsx`
  - `web-ui/src/components/ProgressBar.tsx`
- **No behavioral changes required** for Phase-17
- Confirm existing tests still pass:
  - `useVideoProcessor.test.ts`
  - `JobList.test.tsx`
- Ensure Phase-17 streaming changes do not break MP4 upload flow

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

**Implementation Details**:
- No code changes required
- Only verify existing tests pass
- Test files specified for regression checking

---

## API Contract

### WebSocket Endpoint: `/ws/video/stream` ✅

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

## Performance Targets

| Stage | Target |
|-------|--------|
| Frame validation | < 2 ms |
| Pipeline inference | < 30 ms |
| WebSocket send | < 5 ms |

At 30 FPS, each frame has ~33 ms available. The total target is within budget.

---

## Reference Documents

### Backend Documentation
- `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_OVERVIEW.md`
- `.ampcode/04_PHASE_NOTES/Phase_17/ENDPOINTS.md`
- `.ampcode/04_PHASE_NOTES/Phase_17/SESSION_MODEL.md`
- `.ampcode/04_PHASE_NOTES/Phase_17/BACKPRESSURE_DESIGN.md`
- `.ampcode/04_PHASE_NOTES/Phase_17/ROLLBACK_PLAN.md`

### Frontend Documentation
- `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_FRONTEND_USER_STORIES`
- `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_FE_Q&A_01.md`
- `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_CODE_SKELETONS.md`

### Progress Tracking
- `.ampcode/03_PLANS/Phase_17/PHASE_17_PROGRESS.md`

---

## Next Steps

**🚀 READY TO START FRONTEND IMPLEMENTATION**

All backend work is complete. All frontend user stories are fully specified with:
- Complete acceptance criteria
- Concrete implementation details
- Code skeletons
- Test skeletons

**Start with FE-1**: WebSocket Hook Extension (`useWebSocket`)

No guesswork required. All decisions locked in.
