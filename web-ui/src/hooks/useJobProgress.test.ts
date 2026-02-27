/**
 * Tests for useJobProgress hook (TDD - Phase 7)
 *
 * Tests for real-time job progress via WebSocket.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useJobProgress } from "./useJobProgress";

// Mock WebSocket constants
const CONNECTING = 0;
const OPEN = 1;
const CLOSING = 2;
const CLOSED = 3;

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = CONNECTING;
  static OPEN = OPEN;
  static CLOSING = CLOSING;
  static CLOSED = CLOSED;

  static instances: MockWebSocket[] = [];

  readyState = CONNECTING;
  url: string;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  send = vi.fn();
  close = vi.fn(() => {
    this.readyState = CLOSED;
    setTimeout(() => {
      this.onclose?.(new CloseEvent("close", { code: 1000, wasClean: true }));
    }, 0);
  });

  simulateOpen() {
    this.readyState = OPEN;
    this.onopen?.(new Event("open"));
  }

  simulateMessage(data: object) {
    this.onmessage?.(
      new MessageEvent("message", { data: JSON.stringify(data) })
    );
  }

  simulateClose(code = 1000, wasClean = true) {
    this.readyState = CLOSED;
    this.onclose?.(new CloseEvent("close", { code, wasClean }));
  }

  simulateError() {
    this.onerror?.(new Event("error"));
  }
}

describe("useJobProgress", () => {
  let mockInstances: MockWebSocket[] = [];

  beforeEach(() => {
    mockInstances = [];
    MockWebSocket.instances = [];
    
    // Use a function that behaves like a constructor
    const wsMock = function(this: unknown, url: string) {
      const instance = new MockWebSocket(url);
      mockInstances.push(instance);
      return instance;
    } as unknown as typeof WebSocket;

    // Match static properties
    const wsMockAsUnknown = wsMock as unknown as Record<string, number>;
    wsMockAsUnknown.CONNECTING = CONNECTING;
    wsMockAsUnknown.OPEN = OPEN;
    wsMockAsUnknown.CLOSING = CLOSING;
    wsMockAsUnknown.CLOSED = CLOSED;

    (global as unknown as { WebSocket: unknown }).WebSocket = vi.fn(wsMock as unknown as () => unknown);
    
    // Also set static properties on the vi.fn() result
    const globalWs = (global as unknown as { WebSocket: Record<string, number> }).WebSocket;
    globalWs.CONNECTING = CONNECTING;
    globalWs.OPEN = OPEN;
    globalWs.CLOSING = CLOSING;
    globalWs.CLOSED = CLOSED;
    
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  const getLatestMock = () => mockInstances[mockInstances.length - 1];

  describe("initialization", () => {
    it("returns null progress initially", () => {
      const { result } = renderHook(() => useJobProgress("job-123"));
      expect(result.current.progress).toBeNull();
      expect(result.current.status).toBe("pending");
      expect(result.current.isConnected).toBe(false);
    });

    it("returns default state when jobId is null", () => {
      const { result } = renderHook(() => useJobProgress(null));
      expect(result.current.progress).toBeNull();
      expect(result.current.status).toBe("pending");
      expect(result.current.isConnected).toBe(false);
    });

    it("does not create WebSocket when jobId is null", () => {
      renderHook(() => useJobProgress(null));
      expect(MockWebSocket.instances.length).toBe(0);
    });
  });

  describe("connection", () => {
    it("creates WebSocket connection when jobId is provided", async () => {
      renderHook(() => useJobProgress("job-123"));

      const mockWs = getLatestMock();
      expect(mockWs).toBeDefined();
      expect(mockWs!.url).toContain("/v1/ws/jobs/job-123");
    });

    it("sets isConnected to true when WebSocket opens", async () => {
      const { result } = renderHook(() => useJobProgress("job-123"));

      const mockWs = getLatestMock();
      
      act(() => {
        mockWs!.simulateOpen();
      });

      expect(result.current.isConnected).toBe(true);
    });
  });

  describe("progress updates", () => {
    it("updates progress on WebSocket message", () => {
      const { result } = renderHook(() => useJobProgress("job-123"));

      const mockWs = getLatestMock();
      expect(mockWs).toBeDefined();
      
      act(() => {
        mockWs!.simulateOpen();
      });

      act(() => {
        mockWs!.simulateMessage({
          job_id: "job-123",
          current_frame: 50,
          total_frames: 100,
          percent: 50,
        });
      });

      expect(result.current.progress).toEqual({
        job_id: "job-123",
        current_frame: 50,
        total_frames: 100,
        percent: 50,
      });
      expect(result.current.status).toBe("running");
    });

    it("includes optional tool fields in progress", () => {
      const { result } = renderHook(() => useJobProgress("job-123"));

      const mockWs = getLatestMock();
      
      act(() => {
        mockWs!.simulateOpen();
      });

      act(() => {
        mockWs!.simulateMessage({
          job_id: "job-123",
          current_frame: 50,
          total_frames: 100,
          percent: 50,
          current_tool: "yolo-tracker",
          tools_total: 2,
          tools_completed: 1,
        });
      });

      expect(result.current.progress?.current_tool).toBe("yolo-tracker");
      expect(result.current.progress?.tools_total).toBe(2);
      expect(result.current.progress?.tools_completed).toBe(1);
    });
  });

  describe("status transitions", () => {
    it("sets status to completed on completion event", () => {
      const { result } = renderHook(() => useJobProgress("job-123"));

      const mockWs = getLatestMock();
      
      act(() => {
        mockWs!.simulateOpen();
      });

      act(() => {
        mockWs!.simulateMessage({ status: "completed", job_id: "job-123" });
      });

      expect(result.current.status).toBe("completed");
    });

    it("sets status to failed on error event", () => {
      const { result } = renderHook(() => useJobProgress("job-123"));

      const mockWs = getLatestMock();
      
      act(() => {
        mockWs!.simulateOpen();
      });

      act(() => {
        mockWs!.simulateMessage({
          status: "error",
          job_id: "job-123",
          message: "Processing failed",
        });
      });

      expect(result.current.status).toBe("failed");
      expect(result.current.error).toBe("Processing failed");
    });
  });

  describe("job isolation", () => {
    it("ignores messages for other jobs", async () => {
      const { result } = renderHook(() => useJobProgress("job-A"));

      const mockWs = getLatestMock();
      
      act(() => {
        mockWs!.simulateOpen();
      });

      act(() => {
        mockWs!.simulateMessage({
          job_id: "job-B", // Different job
          current_frame: 50,
          total_frames: 100,
          percent: 50,
        });
      });

      // Progress should remain null (message ignored)
      expect(result.current.progress).toBeNull();
    });
  });

  describe("ping/pong", () => {
    it("handles pong messages without state change", async () => {
      const { result } = renderHook(() => useJobProgress("job-123"));

      const mockWs = getLatestMock();
      
      act(() => {
        mockWs!.simulateOpen();
      });
      
      const prevProgress = result.current.progress;

      act(() => {
        mockWs!.simulateMessage({ type: "pong" });
      });

      // State should be unchanged
      expect(result.current.progress).toBe(prevProgress);
    });
  });

  describe("cleanup", () => {
    it("closes WebSocket on unmount", async () => {
      const { unmount } = renderHook(() => useJobProgress("job-123"));

      const mockWs = getLatestMock();
      expect(mockWs).toBeDefined();

      unmount();

      expect(mockWs!.close).toHaveBeenCalled();
    });

    it("resets state when jobId changes", () => {
      const { result, rerender } = renderHook(
        ({ jobId }) => useJobProgress(jobId),
        { initialProps: { jobId: "job-A" } }
      );

      const mockWs1 = getLatestMock();
      
      act(() => {
        mockWs1!.simulateOpen();
      });
      
      // Simulate progress for job-A
      act(() => {
        mockWs1!.simulateMessage({
          job_id: "job-A",
          current_frame: 50,
          total_frames: 100,
          percent: 50,
        });
      });

      expect(result.current.progress?.percent).toBe(50);

      // Change jobId
      rerender({ jobId: "job-B" });

      // Should reset progress
      expect(result.current.progress).toBeNull();
      expect(result.current.status).toBe("pending");
    });
  });

  describe("reconnection", () => {
    it("attempts reconnection on unexpected close", () => {
      const { result } = renderHook(() => useJobProgress("job-123"));

      const mockWs = getLatestMock();
      
      act(() => {
        mockWs!.simulateOpen();
      });
      
      expect(result.current.isConnected).toBe(true);

      // Simulate unexpected close
      act(() => {
        mockWs!.simulateClose(1006, false);
      });

      expect(result.current.isConnected).toBe(false);

      // Advance timers for reconnection delay
      act(() => {
        vi.advanceTimersByTime(3000);
      });

      // Should have created a new WebSocket
      expect(mockInstances.length).toBe(2);
    });
  });

  describe("completion handling", () => {
    it("should NOT show error when WebSocket closes after completed status", () => {
      const { result } = renderHook(() => useJobProgress("job-123"));

      const mockWs = getLatestMock();
      
      act(() => {
        mockWs!.simulateOpen();
      });

      // Simulate completion message
      act(() => {
        mockWs!.simulateMessage({ status: "completed", job_id: "job-123" });
      });

      expect(result.current.status).toBe("completed");

      // Simulate WebSocket close after completion
      act(() => {
        mockWs!.simulateClose(1000, true);
      });

      // Should NOT show error - this is the bug we're fixing
      expect(result.current.error).toBeNull();
    });

    it("should NOT show error when WebSocket errors after completed status", () => {
      const { result } = renderHook(() => useJobProgress("job-123"));

      const mockWs = getLatestMock();
      
      act(() => {
        mockWs!.simulateOpen();
      });

      // Simulate completion message
      act(() => {
        mockWs!.simulateMessage({ status: "completed", job_id: "job-123" });
      });

      expect(result.current.status).toBe("completed");

      // Simulate WebSocket error after completion
      act(() => {
        mockWs!.simulateError();
      });

      // Should NOT show error - job already completed
      expect(result.current.error).toBeNull();
    });

    it("should show disconnected error when WebSocket closes during running", () => {
      const { result } = renderHook(() => useJobProgress("job-123"));

      const mockWs = getLatestMock();
      
      act(() => {
        mockWs!.simulateOpen();
      });

      // Simulate running state
      act(() => {
        mockWs!.simulateMessage({
          job_id: "job-123",
          current_frame: 50,
          total_frames: 100,
          percent: 50,
        });
      });

      expect(result.current.status).toBe("running");

      // Simulate unexpected close during running
      act(() => {
        mockWs!.simulateClose(1006, false);
      });

      // Should show disconnected error - job was NOT completed
      expect(result.current.error).toBe("WebSocket disconnected");
    });
  });
});
