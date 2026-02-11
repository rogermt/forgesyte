/**
 * Integration tests for App.tsx - WebSocket streaming and connection states
 * Consolidated from App.test.tsx and App.integration.test.tsx
 */

import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";
import * as useWebSocketModule from "./hooks/useWebSocket";
import type { MockReturn } from "./__mocks__/useWebSocketMock";

// ---------------------------------------------------------------------------
// Mock dependencies
// ---------------------------------------------------------------------------

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
    getPluginManifest: vi.fn(() => Promise.resolve(null)),
  },
}));

vi.mock("./components/CameraPreview", () => ({
  CameraPreview: (props: { enabled: boolean; onFrame: (data: string) => void }) => (
    <div data-testid="camera-preview">
      <div data-testid="camera-preview-text">{props.enabled ? "Streaming" : "Not streaming"}</div>
      <button
        data-testid="emit-frame"
        onClick={() => props.onFrame("base64imagedata")}
      >
        Emit Frame
      </button>
    </div>
  ),
}));

vi.mock("./components/PluginSelector", () => ({
  PluginSelector: (props: {
    selectedPlugin: string;
    onPluginChange: (p: string) => void;
    disabled: boolean;
  }) => (
    <div data-testid="plugin-selector">
      <div>Selected: {props.selectedPlugin}</div>
      <button
        onClick={() => props.onPluginChange("object_detection")}
        disabled={props.disabled}
      >
        Select Object Detection
      </button>
    </div>
  ),
}));

vi.mock("./components/JobList", () => ({
  JobList: () => <div data-testid="job-list">JobList</div>,
}));

vi.mock("./components/ResultsPanel", () => ({
  ResultsPanel: () => <div data-testid="results-panel">ResultsPanel</div>,
}));

// ---------------------------------------------------------------------------
// Test Setup
// ---------------------------------------------------------------------------

const mockUseWebSocket = vi.mocked(useWebSocketModule.useWebSocket);

// Default mock values
const defaultMockValues: MockReturn = {
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
};

function setupWebSocketMock(overrides: Partial<MockReturn> = {}) {
  mockUseWebSocket.mockReturnValue({ ...defaultMockValues, ...overrides } as unknown as ReturnType<typeof useWebSocketModule.useWebSocket>);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("App - WebSocket Connection States", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupWebSocketMock({ connectionStatus: "disconnected" });
  });

  it("shows disconnected status initially", async () => {
    await act(async () => {
      render(<App />);
    });

    expect(screen.getByTestId("connection-status-text")).toHaveTextContent("Disconnected");
  });

  it("shows 'Connecting...' text and yellow indicator when connecting", () => {
    setupWebSocketMock({
      connectionStatus: "connecting",
      isConnecting: true,
      isConnected: false,
    });

    render(<App />);

    expect(screen.getByTestId("connection-status-text")).toHaveTextContent("Connecting...");
    expect(screen.getByTestId("connection-status-indicator")).toHaveStyle({
      backgroundColor: "#ffc107",
    });
  });

  it("shows 'Connected' text and green indicator when connected", () => {
    setupWebSocketMock({
      connectionStatus: "connected",
      isConnected: true,
      isConnecting: false,
    });

    render(<App />);

    expect(screen.getByTestId("connection-status-text")).toHaveTextContent("Connected");
    expect(screen.getByTestId("connection-status-indicator")).toHaveStyle({
      backgroundColor: "#28a745",
    });
  });

  it("shows 'Reconnecting... (attempt N)' text and orange indicator when reconnecting", () => {
    setupWebSocketMock({
      connectionStatus: "reconnecting",
      isConnecting: true,
      attempt: 3,
    });

    render(<App />);

    expect(screen.getByTestId("connection-status-text")).toHaveTextContent(
      "Reconnecting... (attempt 3)"
    );
    expect(screen.getByTestId("connection-status-indicator")).toHaveStyle({
      backgroundColor: "#fd7e14",
    });
  });

  it("shows WebSocket error when present", () => {
    setupWebSocketMock({
      connectionStatus: "failed",
      error: "Unable to establish a stable WebSocket connection",
    });

    render(<App />);

    expect(screen.getByTestId("ws-error-box")).toHaveTextContent("WebSocket Error:");
    expect(screen.getByTestId("ws-error-box")).toHaveTextContent(
      "Unable to establish a stable WebSocket connection"
    );
  });

  it("shows Reconnect button when failed and calls reconnect()", async () => {
    const user = userEvent.setup();
    const reconnectFn = vi.fn();

    setupWebSocketMock({
      connectionStatus: "failed",
      error: "Max retries",
      reconnect: reconnectFn,
    });

    render(<App />);

    await user.click(screen.getByRole("button", { name: /reconnect/i }));
    expect(reconnectFn).toHaveBeenCalledTimes(1);
  });
});

describe("App - Streaming Controls", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupWebSocketMock({ connectionStatus: "disconnected" });
  });

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
      expect(screen.getByTestId("camera-preview")).toBeInTheDocument();
    });
  });

  it("disables Start Streaming button when not connected", () => {
    setupWebSocketMock({
      connectionStatus: "disconnected",
      isConnected: false,
    });

    render(<App />);

    expect(screen.getByRole("button", { name: /start streaming/i })).toBeDisabled();
  });

  it("enables Start Streaming button when connected and toggles to Stop Streaming", async () => {
    const user = userEvent.setup();

    setupWebSocketMock({
      connectionStatus: "connected",
      isConnected: true,
    });

    render(<App />);

    const startBtn = screen.getByRole("button", { name: /start streaming/i });
    expect(startBtn).not.toBeDisabled();

    await user.click(startBtn);
    expect(screen.getByRole("button", { name: /stop streaming/i })).toBeInTheDocument();
  });

  it("should call useWebSocket on mount with empty plugin", async () => {
    await act(async () => {
      render(<App />);
    });

    expect(mockUseWebSocket).toHaveBeenCalledWith(
      expect.objectContaining({
        plugin: "",
      })
    );
  });
});

describe("App - Results Display", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupWebSocketMock({ connectionStatus: "disconnected" });
  });

  it("should show ResultsPanel in stream mode", async () => {
    await act(async () => {
      render(<App />);
    });

    await waitFor(() => {
      expect(screen.getByTestId("results-panel")).toBeInTheDocument();
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
    } as unknown as ReturnType<typeof useWebSocketModule.useWebSocket>);

    await act(async () => {
      render(<App />);
    });

    // ResultsPanel should be present with the mock data
    expect(screen.getByTestId("results-panel")).toBeInTheDocument();
  });
});

describe("App - Plugin Selector Interaction", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupWebSocketMock({ connectionStatus: "disconnected" });
  });

  it.skip("should disable plugin selector when streaming enabled", async () => {
    // APPROVED: Skipped intentionally. Requires plugin_selector plugin to be synced to public/forgesyte-plugins
    // This test passes in local dev with plugins synced, but fails in CI
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

describe("App - Frame Handling", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupWebSocketMock({ connectionStatus: "connected", isConnected: true });
  });

  it("should pass correct handlers to CameraPreview", async () => {
    await act(async () => {
      render(<App />);
    });

    await waitFor(() => {
      expect(screen.getByTestId("camera-preview")).toBeInTheDocument();
    });
  });
});

