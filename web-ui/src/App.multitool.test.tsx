/**
 * Multitool Selection Tests - REAL tests
 *
 * These tests test the ACTUAL App behavior:
 * - selectedTools should contain capabilities after selection
 * - If toolList returns tool IDs, auto-select will reset selectedTools
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import * as React from "react";

// ---------------------------------------------------------------------------
// Mocks - only external dependencies, NOT ToolSelector
// ---------------------------------------------------------------------------

vi.mock("./components/CameraPreview", () => ({
  CameraPreview: () => <div data-testid="camera-preview" />,
}));

vi.mock("./components/PluginSelector", () => ({
  PluginSelector: (props: { selectedPlugin: string; onPluginChange: (p: string) => void }) => (
    <div data-testid="plugin-selector">
      <span data-testid="selected-plugin">{props.selectedPlugin}</span>
      <button data-testid="select-yolo" onClick={() => props.onPluginChange("yolo-tracker")}>
        Select YOLO
      </button>
    </div>
  ),
}));

vi.mock("./components/JobList", () => ({ JobList: () => <div data-testid="job-list" /> }));
vi.mock("./components/ResultsPanel", () => ({ ResultsPanel: () => <div data-testid="results-panel" /> }));
vi.mock("./components/JobStatus", () => ({ JobStatus: () => <div data-testid="job-status" /> }));
vi.mock("./components/VideoTracker", () => ({ VideoTracker: () => <div data-testid="video-tracker" /> }));
vi.mock("./components/VideoUpload", () => ({ VideoUpload: () => <div data-testid="video-upload" /> }));

// Mock apiClient with REAL manifest structure
vi.mock("./api/client", () => ({
  apiClient: {
    submitImage: vi.fn(() => Promise.resolve({ job_id: "test-job" })),
    submitVideoJob: vi.fn(),
    getJob: vi.fn(),
    pollJob: vi.fn(() => Promise.resolve({ job_id: "test-job", status: "completed" })),
    // REAL manifest: tool ID != capability name
    getPluginManifest: vi.fn((pluginId: string) => {
      if (pluginId === "yolo-tracker") {
        return Promise.resolve({
          id: "yolo-tracker",
          name: "YOLO Tracker",
          version: "1.0.0",
          tools: {
            // Tool ID: video_player_detection
            // Capability: player_detection (DIFFERENT!)
            video_player_detection: {
              capabilities: ["player_detection"],
              input_types: ["video"],
            },
            video_ball_detection: {
              capabilities: ["ball_detection"],
              input_types: ["video"],
            },
          },
        });
      }
      return Promise.resolve({ id: pluginId, tools: {} });
    }),
  },
}));

vi.mock("./hooks/useWebSocket", () => ({
  useWebSocket: vi.fn(() => ({
    isConnected: false,
    connectionStatus: "disconnected",
    attempt: 0,
    error: null,
    sendFrame: vi.fn(),
    switchPlugin: vi.fn(),
    reconnect: vi.fn(),
    latestResult: null,
  })),
}));

// Import App AFTER mocks are set up
// Note: NOT mocking ToolSelector - using REAL component
import App from "./App";

// ---------------------------------------------------------------------------
// REAL tests - test actual App behavior
// ---------------------------------------------------------------------------

describe("Multitool Selection - REAL tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("App's toolList should return capabilities so auto-select doesn't reset", async () => {
    render(<App />);

    // Select YOLO plugin
    await userEvent.click(screen.getByTestId("select-yolo"));

    // Wait for tool buttons to appear
    await waitFor(() => {
      const buttons = screen.getAllByRole("button");
      expect(buttons.length).toBeGreaterThan(5);
    }, { timeout: 5000 });

    // Find tool buttons (Player Detection, Ball Detection)
    const allButtons = screen.getAllByRole("button");
    const toolButtons = allButtons.filter(b => {
      const text = b.textContent?.toLowerCase() || "";
      return text.includes("player") || text.includes("ball");
    });

    expect(toolButtons.length).toBeGreaterThan(0);
    
    // Click the first tool button (Player Detection)
    await userEvent.click(toolButtons[0]);

    // Check: is the button selected (aria-pressed=true)?
    // With FIXED code: toolList returns capabilities, auto-select keeps capability
    // -> selectedTools = ["player_detection"], matches button -> aria-pressed=true
    // With BROKEN code: toolList returns tool IDs, auto-select resets to tool ID
    // -> selectedTools = ["video_player_detection"], doesn't match button -> aria-pressed=false
    
    await waitFor(() => {
      // Check if the clicked button has aria-pressed="true"
      const button = toolButtons[0];
      expect(button.getAttribute("aria-pressed")).toBe("true");
    }, { timeout: 3000 });
  });
});
