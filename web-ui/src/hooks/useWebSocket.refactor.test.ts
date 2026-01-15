/**
 * Tests for useWebSocket Hook
 *
 * Organized by User Stories from the refactoring specification.
 * Each test validates specific acceptance criteria.
 *
 * [BP-15] AAA Test Pattern (Arrange, Act, Assert)
 * [BP-16] Async Testing with waitFor
 *
 * @see https://kentcdodds.com/blog/common-mistakes-with-react-testing-library
 * @see https://testing-library.com/docs/react-testing-library/api
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useWebSocket, ConnectionStatus } from "./useWebSocket";
import { createMockFrameResult } from "../test-utils/factories";

// ============================================================================
// MOCK SETUP
// ============================================================================

const WS_STATES = {
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3,
} as const;

class MockWebSocket {
  static CONNECTING = WS_STATES.CONNECTING;
  static OPEN = WS_STATES.OPEN;
  static CLOSING = WS_STATES.CLOSING;
  static CLOSED = WS_STATES.CLOSED;

  readyState = WS_STATES.CONNECTING;
  url: string;

  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;

  send = vi.fn();
  close = vi.fn();

  constructor(url: string) {
    this.url = url;
  }

  simulateOpen() {
    this.readyState = WS_STATES.OPEN;
    this.onopen?.(new Event("open"));
  }

  simulateMessage(data: unknown) {
    this.onmessage?.(
      new MessageEvent("message", { data: JSON.stringify(data) })
    );
  }

  simulateError() {
    this.onerror?.(new Event("error"));
  }

  simulateClose(code = 1000, wasClean = true) {
    this.readyState = WS_STATES.CLOSED;
    this.onclose?.(new CloseEvent("close", { code, wasClean }));
  }
}

// ============================================================================
// TEST SUITE
// ============================================================================

describe("useWebSocket", () => {
  let mockInstances: MockWebSocket[] = [];
  const defaultUrl = "ws://localhost:8000/v1/stream";

  beforeEach(() => {
    mockInstances = [];
    vi.useFakeTimers();

    // Create a proper constructor that can be called with `new`
    const MockWebSocketConstructor = function(url: string) {
      const instance = new MockWebSocket(url);
      mockInstances.push(instance);
      return instance;
    } as unknown as typeof WebSocket;

    Object.assign(MockWebSocketConstructor, WS_STATES);
    (global as { WebSocket: typeof WebSocket }).WebSocket =
      MockWebSocketConstructor;
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  const getLatestMock = () => mockInstances[mockInstances.length - 1];

  // ==========================================================================
  // EPIC 1: STATE MANAGEMENT MODERNIZATION
  // ==========================================================================

  describe("Epic 1: State Management Modernization", () => {
    describe("Story 1.1: Unified Connection State", () => {
      it("should provide accurate connection status - 'connecting' on init", () => {
        // Arrange & Act
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );

        // Assert
        expect(result.current.connectionState).toBe("connecting");
        expect(result.current.isConnected).toBe(false);
        expect(result.current.isConnecting).toBe(true);
      });

      it("should provide accurate connection status - 'connected' after open", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        // Act
        act(() => {
          mockWs.simulateOpen();
        });

        // Assert
        await waitFor(() => {
          expect(result.current.connectionState).toBe("connected");
          expect(result.current.isConnected).toBe(true);
          expect(result.current.isConnecting).toBe(false);
        });
      });

      it("should have no conflicting status indicators", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        // Assert - connecting state
        expect(result.current.isConnected).toBe(false);
        expect(result.current.isConnecting).toBe(true);

        // Act - connect
        act(() => {
          mockWs.simulateOpen();
        });

        // Assert - connected state
        await waitFor(() => {
          expect(result.current.isConnected).toBe(true);
          expect(result.current.isConnecting).toBe(false);
        });

        // Act - disconnect
        act(() => {
          mockWs.simulateClose(1000, true);
        });

        // Assert - disconnected state
        await waitFor(() => {
          expect(result.current.isConnected).toBe(false);
          expect(result.current.isConnecting).toBe(false);
          expect(result.current.connectionState).toBe("disconnected");
        });
      });

      it("should clearly distinguish between connection states", () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );

        // Assert
        const validStates: ConnectionStatus[] = [
          "idle",
          "connecting",
          "connected",
          "reconnecting",
          "failed",
          "disconnected",
        ];

        expect(validStates).toContain(result.current.connectionState);
      });
    });

    describe("Story 1.2: Predictable State Transitions", () => {
      it("should transition logically: connecting -> connected", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        // Assert initial
        expect(result.current.connectionState).toBe("connecting");

        // Act
        act(() => {
          mockWs.simulateOpen();
        });

        // Assert
        await waitFor(() => {
          expect(result.current.connectionState).toBe("connected");
        });
      });

      it("should transition: connected -> disconnected on clean close", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        await waitFor(() => {
          expect(result.current.connectionState).toBe("connected");
        });

        // Act
        act(() => {
          mockWs.simulateClose(1000, true);
        });

        // Assert
        await waitFor(() => {
          expect(result.current.connectionState).toBe("disconnected");
        });
      });

      it("should transition: connected -> reconnecting on unclean close", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl, reconnectInterval: 100 })
        );
        const mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        await waitFor(() => {
          expect(result.current.connectionState).toBe("connected");
        });

        // Act
        act(() => {
          mockWs.simulateClose(1006, false);
        });

        // Assert
        await waitFor(() => {
          expect(result.current.connectionState).toBe("reconnecting");
        });
      });
    });
  });

  // ==========================================================================
  // EPIC 2: ERROR HANDLING ENHANCEMENT
  // ==========================================================================

  describe("Epic 2: Error Handling Enhancement", () => {
    describe("Story 2.1: Suppress Initial Connection Errors", () => {
      it("should NOT display error during initial connection grace period", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        // Act - Error immediately (within grace period)
        act(() => {
          mockWs.simulateError();
        });

        // Assert - Error NOT displayed but state is accurate
        expect(result.current.error).toBeNull();
        expect(result.current.connectionState).toBe("failed");
      });

      it("should display error after grace period (3000ms) has elapsed", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        // Act - Advance past grace period
        act(() => {
          vi.advanceTimersByTime(3500);
        });

        act(() => {
          mockWs.simulateError();
        });

        // Assert - Error IS displayed
        await waitFor(() => {
          expect(result.current.error).not.toBeNull();
        });
      });

      it("should display error immediately if previously connected", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        let mockWs = getLatestMock();

        // Connect first
        act(() => {
          mockWs.simulateOpen();
        });

        await waitFor(() => {
          expect(result.current.isConnected).toBe(true);
        });

        // Close and get new mock
        act(() => {
          mockWs.simulateClose(1006, false);
        });

        act(() => {
          vi.advanceTimersByTime(1500);
        });

        mockWs = getLatestMock();

        // Act - Error on reconnection attempt
        act(() => {
          mockWs.simulateError();
        });

        // Assert - Error IS displayed
        await waitFor(() => {
          expect(result.current.error).not.toBeNull();
        });
      });

      it("should maintain accurate visual indicators during initial connection", () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        // Act
        act(() => {
          mockWs.simulateError();
        });

        // Assert
        expect(result.current.error).toBeNull();
        expect(result.current.connectionState).toBe("failed");
        expect(result.current.isConnected).toBe(false);
      });
    });

    describe("Story 2.2: Meaningful Error Messages", () => {
      it("should provide error type information", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        act(() => {
          vi.advanceTimersByTime(3500);
        });

        // Act
        act(() => {
          mockWs.simulateError();
        });

        // Assert
        await waitFor(() => {
          expect(result.current.errorDetails).not.toBeNull();
          expect(result.current.errorDetails?.type).toBe("CONNECTION_FAILED");
        });
      });

      it("should provide different error types for different scenarios", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        await waitFor(() => {
          expect(result.current.isConnected).toBe(true);
        });

        // Act - Server error
        act(() => {
          mockWs.simulateMessage({
            type: "error",
            payload: { error: "Server processing failed" },
          });
        });

        // Assert
        await waitFor(() => {
          expect(result.current.errorDetails?.type).toBe("SERVER_ERROR");
        });
      });

      it("should provide actionable guidance in error details", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        act(() => {
          vi.advanceTimersByTime(3500);
        });

        // Act
        act(() => {
          mockWs.simulateError();
        });

        // Assert
        await waitFor(() => {
          expect(result.current.errorDetails?.guidance).toBeTruthy();
          expect(result.current.errorDetails?.guidance).toContain("backend server");
        });
      });

      it("should show MAX_RETRIES_EXCEEDED when reconnection exhausted", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({
            url: defaultUrl,
            reconnectInterval: 100,
            maxReconnectAttempts: 2,
          })
        );
        let mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        // Exhaust retries
        for (let i = 0; i < 3; i++) {
          mockWs = getLatestMock();
          act(() => {
            mockWs.simulateClose(1006, false);
          });
          act(() => {
            vi.advanceTimersByTime(5000);
          });
        }

        // Assert
        await waitFor(() => {
          expect(result.current.errorDetails?.type).toBe("MAX_RETRIES_EXCEEDED");
          expect(result.current.errorDetails?.guidance).toContain("refresh");
        });
      });
    });

    describe("Story 2.3: Clear Errors on Successful Connection", () => {
      it("should clear error when connection is re-established", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        act(() => {
          vi.advanceTimersByTime(3500);
          mockWs.simulateError();
        });

        await waitFor(() => {
          expect(result.current.error).not.toBeNull();
        });

        // Act
        act(() => {
          mockWs.simulateOpen();
        });

        // Assert
        await waitFor(() => {
          expect(result.current.error).toBeNull();
          expect(result.current.errorDetails).toBeNull();
          expect(result.current.isConnected).toBe(true);
        });
      });

      it("should update UI immediately on error clear", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        act(() => {
          vi.advanceTimersByTime(3500);
          mockWs.simulateError();
        });

        expect(result.current.error).not.toBeNull();

        // Act
        act(() => {
          mockWs.simulateOpen();
        });

        // Assert - Immediate update
        expect(result.current.error).toBeNull();
      });
    });
  });

  // ==========================================================================
  // EPIC 3: CONNECTION LOGIC IMPROVEMENT
  // ==========================================================================

  describe("Epic 3: Connection Logic Improvement", () => {
    describe("Story 3.1: Reliable Connection Establishment", () => {
      it("should accurately reflect actual connection state", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        // Assert - Not connected before open
        expect(result.current.isConnected).toBe(false);
        expect(mockWs.readyState).toBe(WS_STATES.CONNECTING);

        // Act
        act(() => {
          mockWs.simulateOpen();
        });

        // Assert - Connected after open
        expect(result.current.isConnected).toBe(true);
      });

      it("should NOT report 'connected' during connection attempts", () => {
        // Arrange & Act
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );

        // Assert
        expect(result.current.isConnecting).toBe(true);
        expect(result.current.isConnected).toBe(false);
        expect(result.current.connectionState).toBe("connecting");
      });

      it("should handle connection timing correctly", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        expect(result.current.stats.lastConnectedAt).toBeNull();

        // Act
        const beforeConnect = Date.now();
        act(() => {
          mockWs.simulateOpen();
        });

        // Assert
        await waitFor(() => {
          expect(result.current.stats.lastConnectedAt).not.toBeNull();
          expect(
            result.current.stats.lastConnectedAt!.getTime()
          ).toBeGreaterThanOrEqual(beforeConnect);
        });
      });
    });

    describe("Story 3.2: Robust Reconnection", () => {
      it("should automatically attempt reconnection after connection loss", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({
            url: defaultUrl,
            reconnectInterval: 100,
            maxReconnectAttempts: 3,
          })
        );
        const mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        const initialCount = mockInstances.length;

        // Act - Unclean close
        act(() => {
          mockWs.simulateClose(1006, false);
        });

        act(() => {
          vi.advanceTimersByTime(200);
        });

        // Assert
        expect(mockInstances.length).toBeGreaterThan(initialCount);
        expect(result.current.stats.currentReconnectAttempt).toBeGreaterThan(0);
      });

      it("should respect maximum retry attempts", async () => {
        // Arrange
        const maxAttempts = 2;
        const { result } = renderHook(() =>
          useWebSocket({
            url: defaultUrl,
            reconnectInterval: 100,
            maxReconnectAttempts: maxAttempts,
          })
        );
        let mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        // Exhaust all retries
        for (let i = 0; i <= maxAttempts; i++) {
          mockWs = getLatestMock();
          act(() => {
            mockWs.simulateClose(1006, false);
          });
          act(() => {
            vi.advanceTimersByTime(10000);
          });
        }

        // Assert
        await waitFor(() => {
          expect(result.current.connectionState).toBe("failed");
          expect(result.current.error).toContain("attempts");
        });
      });

      it("should use exponential backoff for reconnection", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({
            url: defaultUrl,
            reconnectInterval: 1000,
            maxReconnectAttempts: 3,
          })
        );
        let mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        // First disconnect
        act(() => {
          mockWs.simulateClose(1006, false);
        });

        const countAfterFirstClose = mockInstances.length;

        // Advance 500ms - should NOT have reconnected yet
        act(() => {
          vi.advanceTimersByTime(500);
        });

        expect(mockInstances.length).toBe(countAfterFirstClose);

        // Advance another 1000ms - should have reconnected
        act(() => {
          vi.advanceTimersByTime(1000);
        });

        expect(mockInstances.length).toBeGreaterThan(countAfterFirstClose);
      });

      it("should reset reconnection counter on manual reconnect", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({
            url: defaultUrl,
            reconnectInterval: 100,
            maxReconnectAttempts: 3,
          })
        );
        let mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        act(() => {
          mockWs.simulateClose(1006, false);
        });

        act(() => {
          vi.advanceTimersByTime(200);
        });

        expect(result.current.stats.currentReconnectAttempt).toBeGreaterThan(0);

        // Act
        act(() => {
          result.current.reconnect();
        });

        act(() => {
          vi.advanceTimersByTime(10);
        });

        // Assert
        expect(result.current.stats.currentReconnectAttempt).toBe(0);
      });
    });
  });

  // ==========================================================================
  // EPIC 4: USER EXPERIENCE ENHANCEMENT
  // ==========================================================================

  describe("Epic 4: User Experience Enhancement", () => {
    describe("Story 4.1: Smooth Connection Transitions", () => {
      it("should not lose latest result during reconnection", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        const frameResult = createMockFrameResult();
        act(() => {
          mockWs.simulateMessage({
            type: "result",
            payload: frameResult,
          });
        });

        expect(result.current.latestResult).toEqual(frameResult);

        // Act - Disconnect
        act(() => {
          mockWs.simulateClose(1006, false);
        });

        // Assert - Result still available
        expect(result.current.latestResult).toEqual(frameResult);
      });

      it("should maintain stats during connection transitions", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        act(() => {
          mockWs.simulateMessage({
            type: "result",
            payload: { ...createMockFrameResult(), processing_time_ms: 100 },
          });
        });

        act(() => {
          mockWs.simulateMessage({
            type: "result",
            payload: { ...createMockFrameResult(), processing_time_ms: 200 },
          });
        });

        const statsBefore = { ...result.current.stats };

        // Act - Disconnect
        act(() => {
          mockWs.simulateClose(1006, false);
        });

        // Assert - Stats preserved
        expect(result.current.stats.framesProcessed).toBe(statsBefore.framesProcessed);
        expect(result.current.stats.avgProcessingTime).toBeCloseTo(
          statsBefore.avgProcessingTime,
          1
        );
      });
    });

    describe("Story 4.2: Transparent Connection Management", () => {
      it("should handle reconnection in background without user intervention", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({
            url: defaultUrl,
            reconnectInterval: 100,
            maxReconnectAttempts: 3,
          })
        );
        let mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        // Act - Connection lost
        act(() => {
          mockWs.simulateClose(1006, false);
        });

        expect(result.current.connectionState).toBe("reconnecting");

        act(() => {
          vi.advanceTimersByTime(200);
        });

        mockWs = getLatestMock();
        act(() => {
          mockWs.simulateOpen();
        });

        // Assert - Reconnected without user action
        await waitFor(() => {
          expect(result.current.isConnected).toBe(true);
          expect(result.current.error).toBeNull();
        });
      });

      it("should provide clear indicators when user attention needed", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({
            url: defaultUrl,
            reconnectInterval: 100,
            maxReconnectAttempts: 1,
          })
        );
        let mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        // Exhaust retries
        for (let i = 0; i < 3; i++) {
          mockWs = getLatestMock();
          act(() => {
            mockWs.simulateClose(1006, false);
          });
          act(() => {
            vi.advanceTimersByTime(1000);
          });
        }

        // Assert
        await waitFor(() => {
          expect(result.current.error).not.toBeNull();
          expect(result.current.errorDetails?.guidance).toContain("refresh");
          expect(result.current.connectionState).toBe("failed");
        });
      });

      it("should allow manual reconnect as escape hatch", async () => {
        // Arrange
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        let mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        act(() => {
          result.current.disconnect();
        });

        expect(result.current.connectionState).toBe("disconnected");

        // Act
        act(() => {
          result.current.reconnect();
        });

        act(() => {
          vi.advanceTimersByTime(10);
        });

        mockWs = getLatestMock();
        act(() => {
          mockWs.simulateOpen();
        });

        // Assert
        await waitFor(() => {
          expect(result.current.isConnected).toBe(true);
        });
      });

      it("should cleanup properly on unmount", () => {
        // Arrange
        const { result, unmount } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        // Act
        unmount();

        // Assert
        expect(mockWs.close).toHaveBeenCalled();
      });
    });
  });

  // ==========================================================================
  // CORE FUNCTIONALITY TESTS
  // ==========================================================================

  describe("Core Functionality", () => {
    describe("Frame Sending", () => {
      it("should send frame when connected", async () => {
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        act(() => {
          result.current.sendFrame("base64data", "frame-123");
        });

        expect(mockWs.send).toHaveBeenCalledWith(
          expect.stringContaining('"type":"frame"')
        );
        expect(mockWs.send).toHaveBeenCalledWith(
          expect.stringContaining('"frame_id":"frame-123"')
        );
      });

      it("should not send frame when disconnected", () => {
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        act(() => {
          result.current.sendFrame("base64data");
        });

        expect(mockWs.send).not.toHaveBeenCalled();
      });
    });

    describe("Plugin Switching", () => {
      it("should send switch_plugin message", async () => {
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl })
        );
        const mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        act(() => {
          result.current.switchPlugin("object_detection");
        });

        expect(mockWs.send).toHaveBeenCalledWith(
          expect.stringContaining('"type":"switch_plugin"')
        );
        expect(mockWs.send).toHaveBeenCalledWith(
          expect.stringContaining('"plugin":"object_detection"')
        );
      });
    });

    describe("Callbacks", () => {
      it("should call onResult callback", async () => {
        const onResult = vi.fn();
        const { result } = renderHook(() =>
          useWebSocket({ url: defaultUrl, onResult })
        );
        const mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        const frameResult = createMockFrameResult();

        act(() => {
          mockWs.simulateMessage({
            type: "result",
            payload: frameResult,
          });
        });

        expect(onResult).toHaveBeenCalledWith(frameResult);
      });

      it("should call onError callback", async () => {
        const onError = vi.fn();
        renderHook(() => useWebSocket({ url: defaultUrl, onError }));
        const mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        act(() => {
          mockWs.simulateMessage({
            type: "error",
            payload: { error: "Server error" },
          });
        });

        expect(onError).toHaveBeenCalledWith("Server error");
      });

      it("should call onConnect callback", async () => {
        const onConnect = vi.fn();
        renderHook(() => useWebSocket({ url: defaultUrl, onConnect }));
        const mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        act(() => {
          mockWs.simulateMessage({
            type: "connected",
            payload: {
              client_id: "client-abc",
              plugin_metadata: { version: "2.0" },
            },
          });
        });

        expect(onConnect).toHaveBeenCalledWith("client-abc", { version: "2.0" });
      });
    });

    describe("URL Construction", () => {
      it("should include plugin in URL", () => {
        renderHook(() =>
          useWebSocket({ url: defaultUrl, plugin: "custom_plugin" })
        );

        expect(global.WebSocket).toHaveBeenCalledWith(
          expect.stringContaining("plugin=custom_plugin")
        );
      });

      it("should include API key in URL when provided", () => {
        renderHook(() =>
          useWebSocket({ url: defaultUrl, apiKey: "secret123" })
        );

        expect(global.WebSocket).toHaveBeenCalledWith(
          expect.stringContaining("api_key=secret123")
        );
      });
    });

    describe("Stats Tracking", () => {
      it("should calculate running average for processing time", async () => {
        const { result } = renderHook(() => useWebSocket({ url: defaultUrl }));
        const mockWs = getLatestMock();

        act(() => {
          mockWs.simulateOpen();
        });

        act(() => {
          mockWs.simulateMessage({
            type: "result",
            payload: { ...createMockFrameResult(), processing_time_ms: 100 },
          });
        });

        act(() => {
          mockWs.simulateMessage({
            type: "result",
            payload: { ...createMockFrameResult(), processing_time_ms: 200 },
          });
        });

        await waitFor(() => {
          expect(result.current.stats.avgProcessingTime).toBeCloseTo(150, 0);
        });
      });

      it("should track connection attempts", async () => {
        const { result } = renderHook(() => useWebSocket({ url: defaultUrl }));

        await waitFor(() => {
          expect(result.current.stats.connectionAttempts).toBe(1);
        });
      });
    });
  });
});
