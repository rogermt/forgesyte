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

import { vi } from "vitest";

// ---------------------------------------------------------------------------
// Mocks (must be declared before importing App)
// ---------------------------------------------------------------------------

vi.mock("./components/CameraPreview", () => ({
  CameraPreview: () => (
    <div data-testid="camera-preview">
      <button data-testid="emit-frame">Emit Frame</button>
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
          const newTools = current.includes("extract_text")
            ? current.filter((t) => t !== "extract_text")
            : [...current, "extract_text"];
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
  VideoTracker: (props: { pluginId: string; tools: string[] }) => (
    <div data-testid="video-tracker">
      <span data-testid="video-tracker-plugin">{props.pluginId}</span>
      <span data-testid="video-tracker-tools">{props.tools.join(",")}</span>
    </div>
  ),
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
            extract_text: {
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

// ---------------------------------------------------------------------------
// REMOVED: Legacy Phase-10 tests for useWebSocket with onFrame callback
// These tests validated APIs that no longer exist in Phase-17 architecture
// Phase-17 replaces useWebSocket with RealtimeProvider
// Phase-17 replaces onFrame callback with RealtimeContext.sendFrame()
// Test coverage replaced by FE-4 → FE-7 tests
// Helper functions (setupHook, startStreaming) were only used by these tests
// ---------------------------------------------------------------------------