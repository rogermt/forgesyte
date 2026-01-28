// web-ui/src/hooks/useVideoProcessor.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useVideoProcessor } from "./useVideoProcessor";

// Mock canvas context with toDataURL
const mockCanvas = {
  getContext: vi.fn().mockReturnValue({
    drawImage: vi.fn(),
  }),
  toDataURL: vi.fn().mockReturnValue("data:image/jpeg;base64,mock"),
  width: 640,
  height: 360,
};

// Mock document.createElement for canvas
const originalCreateElement = document.createElement.bind(document);
document.createElement = vi.fn((tagName: string) => {
  if (tagName === "canvas") {
    return mockCanvas as unknown as HTMLCanvasElement;
  }
  return originalCreateElement(tagName);
});

function mockVideo(readyState = 2) {
  return {
    readyState,
    videoWidth: 640,
    videoHeight: 360,
  } as unknown as HTMLVideoElement;
}

describe("useVideoProcessor", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.useFakeTimers();
    fetchMock = vi.fn();
    vi.spyOn(window, "fetch").mockImplementation(fetchMock);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("skips frame extraction when video not ready", () => {
    const videoRef = { current: mockVideo(0) };

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "p",
        toolName: "t",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    // Advance timers but video not ready
    act(() => {
      vi.advanceTimersByTime(100);
    });

    expect(result.current.processing).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("sends correct backend payload on frame", async () => {
    const videoRef = { current: mockVideo() };

    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, result: { detections: [] } }),
    });

    renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "yolo-tracker",
        toolName: "track",
        fps: 30,
        device: "cuda",
        enabled: true,
      })
    );

    // Advance past first tick
    await act(async () => {
      vi.advanceTimersByTime(100);
      await Promise.resolve();
      vi.advanceTimersByTime(200);
    });

    // Should call correct endpoint with correct payload
    expect(fetchMock).toHaveBeenCalledWith(
      "/v1/plugins/yolo-tracker/tools/track/run",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          args: {
            frame_base64: "mock", // Raw base64 without data URL prefix
            device: "cuda",
            annotated: false,
          },
        }),
      })
    );
  });

  it("stores result in latestResult on success", async () => {
    const videoRef = { current: mockVideo() };
    const mockResult = { detections: [{ id: 1 }] };

    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, result: mockResult }),
    });

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "p",
        toolName: "t",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(100);
      await Promise.resolve();
      vi.advanceTimersByTime(200);
    });

    expect(result.current.latestResult).toEqual(mockResult);
    expect(result.current.error).toBeNull();
  });

  it("maintains rolling buffer", async () => {
    const videoRef = { current: mockVideo() };

    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, result: { x: 1 } }),
    });

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "p",
        toolName: "t",
        fps: 30,
        device: "cpu",
        enabled: true,
        bufferSize: 3,
      })
    );

    // Run multiple ticks
    for (let i = 0; i < 5; i++) {
      await act(async () => {
        vi.advanceTimersByTime(100);
        await Promise.resolve();
        vi.advanceTimersByTime(200);
      });
    }

    expect(result.current.buffer.length).toBe(3);
  });

  it("sets error on backend failure", async () => {
    const videoRef = { current: mockVideo() };

    fetchMock.mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ success: false, error: "Backend error" }),
    });

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "p",
        toolName: "t",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(100);
      await Promise.resolve();
      vi.advanceTimersByTime(200);
    });

    expect(result.current.error).toBe("Backend error");
  });

  it("tracks processing state", async () => {
    const videoRef = { current: mockVideo() };

    let resolveFetch: (value: Response) => void;
    fetchMock.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveFetch = resolve;
        })
    );

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "p",
        toolName: "t",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    // Advance time to trigger the first tick
    await act(async () => {
      vi.advanceTimersByTime(50);
      await Promise.resolve();
    });

    // Now processing should be true (request in flight)
    expect(result.current.processing).toBe(true);

    // Complete request
    await act(async () => {
      resolveFetch!({
        ok: true,
        json: async () => ({ success: true, result: {} }),
      } as Response);
      await Promise.resolve();
      vi.advanceTimersByTime(200);
    });

    expect(result.current.processing).toBe(false);
  });

  it("handles network failure with retry", async () => {
    const videoRef = { current: mockVideo() };

    fetchMock
      .mockRejectedValueOnce(new Error("Network error"))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, result: {} }),
      });

    renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "p",
        toolName: "t",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    // Advance to trigger first call
    await act(async () => {
      vi.advanceTimersByTime(50);
      await Promise.resolve();
    });

    // Advance past retry delay (200ms) + processing time
    await act(async () => {
      vi.advanceTimersByTime(400);
      await Promise.resolve();
    });

    // Should be called twice (initial + retry)
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("returns null latestResult initially", () => {
    const videoRef = { current: mockVideo() };

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "p",
        toolName: "t",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    expect(result.current.latestResult).toBeNull();
    expect(result.current.buffer).toEqual([]);
  });

  it("tracks request timing metrics", async () => {
    const videoRef = { current: mockVideo() };

    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, result: {} }),
    });

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "p",
        toolName: "t",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(100);
      await Promise.resolve();
      vi.advanceTimersByTime(200);
    });

    expect(result.current.lastTickTime).not.toBeNull();
    expect(result.current.lastRequestDuration).not.toBeNull();
  });
});

