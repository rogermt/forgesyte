## Code Skeletons (Concrete, Wired to Decisions)


# ⭐ **PHASE‑17 FRONTEND TEST SKELETONS (Commit FE‑1 → FE‑8, Final & Corrected)**  
*Real‑Time Streaming Inference — WebSocket + Realtime UI*

Each test skeleton is atomic, testable, and aligned with the commit it belongs to.

---

# **FE‑1 — useWebSocket Test Skeleton**

### Story  
As a frontend engineer, I want tests that verify the WebSocket hook handles all Phase‑17 message types.

### Test File  
`src/hooks/useWebSocket.test.ts`

### Test Skeleton  
```ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useWebSocket } from "./useWebSocket";

describe("useWebSocket (Phase‑17)", () => {
  let wsMock: any;

  beforeEach(() => {
    wsMock = {
      send: vi.fn(),
      close: vi.fn(),
      readyState: WebSocket.OPEN,
      onopen: null,
      onmessage: null,
      onclose: null,
      onerror: null,
    };

    global.WebSocket = vi.fn(() => wsMock) as any;
  });

  it("connects and sets status to connected", () => {
    const { result } = renderHook(() => useWebSocket("ws://test"));
    act(() => wsMock.onopen?.());
    expect(result.current.status).toBe("connected");
  });

  it("handles result messages", () => {
    const { result } = renderHook(() => useWebSocket("ws://test"));
    act(() => wsMock.onopen?.());

    act(() =>
      wsMock.onmessage?.({
        data: JSON.stringify({ frame_index: 1, result: { foo: "bar" } }),
      }),
    );

    expect(result.current.lastResult?.frame_index).toBe(1);
  });

  it("increments droppedFrames", () => {
    const { result } = renderHook(() => useWebSocket("ws://test"));
    act(() => wsMock.onopen?.());

    act(() =>
      wsMock.onmessage?.({
        data: JSON.stringify({ frame_index: 2, dropped: true }),
      }),
    );

    expect(result.current.droppedFrames).toBe(1);
  });

  it("increments slowDownWarnings", () => {
    const { result } = renderHook(() => useWebSocket("ws://test"));
    act(() => wsMock.onopen?.());

    act(() =>
      wsMock.onmessage?.({
        data: JSON.stringify({ warning: "slow_down" }),
      }),
    );

    expect(result.current.slowDownWarnings).toBe(1);
  });

  it("sets lastError on error messages", () => {
    const { result } = renderHook(() => useWebSocket("ws://test"));
    act(() => wsMock.onopen?.());

    act(() =>
      wsMock.onmessage?.({
        data: JSON.stringify({ error: "invalid_frame", detail: "bad" }),
      }),
    );

    expect(result.current.lastError?.error).toBe("invalid_frame");
  });

  it("sendFrame sends binary data", () => {
    const { result } = renderHook(() => useWebSocket("ws://test"));
    act(() => wsMock.onopen?.());

    const bytes = new Uint8Array([1, 2, 3]);
    act(() => result.current.sendFrame(bytes));

    expect(wsMock.send).toHaveBeenCalledWith(bytes);
  });
});
```

---

# **FE‑2 — useRealtime Test Skeleton**

### Story  
As a frontend engineer, I want tests verifying realtime orchestration, FPS throttling, and WebSocket integration.

### Test File  
`src/realtime/useRealtime.test.ts`

### Test Skeleton  
```ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useRealtime } from "./useRealtime";

vi.mock("../hooks/useWebSocket", () => {
  const wsMock = {
    status: "connected",
    lastResult: null,
    droppedFrames: 0,
    slowDownWarnings: 0,
    lastError: null,
    sendFrame: vi.fn(),
    disconnect: vi.fn(),
  };
  return {
    __esModule: true,
    useWebSocket: () => wsMock,
  };
});

describe("useRealtime (Phase‑17)", () => {
  it("connect() sets pipelineId and resets counters", () => {
    const { result } = renderHook(() => useRealtime());

    act(() => result.current.connect("p1"));

    expect(result.current.state.framesSent).toBe(0);
    expect(result.current.state.status).toBe("connected");
  });

  it("sendFrame increments framesSent", () => {
    const { result } = renderHook(() => useRealtime());
    act(() => result.current.connect("p1"));

    act(() => result.current.sendFrame(new Uint8Array([1])));

    expect(result.current.state.framesSent).toBe(1);
  });

  it("reduces FPS when slowDownWarnings > 0", () => {
    const { result } = renderHook(() => useRealtime());
    act(() => result.current.connect("p1"));

    // simulate slow_down
    result.current.state.slowDownWarnings = 1;

    act(() => result.current.sendFrame(new Uint8Array([1])));

    expect(result.current.state.framesSent).toBe(1);
  });

  it("disconnect() calls underlying WebSocket disconnect", () => {
    const { result } = renderHook(() => useRealtime());
    act(() => result.current.connect("p1"));

    act(() => result.current.disconnect());

    expect(result.current.state.status).toBe("disconnected");
  });
});
```

---

# **FE‑3 — CameraPreview Test Skeleton**

### Story  
As a frontend engineer, I want tests verifying webcam capture, JPEG conversion, and frame sending.

### Test File  
`src/components/CameraPreview.test.tsx`

