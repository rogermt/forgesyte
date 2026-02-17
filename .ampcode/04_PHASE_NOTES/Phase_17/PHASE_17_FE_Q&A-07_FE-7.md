Refined FE-7 Questions (After Codebase Analysis)
After reading Phase 17 documentation, here are my refined questions where I'm less than 90% confident:

1. How to track frame sizes for "last 5 frame sizes"? ⚠️
Found: Test skeleton shows startTime and framesSent are tracked in state
Found: sendFrame receives bytes but doesn't track size
Question: Should I add frame size tracking in sendFrame() and store last 5 sizes in state?
Impact: Need to implement circular buffer for last 5 frame sizes
2. How to measure backend latency? ⚠️
Found: Golden Path Debug Mode requires "last 5 backend latencies"
Found: useWebSocket tracks processing_time_ms for Phase-10 but not for Phase-17
Question: Should I add client-side timing (send timestamp → receive timestamp) to measure latency?
Impact: Backend latency measurement would be guesswork without this
3. Where to mount the "Debug" button in App.tsx? ⚠️
Found: App.tsx structure shows a main layout with sections and aside
Found: Debug toggle example shows checkbox in a div with className "debug-toggle"
Question: Should I add the debug button in the header, in a toolbar, or in a corner of the main layout?
Impact: Affects UI layout and component placement
4. How to expose WebSocket URL? ⚠️
Found: WebSocket URL is constructed internally in useRealtime but not exposed
Question: Should I expose wsUrl from useRealtime or reconstruct it from currentPipelineId in the debug panel?
Impact: Need to know which approach is correct
5. How to expose throttler FPS? ⚠️
Found: FPSThrottler is internal to useRealtime (not exposed)
Found: Throttler switches from 15 FPS → 5 FPS on slow-down warnings
Question: Should I expose currentFps from useRealtime or track it separately?
Impact: Can't show throttler FPS without exposing it
6. Debug mode state management? ⚠️
Found: Debug mode is controlled via checkbox in UI and passed through RealtimeProvider
Question: Should debug state be in App.tsx (local state) or in RealtimeContext (global)?
Impact: Affects how debug panel visibility is controlled
Summary
FE-7 has 6 areas of uncertainty (moderate)

Implementation Clarified:

✅ framesSent - Add tracking in useRealtime and expose in state
✅ startTime - Add tracking in useRealtime when connecting
✅ FPS calculation - framesSent / (now - startTime)
✅ Drop rate - droppedFrames / framesSent
✅ Debug toggle - Checkbox in main layout, passed through RealtimeProvider
Still Uncertain:

Frame size tracking mechanism
Backend latency measurement approach
Debug button placement in App.tsx
WebSocket URL exposure method
Throttler FPS exposure
Debug mode state management location
Recommendation: I need clarification on:

Whether frame size tracking is required (last 5 sizes)
Whether backend latency measurement is actually required or optional
Where to place the debug button in the app layout
Whether to expose WebSocket URL or reconstruct it from pipelineId
Whether to expose throttler FPS or track it separately
Whether debug mode should be local to App.tsx or global in context

ANSWER

Roger — FE‑7 is the *most architectural* of the frontend stories, so your caution is exactly right.  
Let’s settle every uncertainty cleanly and decisively so you can implement FE‑7 without drift, without rework, and without breaking Phase‑17.

Below is the **final, authoritative guidance** for all six FE‑7 questions.

---

# ⭐ **FE‑7 — Final Decisions (Authoritative, Repo‑Aligned)**

I’ll give you:

- The correct answer  
- Why it’s correct  
- What to implement  

Let’s go one by one.

---

# ⭐ 1. **How to track frame sizes (last 5 frame sizes)?**

### ✔ Correct answer: **Yes — track frame sizes inside `sendFrame()` using a circular buffer.**

### Why?
- Phase‑17 Golden Path Debug Mode explicitly requires “last 5 frame sizes”
- The only place where you have access to the raw bytes is `sendFrame()`
- Tracking this in the debug panel would be impossible without storing it

### Implementation:

In `useRealtime.ts`:

```ts
const [lastFrameSizes, setLastFrameSizes] = useState<number[]>([]);
```

Inside `sendFrame(bytes)`:

