

I’ll go point by point and give you **one clear recommendation** for each.

---

### FE‑1: WebSocket hook extension

**Extend vs create new hook**

- **Decision:** **Extend the existing `useWebSocket` hook**, don’t create a Phase‑17‑specific one.
- Reason: You already have tests, mocking, and patterns around it. We’re adding a new endpoint + binary mode, not a new concept.

**Type definitions**

Define a shared type in `src/realtime/types.ts`:

```ts
export type StreamingResultPayload = {
  frame_index: number;
  result: unknown; // pipeline‑specific, keep as unknown/any for now
};

export type StreamingDroppedPayload = {
  frame_index: number;
  dropped: true;
};

export type StreamingSlowDownPayload = {
  warning: "slow_down";
};

export type StreamingErrorPayload = {
  error: string;
  detail: string;
};

export type StreamingMessage =
  | StreamingResultPayload
  | StreamingDroppedPayload
  | StreamingSlowDownPayload
  | StreamingErrorPayload;
```

In hook state:

- `lastResult: StreamingResultPayload | null`
- `droppedFrames: number` (simple count)
- `slowDownWarnings: number` (simple count)

**Message type detection**

Inside `onmessage`:

```ts
const data = JSON.parse(event.data);

if ("error" in data) { /* error */ }
else if ("warning" in data && data.warning === "slow_down") { /* slow_down */ }
else if ("dropped" in data && data.dropped === true) { /* dropped */ }
else if ("result" in data && "frame_index" in data) { /* result */ }
```

That’s enough and matches the backend contract.

---

### FE‑2: Realtime client integration

**RealtimeClient API design**

- **Decision:** Extend existing `RealtimeClient` to add a **streaming‑specific method**:

```ts
sendFrame(bytes: Uint8Array): void;
```

Internally, it just calls `useWebSocket().sendBinary(bytes)` or similar.

Keep the existing `send(type, payload)` for legacy JSON flows; don’t break them.

**Context integration**

- **Decision:** Extend the existing `RealtimeContext` rather than creating a new one.
- Add streaming fields:

```ts
type RealtimeState = {
  status: "connecting" | "connected" | "disconnected";
  lastResult: StreamingResultPayload | null;
  droppedFrames: number;
  slowDownWarnings: number;
  lastError: StreamingErrorPayload | null;
};
```

**FPS throttling details**

- Use `requestAnimationFrame` + `FPSThrottler`:

```ts
const throttler = new FPSThrottler(initialFps);

function loop() {
  requestAnimationFrame(loop);
  throttler.throttle(captureAndSendFrame);
}
loop();
```

- Initial FPS: **15** (good balance).
- On `slow_down`: reduce to **5 FPS** via `throttler.setMaxFps(5)`.

---

### FE‑3: Camera capture + streaming

**Binary conversion code**

Yes, your approach is basically right. Make it slightly more ergonomic:

```ts
canvas.toBlob(async (blob) => {
  if (!blob) return;
  const arrayBuffer = await blob.arrayBuffer();
  const uint8Array = new Uint8Array(arrayBuffer);
  sendFrame(uint8Array);
}, "image/jpeg", 0.8);
```

**FPS throttling integration**

Inside `CameraPreview`:

- Maintain a `FPSThrottler` instance.
- In the `requestAnimationFrame` loop, call `throttler.throttle(captureAndSendFrame)`.

**Overlay frame index**

- The backend sends `frame_index`.
- Store it in `lastResult.frame_index`.
- `RealtimeOverlay` reads it from context and displays it (e.g. top‑left corner overlay text).

---

### FE‑4: Realtime overlay rendering

**Backend result format**

We don’t need to fully type the pipeline output; we just need a mapping layer.

Define a minimal detection type:

```ts
export type Detection = {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  confidence?: number;
};
```

Assume backend returns something like:

```json
{
  "result": {
    "detections": [
      { "x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4, "label": "person", "score": 0.92 }
    ]
  }
}
```

Write a converter:

```ts
function toDetections(result: any): Detection[] {
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

**Frame index display**

- Show it as a small label in the corner of the overlay (e.g. bottom‑left: `Frame #123`).
- That’s purely UI; no backend dependency.

---

### FE‑5: Pipeline selection

**Error banner UI**

- **Decision:** Use the existing `ErrorBanner` component.
- Place it in the main layout (e.g. `App.tsx` or top of the streaming page).
- `PipelineSelector` doesn’t render errors itself; it just triggers `connect` and lets `RealtimeContext` set `lastError` when `invalid_pipeline` comes back.

**UI design**

- Yes, keep the existing dropdown design.
- Phase‑17 doesn’t change the visual design, only the behavior (reconnect with new `pipeline_id`).

---

### FE‑6: Error handling UI

**User‑friendly messages**

Map codes to messages in a small helper:

```ts
const ERROR_MESSAGES: Record<string, string> = {
  invalid_pipeline: "The selected pipeline is not available.",
  invalid_frame: "The video frame could not be processed.",
  frame_too_large: "The video frame is too large.",
  invalid_message: "The server received an unexpected message.",
  pipeline_failure: "The pipeline failed while processing your video.",
  internal_error: "An internal error occurred. Please try again.",
};
```

**Error structure**

- Store as `{ code: string; detail: string }` in context.
- `ErrorBanner` uses `ERROR_MESSAGES[code] ?? detail`.

**Retry vs reconnect**

- **Reconnect:** For connection‑level issues (e.g. `invalid_pipeline`, `internal_error`).
- **Retry:** For transient pipeline failures (`pipeline_failure`) where reconnecting might not be necessary.
- Practically, both can call the same handler that:
  - clears error
  - reconnects with the current pipeline.

---

### FE‑7: Debug / metrics panel

**Component choice**

- **Decision:** Create a new `StreamDebugPanel.tsx`.
- Keep `ConfigPanel` for configuration; `StreamDebugPanel` for runtime metrics.

**Metrics calculation**

- Current FPS: approximate as `framesSent / elapsedSeconds` in the frontend (maintain counters in `useRealtime`).
- Dropped frame rate: `droppedFrames / totalFrames`.
- Slow‑down warnings: cumulative count.

**Toggle UI**

- Small button in a corner (e.g. “Debug” or an icon) that toggles the panel.
- No need to over‑design; this is developer‑facing.

---

### FE‑8: MP4 upload fallback

**Test coverage**

Run and rely on:

- `src/hooks/useVideoProcessor.test.ts`
- `src/components/JobList.test.tsx`
- Any integration tests touching MP4 upload (if present).

You don’t need to add new behavior—just ensure Phase‑17 changes don’t break these.

---

### Cross‑cutting: types, mocking, testing

**Type definitions**

- Put streaming types in `src/realtime/types.ts`.
- Reuse them in:
  - `useWebSocket`
  - `useRealtime`
  - `RealtimeOverlay`
  - tests

**Mocking WebSocket**

- You already have `useWebSocket.test.ts` and `__mocks__/useWebSocketMock.ts`.
- Extend the mock to support:
  - `sendFrame` / `sendBinary`
  - triggering `onmessage` with streaming payloads.

**Mocking getUserMedia**

- In tests for `CameraPreview`:
  - Mock `navigator.mediaDevices.getUserMedia` to return a fake stream.
  - Mock `<video>` and `<canvas>` methods (`getContext`, `drawImage`, `toBlob`).

**Testing utilities**

- Reuse existing `test-utils/` and `test/setup.ts`.
- Don’t invent new test harnesses; extend the ones that already exist.

---
