/**
 * Phase 10: Real-Time Hook.
 *
 * TODO: Implement the following:
 * - Hook for accessing real-time client
 * - Connection state helpers
 * - Message sending helpers
 *
 * Author: Roger
 * Phase: 10
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useRealtime } from './RealtimeContext';
import { RealtimeMessage } from './RealtimeClient';
import { useWebSocket } from '../hooks/useWebSocket';
import { FPSThrottler } from '../utils/FPSThrottler';
import type { StreamingResultPayload, StreamingErrorPayload } from './types';

export function useRealtimeConnection() {
  const { state, connect, disconnect } = useRealtime();

  return {
    isConnected: state.isConnected,
    connectionState: state.connectionState,
    connect: connect,
    disconnect: disconnect,
    progress: state.progress,
    pluginTimings: state.pluginTimings,
    warnings: state.warnings,
    errors: state.errors,
    currentPlugin: state.currentPlugin,
  };
}

export function useRealtimeMessages() {
  const { on, off, send } = useRealtime();

  const subscribe = useCallback(
    (type: string, handler: (message: RealtimeMessage) => void) => {
      on(type, handler);
      return () => off(type, handler);
    },
    [on, off]
  );

  const sendMessage = useCallback(
    (type: string, payload: Record<string, unknown>) => {
      send(type, payload);
    },
    [send]
  );

  const subscribeToAll = useCallback(
    (handler: (message: RealtimeMessage) => void) => {
      on('*', handler);
      return () => off('*', handler);
    },
    [on, off]
  );

  return {
    subscribe,
    subscribeToAll,
    sendMessage,
  };
}

export function useProgress() {
  const { state } = useRealtime();

  return {
    progress: state.progress,
    isComplete: state.progress === 100,
    hasProgress: state.progress !== null,
  };
}

export function usePluginTimings() {
  const { state } = useRealtime();

  return {
    timings: state.pluginTimings,
    plugins: Object.keys(state.pluginTimings),
    getTiming: (pluginId: string) => state.pluginTimings[pluginId] || null,
  };
}

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
  state: {
    isConnected: boolean;
    isConnecting: boolean;
    connectionStatus: 'idle' | 'connecting' | 'connected' | 'disconnected' | 'failed';
    lastResult: StreamingResultPayload | null;
    droppedFrames: number;
    slowDownWarnings: number;
    lastError: StreamingErrorPayload | null;
  };
}

export function useRealtimeStreaming(options: UseRealtimeStreamingOptions = {}): UseRealtimeStreamingReturn {
  const { pipelineId: initialPipelineId, apiKey, debug = false } = options;
  
  const [pipelineId, setPipelineId] = useState<string | undefined>(initialPipelineId);
  
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
  }, []);

  const disconnect = useCallback(() => {
    setPipelineId(undefined);
  }, []);

  const sendFrame = useCallback((bytes: Uint8Array | ArrayBuffer) => {
    if (!throttlerRef.current) return;
    
    // Use throttler to control FPS
    throttlerRef.current.throttle(() => {
      ws.sendBinaryFrame(bytes);
    });
  }, [ws]);

  // Reduce FPS when slow_down warnings received
  useEffect(() => {
    if (ws.slowDownWarnings > 0 && throttlerRef.current) {
      throttlerRef.current = new FPSThrottler(5);
    }
  }, [ws.slowDownWarnings]);

  const state = {
    isConnected: ws.isConnected,
    isConnecting: ws.isConnecting,
    connectionStatus: ws.connectionStatus as 'idle' | 'connecting' | 'connected' | 'disconnected' | 'failed',
    lastResult: ws.lastResult,
    droppedFrames: ws.droppedFrames,
    slowDownWarnings: ws.slowDownWarnings,
    lastError: ws.lastError,
  };

  return {
    connect,
    disconnect,
    sendFrame,
    state,
  };
}
