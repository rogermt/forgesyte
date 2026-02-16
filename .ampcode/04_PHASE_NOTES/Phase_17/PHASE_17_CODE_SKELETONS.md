## Code Skeletons (Concrete, Wired to Decisions)

### ⭐ Phase‑17 Frontend Commit‑by‑Commit Diff Plan (FE‑1 → FE‑8)  
*Plus test skeletons wired to each change*

---

## FE‑1 — WebSocket Hook Extension (`useWebSocket`)

**Goal:** Extend existing hook to support binary streaming + Phase‑17 message types.

### Files touched

- **Modify:** `src/hooks/useWebSocket.ts`
- **Add:** `src/realtime/types.ts`
- **Add tests:** `src/hooks/useWebSocket.test.ts` (extend existing or create if missing)

### Diff summary

**1. Add shared streaming types**

```ts
// src/realtime/types.ts
export type StreamingResultPayload = {
  frame_index: number;
  result: unknown;
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

**2. Extend `useWebSocket`**

- Import streaming types.
- Add state: `lastResult`, `droppedFrames`, `slowDownWarnings`, `lastError`.
- Implement `handleMessage` with key‑based detection.
- Add `sendFrame(bytes)` that sends binary.

```ts
// src/hooks/useWebSocket.ts (core changes)
import {
  StreamingMessage,
  StreamingResultPayload,
  StreamingErrorPayload,
} from "../realtime/types";

type Status = "connecting" | "connected" | "disconnected";

export function useWebSocket(url: string | null) {
  // add new state
  const [status, setStatus] = useState<Status>("disconnected");
  const [lastResult, setLastResult] = useState<StreamingResultPayload | null>(null);
  const [droppedFrames, setDroppedFrames] = useState(0);
  const [slowDownWarnings, setSlowDownWarnings] = useState(0);
  const [lastError, setLastError] = useState<StreamingErrorPayload | null>(null);

  // onmessage → parse JSON and route to handleMessage
  // add handleMessage(msg: StreamingMessage)
  // add sendFrame(bytes: Uint8Array | ArrayBuffer)
}
```

**3. Test skeleton**

```ts
// src/hooks/useWebSocket.test.ts
import { renderHook, act } from "@testing-library/react";
import { useWebSocket } from "./useWebSocket";

describe("useWebSocket (Phase‑17 streaming)", () => {
  it("handles result messages", () => {
    // mock WebSocket, trigger onmessage with { frame_index, result }
    // assert lastResult updated
  });

  it("increments droppedFrames on dropped messages", () => {
    // trigger { frame_index, dropped: true }
  });

  it("increments slowDownWarnings on slow_down messages", () => {
    // trigger { warning: 'slow_down' }
  });

  it("sets lastError on error messages", () => {
    // trigger { error, detail }
  });

  it("sends binary frames via sendFrame", () => {
    // assert ws.send called with Uint8Array
  });
});
```

---

## FE‑2 — Realtime Client Integration (`useRealtime`, `RealtimeClient`, `RealtimeContext`)

**Goal:** Wire `useWebSocket` into a higher‑level realtime API with FPS throttling.

### Files touched

- **Modify:** `src/realtime/RealtimeClient.ts`
- **Modify:** `src/realtime/useRealtime.ts`
- **Modify:** `src/realtime/RealtimeContext.tsx`
- **Add tests:** `src/realtime/useRealtime.test.ts`

### Diff summary

**1. Extend `RealtimeClient`**

```ts
// src/realtime/RealtimeClient.ts (add method)
sendFrame(bytes: Uint8Array) {
  this.wsHook.sendFrame(bytes);
}
```

**2. Implement `useRealtime`**

```ts
// src/realtime/useRealtime.ts
import { useWebSocket } from "../hooks/useWebSocket";
import FPSThrottler from "../utils/FPSThrottler";

export function useRealtime() {
  // pipelineId, framesSent, startTime
  // derive ws URL with /ws/video/stream?pipeline_id=
  // call useWebSocket(url)
  // create FPSThrottler(15)
  // connect(), disconnect(), sendFrame() with throttler.throttle(...)
  // if slowDownWarnings > 0 → throttler.setMaxFps(5)
}
```

**3. Context wiring**

```ts
// src/realtime/RealtimeContext.tsx
const RealtimeContext = createContext<ReturnType<typeof useRealtime> | null>(null);

