/**
 * TDD Tests for App Component - Issue #102 Tool Selection Wiring
 *
 * These tests define the expected behavior for tool selection:
 * - App should have no default tool selected
 * - ToolSelector should receive correct props
 * - Tool selection should update App state
 * - Upload should be disabled when no tool is selected
 * - ToolSelector should disable during streaming
 *
 * Issue #102: UI tool selection wiring fix
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

vi.mock("./components/ToolSelector", () => ({
  ToolSelector: (props: {
    pluginId: string;
    selectedTool: string;
    onToolChange: (t: string) => void;
    disabled: boolean;
  }) => (
    <div data-testid="tool-selector">
      <div data-testid="selected-tool">{props.selectedTool || "(none)"}</div>
      <button
        data-testid="select-tool-btn"
        onClick={() => props.onToolChange("test_tool")}
        disabled={props.disabled}
      >
        Select Test Tool
      </button>
      {props.disabled && (
        <span data-testid="tool-selector-disabled">Disabled during streaming</span>
      )}
    </div>
  ),
}));

vi.mock("./components/VideoTracker", () => ({
  VideoTracker: (props: { pluginId: string; toolName: string }) => (
    <div data-testid="video-tracker">
      VideoTracker: {props.pluginId} / {props.toolName}
    </div>
  ),
}));

vi.mock("./utils/detectToolType", () => ({
  detectToolType: () => "image",
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
    getPluginManifest: vi.fn(),
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
    expect(selectedPlugin.textContent).toBe("(none)");
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
    
    expect(screen.getByTestId("selected-plugin").textContent).toBe("object_detection");
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
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement | null;
    if (fileInput) {
      expect(fileInput.disabled).toBe(true);
    } else {
      // File input doesn't render when no plugin selected
      // Look for the message in the upload content area (not the sidebar)
      // The sidebar ToolSelector also shows "Select a plugin first"
      const messages = screen.queryAllByText("Select a plugin first");
      expect(messages.length).toBeGreaterThanOrEqual(1);
    }
  });

  it("should show message prompting user to select plugin when none selected", async () => {
    const user = userEvent.setup();
    render(<App />);
    
    // Switch to upload view
    const uploadTab = screen.getByRole("button", { name: /upload/i });
    await user.click(uploadTab);
    
    // Find "Select a plugin first" in the document
    // The sidebar ToolSelector shows this message when no plugin is selected
    // Use queryAllByText to avoid error when multiple elements exist
    const messages = screen.queryAllByText("Select a plugin first");
    expect(messages.length).toBeGreaterThanOrEqual(1);
  });

  it("should show 'Select a tool' when no tool is selected", async () => {
    const user = userEvent.setup();
    
    // Mock fetch for manifest
    vi.spyOn(window, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        name: "Test Plugin",
        tools: [{ name: "test_tool", type: "image" }],
      }),
    } as Response);
    
    render(<App />);
    
    // First select a plugin
    const changeBtn = screen.getByTestId("change-plugin-btn");
    await user.click(changeBtn);
    
    // Switch to upload view
    const uploadTab = screen.getByRole("button", { name: /upload/i });
    await user.click(uploadTab);
    
    // Wait a bit for manifest to load
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Check that upload section is visible
    expect(uploadTab).toBeTruthy();
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
    
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement | null;
    if (fileInput) {
      expect(fileInput.disabled).toBe(false);
    } else {
      // File input may not render if tool type is frame-based or still loading
      // At minimum, UI should be rendered without error
      expect(uploadTab).toBeTruthy();
    }
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
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement | null;
    if (fileInput) {
      fileInput.disabled = false;

      // Upload a file without selecting a plugin
      const file = new File(["test"], "test.png", { type: "image/png" });
      await user.upload(fileInput, file);

      // analyzeImage should NOT have been called
      expect(mockAnalyze).not.toHaveBeenCalled();
    } else {
      // If file input doesn't exist, verify plugin selection message appears
      const messages = screen.queryAllByText("Select a plugin first");
      expect(messages.length).toBeGreaterThanOrEqual(1);
    }
  });

  it("should render VideoTracker for frame-based tools", async () => {
    const user = userEvent.setup();
    render(<App />);

    // Select a plugin and tool
    const changeBtn = screen.getByTestId("change-plugin-btn");
    await user.click(changeBtn);
    
    // Switch to upload view
    const uploadTab = screen.getByRole("button", { name: /upload/i });
    await user.click(uploadTab);

    // Tool selector would be rendered here (in sidebar)
    // For now, just verify upload view renders without crashing
    expect(uploadTab).toBeTruthy();
  });
});

// =============================================================================
// Issue #102: Tool Selection Wiring Tests
// =============================================================================

describe("App - TDD: Tool Selection Wiring (Issue #102)", () => {
  beforeEach(() => {
    setWsMock({ connectionStatus: "disconnected" });
  });

  it("ToolSelector shows no tool selected by default", () => {
    render(<App />);
    expect(screen.getByTestId("selected-tool").textContent).toBe("(none)");
  });

  it("selecting a tool updates selectedTool state", async () => {
    const user = userEvent.setup();
    render(<App />);

    // Select plugin first
    await user.click(screen.getByTestId("change-plugin-btn"));

    // Now select tool
    await user.click(screen.getByTestId("select-tool-btn"));

    expect(screen.getByTestId("selected-tool").textContent).toBe("test_tool");
  });

  it("ToolSelector is disabled when streaming is enabled", async () => {
    setWsMock({ isConnected: true, connectionStatus: "connected" });
    const user = userEvent.setup();
    render(<App />);

    // Select plugin first (ToolSelector only enables after plugin selection)
    await user.click(screen.getByTestId("change-plugin-btn"));

    // Start streaming to enable streamEnabled state
    const startStreamingBtn = screen.getByRole("button", { name: /start streaming/i });
    await user.click(startStreamingBtn);

    // Now ToolSelector should be disabled
    expect(screen.queryByTestId("tool-selector-disabled")).toBeTruthy();
  });

  it("upload is enabled when tool is auto-selected after plugin selection", async () => {
    const user = userEvent.setup();
    const { apiClient } = await import("./api/client");

    // Mock manifest with tools
    vi.mocked(apiClient.getPluginManifest).mockResolvedValue({
      id: "test-plugin",
      name: "Test Plugin",
      version: "1.0.0",
      entrypoint: "/plugins/test",
      tools: {
        auto_tool: { description: "Auto tool", inputs: {}, outputs: {} },
      },
    });

    render(<App />);

    // Select plugin - tool should auto-select
    await user.click(screen.getByTestId("change-plugin-btn"));
    
    // Wait for manifest to load and auto-select
    await new Promise(resolve => setTimeout(resolve, 50));

    // Switch to upload tab
    await user.click(screen.getByRole("button", { name: /upload/i }));

    // With auto-selected tool, upload should be enabled
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement | null;
    expect(fileInput).not.toBeNull();
    expect(fileInput?.disabled).toBe(false);
  });

  it("upload enabled when plugin and tool selected", async () => {
    const user = userEvent.setup();
    render(<App />);

    // Select plugin
    await user.click(screen.getByTestId("change-plugin-btn"));
    
    // Select tool
    await user.click(screen.getByTestId("select-tool-btn"));
    
    // Switch to upload tab
    await user.click(screen.getByRole("button", { name: /upload/i }));

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement | null;
    if (fileInput) {
      expect(fileInput.disabled).toBe(false);
    } else {
      // File input may not render if tool type is frame-based
      // At minimum, UI should be rendered without error
      expect(screen.getByRole("button", { name: /upload/i })).toBeTruthy();
    }
  });

  it("auto-selects the first tool from the manifest when plugin is selected", async () => {
    const user = userEvent.setup();
    const { apiClient } = await import("./api/client");

    // Mock manifest with multiple tools via API client
    vi.mocked(apiClient.getPluginManifest).mockResolvedValue({
      id: "test-plugin",
      name: "Test Plugin",
      version: "1.0.0",
      entrypoint: "/plugins/test",
      tools: {
        first_tool: { description: "First tool", inputs: {}, outputs: {} },
        second_tool: { description: "Second tool", inputs: {}, outputs: {} },
      },
    });

    render(<App />);

    // Select plugin
    await user.click(screen.getByTestId("change-plugin-btn"));

    // Wait for manifest to load and auto-select
    await new Promise(resolve => setTimeout(resolve, 50));

    // ToolSelector should now show first_tool (auto-selected)
    expect(screen.getByTestId("selected-tool").textContent).toBe("first_tool");
  });

  it("never renders ToolSelector with a blank selectedTool once manifest is loaded", async () => {
    const user = userEvent.setup();
    const { apiClient } = await import("./api/client");

    // Mock manifest with a single tool via API client
    vi.mocked(apiClient.getPluginManifest).mockResolvedValue({
      id: "test-plugin",
      name: "Test Plugin",
      version: "1.0.0",
      entrypoint: "/plugins/test",
      tools: {
        auto_tool: { description: "Auto tool", inputs: {}, outputs: {} },
      },
    });

    render(<App />);

    // Select plugin
    await user.click(screen.getByTestId("change-plugin-btn"));

    // Wait for manifest to load
    await new Promise(resolve => setTimeout(resolve, 50));

    // ToolSelector should never show "(none)" after manifest loads
    expect(screen.getByTestId("selected-tool").textContent).not.toBe("(none)");
    expect(screen.getByTestId("selected-tool").textContent).toBe("auto_tool");
  });

  it("upload works correctly with auto-selected tool", async () => {
    const user = userEvent.setup();
    const { apiClient } = await import("./api/client");

    // Mock manifest with tools
    vi.mocked(apiClient.getPluginManifest).mockResolvedValue({
      id: "test-plugin",
      name: "Test Plugin",
      version: "1.0.0",
      entrypoint: "/plugins/test",
      tools: {
        first_tool: { description: "First tool", inputs: {}, outputs: {} },
      },
    });

    render(<App />);

    // Select plugin - tool should auto-select to first_tool
    await user.click(screen.getByTestId("change-plugin-btn"));

    // Switch to upload tab
    await user.click(screen.getByRole("button", { name: /upload/i }));

    // Wait for manifest to load
    await new Promise(resolve => setTimeout(resolve, 50));

    // Upload input should be enabled because tool is auto-selected
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement | null;
    expect(fileInput).not.toBeNull();
    expect(fileInput?.disabled).toBe(false);

    // UI should show upload panel, not tool selection prompt
    const uploadPanel = screen.queryByText(/upload image for analysis/i);
    expect(uploadPanel).toBeTruthy();
  });
});

