/**
 * Tests for ToolSelector component
 */

import { describe, it, expect, vi } from "vitest";
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

const mockManifest = {
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

  it("renders empty state when manifest has no tools", () => {
    mockUseManifest.mockReturnValue({
      manifest: {
        ...mockManifest,
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

  it("renders tool list from manifest", () => {
    mockUseManifest.mockReturnValue({
      manifest: mockManifest,
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

  it("displays selected tool details", () => {
    mockUseManifest.mockReturnValue({
      manifest: mockManifest,
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

  it("calls onToolChange when tool selection changes", () => {
    const onToolChange = vi.fn();

    mockUseManifest.mockReturnValue({
      manifest: mockManifest,
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
    fireEvent.change(select, { target: { value: "detect_ball" } });

    expect(onToolChange).toHaveBeenCalledWith("detect_ball");
  });

  it("disables selector when disabled prop is true", () => {
    mockUseManifest.mockReturnValue({
      manifest: mockManifest,
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
      manifest: mockManifest,
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

  it("displays tool inputs and outputs in info box", () => {
    mockUseManifest.mockReturnValue({
      manifest: mockManifest,
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