describe("useVideoProcessor - Base64 Format Guardrail", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.spyOn(window, "fetch").mockImplementation(
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ result: {} }),
      })
    );
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("sends raw base64 without data URL prefix to backend", async () => {
    const videoRef = { current: mockVideo() };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ result: {} }),
    });
    vi.spyOn(window, "fetch").mockImplementation(fetchMock);

    renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "yolo-tracker",
        toolName: "player_detection",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(100);
      await Promise.resolve();
      vi.advanceTimersByTime(200);
    });

    // Get the actual call and verify raw base64 (no data: prefix)
    const lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1];
    const body = JSON.parse(lastCall[1].body);
    const frameBase64 = body.args.frame_base64;

    // Guardrail: MUST NOT contain data URL prefix
    expect(frameBase64.startsWith("data:")).toBe(false);
    expect(frameBase64.includes("base64,")).toBe(false);

    // Guardrail: MUST equal raw base64 content only
    expect(frameBase64).toBe("mock");
  });
});

describe("useVideoProcessor - Endpoint Correctness", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.spyOn(window, "fetch").mockImplementation(
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ result: {} }),
      })
    );
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("calls the correct backend endpoint based on pluginId and toolName", async () => {
    const videoRef = { current: mockVideo() };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ result: {} }),
    });
    vi.spyOn(window, "fetch").mockImplementation(fetchMock);

    renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "forgesyte-yolo-tracker",
        toolName: "player_detection",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(100);
      await Promise.resolve();
      vi.advanceTimersByTime(200);
    });

    // Verify the correct endpoint is called
    expect(fetchMock).toHaveBeenCalledWith(
      "/v1/plugins/forgesyte-yolo-tracker/tools/player_detection/run",
      expect.objectContaining({
        method: "POST",
      })
    );
  });

  it("matches the manifest tool definition structure", async () => {
    const videoRef = { current: mockVideo() };

    // Simulate a manifest with tool definitions
    const manifest = {
      id: "forgesyte-yolo-tracker",
      name: "YOLO Football Tracker",
      tools: [
        {
          name: "player_detection",
          description: "Detect players in video frames",
          inputs: {
            type: "object",
            properties: {
              frame_base64: { type: "string" },
              device: { type: "string" },
              annotated: { type: "boolean" },
            },
          },
          outputs: {
            type: "object",
            properties: {
              detections: { type: "array" },
            },
          },
        },
      ],
    };

    // Verify tool exists in manifest
    const tool = manifest.tools.find((t) => t.name === "player_detection");
    expect(tool).toBeDefined();
    expect(tool?.inputs.properties).toHaveProperty("frame_base64");
    expect(tool?.inputs.properties).toHaveProperty("device");
    expect(tool?.inputs.properties).toHaveProperty("annotated");

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ result: { detections: [] } }),
    });
    vi.spyOn(window, "fetch").mockImplementation(fetchMock);

    renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "forgesyte-yolo-tracker",
        toolName: "player_detection",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(100);
      await Promise.resolve();
      vi.advanceTimersByTime(200);
    });

    // Verify the payload matches the manifest input schema
    const lastCall = fetchMock.mock.calls[fetchMock.mock.calls.length - 1];
    const body = JSON.parse(lastCall[1].body);

    expect(body.args).toHaveProperty("frame_base64");
    expect(body.args).toHaveProperty("device");
    expect(body.args).toHaveProperty("annotated");
  });

  it("handles HTTP 404 for missing plugin/tool", async () => {
    const videoRef = { current: mockVideo() };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({
        detail: "Plugin 'unknown-plugin' not found or has no tools",
      }),
    });
    vi.spyOn(window, "fetch").mockImplementation(fetchMock);

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "unknown-plugin",
        toolName: "unknown-tool",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(100);
      await Promise.resolve();
      vi.advanceTimersByTime(200);
    });

    expect(result.current.error).toContain("unknown-plugin");
  });

  it("handles HTTP 400 for invalid arguments", async () => {
    const videoRef = { current: mockVideo() };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({
        detail: "Invalid arguments for tool 'track': missing required field 'frame_base64'",
      }),
    });
    vi.spyOn(window, "fetch").mockImplementation(fetchMock);

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "yolo-tracker",
        toolName: "track",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(100);
      await Promise.resolve();
      vi.advanceTimersByTime(200);
    });

    expect(result.current.error).toContain("Invalid arguments");
  });

  it("handles HTTP 500 for server errors", async () => {
    const videoRef = { current: mockVideo() };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({
        detail: "Internal server error during tool execution",
      }),
    });
    vi.spyOn(window, "fetch").mockImplementation(fetchMock);

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "yolo-tracker",
        toolName: "track",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(100);
      await Promise.resolve();
      vi.advanceTimersByTime(200);
    });

    // The error should contain the server error message
    expect(result.current.error).toContain("Internal server error");
    expect(result.current.error).toContain("tool execution");
  });

  it("handles successful API response with different result structures", async () => {
    const videoRef = { current: mockVideo() };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        tool_name: "track",
        plugin_id: "yolo-tracker",
        result: { players: [], ball: null },
        processing_time_ms: 42,
      }),
    });
    vi.spyOn(window, "fetch").mockImplementation(fetchMock);

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "yolo-tracker",
        toolName: "track",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(100);
      await Promise.resolve();
      vi.advanceTimersByTime(200);
    });

    expect(result.current.latestResult).toEqual({
      players: [],
      ball: null,
    });
    expect(result.current.error).toBeNull();
  });
});

