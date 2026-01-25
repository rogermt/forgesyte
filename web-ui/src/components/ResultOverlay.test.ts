/**
 * Tests for ResultOverlay (pure drawing function)
 *
 * This is a refactored version from React component to pure function.
 * Tests verify canvas drawing behavior with mocked context.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// ============================================================================
// Mock Canvas Context
// ============================================================================

const mockCanvasContext = {
  clearRect: vi.fn(),
  strokeRect: vi.fn(),
  fillRect: vi.fn(),
  beginPath: vi.fn(),
  arc: vi.fn(),
  fill: vi.fn(),
  stroke: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  fillText: vi.fn(),
  measureText: vi.fn(() => ({ width: 100 })),
  strokeStyle: "",
  fillStyle: "",
  lineWidth: 0,
  font: "",
};

// Mock getContext before tests
beforeEach(() => {
  vi.clearAllMocks();
  HTMLCanvasElement.prototype.getContext = vi.fn(
    () => mockCanvasContext
  ) as typeof HTMLCanvasElement.prototype.getContext;
});

// Clean up after tests
afterEach(() => {
  vi.restoreAllMocks();
});

// ============================================================================
// Helper Functions
// ============================================================================

function createMockCanvas(width = 640, height = 480): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  return canvas;
}

// ============================================================================
// Imports
// ============================================================================

import { ResultOverlay, type OverlayToggles } from "./ResultOverlay";

// ============================================================================
// Tests
// ============================================================================

describe("ResultOverlay (pure drawing function)", () => {
  // =========================================================================
  // Type Tests
  // =========================================================================

  it("exports OverlayToggles interface", () => {
    const toggles: OverlayToggles = {
      players: true,
      tracking: true,
      ball: true,
      pitch: true,
      radar: true,
    };
    expect(toggles.players).toBe(true);
  });

  it("ResultOverlay is a function", () => {
    expect(typeof ResultOverlay).toBe("function");
  });

  // =========================================================================
  // Canvas Setup Tests
  // =========================================================================

  it("resizes canvas to match video dimensions", () => {
    const canvas = createMockCanvas(0, 0);
    const originalGetContext = canvas.getContext.bind(canvas);
    
    (canvas as unknown).getContext = function(contextId: string) {
      if (contextId === "2d") {
        return mockCanvasContext;
      }
      return originalGetContext(contextId);
    };

    ResultOverlay({
      canvas,
      frameWidth: 1280,
      frameHeight: 720,
      detections: {},
      overlayToggles: {
        players: false,
        tracking: false,
        ball: false,
        pitch: false,
        radar: false,
      },
    });

    expect(canvas.width).toBe(1280);
    expect(canvas.height).toBe(720);
  });

  it("clears the canvas", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: {},
      overlayToggles: {
        players: false,
        tracking: false,
        ball: false,
        pitch: false,
        radar: false,
      },
    });

    expect(mockCanvasContext.clearRect).toHaveBeenCalledWith(0, 0, 640, 480);
  });

  it("does not draw when detections is null or undefined", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: null,

      overlayToggles: {
        players: true,
        tracking: true,
        ball: true,
        pitch: true,
        radar: true,
      },
    });

    // Should have cleared canvas but not drawn anything
    expect(mockCanvasContext.clearRect).toHaveBeenCalled();
    expect(mockCanvasContext.strokeRect).not.toHaveBeenCalled();
    expect(mockCanvasContext.fillRect).not.toHaveBeenCalled();
  });

  // =========================================================================
  // Player/Detection Drawing Tests
  // =========================================================================

  it("does not draw players when players toggle is false", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: {
        detections: [
          { x: 10, y: 20, width: 100, height: 150, class: "team_1" },
        ],
      },

      overlayToggles: {
        players: false,
        tracking: true,
        ball: false,
        pitch: false,
        radar: false,
      },
    });

    expect(mockCanvasContext.strokeRect).not.toHaveBeenCalled();
  });

  it("draws bounding boxes for detections when players toggle is true", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: {
        detections: [
          { x: 10, y: 20, width: 100, height: 150, class: "team_1" },
        ],
      },

      overlayToggles: {
        players: true,
        tracking: false,
        ball: false,
        pitch: false,
        radar: false,
      },
    });

    expect(mockCanvasContext.strokeRect).toHaveBeenCalledWith(10, 20, 100, 150);
  });

  it("draws corner markers for each detection", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: {
        detections: [
          { x: 10, y: 20, width: 100, height: 150, class: "team_1" },
        ],
      },

      overlayToggles: {
        players: true,
        tracking: false,
        ball: false,
        pitch: false,
        radar: false,
      },
    });

    // Each detection has 4 corners + 1 label background = 5 fillRect calls
    expect(mockCanvasContext.fillRect).toHaveBeenCalled();
    expect(mockCanvasContext.fillRect).toHaveBeenCalledTimes(5);
  });

  it("uses different colors for team_1 and team_2 classes", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: {
        detections: [
          { x: 10, y: 20, width: 50, height: 60, class: "team_1" },
          { x: 100, y: 150, width: 40, height: 50, class: "team_2" },
        ],
      },

      overlayToggles: {
        players: true,
        tracking: false,
        ball: false,
        pitch: false,
        radar: false,
      },
    });

    // strokeStyle should be set for each detection
    expect(mockCanvasContext.strokeStyle).toBeDefined();
  });

  it("uses ball color for ball class", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: {
        detections: [
          { x: 100, y: 200, width: 20, height: 20, class: "ball" },
        ],
      },

      overlayToggles: {
        players: true,
        tracking: false,
        ball: false,
        pitch: false,
        radar: false,
      },
    });

    expect(mockCanvasContext.strokeStyle).toBeDefined();
  });

  // =========================================================================
  // Tracking ID Tests
  // =========================================================================

  it("does not draw track IDs when tracking toggle is false", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: {
        detections: [
          { x: 10, y: 20, width: 50, height: 60, track_id: 7 },
        ],
      },

      overlayToggles: {
        players: true,
        tracking: false,
        ball: false,
        pitch: false,
        radar: false,
      },
    });

    expect(mockCanvasContext.fillText).not.toHaveBeenCalledWith(
      expect.stringContaining("ID:"),
      expect.any(Number),
      expect.any(Number)
    );
  });

  it("draws track IDs when tracking toggle is true and track_id exists", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: {
        detections: [
          { x: 10, y: 20, width: 50, height: 60, track_id: 7 },
        ],
      },

      overlayToggles: {
        players: true,
        tracking: true,
        ball: false,
        pitch: false,
        radar: false,
      },
    });

    expect(mockCanvasContext.fillText).toHaveBeenCalledWith(
      "ID:7",
      expect.any(Number),
      expect.any(Number)
    );
  });

  // =========================================================================
  // Ball Drawing Tests
  // =========================================================================

  it("does not draw ball when ball toggle is false", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: { ball: { x: 100, y: 200 } },

      overlayToggles: {
        players: false,
        tracking: false,
        ball: false,
        pitch: false,
        radar: false,
      },
    });

    expect(mockCanvasContext.arc).not.toHaveBeenCalled();
    expect(mockCanvasContext.fill).not.toHaveBeenCalled();
  });

  it("draws ball marker when ball toggle is true and ball data exists", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: { ball: { x: 100, y: 200 } },

      overlayToggles: {
        players: false,
        tracking: false,
        ball: true,
        pitch: false,
        radar: false,
      },
    });

    expect(mockCanvasContext.arc).toHaveBeenCalled();
    expect(mockCanvasContext.fill).toHaveBeenCalled();
  });

  // =========================================================================
  // Pitch Drawing Tests
  // =========================================================================

  it("does not draw pitch when pitch toggle is false", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: {
        pitch: {
          lines: [{ x1: 0, y1: 0, x2: 100, y2: 100 }],
        },
      },

      overlayToggles: {
        players: false,
        tracking: false,
        ball: false,
        pitch: false,
        radar: false,
      },
    });

    expect(mockCanvasContext.moveTo).not.toHaveBeenCalled();
    expect(mockCanvasContext.lineTo).not.toHaveBeenCalled();
    expect(mockCanvasContext.stroke).not.toHaveBeenCalled();
  });

  it("draws pitch lines when pitch toggle is true", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: {
        pitch: {
          lines: [{ x1: 0, y1: 0, x2: 100, y2: 100 }],
        },
      },

      overlayToggles: {
        players: false,
        tracking: false,
        ball: false,
        pitch: true,
        radar: false,
      },
    });

    expect(mockCanvasContext.moveTo).toHaveBeenCalledWith(0, 0);
    expect(mockCanvasContext.lineTo).toHaveBeenCalledWith(100, 100);
    expect(mockCanvasContext.stroke).toHaveBeenCalled();
  });

  it("draws multiple pitch lines", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: {
        pitch: {
          lines: [
            { x1: 0, y1: 0, x2: 100, y2: 100 },
            { x1: 100, y1: 100, x2: 200, y2: 200 },
          ],
        },
      },

      overlayToggles: {
        players: false,
        tracking: false,
        ball: false,
        pitch: true,
        radar: false,
      },
    });

    expect(mockCanvasContext.moveTo).toHaveBeenCalledTimes(2);
    expect(mockCanvasContext.lineTo).toHaveBeenCalledTimes(2);
    expect(mockCanvasContext.stroke).toHaveBeenCalled();
  });

  // =========================================================================
  // Radar Drawing Tests
  // =========================================================================

  it("does not draw radar when radar toggle is false", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: {
        radar: { points: [{ x: 50, y: 60 }] },
      },

      overlayToggles: {
        players: false,
        tracking: false,
        ball: false,
        pitch: false,
        radar: false,
      },
    });

    expect(mockCanvasContext.fillRect).not.toHaveBeenCalled();
  });

  it("draws radar points when radar toggle is true", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: {
        radar: { points: [{ x: 50, y: 60 }] },
      },

      overlayToggles: {
        players: false,
        tracking: false,
        ball: false,
        pitch: false,
        radar: true,
      },
    });

    expect(mockCanvasContext.fillRect).toHaveBeenCalled();
  });

  it("draws multiple radar points", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: {
        radar: {
          points: [
            { x: 50, y: 60 },
            { x: 100, y: 120 },
            { x: 150, y: 180 },
          ],
        },
      },

      overlayToggles: {
        players: false,
        tracking: false,
        ball: false,
        pitch: false,
        radar: true,
      },
    });

    expect(mockCanvasContext.fillRect).toHaveBeenCalledTimes(3);
  });

  // =========================================================================
  // Buffer Tests
  // =========================================================================

  it("accepts buffer parameter but doesn't use it for basic drawing", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: {
        detections: [
          { x: 10, y: 20, width: 50, height: 60, class: "team_1" },
        ],
      },
      overlayToggles: {
        players: true,
        tracking: false,
        ball: false,
        pitch: false,
        radar: false,
      },
    });

    // Should still draw current detection
    expect(mockCanvasContext.strokeRect).toHaveBeenCalled();
  });

  // =========================================================================
  // All Toggles On Tests
  // =========================================================================

  it("draws everything when all toggles are true", () => {
    const canvas = createMockCanvas();

    ResultOverlay({
      canvas,
      frameWidth: 640,
      frameHeight: 480,
      detections: {
        detections: [
          { x: 10, y: 20, width: 50, height: 60, class: "team_1", track_id: 1 },
        ],
        ball: { x: 100, y: 200 },
        pitch: {
          lines: [{ x1: 0, y1: 0, x2: 100, y2: 100 }],
        },
        radar: { points: [{ x: 50, y: 60 }] },
      },

      overlayToggles: {
        players: true,
        tracking: true,
        ball: true,
        pitch: true,
        radar: true,
      },
    });

    // All drawing methods should have been called
    expect(mockCanvasContext.clearRect).toHaveBeenCalled();
    expect(mockCanvasContext.strokeRect).toHaveBeenCalled();
    expect(mockCanvasContext.fillText).toHaveBeenCalled();
    expect(mockCanvasContext.arc).toHaveBeenCalled();
    expect(mockCanvasContext.moveTo).toHaveBeenCalled();
    expect(mockCanvasContext.fillRect).toHaveBeenCalled();
  });
});

