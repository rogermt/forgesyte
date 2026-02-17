Here’s the tight version you need, no fluff.

---

### Phase‑17 realtime architecture diagram

```text
+-------------------+          +------------------------+
|   CameraPreview   |          |    PipelineSelector    |
|-------------------|          |------------------------|
| - getUserMedia    |          | - choose pipelineId    |
| - draw to canvas  |          | - calls connect(id)    |
| - toBlob → bytes  |          +-----------+------------+
| - sendFrame(bytes)            |
+--------------+----------------+
               |
               v
      +--------------------+
      |  useRealtimeContext|
      |--------------------|
      | wraps useRealtime  |
      | exposes:           |
      |  - connect         |
      |  - disconnect      |
      |  - sendFrame       |
      |  - state:          |
      |    isConnected     |
      |    isConnecting    |
      |    connectionStatus|
      |    lastResult      |
      |    droppedFrames   |
      |    slowDownWarnings|
      |    lastError       |
      +----------+---------+
                 |
                 v
        +------------------+
        |   useRealtime    |
        |  (Phase‑17 hook) |
        |------------------|
        | - builds ws URL  |
        | - owns pipelineId|
        | - owns throttler |
        | - connect(id)    |
        | - disconnect()   |
        | - sendFrame()    |
        |   → throttler    |
        |   → ws.sendBinary|
        | - maps ws state  |
        +---------+--------+
                  |
                  v
        +----------------------+
        |    useWebSocket      |
        |----------------------|
        | - WebSocket connect  |
        | - isConnected        |
        | - isConnecting       |
        | - connectionStatus   |
        | - lastResult         |
        | - droppedFrames      |
        | - slowDownWarnings   |
        | - lastError          |
        | - sendBinaryFrame()  |
        | - disconnect()       |
        +----------+-----------+
                   |
                   v
        +--------------------------+
        |  /ws/video/stream        |
        |  Backend WebSocket API   |
        |--------------------------|
        | - validate pipeline_id   |
        | - receive JPEG frames    |
        | - run pipeline           |
        | - send {frame_index,     |
        |        result}           |
        | - emit slow_down, drop   |
        +--------------------------+

UI consumers of state:
- RealtimeOverlay: uses state.lastResult → detections
- ErrorBanner: uses state.lastError
- StreamDebugPanel: uses isConnected, droppedFrames, slowDownWarnings, etc.
```

---

### Phase‑17 debugging guide (WebSocket + FPS + backpressure)

#### 1. Connection issues

**Symptoms:**
- `connectionStatus` stuck on `"connecting"` or `"failed"`
- `isConnected` is `false`
- No messages arriving

**Check:**

- **URL construction in `useRealtime`:**

  ```ts
  ws://localhost:8000/ws/video/stream?pipeline_id=${pipelineId}&api_key=...
  ```

  - Log the final URL when `connect(pipelineId)` is called.
  - Confirm `pipelineId` is non‑empty when you expect a connection.

- **Backend health:**
  - Hit `/v1/health` manually.
  - Check server logs for WebSocket errors (invalid pipeline, auth, etc.).

- **Frontend state:**
  - Log `connectionStatus` from `useRealtimeContext` in `StreamDebugPanel`.
  - If it flips to `"failed"`, inspect `lastError`.

#### 2. No frames arriving / no detections

**Symptoms:**
- `lastResult` stays `null`
- Overlay never renders
- Backend shows no frame logs

**Check:**

- **CameraPreview:**
  - Confirm `getUserMedia` resolves.
  - Confirm `requestAnimationFrame` loop is running.
  - Confirm `canvas.toBlob` is called and produces a JPEG.
  - Log the byte length before calling `sendFrame(bytes)`.

- **useRealtime:**
  - Add a log inside `sendFrame` to confirm it’s being called.
  - Ensure `pipelineId` is set (you called `connect("p1")`).

- **useWebSocket:**
  - Confirm `sendBinaryFrame` is invoked (use `expectFrameSent()` in tests).
  - If using mocks, ensure they match the real API shape.

