import { describe, it, expect, vi } from "vitest";
import { renderHook } from "@testing-library/react";
import { useRealtime } from "./useRealtime";

// Mock RealtimeClient
vi.mock("./RealtimeClient", () => ({
  RealtimeClient: vi.fn().mockImplementation(() => ({
    connect: vi.fn().mockResolvedValue(undefined),
    disconnect: vi.fn(),
    sendFrame: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
    getState: vi.fn().mockReturnValue("CONNECTED"),
    isConnected: vi.fn().mockReturnValue(true),
  })),
  ConnectionState: {
    IDLE: "IDLE",
    CONNECTING: "CONNECTING",
    CONNECTED: "CONNECTED",
    DISCONNECTED: "DISCONNECTED",
    RECONNECTING: "RECONNECTING",
    CLOSED: "CLOSED",
  },
}));

// Mock FPSThrottler
vi.mock("../utils/FPSThrottler", () => ({
  FPSThrottler: class MockFPSThrottler {
    throttle = vi.fn((callback: () => void) => callback());
  },
}));

describe("useRealtime (Phase‑17)", () => {
  it("initializes with default state", () => {
    const { result } = renderHook(() => useRealtime());

    expect(result.current.state.isConnected).toBe(false);
    expect(result.current.state.isConnecting).toBe(false);
    expect(result.current.state.droppedFrames).toBe(0);
    expect(result.current.state.slowDownWarnings).toBe(0);
    expect(result.current.state.framesSent).toBe(0);
    expect(result.current.state.lastResult).toBe(null);
    expect(result.current.state.lastError).toBe(null);
  });

  it("provides required functions", () => {
    const { result } = renderHook(() => useRealtime());

    expect(result.current.connect).toBeDefined();
    expect(result.current.disconnect).toBeDefined();
    expect(result.current.sendFrame).toBeDefined();
    expect(result.current.clearError).toBeDefined();
  });

  it("provides currentPipelineId and wsUrl", () => {
    const { result } = renderHook(() => useRealtime());

    expect(result.current.currentPipelineId).toBe(null);
    expect(result.current.wsUrl).toBe("");
  });
});
