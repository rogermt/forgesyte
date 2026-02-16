/**
 * Phase 10: Real-Time Context for state management.
 *
 * TODO: Implement the following:
 * - Provider component for real-time state
 * - State machine integration
 * - Message dispatching
 * - Plugin inspector state
 * - Progress tracking
 *
 * Author: Roger
 * Phase: 10
 */

import { createContext, useContext, useReducer, useEffect, useState, ReactNode } from 'react';
import type { StreamingResultPayload, StreamingErrorPayload } from './types';
import { RealtimeClient, RealtimeMessage, ConnectionState } from './RealtimeClient';

interface RealtimeState {
  connectionState: ConnectionState;
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

type RealtimeAction =
  | { type: 'SET_CONNECTION_STATE'; payload: ConnectionState }
  | { type: 'SET_PROGRESS'; payload: number }
  | { type: 'SET_PLUGIN_TIMINGS'; payload: Record<string, number> }
  | { type: 'ADD_WARNING'; payload: string }
  | { type: 'ADD_ERROR'; payload: string }
  | { type: 'SET_CURRENT_PLUGIN'; payload: string | null }
  | { type: 'RESET' }
  // Phase 17: Streaming actions
  | { type: 'SET_LAST_RESULT'; payload: StreamingResultPayload }
  | { type: 'INCREMENT_DROPPED_FRAMES' }
  | { type: 'INCREMENT_SLOW_DOWN_WARNINGS' }
  | { type: 'SET_LAST_ERROR'; payload: StreamingErrorPayload };

const initialState: RealtimeState = {
  connectionState: ConnectionState.IDLE,
  progress: null,
  pluginTimings: {},
  warnings: [],
  errors: [],
  currentPlugin: null,
  isConnected: false,
  // Phase 17: Streaming state
  lastResult: null,
  droppedFrames: 0,
  slowDownWarnings: 0,
  lastError: null,
};

function reducer(state: RealtimeState, action: RealtimeAction): RealtimeState {
  switch (action.type) {
    case 'SET_CONNECTION_STATE':
      return {
        ...state,
        connectionState: action.payload,
        isConnected: action.payload === ConnectionState.CONNECTED,
      };
    case 'SET_PROGRESS':
      return { ...state, progress: action.payload };
    case 'SET_PLUGIN_TIMINGS':
      return { ...state, pluginTimings: action.payload };
    case 'ADD_WARNING':
      return { ...state, warnings: [...state.warnings, action.payload] };
    case 'ADD_ERROR':
      return { ...state, errors: [...state.errors, action.payload] };
    case 'SET_CURRENT_PLUGIN':
      return { ...state, currentPlugin: action.payload };
    case 'RESET':
      return initialState;
    // Phase 17: Streaming action handlers
    case 'SET_LAST_RESULT':
      return { ...state, lastResult: action.payload };
    case 'INCREMENT_DROPPED_FRAMES':
      return { ...state, droppedFrames: state.droppedFrames + 1 };
    case 'INCREMENT_SLOW_DOWN_WARNINGS':
      return { ...state, slowDownWarnings: state.slowDownWarnings + 1 };
    case 'SET_LAST_ERROR':
      return { ...state, lastError: action.payload };
    default:
      return state;
  }
}

interface RealtimeContextValue {
  state: RealtimeState;
  client: RealtimeClient | null;
  connect: () => Promise<void>;
  disconnect: () => void;
  send: (type: string, payload: Record<string, unknown>) => void;
  on: (type: string, handler: (message: RealtimeMessage) => void) => void;
  off: (type: string, handler: (message: RealtimeMessage) => void) => void;
}

const RealtimeContext = createContext<RealtimeContextValue | null>(null);

interface RealtimeProviderProps {
  children: ReactNode;
  url?: string;
}

// Helper to ensure context is not null
function useRealtimeContext(): RealtimeContextValue {
  const context = useContext(RealtimeContext);
  if (!context) {
    throw new Error('useRealtime must be used within a RealtimeProvider');
  }
  return context;
}

export function RealtimeProvider({ children, url = 'ws://localhost:8000/v1/realtime' }: RealtimeProviderProps) {
   const [state, dispatch] = useReducer(reducer, initialState);
   const [client, setClient] = useState<RealtimeClient | null>(null);

  useEffect(() => {
    const realtimeClient = new RealtimeClient(url);
    setClient(realtimeClient);

    realtimeClient.on('connected', () => {
      dispatch({ type: 'SET_CONNECTION_STATE', payload: ConnectionState.CONNECTED });
    });

    realtimeClient.on('disconnected', () => {
      dispatch({ type: 'SET_CONNECTION_STATE', payload: ConnectionState.DISCONNECTED });
    });

    realtimeClient.on('progress', (message) => {
      dispatch({ type: 'SET_PROGRESS', payload: message.payload.progress as number });
    });

    realtimeClient.on('plugin_status', (message) => {
      dispatch({ type: 'SET_CURRENT_PLUGIN', payload: message.payload.plugin_id as string });
    });

    realtimeClient.on('warning', (message) => {
      dispatch({ type: 'ADD_WARNING', payload: message.payload.message as string });
    });

    realtimeClient.on('error', (message) => {
      dispatch({ type: 'ADD_ERROR', payload: message.payload.message as string });
    });

    realtimeClient.on('*', (message) => {
      if (message.type === 'plugin_timing') {
        const timings = { ...state.pluginTimings };
        timings[message.payload.plugin_id as string] = message.payload.timing_ms as number;
        dispatch({ type: 'SET_PLUGIN_TIMINGS', payload: timings });
      }
    });

    return () => {
      realtimeClient.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url]);

  const connect = async () => {
    if (client) {
      await client.connect();
    }
  };

  const disconnect = () => {
    if (client) {
      client.disconnect();
    }
  };

  const send = (type: string, payload: Record<string, unknown>) => {
    if (client) {
      client.send(type, payload);
    }
  };

  const on = (type: string, handler: (message: RealtimeMessage) => void) => {
    if (client) {
      client.on(type, handler);
    }
  };

  const off = (type: string, handler: (message: RealtimeMessage) => void) => {
    if (client) {
      client.off(type, handler);
    }
  };

  return (
    <RealtimeContext.Provider
      value={{
        state,
        client,
        connect,
        disconnect,
        send,
        on,
        off,
      }}
    >
      {children}
    </RealtimeContext.Provider>
  );
}

export function useRealtime(): RealtimeContextValue {
  return useRealtimeContext();
}

