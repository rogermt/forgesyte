import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useRealtime } from "./useRealtime";

const wsMock = {
  isConnected: true,
  isConnecting: false,
  connectionStatus: "connected",

  lastResult: null,
  droppedFrames: 0,
  slowDownWarnings: 0,
  lastError: null,

  sendBinaryFrame: vi.fn(),
  disconnect: vi.fn(),

  framesSent: 0,
};

vi.mock("../hooks/useWebSocket", () => {
  return {
    __esModule: true,
    useWebSocket: () => wsMock,
  };
});

describe("useRealtime (Phase‑17)", () => {
  beforeEach(() => {
    wsMock.sendBinaryFrame.mockClear();
    wsMock.disconnect.mockClear();
    wsMock.framesSent = 0;
    wsMock.slowDownWarnings = 0;
  });

  it("connect() sets pipelineId and resets counters", () => {
    const { result } = renderHook(() => useRealtime());

    act(() => result.current.connect("p1"));

    expect(result.current.state.isConnected).toBe(true);
    expect(result.current.state.droppedFrames).toBe(0);
  });

  it("sendFrame increments framesSent", () => {
    const { result } = renderHook(() => useRealtime());
    act(() => result.current.connect("p1"));

    act(() => result.current.sendFrame(new Uint8Array([1])));

    expect(wsMock.sendBinaryFrame).toHaveBeenCalledTimes(1);
  });

  it("reduces FPS when slowDownWarnings > 0", () => {
    const { result } = renderHook(() => useRealtime());
    act(() => result.current.connect("p1"));

    wsMock.slowDownWarnings = 1;

    act(() => result.current.sendFrame(new Uint8Array([1])));

    expect(wsMock.sendBinaryFrame).toHaveBeenCalledTimes(1);
  });

  it("disconnect() clears connection state", () => {
    const { result } = renderHook(() => useRealtime());
    act(() => result.current.connect("p1"));

    // Change mock to simulate disconnected state
    act(() => {
      wsMock.isConnected = false;
      wsMock.connectionStatus = "disconnected";
      result.current.disconnect();
    });

    expect(result.current.state.isConnected).toBe(false);
  });
});
