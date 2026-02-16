Here you go, Roger—five clean, self‑contained docs, all aligned with the **actual `web-ui/` structure** and the **final Phase‑17 backend spec**.

---

---

### 2. `PHASE_17_FRONTEND_GIT_DIFF_PLAN.md`

```markdown
# Phase‑17 Frontend Commit‑by‑Commit Git Diff Plan

Target: `web-ui/` repo.

---

## Commit FE‑1 — Extend useWebSocket for Streaming

**Files touched:**
- `src/hooks/useWebSocket.ts`
- `src/hooks/useWebSocket.test.ts`

**Diff outline:**
- Add `sendFrame(bytes)` API.
- Add handling for:
  - dropped frames
  - slow_down warnings
  - error objects
- Extend tests to cover:
  - binary send
  - message parsing
  - error handling.

---

## Commit FE‑2 — RealtimeClient + useRealtime Integration

**Files touched:**
- `src/realtime/RealtimeClient.ts`
- `src/realtime/useRealtime.ts`
- `src/realtime/RealtimeContext.tsx`
- `tests/realtime/realtime_client.spec.tsx`

**Diff outline:**
- Wire `useWebSocket` into `RealtimeClient`.
- Expose `connect`, `disconnect`, `sendFrame`, and state.
- Provide context via `RealtimeContext`.
- Add integration tests for connect + message flow.

---

## Commit FE‑3 — CameraPreview Streaming

**Files touched:**
- `src/components/CameraPreview.tsx`
- `src/components/CameraPreview.test.tsx`
- `src/utils/FPSThrottler.ts`
- `src/utils/FPSThrottler.test.ts` (if needed)

**Diff outline:**
- Add frame capture loop using `<video>` + `<canvas>`.
- Use `FPSThrottler` to control FPS.
- Call `realtime.sendFrame(jpegBytes)`.
- Tests:
  - Mock getUserMedia.
  - Assert sendFrame is called at throttled intervals.

---

## Commit FE‑4 — RealtimeOverlay Integration

**Files touched:**
- `src/components/RealtimeOverlay.tsx`
- `src/components/OverlayRenderer.tsx`
- `src/components/OverlayRenderer.test.tsx`
- `src/utils/drawDetections.ts`

**Diff outline:**
- Subscribe to realtime results from context.
- Render bounding boxes and labels.
- Tests:
  - Given a result payload, overlay renders expected boxes.

---

## Commit FE‑5 — PipelineSelector Reconnect Logic

**Files touched:**
- `src/components/PipelineSelector.tsx`
- `src/components/PluginSelector.test.tsx` (if reused)
- `src/api/pipelines.ts`

**Diff outline:**
- On pipeline change:
  - call `realtime.disconnect()`
  - call `realtime.connect(newPipelineId)`
- Tests:
  - Assert reconnect is called with new pipelineId.

---

## Commit FE‑6 — ErrorBanner Integration

**Files touched:**
- `src/components/ErrorBanner.tsx`
- `src/components/ErrorBanner.test.tsx` (new if missing)
- `src/realtime/useRealtime.ts` (to expose lastError)

**Diff outline:**
- Map backend error codes to user‑friendly messages.
- Show banner when lastError is set.
- Tests:
  - Each error code renders correct message.

---

## Commit FE‑7 — Debug Panel

**Files touched:**
- `src/components/ConfigPanel.tsx` (or new `StreamDebugPanel.tsx`)
- `src/components/ConfigPanel.test.tsx` (or new test file)
- `src/realtime/useRealtime.ts` (expose metrics)

**Diff outline:**
- Display:
  - FPS
  - dropped frame rate
  - slow_down count
  - connection status
- Tests:
  - Given metrics in context, panel renders correct values.

---

## Commit FE‑8 — MP4 Upload Regression Check

**Files touched:**
- `src/hooks/useVideoProcessor.ts`
- `src/hooks/useVideoProcessor.test.ts`
- `src/components/JobList.test.tsx`

**Diff outline:**
- Ensure no breaking changes.
- Add tests if missing for:
  - successful MP4 upload
  - result rendering.
```

---

### 3. `PHASE_17_INTEGRATION_TEST_PLAN_BACKEND_FRONTEND.md`

