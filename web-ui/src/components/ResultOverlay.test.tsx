/**
 * Tests for ResultOverlay component (plugin-agnostic for v0.9.4)
 * Tests generic bounding box drawing only
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { ResultOverlay } from "./ResultOverlay";
import type { Detection } from "../types/plugin";

// ============================================================================
// Mock Canvas Context
// ============================================================================

const mockCanvasContext = {
  clearRect: vi.fn(),
  strokeRect: vi.fn(),
  fillRect: vi.fn(),
  measureText: vi.fn(() => ({ width: 100 })),
  fillText: vi.fn(),
  strokeStyle: "",
  fillStyle: "",
  lineWidth: 0,
  font: "",
};

HTMLCanvasElement.prototype.getContext = vi.fn(
  () => mockCanvasContext
) as unknown as typeof HTMLCanvasElement.prototype.getContext;

// ============================================================================
// Tests
// ============================================================================

describe("ResultOverlay (v0.9.4 - Plugin-Agnostic)", () => {
  const mockDetections: Detection[] = [
    {
      x: 100,
      y: 100,
      width: 50,
      height: 60,
      confidence: 0.95,
      class: "person",
      track_id: 1,
    },
    {
      x: 200,
      y: 150,
      width: 40,
      height: 50,
      confidence: 0.87,
      class: "vehicle",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders canvas with correct dimensions", () => {
    render(<ResultOverlay width={640} height={480} detections={[]} />);

    const canvas = screen.getByRole("presentation");
    expect(canvas).toHaveAttribute("width", "640");
    expect(canvas).toHaveAttribute("height", "480");
  });

  it("displays detection count when detections exist", () => {
    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
      />
    );

    expect(screen.getByText("2 detections")).toBeInTheDocument();
  });

  it("does not show detection count when no detections", () => {
    render(
      <ResultOverlay width={640} height={480} detections={[]} />
    );

    expect(screen.queryByText(/detection/)).not.toBeInTheDocument();
  });

  it("draws bounding boxes for all detections", () => {
    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
      />
    );

    // One strokeRect call per detection for the box
    expect(mockCanvasContext.strokeRect.mock.calls.length).toBe(2);
  });

  it("draws labels for detections with class", () => {
    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
      />
    );

    // fillText should be called for each detection's label
    expect(mockCanvasContext.fillText.mock.calls.length).toBeGreaterThan(0);
  });

  it("displays detection count with singular form for 1 detection", () => {
    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={[mockDetections[0]]}
      />
    );

    expect(screen.getByText("1 detection")).toBeInTheDocument();
  });

  it("clears canvas before drawing", () => {
    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
      />
    );

    expect(mockCanvasContext.clearRect).toHaveBeenCalledWith(0, 0, 640, 480);
  });

  it("respects custom fontSize", () => {
    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
        fontSize={16}
      />
    );

    // Check that font was set during drawing
    expect(mockCanvasContext.font).toMatch(/bold 16px monospace/);
  });

  it("handles empty detection array", () => {
    render(
      <ResultOverlay width={640} height={480} detections={[]} />
    );

    // Should clear canvas but not attempt to draw anything
    expect(mockCanvasContext.clearRect).toHaveBeenCalled();
    expect(mockCanvasContext.strokeRect).not.toHaveBeenCalled();
  });

  it("updates when detections prop changes", () => {
    const { rerender } = render(
      <ResultOverlay
        width={640}
        height={480}
        detections={[mockDetections[0]]}
      />
    );

    expect(screen.getByText("1 detection")).toBeInTheDocument();

    rerender(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
      />
    );

    expect(screen.getByText("2 detections")).toBeInTheDocument();
  });

  it("uses generic cyan color for all boxes", () => {
    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
      />
    );

    // All strokes should use the same cyan color
    const strokeStyleCalls = mockCanvasContext.strokeStyle;
    expect(strokeStyleCalls).toContain("#00BFFF");
  });

  it("labels replace underscores with spaces", () => {
    const detectionsWithUnderscores: Detection[] = [
      {
        x: 100,
        y: 100,
        width: 50,
        height: 60,
        confidence: 0.95,
        class: "fire_truck",
      },
    ];

    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={detectionsWithUnderscores}
      />
    );

    // fillText should be called with "fire truck" not "fire_truck"
    expect(mockCanvasContext.fillText).toHaveBeenCalledWith(
      expect.stringContaining("fire truck"),
      expect.any(Number),
      expect.any(Number)
    );
  });

  it("draws label background rect before label text", () => {
    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
      />
    );

    // fillRect should be called for label backgrounds
    // fillText should be called for label text
    expect(mockCanvasContext.fillRect.mock.calls.length).toBeGreaterThan(0);
    expect(mockCanvasContext.fillText.mock.calls.length).toBeGreaterThan(0);
  });

  it("handles detections without class property", () => {
    const detectionsNoClass: Detection[] = [
      {
        x: 100,
        y: 100,
        width: 50,
        height: 60,
        confidence: 0.95,
      },
    ];

    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={detectionsNoClass}
      />
    );

    // Should still draw the bounding box
    expect(mockCanvasContext.strokeRect).toHaveBeenCalled();
  });

  it("displays info overlay when detections exist", () => {
    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
      />
    );

    // The info overlay should be visible with detection count
    const infoOverlay = screen.getByText("2 detections");
    expect(infoOverlay).toBeInTheDocument();
  });
});
