/**
 * Phase 17 RealtimeStreamingOverlay Component
 *
 * Renders detection boxes over the video stream
 */

import { useEffect, useRef } from "react";
import { useRealtime } from "../realtime/useRealtime";
import { toDetections, type Detection } from "../realtime/types";

export function RealtimeStreamingOverlay() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const realtime = useRealtime();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const result = realtime.state.lastResult;
    if (!result) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      return;
    }

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Convert backend result to frontend detections
    const detections: Detection[] = toDetections(result.result);

    // Draw each detection
    detections.forEach((det) => {
      // Draw bounding box
      ctx.strokeStyle = "#00ff00";
      ctx.lineWidth = 2;
      ctx.strokeRect(det.x, det.y, det.width, det.height);

      // Draw label
      ctx.fillStyle = "#00ff00";
      ctx.font = "14px monospace";
      const label = `${det.label}${det.confidence ? ` ${(det.confidence * 100).toFixed(0)}%` : ""}`;
      ctx.fillText(label, det.x, det.y - 4);
    });

    // Draw frame index
    ctx.fillStyle = "#ffffff";
    ctx.font = "12px monospace";
    ctx.fillText(`Frame: ${result.frame_index}`, 10, 20);
  }, [realtime.state.lastResult]);

  return <canvas ref={canvasRef} className="overlay-canvas" />;
}

export default RealtimeStreamingOverlay;