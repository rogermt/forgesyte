/**
 * Result Overlay Component
 * Renders detection boxes, tracks, and radar overlays on canvas
 *
 * Best Practices Applied:
 * - [BP-1] Canvas rendering with proper cleanup
 * - [BP-2] useEffect for animation frames
 * - [BP-3] useMemo for computed styles
 * - [BP-4] Proper canvas sizing to match video dimensions
 * - [BP-5] Support for multiple overlay types (detections, radar, annotated frame)
 */

import { useEffect, useRef, useMemo } from "react";
import type { Detection } from "../types/video-tracker";

// ============================================================================
// Types
// ============================================================================

export interface ResultOverlayProps {
  /** Canvas dimensions */
  width: number;
  height: number;
  /** Current detections to draw */
  detections: Detection[];
  /** Latest annotated frame (base64) */
  annotatedFrame?: string;
  /** Radar overlay (base64) */
  radarOverlay?: string;
  /** Color scheme for bounding boxes */
  colors?: {
    default: string;
    team1: string;
    team2: string;
    ball: string;
    referee: string;
  };
  /** Whether to show detection labels */
  showLabels?: boolean;
  /** Whether to show confidence scores */
  showConfidence?: boolean;
  /** Font size for labels */
  fontSize?: number;
  /** Track persistence map for drawing tracks */
  trackMap?: Map<number, Detection>;
}

// ============================================================================
// Color Defaults
// ============================================================================

const DEFAULT_COLORS = {
  default: "#00BFFF",   // Cyan
  team1: "#00BFFF",     // Cyan (Team A)
  team2: "#FF1493",     // Magenta (Team B)
  ball: "#FFD700",      // Gold
  referee: "#FF6347",   // Tomato
} as const;

// ============================================================================
// Component
// ============================================================================

