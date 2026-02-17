/**
 * Phase 17: RealtimeClient Tests
 *
 * Tests for streaming functionality added to RealtimeClient
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { RealtimeClient, ConnectionState } from "../../src/realtime/RealtimeClient";

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;

  url: string;

  constructor(url: string) {
    this.url = url;
    // Immediately trigger onopen to resolve the connect() promise
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      this.onopen?.(new Event("open"));
    }, 0);
  }

  send = vi.fn();
  close = vi.fn((code?: number) => {
    this.readyState = MockWebSocket.CLOSED;
    setTimeout(() => {
      this.onclose?.(
        new CloseEvent("close", { code: code || 1000, wasClean: true })
      );
    }, 0);
  });

  simulateMessage(data: unknown) {
    this.onmessage?.(new MessageEvent("message", { data: JSON.stringify(data) }));
  }

  simulateClose(code = 1000, wasClean = true) {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.(new CloseEvent("close", { code, wasClean }));
  }
}

describe("RealtimeClient (Phase 17 Streaming)", () => {
  let mockInstances: MockWebSocket[] = [];

  beforeEach(() => {
    mockInstances = [];
    const wsMock = function(this: unknown, url: string) {
      const instance = new MockWebSocket(url);
      mockInstances.push(instance);
      return instance;
    } as unknown as typeof WebSocket;
    
    const wsMockAsUnknown = wsMock as unknown as Record<string, number>;
    wsMockAsUnknown.CONNECTING = MockWebSocket.CONNECTING;
    wsMockAsUnknown.OPEN = MockWebSocket.OPEN;
    wsMockAsUnknown.CLOSING = MockWebSocket.CLOSING;
    wsMockAsUnknown.CLOSED = MockWebSocket.CLOSED;

    (global as unknown as { WebSocket: unknown }).WebSocket = vi.fn(wsMock as unknown as () => unknown);
    const globalWs = (global as unknown as { WebSocket: Record<string, number> }).WebSocket;
    globalWs.CONNECTING = MockWebSocket.CONNECTING;
    globalWs.OPEN = MockWebSocket.OPEN;
    globalWs.CLOSING = MockWebSocket.CLOSING;
    globalWs.CLOSED = MockWebSocket.CLOSED;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const getLatestMock = () => mockInstances[mockInstances.length - 1];

  describe("sendFrame() - Phase 17 binary frame sending", () => {
    it("sends binary data when connected", async () => {
      const client = new RealtimeClient("ws://localhost:8000/ws/video/stream");

      // Connect first to create WebSocket
      await client.connect();
      await vi.runAllTimersAsync();

      expect(client.isConnected()).toBe(true);

      const binaryData = new Uint8Array([0xFF, 0xD8, 0xFF, 0xE0]);
      
      client.sendFrame(binaryData);

      // Verify binary data was sent
      const mockWs = getLatestMock();
      expect(mockWs.send).toHaveBeenCalled();
      const sentData = mockWs.send.mock.calls[0][0];
      expect(sentData).toBeInstanceOf(Uint8Array);
      expect(Array.from(sentData)).toEqual([0xFF, 0xD8, 0xFF, 0xE0]);
    });

    it("accepts ArrayBuffer and converts to Uint8Array", async () => {
      const client = new RealtimeClient("ws://localhost:8000/ws/video/stream");

      // Connect first to create WebSocket
      await client.connect();
      await vi.runAllTimersAsync();

      expect(client.isConnected()).toBe(true);

      const arrayBuffer = new ArrayBuffer(8);
      const uint8View = new Uint8Array(arrayBuffer);
      uint8View.set([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46]);
      
      client.sendFrame(arrayBuffer);

      const mockWs = getLatestMock();
      expect(mockWs.send).toHaveBeenCalled();
      const sentData = mockWs.send.mock.calls[0][0];
      expect(sentData).toBeInstanceOf(Uint8Array);
    });

    it("does not send when disconnected", () => {
      const client = new RealtimeClient("ws://localhost:8000/ws/video/stream");

      const binaryData = new Uint8Array([0xFF, 0xD8, 0xFF, 0xE0]);
      
      client.sendFrame(binaryData);

      // No WebSocket should have been created
      expect(mockInstances.length).toBe(0);
    });
  });
});
