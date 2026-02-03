/**
 * Canvas drawing utility for rendering detections, tracks, and overlays
 * Separated from ResultOverlay component to satisfy react-refresh/only-export-components
 */

import type { Detection } from "../types/plugin";

export interface OverlayToggles {
  players: boolean;
  tracking: boolean;
  ball: boolean;
  pitch: boolean;
  radar: boolean;
}

export interface DrawDetectionsParams {
  canvas: HTMLCanvasElement;
  detections: Detection[];
  overlayToggles?: Partial<OverlayToggles>;
  fontSize?: number;
  colors?: {
    default: string;
    team1: string;
    team2: string;
    ball: string;
    referee: string;
  };
  annotatedFrame?: string;
  radarOverlay?: string;
  pitchLines?: Array<{ x1: number; y1: number; x2: number; y2: number }>;
  width?: number;
  height?: number;
}

const DEFAULT_COLORS = {
  default: "#00BFFF",   // Cyan
  team1: "#00BFFF",     // Cyan (Team A)
  team2: "#FF1493",     // Magenta (Team B)
  ball: "#FFD700",      // Gold
  referee: "#FF6347",   // Tomato
};

export function drawDetections({
  canvas,
  detections,
  overlayToggles = {
    players: true,
    tracking: true,
    ball: true,
    pitch: true,
    radar: true,
  },
  fontSize = 12,
  colors = DEFAULT_COLORS,
  annotatedFrame,
  radarOverlay,
  pitchLines,
  width,
  height,
}: DrawDetectionsParams): void {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const canvasWidth = width || canvas.width;
  const canvasHeight = height || canvas.height;

  // Clear canvas
  ctx.fillStyle = "rgba(0, 0, 0, 0)";
  ctx.clearRect(0, 0, canvasWidth, canvasHeight);

  // Handle annotated frame if provided (for pitch overlay)
  if (annotatedFrame && overlayToggles.pitch !== false) {
    const img = new Image();
    img.src = `data:image/png;base64,${annotatedFrame}`;
    if (img.complete) {
      ctx.drawImage(img, 0, 0, canvasWidth, canvasHeight);
    }
  }

  // Draw pitch lines if provided and pitch toggle is enabled
  if (pitchLines && overlayToggles.pitch !== false) {
    ctx.strokeStyle = colors.default;
    ctx.lineWidth = 2;
    pitchLines.forEach((line) => {
      ctx.beginPath();
      ctx.moveTo(line.x1, line.y1);
      ctx.lineTo(line.x2, line.y2);
      ctx.stroke();
    });
  }

  // Draw detections
  detections.forEach((detection) => {
    // Determine color based on class
    let boxColor = colors.default;
    let isBall = false;
    if (detection.class === "team_1") boxColor = colors.team1;
    else if (detection.class === "team_2") boxColor = colors.team2;
    else if (detection.class === "ball") {
      boxColor = colors.ball;
      isBall = true;
    } else if (detection.class === "referee") boxColor = colors.referee;

    // Draw bounding box (players layer)
    if (!isBall && overlayToggles.players !== false) {
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
      if (detection.class) {
        const label = detection.class.replace(/_/g, " ");
        const text = label;

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
    }

    // Draw ball marker (ball layer)
    if (isBall && overlayToggles.ball !== false) {
      const centerX = detection.x + detection.width / 2;
      const centerY = detection.y + detection.height / 2;
      const radius = Math.max(detection.width, detection.height) / 2;

      ctx.strokeStyle = boxColor;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
      ctx.stroke();
    }
  });

  // Draw radar overlay if provided
  if (radarOverlay && overlayToggles.radar !== false) {
    const img = new Image();
    img.src = `data:image/png;base64,${radarOverlay}`;
    if (img.complete) {
      const radarWidth = 200;
      const radarHeight = 100;
      ctx.drawImage(img, canvasWidth - radarWidth - 10, canvasHeight - radarHeight - 10, radarWidth, radarHeight);
    }
  }
}
