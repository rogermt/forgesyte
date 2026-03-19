/**
 * Phase 10: RealtimeClient connection test.
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { RealtimeClient, ConnectionState } from "@/realtime/RealtimeClient";

describe("RealtimeClient", () => {
    let client: RealtimeClient;

    beforeEach(() => {
        client = new RealtimeClient("ws://localhost:8000/v1/realtime");
    });

    afterEach(() => {
        client.disconnect();
    });

    it("should have IDLE state initially", () => {
        expect(client.getState()).toBe(ConnectionState.IDLE);
    });

    it("should not be connected initially", () => {
        expect(client.isConnected()).toBe(false);
    });

    it("should have correct message type exports", () => {
        expect(ConnectionState.IDLE).toBe("IDLE");
        expect(ConnectionState.CONNECTING).toBe("CONNECTING");
        expect(ConnectionState.CONNECTED).toBe("CONNECTED");
        expect(ConnectionState.DISCONNECTED).toBe("DISCONNECTED");
        expect(ConnectionState.RECONNECTING).toBe("RECONNECTING");
        expect(ConnectionState.CLOSED).toBe("CLOSED");
    });

    it("should have correct default max reconnect attempts", () => {
        expect(client.getMaxReconnectAttempts()).toBe(5);
    });

    it("should have correct reconnect delay schedule", () => {
        const delays = client.getReconnectDelays();
        expect(delays).toHaveLength(5);
        expect(delays[0]).toBe(1000);
        expect(delays[1]).toBe(2000);
        expect(delays[2]).toBe(4000);
        expect(delays[3]).toBe(8000);
        expect(delays[4]).toBe(16000);
    });
});

