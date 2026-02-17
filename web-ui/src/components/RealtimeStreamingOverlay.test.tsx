import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { RealtimeStreamingOverlay } from "./RealtimeStreamingOverlay";

// Mock context
vi.mock("../realtime/RealtimeContext", () => ({
  __esModule: true,
  useRealtimeContext: vi.fn(),
}));

import { useRealtimeContext } from "../realtime/RealtimeContext";

describe("RealtimeStreamingOverlay (Phase-17)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock canvas context
    HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
      clearRect: vi.fn(),
      strokeRect: vi.fn(),
      fillRect: vi.fn(),
      fillText: vi.fn(),
      measureText: vi.fn(() => ({ width: 100 })),
      font: "",
      fillStyle: "",
      lineWidth: 0,
      strokeStyle: "",
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

  it("renders detections with bounding boxes", () => {
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

    expect(screen.getByText("Frame #1")).toBeInTheDocument();
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
