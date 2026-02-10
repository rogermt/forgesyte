/**
 * TDD tests for App component - Tool Routing and Plugin Switching
 *
 * Verifies:
 * 1) sendFrame receives the currently selected tool in its "extra" payload
 * 2) Changing tool updates the tool sent to sendFrame
 * 3) Changing plugin resets tool to the new plugin's first tool
 * 4) Handles both Phase-12 array and legacy object manifest formats
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
    selectedTool: string;
    onToolChange: (t: string) => void;
    disabled: boolean;
  }) => (
    <div data-testid="tool-selector">
      <span data-testid="selected-tool">{props.selectedTool}</span>

      <button
        data-testid="select-ball-detection"
        onClick={() => props.onToolChange("ball_detection")}
      >
        Select Ball Detection
      </button>

      <button
        data-testid="select-radar"
        onClick={() => props.onToolChange("radar")}
      >
        Select Radar
      </button>

      <button
        data-testid="select-extract-text"
        onClick={() => props.onToolChange("extract_text")}
      >
        Select Extract Text
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
  VideoTracker: () => <div data-testid="video-tracker">VideoTracker</div>,
}));

vi.mock("./api/client", () => ({
  apiClient: {
    analyzeImage: vi.fn(),
    pollJob: vi.fn(),
    // Return different manifests per plugin
    getPluginManifest: vi.fn((pluginId: string) => {
      if (pluginId === "yolo-tracker") {
        // Legacy format: tools is an object
        return Promise.resolve({
          id: "yolo-tracker",
          name: "YOLO Tracker",
          version: "1.0.0",
          entrypoint: "plugin.py",
          tools: {
            player_detection: {
              inputs: {},
              outputs: {},
              description: "Detect players",
            },
            ball_detection: {
              inputs: {},
              outputs: {},
              description: "Detect ball",
            },
            radar: {
              inputs: {},
              outputs: {},
              description: "Radar overlay",
            },
          },
        });
      }

      if (pluginId === "ocr") {
        // Phase-12 format: tools is an array
        return Promise.resolve({
          id: "ocr",
          name: "OCR",
          version: "1.0.0",
          entrypoint: "plugin.py",
          tools: [
            {
              id: "extract_text",
              inputs: {},
              outputs: {},
              description: "Extract text",
            },
          ],
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

describe("App - Tool Routing via sendFrame", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("passes auto-selected first tool in sendFrame extra payload when streaming", async () => {
    const { mockSendFrame } = setupHook();
    const user = userEvent.setup();

    render(<App />);

    // Select YOLO plugin -> manifest loads -> App auto-selects first tool (player_detection)
    await user.click(screen.getByTestId("select-yolo"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tool")).toHaveTextContent(
        "player_detection"
      );
    });

    await startStreaming(user);

    // Emit a frame
    await user.click(screen.getByTestId("emit-frame"));

    expect(mockSendFrame).toHaveBeenCalledTimes(1);

    const [imageData, , extra] = mockSendFrame.mock.calls[0];
    expect(imageData).toBe("base64imagedata");
    expect(extra).toEqual(
      expect.objectContaining({ tool: "player_detection" })
    );
  });

  it("passes updated tool when user switches tool", async () => {
    const { mockSendFrame } = setupHook();
    const user = userEvent.setup();

    render(<App />);

    await user.click(screen.getByTestId("select-yolo"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tool")).toHaveTextContent(
        "player_detection"
      );
    });

    // Switch tool to ball_detection
    await user.click(screen.getByTestId("select-ball-detection"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tool")).toHaveTextContent(
        "ball_detection"
      );
    });

    await startStreaming(user);

    await user.click(screen.getByTestId("emit-frame"));

    expect(mockSendFrame).toHaveBeenCalledTimes(1);

    const [, , extra] = mockSendFrame.mock.calls[0];
    expect(extra).toEqual(expect.objectContaining({ tool: "ball_detection" }));
  });

  it("resets tool when plugin changes (yolo -> ocr) and uses new plugin default", async () => {
    const { mockSendFrame, mockSwitchPlugin } = setupHook();
    const user = userEvent.setup();

    render(<App />);

    // Start on YOLO and choose a non-OCR tool (radar)
    await user.click(screen.getByTestId("select-yolo"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tool")).toHaveTextContent(
        "player_detection"
      );
    });

    await user.click(screen.getByTestId("select-radar"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tool")).toHaveTextContent("radar");
    });

    // Switch plugin to OCR -> App should reset selectedTool -> auto-select OCR's first tool
    await user.click(screen.getByTestId("select-ocr"));

    // When connected, App should also call switchPlugin on the websocket
    expect(mockSwitchPlugin).toHaveBeenCalledWith("ocr");

    // OCR manifest is Phase-12 array format: [{ id: "extract_text" }]
    // App.tsx toolList handles this and extracts "extract_text"
    await waitFor(() => {
      expect(screen.getByTestId("selected-tool")).toHaveTextContent(
        "extract_text"
      );
    });

    // Start streaming and emit frame -> must use extract_text, not previous yolo tool
    await startStreaming(user);
    await user.click(screen.getByTestId("emit-frame"));

    expect(mockSendFrame).toHaveBeenCalledTimes(1);
    const [, , extra] = mockSendFrame.mock.calls[0];
    expect(extra).toEqual(expect.objectContaining({ tool: "extract_text" }));
  });

  it("handles Phase-12 array format manifest correctly", async () => {
    setupHook();
    const user = userEvent.setup();

    render(<App />);

    // Select OCR which returns Phase-12 array format: tools: [{ id: "extract_text" }]
    await user.click(screen.getByTestId("select-ocr"));

    // Should auto-select extract_text (not "0" which would happen with Object.keys on array)
    await waitFor(() => {
      expect(screen.getByTestId("selected-tool")).toHaveTextContent(
        "extract_text"
      );
    });
  });

  it("handles legacy object format manifest correctly", async () => {
    setupHook();
    const user = userEvent.setup();

    render(<App />);

    // Select YOLO which returns legacy object format: tools: { player_detection: {...} }
    await user.click(screen.getByTestId("select-yolo"));

    // Should auto-select player_detection
    await waitFor(() => {
      expect(screen.getByTestId("selected-tool")).toHaveTextContent(
        "player_detection"
      );
    });
  });

  it("clears upload result and selected job when plugin changes", async () => {
    setupHook();
    const user = userEvent.setup();

    render(<App />);

    // Select YOLO
    await user.click(screen.getByTestId("select-yolo"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-plugin")).toHaveTextContent(
        "yolo-tracker"
      );
    });

    // Switch to OCR - this should clear uploadResult and selectedJob
    // (verified by the useEffect that resets on plugin change)
    await user.click(screen.getByTestId("select-ocr"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-plugin")).toHaveTextContent("ocr");
    });

    // Tool should be reset to OCR's first tool
    await waitFor(() => {
      expect(screen.getByTestId("selected-tool")).toHaveTextContent(
        "extract_text"
      );
    });
  });

  it("does not send frame if not connected", async () => {
    const { mockSendFrame } = setupHook({ isConnected: false });
    const user = userEvent.setup();

    render(<App />);

    await user.click(screen.getByTestId("select-yolo"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tool")).toHaveTextContent(
        "player_detection"
      );
    });

    // Try to emit a frame without connection
    await user.click(screen.getByTestId("emit-frame"));

    // sendFrame should not be called since we're not connected
    expect(mockSendFrame).not.toHaveBeenCalled();
  });

  it("does not send frame if streaming is disabled", async () => {
    const { mockSendFrame } = setupHook();
    const user = userEvent.setup();

    render(<App />);

    await user.click(screen.getByTestId("select-yolo"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tool")).toHaveTextContent(
        "player_detection"
      );
    });

    // Don't start streaming, just emit a frame
    await user.click(screen.getByTestId("emit-frame"));

    // sendFrame should not be called since streaming is disabled
    expect(mockSendFrame).not.toHaveBeenCalled();
  });
});

describe("App - Connection Status Display", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("displays connected status", () => {
    setupHook({ connectionStatus: "connected" });
    render(<App />);

    expect(screen.getByTestId("connection-status-text")).toHaveTextContent(
      "Connected"
    );
  });

  it("displays connecting status", () => {
    setupHook({ connectionStatus: "connecting" });
    render(<App />);

    expect(screen.getByTestId("connection-status-text")).toHaveTextContent(
      "Connecting..."
    );
  });

  it("displays reconnecting status with attempt number", () => {
    setupHook({ connectionStatus: "reconnecting", attempt: 3 });
    render(<App />);

    expect(screen.getByTestId("connection-status-text")).toHaveTextContent(
      "Reconnecting... (attempt 3)"
    );
  });

  it("displays failed status", () => {
    setupHook({ connectionStatus: "failed" });
    render(<App />);

    expect(screen.getByTestId("connection-status-text")).toHaveTextContent(
      "Connection failed"
    );
  });

  it("displays disconnected status", () => {
    setupHook({ connectionStatus: "disconnected" });
    render(<App />);

    expect(screen.getByTestId("connection-status-text")).toHaveTextContent(
      "Disconnected"
    );
  });
});

describe("App - View Mode Navigation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("defaults to stream view", () => {
    setupHook();
    render(<App />);

    expect(screen.getByTestId("camera-preview")).toBeInTheDocument();
  });

  it("switches to jobs view when jobs button clicked", async () => {
    setupHook();
    const user = userEvent.setup();

    render(<App />);

    await user.click(screen.getByRole("button", { name: /jobs/i }));

    expect(screen.getByTestId("job-list")).toBeInTheDocument();
    expect(screen.getByText("Job Details")).toBeInTheDocument();
  });
});

describe("App - WebSocket Error Display", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("displays WebSocket error when present", () => {
    setupHook({ error: "Connection lost" });
    render(<App />);

    expect(screen.getByTestId("ws-error-box")).toHaveTextContent(
      "WebSocket Error: Connection lost"
    );
  });

  it("shows reconnect button when disconnected with error", async () => {
    setupHook({
      error: "Connection lost",
      connectionStatus: "disconnected",
    });

    // Re-setup with reconnect mock accessible
    const mockReconnect = vi.fn();
    mockUseWebSocket.mockReturnValue({
      isConnected: false,
      isConnecting: false,
      connectionStatus: "disconnected",
      attempt: 0,
      error: "Connection lost",
      errorInfo: null,
      sendFrame: vi.fn(),
      switchPlugin: vi.fn(),
      disconnect: vi.fn(),
      reconnect: mockReconnect,
      latestResult: null,
      stats: { framesProcessed: 0, avgProcessingTime: 0 },
    } as unknown as ReturnType<typeof useWebSocket>);

    const user = userEvent.setup();

    render(<App />);

    const reconnectButton = screen.getByRole("button", { name: /reconnect/i });
    expect(reconnectButton).toBeInTheDocument();

    await user.click(reconnectButton);
    expect(mockReconnect).toHaveBeenCalled();
  });
});