```ts
setLastFrameSizes((prev) => {
  const next = [...prev, bytes.byteLength];
  return next.length > 5 ? next.slice(next.length - 5) : next;
});
```

Expose in state:

```ts
state: {
  ...,
  lastFrameSizes,
}
```

### Final rule:
✔ Track last 5 frame sizes  
✔ Store in realtime state  
✔ FE‑7 reads it  

---

# ⭐ 2. **How to measure backend latency?**

### ✔ Correct answer: **Yes — measure client‑side latency using send timestamp → receive timestamp.**

### Why?
- Phase‑17 backend does NOT send processing time  
- Phase‑10’s `processing_time_ms` is irrelevant  
- The only reliable method is:
  - Record timestamp when sending frame
  - Record timestamp when receiving result for that frame_index
  - Compute delta

### Implementation:

In `useRealtime.ts`:

```ts
const sendTimestamps = useRef(new Map<number, number>());
```

When sending:

```ts
sendTimestamps.current.set(localFrameIndex, performance.now());
```

When receiving:

```ts
if (msg.frame_index !== undefined) {
  const start = sendTimestamps.current.get(msg.frame_index);
  if (start) {
    const latency = performance.now() - start;
    setLastLatencies((prev) => {
      const next = [...prev, latency];
      return next.length > 5 ? next.slice(next.length - 5) : next;
    });
  }
}
```

Expose:

```ts
state.lastLatencies
```

### Final rule:
✔ Track last 5 backend latencies  
✔ Client‑side measurement is correct  
✔ FE‑7 displays them  

---

# ⭐ 3. **Where to mount the Debug button?**

### ✔ Correct answer: **Place the Debug toggle in the main layout header (top‑right).**

### Why?
- It must be globally visible  
- It must not interfere with video layout  
- It must not be inside CameraPreview  
- It must not be inside the overlay  
- It must not be inside the debug panel itself  

### Implementation:

In `App.tsx` or `MainLayout.tsx`:

```tsx
<div className="top-right-controls">
  <label>
    <input type="checkbox" checked={debug} onChange={toggleDebug} />
    Debug
  </label>
</div>
```

CSS:

```css
.top-right-controls {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 9999;
}
```

### Final rule:
✔ Debug toggle lives in main layout  
✔ Not inside any streaming component  

---

# ⭐ 4. **How to expose WebSocket URL?**

### ✔ Correct answer: **Expose wsUrl from `useRealtime` (do NOT reconstruct it).**

### Why?
- The URL includes:
  - host
  - pipeline_id
  - api_key
  - environment‑specific base URL
- Reconstructing it in FE‑7 would duplicate logic and risk drift
- The debug panel must show the *actual* URL used

### Implementation:

In `useRealtime.ts`:

```ts
const wsUrl = computedUrl; // already exists internally
```

Expose:

```ts
return {
  ...,
  wsUrl,
};
```

### Final rule:
✔ Expose wsUrl  
✘ Do not reconstruct it in FE‑7  

---

# ⭐ 5. **How to expose throttler FPS?**

### ✔ Correct answer: **Expose current FPS from `useRealtime` by reading from FPSThrottler.**

### Why?
- FPSThrottler already stores `maxFps`
- It changes from 15 → 5 on slow_down
- FE‑7 must display the current throttled FPS

### Implementation:

In `useRealtime.ts`:

```ts
const [currentFps, setCurrentFps] = useState(15);
```

Whenever throttler changes:

```ts
throttlerRef.current = new FPSThrottler(newFps);
setCurrentFps(newFps);
```

Expose:

```ts
state.currentFps
```

### Final rule:
✔ Expose currentFps  
✔ FE‑7 displays it  

---

# ⭐ 6. **Debug mode state management — local or global?**

### ✔ Correct answer: **Debug mode should be local to App.tsx and passed into RealtimeProvider.**

### Why?
- Debug mode is a UI concern, not a realtime concern  
- RealtimeContext should not know about debug mode  
- Debug mode affects:
  - Overlay debug info
  - Debug panel visibility
  - Logging verbosity  
- Keeping it global would pollute realtime state

### Implementation:

In `App.tsx`:

```tsx
const [debug, setDebug] = useState(false);

<RealtimeProvider debug={debug}>
  <StreamingPage debug={debug} />
</RealtimeProvider>
```