- **Backend:**
  - Log when a frame is received (size, frame_index).
  - If frames are rejected, check validation (JPEG, size, etc.).

#### 3. FPS / throttling issues

**Symptoms:**
- Too many frames → backend overloaded
- Too few frames → choppy UI
- `slowDownWarnings` increments

**Check:**

- **FPSThrottler usage in `useRealtime`:**
  - Initial FPS: 15
  - On `slowDownWarnings > 0`, you recreate with FPS 5.

  ```ts
  if (ws.slowDownWarnings > 0 && throttlerRef.current) {
    throttlerRef.current = new FPSThrottler(5);
  }
  ```

- **Debugging strategy:**
  - Log every time `throttlerRef.current.throttle` executes.
  - Log current FPS setting when `slowDownWarnings` changes.
  - In tests, fake timers + a mock throttler can assert call frequency.

#### 4. Backpressure (drops + slow_down)

**Symptoms:**
- `droppedFrames` increasing
- `slowDownWarnings` increasing
- StreamDebugPanel shows warnings

**Check:**

- **Backend:**
  - Inspect logic that emits `slow_down` and drops frames.
  - Confirm thresholds (queue length, processing time) are set as expected.

- **Frontend:**
  - `useWebSocket` should map backend messages into:
    - `droppedFrames`
    - `slowDownWarnings`
    - `lastError` (for hard failures)
  - `useRealtime` should:
    - React to `slowDownWarnings` by lowering FPS.
    - Surface `droppedFrames` and `slowDownWarnings` in `state`.

- **UI:**
  - StreamDebugPanel should show:
    - current FPS (derived from throttler or frames/time)
    - droppedFrames
    - slowDownWarnings
  - Use this panel as your live “backpressure dashboard”.

#### 5. Error handling

**Symptoms:**
- ErrorBanner shows generic or no message
- Connection drops unexpectedly

**Check:**

- **Backend error payloads:**
  - Ensure errors include a stable `error` code and optional `detail`.

- **useWebSocket:**
  - Map error messages into `lastError`.

- **useRealtime:**
  - Expose `lastError` in `state`.

- **ErrorBanner:**
  - Map known codes (`invalid_pipeline`, `invalid_frame`, etc.) to friendly messages.
  - On “Retry”, call `connect(currentPipelineId)`.

#### 6. Test‑driven debugging

When something feels off, write a small Vitest around the hook:

- For `useRealtime`:
  - Mock `useWebSocket` with `createMockWebSocket`.
  - Assert:
    - `connect()` changes URL / pipelineId.
    - `sendFrame()` calls `sendBinaryFrame`.
    - `slowDownWarnings` triggers FPS reduction (you can mock FPSThrottler).

- For `CameraPreview`:
  - Mock `getUserMedia`, `<canvas>`, and `toBlob`.
  - Assert `sendFrame` is called with non‑empty bytes.

- For `StreamDebugPanel`:
  - Mock `useRealtimeContext` with known values.
  - Assert it renders status, FPS, drops, slow_down warnings.

---
Roger — here is the **cleanest, clearest, most operationally useful Phase‑17 “Golden Path” E2E trace** you can possibly have.  
This is the *single canonical flow* of one frame moving through your entire realtime system:

- **CameraPreview → useRealtimeContext → useRealtime → useWebSocket → Backend → useWebSocket → useRealtime → RealtimeOverlay**

And I’ll give you:

1. **A step‑by‑step trace with explicit log points**  
2. **A full ASCII architecture diagram of the golden path**  

This is the kind of thing you put in `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_GOLDEN_PATH.md`.

Let’s lock it in.

---

# ⭐ **PHASE‑17 GOLDEN PATH — ONE FRAME, END‑TO‑END**

Below is the **exact sequence** of events when a single frame is captured, sent, processed, and rendered.

Each step includes:

- **Component / Hook**
- **Action**
- **Data shape**
- **Recommended log point**

