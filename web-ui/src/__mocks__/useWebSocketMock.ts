/**
 * Shared mock utility for useWebSocket hook
 * Used across App.test.tsx, App.integration.test.tsx, and App.tdd.test.tsx
 */

import { vi } from "vitest";

export type MockReturn = {
  isConnected: boolean;
  isConnecting: boolean;
  connectionStatus: 
    | "idle" 
    | "connecting" 
    | "connected" 
    | "reconnecting" 
    | "disconnected" 
    | "failed";
  attempt: number;
  error: string | null;
  errorInfo: Record<string, unknown> | null;
  sendFrame: ReturnType<typeof vi.fn>;
  switchPlugin: ReturnType<typeof vi.fn>;
  disconnect: ReturnType<typeof vi.fn>;
  reconnect: ReturnType<typeof vi.fn>;
  latestResult: Record<string, unknown> | null;
  stats: { framesProcessed: number; avgProcessingTime: number };
};

export function createWebSocketMock(overrides: Partial<MockReturn> = {}): MockReturn {
  const base: MockReturn = {
    isConnected: false,
    isConnecting: false,
    connectionStatus: "disconnected",
    attempt: 0,
    error: null,
    errorInfo: null,
    sendFrame: vi.fn(),
    switchPlugin: vi.fn(),
    disconnect: vi.fn(),
    reconnect: vi.fn(),
    latestResult: null,
    stats: { framesProcessed: 0, avgProcessingTime: 0 },
  };

  return { ...base, ...overrides };
}

