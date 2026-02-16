Roger — thank you for calling this out.  
And yes: **the mocking guide you pasted is now outdated** because your realtime layer has *changed underneath it*.

Phase‑17 introduced:

- `sendBinaryFrame()` instead of `sendFrame()`
- `isConnected`, `isConnecting`, `connectionStatus` instead of `status`
- `framesSent` counter
- A new `useRealtime` hook that wraps `useWebSocket`
- A new `useRealtimeContext` that exposes Phase‑17 state
- A new `useWebSocket` return type

Your old mocking guide was correct **for Phase‑10** and **early Phase‑17 skeletons**, but once we corrected:

- `useRealtime.ts`
- `RealtimeContext.tsx`
- `useWebSocket` API surface
- The test skeletons

…the mocking guide needed to be updated too.

So let’s fix this properly.

Below is the **final, authoritative Phase‑17 mocking guide**, replacing the outdated one.

---

# ⭐ **🔥 FINAL PHASE‑17 MOCKING GUIDE (UPDATED & CORRECT)**  
This is the version you should put into:

```
.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_MOCKING_GUIDE.md
```

Everything below matches:

- Your corrected `useRealtime.ts`
- Your corrected `RealtimeContext.tsx`
- Your corrected `useWebSocket` API
- Your Phase‑17 test skeletons
- Your Phase‑17 architecture

---

# ⭐ 1. The Golden Rule (unchanged)

Vitest hoists `vi.mock()` to the top of the file.

### ❌ Never reference top‑level variables inside a mock factory:

```ts
const mockFn = vi.fn();

vi.mock("./module", () => ({
  fn: mockFn, // ❌ mockFn is undefined at hoist time
}));
```

### ✔ Always create mocks *inside* the factory:

```ts
vi.mock("./module", () => {
  const mockFn = vi.fn();
  return { fn: mockFn };
});
```

---

# ⭐ 2. Phase‑17 `useWebSocket` — Correct Mock Shape

Your Phase‑17 hook expects this shape:

```ts
{
  isConnected: boolean;
  isConnecting: boolean;
  connectionStatus: "idle" | "connecting" | "connected" | "disconnected" | "failed";

  lastResult: any;
  droppedFrames: number;
  slowDownWarnings: number;
  lastError: any;

  sendBinaryFrame: (bytes) => void;
  disconnect: () => void;

  framesSent: number;
}
```

### ✔ Correct mock:

```ts
vi.mock("../hooks/useWebSocket", () => {
  const wsMock = {
    isConnected: true,
    isConnecting: false,
    connectionStatus: "connected",

    lastResult: null,
    droppedFrames: 0,
    slowDownWarnings: 0,
    lastError: null,

    sendBinaryFrame: vi.fn(),
    disconnect: vi.fn(),

    framesSent: 0,
  };

  return {
    __esModule: true,
    useWebSocket: () => wsMock,
  };
});
```

---

# ⭐ 3. Reusable `createMockWebSocket()` Helper (FINAL VERSION)

Put in:

```
src/test-utils/createMockWebSocket.ts
```

```ts
import { vi } from "vitest";

export function createMockWebSocket(overrides = {}) {
  return {
    isConnected: true,
    isConnecting: false,
    connectionStatus: "connected",

    lastResult: null,
    droppedFrames: 0,
    slowDownWarnings: 0,
    lastError: null,

    sendBinaryFrame: vi.fn(),
    disconnect: vi.fn(),

    framesSent: 0,

    ...overrides,
  };
}
```

---

# ⭐ 4. Phase‑17 `useRealtime` — Correct Mock Shape

Your Phase‑17 hook returns:

```ts
{
  connect: fn,
  disconnect: fn,
  sendFrame: fn,
  state: {
    isConnected,
    isConnecting,
    connectionStatus,
    lastResult,
    droppedFrames,
    slowDownWarnings,
    lastError,
  }
}
```

### ✔ Correct mock:

```ts
export function mockUseRealtime(overrides = {}) {
  const realtimeMock = {
    connect: vi.fn(),
    disconnect: vi.fn(),
    sendFrame: vi.fn(),
    state: {
      isConnected: true,
      isConnecting: false,
      connectionStatus: "connected",
      lastResult: null,
      droppedFrames: 0,
      slowDownWarnings: 0,
      lastError: null,
      ...overrides,
    },
  };

  vi.mock("../realtime/useRealtime", () => ({
    __esModule: true,
    useRealtime: () => realtimeMock,
  }));

  return realtimeMock;
}
```

---

# ⭐ 5. Phase‑17 `useRealtimeContext` — Correct Mock

```ts
export function mockRealtimeContext(overrides = {}) {
  const ctx = mockUseRealtime(overrides);

  vi.mock("../realtime/RealtimeContext", () => ({
    __esModule: true,
    useRealtimeContext: () => ctx,
  }));

  return ctx;
}
```

---

# ⭐ 6. CameraPreview Mocks (FINAL)

### Mock `getUserMedia`

```ts
Object.defineProperty(global.navigator, "mediaDevices", {
  value: {
    getUserMedia: vi.fn().mockResolvedValue({
      getTracks: () => [{ stop: vi.fn() }],
    }),
  },
});
```

### Mock `<canvas>`

```ts
HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
  drawImage: vi.fn(),
}));

HTMLCanvasElement.prototype.toBlob = vi.fn((cb) =>
  cb(new Blob([new Uint8Array([1, 2, 3])], { type: "image/jpeg" })),
);
```

---

# ⭐ 7. Vitest Matcher: `expectFrameSent()`

Put in:

```
src/test-utils/matchers.ts
```

```ts
import { expect } from "vitest";

expect.extend({
  toHaveSentFrame(received, expectedCount = 1) {
    const calls = received.sendBinaryFrame?.mock.calls.length ?? 0;
    const pass = calls === expectedCount;

    return {
      pass,
      message: () =>
        pass
          ? `Expected WebSocket NOT to have sent ${expectedCount} frames`
          : `Expected WebSocket to have sent ${expectedCount} frames, but got ${calls}`,
    };
  },
});
```

### Usage:

```ts
expect(wsMock).toHaveSentFrame();
expect(wsMock).toHaveSentFrame(3);
```

---

# ⭐ 8. Why Your Old Mocking Guide Is Now Wrong

Your old guide assumed:

- `sendFrame()` existed  
- `status` existed  
- `useRealtime` came from `RealtimeContext`  
- Phase‑10 message‑based realtime  
- No `sendBinaryFrame()`  
- No `framesSent`  
- No `connectionStatus`  
- No Phase‑17 streaming state  

Phase‑17 **replaced** all of that.

So yes — the old guide is now obsolete.

---

# ⭐ Final Summary

You now have:

### ✔ A reusable `createMockWebSocket()` helper  
### ✔ A corrected `useWebSocket` type definition  
### ✔ A full Phase‑17 mock suite  
### ✔ A Vitest matcher extension (`expectFrameSent()`)  
### ✔ A fully updated mocking guide that matches your actual code  

This is the **final, authoritative Phase‑17 mocking foundation**.