describe("useVideoProcessor - Metrics & Logging", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.spyOn(window, "fetch").mockImplementation(
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ success: true, result: { detections: [] } }),
      })
    );
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("tracks metrics on successful frame processing", async () => {
    const videoRef = { current: mockVideo() };

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "forgesyte-yolo-tracker",
        toolName: "player_detection",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(100);
      await Promise.resolve();
      vi.advanceTimersByTime(200);
    });

    expect(result.current.metrics).toBeDefined();
    expect(result.current.metrics.totalFrames).toBe(1);
    expect(result.current.metrics.successfulFrames).toBe(1);
    expect(result.current.metrics.failedFrames).toBe(0);
    expect(result.current.metrics.averageDurationMs).toBeGreaterThan(0);
  });

  it("tracks metrics on failed frame processing", async () => {
    const videoRef = { current: mockVideo() };

    vi.spyOn(window, "fetch").mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ success: false, error: "Server error" }),
    });

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "forgesyte-yolo-tracker",
        toolName: "player_detection",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(100);
      await Promise.resolve();
      vi.advanceTimersByTime(200);
    });

    expect(result.current.metrics.totalFrames).toBe(1);
    expect(result.current.metrics.successfulFrames).toBe(0);
    expect(result.current.metrics.failedFrames).toBe(1);
    expect(result.current.metrics.lastError).toContain("Server error");
  });

  it("accumulates metrics across multiple frames", async () => {
    const videoRef = { current: mockVideo() };

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "forgesyte-yolo-tracker",
        toolName: "player_detection",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    // Process 3 frames
    for (let i = 0; i < 3; i++) {
      await act(async () => {
        vi.advanceTimersByTime(100);
        await Promise.resolve();
        vi.advanceTimersByTime(200);
      });
    }

    expect(result.current.metrics.totalFrames).toBe(3);
    expect(result.current.metrics.successfulFrames).toBe(3);
    expect(result.current.metrics.averageDurationMs).toBeGreaterThan(0);
  });

  it("logs each frame processing attempt", async () => {
    const videoRef = { current: mockVideo() };

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "forgesyte-yolo-tracker",
        toolName: "player_detection",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(100);
      await Promise.resolve();
      vi.advanceTimersByTime(200);
    });

    expect(result.current.logs).toBeDefined();
    expect(result.current.logs.length).toBe(1);
    expect(result.current.logs[0]).toMatchObject({
      pluginId: "forgesyte-yolo-tracker",
      toolName: "player_detection",
      success: true,
      durationMs: expect.any(Number),
    });
  });

  it("logs contain error information on failure", async () => {
    const videoRef = { current: mockVideo() };

    vi.spyOn(window, "fetch").mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ success: false, error: "Bad request" }),
    });

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "forgesyte-yolo-tracker",
        toolName: "player_detection",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    await act(async () => {
      vi.advanceTimersByTime(100);
      await Promise.resolve();
      vi.advanceTimersByTime(200);
    });

    expect(result.current.logs.length).toBe(1);
    expect(result.current.logs[0].success).toBe(false);
    expect(result.current.logs[0].error).toContain("Bad request");
  });

  it("maintains rolling log buffer", async () => {
    const videoRef = { current: mockVideo() };

    const { result } = renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "forgesyte-yolo-tracker",
        toolName: "player_detection",
        fps: 30,
        device: "cpu",
        enabled: true,
      })
    );

    // Process more frames than default log buffer
    for (let i = 0; i < 10; i++) {
      await act(async () => {
        vi.advanceTimersByTime(100);
        await Promise.resolve();
        vi.advanceTimersByTime(200);
      });
    }

    // Logs should be accumulated (no size limit by default)
    expect(result.current.logs.length).toBe(10);
  });
});
