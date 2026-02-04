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

import { useCallback } from 'react';
import { useRealtime } from './RealtimeContext';
import { RealtimeMessage, ConnectionState } from './RealtimeClient';

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

