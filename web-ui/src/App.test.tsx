import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";

// ---- Mock child components to avoid browser camera APIs etc.
vi.mock("./components/CameraPreview", () => ({
  CameraPreview: (props: { enabled: boolean; onFrame: (data: string) => void }) => (
    <div data-testid="camera-preview">
      <div>{props.enabled ? "Streaming" : "Not streaming"}</div>
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

// ---- Mock API client
vi.mock("./api/client", () => ({
  apiClient: {
    analyzeImage: vi.fn(),
    pollJob: vi.fn(),
    getPluginManifest: vi.fn(),
  },
}));

// ---- Mock useWebSocket hook
vi.mock("./hooks/useWebSocket", () => ({
  useWebSocket: vi.fn(),
}));

import { useWebSocket } from "./hooks/useWebSocket";

type MockReturn = {
  isConnected: boolean;
  isConnecting: boolean;
  connectionStatus: "idle" | "connecting" | "connected" | "reconnecting" | "disconnected" | "failed";
  attempt: number;
  error: string | null;
  errorInfo: Record<string, unknown> | null;
  sendFrame: ReturnType<typeof vi.fn>;
  switchPlugin: ReturnType<typeof vi.fn>;
  disconnect: ReturnType<typeof vi.fn>;
  reconnect: ReturnType<typeof vi.fn>;
  latestResult: Record<string, unknown> | null;
  stats: { framesProcessed: number; avgProcessingTime: number };
};

const mockUseWebSocket = vi.mocked(useWebSocket);

function setWsMock(overrides: Partial<MockReturn> = {}) {
  const base: MockReturn = {
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

  mockUseWebSocket.mockReturnValue({ ...base, ...overrides } as unknown as ReturnType<typeof useWebSocket>);
}

describe("App (updated for unified WebSocket status)", () => {
  beforeEach(() => {
    setWsMock({ connectionStatus: "disconnected" });
  });

  it("shows ForgeSyte logo", () => {
    render(<App />);
    expect(screen.getByTestId("app-logo")).toBeInTheDocument();
  });

  it("shows 'Connecting...' text and yellow indicator when connecting", () => {
    setWsMock({
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

  it("shows 'Reconnecting... (attempt N)' text and orange indicator when reconnecting", () => {
    setWsMock({
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

  it("shows 'Connected' text and green indicator when connected", () => {
    setWsMock({
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

  it("disables Start Streaming button when not connected", () => {
    setWsMock({
      connectionStatus: "disconnected",
      isConnected: false,
    });

    render(<App />);

    expect(screen.getByRole("button", { name: /start streaming/i })).toBeDisabled();
  });

  it("enables Start Streaming button when connected and toggles to Stop Streaming", async () => {
    const user = userEvent.setup();

    setWsMock({
      connectionStatus: "connected",
      isConnected: true,
    });

    render(<App />);

    const startBtn = screen.getByRole("button", { name: /start streaming/i });
    expect(startBtn).not.toBeDisabled();

    await user.click(startBtn);
    expect(screen.getByRole("button", { name: /stop streaming/i })).toBeInTheDocument();
  });

  it("shows WebSocket error banner when wsError exists", () => {
    setWsMock({
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

    setWsMock({
      connectionStatus: "failed",
      error: "Max retries",
      reconnect: reconnectFn,
    });

    render(<App />);

    await user.click(screen.getByRole("button", { name: /reconnect/i }));
    expect(reconnectFn).toHaveBeenCalledTimes(1);
  });
});