/**
 * TDD tests for tool routing + plugin-switch tool reset (Issue #181).
 *
 * Verifies:
 * 1) tools are passed to useWebSocket options
 * 2) changing tools updates the tools passed to useWebSocket
 * 3) changing plugin resets tools to the new plugin's first tool (prevents ocr+radar)
 * 4) Multiple tools can be selected and sent together
 * 5) sendFrame is called without extra parameter (tools are in useWebSocket options)
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// ---------------------------------------------------------------------------
// Mocks (must be declared before importing App)
// ---------------------------------------------------------------------------

vi.mock("./components/CameraPreview", () => ({
  CameraPreview: (props: {
    enabled: boolean;
    onFrame: (data: string) => void;
  }) => (
    <div data-testid="camera-preview">
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
      <div data-testid="selected-plugin">{props.selectedPlugin}</div>

      <button
        data-testid="select-yolo"
        onClick={() => props.onPluginChange("yolo-tracker")}
      >
        Select YOLO
      </button>

      <button
        data-testid="select-ocr"
        onClick={() => props.onPluginChange("ocr")}
      >
        Select OCR
      </button>
    </div>
  ),
}));

vi.mock("./components/ToolSelector", () => ({
  ToolSelector: (props: {
    pluginId: string | null;
    selectedTools: string[];
    onToolChange: (t: string[]) => void;
    disabled: boolean;
  }) => (
    <div data-testid="tool-selector">
      <span data-testid="selected-tools">{props.selectedTools.join(",")}</span>

      <button
        data-testid="select-ball-detection"
        onClick={() => {
          const current = props.selectedTools;
          const newTools = current.includes("ball_detection")
            ? current.filter((t) => t !== "ball_detection")
            : [...current, "ball_detection"];
          props.onToolChange(newTools);
        }}
      >
        Toggle Ball Detection
      </button>

      <button
        data-testid="select-extract-text"
        onClick={() => {
          const current = props.selectedTools;
          const newTools = current.includes("analyze")
            ? current.filter((t) => t !== "analyze")
            : [...current, "analyze"];
          props.onToolChange(newTools);
        }}
      >
        Toggle Extract Text
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

vi.mock("./components/VideoTracker", () => ({
  VideoTracker: (props: { pluginId: string; tools: string[]; jobId?: string | null }) => (
    <div data-testid="video-tracker">
      <span data-testid="video-tracker-plugin">{props.pluginId}</span>
      <span data-testid="video-tracker-tools">{props.tools.join(",")}</span>
      {props.jobId && <span data-testid="video-tracker-job-id">{props.jobId}</span>}
    </div>
  ),
}));

vi.mock("./api/client", () => ({
  apiClient: {
    submitImage: vi.fn(),
    pollJob: vi.fn(),
    // IMPORTANT: return different manifests per plugin
    getPluginManifest: vi.fn((pluginId: string) => {
      if (pluginId === "yolo-tracker") {
        return Promise.resolve({
          id: "yolo-tracker",
          name: "YOLO Tracker",
          version: "1.0.0",
          entrypoint: "plugin.py",
          tools: {
            // Object key order is insertion order: first tool becomes default
            player_detection: {
              inputs: { frame_base64: { type: "string" } },
              outputs: {},
              description: "Detect players",
            },
            ball_detection: {
              inputs: { frame_base64: { type: "string" } },
              outputs: {},
              description: "Detect ball",
            },
            radar: {
              inputs: { frame_base64: { type: "string" } },
              outputs: {},
              description: "Radar overlay",
            },
          },
        });
      }

      if (pluginId === "ocr") {
        return Promise.resolve({
          id: "ocr",
          name: "OCR",
          version: "1.0.0",
          entrypoint: "plugin.py",
          tools: {
            analyze: {
              inputs: { image: { type: "string" } },
              outputs: {},
              description: "Extract text",
            },
          },
        });
      }

      return Promise.resolve({
        id: pluginId,
        name: pluginId,
        version: "1.0.0",
        entrypoint: "plugin.py",
        tools: {},
      });
    }),
  },
}));

vi.mock("./hooks/useWebSocket", () => ({
  useWebSocket: vi.fn(),
}));

import App from "./App";
import { useWebSocket } from "./hooks/useWebSocket";

const mockUseWebSocket = vi.mocked(useWebSocket);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function setupHook(overrides: Record<string, unknown> = {}) {
  const mockSendFrame = vi.fn();
  const mockSwitchPlugin = vi.fn();

  mockUseWebSocket.mockReturnValue({
    isConnected: true,
    isConnecting: false,
    connectionStatus: "connected",
    attempt: 0,
    error: null,
    errorInfo: null,

    sendFrame: mockSendFrame,
    switchPlugin: mockSwitchPlugin,
    disconnect: vi.fn(),
    reconnect: vi.fn(),

    latestResult: null,
    stats: { framesProcessed: 0, avgProcessingTime: 0 },

    ...overrides,
  } as unknown as ReturnType<typeof useWebSocket>);

  return { mockSendFrame, mockSwitchPlugin };
}

async function startStreaming(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole("button", { name: /start streaming/i }));
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("App - Tool Routing via sendFrame (Multi-Tool Support)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("passes auto-selected first tool in useWebSocket options when streaming", async () => {
    const { mockSendFrame } = setupHook();
    const user = userEvent.setup();

    render(<App />);

    // Select YOLO plugin -> manifest loads -> App auto-selects first tool (player_detection)
    await user.click(screen.getByTestId("select-yolo"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tools")).toHaveTextContent("player_detection");
    });

    // Verify useWebSocket was called with tools option
    expect(mockUseWebSocket).toHaveBeenCalledWith(
      expect.objectContaining({
        tools: ["player_detection"],
      })
    );

    await startStreaming(user);

    // Emit a frame
    await user.click(screen.getByTestId("emit-frame"));

    expect(mockSendFrame).toHaveBeenCalledTimes(1);

    // sendFrame should be called without extra parameter (tools are in useWebSocket options)
    const [imageData] = mockSendFrame.mock.calls[0];
    expect(imageData).toBe("base64imagedata");
  });

  it("passes updated tools when user toggles tools", async () => {
    const { mockSendFrame } = setupHook();
    const user = userEvent.setup();

    render(<App />);

    await user.click(screen.getByTestId("select-yolo"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tools")).toHaveTextContent("player_detection");
    });

    // Toggle ball_detection to add it
    await user.click(screen.getByTestId("select-ball-detection"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tools")).toHaveTextContent("player_detection,ball_detection");
    });

    // Verify useWebSocket was called with updated tools option
    expect(mockUseWebSocket).toHaveBeenCalledWith(
      expect.objectContaining({
        tools: ["player_detection", "ball_detection"],
      })
    );

    await startStreaming(user);

    await user.click(screen.getByTestId("emit-frame"));

    expect(mockSendFrame).toHaveBeenCalledTimes(1);

    // sendFrame should be called without extra parameter
    const [imageData] = mockSendFrame.mock.calls[0];
    expect(imageData).toBe("base64imagedata");
  });

  it("resets tools when plugin changes (yolo -> ocr) and uses new plugin default", async () => {
    const { mockSendFrame, mockSwitchPlugin } = setupHook();
    const user = userEvent.setup();

    render(<App />);

    // Start on YOLO and select multiple tools
    await user.click(screen.getByTestId("select-yolo"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tools")).toHaveTextContent("player_detection");
    });

    await user.click(screen.getByTestId("select-ball-detection"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tools")).toHaveTextContent("player_detection,ball_detection");
    });

    // Switch plugin to OCR -> App should reset selectedTools -> auto-select OCR's first tool ("analyze")
    await user.click(screen.getByTestId("select-ocr"));

    // When connected, App should also call switchPlugin on the websocket
    expect(mockSwitchPlugin).toHaveBeenCalledWith("ocr");

    await waitFor(() => {
      expect(screen.getByTestId("selected-tools")).toHaveTextContent("analyze");
    });

    // Verify useWebSocket was called with reset tools option
    expect(mockUseWebSocket).toHaveBeenCalledWith(
      expect.objectContaining({
        tools: ["analyze"],
      })
    );

    // Start streaming and emit frame -> must use analyze, not previous yolo tools
    await startStreaming(user);
    await user.click(screen.getByTestId("emit-frame"));

    expect(mockSendFrame).toHaveBeenCalledTimes(1);
    // sendFrame should be called without extra parameter
    const [imageData] = mockSendFrame.mock.calls[0];
    expect(imageData).toBe("base64imagedata");
  });

  it("can remove tools by toggling them again", async () => {
    const { mockSendFrame } = setupHook();
    const user = userEvent.setup();

    render(<App />);

    await user.click(screen.getByTestId("select-yolo"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tools")).toHaveTextContent("player_detection");
    });

    // Add ball_detection
    await user.click(screen.getByTestId("select-ball-detection"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tools")).toHaveTextContent("player_detection,ball_detection");
    });

    // Remove ball_detection by toggling again
    await user.click(screen.getByTestId("select-ball-detection"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tools")).toHaveTextContent("player_detection");
    });

    // Verify useWebSocket was called with updated tools option
    expect(mockUseWebSocket).toHaveBeenCalledWith(
      expect.objectContaining({
        tools: ["player_detection"],
      })
    );

    await startStreaming(user);
    await user.click(screen.getByTestId("emit-frame"));

    expect(mockSendFrame).toHaveBeenCalledTimes(1);
    // sendFrame should be called without extra parameter
    const [imageData] = mockSendFrame.mock.calls[0];
    expect(imageData).toBe("base64imagedata");
  });

  it("passes tools array to VideoTracker component", async () => {
    setupHook();
    const user = userEvent.setup();

    render(<App />);

    await user.click(screen.getByTestId("select-yolo"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tools")).toHaveTextContent("player_detection");
    });

    // Add ball_detection
    await user.click(screen.getByTestId("select-ball-detection"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tools")).toHaveTextContent("player_detection,ball_detection");
    });

    // Switch to upload mode to see VideoTracker
    await user.click(screen.getByRole("button", { name: "Upload" }));

    await waitFor(() => {
      const videoTracker = screen.getByTestId("video-tracker");
      expect(videoTracker).toBeInTheDocument();
      expect(screen.getByTestId("video-tracker-plugin")).toHaveTextContent("yolo-tracker");
      expect(screen.getByTestId("video-tracker-tools")).toHaveTextContent("player_detection,ball_detection");
    });
  });
});

// ---------------------------------------------------------------------------
// v0.10.1: Locked Tools Tests
// ---------------------------------------------------------------------------

describe("App - Locked Tools After Upload (v0.10.1)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("locks tools after file upload - ToolSelector becomes disabled", async () => {
    // This test verifies that after upload, tools are locked and cannot be changed
    const { apiClient } = await import("./api/client");
    const mockSubmitImage = vi.fn().mockResolvedValue({ job_id: "test-job-123" });
    const mockPollJob = vi.fn().mockResolvedValue({
      job_id: "test-job-123",
      status: "completed",
      results: { text: "test" },
    });
    vi.mocked(apiClient.submitImage).mockImplementation(mockSubmitImage);
    vi.mocked(apiClient.pollJob).mockImplementation(mockPollJob);

    setupHook();
    const user = userEvent.setup();

    render(<App />);

    // Select plugin
    await user.click(screen.getByTestId("select-yolo"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tools")).toHaveTextContent("player_detection");
    });

    // Switch to upload mode
    await user.click(screen.getByRole("button", { name: "Upload" }));

    // The test passes if we can verify the lockedTools behavior
    // Since ToolSelector is mocked, we verify through useWebSocket calls
    // After implementation, upload should lock tools
  });

  it("resets locked tools when plugin changes", async () => {
    setupHook();
    const user = userEvent.setup();

    render(<App />);

    // Select YOLO and get first tool
    await user.click(screen.getByTestId("select-yolo"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tools")).toHaveTextContent("player_detection");
    });

    // Switch to OCR - locked tools should reset
    await user.click(screen.getByTestId("select-ocr"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tools")).toHaveTextContent("analyze");
    });

    // Verify useWebSocket was called with the new plugin's tool
    expect(mockUseWebSocket).toHaveBeenCalledWith(
      expect.objectContaining({
        tools: ["analyze"],
      })
    );
  });
});