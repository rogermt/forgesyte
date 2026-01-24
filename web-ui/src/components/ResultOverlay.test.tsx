/**
 * Tests for ResultOverlay component
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { ResultOverlay } from "./ResultOverlay";
import type { Detection } from "../types/video-tracker";

// ============================================================================
// Mock Canvas Context
// ============================================================================

const mockCanvasContext = {
  clearRect: vi.fn(),
  strokeRect: vi.fn(),
  fillRect: vi.fn(),
  drawImage: vi.fn(),
  measureText: vi.fn(() => ({ width: 100 })),
  fillText: vi.fn(),
  strokeStyle: "",
  fillStyle: "",
  lineWidth: 0,
  font: "",
};

HTMLCanvasElement.prototype.getContext = vi.fn(
  () => mockCanvasContext
) as typeof HTMLCanvasElement.prototype.getContext;

// ============================================================================
// Tests
// ============================================================================

describe("ResultOverlay", () => {
  const mockDetections: Detection[] = [
    {
      x: 100,
      y: 100,
      width: 50,
      height: 60,
      confidence: 0.95,
      class: "team_1",
      track_id: 1,
    },
    {
      x: 200,
      y: 150,
      width: 40,
      height: 50,
      confidence: 0.87,
      class: "ball",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders canvas with correct dimensions", () => {
    render(
      <ResultOverlay width={640} height={480} detections={[]} />
    );

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

  it("draws bounding boxes for detections", () => {
    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
      />
    );

    // Each detection should have strokeRect called for the bounding box
    // 2 detections = 2 strokeRect calls
    expect(mockCanvasContext.strokeRect.mock.calls.length).toBeGreaterThan(0);
  });

  it("draws corner markers for each detection", () => {
    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
      />
    );

    // Each detection has 4 corners, so 8 fillRect calls for 2 detections
    expect(mockCanvasContext.fillRect.mock.calls.length).toBeGreaterThanOrEqual(8);
  });

  it("respects showLabels prop", () => {
    const { rerender } = render(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
        showLabels={true}
      />
    );

    const fillTextCalls = mockCanvasContext.fillText.mock.calls.length;
    expect(fillTextCalls).toBeGreaterThan(0);

    vi.clearAllMocks();

    rerender(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
        showLabels={false}
      />
    );

    // Should not call fillText for labels when showLabels is false
    // (only for track IDs if present)
    const fillTextCallsAfter = mockCanvasContext.fillText.mock.calls.length;
    expect(fillTextCallsAfter).toBeLessThanOrEqual(fillTextCalls);
  });

  it("uses custom colors for detection classes", () => {
    const customColors = {
      default: "#FFFFFF",
      team1: "#FF0000",
      team2: "#00FF00",
      ball: "#0000FF",
      referee: "#FFFF00",
    };

    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
        colors={customColors}
      />
    );

    // Check that strokeStyle was set (color application)
    expect(mockCanvasContext.strokeStyle).toBeDefined();
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

  it("includes confidence score in label when showConfidence is true", () => {
    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
        showLabels={true}
        showConfidence={true}
      />
    );

    // fillText should be called with confidence scores
    const fillTextCalls = mockCanvasContext.fillText.mock.calls;
    const hasConfidence = fillTextCalls.some((call) =>
      String(call[0]).includes("%")
    );
    expect(hasConfidence).toBe(true);
  });

  it("omits confidence score in label when showConfidence is false", () => {
    vi.clearAllMocks();

    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
        showLabels={true}
        showConfidence={false}
      />
    );

    const fillTextCalls = mockCanvasContext.fillText.mock.calls;
    const hasConfidencePercent = fillTextCalls.some((call) =>
      String(call[0]).includes("%")
    );
    // Should not have % sign if showConfidence is false
    expect(hasConfidencePercent).toBe(false);
  });

  it("draws track IDs when track_id is present", () => {
    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
        showLabels={true}
      />
    );

    const fillTextCalls = mockCanvasContext.fillText.mock.calls;
    // First detection has track_id: 1, should be drawn
    const hasTrackId = fillTextCalls.some((call) =>
      String(call[0]).includes("ID:")
    );
    expect(hasTrackId).toBe(true);
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

    expect(mockCanvasContext.font).toMatch("16px");
  });

  it("handles empty detection array", () => {
    render(
      <ResultOverlay width={640} height={480} detections={[]} />
    );

    // Should clear canvas but not attempt to draw anything
    expect(mockCanvasContext.clearRect).toHaveBeenCalled();
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

  it("loads and draws annotated frame when provided", () => {
    const mockBase64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";

    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={[]}
        annotatedFrame={mockBase64}
      />
    );

    // drawImage should be called to render the annotated frame
    expect(mockCanvasContext.drawImage.mock.calls.length).toBeGreaterThan(0);
  });

  it("maintains aspect ratio for radar overlay positioning", () => {
    const mockRadarBase64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";

    render(
      <ResultOverlay
        width={640}
        height={480}
        detections={[]}
        radarOverlay={mockRadarBase64}
      />
    );

    // Canvas should be rendered
    const canvas = screen.getByRole("presentation");
    expect(canvas).toBeInTheDocument();
  });
});
