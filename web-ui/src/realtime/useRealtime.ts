/**
 * Phase 17 useRealtime Hook
 *
 * Convenience hook for accessing realtime state and methods
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { RealtimeClient, ConnectionState } from './RealtimeClient';
import { FPSThrottler } from '../utils/FPSThrottler';
import type { StreamingResultPayload, StreamingErrorPayload, StreamingMessage } from './types';

/**
 * Phase 17: Real-Time Streaming Hook
 *
 * High-level hook that orchestrates WebSocket, FPS throttling, and streaming state.
 * Uses RealtimeClient directly for Phase 17 binary streaming.
 */

export interface UseRealtimeStreamingOptions {
  pipelineId?: string;
  apiKey?: string;
  debug?: boolean;
}

export interface UseRealtimeStreamingReturn {
  connect: (pipelineId: string) => void;
  disconnect: () => void;
  sendFrame: (bytes: Uint8Array | ArrayBuffer) => void;
  clearError: () => void;
  currentPipelineId: string | null;
  wsUrl: string;
  state: {
    isConnected: boolean;
    isConnecting: boolean;
    connectionStatus: 'idle' | 'connecting' | 'connected' | 'disconnected' | 'closed';
    lastResult: StreamingResultPayload | null;
    droppedFrames: number;
    slowDownWarnings: number;
    lastError: StreamingErrorPayload | null;
    // FE-7 metrics
    framesSent: number;
    startTime: number | null;
    lastFrameSizes: number[];
    lastLatencies: number[];
    currentFps: number;
  };
}

