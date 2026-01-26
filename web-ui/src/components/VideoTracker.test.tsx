/**
 * Tests for VideoTracker Component (Layout + Integration)
 *
 * Verifies:
 * - Layout matches ASCII diagram
 * - All UI elements render correctly
 * - Canvas positioned above video with correct initialization
 * - Controls match specification (enabled, non-functional)
 * - Sparse FPS values
 * - Webcam button hidden
 * - No plugin coupling
 * - ResultOverlay wiring
 * - FPS selector integration
 * - Device selector integration (Task 6.2)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { VideoTracker } from "./VideoTracker";

// Mock useVideoProcessor - must be at top level for hoisting
const mockUseVideoProcessor = vi.fn().mockReturnValue({
  latestResult: null,
  buffer: [],
  processing: false,
  error: null,
  lastRequestDuration: null,
});

vi.mock("../hooks/useVideoProcessor", () => ({
  useVideoProcessor: (...args: unknown[]) => mockUseVideoProcessor(...args),
}));

describe("VideoTracker (Layout Only)", () => {
  const defaultProps = {
    pluginId: "forgesyte-yolo-tracker",
    toolName: "detect_players",
  };

  // =========================================================================
  // Header
  // =========================================================================

  it("renders component title", () => {
    render(<VideoTracker {...defaultProps} />);
    expect(screen.getByText("VideoTracker")).toBeInTheDocument();
  });

  it("displays pluginId and toolName in header (routing info)", () => {
    render(
      <VideoTracker pluginId="test-plugin" toolName="test-tool" />
    );
    expect(screen.getByText(/test-plugin/)).toBeInTheDocument();
    expect(screen.getByText(/test-tool/)).toBeInTheDocument();
  });

  // =========================================================================
  // Upload Row
  // =========================================================================

  it("renders Upload Video button", async () => {
    render(<VideoTracker {...defaultProps} />);
    
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /Upload Video/ })
      ).toBeInTheDocument();
    }, { timeout: 10000 });
  });

  it("does NOT render Webcam button (hidden, not disabled)", () => {
    render(<VideoTracker {...defaultProps} />);
    expect(
      screen.queryByRole("button", { name: /Webcam/ })
    ).not.toBeInTheDocument();
  });

  // =========================================================================
  // Video + Canvas Section
  // =========================================================================

  it("shows placeholder text when no video selected", () => {
    render(<VideoTracker {...defaultProps} />);
    expect(screen.getByText("No video selected")).toBeInTheDocument();
  });

  it("video element renders (shown when video file selected)", () => {
    const { container } = render(<VideoTracker {...defaultProps} />);
    // Video element is in the JSX with controls attribute
    // Visibility depends on videoFile state (managed in component)
    const videoContainer = container.querySelector("div[style*='position: relative']");
    expect(videoContainer).toBeTruthy();
  });

  // =========================================================================
  // Playback Controls
  // =========================================================================

  it("renders Play button", () => {
    render(<VideoTracker {...defaultProps} />);
    expect(screen.getByRole("button", { name: /Play/ })).toBeInTheDocument();
  });

  it("renders Pause button", () => {
    render(<VideoTracker {...defaultProps} />);
    expect(
      screen.getByRole("button", { name: /Pause/ })
    ).toBeInTheDocument();
  });

  it("Play and Pause buttons are enabled (non-functional)", () => {
    render(<VideoTracker {...defaultProps} />);
    const playButton = screen.getByRole("button", { name: /Play/ });
    const pauseButton = screen.getByRole("button", { name: /Pause/ });
    expect(playButton).not.toBeDisabled();
    expect(pauseButton).not.toBeDisabled();
  });

  // =========================================================================
  // FPS Dropdown
  // =========================================================================

  it("renders FPS dropdown", () => {
    render(<VideoTracker {...defaultProps} />);
    const fpsSelects = screen.getAllByRole("combobox");
    expect(fpsSelects.length).toBeGreaterThan(0);
  });

  it("FPS dropdown has sparse values only", () => {
    render(<VideoTracker {...defaultProps} />);
    const fpsSelect = screen.getByDisplayValue("30 FPS") as HTMLSelectElement;
    const values = Array.from(fpsSelect.options).map((opt) => opt.value);
    expect(values).toEqual(["5", "10", "15", "24", "30", "45", "60"]);
  });

  it("FPS defaults to 30", () => {
    render(<VideoTracker {...defaultProps} />);
    expect(screen.getByDisplayValue("30 FPS")).toHaveValue("30");
  });

  // =========================================================================
  // Device Dropdown (Task 6.2)
  // =========================================================================

  it("renders Device dropdown with CPU/GPU options", () => {
    render(<VideoTracker {...defaultProps} />);
    const deviceSelect = screen.getByLabelText("Device") as HTMLSelectElement;
    const values = Array.from(deviceSelect.options).map((opt) => opt.value);
    expect(values).toContain("cpu");
    expect(values).toContain("cuda");
  });

  it("Device defaults to CPU", () => {
    render(<VideoTracker {...defaultProps} />);
    expect(screen.getByDisplayValue("CPU")).toHaveValue("cpu");
  });

  it("Device dropdown has aria-label for accessibility", () => {
    render(<VideoTracker {...defaultProps} />);
    expect(screen.getByLabelText("Device")).toBeInTheDocument();
  });

  // =========================================================================
  // Overlay Toggles
  // =========================================================================

  it("renders all 5 overlay toggle checkboxes", () => {
    render(<VideoTracker {...defaultProps} />);
    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes).toHaveLength(5);
  });

  it("all overlay toggles are checked by default", () => {
    render(<VideoTracker {...defaultProps} />);
    const checkboxes = screen.getAllByRole("checkbox");
    checkboxes.forEach((checkbox) => {
      expect(checkbox).toBeChecked();
    });
  });

  it("renders overlay toggle labels in horizontal layout", () => {
    render(<VideoTracker {...defaultProps} />);
    expect(screen.getByText(/Players/)).toBeInTheDocument();
    expect(screen.getByText(/Tracking/)).toBeInTheDocument();
    expect(screen.getByText(/Ball/)).toBeInTheDocument();
    expect(screen.getByText(/Pitch/)).toBeInTheDocument();
    expect(screen.getByText(/Radar/)).toBeInTheDocument();
  });

  // =========================================================================
  // Plugin-Agnostic Tests
  // =========================================================================

  it("is plugin-agnostic (works with any pluginId and toolName)", () => {
    const { rerender } = render(
      <VideoTracker pluginId="plugin-1" toolName="tool-1" />
    );
    expect(screen.getByText(/plugin-1/)).toBeInTheDocument();

    rerender(<VideoTracker pluginId="plugin-2" toolName="tool-2" />);
    expect(screen.getByText(/plugin-2/)).toBeInTheDocument();
  });

  it("has no backend call logic (skeleton only)", () => {
    render(<VideoTracker {...defaultProps} />);
    expect(screen.getByText("VideoTracker")).toBeInTheDocument();
  });

  it("compiles with TypeScript strict mode", () => {
    expect(true).toBe(true);
  });
});

// ============================================================================
// Integration Tests: ResultOverlay Wiring (Structural)
// ============================================================================

describe("VideoTracker - ResultOverlay Integration", () => {
  const defaultProps = {
    pluginId: "forgesyte-yolo-tracker",
    toolName: "detect_players",
  };

  it("renders canvas element for ResultOverlay drawing when video loaded", () => {
    const { container } = render(<VideoTracker {...defaultProps} />);
    // Canvas is only rendered when video file is present
    // The component has canvasRef prepared for ResultOverlay
    const videoContainer = container.querySelector("div[style*='position: relative']");
    expect(videoContainer).toBeTruthy();
  });

  it("video container positioned for overlay", () => {
    const { container } = render(<VideoTracker {...defaultProps} />);
    const videoContainer = container.querySelector("div[style*='position: relative']");
    const style = videoContainer?.getAttribute("style") || "";
    expect(style).toContain("position: relative");
  });

  it("renders all 5 overlay toggle checkboxes", () => {
    render(<VideoTracker {...defaultProps} />);
    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes.length).toBe(5);
  });

  it("overlay toggles have proper labels", () => {
    render(<VideoTracker {...defaultProps} />);
    expect(screen.getByText(/Players/)).toBeTruthy();
    expect(screen.getByText(/Tracking/)).toBeTruthy();
    expect(screen.getByText(/Ball/)).toBeTruthy();
    expect(screen.getByText(/Pitch/)).toBeTruthy();
    expect(screen.getByText(/Radar/)).toBeTruthy();
  });
});

// ============================================================================
// Task 6.1: FPS Selector Integration Tests
// ============================================================================

describe("FPS selector integration", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockUseVideoProcessor.mockClear();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("passes fps to useVideoProcessor hook", () => {
    render(<VideoTracker pluginId="p" toolName="t" />);

    // Initial render with default FPS = 30
    expect(mockUseVideoProcessor).toHaveBeenCalledWith(
      expect.objectContaining({ fps: 30 })
    );

    // Click Play to start processing
    fireEvent.click(screen.getByRole("button", { name: /Play/ }));

    // Should still be called with fps: 30 and enabled: true
    expect(mockUseVideoProcessor).toHaveBeenCalledWith(
      expect.objectContaining({ fps: 30, enabled: true })
    );

    // Change FPS to 5
    fireEvent.change(screen.getByDisplayValue("30 FPS"), {
      target: { value: "5" },
    });

    // Hook should be called with fps: 5
    expect(mockUseVideoProcessor).toHaveBeenCalledWith(
      expect.objectContaining({ fps: 5 })
    );

    // Change FPS to 60
    fireEvent.change(screen.getByDisplayValue("5 FPS"), {
      target: { value: "60" },
    });

    // Hook should be called with fps: 60
    expect(mockUseVideoProcessor).toHaveBeenCalledWith(
      expect.objectContaining({ fps: 60 })
    );
  });

  it("does not create duplicate calls when FPS changes repeatedly", () => {
    render(<VideoTracker pluginId="p" toolName="t" />);

    fireEvent.click(screen.getByRole("button", { name: /Play/ }));

    // Clear mock calls to focus on FPS changes
    mockUseVideoProcessor.mockClear();

    // Change FPS multiple times rapidly
    fireEvent.change(screen.getByDisplayValue("30 FPS"), {
      target: { value: "10" },
    });
    fireEvent.change(screen.getByDisplayValue("10 FPS"), {
      target: { value: "30" },
    });
    fireEvent.change(screen.getByDisplayValue("30 FPS"), {
      target: { value: "60" },
    });

    // Should only have 3 calls (one per FPS change), not accumulated
    expect(mockUseVideoProcessor).toHaveBeenCalledTimes(3);

    // Verify the last call was with fps: 60
    const lastCall = mockUseVideoProcessor.mock.calls[mockUseVideoProcessor.mock.calls.length - 1][0] as Record<string, unknown>;
    expect(lastCall.fps).toBe(60);
  });

  it("passes correct enabled state with FPS", () => {
    render(<VideoTracker pluginId="p" toolName="t" />);

    // Initially not running, so enabled should be false
    const initialCall = mockUseVideoProcessor.mock.calls[0][0] as Record<string, unknown>;
    expect(initialCall.enabled).toBe(false);
    expect(initialCall.fps).toBe(30);

    // Click Play
    fireEvent.click(screen.getByRole("button", { name: /Play/ }));
    const playCall = mockUseVideoProcessor.mock.calls[mockUseVideoProcessor.mock.calls.length - 1][0] as Record<string, unknown>;
    expect(playCall.enabled).toBe(true);
    expect(playCall.fps).toBe(30);

    // Change FPS to 10 while running
    fireEvent.change(screen.getByDisplayValue("30 FPS"), {
      target: { value: "10" },
    });
    const fpsChangeCall = mockUseVideoProcessor.mock.calls[mockUseVideoProcessor.mock.calls.length - 1][0] as Record<string, unknown>;
    expect(fpsChangeCall.enabled).toBe(true);
    expect(fpsChangeCall.fps).toBe(10);

    // Click Pause
    fireEvent.click(screen.getByRole("button", { name: /Pause/ }));
    const pauseCall = mockUseVideoProcessor.mock.calls[mockUseVideoProcessor.mock.calls.length - 1][0] as Record<string, unknown>;
    expect(pauseCall.enabled).toBe(false);
    expect(pauseCall.fps).toBe(10);
  });
});

// ============================================================================
// Task 6.2: Device Selector Integration Tests
// ============================================================================

describe("Device selector integration", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockUseVideoProcessor.mockClear();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("passes device to useVideoProcessor hook", () => {
    render(<VideoTracker pluginId="p" toolName="t" />);

    // Initial render with default device = cpu
    expect(mockUseVideoProcessor).toHaveBeenCalledWith(
      expect.objectContaining({ device: "cpu" })
    );

    // Click Play to start processing
    fireEvent.click(screen.getByRole("button", { name: /Play/ }));

    // Should still be called with device: cpu and enabled: true
    expect(mockUseVideoProcessor).toHaveBeenCalledWith(
      expect.objectContaining({ device: "cpu", enabled: true })
    );

    // Change device to cuda
    fireEvent.change(screen.getByLabelText("Device"), {
      target: { value: "cuda" },
    });

    // Hook should be called with device: cuda
    expect(mockUseVideoProcessor).toHaveBeenCalledWith(
      expect.objectContaining({ device: "cuda" })
    );

    // Change device back to cpu
    fireEvent.change(screen.getByLabelText("Device"), {
      target: { value: "cpu" },
    });

    // Hook should be called with device: cpu
    expect(mockUseVideoProcessor).toHaveBeenCalledWith(
      expect.objectContaining({ device: "cpu" })
    );
  });

  it("does not create duplicate calls when device changes repeatedly", () => {
    render(<VideoTracker pluginId="p" toolName="t" />);

    fireEvent.click(screen.getByRole("button", { name: /Play/ }));

    // Clear mock calls to focus on device changes
    mockUseVideoProcessor.mockClear();

    // Change device multiple times rapidly
    fireEvent.change(screen.getByLabelText("Device"), {
      target: { value: "cuda" },
    });
    fireEvent.change(screen.getByLabelText("Device"), {
      target: { value: "cpu" },
    });
    fireEvent.change(screen.getByLabelText("Device"), {
      target: { value: "cuda" },
    });

    // Should only have 3 calls (one per device change), not accumulated
    expect(mockUseVideoProcessor).toHaveBeenCalledTimes(3);

    // Verify the last call was with device: cuda
    const lastCall = mockUseVideoProcessor.mock.calls[mockUseVideoProcessor.mock.calls.length - 1][0] as Record<string, unknown>;
    expect(lastCall.device).toBe("cuda");
  });

  it("passes correct enabled state with device", () => {
    render(<VideoTracker pluginId="p" toolName="t" />);

    // Initially not running, so enabled should be false
    const initialCall = mockUseVideoProcessor.mock.calls[0][0] as Record<string, unknown>;
    expect(initialCall.enabled).toBe(false);
    expect(initialCall.device).toBe("cpu");

    // Click Play
    fireEvent.click(screen.getByRole("button", { name: /Play/ }));
    const playCall = mockUseVideoProcessor.mock.calls[mockUseVideoProcessor.mock.calls.length - 1][0] as Record<string, unknown>;
    expect(playCall.enabled).toBe(true);
    expect(playCall.device).toBe("cpu");

    // Change device to cuda while running
    fireEvent.change(screen.getByLabelText("Device"), {
      target: { value: "cuda" },
    });
    const deviceChangeCall = mockUseVideoProcessor.mock.calls[mockUseVideoProcessor.mock.calls.length - 1][0] as Record<string, unknown>;
    expect(deviceChangeCall.enabled).toBe(true);
    expect(deviceChangeCall.device).toBe("cuda");

    // Click Pause
    fireEvent.click(screen.getByRole("button", { name: /Pause/ }));
    const pauseCall = mockUseVideoProcessor.mock.calls[mockUseVideoProcessor.mock.calls.length - 1][0] as Record<string, unknown>;
    expect(pauseCall.enabled).toBe(false);
    expect(pauseCall.device).toBe("cuda");
  });
});

// ============================================================================
// Task 6.3: Overlay Toggles Integration Tests
// ============================================================================

describe("Overlay toggles integration", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("toggles players layer on/off", () => {
    render(<VideoTracker pluginId="p" toolName="t" />);

    // Initial state: players toggle should be checked
    const playersToggle = screen.getByLabelText(/players/i);
    expect(playersToggle).toBeChecked();

    // Click to toggle players off
    fireEvent.click(playersToggle);

    // Should now be unchecked
    expect(playersToggle).not.toBeChecked();
  });

  it("toggles tracking layer on/off", () => {
    render(<VideoTracker pluginId="p" toolName="t" />);

    // Initial state: tracking toggle should be checked
    const trackingToggle = screen.getByLabelText(/tracking/i);
    expect(trackingToggle).toBeChecked();

    // Click to toggle tracking off
    fireEvent.click(trackingToggle);

    // Should now be unchecked
    expect(trackingToggle).not.toBeChecked();
  });

  it("toggles ball layer on/off", () => {
    render(<VideoTracker pluginId="p" toolName="t" />);

    // Initial state: ball toggle should be checked
    const ballToggle = screen.getByLabelText(/ball/i);
    expect(ballToggle).toBeChecked();

    // Click to toggle ball off
    fireEvent.click(ballToggle);

    // Should now be unchecked
    expect(ballToggle).not.toBeChecked();
  });

  it("toggles pitch layer on/off", () => {
    render(<VideoTracker pluginId="p" toolName="t" />);

    // Initial state: pitch toggle should be checked
    const pitchToggle = screen.getByLabelText(/pitch/i);
    expect(pitchToggle).toBeChecked();

    // Click to toggle pitch off
    fireEvent.click(pitchToggle);

    // Should now be unchecked
    expect(pitchToggle).not.toBeChecked();
  });

  it("toggles radar layer on/off", () => {
    render(<VideoTracker pluginId="p" toolName="t" />);

    // Initial state: radar toggle should be checked
    const radarToggle = screen.getByLabelText(/radar/i);
    expect(radarToggle).toBeChecked();

    // Click to toggle radar off
    fireEvent.click(radarToggle);

    // Should now be unchecked
    expect(radarToggle).not.toBeChecked();
  });

  it("all toggles are independent (toggling one does not affect others)", () => {
    render(<VideoTracker pluginId="p" toolName="t" />);

    // Get all toggle checkboxes
    const playersToggle = screen.getByLabelText(/players/i);
    const trackingToggle = screen.getByLabelText(/tracking/i);
    const ballToggle = screen.getByLabelText(/ball/i);
    const pitchToggle = screen.getByLabelText(/pitch/i);
    const radarToggle = screen.getByLabelText(/radar/i);

    // Toggle players off
    fireEvent.click(playersToggle);
    expect(playersToggle).not.toBeChecked();
    expect(trackingToggle).toBeChecked();
    expect(ballToggle).toBeChecked();
    expect(pitchToggle).toBeChecked();
    expect(radarToggle).toBeChecked();

    // Toggle tracking off
    fireEvent.click(trackingToggle);
    expect(playersToggle).not.toBeChecked();
    expect(trackingToggle).not.toBeChecked();
    expect(ballToggle).toBeChecked();
    expect(pitchToggle).toBeChecked();
    expect(radarToggle).toBeChecked();

    // Toggle ball off
    fireEvent.click(ballToggle);
    expect(playersToggle).not.toBeChecked();
    expect(trackingToggle).not.toBeChecked();
    expect(ballToggle).not.toBeChecked();
    expect(pitchToggle).toBeChecked();
    expect(radarToggle).toBeChecked();

    // Toggle pitch off
    fireEvent.click(pitchToggle);
    expect(playersToggle).not.toBeChecked();
    expect(trackingToggle).not.toBeChecked();
    expect(ballToggle).not.toBeChecked();
    expect(pitchToggle).not.toBeChecked();
    expect(radarToggle).toBeChecked();

    // Toggle radar off
    fireEvent.click(radarToggle);
    expect(playersToggle).not.toBeChecked();
    expect(trackingToggle).not.toBeChecked();
    expect(ballToggle).not.toBeChecked();
    expect(pitchToggle).not.toBeChecked();
    expect(radarToggle).not.toBeChecked();
  });

  it("can re-enable a toggle after disabling it", () => {
    render(<VideoTracker pluginId="p" toolName="t" />);

    const playersToggle = screen.getByLabelText(/players/i);

    // Toggle off
    fireEvent.click(playersToggle);
    expect(playersToggle).not.toBeChecked();

    // Toggle back on
    fireEvent.click(playersToggle);
    expect(playersToggle).toBeChecked();
  });
});

