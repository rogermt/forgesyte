/**
 * TDD Tests for App Component - Empty Plugin Handling
 *
 * These tests define the expected behavior:
 * - App should have no default plugin selected
 * - WebSocket should handle empty plugin gracefully
 * - UI should handle empty plugin list from server
 */

import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";

// Mock child components
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
      <div data-testid="selected-plugin">{props.selectedPlugin || "(none)"}</div>
      <button
        data-testid="change-plugin-btn"
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

vi.mock("./api/client", () => ({
  apiClient: {
    analyzeImage: vi.fn(),
    pollJob: vi.fn(),
  },
}));

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

describe("App - TDD: Empty Plugin Default", () => {
  beforeEach(() => {
    setWsMock({ connectionStatus: "disconnected" });
  });

  it("should have no plugin selected by default (empty string)", () => {
    render(<App />);
    
    const selectedPlugin = screen.getByTestId("selected-plugin");
    expect(selectedPlugin).toHaveTextContent("(none)");
  });

  it("should pass empty plugin to useWebSocket when no plugin selected", () => {
    render(<App />);
    
    expect(mockUseWebSocket).toHaveBeenCalledWith(
      expect.objectContaining({
        plugin: "",
      })
    );
  });

  it("should allow user to select a plugin", async () => {
    const user = userEvent.setup();
    
    render(<App />);
    
    const changeBtn = screen.getByTestId("change-plugin-btn");
    await user.click(changeBtn);
    
    expect(screen.getByTestId("selected-plugin")).toHaveTextContent("object_detection");
  });
});

describe("App - TDD: Upload requires plugin selection", () => {
  beforeEach(() => {
    setWsMock({ connectionStatus: "connected", isConnected: true });
  });

  it("should disable file upload input when no plugin is selected", async () => {
    const user = userEvent.setup();
    render(<App />);
    
    // Switch to upload view
    const uploadTab = screen.getByRole("button", { name: /upload/i });
    await user.click(uploadTab);
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(fileInput).toBeDisabled();
  });

  it("should show message prompting user to select plugin when none selected", async () => {
    const user = userEvent.setup();
    render(<App />);
    
    // Switch to upload view
    const uploadTab = screen.getByRole("button", { name: /upload/i });
    await user.click(uploadTab);
    
    expect(screen.getByText(/select a plugin/i)).toBeInTheDocument();
  });

  it("should enable file upload when a plugin is selected", async () => {
    const user = userEvent.setup();
    
    render(<App />);
    
    // First select a plugin
    const changeBtn = screen.getByTestId("change-plugin-btn");
    await user.click(changeBtn);
    
    // Switch to upload view
    const uploadTab = screen.getByRole("button", { name: /upload/i });
    await user.click(uploadTab);
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(fileInput).not.toBeDisabled();
  });

  it("should not call analyzeImage if no plugin is selected", async () => {
    const { apiClient } = await import("./api/client");
    const mockAnalyze = vi.mocked(apiClient.analyzeImage);
    mockAnalyze.mockClear();

    const user = userEvent.setup();
    render(<App />);

    // Switch to upload view
    const uploadTab = screen.getByRole("button", { name: /upload/i });
    await user.click(uploadTab);

    // Force-enable the input to simulate edge case (e.g., race condition)
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    fileInput.disabled = false;

    // Upload a file without selecting a plugin
    const file = new File(["test"], "test.png", { type: "image/png" });
    await user.upload(fileInput, file);

    // analyzeImage should NOT have been called
    expect(mockAnalyze).not.toHaveBeenCalled();
  });
});
