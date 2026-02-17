/**
 * FE-7: StreamDebugPanel Tests
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { StreamDebugPanel } from "./StreamDebugPanel";

vi.mock("../realtime/RealtimeContext", () => ({
  __esModule: true,
  useRealtimeContext: vi.fn(),
}));

import { useRealtimeContext } from "../realtime/RealtimeContext";

describe("StreamDebugPanel", () => {
  // Set up default mock before all tests
  beforeEach(() => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      wsUrl: "ws://localhost/ws/video/stream?pipeline_id=p1",
      currentPipelineId: "p1",
      state: {
        connectionStatus: "connected",
        framesSent: 0,
        startTime: null,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastFrameSizes: [],
        lastLatencies: [],
        currentFps: 15,
        lastResult: null,
      },
    });
  });

  it("renders nothing when debug=false", () => {
    const { container } = render(<StreamDebugPanel debug={false} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders metrics when debug=true", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      wsUrl: "ws://localhost/ws/video/stream?pipeline_id=p1",
      currentPipelineId: "p1",
      state: {
        connectionStatus: "connected",
        framesSent: 10,
        startTime: performance.now() - 1000,
        droppedFrames: 2,
        slowDownWarnings: 1,
        lastFrameSizes: [1000, 1200],
        lastLatencies: [30, 40],
        currentFps: 15,
        lastResult: { frame_index: 42 },
      },
    });

    render(<StreamDebugPanel debug={true} />);

    expect(screen.getByText("Phase-17 Debug Panel")).toBeInTheDocument();
    expect(screen.getByText("Frames Sent: 10")).toBeInTheDocument();
    expect(screen.getByText("Dropped Frames: 2")).toBeInTheDocument();
    expect(screen.getByText("1000 bytes")).toBeInTheDocument();
    expect(screen.getByText("30.0 ms")).toBeInTheDocument();
    expect(screen.getByText("Last Frame Index: 42")).toBeInTheDocument();
  });

  it("displays connection status", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      wsUrl: "ws://localhost/ws/video/stream?pipeline_id=p1",
      currentPipelineId: "p1",
      state: {
        connectionStatus: "connecting",
        framesSent: 0,
        startTime: null,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastFrameSizes: [],
        lastLatencies: [],
        currentFps: 15,
        lastResult: null,
      },
    });

    render(<StreamDebugPanel debug={true} />);

    expect(screen.getByText("Status: connecting")).toBeInTheDocument();
  });

  it("displays pipeline ID", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      wsUrl: "ws://localhost/ws/video/stream?pipeline_id=test_pipeline",
      currentPipelineId: "test_pipeline",
      state: {
        connectionStatus: "connected",
        framesSent: 0,
        startTime: null,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastFrameSizes: [],
        lastLatencies: [],
        currentFps: 15,
        lastResult: null,
      },
    });

    render(<StreamDebugPanel debug={true} />);

    expect(screen.getByText("Pipeline: test_pipeline")).toBeInTheDocument();
  });

  it("displays WebSocket URL", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      wsUrl: "ws://localhost:8000/ws/video/stream?pipeline_id=p1",
      currentPipelineId: "p1",
      state: {
        connectionStatus: "connected",
        framesSent: 0,
        startTime: null,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastFrameSizes: [],
        lastLatencies: [],
        currentFps: 15,
        lastResult: null,
      },
    });

    render(<StreamDebugPanel debug={true} />);

    expect(screen.getByText(/ws:\/\/localhost:8000\/ws\/video\/stream/)).toBeInTheDocument();
  });

  it("calculates and displays FPS", () => {
    const startTime = performance.now() - 2000; // 2 seconds ago

    (useRealtimeContext as vi.Mock).mockReturnValue({
      wsUrl: "ws://localhost/ws/video/stream?pipeline_id=p1",
      currentPipelineId: "p1",
      state: {
        connectionStatus: "connected",
        framesSent: 30, // 30 frames in 2 seconds = 15 FPS
        startTime,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastFrameSizes: [],
        lastLatencies: [],
        currentFps: 15,
        lastResult: null,
      },
    });

    render(<StreamDebugPanel debug={true} />);

    expect(screen.getByText(/FPS \(approx\): 15\.0/)).toBeInTheDocument();
  });

  it("displays throttler FPS", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      wsUrl: "ws://localhost/ws/video/stream?pipeline_id=p1",
      currentPipelineId: "p1",
      state: {
        connectionStatus: "connected",
        framesSent: 0,
        startTime: null,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastFrameSizes: [],
        lastLatencies: [],
        currentFps: 5,
        lastResult: null,
      },
    });

    render(<StreamDebugPanel debug={true} />);

    expect(screen.getByText("Throttler FPS: 5")).toBeInTheDocument();
  });

  it("calculates and displays drop rate", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      wsUrl: "ws://localhost/ws/video/stream?pipeline_id=p1",
      currentPipelineId: "p1",
      state: {
        connectionStatus: "connected",
        framesSent: 100,
        startTime: null,
        droppedFrames: 10, // 10% drop rate
        slowDownWarnings: 0,
        lastFrameSizes: [],
        lastLatencies: [],
        currentFps: 15,
        lastResult: null,
      },
    });

    render(<StreamDebugPanel debug={true} />);

    expect(screen.getByText("Drop Rate: 10.0%")).toBeInTheDocument();
  });

  it("displays slow-down warnings", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      wsUrl: "ws://localhost/ws/video/stream?pipeline_id=p1",
      currentPipelineId: "p1",
      state: {
        connectionStatus: "connected",
        framesSent: 0,
        startTime: null,
        droppedFrames: 0,
        slowDownWarnings: 3,
        lastFrameSizes: [],
        lastLatencies: [],
        currentFps: 15,
        lastResult: null,
      },
    });

    render(<StreamDebugPanel debug={true} />);

    expect(screen.getByText("Slow-Down Warnings: 3")).toBeInTheDocument();
  });

  it("displays last 5 frame sizes", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      wsUrl: "ws://localhost/ws/video/stream?pipeline_id=p1",
      currentPipelineId: "p1",
      state: {
        connectionStatus: "connected",
        framesSent: 0,
        startTime: null,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastFrameSizes: [1000, 1200, 1500, 1800, 2000],
        lastLatencies: [],
        currentFps: 15,
        lastResult: null,
      },
    });

    render(<StreamDebugPanel debug={true} />);

    expect(screen.getByText("1000 bytes")).toBeInTheDocument();
    expect(screen.getByText("1200 bytes")).toBeInTheDocument();
    expect(screen.getByText("1500 bytes")).toBeInTheDocument();
    expect(screen.getByText("1800 bytes")).toBeInTheDocument();
    expect(screen.getByText("2000 bytes")).toBeInTheDocument();
  });

  it("limits frame sizes to last 5", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      wsUrl: "ws://localhost/ws/video/stream?pipeline_id=p1",
      currentPipelineId: "p1",
      state: {
        connectionStatus: "connected",
        framesSent: 0,
        startTime: null,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastFrameSizes: [1000, 1200, 1500, 1800, 2000, 2200, 2500], // 7 items, should show last 5
        lastLatencies: [],
        currentFps: 15,
        lastResult: null,
      },
    });

    render(<StreamDebugPanel debug={true} />);

    // Should only show last 5
    expect(screen.queryByText("1000 bytes")).toBeNull();
    expect(screen.getByText("1500 bytes")).toBeInTheDocument();
    expect(screen.getByText("2500 bytes")).toBeInTheDocument();
  });

  it("displays last 5 latencies", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      wsUrl: "ws://localhost/ws/video/stream?pipeline_id=p1",
      currentPipelineId: "p1",
      state: {
        connectionStatus: "connected",
        framesSent: 0,
        startTime: null,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastFrameSizes: [],
        lastLatencies: [25.5, 30.2, 35.8, 40.1, 45.0],
        currentFps: 15,
        lastResult: null,
      },
    });

    render(<StreamDebugPanel debug={true} />);

    expect(screen.getByText("25.5 ms")).toBeInTheDocument();
    expect(screen.getByText("30.2 ms")).toBeInTheDocument();
    expect(screen.getByText("35.8 ms")).toBeInTheDocument();
    expect(screen.getByText("40.1 ms")).toBeInTheDocument();
    expect(screen.getByText("45.0 ms")).toBeInTheDocument();
  });

  it("limits latencies to last 5", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      wsUrl: "ws://localhost/ws/video/stream?pipeline_id=p1",
      currentPipelineId: "p1",
      state: {
        connectionStatus: "connected",
        framesSent: 0,
        startTime: null,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastFrameSizes: [],
        lastLatencies: [20, 25, 30, 35, 40, 45, 50], // 7 items, should show last 5
        currentFps: 15,
        lastResult: null,
      },
    });

    render(<StreamDebugPanel debug={true} />);

    // Should only show last 5
    expect(screen.queryByText("20.0 ms")).toBeNull();
    expect(screen.getByText("30.0 ms")).toBeInTheDocument();
    expect(screen.getByText("50.0 ms")).toBeInTheDocument();
  });

  it("displays 'none' when no frame sizes", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      wsUrl: "ws://localhost/ws/video/stream?pipeline_id=p1",
      currentPipelineId: "p1",
      state: {
        connectionStatus: "connected",
        framesSent: 0,
        startTime: null,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastFrameSizes: [],
        lastLatencies: [],
        currentFps: 15,
        lastResult: null,
      },
    });

    render(<StreamDebugPanel debug={true} />);

    expect(screen.getAllByText("none")).toHaveLength(2); // frame sizes, latencies (lastResult "none" is part of a larger string)
  });

  it("displays 'none' when no latencies", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      wsUrl: "ws://localhost/ws/video/stream?pipeline_id=p1",
      currentPipelineId: "p1",
      state: {
        connectionStatus: "connected",
        framesSent: 0,
        startTime: null,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastFrameSizes: [],
        lastLatencies: [],
        currentFps: 15,
        lastResult: null,
      },
    });

    render(<StreamDebugPanel debug={true} />);

    // Should have two "none" entries (one for frame sizes, one for latencies)
    const noneElements = screen.getAllByText("none");
    expect(noneElements.length).toBeGreaterThanOrEqual(2);
  });

  it("displays 'none' when no last result", () => {
    (useRealtimeContext as vi.Mock).mockReturnValue({
      wsUrl: "ws://localhost/ws/video/stream?pipeline_id=p1",
      currentPipelineId: "p1",
      state: {
        connectionStatus: "connected",
        framesSent: 0,
        startTime: null,
        droppedFrames: 0,
        slowDownWarnings: 0,
        lastFrameSizes: [],
        lastLatencies: [],
        currentFps: 15,
        lastResult: null,
      },
    });

    render(<StreamDebugPanel debug={true} />);

    expect(screen.getByText("Last Frame Index: none")).toBeInTheDocument();
  });
});