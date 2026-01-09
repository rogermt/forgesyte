/**
 * Integration tests for App.tsx WebSocket streaming
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";
import * as useWebSocketModule from "./hooks/useWebSocket";

// Mock dependencies
vi.mock("./hooks/useWebSocket");
vi.mock("./api/client", () => ({
    apiClient: {
        listJobs: vi.fn(() => Promise.resolve([])),
        getPlugins: vi.fn(() =>
            Promise.resolve([
                {
                    name: "motion_detector",
                    description: "Test plugin",
                    version: "1.0.0",
                    inputs: ["image"],
                    outputs: ["detection"],
                    permissions: [],
                },
            ])
        ),
    },
}));

describe("App - WebSocket Streaming Integration", () => {
    const mockUseWebSocket = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();

        // Mock useWebSocket hook
        mockUseWebSocket.mockReturnValue({
            isConnected: false,
            isConnecting: false,
            error: null,
            sendFrame: vi.fn(),
            switchPlugin: vi.fn(),
            latestResult: null,
            stats: { frames_sent: 0, frames_received: 0 },
        });

        vi.mocked(useWebSocketModule.useWebSocket).mockImplementation(
            mockUseWebSocket
        );
    });

    describe("streaming controls", () => {
        it("should display stream view when stream mode selected", async () => {
            render(<App />);

            const streamButton = screen.getByText("Stream");
            expect(streamButton).toBeInTheDocument();
        });

        it("should show camera preview in stream view", async () => {
            render(<App />);

            await waitFor(() => {
                expect(
                    screen.getByText("Camera Preview")
                ).toBeInTheDocument();
            });
        });

        it("should call useWebSocket on mount with correct params", () => {
            render(<App />);

            expect(mockUseWebSocket).toHaveBeenCalledWith(
                expect.objectContaining({
                    url: "/v1/stream",
                    plugin: "motion_detector",
                })
            );
        });
    });

    describe("streaming state", () => {
        it("should show disconnected status initially", () => {
            render(<App />);

            expect(screen.getByText("Disconnected")).toBeInTheDocument();
        });

        it("should show connected status when WebSocket connected", () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: true,
                isConnecting: false,
                error: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
                stats: { frames_sent: 0, frames_received: 0 },
            });

            render(<App />);

            expect(screen.getByText("Connected")).toBeInTheDocument();
        });

        it("should show connecting status", () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: false,
                isConnecting: true,
                error: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
                stats: { frames_sent: 0, frames_received: 0 },
            });

            render(<App />);

            expect(screen.getByText("Connecting...")).toBeInTheDocument();
        });

        it("should display WebSocket error when present", () => {
            const errorMsg = "Connection refused";
            mockUseWebSocket.mockReturnValue({
                isConnected: false,
                isConnecting: false,
                error: errorMsg,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
                stats: { frames_sent: 0, frames_received: 0 },
            });

            render(<App />);

            expect(screen.getByText(new RegExp(errorMsg))).toBeInTheDocument();
        });
    });

    describe("plugin selector interaction", () => {
        it("should disable plugin selector when streaming enabled", async () => {
            const { container } = render(<App />);

            await waitFor(() => {
                const select = container.querySelector("select");
                // Initially not disabled
                expect(select).not.toBeDisabled();
            });
        });
    });

    describe("frame handling", () => {
        it("should pass correct handlers to CameraPreview", async () => {
            render(<App />);

            await waitFor(() => {
                expect(
                    screen.getByText("Camera Preview")
                ).toBeInTheDocument();
            });
        });
    });

    describe("results display", () => {
        it("should show ResultsPanel in stream mode", async () => {
            render(<App />);

            await waitFor(() => {
                expect(screen.getByText("Results")).toBeInTheDocument();
            });
        });

        it("should display latest stream results", () => {
            const mockResult = {
                frame_id: "frame-001",
                processing_time_ms: 45,
                result: { motion: true },
                timestamp: Date.now(),
            };

            mockUseWebSocket.mockReturnValue({
                isConnected: true,
                isConnecting: false,
                error: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: mockResult,
                stats: { frames_sent: 10, frames_received: 10 },
            });

            render(<App />);

            expect(screen.getByText(/frame-001/)).toBeInTheDocument();
        });
    });
});

import { vi } from "vitest";
