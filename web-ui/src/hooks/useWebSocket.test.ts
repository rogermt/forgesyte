/**
 * Tests for useWebSocket hook
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useWebSocket, FrameResult } from "./useWebSocket";

// Mock WebSocket
class MockWebSocket {
    readyState = WebSocket.CONNECTING;
    onopen: ((event: Event) => void) | null = null;
    onmessage: ((event: MessageEvent) => void) | null = null;
    onerror: ((event: Event) => void) | null = null;
    onclose: ((event: CloseEvent) => void) | null = null;

    send = vi.fn();
    close = vi.fn((code?: number) => {
        this.readyState = 3; // WebSocket.CLOSED
        this.onclose?.(
            new CloseEvent("close", { code: code || 1000, wasClean: true })
        );
    });

    simulateOpen() {
        this.readyState = 1; // WebSocket.OPEN
        this.onopen?.(new Event("open"));
    }

    simulateMessage(data: unknown) {
        this.onmessage?.(new MessageEvent("message", { data: JSON.stringify(data) }));
    }

    simulateError() {
        this.onerror?.(new Event("error"));
    }

    simulateClose(code = 1000, wasClean = true) {
        this.readyState = 3; // WebSocket.CLOSED
        this.onclose?.(new CloseEvent("close", { code, wasClean }));
    }
}

describe("useWebSocket", () => {
    let mockWs: MockWebSocket;

    beforeEach(() => {
        mockWs = new MockWebSocket();
        (global as any).WebSocket = vi.fn(() => mockWs) as any;
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

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

            act(() => {
                mockWs.simulateOpen();
            });

            await waitFor(() => {
                expect((global as any).WebSocket).toHaveBeenCalledWith(
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
                expect((global as any).WebSocket).toHaveBeenCalledWith(
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
                expect((global as any).WebSocket).toHaveBeenCalledWith(
                    expect.stringContaining("api_key=secret-key")
                );
            });
        });

        it("should update state when connected", async () => {
            const { result } = renderHook(() =>
                useWebSocket({ url: "ws://localhost:8000/v1/stream" })
            );

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

            act(() => {
                mockWs.simulateOpen();
            });

            const frameResult: FrameResult = {
                frame_id: "frame-001",
                plugin: "motion_detector",
                result: { motion: true },
                processing_time_ms: 45,
            };

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
                expect(result.current.error).toBe("Processing failed");
                expect(onError).toHaveBeenCalledWith("Processing failed");
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
            const { result } = renderHook(() =>
                useWebSocket({
                    url: "ws://localhost:8000/v1/stream",
                    reconnectInterval: 100,
                    maxReconnectAttempts: 3,
                })
            );

            act(() => {
                mockWs.simulateOpen();
            });

            act(() => {
                mockWs.simulateClose(1006, false);
            });

            await waitFor(() => {
                expect(result.current.isConnecting).toBe(true);
            }, { timeout: 500 });
        });

        it("should reconnect on explicit reconnect call", async () => {
            const { result } = renderHook(() =>
                useWebSocket({ url: "ws://localhost:8000/v1/stream" })
            );

            act(() => {
                mockWs.simulateOpen();
            });

            act(() => {
                result.current.reconnect();
            });

            expect(mockWs.close).toHaveBeenCalled();
        });
    });
});
