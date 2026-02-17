/**
 * Phase 17: Real-Time Context for state management.
 *
 * Updated to use Phase-17 useRealtime hook for streaming.
 * Maintains backward compatibility with Phase-10 legacy components.
 */

import { createContext, useContext, ReactNode } from 'react';
import { useRealtime as useRealtimeStreaming } from './useRealtime';
import type { StreamingResultPayload, StreamingErrorPayload } from './types';

interface RealtimeState {
  connectionState: string;
  progress: number | null;
  pluginTimings: Record<string, number>;
  warnings: string[];
  errors: string[];
  currentPlugin: string | null;
  isConnected: boolean;
  // Phase 17: Streaming state
  lastResult: StreamingResultPayload | null;
  droppedFrames: number;
  slowDownWarnings: number;
  lastError: StreamingErrorPayload | null;
}

interface RealtimeContextValue {
  state: RealtimeState;
  connect: (pipelineId: string) => void;
  disconnect: () => void;
  sendFrame: (bytes: Uint8Array | ArrayBuffer) => void;
  clearError: () => void;
  currentPipelineId: string | null;
  // Phase 10 legacy fields for backward compatibility
  client: any; // eslint-disable-line @typescript-eslint/no-explicit-any
  send: any; // eslint-disable-line @typescript-eslint/no-explicit-any
  on: any; // eslint-disable-line @typescript-eslint/no-explicit-any
  off: any; // eslint-disable-line @typescript-eslint/no-explicit-any
}

const RealtimeContext = createContext<RealtimeContextValue | null>(null);

interface RealtimeProviderProps {
  children: ReactNode;
}

// Helper to ensure context is not null
export function useRealtimeContext(): RealtimeContextValue {
  const context = useContext(RealtimeContext);
  if (!context) {
    throw new Error('useRealtime must be used within a RealtimeProvider');
  }
  return context;
}

export function RealtimeProvider({ children }: RealtimeProviderProps) {
  // Use Phase-17 useRealtime hook (renamed to avoid conflict)
  const { connect, disconnect, sendFrame, clearError, currentPipelineId, state: streamingState } = useRealtimeStreaming();

  // Map Phase-17 state to RealtimeState format
  const state: RealtimeState = {
    connectionState: streamingState.connectionStatus,
    progress: null, // Phase-17 doesn't use progress
    pluginTimings: {}, // Phase-17 doesn't use plugin timings
    warnings: [], // Phase-17 doesn't use warnings
    errors: [], // Phase-17 doesn't use errors
    currentPlugin: null, // Phase-17 doesn't use currentPlugin
    isConnected: streamingState.isConnected,
    // Phase 17: Streaming state
    lastResult: streamingState.lastResult,
    droppedFrames: streamingState.droppedFrames,
    slowDownWarnings: streamingState.slowDownWarnings,
    lastError: streamingState.lastError,
  };

  return (
    <RealtimeContext.Provider
      value={{
        state,
        connect,
        disconnect,
        sendFrame,
        clearError,
        currentPipelineId,
        // Phase 10 legacy fields (no-ops for Phase-17)
        client: null,
        send: () => {},
        on: () => {},
        off: () => {},
      }}
    >
      {children}
    </RealtimeContext.Provider>
  );
}

// Phase 10 legacy export for backward compatibility
export function useRealtime(): RealtimeContextValue {
  return useRealtimeContext();
}

// Legacy export for backward compatibility
export function useRealtimeLegacy(): RealtimeContextValue {
  return useRealtimeContext();
}
