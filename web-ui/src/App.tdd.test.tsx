/**
 * TDD tests for tool routing + plugin-switch tool reset (Issue #181).
 *
 * Verifies:
 * 1) sendFrame receives the currently selected tool in its "extra" payload
 * 2) changing tool updates the tool sent to sendFrame
 * 3) changing plugin resets tool to the new plugin’s first tool (prevents ocr+radar)
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// ---------------------------------------------------------------------------
// Mocks (must be declared before importing App)
// ---------------------------------------------------------------------------

vi.mock("./components/CameraPreview", () => ({
  CameraPreview: (props: { enabled: boolean; onFrame: (data: string) => void }) => (
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
        return Promise.resolve({
          id: "ocr",
          name: "OCR",
          version: "1.0.0",
          entrypoint: "plugin.py",
          tools: {
            extract_text: {
              inputs: {},
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
      expect(screen.getByTestId("selected-tool")).toHaveTextContent("player_detection");
    });

    await startStreaming(user);

    // Emit a frame
    await user.click(screen.getByTestId("emit-frame"));

    expect(mockSendFrame).toHaveBeenCalledTimes(1);

    const [imageData, , extra] = mockSendFrame.mock.calls[0];
    expect(imageData).toBe("base64imagedata");
    expect(extra).toEqual(expect.objectContaining({ tool: "player_detection" }));
  });

  it("passes updated tool when user switches tool", async () => {
    const { mockSendFrame } = setupHook();
    const user = userEvent.setup();

    render(<App />);

    await user.click(screen.getByTestId("select-yolo"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tool")).toHaveTextContent("player_detection");
    });

    // Switch tool to ball_detection
    await user.click(screen.getByTestId("select-ball-detection"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tool")).toHaveTextContent("ball_detection");
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

    // Start on YOLO and choose a non-OCR tool
    await user.click(screen.getByTestId("select-yolo"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tool")).toHaveTextContent("player_detection");
    });

    await user.click(screen.getByTestId("select-ball-detection"));

    await waitFor(() => {
      expect(screen.getByTestId("selected-tool")).toHaveTextContent("ball_detection");
    });

    // Switch plugin to OCR -> App should reset selectedTool -> auto-select OCR's first tool ("extract_text")
    await user.click(screen.getByTestId("select-ocr"));

    // When connected, App should also call switchPlugin on the websocket
    expect(mockSwitchPlugin).toHaveBeenCalledWith("ocr");

    await waitFor(() => {
      expect(screen.getByTestId("selected-tool")).toHaveTextContent("extract_text");
    });

    // Start streaming and emit frame -> must use extract_text, not previous yolo tool
    await startStreaming(user);
    await user.click(screen.getByTestId("emit-frame"));

    expect(mockSendFrame).toHaveBeenCalledTimes(1);
    const [, , extra] = mockSendFrame.mock.calls[0];
    expect(extra).toEqual(expect.objectContaining({ tool: "extract_text" }));
  });
});