This is the authoritative trace.

---

# 🔥 **1. CameraPreview — Capture & Encode**

### Component:
`src/components/CameraPreview.tsx`

### Action:
- `requestAnimationFrame` loop fires
- `<video>` frame drawn to `<canvas>`
- `canvas.toBlob()` produces JPEG bytes
- Convert Blob → `Uint8Array`
- Call `sendFrame(bytes)`

### Data:
```
Uint8Array([ ... JPEG bytes ... ])
```

### Log point:
```ts
console.debug("[CameraPreview] sending frame", { size: bytes.length });
```

---

# 🔥 **2. useRealtimeContext — Pass Through**

### Hook:
`useRealtimeContext()`

### Action:
- Simply forwards `sendFrame(bytes)` to `useRealtime`

### Log point:
```ts
console.debug("[useRealtimeContext] forwarding frame");
```

---

# 🔥 **3. useRealtime — FPS Throttling + WebSocket Dispatch**

### Hook:
`useRealtime()`

### Action:
- `sendFrame(bytes)` calls:
  - `throttlerRef.current.throttle(() => ws.sendBinaryFrame(bytes))`

### Data:
```
Uint8Array([...])
```

### Log point:
```ts
console.debug("[useRealtime] throttled send", {
  slowDownWarnings: ws.slowDownWarnings,
  fps: throttlerRef.current.fps,
});
```

---

# 🔥 **4. useWebSocket — Binary Send**

### Hook:
`useWebSocket()`

### Action:
- Calls `websocket.send(bytes)`
- Increments internal counters

### Log point:
```ts
console.debug("[useWebSocket] sendBinaryFrame", { size: bytes.length });
```

---

# 🔥 **5. Backend — Receive Frame**

### Endpoint:
`/ws/video/stream`

### Action:
- Validate JPEG
- Assign `frame_index`
- Run pipeline
- Produce result

### Data:
```
{
  frame_index: 42,
  result: {
    detections: [
      { x, y, w, h, label, score }
    ]
  }
}
```

### Log point:
```python
logger.info("Frame received", frame_index=frame_index, size=len(frame_bytes))
logger.info("Pipeline result", frame_index=frame_index, detections=len(result["detections"]))
```

---

# 🔥 **6. Backend → Frontend — Send Result**

### Message:
```
{
  "frame_index": 42,
  "result": { ... }
}
```

### Log point:
```python
logger.info("Sending result", frame_index=frame_index)
```

---

# 🔥 **7. useWebSocket — Receive Result**

### Hook:
`useWebSocket()`

### Action:
- Parse JSON
- Update:
  - `lastResult`
  - `droppedFrames`
  - `slowDownWarnings`
  - `lastError`

### Log point:
```ts
console.debug("[useWebSocket] received result", {
  frame_index: msg.frame_index,
  detections: msg.result?.detections?.length,
});
```

---

# 🔥 **8. useRealtime — Map State**

### Hook:
`useRealtime()`

### Action:
- Maps `ws.lastResult` → `state.lastResult`
- Triggers React re-render

### Log point:
```ts
console.debug("[useRealtime] updated state", {
  frame_index: state.lastResult?.frame_index,
});
```

---

# 🔥 **9. RealtimeOverlay — Render Detections**

### Component:
`src/components/RealtimeOverlay.tsx`

### Action:
- Reads `state.lastResult`
- Converts to detections via `toDetections()`
- Renders `<BoundingBoxOverlay detections={...} />`
- Renders frame index label

### Log point:
```ts
console.debug("[RealtimeOverlay] rendering", {
  frame_index: lastResult.frame_index,
  detections: detections.length,
});
```

---

# ⭐ **FULL GOLDEN PATH DIAGRAM**

