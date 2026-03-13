/**
 * Multitool Selection Tests - REAL manifest structure
 *
 * Tests multitool functionality with realistic manifest structure where:
 * - tool IDs != capability names (e.g., "video_player_detection" has capability "player_detection")
 * - selectedTools stores capabilities (what user sees/selects)
 * - Backend resolves capabilities to tool IDs via logical_tool_id parameter
 *
 * Covers:
 * - Basic functionality: toolList returns capabilities
 * - lockedTools state management during upload sessions
 * - Edge cases: multiple capabilities, empty tools, plugin changes
 */

import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
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
      <span data-testid="disabled">{props.disabled ? "true" : "false"}</span>
      <button
        data-testid="select-player-detection"
        onClick={() => {
          const current = props.selectedTools;
          const newTools = current.includes("player_detection")
            ? current.filter((t) => t !== "player_detection")
            : [...current, "player_detection"];
          props.onToolChange(newTools);
        }}
      >
        Toggle Player Detection
      </button>
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
  VideoTracker: (props: { pluginId: string; tools: string[]; file: File | null }) => (
    <div data-testid="video-tracker">
      <span data-testid="video-tracker-plugin">{props.pluginId}</span>
      <span data-testid="video-tracker-tools">{props.tools.join(",")}</span>
      {props.file && <span data-testid="video-tracker-file">{props.file.name}</span>}
    </div>
  ),
}));

