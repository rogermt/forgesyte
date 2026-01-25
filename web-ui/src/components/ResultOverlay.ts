

/**
 * ResultOverlay - Pure Drawing Function
 *
 * Renders detection boxes, tracks, and radar overlays on an external canvas.
 * This is the schema boundary - only place that interprets plugin JSON.
 *
 * Architecture:
 * - Pure function (no React hooks, no JSX)
 * - Accepts external canvas reference
 * - Plugin-agnostic at VideoTracker level
 * - YOLO-specific logic isolated here (correct boundary)
 */

// ============================================================================
// Types
// ============================================================================

// Local YOLO detection type - schema-specific to ResultOverlay
// VideoTracker remains plugin-agnostic
interface YoloDetection {
  x: number;
  y: number;
  width: number;
  height: number;
  class?: string;
  confidence?: number;
  track_id?: number;
}

interface PitchLines {
  lines: Array<{ x1: number; y1: number; x2: number; y2: number }>;
}

interface RadarPoints {
  points: Array<{ x: number; y: number }>;
}

interface BallPosition {
  x: number;
  y: number;
}

interface YoloDetections {
  detections?: YoloDetection[];
  ball?: BallPosition;
  pitch?: PitchLines;
  radar?: RadarPoints;
}

export interface OverlayToggles {
  players: boolean;
  tracking: boolean;
  ball: boolean;
  pitch: boolean;
  radar: boolean;
}

export interface ResultOverlayArgs {
  /** Canvas to draw on */
  canvas: HTMLCanvasElement;
  /** Video frame width */
  frameWidth: number;
  /** Video frame height */
  frameHeight: number;
  /** Raw detections from plugin */
  detections?: YoloDetections | null;
  /** Overlay toggle states */
  overlayToggles: OverlayToggles;
}

// ============================================================================
// Color Constants
// ============================================================================

type ColorValue = string;

const COLORS: Record<string, ColorValue> = {
  default: "#00BFFF",
  team1: "#00BFFF",
  team2: "#FF1493",
  ball: "#FFD700",
  referee: "#FF6347",
  pitch: "#00BFFF",
  radar: "#00BFFF",
};

// ============================================================================
// Pure Drawing Function
// ============================================================================

export function ResultOverlay({
  canvas,
  frameWidth,
  frameHeight,
  detections,
  overlayToggles,
}: ResultOverlayArgs): void {
  // Get canvas context
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  // Resize canvas to match video dimensions
  canvas.width = frameWidth;
  canvas.height = frameHeight;

  // Clear canvas
  ctx.clearRect(0, 0, frameWidth, frameHeight);

  // Guard: no detections to draw
  if (!detections) return;

  // Draw detections (players, ball, etc.)
  if (overlayToggles.players && Array.isArray(detections.detections)) {
    drawDetections(ctx, detections.detections, overlayToggles);
  }

  // Draw ball marker
  if (overlayToggles.ball && detections.ball) {
    drawBall(ctx, detections.ball);
  }

  // Draw pitch lines
  if (overlayToggles.pitch && detections.pitch?.lines) {
    drawPitchLines(ctx, detections.pitch.lines);
  }

  // Draw radar overlay
  if (overlayToggles.radar && detections.radar?.points) {
    drawRadarPoints(ctx, detections.radar.points, frameWidth, frameHeight);
  }
}

// ============================================================================
// Drawing Helpers
// ============================================================================

function drawDetections(
  ctx: CanvasRenderingContext2D,
  detections: YoloDetection[],
  toggles: OverlayToggles
): void {
  const fontSize = 12;

  detections.forEach((det: YoloDetection) => {
    const { x, y, width, height, class: cls, track_id } = det;

    // Determine color based on class
    let boxColor = COLORS.default;
    if (cls === "team_1") boxColor = COLORS.team1;
    else if (cls === "team_2") boxColor = COLORS.team2;
    else if (cls === "ball") boxColor = COLORS.ball;
    else if (cls === "referee") boxColor = COLORS.referee;

    // Draw bounding box
    ctx.strokeStyle = boxColor;
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, width, height);

    // Draw filled corner markers
    const cornerSize = 4;
    ctx.fillStyle = boxColor;
    ctx.fillRect(x, y, cornerSize, cornerSize);
    ctx.fillRect(x + width - cornerSize, y, cornerSize, cornerSize);
    ctx.fillRect(x, y + height - cornerSize, cornerSize, cornerSize);
    ctx.fillRect(x + width - cornerSize, y + height - cornerSize, cornerSize, cornerSize);

    // Draw label (class name)
    if (cls) {
      const label = String(cls).replace(/_/g, " ");
      const confidence = det.confidence !== undefined
        ? ` (${(det.confidence * 100).toFixed(0)}%)`
        : "";
      const text = `${label}${confidence}`;

      ctx.font = `bold ${fontSize}px monospace`;
      ctx.fillStyle = boxColor;
      const metrics = ctx.measureText(text);
      const textHeight = fontSize + 4;

      // Semi-transparent background
      ctx.fillStyle = `rgba(0, 0, 0, 0.7)`;
      ctx.fillRect(x, y - textHeight, metrics.width + 8, textHeight);

      // Text
      ctx.fillStyle = boxColor;
      ctx.fillText(text, x + 4, y - 6);
    }

    // Draw track ID
    if (toggles.tracking && track_id !== undefined) {
      const trackText = `ID:${track_id}`;
      ctx.font = `bold ${fontSize - 2}px monospace`;
      ctx.fillStyle = COLORS.default;
      const metrics = ctx.measureText(trackText);
      const textHeight = fontSize - 2 + 4;

      // Semi-transparent background
      ctx.fillStyle = `rgba(0, 0, 0, 0.7)`;
      ctx.fillRect(x, y + height, metrics.width + 8, textHeight);

      // Text
      ctx.fillStyle = COLORS.default;
      ctx.fillText(trackText, x + 4, y + height + fontSize - 4);
    }
  });
}

function drawBall(ctx: CanvasRenderingContext2D, ball: { x: number; y: number }): void {
  const { x, y } = ball;
  const radius = 6;

  ctx.fillStyle = COLORS.ball;
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.fill();

  // Draw border
  ctx.strokeStyle = COLORS.ball;
  ctx.lineWidth = 1;
  ctx.stroke();
}

function drawPitchLines(
  ctx: CanvasRenderingContext2D,
  lines: Array<{ x1: number; y1: number; x2: number; y2: number }>
): void {
  ctx.strokeStyle = COLORS.pitch;
  ctx.lineWidth = 2;

  lines.forEach((line) => {
    ctx.beginPath();
    ctx.moveTo(line.x1, line.y1);
    ctx.lineTo(line.x2, line.y2);
    ctx.stroke();
  });
}

function drawRadarPoints(
  ctx: CanvasRenderingContext2D,
  points: Array<{ x: number; y: number }>,
  frameWidth: number,
  frameHeight: number
): void {
  // Calculate radar position (bottom-right corner)
  const radarSize = Math.min(frameWidth / 3, frameHeight / 3);
  const radarX = frameWidth - radarSize - 10;
  const radarY = frameHeight - radarSize - 10;

  // Draw radar background/border
  ctx.strokeStyle = COLORS.radar;
  ctx.lineWidth = 2;
  ctx.strokeRect(radarX, radarY, radarSize, radarSize);

  // Draw points
  ctx.fillStyle = COLORS.radar;
  points.forEach((point) => {
    const px = radarX + (point.x / frameWidth) * radarSize;
    const py = radarY + (point.y / frameHeight) * radarSize;
    ctx.fillRect(px - 2, py - 2, 4, 4);
  });
}