```
+--------------------------------------------------------------+
|                        CameraPreview                         |
|--------------------------------------------------------------|
| requestAnimationFrame → drawImage → toBlob → Uint8Array      |
| sendFrame(bytes)                                             |
+-------------------------------+------------------------------+
                                |
                                v
+-------------------------------+------------------------------+
|                    useRealtimeContext                        |
|--------------------------------------------------------------|
| forwards sendFrame(bytes) → useRealtime                      |
+-------------------------------+------------------------------+
                                |
                                v
+-------------------------------+------------------------------+
|                          useRealtime                         |
|--------------------------------------------------------------|
| throttler.throttle(fn)                                        |
| fn → ws.sendBinaryFrame(bytes)                                |
| state = map(ws)                                               |
+-------------------------------+------------------------------+
                                |
                                v
+-------------------------------+------------------------------+
|                         useWebSocket                         |
|--------------------------------------------------------------|
| websocket.send(bytes)                                         |
| websocket.onmessage → update:                                 |
|   lastResult                                                   |
|   droppedFrames                                                |
|   slowDownWarnings                                             |
|   lastError                                                    |
+-------------------------------+------------------------------+
                                |
                                v
+-------------------------------+------------------------------+
|                     Backend WebSocket API                    |
|--------------------------------------------------------------|
| receive JPEG bytes                                             |
| validate                                                       |
| frame_index++                                                  |
| run pipeline                                                   |
| send {frame_index, result}                                    |
+-------------------------------+------------------------------+
                                |
                                v
+-------------------------------+------------------------------+
|                         useWebSocket                         |
|--------------------------------------------------------------|
| receives result → updates ws.lastResult                       |
+-------------------------------+------------------------------+
                                |
                                v
+-------------------------------+------------------------------+
|                          useRealtime                         |
|--------------------------------------------------------------|
| maps ws.lastResult → state.lastResult                         |
| triggers re-render                                             |
+-------------------------------+------------------------------+
                                |
                                v
+-------------------------------+------------------------------+
|                       RealtimeOverlay                        |
|--------------------------------------------------------------|
| toDetections(lastResult.result)                               |
| <BoundingBoxOverlay detections={...} />                       |
| "Frame #42"                                                   |
+--------------------------------------------------------------+
```

---

# ⭐ Final Summary

You now have:

### ✔ A complete Phase‑17 golden path trace  
### ✔ Explicit log points at every hop  
### ✔ A full ASCII architecture diagram  
### ✔ A single authoritative reference for debugging  


You’re basically asking for a “turn the lights on everywhere” mode for Phase‑17. Let’s wire that in.

---

### Golden Path Debug Mode (UI toggle)

**Goal:** One toggle in the UI that:

- Enables verbose logging along the golden path  
- Surfaces extra debug UI (overlay + panel)  
- Flows down into `useRealtime`/`useWebSocket` as `debug: true`

#### 1. Add a debug flag to `useRealtime`

```ts
// useRealtime.ts
export interface UseRealtimeOptions {
  pipelineId?: string;
  apiKey?: string;
  debug?: boolean;
}

export function useRealtime(options: UseRealtimeOptions = {}): UseRealtimeReturn {
  const { pipelineId: initialPipelineId, apiKey, debug = false } = options;

  // ...
  const ws = useWebSocket({
    url: wsUrl,
    plugin: pipelineId || "",
    apiKey,
    debug, // ← propagate
  });

  if (debug) {
    console.debug("[useRealtime] init", { wsUrl, pipelineId: initialPipelineId });
  }

  const sendFrame = useCallback(
    (bytes: Uint8Array | ArrayBuffer) => {
      if (!throttlerRef.current) return;
      if (debug) console.debug("[useRealtime] sendFrame", { size: (bytes as Uint8Array).length });

      throttlerRef.current.throttle(() => {
        ws.sendBinaryFrame(bytes);
      });
    },
    [ws, debug]
  );

  // ...
}
```

#### 2. Make RealtimeProvider accept a debug prop

```tsx
// RealtimeContext.tsx
export const RealtimeProvider: React.FC<{ children: React.ReactNode; debug?: boolean }> = ({
  children,
  debug = false,
}) => {
  const realtime = useRealtime({ debug });
  return <RealtimeContext.Provider value={realtime}>{children}</RealtimeContext.Provider>;
};
```

