/**
 * Tests for useWebSocket hook
 *
 * Uses mock factories to generate test data matching actual API responses.
 * API Reference: WebSocket /v1/stream (fixtures/api-responses.json)
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useWebSocket } from "./useWebSocket";
import { createMockFrameResult } from "../test-utils/factories";

// Mock WebSocket constants if not available in environment
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

    readyState = CONNECTING;
    onopen: ((event: Event) => void) | null = null;
    onmessage: ((event: MessageEvent) => void) | null = null;
    onerror: ((event: Event) => void) | null = null;
    onclose: ((event: CloseEvent) => void) | null = null;

    url: string;

    constructor(url: string) {
        this.url = url;
        // Automatically move to OPEN if we want simple tests, 
        // but hook expects to wait for onopen.
    }

    send = vi.fn();
    close = vi.fn((code?: number) => {
        this.readyState = CLOSED;
        setTimeout(() => {
            this.onclose?.(
                new CloseEvent("close", { code: code || 1000, wasClean: true })
            );
        }, 0);
    });

    simulateOpen() {
        this.readyState = OPEN;
        this.onopen?.(new Event("open"));
    }

    simulateMessage(data: unknown) {
        this.onmessage?.(new MessageEvent("message", { data: JSON.stringify(data) }));
    }

    simulateError() {
        this.onerror?.(new Event("error"));
    }

    simulateClose(code = 1000, wasClean = true) {
        this.readyState = CLOSED;
        this.onclose?.(new CloseEvent("close", { code, wasClean }));
    }
}

describe("useWebSocket", () => {
    let mockInstances: MockWebSocket[] = [];

    beforeEach(() => {
        mockInstances = [];
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
        // Also need to set the static properties on the vi.fn() result
        const globalWs = (global as unknown as { WebSocket: Record<string, number> }).WebSocket;
        globalWs.CONNECTING = CONNECTING;
        globalWs.OPEN = OPEN;
        globalWs.CLOSING = CLOSING;
        globalWs.CLOSED = CLOSED;
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    const getLatestMock = () => mockInstances[mockInstances.length - 1];

    describe("connection", () => {
        it("should initialize in disconnected state", () => {
            const { result } = renderHook(() =>
                useWebSocket({ url: "ws://localhost:8000/v1/stream" })
            );

            expect(result.current.isConnected).toBe(false);
            expect(result.current.isConnecting).toBe(true);
        });

        it("should connect to WebSocket URL", async () => {
            renderHook(() =>
                useWebSocket({ url: "ws://localhost:8000/v1/stream" })
            );

            const mockWs = getLatestMock();
            act(() => {
                mockWs.simulateOpen();
            });

            await waitFor(() => {
                expect(global.WebSocket).toHaveBeenCalledWith(
                    expect.stringContaining("ws://")
                );
            });
        });

        it("should include plugin in connection URL", async () => {
            renderHook(() =>
                useWebSocket({
                    url: "ws://localhost:8000/v1/stream",
                    plugin: "motion_detector",
                })
            );

            await waitFor(() => {
                expect(global.WebSocket).toHaveBeenCalledWith(
                    expect.stringContaining("motion_detector")
                );
            });
        });

        it("should include API key in connection URL when provided", async () => {
            renderHook(() =>
                useWebSocket({
                    url: "ws://localhost:8000/v1/stream",
                    apiKey: "secret-key",
                })
            );

            await waitFor(() => {
                expect(global.WebSocket).toHaveBeenCalledWith(
                    expect.stringContaining("api_key=secret-key")
                );
            });
        });

        it("should update state when connected", async () => {
            const { result } = renderHook(() =>
                useWebSocket({ url: "ws://localhost:8000/v1/stream" })
            );

            const mockWs = getLatestMock();
            act(() => {
                mockWs.simulateOpen();
            });

            await waitFor(() => {
                expect(result.current.isConnected).toBe(true);
                expect(result.current.isConnecting).toBe(false);
            });
        });
    });

    describe("frame sending", () => {
        it("should send frame when connected", async () => {
            const { result } = renderHook(() =>
                useWebSocket({ url: "ws://localhost:8000/v1/stream" })
            );

            const mockWs = getLatestMock();
            act(() => {
                mockWs.simulateOpen();
            });

            await waitFor(() => {
                expect(result.current.isConnected).toBe(true);
            });

            act(() => {
                result.current.sendFrame("base64imagedata");
            });

            expect(mockWs.send).toHaveBeenCalledWith(
                expect.stringContaining("frame")
            );
        });

        it("should not send frame when disconnected", () => {
            const { result } = renderHook(() =>
                useWebSocket({ url: "ws://localhost:8000/v1/stream" })
            );

            const mockWs = getLatestMock();
            act(() => {
                result.current.sendFrame("base64imagedata");
            });

            expect(mockWs.send).not.toHaveBeenCalled();
        });
    });

    describe("plugin switching", () => {
        it("should switch plugin when connected", async () => {
            const { result } = renderHook(() =>
                useWebSocket({ url: "ws://localhost:8000/v1/stream" })
            );

            const mockWs = getLatestMock();
            act(() => {
                mockWs.simulateOpen();
            });

            await waitFor(() => {
                expect(result.current.isConnected).toBe(true);
            });

            act(() => {
                result.current.switchPlugin("object_detection");
            });

            expect(mockWs.send).toHaveBeenCalledWith(
                expect.stringContaining("switch_plugin")
            );
        });

        it("should not switch plugin when disconnected", () => {
            const { result } = renderHook(() =>
                useWebSocket({ url: "ws://localhost:8000/v1/stream" })
            );

            const mockWs = getLatestMock();
            act(() => {
                result.current.switchPlugin("object_detection");
            });

            expect(mockWs.send).not.toHaveBeenCalled();
        });
    });

    describe("message handling", () => {
        it("should handle result messages", async () => {
            const onResult = vi.fn();
            const { result } = renderHook(() =>
                useWebSocket({
                    url: "ws://localhost:8000/v1/stream",
                    onResult,
                })
            );

            const mockWs = getLatestMock();
            act(() => {
                mockWs.simulateOpen();
            });

            // Uses factory-generated test data matching WebSocket API
            const frameResult = createMockFrameResult();

            act(() => {
                mockWs.simulateMessage({
                    type: "result",
                    payload: frameResult,
                });
            });

            await waitFor(() => {
                expect(result.current.latestResult).toEqual(frameResult);
                expect(onResult).toHaveBeenCalledWith(frameResult);
            });
        });

        it("should handle error messages", async () => {
            const onError = vi.fn();
            const { result } = renderHook(() =>
                useWebSocket({
                    url: "ws://localhost:8000/v1/stream",
                    onError,
                })
            );

            const mockWs = getLatestMock();
            act(() => {
                mockWs.simulateOpen();
            });

            act(() => {
                mockWs.simulateMessage({
                    type: "error",
                    payload: { error: "Processing failed" },
                });
            });

            await waitFor(() => {
                expect(result.current.error).toContain("Processing failed");
                expect(onError).toHaveBeenCalledWith(expect.stringContaining("Processing failed"));
            });
        });

        it("should handle connection messages", async () => {
            const onConnect = vi.fn();
            renderHook(() =>
                useWebSocket({
                    url: "ws://localhost:8000/v1/stream",
                    onConnect,
                })
            );

            const mockWs = getLatestMock();
            act(() => {
                mockWs.simulateOpen();
            });

            act(() => {
                mockWs.simulateMessage({
                    type: "connected",
                    payload: {
                        client_id: "client-123",
                        plugin_metadata: { version: "1.0.0" },
                    },
                });
            });

            await waitFor(() => {
                expect(onConnect).toHaveBeenCalledWith(
                    "client-123",
                    expect.objectContaining({ version: "1.0.0" })
                );
            });
        });
    });

    describe("stats tracking", () => {
        it("should track frame processing stats", async () => {
            const { result } = renderHook(() =>
                useWebSocket({ url: "ws://localhost:8000/v1/stream" })
            );

            const mockWs = getLatestMock();
            act(() => {
                mockWs.simulateOpen();
            });

            act(() => {
                mockWs.simulateMessage({
                    type: "result",
                    payload: {
                        frame_id: "f1",
                        plugin: "motion_detector",
                        result: {},
                        processing_time_ms: 50,
                    },
                });
            });

            await waitFor(() => {
                expect(result.current.stats.framesProcessed).toBeGreaterThan(0);
                expect(result.current.stats.avgProcessingTime).toBeGreaterThan(0);
            });
        });
    });

    describe("disconnection", () => {
        it("should handle clean disconnect", async () => {
            const { result } = renderHook(() =>
                useWebSocket({ url: "ws://localhost:8000/v1/stream" })
            );

            const mockWs = getLatestMock();
            act(() => {
                mockWs.simulateOpen();
            });

            act(() => {
                result.current.disconnect();
            });

            expect(mockWs.close).toHaveBeenCalled();
        });

        it("should update state on disconnect", async () => {
            const { result } = renderHook(() =>
                useWebSocket({ url: "ws://localhost:8000/v1/stream" })
            );

            const mockWs = getLatestMock();
            act(() => {
                mockWs.simulateOpen();
            });

            await waitFor(() => {
                expect(result.current.isConnected).toBe(true);
            });

            act(() => {
                mockWs.simulateClose(1000, true);
            });

            await waitFor(() => {
                expect(result.current.isConnected).toBe(false);
            });
        });
    });

    describe("reconnection", () => {
        it("should attempt reconnection on unexpected close", async () => {
            vi.useFakeTimers();
            const { result } = renderHook(() =>
                useWebSocket({
                    url: "ws://localhost:8000/v1/stream",
                    reconnectBaseDelayMs: 100,
                    maxReconnectAttempts: 3,
                })
            );

            const mockWs = getLatestMock();
            act(() => {
                mockWs.simulateOpen();
            });

            act(() => {
                mockWs.simulateClose(1006, false);
            });

            // Status should update to disconnected
            expect(result.current.isConnected).toBe(false);

            // Advance timers to trigger reconnect
            act(() => {
                vi.advanceTimersByTime(150);
            });

            // Reconnection scheduled - check that reconnection is in progress
            expect(result.current.isConnecting).toBe(true);

            vi.useRealTimers();
        });

        it("should reconnect on explicit reconnect call", async () => {
            const { result } = renderHook(() =>
                useWebSocket({ url: "ws://localhost:8000/v1/stream" })
            );

            const mockWs = getLatestMock();
            act(() => {
                mockWs.simulateOpen();
            });

            act(() => {
                result.current.reconnect();
            });

            expect(mockWs.close).toHaveBeenCalled();
            // Should have created a new instance
            expect(global.WebSocket).toHaveBeenCalledTimes(2);
        });
    });

    describe("error state management", () => {
        it("should clear error state when transitioning from error to successful connection", () => {
            const { result } = renderHook(() =>
                useWebSocket({ url: "ws://localhost:8000/v1/stream" })
            );

            const mockWs = getLatestMock();

            // Simulate an error first
            act(() => {
                mockWs.simulateError();
            });

            // Then simulate a successful connection
            act(() => {
                mockWs.simulateOpen();
            });

            // After successful connection, error should be cleared
            expect(result.current.isConnected).toBe(true);
            expect(result.current.error).toBeNull();
        });
    });
});