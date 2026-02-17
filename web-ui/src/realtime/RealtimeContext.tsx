/**
 * Phase 17 Realtime Context
 *
 * Provides realtime streaming state and methods to components
 */

import { createContext, useContext, useReducer, useCallback, useEffect, useRef, ReactNode } from 'react';
import type {
  RealtimeState,
  ConnectionStatus,
  StreamingResultPayload,
  StreamingDroppedPayload,
  StreamingSlowDownPayload,
  StreamingErrorPayload,
} from './types';

// ============================================================================
// State
// ============================================================================

const initialState: RealtimeState = {
  status: "disconnected",
  lastResult: null,
  droppedFrames: 0,
  slowDownWarnings: 0,
  lastError: null,
  framesSent: 0,
  startTime: null,
};

type RealtimeAction =
  | { type: 'SET_STATUS'; payload: ConnectionStatus }
  | { type: 'SET_RESULT'; payload: StreamingResultPayload }
  | { type: 'DROP_FRAME' }
  | { type: 'SLOW_DOWN' }
  | { type: 'SET_ERROR'; payload: StreamingErrorPayload }
  | { type: 'CLEAR_ERROR' }
  | { type: 'SEND_FRAME' }
  | { type: 'RESET' };

function reducer(state: RealtimeState, action: RealtimeAction): RealtimeState {
  switch (action.type) {
    case 'SET_STATUS':
      return { ...state, status: action.payload };
    case 'SET_RESULT':
      return { ...state, lastResult: action.payload };
    case 'DROP_FRAME':
      return { ...state, droppedFrames: state.droppedFrames + 1 };
    case 'SLOW_DOWN':
      return { ...state, slowDownWarnings: state.slowDownWarnings + 1 };
    case 'SET_ERROR':
      return { ...state, lastError: action.payload };
    case 'CLEAR_ERROR':
      return { ...state, lastError: null };
    case 'SEND_FRAME':
      return {
        ...state,
        framesSent: state.framesSent + 1,
        startTime: state.startTime ?? Date.now(),
      };
    case 'RESET':
      return initialState;
    default:
      return state;
  }
}

// ============================================================================
// Context
// ============================================================================

interface RealtimeContextValue {
  state: RealtimeState;
  connect: (pipelineId: string) => void;
  disconnect: () => void;
  sendFrame: (bytes: Uint8Array) => void;
  handleMessage: (message: unknown) => void;
}

const RealtimeContext = createContext<RealtimeContextValue | null>(null);

interface RealtimeProviderProps {
  children: ReactNode;
  debug?: boolean;
}

function useRealtimeContext(): RealtimeContextValue {
  const context = useContext(RealtimeContext);
  if (!context) {
    throw new Error('useRealtime must be used within a RealtimeProvider');
  }
  return context;
}

export function RealtimeProvider({ children, debug = false }: RealtimeProviderProps) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const wsRef = useRef<WebSocket | null>(null);

  const log = useCallback((...args: unknown[]) => {
    if (debug) console.log('[Realtime]', ...args);
  }, [debug]);

  const connect = useCallback((pipelineId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      disconnect();
    }

    const wsUrl = new URL('/ws/video/stream', window.location.origin);
    wsUrl.protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    wsUrl.host = window.location.host;
    wsUrl.searchParams.set('pipeline_id', pipelineId);

    log('Connecting to:', wsUrl.toString());

    const ws = new WebSocket(wsUrl.toString());
    ws.binaryType = 'arraybuffer';
    wsRef.current = ws;

    ws.onopen = () => {
      log('Connected');
      dispatch({ type: 'SET_STATUS', payload: 'connected' });
    };

    ws.onclose = () => {
      log('Disconnected');
      dispatch({ type: 'SET_STATUS', payload: 'disconnected' });
    };

    ws.onerror = (error) => {
      log('Error:', error);
      dispatch({ type: 'SET_STATUS', payload: 'disconnected' });
    };

    ws.onmessage = (event) => {
      handleMessage(event.data);
    };
  }, [debug]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    dispatch({ type: 'RESET' });
  }, []);

  const sendFrame = useCallback((bytes: Uint8Array) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(bytes);
      dispatch({ type: 'SEND_FRAME' });
    }
  }, []);

  const handleMessage = useCallback((data: unknown) => {
    if (typeof data !== 'string') return;

    try {
      const message = JSON.parse(data) as
        | StreamingResultPayload
        | StreamingDroppedPayload
        | StreamingSlowDownPayload
        | StreamingErrorPayload;

      // Result message
      if ('result' in message) {
        dispatch({ type: 'SET_RESULT', payload: message as StreamingResultPayload });
        return;
      }

      // Dropped frame message
      if ('dropped' in message && message.dropped === true) {
        dispatch({ type: 'DROP_FRAME' });
        log('Frame dropped:', message);
        return;
      }

      // Slow-down warning
      if ('warning' in message && message.warning === 'slow_down') {
        dispatch({ type: 'SLOW_DOWN' });
        log('Slow-down warning received');
        return;
      }

      // Error message
      if ('error' in message) {
        dispatch({ type: 'SET_ERROR', payload: message as StreamingErrorPayload });
        log('Error:', message);
        return;
      }
    } catch (err) {
      log('Failed to parse message:', err);
    }
  }, [debug]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return (
    <RealtimeContext.Provider
      value={{
        state,
        connect,
        disconnect,
        sendFrame,
        handleMessage,
      }}
    >
      {children}
    </RealtimeContext.Provider>
  );
}

export function useRealtime(): RealtimeContextValue {
  return useRealtimeContext();
}

export { useRealtimeContext };