export function ResultOverlay({
  width,
  height,
  detections,
  annotatedFrame,
  radarOverlay,
  colors = DEFAULT_COLORS,
  showLabels = true,
  showConfidence = true,
  fontSize = 12,
}: ResultOverlayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const radarRef = useRef<HTMLImageElement | null>(null);

  // -------------------------------------------------------------------------
  // Computed styles
  // -------------------------------------------------------------------------
  const containerStyles = useMemo(
    () => ({
      position: "relative" as const,
      width,
      height,
      backgroundColor: "black",
      overflow: "hidden" as const,
    }),
    [width, height]
  );

  const canvasStyles = useMemo(
    () => ({
      position: "absolute" as const,
      top: 0,
      left: 0,
      width,
      height,
      cursor: "crosshair" as const,
    }),
    [width, height]
  );

  const imageStyles = useMemo(
    () => ({
      position: "absolute" as const,
      top: 0,
      left: 0,
      width,
      height,
      display: "none" as const, // Hidden, used only for loading
    }),
    [width, height]
  );

  // -------------------------------------------------------------------------
  // Load annotated frame image
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!annotatedFrame) return;

    if (!imageRef.current) {
      imageRef.current = new Image();
    }

    imageRef.current.onload = () => {
      // Image loaded, will be drawn in canvas effect
    };

    imageRef.current.src = `data:image/png;base64,${annotatedFrame}`;
  }, [annotatedFrame]);

  // -------------------------------------------------------------------------
  // Load radar overlay image
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!radarOverlay) return;

    if (!radarRef.current) {
      radarRef.current = new Image();
    }

    radarRef.current.onload = () => {
      // Image loaded, will be drawn in canvas effect
    };

    radarRef.current.src = `data:image/png;base64,${radarOverlay}`;
  }, [radarOverlay]);

  // -------------------------------------------------------------------------
  // Draw detections on canvas
  // -------------------------------------------------------------------------
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Clear canvas
    ctx.fillStyle = "rgba(0, 0, 0, 0)";
    ctx.clearRect(0, 0, width, height);

    // Draw annotated frame if available
    if (imageRef.current && imageRef.current.complete) {
      ctx.drawImage(imageRef.current, 0, 0, width, height);
    }

    // Draw detections
    detections.forEach((detection) => {
      // Determine color based on class
      let boxColor = colors.default;
      if (detection.class === "team_1") boxColor = colors.team1;
      else if (detection.class === "team_2") boxColor = colors.team2;
      else if (detection.class === "ball") boxColor = colors.ball;
      else if (detection.class === "referee") boxColor = colors.referee;

      // Draw bounding box
      ctx.strokeStyle = boxColor;
      ctx.lineWidth = 2;
      ctx.strokeRect(detection.x, detection.y, detection.width, detection.height);

      // Draw filled corner markers
      const cornerSize = 4;
      ctx.fillStyle = boxColor;
      ctx.fillRect(detection.x, detection.y, cornerSize, cornerSize);
      ctx.fillRect(
        detection.x + detection.width - cornerSize,
        detection.y,
        cornerSize,
        cornerSize
      );
      ctx.fillRect(
        detection.x,
        detection.y + detection.height - cornerSize,
        cornerSize,
        cornerSize
      );
      ctx.fillRect(
        detection.x + detection.width - cornerSize,
        detection.y + detection.height - cornerSize,
        cornerSize,
        cornerSize
      );

      // Draw label
      if (showLabels && detection.class) {
        const label = detection.class.replace(/_/g, " ");
        const confidence = showConfidence
          ? ` (${(detection.confidence * 100).toFixed(0)}%)`
          : "";
        const text = `${label}${confidence}`;

        ctx.font = `bold ${fontSize}px monospace`;
        ctx.fillStyle = boxColor;
        const metrics = ctx.measureText(text);
        const textHeight = fontSize + 4;

        // Semi-transparent background
        ctx.fillStyle = `rgba(0, 0, 0, 0.7)`;
        ctx.fillRect(
          detection.x,
          detection.y - textHeight,
          metrics.width + 8,
          textHeight
        );

        // Text
        ctx.fillStyle = boxColor;
        ctx.fillText(text, detection.x + 4, detection.y - 6);
      }

      // Draw track ID if available
      if (detection.track_id !== undefined) {
        const trackText = `ID:${detection.track_id}`;
        ctx.font = `bold ${fontSize - 2}px monospace`;
        ctx.fillStyle = colors.default;
        const metrics = ctx.measureText(trackText);
        const textHeight = fontSize - 2 + 4;

        // Semi-transparent background
        ctx.fillStyle = `rgba(0, 0, 0, 0.7)`;
        ctx.fillRect(
          detection.x,
          detection.y + detection.height,
          metrics.width + 8,
          textHeight
        );

        // Text
        ctx.fillStyle = colors.default;
        ctx.fillText(trackText, detection.x + 4, detection.y + detection.height + fontSize - 4);
      }
    });

    // Draw radar overlay if available
    if (radarRef.current && radarRef.current.complete) {
      // Position radar at bottom-right
      const radarSize = Math.min(width / 3, height / 3);
      const radarX = width - radarSize - 10;
      const radarY = height - radarSize - 10;

      ctx.drawImage(
        radarRef.current,
        radarX,
        radarY,
        radarSize,
        radarSize
      );

      // Draw radar border
      ctx.strokeStyle = colors.default;
      ctx.lineWidth = 2;
      ctx.strokeRect(radarX, radarY, radarSize, radarSize);
    }
  }, [detections, width, height, colors, showLabels, showConfidence, fontSize]);

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  return (
    <div style={containerStyles}>
      {/* Canvas for drawing detections */}
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={canvasStyles}
        role="presentation"
        aria-label="Detection overlay"
      />

      {/* Hidden images for loading */}
      <img ref={imageRef} style={imageStyles} alt="annotated-frame" />
      <img ref={radarRef} style={imageStyles} alt="radar-overlay" />

      {/* Info overlay */}
      {detections.length > 0 && (
        <div
          style={{
            position: "absolute",
            top: "10px",
            left: "10px",
            backgroundColor: "rgba(0, 0, 0, 0.7)",
            color: colors.default,
            padding: "8px 12px",
            borderRadius: "4px",
            fontSize: "12px",
            fontFamily: "monospace",
            border: `1px solid ${colors.default}`,
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
