/**
 * WebSocket hook for real-time frame streaming
 *
 * Uses environment variables:
 * - VITE_WS_URL: WebSocket endpoint URL (default: ws://localhost:8000/v1/stream)
 * - VITE_API_KEY: Optional API authentication key
 *
 * ==========================
 * Best practices + citations
 * ==========================
 * [BP-1] Avoid redundant/duplicated state; derive booleans from a single source of truth.
 *   https://react.dev/learn/choosing-the-state-structure#avoid-redundant-state
 *
 * [BP-2] Manage complex/predictable state transitions with useReducer.
 *   https://react.dev/reference/react/useReducer
 *
 * [BP-3] Clean up effects (close sockets, clear timers) to avoid memory leaks.
 *   https://react.dev/reference/react/useEffect#cleaning-up-effects
 *
 * [BP-4] Store mutable values that shouldn't re-render (socket instance, timers) in useRef.
 *   https://react.dev/reference/react/useRef
 *
 * [BP-5] Avoid stale closures for callbacks (store callbacks in refs).
 *   React docs on reading latest values without re-running effects:
 *   https://react.dev/learn/removing-effect-dependencies#do-you-want-to-read-a-value-without-reacting-to-its-changes
 *
 * [BP-6] Prefer URL + URLSearchParams for safe querystring construction.
 *   https://developer.mozilla.org/en-US/docs/Web/API/URL
 *   https://developer.mozilla.org/en-US/docs/Web/API/URLSearchParams
 *
 * [BP-7] Use the documented WebSocket lifecycle and readyState guards.
 *   https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
 *
 * [BP-8] Exponential backoff + jitter for retries (robust reconnection).
 *   https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
 */

import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";

const DEFAULT_WS_URL =
  import.meta.env.VITE_WS_URL || "ws://localhost:8000/v1/stream";
const DEFAULT_WS_API_KEY = import.meta.env.VITE_API_KEY;

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

export type ConnectionStatus =
  | "idle"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "disconnected"
  | "failed";

export type ErrorKind =
  | "NETWORK"
  | "TIMEOUT"
  | "SERVER"
  | "PROTOCOL"
  | "MAX_RETRIES";

export interface ErrorInfo {
  kind: ErrorKind;
  message: string;
  at: Date;
  userVisible: boolean;
}

export interface UseWebSocketOptions {
  url?: string;
  plugin?: string;
  tools?: string[];
  apiKey?: string;

  onResult?: (result: FrameResult) => void;
  onError?: (error: string) => void;
  onConnect?: (clientId: string, pluginMetadata: Record<string, unknown>) => void;

  reconnectBaseDelayMs?: number;
  maxReconnectDelayMs?: number;
  maxReconnectAttempts?: number;
  backoffMultiplier?: number;
  jitterRatio?: number;

  connectionTimeoutMs?: number;

  reconnectErrorDisplayDelayMs?: number;

  debug?: boolean;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;

  connectionStatus: ConnectionStatus;
  attempt: number;
  errorInfo: ErrorInfo | null;

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

type State = {
  status: ConnectionStatus;
  attempt: number;
  errorInfo: ErrorInfo | null;
  latestResult: FrameResult | null;

  stats: {
    framesProcessed: number;
    avgProcessingTime: number;
  };

  hasEverConnected: boolean;
};

type Action =
  | { type: "CONNECT_START"; attempt: number; reconnecting: boolean }
  | { type: "CONNECTED" }
  | { type: "DISCONNECTED" }
  | { type: "FAILED"; errorInfo: ErrorInfo }
  | { type: "SET_ERROR"; errorInfo: ErrorInfo }
  | { type: "CLEAR_ERROR" }
  | { type: "RESULT"; result: FrameResult; avgProcessingTime: number }
  | { type: "MARK_EVER_CONNECTED" };

const initialState: State = {
  status: "idle",
  attempt: 0,
  errorInfo: null,
  latestResult: null,
  stats: { framesProcessed: 0, avgProcessingTime: 0 },
  hasEverConnected: false,
};

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "CONNECT_START":
      return {
        ...state,
        status: action.reconnecting ? "reconnecting" : "connecting",
        attempt: action.attempt,
      };

    case "MARK_EVER_CONNECTED":
      return { ...state, hasEverConnected: true };

    case "CONNECTED":
      return {
        ...state,
        status: "connected",
        attempt: 0,
        errorInfo: null,
      };

    case "DISCONNECTED":
      return { ...state, status: "disconnected" };

    case "FAILED":
      return { ...state, status: "failed", errorInfo: action.errorInfo };

    case "SET_ERROR":
      return { ...state, errorInfo: action.errorInfo };

