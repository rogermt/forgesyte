/**
 * Phase 10: RealtimeContext dispatch test.
 */

import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { RealtimeProvider, useRealtime } from "@/realtime/RealtimeContext";

describe("RealtimeContext", () => {
    it("should provide initial state", () => {
        let capturedState: ReturnType<typeof useRealtime>["state"] | null = null;

        function TestComponent() {
            const { state } = useRealtime();
            capturedState = state;
            return <div>Test</div>;
        }

        render(
            <RealtimeProvider>
                <TestComponent />
            </RealtimeProvider>
        );

        expect(capturedState).toBeDefined();
        expect(capturedState?.progress).toBeNull();
        expect(capturedState?.isConnected).toBe(false);
    });

    it("should have isConnected false initially", () => {
        let connectedState: boolean | null = null;

        function TestComponent() {
            const { state } = useRealtime();
            connectedState = state.isConnected;
            return <div>Test</div>;
        }

        render(
            <RealtimeProvider>
                <TestComponent />
            </RealtimeProvider>
        );

        expect(connectedState).toBe(false);
    });

    it("should expose connect and disconnect methods", () => {
        let methods: { connect: () => Promise<void>; disconnect: () => void } | null = null;

        function TestComponent() {
            const context = useRealtime();
            methods = {
                connect: context.connect,
                disconnect: context.disconnect,
            };
            return <div>Test</div>;
        }

        render(
            <RealtimeProvider>
                <TestComponent />
            </RealtimeProvider>
        );

        expect(methods?.connect).toBeDefined();
        expect(typeof methods?.connect).toBe("function");
        expect(methods?.disconnect).toBeDefined();
        expect(typeof methods?.disconnect).toBe("function");
    });

    it("should expose send method", () => {
        let send: ((type: string, payload: Record<string, unknown>) => void) | null = null;

        function TestComponent() {
            const { send: sendFn } = useRealtime();
            send = sendFn;
            return <div>Test</div>;
        }

        render(
            <RealtimeProvider>
                <TestComponent />
            </RealtimeProvider>
        );

        expect(send).toBeDefined();
        expect(typeof send).toBe("function");
    });
});

