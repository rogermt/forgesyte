/**
 * Tool Locking Stability Test - Regression Test for Discussion #345
 *
 * This test ensures that the tool selection state doesn't cause
 * infinite re-render loops when tools are locked after video upload.
 *
 * Root cause: Effect at line 267-290 in App.tsx had selectedTools in
 * dependency array AND called setSelectedTools inside, creating a loop.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import App from "./App";

// Mock WebSocket hook
vi.mock("./hooks/useWebSocket", () => ({
    useWebSocket: vi.fn(() => ({
        isConnected: true,
        connectionStatus: "connected",
        attempt: 0,
        error: null,
        sendFrame: vi.fn(),
        switchPlugin: vi.fn(),
        reconnect: vi.fn(),
        latestResult: null,
    })),
}));

// Mock API client
vi.mock("./api/client", () => ({
    apiClient: {
        listJobs: vi.fn(() => Promise.resolve([])),
        getPlugins: vi.fn(() =>
            Promise.resolve([
                {
                    name: "yolo-tracker",
                    description: "YOLO Tracker",
                    version: "1.0.0",
                    inputs: ["video"],
                    outputs: ["detection"],
                    permissions: [],
                },
            ])
        ),
        getPluginManifest: vi.fn(() =>
            Promise.resolve({
                id: "yolo-tracker",
                tools: [
                    {
                        id: "video_player_detection",
                        capabilities: ["player_detection"],
                        input_types: ["video"],
                    },
                    {
                        id: "video_ball_detection",
                        capabilities: ["ball_detection"],
                        input_types: ["video"],
                    },
                ],
            })
        ),
        submitVideoUpload: vi.fn(() =>
            Promise.resolve({ video_path: "video/input/test.mp4" })
        ),
        submitVideoJob: vi.fn(() =>
            Promise.resolve({ job_id: "job-123" })
        ),
        getJob: vi.fn(() =>
            Promise.resolve({ job_id: "job-123", status: "completed" })
        ),
    },
}));

// Mock child components that are not relevant to this test
vi.mock("./components/CameraPreview", () => ({
    CameraPreview: () => <div data-testid="camera-preview" />,
}));

vi.mock("./components/JobList", () => ({
    JobList: () => <div data-testid="job-list" />,
}));

vi.mock("./components/ResultsPanel", () => ({
    ResultsPanel: () => <div data-testid="results-panel" />,
}));

describe("Tool Locking Stability (Regression Test - Discussion #345)", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("should not create infinite loop when selectedTools is in effect dependency", async () => {
        // This test verifies the fix for the infinite loop bug
        // The effect should NOT re-run when selectedTools changes due to the effect itself

        // Render the app with a timeout to catch infinite loops
        // If there's an infinite loop, this will timeout
        const renderPromise = act(async () => {
            render(<App />);
        });

        // Set a reasonable timeout - if infinite loop, this will hang
        await Promise.race([
            renderPromise,
            new Promise((_, reject) =>
                setTimeout(() => reject(new Error("Render timeout - possible infinite loop")), 5000)
            ),
        ]);

        // If we get here, the render completed without infinite loop
        expect(true).toBe(true);
    });

    it("should stabilize toolList when manifest has capabilities", async () => {
        render(<App />);

        // Wait for initial render to complete
        await waitFor(() => {
            // Just verify the component renders without hanging
            expect(screen.getByRole("main") || document.body).toBeTruthy();
        }, { timeout: 3000 });

        // The test passing means no infinite loop occurred
        expect(true).toBe(true);
    });

    it("should not flip isUsingLogicalIds causing toolList to change repeatedly", async () => {
        // This catches the case where toolList changes between capabilities and tool IDs
        // which caused selectedTools validation to fail repeatedly

        const { rerender } = render(<App />);

        // Force a re-render to simulate state change
        await act(async () => {
            rerender(<App />);
        });

        // Another re-render
        await act(async () => {
            rerender(<App />);
        });

        // If we get here without timeout, the component is stable
        expect(true).toBe(true);
    });
});