### Final rule:
✔ Debug mode lives in App.tsx  
✔ Passed down as prop  
✘ Not stored in RealtimeContext  

---

# ⭐ **Final FE‑7 Implementation Summary**

| Feature | Implementation |
|--------|----------------|
| Last 5 frame sizes | Track in sendFrame() via circular buffer |
| Last 5 backend latencies | Timestamp send + receive, store in circular buffer |
| Debug button placement | Top‑right of main layout |
| WebSocket URL | Expose wsUrl from useRealtime |
| Throttler FPS | Expose currentFps from useRealtime |
| Debug mode state | Local to App.tsx, passed to RealtimeProvider |

---

Roger — here is the **complete, final, production‑ready FE‑7 package** you asked for:

- **A full FE‑7 implementation blueprint**  
- **A complete `StreamDebugPanel.tsx` skeleton**  
- **A full FE‑7 test skeleton**  
- **A commit‑by‑commit Git diff plan**  

Everything below is aligned with:

- Phase‑17 realtime architecture  
- The decisions we locked in for FE‑7  
- Your existing repo structure  
- Zero breaking changes to Phase‑10  

Let’s lock this in.

---

# ⭐ **FE‑7 Implementation Blueprint (Final, Authoritative)**

This blueprint describes exactly what FE‑7 must implement, where, and how.

---

## **1. Extend `useRealtime` to expose debug metrics**

### Add state fields:

```ts
const [framesSent, setFramesSent] = useState(0);
const [startTime, setStartTime] = useState<number | null>(null);
const [lastFrameSizes, setLastFrameSizes] = useState<number[]>([]);
const [lastLatencies, setLastLatencies] = useState<number[]>([]);
const [currentFps, setCurrentFps] = useState(15);
```

### Add send timestamp tracking:

```ts
const sendTimestamps = useRef(new Map<number, number>());
let localFrameIndex = useRef(0);
```

### In `sendFrame(bytes)`:

```ts
const size = bytes.byteLength;

setFramesSent((n) => n + 1);

setLastFrameSizes((prev) => {
  const next = [...prev, size];
  return next.length > 5 ? next.slice(next.length - 5) : next;
});

const frameIndex = localFrameIndex.current++;
sendTimestamps.current.set(frameIndex, performance.now());
```

### In WebSocket message handler:

```ts
if (msg.frame_index !== undefined) {
  const start = sendTimestamps.current.get(msg.frame_index);
  if (start) {
    const latency = performance.now() - start;
    setLastLatencies((prev) => {
      const next = [...prev, latency];
      return next.length > 5 ? next.slice(next.length - 5) : next;
    });
  }
}
```

### Expose all debug fields:

```ts
state: {
  ...,
  framesSent,
  startTime,
  lastFrameSizes,
  lastLatencies,
  currentFps,
}
```

---

## **2. Add `debug` prop to `RealtimeProvider`**

In `RealtimeContext.tsx`:

```tsx
export const RealtimeProvider = ({ children, debug = false }) => {
  const realtime = useRealtime({ debug });
  return <RealtimeContext.Provider value={realtime}>{children}</RealtimeContext.Provider>;
};
```

---

## **3. Add Debug toggle in `App.tsx`**

Top‑right corner:

```tsx
const [debug, setDebug] = useState(false);

<div className="top-right-controls">
  <label>
    <input type="checkbox" checked={debug} onChange={(e) => setDebug(e.target.checked)} />
    Debug
  </label>
</div>

<RealtimeProvider debug={debug}>
  <StreamDebugPanel debug={debug} />
  <StreamingPage debug={debug} />
</RealtimeProvider>
```

---

## **4. Implement `StreamDebugPanel.tsx`**

- Shows:
  - connectionStatus  
  - framesSent  
  - FPS  
  - droppedFrames  
  - slowDownWarnings  
  - last 5 frame sizes  
  - last 5 backend latencies  
  - wsUrl  
  - currentFps  

- Only visible when `debug === true`.

---

## **5. Add tests for FE‑7**

- Mock `useRealtimeContext`
- Assert:
  - Panel renders only when debug=true  
  - FPS calculation is correct  
  - Frame sizes and latencies are displayed  
  - WebSocket URL is shown  
  - Slow‑down warnings and dropped frames appear  

---