    case "CLEAR_ERROR":
      return { ...state, errorInfo: null };

    case "RESULT":
      return {
        ...state,
        latestResult: action.result,
        stats: {
          framesProcessed: state.stats.framesProcessed + 1,
          avgProcessingTime: action.avgProcessingTime,
        },
      };

    default:
      return state;
  }
}

const PROCESSING_WINDOW_SIZE = 100;

function makeFrameId(): string {
  return (
    globalThis.crypto?.randomUUID?.() ??
    `frame_${Date.now()}_${Math.random().toString(16).slice(2)}`
  );
}

function normalizeWsUrl(raw: string): URL {
  if (raw.startsWith("ws://") || raw.startsWith("wss://")) return new URL(raw);

  const base = new URL(window.location.href);
  base.protocol = base.protocol === "https:" ? "wss:" : "ws:";
  return new URL(raw, base);
}

function buildWsUrl(baseUrl: string, plugin: string, apiKey?: string): string {
  const u = normalizeWsUrl(baseUrl);
  u.searchParams.set("plugin", plugin);
  if (apiKey) u.searchParams.set("api_key", apiKey);
  return u.toString();
}

function safeParseMessage(data: unknown): WebSocketMessage | null {
  if (typeof data !== "string") return null;
  try {
    const parsed = JSON.parse(data) as WebSocketMessage;
    if (!parsed || typeof parsed !== "object") return null;
    if (typeof parsed.type !== "string") return null;
    if (!("payload" in parsed)) return null;
    return parsed;
  } catch {
    return null;
  }
}

function computeBackoffDelayMs(params: {
  attempt: number;
  baseDelayMs: number;
  maxDelayMs: number;
  multiplier: number;
  jitterRatio: number;
}): number {
  const { attempt, baseDelayMs, maxDelayMs, multiplier, jitterRatio } = params;
  const exp = baseDelayMs * Math.pow(multiplier, Math.max(0, attempt - 1));
  const capped = Math.min(exp, maxDelayMs);
  const jitter = capped * jitterRatio * Math.random();
  return Math.round(Math.min(capped + jitter, maxDelayMs));
}

function networkErrorMessage(wsUrl: string): string {
  return [
    `WebSocket network error: unable to connect to ${wsUrl}.`,
    `What to check:`,
    `- Backend service is running and reachable`,
    `- VITE_WS_URL is correct for this environment`,
    `- Firewall/VPN/proxy/network settings`,
  ].join("\n");
}

