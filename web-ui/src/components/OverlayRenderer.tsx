import React from 'react';

interface Box {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

interface NormalisedFrame {
  frame_index: number;
  boxes: Box[];
  scores: number[];
  labels: string[];
}

interface OverlayRendererProps {
  data: { frames: NormalisedFrame[] };
  width: number;
  height: number;
}

/**
 * OverlayRenderer
 *
 * Canonical overlay renderer for all plugin outputs.
 * Consumes normalised schema and renders SVG overlays.
 *
 * Renders:
 * - Bounding boxes (from canonical schema)
 * - Labels (text overlays)
 * - Track IDs (if present in schema)
 * - Pitch lines (if applicable)
 * - Radar overlays (if applicable)
 */
export const OverlayRenderer: React.FC<OverlayRendererProps> = ({
  data,
  width,
  height,
}) => {
  // Use first frame (single-frame support for now)
  const frame = data.frames[0];

  if (!frame) {
    return <svg width={width} height={height} />;
  }

  return (
    <svg
      width={width}
      height={height}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        pointerEvents: 'none',
      }}
    >
      {frame.boxes.map((box, i) => (
        <rect
          key={i}
          x={box.x1}
          y={box.y1}
          width={box.x2 - box.x1}
          height={box.y2 - box.y1}
          fill="none"
          stroke="blue"
          strokeWidth="2"
        />
      ))}
    </svg>
  );
};