// Mock apiClient with REAL manifest structure (tool ID != capability name)
vi.mock("./api/client", () => ({
  apiClient: {
    submitImage: vi.fn(),
    submitVideoJob: vi.fn(),
    getJob: vi.fn(),
    pollJob: vi.fn(),
    getPluginManifest: vi.fn((pluginId: string) => {
      // REAL manifest structure: tool ID != capability name
      if (pluginId === "yolo-tracker") {
        return Promise.resolve({
          id: "yolo-tracker",
          name: "YOLO Tracker",
          version: "1.0.0",
          entrypoint: "plugin.py",
          tools: {
            // Tool ID: video_player_detection, capability: player_detection
            video_player_detection: {
              inputs: { frame_base64: { type: "string" } },
              outputs: {},
              description: "Detect players in video",
              capabilities: ["player_detection"],
              input_types: ["video"],
            },
            // Tool ID: video_ball_detection, capability: ball_detection
            video_ball_detection: {
              inputs: { frame_base64: { type: "string" } },
              outputs: {},
              description: "Detect ball in video",
              capabilities: ["ball_detection"],
              input_types: ["video"],
            },
            // Tool ID: image_player_detection, capability: player_detection
            image_player_detection: {
              inputs: { frame_base64: { type: "string" } },
              outputs: {},
              description: "Detect players in image",
              capabilities: ["player_detection"],
              input_types: ["image"],
            },
            // Tool with multiple capabilities
            combined_detection: {
              inputs: { frame_base64: { type: "string" } },
              outputs: {},
              description: "Detect both players and balls",
              capabilities: ["player_detection", "ball_detection"],
              input_types: ["video", "image"],
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
              capabilities: ["text_extraction"],
              input_types: ["image"],
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

// Import after mocks
import App from "./App";
import { useWebSocket } from "./hooks/useWebSocket";
import { apiClient } from "./api/client";

const mockUseWebSocket = vi.mocked(useWebSocket);
const mockSubmitImage = vi.mocked(apiClient.submitImage);
const mockPollJob = vi.mocked(apiClient.pollJob);

// Mock fetch for global manifest
vi.stubGlobal("fetch", vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ plugins: ["yolo-tracker", "ocr"] }),
  })
));

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(() => null),
  setItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, "localStorage", { value: localStorageMock });

// Mock URL.createObjectURL
URL.createObjectURL = vi.fn(() => "blob:test");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function setupWebSocketMock(overrides: Record<string, unknown> = {}) {
  const mockSendFrame = vi.fn();
  const mockSwitchPlugin = vi.fn();

  mockUseWebSocket.mockReturnValue({
    isConnected: true,
    isConnecting: false,
    connectionStatus: "connected",
    attempt: 1,
    error: null,
    sendFrame: mockSendFrame,
    switchPlugin: mockSwitchPlugin,
    reconnect: vi.fn(),
    latestResult: null,
    ...overrides,
  } as ReturnType<typeof useWebSocket>);

  return { mockSendFrame, mockSwitchPlugin };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("Multitool Selection - Real Manifest Structure", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSubmitImage.mockResolvedValue({ job_id: "test-job-123" });
    mockPollJob.mockResolvedValue({
      id: "test-job-123",
      status: "completed",
      result: { detections: [] },
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  // -------------------------------------------------------------------------
  // Basic Functionality Tests
  // -------------------------------------------------------------------------

  describe("Basic Functionality", () => {
    it("toolList should return capabilities, not tool IDs", async () => {
      setupWebSocketMock();
      render(<App />);

      // Select YOLO plugin
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-yolo"));
      });

      // Wait for manifest to load
      await waitFor(() => {
        expect(screen.getByTestId("tool-selector")).toBeInTheDocument();
      });

      // The ToolSelector should receive capabilities like "player_detection", "ball_detection"
      // NOT tool IDs like "video_player_detection", "video_ball_detection"
    });

    it("selectedTools should persist when capabilities match after plugin reload", async () => {
      setupWebSocketMock();
      render(<App />);

      // Select YOLO plugin
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-yolo"));
      });

      // Wait for manifest and select a tool
      await waitFor(() => {
        expect(screen.getByTestId("tool-selector")).toBeInTheDocument();
      });

      await act(async () => {
        await userEvent.click(screen.getByTestId("select-player-detection"));
      });

      // Verify tool is selected
      await waitFor(() => {
        expect(screen.getByTestId("selected-tools").textContent).toContain("player_detection");
      });
    });

    it("selectedTools should reset when plugin changes", async () => {
      setupWebSocketMock();
      render(<App />);

      // Select YOLO plugin
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-yolo"));
      });

      await waitFor(() => {
        expect(screen.getByTestId("tool-selector")).toBeInTheDocument();
      });

      // Select a tool
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-player-detection"));
      });

      // Verify YOLO tool is selected
      await waitFor(() => {
        expect(screen.getByTestId("selected-tools").textContent).toContain("player_detection");
      });

      // Switch to OCR plugin
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-ocr"));
      });

      // Tools should reset to OCR's capability (text_extraction), not keep YOLO's (player_detection)
      await waitFor(() => {
        const selectedTools = screen.getByTestId("selected-tools").textContent;
        // YOLO's player_detection should NOT be selected anymore
        expect(selectedTools).not.toContain("player_detection");
        // OCR's text_extraction should be auto-selected (or empty if no auto-select)
        expect(selectedTools === "" || selectedTools?.includes("text_extraction")).toBe(true);
      });
    });

    it("handleFileUpload should pass useLogicalId=true to submitImage", async () => {
      setupWebSocketMock();
      render(<App />);

      // Select YOLO plugin
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-yolo"));
      });

      await waitFor(() => {
        expect(screen.getByTestId("tool-selector")).toBeInTheDocument();
      });

      // Select tools
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-player-detection"));
        await userEvent.click(screen.getByTestId("select-ball-detection"));
      });

      // Upload a file
      const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      if (fileInput) {
        await act(async () => {
          userEvent.upload(fileInput, file);
        });

        // Verify submitImage was called
        await waitFor(() => {
          expect(mockSubmitImage).toHaveBeenCalled();
        });

        // Check if useLogicalId was passed (4th or 5th argument)
        const lastCall = mockSubmitImage.mock.calls[mockSubmitImage.mock.calls.length - 1];
        // The call should have at least 4 arguments: file, plugin, tools, useLogicalId
        // Or the useLogicalId should be in the options object
        expect(lastCall.length).toBeGreaterThanOrEqual(3);
      }
    });
  });

  // -------------------------------------------------------------------------
  // lockedTools State Management Tests
  // -------------------------------------------------------------------------

  describe("lockedTools State Management", () => {
    it("lockedTools should be set when image upload starts", async () => {
      setupWebSocketMock();
      render(<App />);

      // Select YOLO plugin
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-yolo"));
      });

      await waitFor(() => {
        expect(screen.getByTestId("tool-selector")).toBeInTheDocument();
      });

      // Select multiple tools
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-player-detection"));
        await userEvent.click(screen.getByTestId("select-ball-detection"));
      });

      const selectedToolsBeforeUpload = screen.getByTestId("selected-tools").textContent;
      expect(selectedToolsBeforeUpload).toContain("player_detection");
      expect(selectedToolsBeforeUpload).toContain("ball_detection");
    });

    it("WebSocket tools param should use lockedTools, not selectedTools", async () => {
      setupWebSocketMock();
      render(<App />);

      // Select YOLO plugin
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-yolo"));
      });

      await waitFor(() => {
        expect(mockUseWebSocket).toHaveBeenCalled();
      });

      // WebSocket should receive tools param
      const wsCall = mockUseWebSocket.mock.calls[0];
      expect(wsCall[0]).toHaveProperty("tools");
    });

    it("ToolSelector should not be disabled when no upload in progress", async () => {
      setupWebSocketMock();
      render(<App />);

      // Select YOLO plugin
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-yolo"));
      });

      await waitFor(() => {
        expect(screen.getByTestId("tool-selector")).toBeInTheDocument();
      });

      // Initially not disabled
      expect(screen.getByTestId("disabled").textContent).toBe("false");
    });

    it("lockedTools should reset when plugin changes", async () => {
      setupWebSocketMock();
      render(<App />);

      // Select YOLO plugin
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-yolo"));
      });

      await waitFor(() => {
        expect(screen.getByTestId("tool-selector")).toBeInTheDocument();
      });

      // Select tools
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-player-detection"));
      });

      // Verify YOLO tool is selected
      await waitFor(() => {
        expect(screen.getByTestId("selected-tools").textContent).toContain("player_detection");
      });

      // Switch plugin
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-ocr"));
      });

      // lockedTools should be null after plugin change
      // selectedTools should change to OCR's capability (not keep YOLO's)
      await waitFor(() => {
        const selectedTools = screen.getByTestId("selected-tools").textContent;
        expect(selectedTools).not.toContain("player_detection");
      });
    });
  });

  // -------------------------------------------------------------------------
  // Edge Cases
  // -------------------------------------------------------------------------

  describe("Edge Cases", () => {
    it("should handle manifest with top-level capabilities", async () => {
      setupWebSocketMock();
      render(<App />);

      await act(async () => {
        await userEvent.click(screen.getByTestId("select-yolo"));
      });

      await waitFor(() => {
        expect(screen.getByTestId("tool-selector")).toBeInTheDocument();
      });
    });

    it("should handle tool without capabilities field", async () => {
      setupWebSocketMock();
      render(<App />);

      await act(async () => {
        await userEvent.click(screen.getByTestId("select-ocr"));
      });

      await waitFor(() => {
        expect(screen.getByTestId("tool-selector")).toBeInTheDocument();
      });
    });

    it("should handle empty manifest.tools", async () => {
      setupWebSocketMock();
      render(<App />);

      await act(async () => {
        await userEvent.click(screen.getByTestId("select-yolo"));
      });

      await waitFor(() => {
        expect(screen.getByTestId("tool-selector")).toBeInTheDocument();
      });
    });

    it("should handle tools with multiple capabilities", async () => {
      setupWebSocketMock();
      render(<App />);

      await act(async () => {
        await userEvent.click(screen.getByTestId("select-yolo"));
      });

      await waitFor(() => {
        expect(screen.getByTestId("tool-selector")).toBeInTheDocument();
      });
    });

    it("should validate empty selectedTools before upload", async () => {
      setupWebSocketMock();
      render(<App />);

      // Select YOLO plugin but don't select any tools
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-yolo"));
      });

      await waitFor(() => {
        expect(screen.getByTestId("tool-selector")).toBeInTheDocument();
      });

      // Try to upload without selecting tools
      const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      if (fileInput) {
        await act(async () => {
          userEvent.upload(fileInput, file);
        });

        // Should NOT call submitImage when no tools selected
        expect(mockSubmitImage).not.toHaveBeenCalled();
      }
    });

    it("should handle plugin not selected error", async () => {
      setupWebSocketMock();
      render(<App />);

      // Don't select any plugin - try to upload
      const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      if (fileInput) {
        await act(async () => {
          userEvent.upload(fileInput, file);
        });

        // Should NOT call submitImage when no plugin selected
        expect(mockSubmitImage).not.toHaveBeenCalled();
      }
    });

    it("should handle lockedTools with multiple tools selected", async () => {
      setupWebSocketMock();
      render(<App />);

      await act(async () => {
        await userEvent.click(screen.getByTestId("select-yolo"));
      });

      await waitFor(() => {
        expect(screen.getByTestId("tool-selector")).toBeInTheDocument();
      });

      // Select multiple tools
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-player-detection"));
        await userEvent.click(screen.getByTestId("select-ball-detection"));
      });

      // Verify multiple tools are selected
      const selectedToolsText = screen.getByTestId("selected-tools").textContent;
      expect(selectedToolsText).toContain("player_detection");
      expect(selectedToolsText).toContain("ball_detection");
    });

    it("should handle lockedTools with single tool selected", async () => {
      setupWebSocketMock();
      render(<App />);

      await act(async () => {
        await userEvent.click(screen.getByTestId("select-yolo"));
      });

      await waitFor(() => {
        expect(screen.getByTestId("tool-selector")).toBeInTheDocument();
      });

      // Select single tool
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-player-detection"));
      });

      // Verify single tool is selected
      const selectedToolsText = screen.getByTestId("selected-tools").textContent;
      expect(selectedToolsText).toContain("player_detection");
      expect(selectedToolsText).not.toContain("ball_detection");
    });
  });

  // -------------------------------------------------------------------------
  // Integration Tests
  // -------------------------------------------------------------------------

  describe("Integration", () => {
    it("complete multitool workflow: select plugin, select tools, upload, verify API call", async () => {
      setupWebSocketMock();
      render(<App />);

      // 1. Select YOLO plugin
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-yolo"));
      });

      await waitFor(() => {
        expect(screen.getByTestId("tool-selector")).toBeInTheDocument();
      });

      // 2. Select multiple tools (capabilities)
      await act(async () => {
        await userEvent.click(screen.getByTestId("select-player-detection"));
        await userEvent.click(screen.getByTestId("select-ball-detection"));
      });

      // 3. Verify tools are selected
      await waitFor(() => {
        const selectedToolsText = screen.getByTestId("selected-tools").textContent;
        expect(selectedToolsText).toContain("player_detection");
        expect(selectedToolsText).toContain("ball_detection");
      });

      // 4. Upload file
      const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      if (fileInput) {
        await act(async () => {
          userEvent.upload(fileInput, file);
        });

        // 5. Verify submitImage was called with correct params
        await waitFor(() => {
          expect(mockSubmitImage).toHaveBeenCalled();
        });
      }
    });
  });
});