```markdown
# Phase‑17 Integration Test Plan (Backend + Frontend)

Goal: Verify end‑to‑end behavior from browser to `/ws/video/stream` and back.

---

## 1. Environment

- Backend:
  - Phase‑17 WebSocket endpoint enabled.
  - `/ws/video/stream?pipeline_id=<id>`
- Frontend:
  - `web-ui/` running via `npm run dev` or `npm run test`.

---

## 2. Manual End‑to‑End Scenarios

### Scenario 1 — Happy Path Streaming

1. Start backend + frontend.
2. Open web UI in browser.
3. Select a valid pipeline.
4. Allow webcam access.
5. Observe:
   - Video preview shows.
   - Overlays appear with detections.
   - Frame index increments.
   - No errors shown.

### Scenario 2 — Invalid Pipeline

1. Configure UI to use an invalid pipelineId (or select one if UI supports it).
2. Observe:
   - Backend returns `invalid_pipeline`.
   - ErrorBanner shows appropriate message.
   - Streaming does not start.

### Scenario 3 — Slow Backend → Dropped Frames

1. Temporarily slow down pipeline on backend (e.g. sleep).
2. Stream video.
3. Observe:
   - Some frames marked as dropped.
   - UI shows dropped frame count.
   - Overlays update less frequently.

### Scenario 4 — Slow Backend → Slow‑Down Warning

1. Configure backend thresholds low for testing.
2. Stream video at high FPS.
3. Observe:
   - `{warning: "slow_down"}` messages.
   - UI reduces FPS (via FPSThrottler).
   - Debug panel shows slow_down count.

### Scenario 5 — Invalid Frame

1. Inject invalid frame from frontend (dev mode or test harness).
2. Observe:
   - Backend returns `invalid_frame`.
   - Connection closes.
   - ErrorBanner shows message.

---

## 3. Automated Integration Tests

### Backend‑only

- `server/tests/streaming/`:
  - WebSocket connect
  - frame validation
  - pipeline integration
  - backpressure
  - error contract

### Frontend‑only

- `web-ui/src/hooks/useWebSocket.test.ts`
- `web-ui/src/components/CameraPreview.test.tsx`
- `web-ui/src/components/RealtimeOverlay.test.tsx`
- `web-ui/tests/realtime/realtime_client.spec.tsx`

### Full stack (optional, later)

- Cypress / Playwright style tests (future phase):
  - Launch backend + frontend.
  - Drive browser.
  - Assert DOM changes based on backend responses.

---

## 4. Regression Checks

- Phase‑15 MP4 upload still works.
- Phase‑16 async upload still works.
- No `/v1` endpoints changed.
- No DB schema changes.
```

---

### 4. `PHASE_17_FRONTEND_DEVELOPER_ONBOARDING.md`