# ⭐ **StreamDebugPanel.tsx — Full Component Skeleton (Final)**

Place in:

```
web-ui/src/components/StreamDebugPanel.tsx
```

---

```tsx
import React from "react";
import { useRealtimeContext } from "../realtime/RealtimeContext";

interface StreamDebugPanelProps {
  debug: boolean;
}

export function StreamDebugPanel({ debug }: StreamDebugPanelProps) {
  const { state, wsUrl, currentPipelineId } = useRealtimeContext();

  if (!debug) return null;

  const {
    connectionStatus,
    framesSent,
    startTime,
    droppedFrames,
    slowDownWarnings,
    lastFrameSizes,
    lastLatencies,
    currentFps,
    lastResult,
  } = state;

  const elapsedSeconds =
    startTime != null ? (performance.now() - startTime) / 1000 : 0;

  const approxFps =
    elapsedSeconds > 0 ? (framesSent / elapsedSeconds).toFixed(1) : "0.0";

  const dropRate =
    framesSent > 0
      ? ((droppedFrames / framesSent) * 100).toFixed(1) + "%"
      : "0%";

  return (
    <div
      style={{
        position: "fixed",
        bottom: 8,
        right: 8,
        background: "rgba(0,0,0,0.85)",
        color: "#0f0",
        padding: "12px",
        borderRadius: 6,
        fontFamily: "monospace",
        fontSize: 12,
        zIndex: 9999,
        width: 260,
      }}
    >
      <div>Phase‑17 Debug Panel</div>
      <hr style={{ borderColor: "#0f0" }} />

      <div>Status: {connectionStatus}</div>
      <div>Pipeline: {currentPipelineId ?? "none"}</div>
      <div>WS URL: {wsUrl}</div>

      <hr style={{ borderColor: "#0f0" }} />

      <div>Frames Sent: {framesSent}</div>
      <div>FPS (approx): {approxFps}</div>
      <div>Throttler FPS: {currentFps}</div>

      <hr style={{ borderColor: "#0f0" }} />

      <div>Dropped Frames: {droppedFrames}</div>
      <div>Drop Rate: {dropRate}</div>
      <div>Slow‑Down Warnings: {slowDownWarnings}</div>

      <hr style={{ borderColor: "#0f0" }} />

      <div>Last 5 Frame Sizes:</div>
      <ul>
        {lastFrameSizes.map((s, i) => (
          <li key={i}>{s} bytes</li>
        ))}
      </ul>

      <div>Last 5 Latencies:</div>
      <ul>
        {lastLatencies.map((l, i) => (
          <li key={i}>{l.toFixed(1)} ms</li>
        ))}
      </ul>

      <hr style={{ borderColor: "#0f0" }} />

      <div>Last Frame Index: {lastResult?.frame_index ?? "none"}</div>
    </div>
  );
}
```

---

# ⭐ **FE‑7 Test Skeleton (Final)**

Place in:

```
web-ui/src/components/StreamDebugPanel.test.tsx
```

---

```tsx
import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { StreamDebugPanel } from "./StreamDebugPanel";

vi.mock("../realtime/RealtimeContext", () => ({
  __esModule: true,
  useRealtimeContext: vi.fn(),
}));

import { useRealtimeContext } from "../realtime/RealtimeContext";

describe("StreamDebugPanel (Phase‑17)", () => {
  it("renders nothing when debug=false", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      state: {},
    });

    const { container } = render(<StreamDebugPanel debug={false} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders debug metrics when debug=true", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      wsUrl: "ws://localhost/ws/video/stream?pipeline_id=p1",
      currentPipelineId: "p1",
      state: {
        connectionStatus: "connected",
        framesSent: 10,
        startTime: performance.now() - 1000,
        droppedFrames: 2,
        slowDownWarnings: 1,
        lastFrameSizes: [1000, 1200],
        lastLatencies: [30, 40],
        currentFps: 15,
        lastResult: { frame_index: 42 },
      },
    });

    render(<StreamDebugPanel debug={true} />);

    expect(screen.getByText("Phase‑17 Debug Panel")).toBeInTheDocument();
    expect(screen.getByText("Frames Sent: 10")).toBeInTheDocument();
    expect(screen.getByText("Dropped Frames: 2")).toBeInTheDocument();
    expect(screen.getByText("Slow‑Down Warnings: 1")).toBeInTheDocument();
    expect(screen.getByText("1000 bytes")).toBeInTheDocument();
    expect(screen.getByText("30.0 ms")).toBeInTheDocument();
    expect(screen.getByText("Last Frame Index: 42")).toBeInTheDocument();
  });
});
```