export const RealtimeProvider: React.FC = ({ children }) => {
  const realtime = useRealtime();
  return (
    <RealtimeContext.Provider value={realtime}>{children}</RealtimeContext.Provider>
  );
};

export function useRealtimeContext() {
  const ctx = useContext(RealtimeContext);
  if (!ctx) throw new Error("useRealtimeContext must be used within RealtimeProvider");
  return ctx;
}
```

**4. Test skeleton**

```ts
// src/realtime/useRealtime.test.ts
import { renderHook, act } from "@testing-library/react";
import { useRealtime } from "./useRealtime";

describe("useRealtime (Phase‑17 streaming)", () => {
  it("connects with pipelineId and builds correct URL", () => {
    // mock env + useWebSocket
  });

  it("increments framesSent when sendFrame is called", () => {
    // assert framesSent++
  });

  it("reduces FPS when slowDownWarnings > 0", () => {
    // simulate ws.slowDownWarnings and assert throttler.setMaxFps called
  });
});
```

---

## FE‑3 — Camera Capture + Streaming (`CameraPreview`)

**Goal:** Capture webcam frames, convert to JPEG, send via `sendFrame`.

### Files touched

- **Modify:** `src/components/CameraPreview.tsx`
- **Add tests:** `src/components/CameraPreview.test.tsx` (if not already present)

### Diff summary

**1. Implement capture loop**

```tsx
// src/components/CameraPreview.tsx
import { useRealtimeContext } from "../realtime/RealtimeContext";

export const CameraPreview: React.FC = () => {
  const { sendFrame } = useRealtimeContext();
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    // getUserMedia, attach to video
    // requestAnimationFrame loop
    // draw video to canvas
    // canvas.toBlob → Uint8Array → sendFrame(bytes)
  }, [sendFrame]);

  return (
    <div>
      <video ref={videoRef} autoPlay muted playsInline />
      <canvas ref={canvasRef} style={{ display: "none" }} />
    </div>
  );
};
```

**2. Test skeleton**

```tsx
// src/components/CameraPreview.test.tsx
import { render } from "@testing-library/react";
import { CameraPreview } from "./CameraPreview";
import { RealtimeProvider } from "../realtime/RealtimeContext";

describe("CameraPreview", () => {
  it("renders video and canvas elements", () => {
    const { getByRole } = render(
      <RealtimeProvider>
        <CameraPreview />
      </RealtimeProvider>,
    );
    // assert video present
  });

  it("calls sendFrame when a frame is captured", () => {
    // mock getUserMedia, video, canvas.toBlob
    // assert sendFrame called
  });
});
```

---

## FE‑4 — Realtime Overlay Rendering (`RealtimeOverlay`)

**Goal:** Convert backend result into detections and overlay them with frame index.

### Files touched

- **Modify:** `src/realtime/types.ts` (add `Detection` + `toDetections`)
- **Modify:** `src/components/RealtimeOverlay.tsx`
- **Add tests:** `src/components/RealtimeOverlay.test.tsx`

### Diff summary

**1. Add detection types + converter**

```ts
// src/realtime/types.ts
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

**2. Use in `RealtimeOverlay`**

```tsx
// src/components/RealtimeOverlay.tsx
import { useRealtimeContext } from "../realtime/RealtimeContext";
import { toDetections } from "../realtime/types";
import { BoundingBoxOverlay } from "./BoundingBoxOverlay";

export const RealtimeOverlay: React.FC = () => {
  const { state } = useRealtimeContext();
  const { lastResult } = state;
  if (!lastResult) return null;

  const detections = toDetections(lastResult.result);

  return (
    <div style={{ position: "relative" }}>
      <BoundingBoxOverlay detections={detections} />
      <div /* frame index label */>Frame #{lastResult.frame_index}</div>
    </div>
  );
};
```

**3. Test skeleton**

```tsx
// src/components/RealtimeOverlay.test.tsx
import { render } from "@testing-library/react";
import { RealtimeOverlay } from "./RealtimeOverlay";
import { RealtimeProvider } from "../realtime/RealtimeContext";

describe("RealtimeOverlay", () => {
  it("renders nothing when no lastResult", () => {
    // mock context with lastResult = null
  });

  it("renders detections and frame index when lastResult is present", () => {
    // mock context with lastResult.result.detections
    // assert frame label and overlay rendered
  });
});
```