```markdown
# Phase‑17 Frontend Developer Onboarding

Target: `web-ui/`

---

## 1. Mental Model

- Backend:
  - `/ws/video/stream?pipeline_id=<id>`
  - Accepts JPEG frames (binary)
  - Returns JSON results, dropped frames, warnings, errors
- Frontend:
  - Captures webcam frames
  - Streams them via WebSocket
  - Renders overlays in real time
  - Falls back to MP4 upload when needed

---

## 2. Key Files

- WebSocket + realtime:
  - `src/hooks/useWebSocket.ts`
  - `src/realtime/RealtimeClient.ts`
  - `src/realtime/useRealtime.ts`
  - `src/realtime/RealtimeContext.tsx`
- Video + overlays:
  - `src/components/CameraPreview.tsx`
  - `src/components/RealtimeOverlay.tsx`
  - `src/components/BoundingBoxOverlay.tsx`
- Controls:
  - `src/components/PipelineSelector.tsx`
  - `src/components/ConfigPanel.tsx`
  - `src/components/ErrorBanner.tsx`
- Utilities:
  - `src/utils/FPSThrottler.ts`
  - `src/utils/drawDetections.ts`
- MP4 upload:
  - `src/hooks/useVideoProcessor.ts`
  - `src/components/JobList.tsx`
  - `src/components/ProgressBar.tsx`

---

## 3. How Data Flows

1. User selects pipeline in `PipelineSelector`.
2. `useRealtime` connects WebSocket with `pipeline_id`.
3. `CameraPreview` captures frames and calls `sendFrame(bytes)`.
4. Backend responds with:
   - `{frame_index, result}` → `RealtimeOverlay` updates.
   - `{frame_index, dropped: true}` → stats update only.
   - `{warning: "slow_down"}` → `FPSThrottler` reduces FPS.
   - `{error, detail}` → `ErrorBanner` shows message and streaming stops.

---

## 4. How to Run Locally

```bash
cd web-ui
npm install
npm run dev
```

Backend must be running with Phase‑17 WebSocket enabled.

---

## 5. Where to Start Coding

If you’re new:

1. Read:
   - `PHASE_17_MASTER_PLAN_BACKEND_AND_FRONTEND.md`
   - `PHASE_17_FRONTEND_USER_STORIES.md`
2. Start with:
   - `src/hooks/useWebSocket.ts`
   - `src/realtime/useRealtime.ts`
   - `src/components/CameraPreview.tsx`
3. Follow the commit plan:
   - FE‑1 → FE‑2 → FE‑3 → FE‑4 → FE‑5 → FE‑6 → FE‑7 → FE‑8

---

## 6. Common Gotchas

- Don’t invent a new WebSocket client—extend `useWebSocket` / `RealtimeClient`.
- Don’t bypass `useRealtime`—it centralizes state and metrics.
- Don’t hardcode URLs—use existing config/env patterns.
- Don’t break MP4 upload—Phase‑15 path must remain intact.

---

## 7. Definition of Done (Frontend)

You’re done when:

- All frontend tests pass:
  - `npm run test`
- Streaming works end‑to‑end:
  - Webcam preview
  - Overlays
  - Dropped frames + slow_down visible
- Errors are surfaced via `ErrorBanner`.
- MP4 upload still works.
```

---

### 5. `PHASE_17_FRONTEND_ARCHITECTURE_DIAGRAM.md`

```markdown
# Phase‑17 Frontend Architecture Diagram

Target: `web-ui/src/`

---

## Component & Hook Relationships

```text
+---------------------------+
|         App.tsx          |
+------------+--------------+
             |
             v
+---------------------------+
|   RealtimeContext.tsx    |
|  (provides useRealtime)  |
+------------+--------------+
             |
   +---------+-------------------------------+
   |                                         |
   v                                         v
+---------------------------+      +---------------------------+
|   CameraPreview.tsx       |      |   RealtimeOverlay.tsx     |
|  (capture + send frames)  |      |  (render detections)      |
+---------------------------+      +---------------------------+
   |
   v
+---------------------------+
|     useRealtime.ts        |
|  (orchestrates streaming) |
+------------+--------------+
             |
             v
+---------------------------+
|     RealtimeClient.ts     |
+------------+--------------+
             |
             v
+---------------------------+
|     useWebSocket.ts       |
|  (raw WS connect/send)    |
+---------------------------+
```

---

## Supporting Components

```text
+---------------------------+
|   PipelineSelector.tsx    |
+---------------------------+
             |
             v
   calls realtime.connect(pipelineId)
```

```text
+---------------------------+
|     ErrorBanner.tsx       |
+---------------------------+
             ^
             |
   reads lastError from useRealtime
```

```text
+---------------------------+
|     ConfigPanel.tsx       |
|  (or Debug Panel)         |
+---------------------------+
             ^
             |
   reads metrics from useRealtime
```

```text
+---------------------------+
|   useVideoProcessor.ts    |
|   JobList.tsx             |
|   ProgressBar.tsx         |
+---------------------------+
   (Phase‑15 MP4 upload path)
```

---

## Data Flow Summary

1. `PipelineSelector` chooses pipeline → `useRealtime.connect(pipelineId)`.
2. `CameraPreview` captures frames → `useRealtime.sendFrame(bytes)`.
3. `useRealtime` → `RealtimeClient` → `useWebSocket` send binary frames.
4. Backend responds:
   - Results → `RealtimeOverlay` via context.
   - Dropped frames / slow_down → metrics + debug panel.
   - Errors → `ErrorBanner`.

This diagram reflects the **actual `web-ui/` structure** and the **Phase‑17 backend contract**.
```

If you want, next we can turn these into actual files under `.ampcode/04_PHASE_NOTES/Phase_17/` with exact filenames you prefer.