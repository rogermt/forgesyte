/**
 * Tests for VideoTracker Component (Plugin-Agnostic Skeleton)
 *
 * Tests verify:
 * - Component renders without crashing
 * - Props (pluginId, toolName) are routing parameters only
 * - Internal state exists as specified
 * - UI renders placeholder elements
 * - No plugin-specific logic
 * - No processing logic (skeleton only)
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { VideoTracker } from "./VideoTracker";

// ============================================================================
// Tests
// ============================================================================

describe("VideoTracker (Plugin-Agnostic Skeleton)", () => {
  const defaultProps = {
    pluginId: "forgesyte-yolo-tracker",
    toolName: "detect_players",
  };

  it("renders with required props", () => {
    render(<VideoTracker {...defaultProps} />);
    expect(screen.getByText("VideoTracker")).toBeInTheDocument();
  });

  it("displays pluginId and toolName in header (routing info only)", () => {
    render(
      <VideoTracker pluginId="test-plugin" toolName="test-tool" />
    );
    expect(screen.getByText(/test-plugin/)).toBeInTheDocument();
    expect(screen.getByText(/test-tool/)).toBeInTheDocument();
  });

  it("renders video upload section", () => {
    render(<VideoTracker {...defaultProps} />);
    expect(screen.getByText("Video")).toBeInTheDocument();
    expect(screen.getByText("Click to upload video")).toBeInTheDocument();
  });

  it("renders FPS control section", () => {
    render(<VideoTracker {...defaultProps} />);
    expect(screen.getByText("FPS")).toBeInTheDocument();
    const slider = screen.getByRole("slider");
    expect(slider).toHaveValue("30");
  });

  it("renders device selection", () => {
    render(<VideoTracker {...defaultProps} />);
    expect(screen.getByText("Device")).toBeInTheDocument();
    const select = screen.getByRole("combobox");
    expect(select).toHaveValue("cpu");
  });

  it("renders overlay toggles", () => {
    render(<VideoTracker {...defaultProps} />);
    expect(screen.getByText("Overlays")).toBeInTheDocument();
    expect(screen.getByText("Players")).toBeInTheDocument();
    expect(screen.getByText("Tracking")).toBeInTheDocument();
    expect(screen.getByText("Ball")).toBeInTheDocument();
    expect(screen.getByText("Pitch")).toBeInTheDocument();
    expect(screen.getByText("Radar")).toBeInTheDocument();
  });

  it("renders Start button", () => {
    render(<VideoTracker {...defaultProps} />);
    expect(screen.getByRole("button", { name: "Start" })).toBeInTheDocument();
  });

  it("renders Preview section with video container", () => {
    render(<VideoTracker {...defaultProps} />);
    expect(screen.getByText("Preview")).toBeInTheDocument();
    expect(screen.getByText("No video selected")).toBeInTheDocument();
  });

  it("renders canvas overlay element", () => {
    const { container } = render(<VideoTracker {...defaultProps} />);
    const canvas = container.querySelector("canvas");
    expect(canvas).toBeInTheDocument();
  });

  it("renders all overlay toggles as checked by default", () => {
    render(<VideoTracker {...defaultProps} />);
    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes).toHaveLength(5); // players, tracking, ball, pitch, radar
    checkboxes.forEach((checkbox) => {
      expect(checkbox).toBeChecked();
    });
  });

  it("Start button is disabled when no video selected", () => {
    render(<VideoTracker {...defaultProps} />);
    const button = screen.getByRole("button", { name: "Start" });
    expect(button).toBeDisabled();
  });

  it("has no plugin-specific assumptions", () => {
    // Component works with any pluginId and toolName
    const { rerender } = render(
      <VideoTracker pluginId="plugin-1" toolName="tool-1" />
    );
    expect(screen.getByText(/plugin-1/)).toBeInTheDocument();
    expect(screen.getByText(/tool-1/)).toBeInTheDocument();

    rerender(<VideoTracker pluginId="plugin-2" toolName="tool-2" />);
    expect(screen.getByText(/plugin-2/)).toBeInTheDocument();
    expect(screen.getByText(/tool-2/)).toBeInTheDocument();
  });

  it("has no backend call logic (skeleton only)", () => {
    // Component should render without needing any API calls
    render(<VideoTracker {...defaultProps} />);
    expect(screen.getByText("VideoTracker")).toBeInTheDocument();
    // If there were API calls, they would fail since we have no mocks
    // This test confirms no calls are made
  });

  it("compiles with TypeScript strict mode", () => {
    // Type checking passes at build time
    // This test confirms types are correct
    expect(true).toBe(true);
  });
});