---

## FE‑5 — Pipeline Selection (`PipelineSelector`)

**Goal:** Reuse dropdown, reconnect with selected pipeline, surface invalid_pipeline via ErrorBanner.

### Files touched

- **Modify:** `src/components/PipelineSelector.tsx`
- **Modify:** `src/components/ErrorBanner.tsx` (to read `lastError` from context)
- **Add tests:** `src/components/PipelineSelector.test.tsx`, `src/components/ErrorBanner.test.tsx`

### Diff summary

**1. PipelineSelector integration**

```tsx
// src/components/PipelineSelector.tsx
import { useRealtimeContext } from "../realtime/RealtimeContext";

export const PipelineSelector: React.FC = () => {
  const { connect, disconnect } = useRealtimeContext();
  // existing dropdown logic
  // onChange: disconnect(); connect(selectedPipelineId);
};
```

**2. ErrorBanner mapping**

```tsx
// src/components/ErrorBanner.tsx
import { useRealtimeContext } from "../realtime/RealtimeContext";

const ERROR_MESSAGES: Record<string, string> = {
  invalid_pipeline: "The selected pipeline is not available.",
  invalid_frame: "The video frame could not be processed.",
  frame_too_large: "The video frame is too large.",
  invalid_message: "The server received an unexpected message.",
  pipeline_failure: "The pipeline failed while processing your video.",
  internal_error: "An internal error occurred. Please try again.",
};

export const ErrorBanner: React.FC = () => {
  const { state, connect } = useRealtimeContext();
  const error = state.lastError;
  if (!error) return null;

  const message = ERROR_MESSAGES[error.error] ?? error.detail;

  return (
    <div>
      <span>{message}</span>
      <button onClick={() => connect(/* current pipeline */)}>Retry</button>
    </div>
  );
};
```

**3. Test skeletons**

```tsx
// src/components/PipelineSelector.test.tsx
describe("PipelineSelector", () => {
  it("calls connect with selected pipeline", () => {
    // mock useRealtimeContext
  });
});
```

```tsx
// src/components/ErrorBanner.test.tsx
describe("ErrorBanner", () => {
  it("renders user‑friendly message for known error codes", () => {
    // mock lastError
  });

  it("calls reconnect on Retry click", () => {
    // assert connect called
  });
});
```

---

## FE‑7 — Debug / Metrics Panel (`StreamDebugPanel`)

**Goal:** Developer‑facing panel showing status, FPS, drops, slow‑downs.

### Files touched

- **Add:** `src/components/StreamDebugPanel.tsx`
- **Modify:** `src/realtime/useRealtime.ts` (ensure framesSent/startTime in state)
- **Add tests:** `src/components/StreamDebugPanel.test.tsx`

### Diff summary

**1. Panel component**

```tsx
// src/components/StreamDebugPanel.tsx
import { useRealtimeContext } from "../realtime/RealtimeContext";

export const StreamDebugPanel: React.FC = () => {
  const { state } = useRealtimeContext();
  // compute fps, dropRate from framesSent, droppedFrames, startTime
  // render small fixed panel
};
```

**2. Test skeleton**

```tsx
// src/components/StreamDebugPanel.test.tsx
describe("StreamDebugPanel", () => {
  it("shows status and metrics from context", () => {
    // mock context with known values
  });
});
```

---

## FE‑8 — MP4 Upload Fallback

**Goal:** Ensure existing MP4 flow remains intact.

### Files touched

- **No functional changes**; only **run tests** and adjust if broken:
  - `src/hooks/useVideoProcessor.test.ts`
  - `src/components/JobList.test.tsx`

If any Phase‑17 changes break these, add minimal fixes (e.g. type imports, context wiring) but **no new behavior**.

---

This gives you:

- A **commit‑by‑commit frontend plan (FE‑1 → FE‑8)**  
- Concrete **diff‑level descriptions** per file  
- **Test skeletons** for:
  - `useWebSocket`
  - `useRealtime`
  - `CameraPreview`
  - `RealtimeOverlay`
  - `PipelineSelector`
  - `ErrorBanner`
  - `StreamDebugPanel`


