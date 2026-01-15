/**
 * WebSocket hook for real-time frame streaming
 *
 * Uses environment variables:
 * - VITE_WS_URL: WebSocket endpoint URL (default: ws://localhost:8000/v1/stream)
 * - VITE_API_KEY: Optional API authentication key
 */

import { useCallback, useEffect, useRef, useState } from "react";

const WS_URL =
    import.meta.env.VITE_WS_URL || "ws://localhost:8000/v1/stream";
const WS_API_KEY = import.meta.env.VITE_API_KEY;

export interface WebSocketMessage {
    type: "connected" | "result" | "error" | "plugin_switched" | "pong";
    payload: Record<string, unknown>;
    timestamp?: string;
}

export interface FrameResult {
    frame_id: string;
    plugin: string;
    result: Record<string, unknown>;
    processing_time_ms: number;
}

export interface UseWebSocketOptions {
    url: string;
    plugin?: string;
    apiKey?: string;
    onResult?: (result: FrameResult) => void;
    onError?: (error: string) => void;
    onConnect?: (
        clientId: string,
        pluginMetadata: Record<string, unknown>
    ) => void;
    reconnectInterval?: number;
    maxReconnectAttempts?: number;
}

export interface UseWebSocketReturn {
    isConnected: boolean;
    isConnecting: boolean;
    error: string | null;
    sendFrame: (
        imageData: string,
        frameId?: string,
        options?: Record<string, unknown>
    ) => void;
    switchPlugin: (pluginName: string) => void;
    disconnect: () => void;
    reconnect: () => void;
    latestResult: FrameResult | null;
    stats: {
        framesProcessed: number;
        avgProcessingTime: number;
    };
}

export function useWebSocket(
    options: UseWebSocketOptions
): UseWebSocketReturn {
    const {
        url = WS_URL,
        plugin = "motion_detector",
        apiKey = WS_API_KEY,
        onResult,
        onError,
        onConnect,
        reconnectInterval = 3000,
        maxReconnectAttempts = 5,
    } = options;

    const wsRef = useRef<WebSocket | null>(null);
    const reconnectAttemptsRef = useRef(0);
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [latestResult, setLatestResult] = useState<FrameResult | null>(null);
    const [stats, setStats] = useState({
        framesProcessed: 0,
        avgProcessingTime: 0,
    });

    const processingTimesRef = useRef<number[]>([]);

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            return;
        }

        setIsConnecting(true);
        setError(null);

        let wsUrl = url.startsWith("ws")
            ? url
            : `ws://${window.location.host}${url}`;
        wsUrl += `?plugin=${encodeURIComponent(plugin)}`;
        if (apiKey) {
            wsUrl += `&api_key=${encodeURIComponent(apiKey)}`;
        }

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            setIsConnected(true);
            setIsConnecting(false);
            setError(null); // Clear any previous error when successfully connected
            reconnectAttemptsRef.current = 0;
            console.log(
                `[WebSocket] Connected to ${url} (plugin: ${plugin})`
            );
        };

        ws.onmessage = (event) => {
            try {
                const message: WebSocketMessage = JSON.parse(
                    event.data as string
                );

                switch (message.type) {
                    case "connected":
                        onConnect?.(
                            message.payload.client_id as string,
                            message.payload
                                .plugin_metadata as Record<string, unknown>
                        );
                        break;

                    case "result": {
                        const result = message.payload as unknown as FrameResult;
                        setLatestResult(result);

                        processingTimesRef.current.push(
                            result.processing_time_ms
                        );
                        if (processingTimesRef.current.length > 100) {
                            processingTimesRef.current.shift();
                        }
                        const avg =
                            processingTimesRef.current.reduce(
                                (a, b) => a + b,
                                0
                            ) / processingTimesRef.current.length;
                        setStats((prev) => ({
                            framesProcessed: prev.framesProcessed + 1,
                            avgProcessingTime: avg,
                        }));

                        onResult?.(result);
                        break;
                    }

                    case "error": {
                        const errorMsg = message.payload.error as string;
                        setError(errorMsg);
                        onError?.(errorMsg);
                        break;
                    }

                    case "plugin_switched":
                        console.log(
                            `[WebSocket] Plugin switched to: ${
                                message.payload.plugin as string
                            }`
                        );
                        break;

                    case "pong":
                        break;
                }
            } catch (e) {
                console.error("Failed to parse WebSocket message:", e);
            }
        };

        ws.onerror = (event) => {
            const errorMsg = `WebSocket connection error. Unable to connect to ${wsUrl}. Check if backend server is running on port 8000.`;
            console.error(`[WebSocket] Error connecting to ${wsUrl}:`, event);
            setError(errorMsg);
        };

        ws.onclose = (event) => {
            setIsConnected(false);
            setIsConnecting(false);
            wsRef.current = null;

            const wasClean = (event as CloseEvent).wasClean;
            const code = (event as CloseEvent).code;

            if (
                !wasClean &&
                reconnectAttemptsRef.current < maxReconnectAttempts
            ) {
                reconnectAttemptsRef.current++;
                console.warn(
                    `[WebSocket] Closed unexpectedly (code: ${code}). Reconnecting (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`
                );
                reconnectTimeoutRef.current = setTimeout(
                    connect,
                    reconnectInterval
                );
            } else if (
                reconnectAttemptsRef.current >= maxReconnectAttempts
            ) {
                const maxAttemptMsg = `Max reconnection attempts reached (${maxReconnectAttempts}). Unable to connect to ${url}. Ensure backend server is running on port 8000.`;
                console.error(`[WebSocket] ${maxAttemptMsg}`);
                setError(maxAttemptMsg);
            } else if (wasClean) {
                console.log(
                    `[WebSocket] Closed cleanly (code: ${code})`
                );
            }
        };
    }, [url, plugin, apiKey, onResult, onError, onConnect, reconnectInterval, maxReconnectAttempts]);

    const sendFrame = useCallback(
        (
            imageData: string,
            frameId?: string,
            options?: Record<string, unknown>
        ) => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send(
                    JSON.stringify({
                        type: "frame",
                        frame_id: frameId || crypto.randomUUID?.(),
                        image_data: imageData,
                        ...options,
                    })
                );
            }
        },
        []
    );

    const switchPlugin = useCallback((pluginName: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(
                JSON.stringify({
                    type: "switch_plugin",
                    plugin: pluginName,
                })
            );
        }
    }, []);

    const disconnect = useCallback(() => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
    }, []);

    const reconnect = useCallback(() => {
        disconnect();
        reconnectAttemptsRef.current = 0;
        connect();
    }, [connect, disconnect]);

    useEffect(() => {
        connect();
        return () => {
            disconnect();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // Empty dependency array - connect on mount only, not on function changes

    return {
        isConnected,
        isConnecting,
        error,
        sendFrame,
        switchPlugin,
        disconnect,
        reconnect,
        latestResult,
        stats,
    };
}