---

# ⭐ **Commit‑by‑Commit Git Diff Plan (FE‑7)**

This is the exact sequence you should commit in.

---

## **Commit 1 — Add debug fields to useRealtime**

Files:

- `src/realtime/useRealtime.ts`

Changes:

- Add framesSent, startTime, lastFrameSizes, lastLatencies, currentFps
- Add send timestamp tracking
- Add latency calculation
- Expose all fields in state

---

## **Commit 2 — Expose wsUrl and currentPipelineId**

Files:

- `src/realtime/useRealtime.ts`

Changes:

- Expose `wsUrl`
- Expose `currentPipelineId`

---

## **Commit 3 — Add debug prop to RealtimeProvider**

Files:

- `src/realtime/RealtimeContext.tsx`

Changes:

- Accept `debug` prop
- Pass to `useRealtime`

---

## **Commit 4 — Add Debug toggle to App.tsx**

Files:

- `src/App.tsx` or `src/layout/MainLayout.tsx`

Changes:

- Add checkbox in top‑right
- Pass debug to RealtimeProvider and StreamDebugPanel

---

## **Commit 5 — Create StreamDebugPanel.tsx**

Files:

- `src/components/StreamDebugPanel.tsx` (new)

---

## **Commit 6 — Add FE‑7 tests**

Files:

- `src/components/StreamDebugPanel.test.tsx` (new)

---

## **Commit 7 — Manual QA**

Checklist:

- Debug toggle shows/hides panel  
- FPS updates  
- Frame sizes update  
- Latencies update  
- Slow‑down warnings update  
- Dropped frames update  
- WebSocket URL displays correctly  

---

# ⭐ Final Summary

You now have:

- ✔ Full FE‑7 implementation blueprint  
- ✔ Full `StreamDebugPanel.tsx` skeleton  
- ✔ Full FE‑7 test skeleton  
- ✔ Full Git diff plan  

This is the **complete, correct, Phase‑17‑aligned FE‑7 implementation**.

Absolutely, Roger — here is a **clear, visual, repo‑aligned layout diagram** for FE‑7.  
This shows exactly where the **Debug Toggle**, **StreamDebugPanel**, **CameraPreview**, and **RealtimeStreamingOverlay** sit in the UI hierarchy.

I’ll give you:

- A **high‑level layout diagram**  
- A **component tree diagram**  
- A **z‑index / layering diagram**  
- A **data‑flow diagram** (how debug state flows)

Everything below matches your actual `web-ui/` structure.

---

# ⭐ **FE‑7 Layout Diagram (High‑Level)**

```
+--------------------------------------------------------------+
|                          App.tsx                             |
|--------------------------------------------------------------|
|                                                              |
|  +----------------------+      +---------------------------+ |
|  |  Debug Toggle (UI)  | ---> |  debug: boolean (state)   | |
|  +----------------------+      +---------------------------+ |
|                                                              |
|  <RealtimeProvider debug={debug}>                            |
|                                                              |
|    +------------------------------------------------------+  |
|    |                    StreamingPage                     |  |
|    |------------------------------------------------------|  |
|    |                                                      |  |
|    |  +-----------------------------------------------+   |  |
|    |  |             CameraPreview (video)             |   |  |
|    |  |-----------------------------------------------|   |  |
|    |  |  <video>                                      |   |  |
|    |  |  <canvas> (capture)                           |   |  |
|    |  |  <RealtimeStreamingOverlay> (Phase‑17)        |   |  |
|    |  +-----------------------------------------------+   |  |
|    |                                                      |  |
|    +------------------------------------------------------+  |
|                                                              |
|    +------------------------------------------------------+  |
|    |                StreamDebugPanel (FE‑7)               |  |
|    |------------------------------------------------------|  |
|    |  Visible only when debug === true                    |  |
|    |  Fixed bottom‑right overlay                          |  |
|    +------------------------------------------------------+  |
|                                                              |
|  </RealtimeProvider>                                         |
|                                                              |
+--------------------------------------------------------------+
```

