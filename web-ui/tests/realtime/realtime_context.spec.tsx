/**
 * Phase 10: RealtimeContext dispatch test.
 */

import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { RealtimeProvider, useRealtime } from "@/realtime/RealtimeContext";

describe("RealtimeContext", () => {
    it("should provide initial state", () => {
        let capturedState: any = null;

        function TestComponent() {
            const context = useRealtime();
            capturedState = context;
            return <div>Test</div>;
        }

        render(
            <RealtimeProvider>
                <TestComponent />
            </RealtimeProvider>
        );

        expect(capturedState).toBeDefined();
        expect(capturedState.state.progress).toBeNull();
        expect(capturedState.state.isConnected).toBe(false);
    });

    it("should have isConnected false initially", () => {
        let connectedState: any = null;

        function TestComponent() {
            const context = useRealtime();
            connectedState = context.state.isConnected;
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
        let capturedContext: any = null;

        function TestComponent() {
            const context = useRealtime();
            capturedContext = context;
            return <div>Test</div>;
        }

        render(
            <RealtimeProvider>
                <TestComponent />
            </RealtimeProvider>
        );

        expect(capturedContext.connect).toBeDefined();
        expect(typeof capturedContext.connect).toBe("function");
        expect(capturedContext.disconnect).toBeDefined();
        expect(typeof capturedContext.disconnect).toBe("function");
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