### Test Skeleton  
```tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import { CameraPreview } from "./CameraPreview";
import { RealtimeProvider } from "../realtime/RealtimeContext";

describe("CameraPreview (Phase‑17)", () => {
  beforeEach(() => {
    Object.defineProperty(global.navigator, "mediaDevices", {
      value: {
        getUserMedia: vi.fn().mockResolvedValue({
          getTracks: () => [{ stop: vi.fn() }],
        }),
      },
    });

    HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
      drawImage: vi.fn(),
    }));

    HTMLCanvasElement.prototype.toBlob = vi.fn((cb) =>
      cb(new Blob([new Uint8Array([1, 2, 3])], { type: "image/jpeg" })),
    );
  });

  it("renders video and canvas", () => {
    const { container } = render(
      <RealtimeProvider>
        <CameraPreview />
      </RealtimeProvider>,
    );

    expect(container.querySelector("video")).toBeTruthy();
    expect(container.querySelector("canvas")).toBeTruthy();
  });

  it("calls sendFrame when a frame is captured", async () => {
    const sendFrame = vi.fn();

    vi.mock("../realtime/RealtimeContext", () => ({
      useRealtimeContext: () => ({ sendFrame }),
    }));

    render(<CameraPreview />);

    await new Promise((r) => setTimeout(r, 10));

    expect(sendFrame).toHaveBeenCalled();
  });
});
```

---

# **FE‑4 — RealtimeOverlay Test Skeleton**

### Story  
As a frontend engineer, I want tests verifying detection rendering and frame index display.

### Test File  
`src/components/RealtimeOverlay.test.tsx`

### Test Skeleton  
```tsx
import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import { RealtimeOverlay } from "./RealtimeOverlay";

describe("RealtimeOverlay (Phase‑17)", () => {
  it("renders nothing when no lastResult", () => {
    vi.mock("../realtime/RealtimeContext", () => ({
      useRealtimeContext: () => ({ state: { lastResult: null } }),
    }));

    const { container } = render(<RealtimeOverlay />);
    expect(container.firstChild).toBeNull();
  });

  it("renders detections and frame index", () => {
    vi.mock("../realtime/RealtimeContext", () => ({
      useRealtimeContext: () => ({
        state: {
          lastResult: {
            frame_index: 42,
            result: {
              detections: [
                { x: 0.1, y: 0.2, w: 0.3, h: 0.4, label: "person", score: 0.9 },
              ],
            },
          },
        },
      }),
    }));

    const { getByText } = render(<RealtimeOverlay />);
    expect(getByText("Frame #42")).toBeTruthy();
  });
});
```

---

# **FE‑5 — PipelineSelector Test Skeleton**

### Story  
As a frontend engineer, I want tests verifying pipeline selection triggers reconnect.

### Test File  
`src/components/PipelineSelector.test.tsx`

### Test Skeleton  
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, fireEvent } from "@testing-library/react";
import { PipelineSelector } from "./PipelineSelector";

describe("PipelineSelector (Phase‑17)", () => {
  it("calls connect with selected pipeline", () => {
    const connect = vi.fn();
    const disconnect = vi.fn();

    vi.mock("../realtime/RealtimeContext", () => ({
      useRealtimeContext: () => ({ connect, disconnect }),
    }));

    const { getByRole } = render(<PipelineSelector />);
    const select = getByRole("combobox");

    fireEvent.change(select, { target: { value: "p1" } });

    expect(disconnect).toHaveBeenCalled();
    expect(connect).toHaveBeenCalledWith("p1");
  });
});
```

---

# **FE‑6 — ErrorBanner Test Skeleton**

### Story  
As a user, I want clear error messages and retry behavior.

### Test File  
`src/components/ErrorBanner.test.tsx`

### Test Skeleton  
```tsx
import { describe, it, expect, vi } from "vitest";
import { render, fireEvent } from "@testing-library/react";
import { ErrorBanner } from "./ErrorBanner";

describe("ErrorBanner (Phase‑17)", () => {
  it("renders user‑friendly message", () => {
    vi.mock("../realtime/RealtimeContext", () => ({
      useRealtimeContext: () => ({
        state: {
          lastError: { error: "invalid_pipeline", detail: "bad" },
        },
        connect: vi.fn(),
      }),
    }));

    const { getByText } = render(<ErrorBanner />);
    expect(getByText("The selected pipeline is not available.")).toBeTruthy();
  });

  it("calls connect on Retry", () => {
    const connect = vi.fn();

    vi.mock("../realtime/RealtimeContext", () => ({
      useRealtimeContext: () => ({
        state: {
          lastError: { error: "invalid_message", detail: "bad" },
        },
        connect,
      }),
    }));

    const { getByText } = render(<ErrorBanner />);
    fireEvent.click(getByText("Retry"));

    expect(connect).toHaveBeenCalled();
  });
});
```

---

# **FE‑7 — StreamDebugPanel Test Skeleton**

### Story  
As a developer, I want tests verifying FPS, drop rate, and status display.

### Test File  
`src/components/StreamDebugPanel.test.tsx`

### Test Skeleton  
```tsx
import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";
import { StreamDebugPanel } from "./StreamDebugPanel";

describe("StreamDebugPanel (Phase‑17)", () => {
  it("shows metrics from context", () => {
    vi.mock("../realtime/RealtimeContext", () => ({
      useRealtimeContext: () => ({
        state: {
          status: "connected",
          framesSent: 10,
          droppedFrames: 2,
          slowDownWarnings: 1,
          startTime: performance.now() - 1000,
        },
      }),
    }));

    const { getByText } = render(<StreamDebugPanel />);

    expect(getByText(/Frames sent/)).toBeTruthy();
    expect(getByText(/Slow‑down warnings/)).toBeTruthy();
  });
});
```