#### 3. Add a UI toggle (e.g. in AppShell / DevBar)

```tsx
// DebugToggle.tsx
import { useState } from "react";
import { RealtimeProvider } from "../realtime/RealtimeContext";

export function AppWithRealtime() {
  const [debug, setDebug] = useState(false);

  return (
    <>
      <div className="debug-toggle">
        <label>
          <input
            type="checkbox"
            checked={debug}
            onChange={(e) => setDebug(e.target.checked)}
          />
          Golden Path Debug Mode
        </label>
      </div>

      <RealtimeProvider debug={debug}>
        {/* rest of app */}
      </RealtimeProvider>
    </>
  );
}
```

Now flipping the checkbox turns on/off golden‑path logging and any extra debug UI you gate behind `debug`.

---

### Backend log formatter for Phase‑17

**Goal:** Every Phase‑17 log line is structured, greppable, and clearly tagged.

#### 1. Define a small helper

```python
# app/logging_phase17.py
import logging

logger = logging.getLogger("phase17")

def log_phase17(event: str, **fields):
  logger.info("phase17 %s %s", event, fields)
```

#### 2. Use it along the golden path

```python
# when frame received
log_phase17(
    "frame_received",
    frame_index=frame_index,
    size=len(frame_bytes),
    pipeline_id=pipeline_id,
)

# when pipeline result ready
log_phase17(
    "pipeline_result",
    frame_index=frame_index,
    detections=len(result.get("detections", [])),
)

# when slow_down emitted
log_phase17(
    "backpressure_slow_down",
    frame_index=frame_index,
    queue_len=current_queue_len,
)
```

#### 3. Configure logger format

```python
# main logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

# optional: route phase17 logs to separate file
phase17_handler = logging.FileHandler("phase17.log")
phase17_handler.setLevel(logging.INFO)
phase17_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))

phase17_logger = logging.getLogger("phase17")
phase17_logger.addHandler(phase17_handler)
phase17_logger.propagate = False
```

Now you can `grep 'phase17 frame_received'` and see the whole golden path.

---

### Frontend devtools overlay for realtime state

**Goal:** A small overlay that shows live Phase‑17 state on top of the app when debug mode is on.

#### 1. Devtools overlay component

```tsx
// RealtimeDevtoolsOverlay.tsx
import { useRealtimeContext } from "../realtime/RealtimeContext";

export function RealtimeDevtoolsOverlay() {
  const { state } = useRealtimeContext();

  return (
    <div
      style={{
        position: "fixed",
        bottom: 8,
        right: 8,
        padding: "8px 12px",
        background: "rgba(0,0,0,0.8)",
        color: "#0f0",
        fontSize: 12,
        zIndex: 9999,
        borderRadius: 4,
        fontFamily: "monospace",
      }}
    >
      <div>Phase‑17 Realtime</div>
      <div>status: {state.connectionStatus}</div>
      <div>connected: {String(state.isConnected)}</div>
      <div>droppedFrames: {state.droppedFrames}</div>
      <div>slowDownWarnings: {state.slowDownWarnings}</div>
      <div>lastError: {state.lastError ? state.lastError.code ?? "yes" : "none"}</div>
      <div>hasResult: {state.lastResult ? "yes" : "no"}</div>
    </div>
  );
}
```

#### 2. Render it only in debug mode

Extend the earlier `AppWithRealtime`:

```tsx
export function AppWithRealtime() {
  const [debug, setDebug] = useState(false);

  return (
    <>
      <div className="debug-toggle">
        <label>
          <input
            type="checkbox"
            checked={debug}
            onChange={(e) => setDebug(e.target.checked)}
          />
          Golden Path Debug Mode
        </label>
      </div>

      <RealtimeProvider debug={debug}>
        {/* main app */}
        {debug && <RealtimeDevtoolsOverlay />}
      </RealtimeProvider>
    </>
  );
}
```

