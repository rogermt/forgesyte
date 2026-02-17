/**
 * Phase 17 useRealtime Hook
 *
 * Convenience hook for accessing realtime state and methods
 */

import { useRealtime as useRealtimeContext } from './RealtimeContext';
import type { RealtimeState } from './types';

export function useRealtime(): {
  state: RealtimeState;
  connect: (pipelineId: string) => void;
  disconnect: () => void;
  sendFrame: (bytes: Uint8Array) => void;
} {
  const context = useRealtimeContext();
  return {
    state: context.state,
    connect: context.connect,
    disconnect: context.disconnect,
    sendFrame: context.sendFrame,
  };
}

export default useRealtime;