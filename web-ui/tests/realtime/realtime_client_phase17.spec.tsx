/**
 * Phase 17: RealtimeClient Extension Tests
 *
 * Tests for Phase 17 streaming functionality added to RealtimeClient
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { RealtimeClient, ConnectionState } from "@/realtime/RealtimeClient";

describe("RealtimeClient (Phase 17 Streaming)", () => {
  let client: RealtimeClient;

  beforeEach(() => {
    client = new RealtimeClient("ws://localhost:8000/ws/video/stream?pipeline_id=test");
  });

  describe("sendFrame() method", () => {
    it("sends binary data when connected", () => {
      // Mock WebSocket
      const mockWebSocket = {
        readyState: WebSocket.OPEN,
        send: vi.fn(),
        close: vi.fn(),
      };
      (client as any).ws = mockWebSocket;
      (client as any).state = ConnectionState.CONNECTED;

      const binaryData = new Uint8Array([0xFF, 0xD8, 0xFF, 0xE0]);
      client.sendFrame(binaryData);

      expect(mockWebSocket.send).toHaveBeenCalledWith(binaryData);
    });

    it("converts ArrayBuffer to Uint8Array", () => {
      const mockWebSocket = {
        readyState: WebSocket.OPEN,
        send: vi.fn(),
        close: vi.fn(),
      };
      (client as any).ws = mockWebSocket;
      (client as any).state = ConnectionState.CONNECTED;

      const arrayBuffer = new ArrayBuffer(4);
      const uint8View = new Uint8Array(arrayBuffer);
      uint8View.set([0xFF, 0xD8, 0xFF, 0xE0]);
      client.sendFrame(arrayBuffer);

      expect(mockWebSocket.send).toHaveBeenCalledWith(expect.any(Uint8Array));
      const sentData = mockWebSocket.send.mock.calls[0][0];
      expect(Array.from(sentData)).toEqual([0xFF, 0xD8, 0xFF, 0xE0]);
    });

    it("does not send when not connected", () => {
      const mockWebSocket = {
        readyState: WebSocket.CLOSED,
        send: vi.fn(),
        close: vi.fn(),
      };
      (client as any).ws = mockWebSocket;
      (client as any).state = ConnectionState.DISCONNECTED;

      const binaryData = new Uint8Array([0xFF, 0xD8, 0xFF, 0xE0]);
      client.sendFrame(binaryData);

      expect(mockWebSocket.send).not.toHaveBeenCalled();
    });

    it("does not send when WebSocket is null", () => {
      (client as any).ws = null;
      (client as any).state = ConnectionState.CONNECTED;

      const binaryData = new Uint8Array([0xFF, 0xD8, 0xFF, 0xE0]);
      client.sendFrame(binaryData);

      // Should not throw, just do nothing
      expect(() => client.sendFrame(binaryData)).not.toThrow();
    });
  });
});