---

# ⭐ **Component Tree Diagram (FE‑7 Context)**

```
App.tsx
 ├── DebugToggle (checkbox)
 └── RealtimeProvider debug={debug}
      └── StreamingPage
           ├── CameraPreview
           │     ├── <video>
           │     ├── <canvas> (capture)
           │     └── RealtimeStreamingOverlay (FE‑4)
           └── StreamDebugPanel debug={debug} (FE‑7)
```

---

# ⭐ **Layering / Z‑Index Diagram**

This shows how the UI layers stack visually:

```
Z‑Index 10000 ───────────────────────────────────────────────
| StreamDebugPanel (FE‑7) — fixed bottom‑right overlay       |
|                                                            |
Z‑Index 9000 ────────────────────────────────────────────────
| RealtimeErrorBanner (FE‑6) — top overlay                   |
|                                                            |
Z‑Index 5000 ────────────────────────────────────────────────
| RealtimeStreamingOverlay (FE‑4) — bounding boxes           |
|                                                            |
Z‑Index 1000 ────────────────────────────────────────────────
| CameraPreview canvas (capture)                             |
|                                                            |
Z‑Index 500 ─────────────────────────────────────────────────
| CameraPreview video                                        |
|                                                            |
Z‑Index 0 ───────────────────────────────────────────────────
| Page background                                            |
```

---

# ⭐ **Debug Mode Data‑Flow Diagram**

```
App.tsx
  debug: boolean
      |
      v
RealtimeProvider debug={debug}
      |
      v
useRealtime({ debug })
      |
      +--> Enables verbose logging
      +--> Enables tracking: lastFrameSizes, lastLatencies
      |
      v
StreamDebugPanel debug={debug}
      |
      +--> Reads realtime state
      +--> Displays metrics
```

---

# ⭐ **Explanation of Layout Decisions**

### ✔ Debug toggle belongs in App.tsx  
Because it controls global UI behavior, not realtime logic.

### ✔ StreamDebugPanel is fixed bottom‑right  
So it never overlaps the video or overlay.

### ✔ RealtimeStreamingOverlay sits inside CameraPreview  
Because it must align with the video canvas.

### ✔ ErrorBanner sits above everything  
Because errors must be visible regardless of debug mode.

---

Roger — you’re going to love this.  
Here is a **complete FE‑7 CSS layout pack** *and* a **Figma‑style visual mockup** (ASCII‑based, but structured exactly like a Figma frame).  
This gives you a crystal‑clear picture of how the debug UI fits into the Phase‑17 streaming layout.

Let’s do this cleanly.

---

# 🎨 **FE‑7 CSS Layout Pack (Final, Drop‑In Ready)**

These styles match the diagrams we’ve been working with and are designed to integrate directly into your existing `web-ui/` structure.

You can place these in:

```
src/styles/streaming.css
```

or inline them in component‑level CSS modules.

---

## **1. Debug Toggle (top‑right)**

```css
.top-right-controls {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.4);
  padding: 6px 10px;
  border-radius: 6px;
  color: white;
  font-family: sans-serif;
  font-size: 13px;
}

.top-right-controls input[type="checkbox"] {
  margin-right: 6px;
}
```

---

## **2. StreamDebugPanel (bottom‑right)**

```css
.stream-debug-panel {
  position: fixed;
  bottom: 8px;
  right: 8px;
  width: 260px;
  background: rgba(0, 0, 0, 0.85);
  color: #0f0;
  padding: 12px;
  border-radius: 6px;
  font-family: monospace;
  font-size: 12px;
  z-index: 10000;
  box-shadow: 0 0 8px rgba(0, 255, 0, 0.3);
}

.stream-debug-panel hr {
  border: none;
  border-top: 1px solid #0f0;
  margin: 6px 0;
}

.stream-debug-panel ul {
  margin: 4px 0 8px 12px;
  padding: 0;
}
```

---

## **3. Streaming Overlay (Phase‑17)**

```css
.streaming-overlay-container {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}

.frame-index-label {
  position: absolute;
  top: 8px;
  left: 8px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  font-family: monospace;
  z-index: 5000;
}

.debug-detection-count {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.6);
  color: #0f0;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-family: monospace;
  z-index: 5000;
}
```

