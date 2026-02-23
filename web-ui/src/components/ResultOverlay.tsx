/**
 * Result Overlay Component (Plugin-Agnostic for v0.9.4)
 * Draws simple bounding boxes and labels on canvas.
 *
 * Best Practices Applied:
 * - [BP-1] Canvas rendering with proper cleanup
 * - [BP-2] useEffect for animation frames
 * - [BP-4] Proper canvas sizing to match video dimensions
 */

import { useEffect, useRef } from "react";
import type { Detection } from "../types/plugin";

// ============================================================================
// Types
// ============================================================================

export interface ResultOverlayProps {
  /** Canvas dimensions */
  width: number;
  height: number;
  /** Current detections to draw */
  detections: Detection[];
  /** Font size for labels */
  fontSize?: number;
}

// ============================================================================
// Color
// ============================================================================

const BOX_COLOR = "#00BFFF"; // Cyan

// ============================================================================
// Utility Function: Draw detections on canvas (generic, plugin-agnostic)
// ============================================================================

export function drawDetections(
  canvas: HTMLCanvasElement,
  detections: Detection[],
  fontSize = 12
): void {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const canvasWidth = canvas.width;
  const canvasHeight = canvas.height;

  // Clear canvas
  ctx.clearRect(0, 0, canvasWidth, canvasHeight);

  // Draw detections (generic bounding boxes + labels)
  detections.forEach((detection) => {
    ctx.strokeStyle = BOX_COLOR;
    ctx.lineWidth = 2;
    ctx.strokeRect(detection.x, detection.y, detection.width, detection.height);

    // Draw label
    if (detection.class) {
      const label = detection.class.replace(/_/g, " ");
      ctx.font = `bold ${fontSize}px monospace`;
      ctx.fillStyle = BOX_COLOR;
      const metrics = ctx.measureText(label);
      const textHeight = fontSize + 4;

      // Semi-transparent background
      ctx.fillStyle = "rgba(0,0,0,0.7)";
      ctx.fillRect(
        detection.x,
        detection.y - textHeight,
        metrics.width + 8,
        textHeight
      );

      // Text
      ctx.fillStyle = BOX_COLOR;
      ctx.fillText(label, detection.x + 4, detection.y - 6);
    }
  });
}

// ============================================================================
// Component
// ============================================================================

export function ResultOverlay({
  width,
  height,
  detections,
  fontSize = 12,
}: ResultOverlayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    drawDetections(canvas, detections, fontSize);
  }, [detections, fontSize]);

  return (
    <div
      style={{
        position: "relative",
        width,
        height,
        backgroundColor: "black",
        overflow: "hidden",
      }}
    >
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width,
          height,
          cursor: "crosshair",
        }}
        role="presentation"
        aria-label="Detection overlay"
      />

      {/* Info overlay */}
      {detections.length > 0 && (
        <div
          style={{
            position: "absolute",
            top: "10px",
            left: "10px",
            backgroundColor: "rgba(0, 0, 0, 0.7)",
            color: BOX_COLOR,
            padding: "8px 12px",
            borderRadius: "4px",
            fontSize: "12px",
            fontFamily: "monospace",
            border: `1px solid ${BOX_COLOR}`,
            zIndex: 10,
          }}
        >
          {detections.length} detection{detections.length !== 1 ? "s" : ""}
        </div>
      )}
    </div>
  );
}

export default ResultOverlay;
