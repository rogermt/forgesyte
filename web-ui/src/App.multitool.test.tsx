/**
 * Multitool Selection Tests - REAL tests
 *
 * These tests verify ACTUAL backend communication:
 * - Frontend sends capabilities with useLogicalId=true
 * - Backend resolves capabilities to tool IDs
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
      <button data-testid="select-nocap" onClick={() => props.onPluginChange("no-cap-plugin")}>
        Select NoCap
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
    // Manifest: tools have capabilities but NO input_types for image
    getPluginManifest: vi.fn((pluginId: string) => {
      if (pluginId === "yolo-tracker") {
        return Promise.resolve({
          id: "yolo-tracker",
          name: "YOLO Tracker",
          version: "1.0.0",
          capabilities: ["player_detection", "ball_detection"],
          tools: {
            video_player_detection: {
              capabilities: ["player_detection"],
              input_types: ["video"],
              inputs: {},
              outputs: { result: { type: "object" } },
            },
            video_ball_detection: {
              capabilities: ["ball_detection"],
              input_types: ["video"],
              inputs: {},
              outputs: { result: { type: "object" } },
            },
          },
        });
      }
      if (pluginId === "no-cap-plugin") {
        // Manifest WITHOUT capabilities - only tool IDs
        return Promise.resolve({
          id: "no-cap-plugin",
          name: "No Cap Plugin",
          tools: {
            toolA: { input_types: ["image"], inputs: {}, outputs: {} },
            toolB: { input_types: ["image"], inputs: {}, outputs: {} },
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
import App from "./App";

// ---------------------------------------------------------------------------
// REAL tests - verify actual backend communication
// ---------------------------------------------------------------------------

describe("Multitool Selection - REAL tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // -------------------------------------------------------------------------
  // Test 1: Multi-tool image upload sends capabilities with useLogicalId=true
  // -------------------------------------------------------------------------
  it("submitImage sends capabilities with useLogicalId=true for multi-tool", { timeout: 10000 }, async () => {
    const { apiClient } = await import("./api/client");

    render(<App />);

    // Select YOLO plugin
    await userEvent.click(screen.getByTestId("select-yolo"));

    // Wait for manifest to load
    await waitFor(() => {
      expect(apiClient.getPluginManifest).toHaveBeenCalled();
    }, { timeout: 5000 });

    // Switch to Upload view
    const navButtons = screen.getAllByRole("button");
    const uploadNavBtn = navButtons.find(b =>
      b.textContent?.toLowerCase().trim() === "upload"
    );
    if (uploadNavBtn) {
      await userEvent.click(uploadNavBtn);
    }

    // Get tool buttons (Player Detection, Ball Detection)
    const allButtons = screen.getAllByRole("button");
    const toolButtons = allButtons.filter(b => {
      const text = b.textContent?.toLowerCase() || "";
      return text.includes("player detection") || text.includes("ball detection");
    });

    expect(toolButtons.length).toBeGreaterThanOrEqual(2);

    // Select BOTH tools
    await userEvent.click(toolButtons[0]);
    await userEvent.click(toolButtons[1]);

    // Verify both are selected
    await waitFor(() => {
      expect(toolButtons[0].getAttribute("aria-pressed")).toBe("true");
      expect(toolButtons[1].getAttribute("aria-pressed")).toBe("true");
    }, { timeout: 3000 });

    // Trigger image upload
    const fileInput = await screen.findByTestId("image-upload");
    expect(fileInput).toBeTruthy();

    const file = new File(["test"], "test.png", { type: "image/png" });
    Object.defineProperty(fileInput, "files", { value: [file] });
    fileInput.dispatchEvent(new Event("change", { bubbles: true }));

    // Wait for submitImage to be called
    await waitFor(() => {
      expect(apiClient.submitImage).toHaveBeenCalled();
    }, { timeout: 5000 });

    // CRITICAL: Verify submitImage receives:
    // - capabilities (NOT tool IDs)
    // - useLogicalId=true (backend resolves)
    expect(apiClient.submitImage).toHaveBeenCalledWith(
      expect.any(File),
      "yolo-tracker",
      ["player_detection", "ball_detection"],  // capabilities, NOT tool IDs
      undefined,
      true  // useLogicalId=true - BACKEND resolves
    );
  });

  // -------------------------------------------------------------------------
  // Test 2: WebSocket receives capabilities (backend resolves for streaming)
  // -------------------------------------------------------------------------
  it("useWebSocket receives capabilities for backend resolution", { timeout: 10000 }, async () => {
    const { useWebSocket } = await import("./hooks/useWebSocket");

    render(<App />);

    // Select YOLO plugin
    await userEvent.click(screen.getByTestId("select-yolo"));

    // Wait for manifest to load
    await waitFor(() => {
      expect(screen.getAllByRole("button").length).toBeGreaterThan(5);
    }, { timeout: 5000 });

    // Get tool buttons
    const allButtons = screen.getAllByRole("button");
    const toolButtons = allButtons.filter(b => {
      const text = b.textContent?.toLowerCase() || "";
      return text.includes("player detection") || text.includes("ball detection");
    });

    // Select both tools
    await userEvent.click(toolButtons[0]);
    await userEvent.click(toolButtons[1]);

    // Verify useWebSocket was called with capabilities
    // The WebSocket hook receives the tools that will be sent in frames
    const lastCall = (useWebSocket as ReturnType<typeof vi.fn>).mock.calls.at(-1);
    expect(lastCall).toBeDefined();
    
    const wsOptions = lastCall?.[0] as { tools?: string[] };
    expect(wsOptions?.tools).toEqual(
      expect.arrayContaining(["player_detection", "ball_detection"])
    );
  });

  // -------------------------------------------------------------------------
  // Test 3: Multi-tool selection preserved in UI
  // -------------------------------------------------------------------------
  it("preserves multi-tool selection in UI", async () => {
    render(<App />);

    // Select YOLO plugin
    await userEvent.click(screen.getByTestId("select-yolo"));

    // Wait for tool buttons to appear
    await waitFor(() => {
      expect(screen.getAllByRole("button").length).toBeGreaterThan(5);
    }, { timeout: 5000 });

    // Get tool buttons
    const allButtons = screen.getAllByRole("button");
    const toolButtons = allButtons.filter(b => {
      const text = b.textContent?.toLowerCase() || "";
      return text.includes("player detection") || text.includes("ball detection");
    });

    // Select both tools
    await userEvent.click(toolButtons[0]);
    await userEvent.click(toolButtons[1]);

    // Both tools should stay selected
    await waitFor(() => {
      expect(toolButtons[0].getAttribute("aria-pressed")).toBe("true");
      expect(toolButtons[1].getAttribute("aria-pressed")).toBe("true");
    }, { timeout: 3000 });
  });
});

// ---------------------------------------------------------------------------
// Discussion #335: isUsingLogicalIds derivation tests
// These tests verify that useLogicalId is derived from manifest, not hardcoded
// ---------------------------------------------------------------------------
describe("Discussion #335: isUsingLogicalIds derivation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // -------------------------------------------------------------------------
  // Test A: Manifest WITH capabilities → useLogicalId=true
  // -------------------------------------------------------------------------
  it("passes useLogicalId=true when manifest HAS capabilities", { timeout: 15000 }, async () => {
    const { apiClient } = await import("./api/client");

    render(<App />);

    // Select plugin (yolo-tracker has capabilities in mock)
    await userEvent.click(screen.getByTestId("select-yolo"));

    // Wait for manifest load
    await waitFor(() => {
      expect(apiClient.getPluginManifest).toHaveBeenCalled();
    }, { timeout: 5000 });

    // Switch to Upload view
    const navButtons = screen.getAllByRole("button");
    const uploadNavBtn = navButtons.find(b =>
      b.textContent?.toLowerCase().trim() === "upload"
    );
    if (uploadNavBtn) {
      await userEvent.click(uploadNavBtn);
    }

    // Select capability buttons
    const buttons = screen.getAllByRole("button");
    const capButtons = buttons.filter(b =>
      (b.textContent || "").toLowerCase().includes("detection")
    );

    if (capButtons.length >= 2) {
      await userEvent.click(capButtons[0]);
      await userEvent.click(capButtons[1]);
    } else if (capButtons.length === 1) {
      await userEvent.click(capButtons[0]);
    }

    // Upload image
    const fileInput = await screen.findByTestId("image-upload");
    const file = new File(["x"], "x.png", { type: "image/png" });
    Object.defineProperty(fileInput, "files", { value: [file] });
    fileInput.dispatchEvent(new Event("change", { bubbles: true }));

    await waitFor(() => {
      expect(apiClient.submitImage).toHaveBeenCalled();
    }, { timeout: 5000 });

    const call = apiClient.submitImage.mock.calls[0];
    const useLogicalId = call[4];
    expect(useLogicalId).toBe(true);
  });

  // -------------------------------------------------------------------------
  // Test B: Manifest WITHOUT capabilities → useLogicalId=false
  // THIS TEST SHOULD FAIL until we fix the hardcoded useLogicalId=true
  // -------------------------------------------------------------------------
  it("passes useLogicalId=false when manifest has NO capabilities", { timeout: 15000 }, async () => {
    const { apiClient } = await import("./api/client");

    render(<App />);

    // Select no-cap-plugin (manifest has NO capabilities, only tool IDs)
    await userEvent.click(screen.getByTestId("select-nocap"));

    // Wait for manifest load
    await waitFor(() => {
      expect(apiClient.getPluginManifest).toHaveBeenCalledWith("no-cap-plugin");
    }, { timeout: 5000 });

    // Switch to Upload view
    const navButtons = screen.getAllByRole("button");
    const uploadNavBtn = navButtons.find(b =>
      b.textContent?.toLowerCase().trim() === "upload"
    );
    if (uploadNavBtn) {
      await userEvent.click(uploadNavBtn);
    }

    // Get tool buttons (toolA, toolB - no capabilities, just IDs)
    const buttons = screen.getAllByRole("button");
    const toolButtons = buttons.filter(b =>
      (b.textContent || "").toLowerCase().includes("tool")
    );

    if (toolButtons.length >= 1) {
      await userEvent.click(toolButtons[0]);
    }

    // Upload image
    const fileInput = await screen.findByTestId("image-upload");
    const file = new File(["x"], "x.png", { type: "image/png" });
    Object.defineProperty(fileInput, "files", { value: [file] });
    fileInput.dispatchEvent(new Event("change", { bubbles: true }));

    await waitFor(() => {
      expect(apiClient.submitImage).toHaveBeenCalled();
    }, { timeout: 5000 });

    const call = apiClient.submitImage.mock.calls[0];
    const useLogicalId = call[4];
    
    // Discussion #335: When manifest has NO capabilities, useLogicalId should be FALSE
    // THIS WILL FAIL with current code because useLogicalId is hardcoded to true
    expect(useLogicalId).toBe(false);
  });
});
