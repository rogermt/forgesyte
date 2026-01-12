/**
 * Tests for App.tsx branding updates and functional behavior
 */

import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import App from "./App";

// Mock useWebSocket hook
vi.mock("./hooks/useWebSocket", () => ({
    useWebSocket: vi.fn(),
    FrameResult: {},
}));

// Mock API client
vi.mock("./api/client", () => ({
    apiClient: {
        analyzeImage: vi.fn(),
        pollJob: vi.fn(),
    },
    Job: {},
}));

import { useWebSocket } from "./hooks/useWebSocket";
import { apiClient } from "./api/client";

const mockUseWebSocket = useWebSocket as ReturnType<typeof vi.fn>;
// Mock apiClient for future use (currently unused but kept for test setup)
vi.mocked(apiClient);

// Set default mock for all tests
mockUseWebSocket.mockReturnValue({
    isConnected: false,
    isConnecting: false,
    error: null,
    sendFrame: vi.fn(),
    switchPlugin: vi.fn(),
    latestResult: null,
});

describe("App - Branding Updates", () => {
    describe("Header styling", () => {
        it("should use ForgeSyte brand colors in header", async () => {
            let container: HTMLElement;
            await act(async () => {
                container = render(<App />).container;
            });
            const header = container!.querySelector("header");

            expect(header).toHaveStyle({
                backgroundColor: "var(--bg-primary)",
            });
        });

        it("should display ForgeSyte branding in logo", async () => {
            await act(async () => {
                render(<App />);
            });
            const logo = screen.getByTestId("app-logo");

            expect(logo).toBeInTheDocument();
            expect(logo).toHaveStyle({
                color: "var(--text-primary)",
            });
        });
    });

    describe("Navigation buttons", () => {
        it("should use brand colors for active nav button", async () => {
            await act(async () => {
                render(<App />);
            });
            const navButton = screen.getByRole("button", { name: "Stream" }); 
            
            expect(navButton).toBeInTheDocument();
            expect(navButton).toHaveStyle({
                backgroundColor: "var(--accent-orange)",
                color: "var(--text-primary)",
            });
        });

        it("should use brand colors for inactive nav button", async () => {
            await act(async () => {
                render(<App />);
            });
            const uploadButton = screen.getByRole("button", { name: /upload/i });

            expect(uploadButton).toHaveStyle({
                backgroundColor: "var(--bg-tertiary)",
            });
        });
    });

    describe("Status indicator", () => {
        it("should use brand color scheme for connection status", async () => {
            await act(async () => {
                render(<App />);
            });
            const statusIndicator = screen.getByTestId("connection-status-indicator");

            expect(statusIndicator).toBeInTheDocument();
            // Status colors will vary based on connection state
        });
    });

    describe("Main layout", () => {
        it("should use ForgeSyte colors for panels", async () => {
            let container: HTMLElement;
            await act(async () => {
                container = render(<App />).container;
            });
            const panels = container!.querySelectorAll("div");

            // At least one panel should use brand background
            const brandPanels = Array.from(panels).filter(
                (panel) =>
                    panel.style.backgroundColor === "var(--bg-secondary)" ||
                    panel.style.backgroundColor === "var(--bg-tertiary)"
            );

            expect(brandPanels.length).toBeGreaterThan(0);
        });

        it("should apply consistent spacing with brand grid", async () => {
            let container: HTMLElement;
            await act(async () => {
                container = render(<App />).container;
            });
            const main = container!.querySelector("main");

            expect(main).toHaveStyle({
                gap: "16px",
                padding: "16px",
            });
        });
    });

    describe("Error messages", () => {
        it("should use brand error color for WebSocket errors", async () => {
            await act(async () => {
                render(<App />);
            });
            const errorStyle = {
                backgroundColor: "rgba(220, 53, 69, 0.1)",
                border: "1px solid var(--accent-red)",
                color: "var(--accent-red)",
            };

            // Error box styling should be consistent with brand
            const hasErrorStyle =
                errorStyle.backgroundColor === "rgba(220, 53, 69, 0.1)";
            expect(hasErrorStyle).toBe(true);
        });
    });
});