export function useRealtimeStreaming(options: UseRealtimeStreamingOptions = {}): UseRealtimeStreamingReturn {
  const { pipelineId: initialPipelineId, apiKey, debug = false } = options;

  const [pipelineId, setPipelineId] = useState<string | null>(initialPipelineId || null);
  const [lastError, setLastError] = useState<StreamingErrorPayload | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>(ConnectionState.IDLE);
  const [lastResult, setLastResult] = useState<StreamingResultPayload | null>(null);
  const [droppedFrames, setDroppedFrames] = useState(0);
  const [slowDownWarnings, setSlowDownWarnings] = useState(0);

  // FE-7 metrics state
  const [framesSent, setFramesSent] = useState(0);
  const [startTime, setStartTime] = useState<number | null>(null);
  const [lastFrameSizes, setLastFrameSizes] = useState<number[]>([]);
  const [lastLatencies, setLastLatencies] = useState<number[]>([]);
  const [currentFps, setCurrentFps] = useState(15);

  // FE-7 refs for latency tracking
  const sendTimestamps = useRef(new Map<number, number>());
  const nextFrameIndexRef = useRef(0);

  // RealtimeClient ref
  const clientRef = useRef<RealtimeClient | null>(null);

  // Create FPS throttler (initial 15 FPS)
  const throttlerRef = useRef<FPSThrottler | null>(null);

  if (!throttlerRef.current) {
    throttlerRef.current = new FPSThrottler(15);
  }

  // Build WebSocket URL with pipeline_id
  const wsUrl = pipelineId
    ? `ws://localhost:8000/ws/video/stream?pipeline_id=${pipelineId}${apiKey ? `&api_key=${apiKey}` : ''}`
    : '';

  // Connect to WebSocket
  const connect = useCallback(async (newPipelineId: string) => {
    setPipelineId(newPipelineId);
    setConnectionState(ConnectionState.CONNECTING);
    // FE-7: Set start time when connecting
    setStartTime(performance.now());
    setDroppedFrames(0);
    setSlowDownWarnings(0);
    setLastResult(null);
    setLastError(null);

    const url = `ws://localhost:8000/ws/video/stream?pipeline_id=${newPipelineId}${apiKey ? `&api_key=${apiKey}` : ''}`;

    try {
      const client = new RealtimeClient(url);
      clientRef.current = client;

      // Register message handler
      client.on('*', (message: unknown) => {
        const msg = message as StreamingMessage;
        if ('warning' in msg && msg.warning === 'slow_down') {
          setSlowDownWarnings((prev) => prev + 1);
        } else if ('error' in msg) {
          setLastError({ error: msg.error, detail: msg.detail });
        } else if ('frame_index' in msg) {
          if ('dropped' in msg && msg.dropped) {
            setDroppedFrames((prev) => prev + 1);
          } else {
            setLastResult(msg as StreamingResultPayload);
          }
        }
      });

      // Listen to connection state changes
      client.on('connected', () => {
        setConnectionState(ConnectionState.CONNECTED);
      });

      client.on('disconnected', () => {
        setConnectionState(ConnectionState.DISCONNECTED);
      });

      await client.connect();
    } catch (error) {
      setConnectionState(ConnectionState.CLOSED);
      if (debug) {
        console.error('[useRealtime] Connection failed:', error);
      }
    }
  }, [apiKey, debug]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.disconnect();
      clientRef.current = null;
    }
    setPipelineId(null);
    setConnectionState(ConnectionState.DISCONNECTED);
    // FE-7: Clear metrics when disconnecting
    setStartTime(null);
    setFramesSent(0);
    setLastFrameSizes([]);
    setLastLatencies([]);
    setCurrentFps(15);
    sendTimestamps.current.clear();
    nextFrameIndexRef.current = 0;
    setDroppedFrames(0);
    setSlowDownWarnings(0);
    setLastResult(null);
    setLastError(null);
  }, []);

  const clearError = useCallback(() => {
    setLastError(null);
  }, []);

  const sendFrame = useCallback((bytes: Uint8Array | ArrayBuffer) => {
    if (!throttlerRef.current || !clientRef.current) return;

    // Use throttler to control FPS
    throttlerRef.current.throttle(() => {
      // FE-7: Track frame size
      const byteLength = bytes instanceof ArrayBuffer ? bytes.byteLength : bytes.byteLength;
      setLastFrameSizes((prev) => {
        const next = [...prev, byteLength];
        return next.length > 5 ? next.slice(next.length - 5) : next;
      });

      // FE-7: Track frame count and timestamp for latency
      setFramesSent((n) => n + 1);
      const frameIndex = nextFrameIndexRef.current++;
      sendTimestamps.current.set(frameIndex, performance.now());

      clientRef.current!.sendFrame(bytes);
    });
  }, []);

  // Reduce FPS when slow_down warnings received
  useEffect(() => {
    if (slowDownWarnings > 0 && throttlerRef.current) {
      throttlerRef.current = new FPSThrottler(5);
      setCurrentFps(5);
    }
  }, [slowDownWarnings]);

  // FE-7: Compute latency from streaming results
  useEffect(() => {
    if (lastResult && lastResult.frame_index !== undefined) {
      const frameIndex = lastResult.frame_index;
      const start = sendTimestamps.current.get(frameIndex);
      if (start) {
        // Prune the map to prevent unbounded growth
        sendTimestamps.current.delete(frameIndex);

        const latency = performance.now() - start;
        setLastLatencies((prev) => {
          const next = [...prev, latency];
          return next.length > 5 ? next.slice(next.length - 5) : next;
        });
      }
    }
  }, [lastResult]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (clientRef.current) {
        clientRef.current.disconnect();
      }
    };
  }, []);

  const state = {
    isConnected: connectionState === ConnectionState.CONNECTED,
    isConnecting: connectionState === ConnectionState.CONNECTING,
    connectionStatus: connectionState.toLowerCase() as 'idle' | 'connecting' | 'connected' | 'disconnected' | 'closed',
    lastResult,
    droppedFrames,
    slowDownWarnings,
    lastError,
    // FE-7 metrics
    framesSent,
    startTime,
    lastFrameSizes,
    lastLatencies,
    currentFps,
  };

  return {
    connect,
    disconnect,
    sendFrame,
    clearError,
    currentPipelineId: pipelineId,
    wsUrl,
    state,
  };
}

/**
 * Canonical Phase 17 realtime hook export.
 * Replaces the old Phase 10 plugin-based realtime system.
 */
export function useRealtime(
  options?: UseRealtimeStreamingOptions
): UseRealtimeStreamingReturn {
  return useRealtimeStreaming(options);
}
