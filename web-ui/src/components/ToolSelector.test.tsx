/**
 * Tests for ToolSelector component
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
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
      inputs: [
        {
          name: "frame_base64",
          type: "string",
          description: "Base64 encoded frame",
        },
      ],
      outputs: [
        {
          name: "detections",
          type: "array",
          description: "Detected players",
        },
      ],
    },
    {
      id: "detect_ball",
      title: "Detect Ball",
      description: "Detect ball object",
      inputs: [
        {
          name: "frame_base64",
          type: "string",
        },
      ],
      outputs: [
        {
          name: "detections",
          type: "array",
        },
      ],
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
        selectedTool="detect_players"
        onToolChange={vi.fn()}
      />
    );

    // Verify dropdown shows tool titles, not indices
    expect(screen.getByDisplayValue("Detect Players")).toBeInTheDocument();

    const options = screen.getAllByRole("option");
    const optionValues = options.map((opt) =>
      opt.getAttribute("value")
    );

    // Should contain tool IDs, not array indices
    expect(optionValues).toContain("detect_players");
    expect(optionValues).toContain("detect_ball");
    expect(optionValues).not.toContain("0");
    expect(optionValues).not.toContain("1");
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
        selectedTool="detect_players"
        onToolChange={vi.fn()}
      />
    );

    // Dropdown option should show title "Detect Players"
    expect(screen.getByDisplayValue("Detect Players")).toBeInTheDocument();
    
    // Info box should show title "Detect Players" with description
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
        selectedTool="detect_players"
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
        selectedTool="detect_players"
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
        selectedTool="detect_players"
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
        selectedTool=""
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
        selectedTool="detect_players"
        onToolChange={vi.fn()}
      />
    );

    expect(screen.getByDisplayValue("detect_players")).toBeInTheDocument();

    const options = screen.getAllByRole("option");
    const optionValues = options.map((opt) =>
      opt.getAttribute("value")
    );

    expect(optionValues).toContain("detect_players");
    expect(optionValues).toContain("detect_ball");
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
        selectedTool="detect_players"
        onToolChange={vi.fn()}
      />
    );

    expect(screen.getByText("Detect player objects")).toBeInTheDocument();
    expect(screen.getByText("frame_base64")).toBeInTheDocument();
    expect(screen.getByDisplayValue("detect_players")).toBeInTheDocument();
  });

  it("calls onToolChange when tool selection changes", async () => {
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
        selectedTool="detect_players"
        onToolChange={onToolChange}
      />
    );

    const select = screen.getByRole("combobox");
    
    // Wait for the select to be available
    await waitFor(() => {
      expect(select).toBeInTheDocument();
    }, { timeout: 10000 });

    // Then change the selection
    fireEvent.change(select, { target: { value: "detect_ball" } });

    expect(onToolChange).toHaveBeenCalledWith("detect_ball");
  });

  it("disables selector when disabled prop is true", () => {
    mockUseManifest.mockReturnValue({
      manifest: mockManifestLegacy,
      loading: false,
      error: null,
      clearCache: vi.fn(),
    });

    render(
      <ToolSelector
        pluginId="test-plugin"
        selectedTool="detect_players"
        onToolChange={vi.fn()}
        disabled={true}
      />
    );

    const select = screen.getByRole("combobox");
    expect(select).toBeDisabled();
    expect(screen.getByText("Stop streaming to change tool")).toBeInTheDocument();
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
        selectedTool="detect_players"
        onToolChange={vi.fn()}
        compact={true}
      />
    );

    expect(screen.getByDisplayValue("detect_players")).toBeInTheDocument();
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
        selectedTool="detect_players"
        onToolChange={vi.fn()}
      />
    );

    expect(screen.getByText("Inputs:")).toBeInTheDocument();
    expect(screen.getByText("Outputs:")).toBeInTheDocument();
    expect(screen.getByText("frame_base64")).toBeInTheDocument();
    expect(screen.getByText("detections")).toBeInTheDocument();
  });
});
