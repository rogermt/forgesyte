import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { RealtimeStreamingOverlay } from "./RealtimeStreamingOverlay";

// Mock context
vi.mock("../realtime/RealtimeContext", () => ({
  __esModule: true,
  useRealtimeContext: vi.fn(),
}));

// Mock drawDetections utility
vi.mock("../utils/drawDetections", () => ({
  __esModule: true,
  drawDetections: vi.fn(),
}));

import { useRealtimeContext } from "../realtime/RealtimeContext";
import { drawDetections } from "../utils/drawDetections";

describe("RealtimeStreamingOverlay (Phase-17)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock canvas context
    HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
      clearRect: vi.fn(),
    }));
  });

  it("renders nothing when there is no lastResult", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      state: { lastResult: null },
    });

    const { container } = render(
      <RealtimeStreamingOverlay width={640} height={480} />
    );

    expect(container.firstChild).toBeNull();
  });

  it("renders frame index label when lastResult is present", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      state: {
        lastResult: {
          frame_index: 42,
          result: { detections: [] },
        },
      },
    });

    render(<RealtimeStreamingOverlay width={640} height={480} />);

    expect(screen.getByText("Frame #42")).toBeInTheDocument();
  });

  it("calls drawDetections with mapped detections", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      state: {
        lastResult: {
          frame_index: 1,
          result: {
            detections: [
              { x: 10, y: 20, w: 30, h: 40, label: "person", score: 0.9 },
            ],
          },
        },
      },
    });

    render(<RealtimeStreamingOverlay width={640} height={480} />);

    expect(drawDetections).toHaveBeenCalledTimes(1);
    const callArgs = (drawDetections as vi.Mock).mock.calls[0][0];
    expect(callArgs.detections[0]).toMatchObject({
      x: 10,
      y: 20,
      width: 30,
      height: 40,
      class: "person",
      confidence: 0.9,
    });
  });

  it("shows detection count when debug is true", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      state: {
        lastResult: {
          frame_index: 1,
          result: {
            detections: [
              { x: 0, y: 0, w: 10, h: 10, label: "a", score: 0.5 },
              { x: 10, y: 10, w: 20, h: 20, label: "b", score: 0.8 },
            ],
          },
        },
      },
    });

    render(<RealtimeStreamingOverlay width={640} height={480} debug />);

    expect(screen.getByText("2 detections")).toBeInTheDocument();
  });
});