function timeoutErrorMessage(ms: number): string {
  return `WebSocket connection timed out after ${ms}ms.`;
}

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const {
    url = DEFAULT_WS_URL,
    plugin = "",
    tools = [],
    apiKey = DEFAULT_WS_API_KEY,

    onResult,
    onError,
    onConnect,

    reconnectBaseDelayMs = 1000,
    maxReconnectDelayMs = 30_000,
    maxReconnectAttempts = 5,
    backoffMultiplier = 2,
    jitterRatio = 0.2,

    connectionTimeoutMs = 8000,
    reconnectErrorDisplayDelayMs = 800,

    debug = false,
  } = options;

  const [state, dispatch] = useReducer(reducer, initialState);

  const log = useCallback(
    (...args: unknown[]) => {
      if (debug) console.log(...args);
    },
    [debug]
  );

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const connectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectErrorTimerRef = useRef<ReturnType<typeof setTimeout> | null>(
    null
  );

  const manualCloseRef = useRef(false);
  const reconnectAttemptRef = useRef(0);

  const processingTimesRef = useRef<number[]>([]);
  const processingSumRef = useRef(0);

  const onResultRef = useRef(onResult);
  const onErrorRef = useRef(onError);
  const onConnectRef = useRef(onConnect);

  useEffect(() => {
    onResultRef.current = onResult;
    onErrorRef.current = onError;
    onConnectRef.current = onConnect;
  }, [onResult, onError, onConnect]);

  const cfg = useMemo(
    () => ({
      url,
      plugin,
      apiKey,
      reconnectBaseDelayMs,
      maxReconnectDelayMs,
      maxReconnectAttempts,
      backoffMultiplier,
      jitterRatio,
      connectionTimeoutMs,
      reconnectErrorDisplayDelayMs,
    }),
    [
      url,
      plugin,
      apiKey,
      reconnectBaseDelayMs,
      maxReconnectDelayMs,
      maxReconnectAttempts,
      backoffMultiplier,
      jitterRatio,
      connectionTimeoutMs,
      reconnectErrorDisplayDelayMs,
    ]
  );

  const clearTimers = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (connectTimeoutRef.current) {
      clearTimeout(connectTimeoutRef.current);
      connectTimeoutRef.current = null;
    }
    if (reconnectErrorTimerRef.current) {
      clearTimeout(reconnectErrorTimerRef.current);
      reconnectErrorTimerRef.current = null;
    }
  }, []);

  const scheduleReconnectErrorDisplay = useCallback(
    (wsUrlString: string) => {
      if (!state.hasEverConnected) return;

      if (reconnectErrorTimerRef.current) {
        clearTimeout(reconnectErrorTimerRef.current);
      }

      reconnectErrorTimerRef.current = setTimeout(() => {
        if (wsRef.current?.readyState !== WebSocket.OPEN) {
          dispatch({
            type: "SET_ERROR",
            errorInfo: {
              kind: "NETWORK",
              message: networkErrorMessage(wsUrlString),
              at: new Date(),
              userVisible: true,
            },
          });
        }
      }, cfg.reconnectErrorDisplayDelayMs);
    },
    [cfg.reconnectErrorDisplayDelayMs, state.hasEverConnected]
  );

  const connectRef = useRef<() => void>(() => {});

  const connect = useCallback(() => {
    // P0 fix: Don't connect if plugin is empty - stay idle (issue #95)
    if (!cfg.plugin?.trim()) {
      return;
    }

    if (
      wsRef.current &&
      (wsRef.current.readyState === WebSocket.OPEN ||
        wsRef.current.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    manualCloseRef.current = false;
    clearTimers();

    const attempt = reconnectAttemptRef.current + 1;
    const reconnecting = state.hasEverConnected && attempt > 1;

    dispatch({ type: "CONNECT_START", attempt, reconnecting });

    const wsUrlString = buildWsUrl(cfg.url, cfg.plugin, cfg.apiKey);
    log(`[WebSocket] Connecting: ${wsUrlString}`);

    const ws = new WebSocket(wsUrlString);
    wsRef.current = ws;

    connectTimeoutRef.current = setTimeout(() => {
      if (wsRef.current?.readyState === WebSocket.CONNECTING) {
        log(`[WebSocket] Connection timeout -> closing socket`);
        try {
          wsRef.current?.close();
        } catch {
          // ignore
        }

        dispatch({
          type: "SET_ERROR",
          errorInfo: {
            kind: "TIMEOUT",
            message: timeoutErrorMessage(cfg.connectionTimeoutMs),
            at: new Date(),
            userVisible: state.hasEverConnected,
          },
        });
      }
    }, cfg.connectionTimeoutMs);

    ws.onopen = () => {
      clearTimers();
      reconnectAttemptRef.current = 0;

      dispatch({ type: "MARK_EVER_CONNECTED" });
      dispatch({ type: "CONNECTED" });

      log(`[WebSocket] Connected`);
    };

    ws.onmessage = (event) => {
      const msg = safeParseMessage(event.data);
      if (!msg) {
        dispatch({
          type: "SET_ERROR",
          errorInfo: {
            kind: "PROTOCOL",
            message: "Received an invalid WebSocket message (parse/protocol error).",
            at: new Date(),
            userVisible: state.hasEverConnected,
          },
        });
        return;
      }

      switch (msg.type) {
        case "connected": {
          const payload = msg.payload ?? {};
          onConnectRef.current?.(
            payload.client_id as string,
            (payload.plugin_metadata ?? {}) as Record<string, unknown>
          );
          return;
        }

        case "result": {
          const result = msg.payload as unknown as FrameResult;

          // P1 fix: Validate processing_time_ms to prevent NaN stats
          const processingTime = result.processing_time_ms;
          if (typeof processingTime !== "number" || !Number.isFinite(processingTime)) {
            // Invalid processing time - still dispatch result but use 0 for stats
            dispatch({ type: "RESULT", result, avgProcessingTime: 0 });
            onResultRef.current?.(result);
            return;
          }

          processingTimesRef.current.push(processingTime);
          processingSumRef.current += processingTime;

          if (processingTimesRef.current.length > PROCESSING_WINDOW_SIZE) {
            const removed = processingTimesRef.current.shift()!;
            processingSumRef.current -= removed;
          }

          const avg =
            processingSumRef.current / processingTimesRef.current.length;

          dispatch({ type: "RESULT", result, avgProcessingTime: avg });
          onResultRef.current?.(result);
          return;
        }

        case "error": {
          const errorMsg =
            (msg.payload?.error as string) || "Unknown server error";

          const info: ErrorInfo = {
            kind: "SERVER",
            message: `Server error: ${errorMsg}`,
            at: new Date(),
            userVisible: true,
          };

          dispatch({ type: "SET_ERROR", errorInfo: info });
          onErrorRef.current?.(info.message);
          return;
        }

        case "plugin_switched":
          log(
            `[WebSocket] Plugin switched: ${
              (msg.payload.plugin as string) ?? "unknown"
            }`
          );
          return;

        case "pong":
          return;
      }
    };

    ws.onerror = () => {
      scheduleReconnectErrorDisplay(wsUrlString);
    };

    ws.onclose = (event) => {
      clearTimers();
      wsRef.current = null;

      dispatch({ type: "DISCONNECTED" });

      if (manualCloseRef.current) {
        log(`[WebSocket] Closed manually (code=${event.code})`);
        return;
      }

      const abnormal = !event.wasClean || event.code !== 1000;

      if (!abnormal) {
        log(`[WebSocket] Closed cleanly (code=${event.code})`);
        return;
      }

      if (reconnectAttemptRef.current < cfg.maxReconnectAttempts) {
        reconnectAttemptRef.current += 1;

        scheduleReconnectErrorDisplay(wsUrlString);

        const delay = computeBackoffDelayMs({
          attempt: reconnectAttemptRef.current,
          baseDelayMs: cfg.reconnectBaseDelayMs,
          maxDelayMs: cfg.maxReconnectDelayMs,
          multiplier: cfg.backoffMultiplier,
          jitterRatio: cfg.jitterRatio,
        });

        log(
          `[WebSocket] Abnormal close (code=${event.code}). Reconnecting in ${delay}ms (attempt ${reconnectAttemptRef.current}/${cfg.maxReconnectAttempts})`
        );

        reconnectTimerRef.current = setTimeout(() => {
          connectRef.current();
        }, delay);

        return;
      }

      const final: ErrorInfo = {
        kind: "MAX_RETRIES",
        message: [
          `Unable to establish a stable WebSocket connection (max retries: ${cfg.maxReconnectAttempts}).`,
          `URL: ${wsUrlString}`,
          `Actions: verify backend is running/reachable; verify VITE_WS_URL; check network.`,
        ].join("\n"),
        at: new Date(),
        userVisible: true,
      };

      dispatch({ type: "FAILED", errorInfo: final });
      onErrorRef.current?.(final.message);
    };
  }, [
    cfg,
    clearTimers,
    log,
    scheduleReconnectErrorDisplay,
    state.hasEverConnected,
  ]);

  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  // P0 fix: Trigger connection when plugin becomes available (issue #95)
  useEffect(() => {
    if (cfg.plugin?.trim()) {
      connectRef.current();
    }
  }, [cfg.plugin]);

  useEffect(() => {
    connectRef.current();

    return () => {
      manualCloseRef.current = true;
      clearTimers();
      try {
        wsRef.current?.close(1000);
      } catch {
        // ignore
      }
      wsRef.current = null;
    };
  }, [clearTimers]);

  const disconnect = useCallback(() => {
    manualCloseRef.current = true;
    clearTimers();

    try {
      wsRef.current?.close(1000);
    } catch {
      // ignore
    }
    wsRef.current = null;

    reconnectAttemptRef.current = 0;

    dispatch({ type: "CLEAR_ERROR" });
    dispatch({ type: "DISCONNECTED" });
  }, [clearTimers]);

  const reconnect = useCallback(() => {
    disconnect();
    manualCloseRef.current = false;
    reconnectAttemptRef.current = 0;
    connectRef.current();
  }, [disconnect]);

  const sendFrame = useCallback(
    (imageData: string, frameId?: string, extra?: Record<string, unknown>) => {
      if (wsRef.current?.readyState !== WebSocket.OPEN) return;

      wsRef.current.send(
        JSON.stringify({
          type: "frame",
          frame_id: frameId ?? makeFrameId(),
          image_data: imageData,
          plugin_id: plugin,
          tools: tools,
          ...(extra ?? {}),
        })
      );
    },
    [plugin, tools]
  );

  const switchPlugin = useCallback((pluginName: string) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return;

    wsRef.current.send(
      JSON.stringify({
        type: "switch_plugin",
        plugin: pluginName,
      })
    );
  }, []);

  const isConnected = state.status === "connected";
  const isConnecting =
    state.status === "connecting" || state.status === "reconnecting";

  const error =
    state.errorInfo && state.errorInfo.userVisible ? state.errorInfo.message : null;

  return {
    isConnected,
    isConnecting,
    error,
    connectionStatus: state.status,
    attempt: state.attempt,
    errorInfo: state.errorInfo,
    sendFrame,
    switchPlugin,
    disconnect,
    reconnect,
    latestResult: state.latestResult,
    stats: state.stats,
  };
}

export default useWebSocket;
