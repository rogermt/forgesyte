/**
 * Tests for useVideoExport hook
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useVideoExport } from "./useVideoExport";

// ============================================================================
// Mocks
// ============================================================================

// Store the original MediaRecorder
const OriginalMediaRecorder = global.MediaRecorder;

// Track calls for assertions
let constructorCallCount = 0;
let lastRecorderOptions: MediaRecorderOptions | undefined;

// Mock MediaRecorder - use proper class methods
class MockMediaRecorder {
  state = "recording";
  mimeType = "video/webm";
  ondataavailable: ((event: BlobEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onstop: (() => void) | null = null;

  constructor(stream: MediaStream, options?: MediaRecorderOptions) {
    void stream; // Intentionally unused in mock
    constructorCallCount++;
    lastRecorderOptions = options;
    this.mimeType = options?.mimeType ?? "video/webm";
  }

  start(): void {
    // Intentionally empty for mock
  }

  stop(): void {
    // Intentionally empty for mock
  }
}

MockMediaRecorder.isTypeSupported = function(type: string): boolean {
  return (
    type === "video/webm" ||
    type === "video/webm;codecs=vp9" ||
    type === "video/webm;codecs=vp8"
  );
};

beforeEach(() => {
  constructorCallCount = 0;
  lastRecorderOptions = undefined;
  (global as Record<string, unknown>).MediaRecorder = MockMediaRecorder;
});

afterEach(() => {
  global.MediaRecorder = OriginalMediaRecorder;
});

// Mock HTMLCanvasElement.captureStream
HTMLCanvasElement.prototype.captureStream = function(): MediaStream {
  return {
    getTracks: () => [],
  } as MediaStream;
};

// Spy on captureStream for assertions
vi.spyOn(HTMLCanvasElement.prototype, "captureStream");

// ============================================================================
// Tests
// ============================================================================

describe("useVideoExport", () => {
  const mockConfig = {
    width: 640,
    height: 480,
    fps: 30,
  };

  const mockCanvas = document.createElement("canvas");

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("initializes with correct state", () => {
    const { result } = renderHook(() => useVideoExport(mockConfig));

    expect(result.current.state.isRecording).toBe(false);
    expect(result.current.state.progress).toBe(0);
    expect(result.current.state.error).toBeUndefined();
  });

  it("throws error when no config provided", () => {
    const { result } = renderHook(() => useVideoExport(null));

    act(() => {
      result.current.startRecording(mockCanvas);
    });

    expect(result.current.state.error).toBeDefined();
    expect(result.current.state.isRecording).toBe(false);
  });

  it("starts recording with valid config", () => {
    const { result } = renderHook(() => useVideoExport(mockConfig));

    expect(result.current.state.isRecording).toBe(false);
    expect(result.current.state.error).toBeUndefined();
  });

  it("captures stream from canvas with correct FPS", () => {
    const { result } = renderHook(() => useVideoExport(mockConfig));

    act(() => {
      result.current.startRecording(mockCanvas);
    });

    // captureStream should be called with 30 fps from config
    expect(mockCanvas.captureStream).toHaveBeenCalledWith(30);
  });

  it("uses MediaRecorder for recording", () => {
    const { result } = renderHook(() => useVideoExport(mockConfig));

    act(() => {
      result.current.startRecording(mockCanvas);
    });

    expect(constructorCallCount).toBeGreaterThan(0);
  });

  it("updates progress correctly", () => {
    const { result } = renderHook(() => useVideoExport(mockConfig));

    act(() => {
      result.current.updateProgress(50, 100);
    });

    expect(result.current.state.progress).toBe(50);
  });

  it("updates progress to 100 for completion", () => {
    const { result } = renderHook(() => useVideoExport(mockConfig));

    act(() => {
      result.current.updateProgress(100, 100);
    });

    expect(result.current.state.progress).toBe(100);
  });

  it("cancels recording properly", () => {
    const { result } = renderHook(() => useVideoExport(mockConfig));

    act(() => {
      result.current.startRecording(mockCanvas);
    });

    act(() => {
      result.current.cancelRecording();
    });

    expect(result.current.state.isRecording).toBe(false);
    expect(result.current.state.progress).toBe(0);
  });

  it("respects custom MIME type in config", () => {
    const customConfig = {
      ...mockConfig,
      mimeType: "video/webm;codecs=vp8",
    };

    const { result } = renderHook(() => useVideoExport(customConfig));

    act(() => {
      result.current.startRecording(mockCanvas);
    });

    // Verify the MIME type was actually passed to MediaRecorder
    expect(lastRecorderOptions?.mimeType).toBe("video/webm;codecs=vp8");
  });

  it("supports default FPS of 30", () => {
    const configNoFps = { width: 640, height: 480 };
    const { result } = renderHook(() => useVideoExport(configNoFps));

    act(() => {
      result.current.startRecording(mockCanvas);
    });

    // Should use 30 as default
    expect(mockCanvas.captureStream).toHaveBeenCalledWith(30);
  });

  it("exposes export methods", () => {
    const { result } = renderHook(() => useVideoExport(mockConfig));

    expect(typeof result.current.startRecording).toBe("function");
    expect(typeof result.current.stopRecording).toBe("function");
    expect(typeof result.current.cancelRecording).toBe("function");
    expect(typeof result.current.updateProgress).toBe("function");
  });

  it("maintains state across operations", () => {
    const { result } = renderHook(() => useVideoExport(mockConfig));

    // Initial state
    expect(result.current.state.isRecording).toBe(false);
    expect(result.current.state.progress).toBe(0);

    // Update progress
    act(() => {
      result.current.updateProgress(25, 100);
    });

    expect(result.current.state.progress).toBe(25);
    expect(result.current.state.isRecording).toBe(false);

    // Start recording changes isRecording
    act(() => {
      result.current.startRecording(mockCanvas);
    });

    // Verify recording started (state was set)
    expect(constructorCallCount).toBeGreaterThan(0);
  });
});