Now you’ve got:

- A **single toggle** that:
  - Turns on verbose golden‑path logging
  - Enables a realtime overlay
- Backend logs that are **structured and Phase‑17‑tagged**
- A visual, always‑on‑top view of realtime state when you need it

Here you go, Roger — the **tiny, brutally practical Phase‑17 Golden Path Release Checklist**.  
This is the one you run **before every Phase‑17 release**, and it’s intentionally short enough that you can execute it in under two minutes.

I’ll keep it crisp, operational, and aligned with the golden‑path trace we built.

---

# ⭐ **Phase‑17 Golden Path Release Checklist**  
*One frame. One path. Everything must work.*

---

## **1. Camera → Bytes**
**Goal:** The frontend can capture a frame and produce JPEG bytes.

- [ ] Webcam permission prompt appears  
- [ ] CameraPreview shows live video  
- [ ] Canvas capture loop runs (check console: `[CameraPreview] sending frame`)  
- [ ] `bytes.length > 0`  

**If this fails:**  
CameraPreview or canvas encoding is broken.

---

## **2. Bytes → WebSocket**
**Goal:** The frontend can send a binary frame.

- [ ] `sendFrame(bytes)` is called  
- [ ] `[useRealtime] throttled send` appears in console  
- [ ] `[useWebSocket] sendBinaryFrame` appears in console  

**If this fails:**  
`useRealtime` or `useWebSocket` is miswired.

---

## **3. WebSocket → Backend**
**Goal:** Backend receives the frame.

- [ ] Backend logs:  
  `phase17 frame_received { frame_index: 0, size: ... }`  
- [ ] No `invalid_frame` errors  
- [ ] No `frame_too_large` errors  

**If this fails:**  
JPEG validation or WebSocket routing is broken.

---

## **4. Backend → Pipeline**
**Goal:** Pipeline runs on the frame.

- [ ] Backend logs:  
  `phase17 pipeline_result { frame_index: 0, detections: N }`  
- [ ] No exceptions in pipeline logs  

**If this fails:**  
Pipeline registry or model inference is broken.

---

## **5. Pipeline → WebSocket Response**
**Goal:** Backend sends a valid result message.

- [ ] Backend logs:  
  `phase17 sending_result { frame_index: 0 }`  
- [ ] No `pipeline_failure` errors  

**If this fails:**  
Serialization or pipeline output formatting is broken.

---

## **6. WebSocket → useWebSocket**
**Goal:** Frontend receives the result.

- [ ] Console:  
  `[useWebSocket] received result { frame_index: 0 }`  
- [ ] `state.lastResult !== null`  

**If this fails:**  
Message parsing or WebSocket event handling is broken.

---

## **7. useWebSocket → useRealtime**
**Goal:** Realtime state updates.

- [ ] Console:  
  `[useRealtime] updated state { frame_index: 0 }`  
- [ ] `state.connectionStatus === "connected"`  
- [ ] `state.lastResult.frame_index === 0`  

**If this fails:**  
State mapping or hook memoization is broken.

---

## **8. useRealtime → RealtimeOverlay**
**Goal:** Overlay renders detections.

- [ ] Overlay appears  
- [ ] Bounding boxes match expected positions  
- [ ] Frame index label updates  

**If this fails:**  
Detection mapping or overlay rendering is broken.

---

# ⭐ **Optional: Backpressure sanity check**
Run this only if you changed throttling or backend queueing.

- [ ] Force slow backend → see `slowDownWarnings > 0`  
- [ ] FPS drops from 15 → 5  
- [ ] `droppedFrames` increments  

---

# ⭐ **Optional: Error path sanity check**
- [ ] Invalid pipeline → ErrorBanner shows  
- [ ] Disconnect → connectionStatus = `"disconnected"`  
- [ ] Retry → reconnects cleanly  

---

# ⭐ **If all boxes are checked → Phase‑17 is safe to release.**

