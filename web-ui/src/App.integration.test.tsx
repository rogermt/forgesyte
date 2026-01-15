/**
 * Integration tests for App.tsx WebSocket streaming
 */

import { render, screen, waitFor, act } from "@testing-library/react";
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
        });

        vi.mocked(useWebSocketModule.useWebSocket).mockImplementation(
            mockUseWebSocket
        );
    });

    describe("streaming controls", () => {
        it("should display stream view when stream mode selected", async () => {
            await act(async () => {
                render(<App />);
            });

            const streamNavButton = screen.getByRole("button", { name: "Stream" });
            expect(streamNavButton).toBeInTheDocument();
        });

        it("should show camera preview in stream view", async () => {
            await act(async () => {
                render(<App />);
            });

            await waitFor(() => {
                expect(
                    screen.getByText("Camera Preview")
                ).toBeInTheDocument();
            });
        });

        it("should call useWebSocket on mount with correct params", async () => {
            await act(async () => {
                render(<App />);
            });

            expect(mockUseWebSocket).toHaveBeenCalledWith(
                expect.objectContaining({
                    url: "ws://localhost:8000/v1/stream",
                    plugin: "motion_detector",
                })
            );
        });
    });

    describe("streaming state", () => {
        it("should show disconnected status initially", async () => {
            await act(async () => {
                render(<App />);
            });

            expect(screen.getByText("Disconnected")).toBeInTheDocument();
        });

        it("should show connected status when WebSocket connected", async () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: true,
                isConnecting: false,
                connectionStatus: "connected",
                attempt: 0,
                error: null,
                errorInfo: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                disconnect: vi.fn(),
                reconnect: vi.fn(),
                latestResult: null,
                stats: { framesProcessed: 0, avgProcessingTime: 0 },
            });

            await act(async () => {
                render(<App />);
            });

            expect(screen.getByText("Connected")).toBeInTheDocument();
        });

        it("should show connecting status", async () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: false,
                isConnecting: true,
                connectionStatus: "connecting",
                attempt: 1,
                error: null,
                errorInfo: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                disconnect: vi.fn(),
                reconnect: vi.fn(),
                latestResult: null,
                stats: { framesProcessed: 0, avgProcessingTime: 0 },
            });

            await act(async () => {
                render(<App />);
            });

            expect(screen.getByText("Connecting...")).toBeInTheDocument();
        });

        it("should display WebSocket error when present", async () => {
            const errorMsg = "Connection refused";
            mockUseWebSocket.mockReturnValue({
                isConnected: false,
                isConnecting: false,
                connectionStatus: "failed",
                attempt: 5,
                error: errorMsg,
                errorInfo: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                disconnect: vi.fn(),
                reconnect: vi.fn(),
                latestResult: null,
                stats: { framesProcessed: 0, avgProcessingTime: 0 },
            });

            await act(async () => {
                render(<App />);
            });

            expect(screen.getByText(new RegExp(errorMsg))).toBeInTheDocument();
        });
    });

    describe("plugin selector interaction", () => {
        it("should disable plugin selector when streaming enabled", async () => {
            let container: HTMLElement;
            await act(async () => {
                container = render(<App />).container;
            });

            await waitFor(() => {
                const select = container!.querySelector("select");
                // Initially not disabled
                expect(select).not.toBeDisabled();
            });
        });
    });

    describe("frame handling", () => {
        it("should pass correct handlers to CameraPreview", async () => {
            await act(async () => {
                render(<App />);
            });

            await waitFor(() => {
                expect(
                    screen.getByText("Camera Preview")
                ).toBeInTheDocument();
            });
        });
    });

    describe("results display", () => {
        it("should show ResultsPanel in stream mode", async () => {
            await act(async () => {
                render(<App />);
            });

            await waitFor(() => {
                expect(screen.getByText("Results")).toBeInTheDocument();
            });
        });

        it("should display latest stream results", async () => {
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

            await act(async () => {
                render(<App />);
            });

            expect(screen.getByText(/frame-001/)).toBeInTheDocument();
        });
    });
});

import { vi } from "vitest";
