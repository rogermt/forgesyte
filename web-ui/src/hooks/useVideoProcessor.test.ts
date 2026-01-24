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
      json: async () => ({ success: true, result: { detections: [] } }),
    });

    renderHook(() =>
      useVideoProcessor({
        videoRef,
        pluginId: "plugin",
        toolName: "tool",
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

    expect(fetchMock).toHaveBeenCalledWith(
      "/plugins/run",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plugin_id: "plugin",
          tool_name: "tool",
          inputs: {
            frame_base64: "data:image/jpeg;base64,mock",
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

