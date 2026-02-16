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

/**
 * Canonical Phase 17 realtime hook export.
 * Replaces the old Phase 10 plugin-based realtime system.
 */
export function useRealtime(
  options?: UseRealtimeStreamingOptions
): UseRealtimeStreamingReturn {
  return useRealtimeStreaming(options);
}
