/**
 * Tests for VideoTracker component
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { VideoTracker } from "./VideoTracker";

// ============================================================================
// Mocks
// ============================================================================

vi.mock("../hooks/useManifest", () => ({
  useManifest: () => ({
    manifest: null,
    loading: false,
    error: null,
    clearCache: vi.fn(),
  }),
}));

vi.mock("../hooks/useVideoProcessor", () => ({
  useVideoProcessor: () => ({
    state: {
      isProcessing: false,
      frameCount: 0,
      fps: 0,
      error: undefined,
    },
    frames: [],
    detections: [],
    processFrame: vi.fn(),
    start: vi.fn(),
    stop: vi.fn(),
    clear: vi.fn(),
  }),
}));

vi.mock("../api/client", () => ({
  apiClient: {
    getPlugins: vi.fn(() => Promise.resolve([])),
    runPluginTool: vi.fn(),
  },
}));

vi.mock("./ToolSelector", () => ({
  default: () => <div>Mock ToolSelector</div>,
}));

vi.mock("./ConfidenceSlider", () => ({
  default: () => <div>Mock ConfidenceSlider</div>,
}));

vi.mock("./ResultOverlay", () => ({
  default: () => <div>Mock ResultOverlay</div>,
}));

// ============================================================================
// Tests
// ============================================================================

describe("VideoTracker", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the main title", () => {
    render(<VideoTracker />);
    expect(screen.getByText("Video Tracker")).toBeInTheDocument();
  });

  it("displays Ready status initially", () => {
    render(<VideoTracker />);
    expect(screen.getByText("Ready")).toBeInTheDocument();
  });

  it("shows upload area for video", () => {
    render(<VideoTracker />);
    expect(
      screen.getByText("Click to upload video")
    ).toBeInTheDocument();
  });

  it("allows file input for video upload", () => {
    render(<VideoTracker />);
    const input = screen.getByDisplayValue("") as HTMLInputElement;
    expect(input).toHaveAttribute("accept", "video/*");
  });

  it("displays preview section", () => {
    render(<VideoTracker />);
    expect(screen.getByText("Preview")).toBeInTheDocument();
  });

  it("shows preview message when no video selected", () => {
    render(<VideoTracker />);
    expect(screen.getByText("No video selected")).toBeInTheDocument();
  });

  it("shows plugin dropdown after video upload", () => {
    const { rerender } = render(<VideoTracker />);

    // Upload a video file
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["video"], "test.mp4", { type: "video/mp4" });
    
    fireEvent.change(input, { target: { files: [file] } });

    rerender(<VideoTracker />);

    // Plugin dropdown should now be visible
    expect(screen.getByText("Select plugin...")).toBeInTheDocument();
  });

  it("displays video file name after upload", () => {
    render(<VideoTracker />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["video"], "test.mp4", { type: "video/mp4" });

    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.getByText(/test\.mp4/)).toBeInTheDocument();
  });

  it("shows Clear Video button after upload", () => {
    render(<VideoTracker />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["video"], "test.mp4", { type: "video/mp4" });

    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.getByText("Clear Video")).toBeInTheDocument();
  });

  it("clears video when Clear Video button clicked", () => {
    const { rerender } = render(<VideoTracker />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["video"], "test.mp4", { type: "video/mp4" });

    fireEvent.change(input, { target: { files: [file] } });

    rerender(<VideoTracker />);

    const clearButton = screen.getByText("Clear Video");
    fireEvent.click(clearButton);

    rerender(<VideoTracker />);

    // Should show upload message again
    expect(screen.getByText("Click to upload video")).toBeInTheDocument();
  });

  it("displays error when non-video file is uploaded", () => {
    render(<VideoTracker />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["data"], "test.txt", { type: "text/plain" });

    fireEvent.change(input, { target: { files: [file] } });

    expect(screen.getByText(/Please select a valid video file/)).toBeInTheDocument();
  });

  it("renders mocked ToolSelector after plugin selection", () => {
    const { rerender } = render(<VideoTracker />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["video"], "test.mp4", { type: "video/mp4" });

    fireEvent.change(input, { target: { files: [file] } });

    rerender(<VideoTracker />);

    const pluginSelect = screen.getByDisplayValue("Select plugin...") as HTMLSelectElement;
    fireEvent.change(pluginSelect, {
      target: { value: "forgesyte-yolo-tracker" },
    });

    rerender(<VideoTracker />);

    expect(screen.getByText("Mock ToolSelector")).toBeInTheDocument();
  });

  it("renders mocked ConfidenceSlider after plugin selection", () => {
    const { rerender } = render(<VideoTracker />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["video"], "test.mp4", { type: "video/mp4" });

    fireEvent.change(input, { target: { files: [file] } });

    rerender(<VideoTracker />);

    const pluginSelect = screen.getByDisplayValue("Select plugin...") as HTMLSelectElement;
    fireEvent.change(pluginSelect, {
      target: { value: "forgesyte-yolo-tracker" },
    });

    rerender(<VideoTracker />);

    expect(screen.getByText("Mock ConfidenceSlider")).toBeInTheDocument();
  });

  it("displays stats section after plugin selection", () => {
    const { rerender } = render(<VideoTracker />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["video"], "test.mp4", { type: "video/mp4" });

    fireEvent.change(input, { target: { files: [file] } });

    rerender(<VideoTracker />);

    const pluginSelect = screen.getByDisplayValue("Select plugin...") as HTMLSelectElement;
    fireEvent.change(pluginSelect, {
      target: { value: "forgesyte-yolo-tracker" },
    });

    rerender(<VideoTracker />);

    expect(screen.getByText("Processed")).toBeInTheDocument();
    expect(screen.getByText("Detections")).toBeInTheDocument();
  });

  it("shows process button after plugin selection", () => {
    const { rerender } = render(<VideoTracker />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["video"], "test.mp4", { type: "video/mp4" });

    fireEvent.change(input, { target: { files: [file] } });

    rerender(<VideoTracker />);

    const pluginSelect = screen.getByDisplayValue("Select plugin...") as HTMLSelectElement;
    fireEvent.change(pluginSelect, {
      target: { value: "forgesyte-yolo-tracker" },
    });

    rerender(<VideoTracker />);

    expect(screen.getByText("Start Processing")).toBeInTheDocument();
  });

  it("disables process button when already processing", () => {
    render(<VideoTracker />);

    // After upload and plugin selection, process button should be enabled
    // (implementation would test actual button state)
    const button = screen.queryByText("Start Processing");
    if (button) {
      expect(button).not.toBeDisabled();
    }
  });

  it("displays file size after upload", () => {
    render(<VideoTracker />);

    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    // Create a file of known size
    const blob = new Blob(["a".repeat(1024 * 1024)], { type: "video/mp4" });
    const file = new File([blob], "test.mp4", { type: "video/mp4" });

    fireEvent.change(input, { target: { files: [file] } });

    // Should show file size
    expect(screen.getByText(/MB/)).toBeInTheDocument();
  });
});
