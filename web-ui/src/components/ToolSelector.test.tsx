/**
 * Tests for ToolSelector component (multi-select with toggle buttons)
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ToolSelector } from "./ToolSelector";
import * as useManifestModule from "../hooks/useManifest";

// ============================================================================
// Mock useManifest hook
// ============================================================================

vi.mock("../hooks/useManifest");

const mockUseManifest = useManifestModule.useManifest as ReturnType<
  typeof vi.fn
>;

// ============================================================================
// Test Fixtures
// ============================================================================

// Phase-12 format: tools as array with id, title, description, inputs, outputs
const mockManifestPhase12 = {
  id: "test-plugin",
  name: "Test Plugin",
  version: "1.0.0",
  description: "Test plugin",
  tools: [
    {
      id: "detect_players",
      title: "Detect Players",
      description: "Detect player objects",
      inputs: {
        frame_base64: {
          type: "string",
          description: "Base64 encoded frame",
        },
      },
      outputs: {
        detections: {
          type: "array",
          description: "Detected players",
        },
      },
    },
    {
      id: "detect_ball",
      title: "Detect Ball",
      description: "Detect ball object",
      inputs: {
        frame_base64: {
          type: "string",
        },
      },
      outputs: {
        detections: {
          type: "array",
        },
      },
    },
  ],
};

// Legacy format: tools as object (for backward compatibility testing)
const mockManifestLegacy = {
  id: "test-plugin",
  name: "Test Plugin",
  version: "1.0.0",
  description: "Test plugin",
  tools: {
    detect_players: {
      description: "Detect player objects",
      inputs: {
        frame_base64: {
          type: "string",
          description: "Base64 encoded frame",
        },
      },
      outputs: {
        detections: {
          type: "array",
          description: "Detected players",
        },
      },
    },
    detect_ball: {
      description: "Detect ball object",
      inputs: {
        frame_base64: {
          type: "string",
        },
      },
      outputs: {
        detections: {
          type: "array",
        },
      },
    },
  },
};

// ============================================================================
// Tests
// ============================================================================

describe("ToolSelector", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ========================================================================
  // Phase-12 Format Tests (Array-based tools)
  // ========================================================================

  it("renders tool titles from Phase-12 array format", () => {
    mockUseManifest.mockReturnValue({
      manifest: mockManifestPhase12,
      loading: false,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="test-plugin"
        selectedTools={["detect_players"]}
        onToolChange={vi.fn()}
      />
    );

    // Verify buttons show tool titles (use getAllByText since text appears in button and info box)
    expect(screen.getAllByText("Detect Players")).toHaveLength(2);
    expect(screen.getByText("Detect Ball")).toBeInTheDocument();
  });

  it("displays Phase-12 tool title in selected state", () => {
    mockUseManifest.mockReturnValue({
      manifest: mockManifestPhase12,
      loading: false,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="test-plugin"
        selectedTools={["detect_players"]}
        onToolChange={vi.fn()}
      />
    );

    // Button and info box should show title "Detect Players"
    expect(screen.getAllByText("Detect Players")).toHaveLength(2);

    // Info box should show description
    expect(screen.getByText("Detect player objects")).toBeInTheDocument();
  });

  // ========================================================================
  // Legacy Format Tests (Object-based tools)
  // ========================================================================

  it("renders loading state when manifest is loading", () => {
    mockUseManifest.mockReturnValue({
      manifest: null,
      loading: true,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="test-plugin"
        selectedTools={["detect_players"]}
        onToolChange={vi.fn()}
      />
    );

    expect(screen.getByText("Loading tools...")).toBeInTheDocument();
  });

  it("renders error state when manifest fails to load", () => {
    mockUseManifest.mockReturnValue({
      manifest: null,
      loading: false,
      error: "Failed to load manifest",
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="test-plugin"
        selectedTools={["detect_players"]}
        onToolChange={vi.fn()}
      />
    );

    expect(screen.getByText(/Failed to load manifest/)).toBeInTheDocument();
  });

  it("renders empty state when no plugin is selected", () => {
    mockUseManifest.mockReturnValue({
      manifest: null,
      loading: false,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId={null}
        selectedTools={[]}
        onToolChange={vi.fn()}
      />
    );

    expect(screen.getByText("Select a plugin first")).toBeInTheDocument();
  });

  it("renders empty state when manifest has no tools (legacy format)", () => {
    mockUseManifest.mockReturnValue({
      manifest: {
        ...mockManifestLegacy,
        tools: {},
      },
      loading: false,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="test-plugin"
        selectedTools={[]}
        onToolChange={vi.fn()}
      />
    );

    expect(
      screen.getByText("No tools available in this plugin")
    ).toBeInTheDocument();
  });

  it("renders tool list from legacy manifest format", () => {
    mockUseManifest.mockReturnValue({
      manifest: mockManifestLegacy,
      loading: false,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="test-plugin"
        selectedTools={["detect_players"]}
        onToolChange={vi.fn()}
      />
    );

    expect(screen.getAllByText("detect_players")).toHaveLength(2);
    expect(screen.getByText("detect_ball")).toBeInTheDocument();
  });

  it("displays selected tool details (legacy format)", () => {
    mockUseManifest.mockReturnValue({
      manifest: mockManifestLegacy,
      loading: false,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="test-plugin"
        selectedTools={["detect_players"]}
        onToolChange={vi.fn()}
      />
    );

    expect(screen.getByText("Detect player objects")).toBeInTheDocument();
    expect(screen.getByText("frame_base64")).toBeInTheDocument();
    expect(screen.getAllByText("detect_players")).toHaveLength(2);
  });

  it("calls onToolChange when tool selection changes (toggle on)", () => {
    const onToolChange = vi.fn();

    mockUseManifest.mockReturnValue({
      manifest: mockManifestLegacy,
      loading: false,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="test-plugin"
        selectedTools={["detect_players"]}
        onToolChange={onToolChange}
      />
    );

    // Click on detect_ball button to add it
    const ballButton = screen.getByText("detect_ball");
    fireEvent.click(ballButton);

    expect(onToolChange).toHaveBeenCalledWith(["detect_players", "detect_ball"]);
  });

  it("calls onToolChange when tool selection changes (toggle off)", () => {
    const onToolChange = vi.fn();

    mockUseManifest.mockReturnValue({
      manifest: mockManifestLegacy,
      loading: false,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="test-plugin"
        selectedTools={["detect_players", "detect_ball"]}
        onToolChange={onToolChange}
      />
    );

    // Click on detect_ball button to remove it
    const ballButton = screen.getByText("detect_ball");
    fireEvent.click(ballButton);

    expect(onToolChange).toHaveBeenCalledWith(["detect_players"]);
  });

  it("does not allow removing the last selected tool", () => {
    const onToolChange = vi.fn();

    mockUseManifest.mockReturnValue({
      manifest: mockManifestLegacy,
      loading: false,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="test-plugin"
        selectedTools={["detect_players"]}
        onToolChange={onToolChange}
      />
    );

    // Click on detect_players button (only selected tool) - should not call onToolChange
    const playerButtons = screen.getAllByText("detect_players");
    fireEvent.click(playerButtons[0]);

    expect(onToolChange).not.toHaveBeenCalled();
  });

  it("disables buttons when disabled prop is true", () => {
    mockUseManifest.mockReturnValue({
      manifest: mockManifestLegacy,
      loading: false,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="test-plugin"
        selectedTools={["detect_players"]}
        onToolChange={vi.fn()}
        disabled={true}
      />
    );

    const buttons = screen.getAllByRole("button");
    buttons.forEach((button) => {
      expect(button).toBeDisabled();
    });
    // v0.10.1: Message updated to reflect locked state
    expect(screen.getByText("Tools are locked for this session")).toBeInTheDocument();
  });

  it("hides details in compact mode", () => {
    mockUseManifest.mockReturnValue({
      manifest: mockManifestLegacy,
      loading: false,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="test-plugin"
        selectedTools={["detect_players"]}
        onToolChange={vi.fn()}
        compact={true}
      />
    );

    expect(screen.getByText("detect_players")).toBeInTheDocument();
    expect(
      screen.queryByText("Detect player objects")
    ).not.toBeInTheDocument();
  });

  it("displays tool inputs and outputs in info box (legacy format)", () => {
    mockUseManifest.mockReturnValue({
      manifest: mockManifestLegacy,
      loading: false,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="test-plugin"
        selectedTools={["detect_players"]}
        onToolChange={vi.fn()}
      />
    );

    expect(screen.getByText("Inputs:")).toBeInTheDocument();
    expect(screen.getByText("Outputs:")).toBeInTheDocument();
    expect(screen.getByText("frame_base64")).toBeInTheDocument();
    expect(screen.getByText("detections")).toBeInTheDocument();
  });

  it("shows first tool indicator when multiple tools are selected", () => {
    mockUseManifest.mockReturnValue({
      manifest: mockManifestPhase12,
      loading: false,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="test-plugin"
        selectedTools={["detect_players", "detect_ball"]}
        onToolChange={vi.fn()}
      />
    );

    // First tool should have a star indicator
    expect(screen.getAllByText("Detect Players")).toHaveLength(2);
    expect(screen.getByText("Detect Ball")).toBeInTheDocument();
    expect(screen.getByText("★")).toBeInTheDocument();
  });

  it("shows count of additional selected tools", () => {
    mockUseManifest.mockReturnValue({
      manifest: mockManifestPhase12,
      loading: false,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="test-plugin"
        selectedTools={["detect_players", "detect_ball"]}
        onToolChange={vi.fn()}
      />
    );

    // Info box should show "+1 more" when 2 tools are selected
    expect(screen.getByText("+1 more")).toBeInTheDocument();
  });

  // ========================================================================
  // Phase 6: Capabilities-based Tool Selection
  // ========================================================================

  // Manifest with top-level capabilities (like yolo-tracker)
  const mockManifestWithCapabilities = {
    id: "yolo-tracker",
    name: "YOLO Tracker",
    version: "1.0.0",
    description: "YOLO-based tracking plugin",
    capabilities: ["player_detection", "ball_detection", "pitch_detection", "radar"],
    tools: [
      {
        id: "player_detection",
        title: "Player Detection",
        description: "Detect players in images",
        input_types: ["image_bytes"],
        capabilities: ["player_detection"],
        inputs: {},
        outputs: { detections: { type: "array" } },
      },
      {
        id: "video_player_tracking",
        title: "Video Player Tracking",
        description: "Track players in videos",
        input_types: ["video"],
        capabilities: ["player_detection"],
        inputs: {},
        outputs: { frames: { type: "array" } },
      },
      {
        id: "ball_detection",
        title: "Ball Detection",
        description: "Detect ball in images",
        input_types: ["image_bytes"],
        capabilities: ["ball_detection"],
        inputs: {},
        outputs: { detections: { type: "array" } },
      },
      {
        id: "video_ball_detection",
        title: "Video Ball Detection",
        description: "Detect ball in videos",
        input_types: ["video"],
        capabilities: ["ball_detection"],
        inputs: {},
        outputs: { frames: { type: "array" } },
      },
    ],
  };

  it("should show manifest.capabilities when present (not all tools)", () => {
    mockUseManifest.mockReturnValue({
      manifest: mockManifestWithCapabilities,
      loading: false,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="yolo-tracker"
        selectedTools={["player_detection"]}
        onToolChange={vi.fn()}
      />
    );

    // Should show 4 capabilities, not 8 concrete tools
    const buttons = screen.getAllByRole("button");
    // 4 capability buttons (excluding disabled streaming button text)
    const toolButtons = buttons.filter(b => !b.textContent?.includes("Stop streaming"));
    expect(toolButtons).toHaveLength(4);

    // Should show capabilities as titles (formatted nicely)
    // Use getAllByText since selected tool appears in both button and info box
    expect(screen.getAllByText("Player Detection").length).toBeGreaterThan(0);
    expect(screen.getByText("Ball Detection")).toBeInTheDocument();
    expect(screen.getByText("Pitch Detection")).toBeInTheDocument();
    expect(screen.getByText("Radar")).toBeInTheDocument();

    // Should NOT show video_* tools
    expect(screen.queryByText("Video Player Tracking")).not.toBeInTheDocument();
    expect(screen.queryByText("Video Ball Detection")).not.toBeInTheDocument();
  });

  it("should fallback to union of tool.capabilities when no top-level capabilities", () => {
    // Manifest without top-level capabilities
    const manifestWithoutCapabilities = {
      id: "test-plugin",
      name: "Test Plugin",
      version: "1.0.0",
      tools: [
        {
          id: "tool_a",
          capabilities: ["capability_x"],
          inputs: {},
          outputs: {},
        },
        {
          id: "tool_b",
          capabilities: ["capability_y"],
          inputs: {},
          outputs: {},
        },
      ],
    };

    mockUseManifest.mockReturnValue({
      manifest: manifestWithoutCapabilities,
      loading: false,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="test-plugin"
        selectedTools={["capability_x"]}
        onToolChange={vi.fn()}
      />
    );

    // Should show union of capabilities from tools
    expect(screen.getByText("Capability X")).toBeInTheDocument();
    expect(screen.getByText("Capability Y")).toBeInTheDocument();
  });

  it("should format capability names as title case", () => {
    mockUseManifest.mockReturnValue({
      manifest: mockManifestWithCapabilities,
      loading: false,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="yolo-tracker"
        selectedTools={["player_detection"]}
        onToolChange={vi.fn()}
      />
    );

    // player_detection -> Player Detection
    // Use getAllByText since selected tool appears in both button and info box
    expect(screen.getAllByText("Player Detection").length).toBeGreaterThan(0);
    // ball_detection -> Ball Detection
    expect(screen.getByText("Ball Detection")).toBeInTheDocument();
  });
});