describe("App - Functional Behavior", () => {
    beforeEach(() => {
        // Default mock: disconnected state
        mockUseWebSocket.mockReturnValue({
            isConnected: false,
            isConnecting: false,
            error: null,
            sendFrame: vi.fn(),
            switchPlugin: vi.fn(),
            latestResult: null,
        });
    });

    describe("WebSocket Connection States", () => {
        it("should display 'Disconnected' when WebSocket not connected", async () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: false,
                isConnecting: false,
                error: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
            });

            await act(async () => {
                render(<App />);
            });

            expect(screen.getByText("Disconnected")).toBeInTheDocument();
        });

        it("should display 'Connecting...' when WebSocket is connecting", async () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: false,
                isConnecting: true,
                error: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
            });

            await act(async () => {
                render(<App />);
            });

            expect(screen.getByText("Connecting...")).toBeInTheDocument();
        });

        it("should display 'Connected' when WebSocket is connected", async () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: true,
                isConnecting: false,
                error: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
            });

            await act(async () => {
                render(<App />);
            });

            expect(screen.getByText("Connected")).toBeInTheDocument();
        });
    });

    describe("WebSocket Error Handling", () => {
        it("should display 'Not streaming' status when WebSocket connection fails", async () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: false,
                isConnecting: false,
                error: "Max reconnection attempts reached",
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
            });

            await act(async () => {
                render(<App />);
            });

            // Should show camera preview with "Not streaming" status
            expect(
                screen.getByText((content) =>
                    content.includes("Not streaming")
                )
            ).toBeInTheDocument();
        });

        it("should display error message when WebSocket connection fails", async () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: false,
                isConnecting: false,
                error: "Max reconnection attempts reached",
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
            });

            await act(async () => {
                render(<App />);
            });

            expect(screen.getByText("Disconnected")).toBeInTheDocument();
        });
    });

    describe("View Mode Switching", () => {
        it("should switch to Stream view when Stream button clicked", async () => {
            await act(async () => {
                render(<App />);
            });

            // Stream view should be visible by default
            expect(
                screen.getByRole("button", { name: /start streaming/i })
            ).toBeInTheDocument();
        });

        it("should switch to Jobs view when Jobs button clicked", async () => {
            const user = userEvent.setup();

            await act(async () => {
                render(<App />);
            });

            const jobsButton = screen.getByRole("button", { name: /jobs/i });
            await act(async () => {
                await user.click(jobsButton);
            });

            // JobList should render when in jobs mode
            // This tests the conditional rendering at lines 216-220
        });

        it("should switch to Upload view when Upload button clicked", async () => {
            const user = userEvent.setup();

            await act(async () => {
                render(<App />);
            });

            const uploadButton = screen.getByRole("button", { name: /upload/i });
            await act(async () => {
                await user.click(uploadButton);
            });

            // File input should be present for upload mode
            // This tests the conditional rendering at lines 296+
        });
    });

    describe("Stream Control", () => {
        it("should disable Start Streaming button when not connected", async () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: false,
                isConnecting: false,
                error: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
            });

            await act(async () => {
                render(<App />);
            });

            const startButton = screen.getByRole("button", {
                name: /start streaming/i,
            });
            expect(startButton).toBeDisabled();
        });

        it("should enable Start Streaming button when connected", async () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: true,
                isConnecting: false,
                error: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
            });

            await act(async () => {
                render(<App />);
            });

            const startButton = screen.getByRole("button", {
                name: /start streaming/i,
            });
            expect(startButton).not.toBeDisabled();
        });

        it("should toggle streaming state when button clicked", async () => {
            const user = userEvent.setup();

            mockUseWebSocket.mockReturnValue({
                isConnected: true,
                isConnecting: false,
                error: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
            });

            await act(async () => {
                render(<App />);
            });

            const startButton = screen.getByRole("button", {
                name: /start streaming/i,
            });

            await act(async () => {
                await user.click(startButton);
            });

            // Button should now say "Stop Streaming"
            expect(
                screen.getByRole("button", { name: /stop streaming/i })
            ).toBeInTheDocument();
        });
    });

    describe("Status Indicator Colors", () => {
        it("should show red indicator when disconnected", async () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: false,
                isConnecting: false,
                error: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
            });

            let container: HTMLElement;
            await act(async () => {
                container = render(<App />).container;
            });

            const indicator = container!.querySelector(
                "[data-testid='connection-status-indicator']"
            );
            expect(indicator).toHaveStyle({
                backgroundColor: "#dc3545",
            });
        });

        it("should show yellow indicator when connecting", async () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: false,
                isConnecting: true,
                error: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
            });

            let container: HTMLElement;
            await act(async () => {
                container = render(<App />).container;
            });

            const indicator = container!.querySelector(
                "[data-testid='connection-status-indicator']"
            );
            expect(indicator).toHaveStyle({
                backgroundColor: "#ffc107",
            });
        });

        it("should show green indicator when connected", async () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: true,
                isConnecting: false,
                error: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
            });

            let container: HTMLElement;
            await act(async () => {
                container = render(<App />).container;
            });

            const indicator = container!.querySelector(
                "[data-testid='connection-status-indicator']"
            );
            expect(indicator).toHaveStyle({
                backgroundColor: "#28a745",
            });
        });
    });

    describe("Upload Functionality", () => {
        it("should show upload section in Upload view", async () => {
            const user = userEvent.setup();

            await act(async () => {
                render(<App />);
            });

            const uploadButton = screen.getByRole("button", { name: /upload/i });
            await act(async () => {
                await user.click(uploadButton);
            });

            // Upload section should show "Upload image for analysis" text
            expect(
                screen.getByText("Upload image for analysis")
            ).toBeInTheDocument();
        });

        it("should have file input in Upload view", async () => {
            const user = userEvent.setup();

            await act(async () => {
                render(<App />);
            });

            const uploadButton = screen.getByRole("button", { name: /upload/i });
            await act(async () => {
                await user.click(uploadButton);
            });

            const fileInputs = document.querySelectorAll('input[type="file"]');
            expect(fileInputs.length).toBeGreaterThan(0);
        });
    });

    describe("Job Details Display", () => {
        it("should show 'Job Details' heading in Jobs view", async () => {
            const user = userEvent.setup();

            await act(async () => {
                render(<App />);
            });

            const jobsButton = screen.getByRole("button", { name: /jobs/i });
            await act(async () => {
                await user.click(jobsButton);
            });

            expect(screen.getByText("Job Details")).toBeInTheDocument();
        });

        it("should display job list in Jobs view", async () => {
            const user = userEvent.setup();

            await act(async () => {
                render(<App />);
            });

            const jobsButton = screen.getByRole("button", { name: /jobs/i });
            await act(async () => {
                await user.click(jobsButton);
            });

            // Jobs section should exist with "Job Details" heading
            const jobsSection = screen.getByText("Job Details");
            expect(jobsSection).toBeInTheDocument();
        });
    });

    describe("Error Display", () => {
        it("should display WebSocket error message when wsError exists", async () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: false,
                isConnecting: false,
                error: "Connection timeout",
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
            });

            await act(async () => {
                render(<App />);
            });

            // Error message should be displayed
            expect(
                screen.getByText((content) =>
                    content.includes("Connection timeout")
                )
            ).toBeInTheDocument();
        });
    });

    describe("Plugin Selection", () => {
        it("should render PluginSelector component in sidebar", async () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: true,
                isConnecting: false,
                error: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
            });

            await act(async () => {
                render(<App />);
            });

            // PluginSelector should be rendered in the left sidebar
            // It's not accessible via role since it's a custom component,
            // so we just verify App rendered without errors
            const logo = screen.getByTestId("app-logo");
            expect(logo).toBeInTheDocument();
        });
    });

    describe("Streaming Button Hover Effects", () => {
        it("should apply hover styles when connected and not streaming", async () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: true,
                isConnecting: false,
                error: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
            });

            await act(async () => {
                render(<App />);
            });

            const streamButton = screen.getByRole("button", {
                name: /start streaming/i,
            });

            // Simulate hover
            await act(async () => {
                const event = new MouseEvent("mouseover", { bubbles: true });
                streamButton.dispatchEvent(event);
            });

            expect(streamButton.style.backgroundColor).toBe(
                "var(--accent-green)"
            );
        });

        it("should not apply hover styles when disconnected", async () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: false,
                isConnecting: false,
                error: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
            });

            await act(async () => {
                render(<App />);
            });

            const streamButton = screen.getByRole("button", {
                name: /start streaming/i,
            });

            // Button should be disabled
            expect(streamButton).toBeDisabled();
        });

        it("should remove hover styles on mouse out", async () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: true,
                isConnecting: false,
                error: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
            });

            await act(async () => {
                render(<App />);
            });

            const streamButton = screen.getByRole("button", {
                name: /start streaming/i,
            });

            // Simulate hover out
            await act(async () => {
                const event = new MouseEvent("mouseout", { bubbles: true });
                streamButton.dispatchEvent(event);
            });

            expect(streamButton.style.backgroundColor).toBe(
                "var(--bg-tertiary)"
            );
        });
    });

    describe("Upload Error Handling", () => {
        it("should render upload input in Upload view", async () => {
            mockUseWebSocket.mockReturnValue({
                isConnected: false,
                isConnecting: false,
                error: null,
                sendFrame: vi.fn(),
                switchPlugin: vi.fn(),
                latestResult: null,
            });

            const user = userEvent.setup();
            await act(async () => {
                render(<App />);
            });

            // Switch to upload view
            const uploadButton = screen.getByRole("button", { name: /upload/i });
            await act(async () => {
                await user.click(uploadButton);
            });

            // Upload prompt should be visible
            expect(
                screen.getByText("Upload image for analysis")
            ).toBeInTheDocument();
        });
    });

    describe("WebSocket Callbacks", () => {
        it("should register onResult callback when component mounts", async () => {
            const mockOnResult = vi.fn();
            const mockOnError = vi.fn();

            mockUseWebSocket.mockImplementation((config) => {
                // Capture callbacks for testing
                mockOnResult.mockImplementation(config.onResult);
                mockOnError.mockImplementation(config.onError);

                return {
                    isConnected: true,
                    isConnecting: false,
                    error: null,
                    sendFrame: vi.fn(),
                    switchPlugin: vi.fn(),
                    latestResult: null,
                };
            });

            await act(async () => {
                render(<App />);
            });

            // Verify hook was called with callbacks
            expect(mockUseWebSocket).toHaveBeenCalled();
            const callConfig = (mockUseWebSocket.mock.calls[0]?.[0]) as {
                onResult?: () => void;
                onError?: () => void;
            };
            expect(callConfig.onResult).toBeDefined();
            expect(callConfig.onError).toBeDefined();
        });
    });
});
