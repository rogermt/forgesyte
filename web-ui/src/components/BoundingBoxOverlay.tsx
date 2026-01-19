/**
 * Bounding box overlay component for rendering detected objects.
 */

import React from "react";

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  label?: string;
  confidence?: number;
  color?: string;
}

export interface BoundingBoxOverlayProps {
  imageUrl?: string;
  boxes: BoundingBox[];
  width?: number;
  height?: number;
}

const DEFAULT_COLORS = [
  "#FF6B6B",
  "#4ECDC4",
  "#45B7D1",
  "#FFA07A",
  "#98D8C8",
  "#F7DC6F",
];

export function BoundingBoxOverlay({
  imageUrl,
  boxes,
  width = 640,
  height = 480,
}: BoundingBoxOverlayProps): JSX.Element {
  const canvasRef = React.useRef<HTMLCanvasElement>(null);

  React.useEffect(() => {
    if (!canvasRef.current || !imageUrl) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

      boxes.forEach((box, idx) => {
        const color = box.color || DEFAULT_COLORS[idx % DEFAULT_COLORS.length];

        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.strokeRect(box.x, box.y, box.width, box.height);

        if (box.label) {
          const text = box.confidence
            ? `${box.label} (${(box.confidence * 100).toFixed(1)}%)`
            : box.label;

          ctx.fillStyle = color;
          ctx.font = "12px monospace";
          const textMetrics = ctx.measureText(text);
          const textHeight = 16;

          ctx.fillRect(
            box.x,
            box.y - textHeight,
            textMetrics.width + 4,
            textHeight
          );
          ctx.fillStyle = "#000";
          ctx.fillText(text, box.x + 2, box.y - 4);
        }
      });
    };
    img.src = imageUrl;
  }, [imageUrl, boxes]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      style={{
        border: "1px solid var(--border-light)",
        borderRadius: "4px",
        maxWidth: "100%",
        height: "auto",
      }}
    />
  );
}
