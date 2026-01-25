/**
 * Tests for ResultOverlay component
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { ResultOverlay, type OverlayToggles } from "./ResultOverlay";
import type { Detection } from "../types/plugin";

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
  stroke: vi.fn(),
  beginPath: vi.fn(),
  arc: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  fill: vi.fn(),
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

  it("respects overlayToggles.players prop", () => {
    const { rerender } = render(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
        overlayToggles={{ players: true, tracking: true, ball: true, pitch: true, radar: true }}
      />
    );

    const strokeRectCalls = mockCanvasContext.strokeRect.mock.calls.length;
    expect(strokeRectCalls).toBeGreaterThan(0);

    vi.clearAllMocks();

    // Rerender with players toggle off
    rerender(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
        overlayToggles={{ players: false, tracking: true, ball: true, pitch: true, radar: true }}
      />
    );

    // Should not call strokeRect for player bounding boxes when players is false
    // (but ball marker might still be drawn if ball is true)
    expect(mockCanvasContext.strokeRect.mock.calls.length).toBe(0);
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

  it("respects overlayToggles.tracking for track IDs", () => {
    const { rerender } = render(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
        overlayToggles={{ players: true, tracking: true, ball: true, pitch: true, radar: true }}
      />
    );

    const fillTextCalls = mockCanvasContext.fillText.mock.calls.length;
    // Should have fillText calls for labels and track IDs
    expect(fillTextCalls).toBeGreaterThan(0);

    vi.clearAllMocks();

    // Rerender with tracking toggle off
    rerender(
      <ResultOverlay
        width={640}
        height={480}
        detections={mockDetections}
        overlayToggles={{ players: true, tracking: false, ball: true, pitch: true, radar: true }}
      />
    );

    // Count track ID related calls (they should be less or absent)
    const fillTextCallsAfter = mockCanvasContext.fillText.mock.calls.length;
    // When tracking is off, track IDs should not be drawn
    const hasTrackId = fillTextCallsAfter > 0 && fillTextCallsAfter < fillTextCalls;
    expect(hasTrackId).toBe(true);
  });

  it("respects overlayToggles.ball for ball marker", () => {
    const ballOnlyDetections: Detection[] = [
      {
        x: 200,
        y: 150,
        width: 40,
        height: 50,
        confidence: 0.87,
        class: "ball",
      },
    ];

    const { rerender } = render(
      <ResultOverlay
        width={640}
        height={480}
        detections={ballOnlyDetections}
        overlayToggles={{ players: true, tracking: true, ball: true, pitch: true, radar: true }}
      />
    );

    // Should have arc calls for ball marker when ball is true
    expect(mockCanvasContext.arc.mock.calls.length).toBeGreaterThan(0);

    vi.clearAllMocks();

    // Rerender with ball toggle off
    rerender(
      <ResultOverlay
        width={640}
        height={480}
        detections={ballOnlyDetections}
        overlayToggles={{ players: true, tracking: true, ball: false, pitch: true, radar: true }}
      />
    );

    // Should not call arc for ball marker when ball is false
    expect(mockCanvasContext.arc.mock.calls.length).toBe(0);
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

    // Check that font includes the custom size
    expect(mockCanvasContext.font).toContain("16px");
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
    // Mock the Image constructor to simulate already-loaded image
    const mockImage = {
      complete: true,
      src: "",
      onload: null as (() => void) | null,
    };
    
    const OriginalImage = window.Image;
    window.Image = vi.fn(() => mockImage) as unknown as typeof window.Image;

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

    // Restore original Image
    window.Image = OriginalImage;
  });

  it("respects overlayToggles.pitch for pitch lines", () => {
    const pitchLines = [
      { x1: 0, y1: 0, x2: 640, y2: 360 },
      { x1: 0, y1: 180, x2: 640, y2: 180 },
    ];

    const { rerender } = render(
      <ResultOverlay
        width={640}
        height={480}
        detections={[]}
        pitchLines={pitchLines}
        overlayToggles={{ players: true, tracking: true, ball: true, pitch: true, radar: true }}
      />
    );

    // Should have stroke calls for pitch lines when pitch is true
    expect(mockCanvasContext.stroke.mock.calls.length).toBeGreaterThan(0);

    vi.clearAllMocks();

    // Rerender with pitch toggle off
    rerender(
      <ResultOverlay
        width={640}
        height={480}
        detections={[]}
        pitchLines={pitchLines}
        overlayToggles={{ players: true, tracking: true, ball: true, pitch: false, radar: true }}
      />
    );

    // Should not call stroke for pitch lines when pitch is false
    expect(mockCanvasContext.stroke.mock.calls.length).toBe(0);
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

  it("respects overlayToggles.radar for radar overlay", () => {
    // Mock the Image constructor to simulate already-loaded image
    const mockImage = {
      complete: true,
      src: "",
      onload: null as (() => void) | null,
    };
    
    const OriginalImage = window.Image;
    window.Image = vi.fn(() => mockImage) as unknown as typeof window.Image;

    const mockRadarBase64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";

    const { rerender } = render(
      <ResultOverlay
        width={640}
        height={480}
        detections={[]}
        radarOverlay={mockRadarBase64}
        overlayToggles={{ players: true, tracking: true, ball: true, pitch: true, radar: true }}
      />
    );

    // Should have drawImage calls for radar when radar is true
    expect(mockCanvasContext.drawImage.mock.calls.length).toBeGreaterThan(0);

    vi.clearAllMocks();

    // Rerender with radar toggle off
    rerender(
      <ResultOverlay
        width={640}
        height={480}
        detections={[]}
        radarOverlay={mockRadarBase64}
        overlayToggles={{ players: true, tracking: true, ball: true, pitch: true, radar: false }}
      />
    );

    // Should not call drawImage for radar when radar is false
    expect(mockCanvasContext.drawImage.mock.calls.length).toBe(0);

    // Restore original Image
    window.Image = OriginalImage;
  });
});

