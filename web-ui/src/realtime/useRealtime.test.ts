/**
 * Phase 17: useRealtime Hook Tests
 *
 * Tests for streaming functionality added to useRealtimeStreaming hook
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import type { StreamingResultPayload, StreamingErrorPayload } from "./types";
import { useRealtimeStreaming } from "./useRealtime";

// Mock useWebSocket
vi.mock("../hooks/useWebSocket", () => ({
  __esModule: true,
  default: vi.fn(),
}));

import useWebSocket from "../hooks/useWebSocket";

describe("useRealtime (Phase 17 Streaming)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("WebSocket connection with pipeline_id", () => {
    it("calls useWebSocket with correct URL containing pipeline_id", () => {
      vi.mocked(useWebSocket).mockReturnValue({
        isConnected: false,
        isConnecting: false,
        error: null,
        connectionStatus: "idle",
        attempt: 0,
        errorInfo: null,
        sendFrame: vi.fn(),
        sendBinaryFrame: vi.fn(),
        switchPlugin: vi.fn(),
        disconnect: vi.fn(),
        reconnect: vi.fn(),
        latestResult: null,
        lastResult: null,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastError: null,
        stats: { framesProcessed: 0, avgProcessingTime: 0 },
      });

      const { result } = renderHook(() => useRealtimeStreaming());

      act(() => {
        result.current.connect("yolo_ocr");
      });

      expect(vi.mocked(useWebSocket)).toHaveBeenCalledWith(
        expect.objectContaining({
          url: expect.stringContaining("ws://"),
          plugin: "yolo_ocr",
        })
      );
    });

    it("disconnects and reconnects with new pipeline_id", () => {
      vi.mocked(useWebSocket).mockReturnValue({
        isConnected: true,
        isConnecting: false,
        error: null,
        connectionStatus: "connected",
        attempt: 0,
        errorInfo: null,
        sendFrame: vi.fn(),
        sendBinaryFrame: vi.fn(),
        switchPlugin: vi.fn(),
        disconnect: vi.fn(),
        reconnect: vi.fn(),
        latestResult: null,
        lastResult: null,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastError: null,
        stats: { framesProcessed: 0, avgProcessingTime: 0 },
      });

      const { result } = renderHook(() => useRealtimeStreaming());

      act(() => {
        result.current.connect("yolo_ocr");
      });

      act(() => {
        result.current.connect("motion_detector");
      });

      expect(vi.mocked(useWebSocket)).toHaveBeenCalledTimes(3);
    });
  });

  describe("sendFrame() delegates to useWebSocket", () => {
    it("sends binary data via sendBinaryFrame", () => {
      const mockSendBinaryFrame = vi.fn();
      vi.mocked(useWebSocket).mockReturnValue({
        isConnected: true,
        isConnecting: false,
        error: null,
        connectionStatus: "connected",
        attempt: 0,
        errorInfo: null,
        sendFrame: vi.fn(),
        sendBinaryFrame: mockSendBinaryFrame,
        switchPlugin: vi.fn(),
        disconnect: vi.fn(),
        reconnect: vi.fn(),
        latestResult: null,
        lastResult: null,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastError: null,
        stats: { framesProcessed: 0, avgProcessingTime: 0 },
      });

      const { result } = renderHook(() => useRealtimeStreaming());

      const binaryData = new Uint8Array([0xFF, 0xD8, 0xFF, 0xE0]);

      act(() => {
        result.current.sendFrame(binaryData);
      });

      expect(mockSendBinaryFrame).toHaveBeenCalledWith(binaryData);
    });
  });

  describe("state updates on messages", () => {
    it("updates lastResult on streaming result messages", () => {
      const mockResult: StreamingResultPayload = {
        frame_index: 42,
        result: { detections: [{ x: 0.1, y:0.2, w: 0.3, h:0.4, label: "person", score: 0.92 }] },
      };

      vi.mocked(useWebSocket).mockReturnValue({
        isConnected: true,
        isConnecting: false,
        error: null,
        connectionStatus: "connected",
        attempt: 0,
        errorInfo: null,
        sendFrame: vi.fn(),
        sendBinaryFrame: vi.fn(),
        switchPlugin: vi.fn(),
        disconnect: vi.fn(),
        reconnect: vi.fn(),
        latestResult: null,
        lastResult: mockResult,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastError: null,
        stats: { framesProcessed: 0, avgProcessingTime: 0 },
      });

      const { result } = renderHook(() => useRealtimeStreaming());

      expect(result.current.state.lastResult).toEqual(mockResult);
    });

    it("increments droppedFrames on dropped frame messages", () => {
      vi.mocked(useWebSocket).mockReturnValue({
        isConnected: true,
        isConnecting: false,
        error: null,
        connectionStatus: "connected",
        attempt: 0,
        errorInfo: null,
        sendFrame: vi.fn(),
        sendBinaryFrame: vi.fn(),
        switchPlugin: vi.fn(),
        disconnect: vi.fn(),
        reconnect: vi.fn(),
        latestResult: null,
        lastResult: null,
        droppedFrames: 5,
        slowDownWarnings: 0,
        lastError: null,
        stats: { framesProcessed: 10, avgProcessingTime: 50 },
      });

      const { result } = renderHook(() => useRealtimeStreaming());

      expect(result.current.state.droppedFrames).toBe(5);
    });

    it("increments slowDownWarnings on slow_down messages", () => {
      vi.mocked(useWebSocket).mockReturnValue({
        isConnected: true,
        isConnecting: false,
        error: null,
        connectionStatus: "connected",
        attempt: 0,
        errorInfo: null,
        sendFrame: vi.fn(),
        sendBinaryFrame: vi.fn(),
        switchPlugin: vi.fn(),
        disconnect: vi.fn(),
        reconnect: vi.fn(),
        latestResult: null,
        lastResult: null,
        droppedFrames: 0,
        slowDownWarnings: 3,
        lastError: null,
        stats: { framesProcessed: 10, avgProcessingTime: 50 },
      });

      const { result } = renderHook(() => useRealtimeStreaming());

      expect(result.current.state.slowDownWarnings).toBe(3);
    });

    it("sets lastError on error messages", () => {
      const mockError: StreamingErrorPayload = {
        error: "invalid_frame",
        detail: "Not a valid JPEG image",
      };

      vi.mocked(useWebSocket).mockReturnValue({
        isConnected: true,
        isConnecting: false,
        error: null,
        connectionStatus: "connected",
        attempt: 0,
        errorInfo: null,
        sendFrame: vi.fn(),
        sendBinaryFrame: vi.fn(),
        switchPlugin: vi.fn(),
        disconnect: vi.fn(),
        reconnect: vi.fn(),
        latestResult: null,
        lastResult: null,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastError: mockError,
        stats: { framesProcessed: 10, avgProcessingTime: 50 },
      });

      const { result } = renderHook(() => useRealtimeStreaming());

      expect(result.current.state.lastError).toEqual(mockError);
    });
  });
});