---

## **4. CameraPreview container (relative positioning)**

```css
.camera-preview-container {
  position: relative;
  display: inline-block;
}
```

---

# 🧩 **How these CSS pieces fit together**

```
App.tsx
 ├── <div class="top-right-controls">Debug Toggle</div>
 └── <RealtimeProvider debug={debug}>
        <StreamingPage>
           <div class="camera-preview-container">
              <video>
              <canvas> (capture)
              <RealtimeStreamingOverlay> (uses .streaming-overlay-container)
           </div>
           <StreamDebugPanel class="stream-debug-panel" />
        </StreamingPage>
     </RealtimeProvider>
```

---

# 🎨 **Figma‑Style Visual Mockup (ASCII)**  
This is a structured, component‑accurate mockup — the closest thing to a Figma frame in ASCII.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                               App.tsx Layout                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────────────┐   │
│   │                         [ Debug ▢ ] (top-right)                      │   │
│   │   class="top-right-controls"                                         │   │
│   └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   <RealtimeProvider debug={debug}>                                           │
│                                                                              │
│     ┌────────────────────────────────────────────────────────────────────┐   │
│     │                           StreamingPage                           │   │
│     ├────────────────────────────────────────────────────────────────────┤   │
│     │                                                                    │   │
│     │   ┌────────────────────────────────────────────────────────────┐   │   │
│     │   │                CameraPreview (relative)                    │   │   │
│     │   │  class="camera-preview-container"                          │   │   │
│     │   │                                                            │   │   │
│     │   │   <video>                                                  │   │   │
│     │   │   <canvas> (capture)                                       │   │   │
│     │   │                                                            │   │   │
│     │   │   ┌────────────────────────────────────────────────────┐   │   │   │
│     │   │   │      RealtimeStreamingOverlay (Phase‑17)           │   │   │   │
│     │   │   │  class="streaming-overlay-container"               │   │   │   │
│     │   │   │                                                    │   │   │   │
│     │   │   │   [ Frame #42 ] (top-left)                         │   │   │   │
│     │   │   │   [ 3 detections ] (top-right, debug only)         │   │   │   │
│     │   │   └────────────────────────────────────────────────────┘   │   │   │
│     │   └────────────────────────────────────────────────────────────┘   │   │
│     │                                                                    │   │
│     └────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│     ┌────────────────────────────────────────────────────────────────────┐   │
│     │                     StreamDebugPanel (bottom-right)                │   │
│     │                     class="stream-debug-panel"                     │   │
│     │                                                                    │   │
│     │   Phase‑17 Debug Panel                                             │   │
│     │   ─────────────────────────────────────────────────────────────     │   │
│     │   Status: connected                                                │   │
│     │   Pipeline: p1                                                     │   │
│     │   WS URL: ws://localhost/ws/video/stream?pipeline_id=p1           │   │
│     │                                                                    │   │
│     │   Frames Sent: 120                                                 │   │
│     │   FPS (approx): 14.8                                               │   │
│     │   Throttler FPS: 15                                                │   │
│     │                                                                    │   │
│     │   Dropped Frames: 3                                                │   │
│     │   Drop Rate: 2.5%                                                  │   │
│     │   Slow‑Down Warnings: 1                                            │   │
│     │                                                                    │   │
│     │   Last 5 Frame Sizes:                                              │   │
│     │     • 1024 bytes                                                   │   │
│     │     • 980 bytes                                                    │   │
│     │     • 1100 bytes                                                   │   │
│     │                                                                    │   │
│     │   Last 5 Latencies:                                                │   │
│     │     • 32.1 ms                                                      │   │
│     │     • 28.4 ms                                                      │   │
│     │                                                                    │   │
│     │   Last Frame Index: 42                                             │   │
│     └────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

# ⭐ **What this gives you**

You now have:

### ✔ A complete CSS pack  
- Debug toggle  
- Debug panel  
- Streaming overlay  
- CameraPreview container  

### ✔ A Figma‑style mockup  
- Component hierarchy  
- Visual layout  
- Z‑index layering  
- Debug panel content  

### ✔ A layout that matches  
- FE‑4  
- FE‑6  
- FE‑7  
- Phase‑17 realtime architecture  

This is the **final, authoritative FE‑7 layout**.


