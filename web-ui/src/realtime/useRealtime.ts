/**
 * Phase 17 useRealtime Hook
 *
 * Convenience hook for accessing realtime state and methods
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { FPSThrottler } from '../utils/FPSThrottler';
import type { StreamingResultPayload, StreamingErrorPayload } from './types';

/**
 * Phase 17: Real-Time Streaming Hook
 *
 * High-level hook that orchestrates WebSocket, FPS throttling, and streaming state.
 * Wraps useWebSocket and provides Phase 17 streaming functionality.
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
    connectionStatus: 'idle' | 'connecting' | 'connected' | 'disconnected' | 'failed';
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

  // FE-7 metrics state
  const [framesSent, setFramesSent] = useState(0);
  const [startTime, setStartTime] = useState<number | null>(null);
  const [lastFrameSizes, setLastFrameSizes] = useState<number[]>([]);
  const [lastLatencies, setLastLatencies] = useState<number[]>([]);
  const [currentFps, setCurrentFps] = useState(15);

  // FE-7 refs for latency tracking
  const sendTimestamps = useRef(new Map<number, number>());
  const nextFrameIndexRef = useRef(0);

  // Create FPS throttler (initial 15 FPS)
  const throttlerRef = useRef<FPSThrottler | null>(null);

  if (!throttlerRef.current) {
    throttlerRef.current = new FPSThrottler(15);
  }

  // Build WebSocket URL with pipeline_id
  const wsUrl = pipelineId
    ? `ws://localhost:8000/ws/video/stream?pipeline_id=${pipelineId}${apiKey ? `&api_key=${apiKey}` : ''}`
    : '';

  // Wrap useWebSocket
  const ws = useWebSocket({
    url: wsUrl,
    plugin: pipelineId || '',
    apiKey,
    debug,
  });

  const connect = useCallback((newPipelineId: string) => {
    setPipelineId(newPipelineId);
    // FE-7: Set start time when connecting
    setStartTime(performance.now());
  }, []);

  const disconnect = useCallback(() => {
    setPipelineId(null);
    // FE-7: Clear metrics when disconnecting
    setStartTime(null);
    setFramesSent(0);
    setLastFrameSizes([]);
    setLastLatencies([]);
    setCurrentFps(15);
    sendTimestamps.current.clear();
    nextFrameIndexRef.current = 0;
  }, []);

  const clearError = useCallback(() => {
    setLastError(null);
  }, []);

  const sendFrame = useCallback((bytes: Uint8Array | ArrayBuffer) => {
    if (!throttlerRef.current) return;

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

      ws.sendBinaryFrame(bytes);
    });
  }, [ws]);

  // Reduce FPS when slow_down warnings received
  useEffect(() => {
    if (ws.slowDownWarnings > 0 && throttlerRef.current) {
      throttlerRef.current = new FPSThrottler(5);
      setCurrentFps(5);
    }
  }, [ws.slowDownWarnings]);

  // FE-7: Compute latency from streaming results
  useEffect(() => {
    if (ws.lastResult && ws.lastResult.frame_index !== undefined) {
      const frameIndex = ws.lastResult.frame_index;
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
  }, [ws.lastResult]);

  // Update lastError from WebSocket state
  useEffect(() => {
    setLastError(ws.lastError);
  }, [ws.lastError]);

  const state = {
    isConnected: ws.isConnected,
    isConnecting: ws.isConnecting,
    connectionStatus: ws.connectionStatus as 'idle' | 'connecting' | 'connected' | 'disconnected' | 'failed',
    lastResult: ws.lastResult,
    droppedFrames: ws.droppedFrames,
    slowDownWarnings: ws.slowDownWarnings,
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
