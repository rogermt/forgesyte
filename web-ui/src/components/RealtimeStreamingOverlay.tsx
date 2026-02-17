import { useEffect, useRef, useMemo } from "react";
import { useRealtimeContext } from "../realtime/RealtimeContext";
import { toStreamingDetections, type Detection } from "../realtime/types";

interface RealtimeStreamingOverlayProps {
  width: number;
  height: number;
  debug?: boolean; // Golden Path Debug Mode
}

/**
 * Phase-17 Streaming Overlay
 * Draws bounding boxes for realtime detections on top of the video canvas.
 */
export function RealtimeStreamingOverlay({
  width,
  height,
  debug = false,
}: RealtimeStreamingOverlayProps) {
  const { state } = useRealtimeContext();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const result = state.lastResult;

  const detections = useMemo(() => {
    return result ? toStreamingDetections(result) : [];
  }, [result]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Clear previous frame
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw detections inline
    detections.forEach((detection: Detection) => {
      const { x, y, width: w, height: h, class: label, confidence, track_id } = detection;

      // Draw bounding box
      ctx.strokeStyle = "#00ff00";
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, w, h);

      // Draw label background
      ctx.fillStyle = "#00ff00";
      ctx.fillRect(x, y - 20, Math.max(ctx.measureText(`${label} ${(confidence * 100).toFixed(0)}%`).width + 10, 100), 20);

      // Draw label text
      ctx.fillStyle = "#000000";
      ctx.font = "12px monospace";
      ctx.fillText(`${label} ${(confidence * 100).toFixed(0)}%`, x + 5, y - 5);

      // Draw track ID if available
      if (track_id !== undefined) {
        ctx.fillStyle = "#ff0000";
        ctx.font = "bold 14px monospace";
        ctx.fillText(`ID: ${track_id}`, x, y - 25);
      }
    });

    if (debug) {
      console.debug("[RealtimeStreamingOverlay] rendered", {
        frame_index: result?.frame_index,
        detections: detections.length,
      });
    }
  }, [result, detections, debug]);

  // If no result OR last message was a dropped frame → render nothing
  if (!result) {
    return null;
  }

  return (
    <div style={{ position: "absolute", top: 0, left: 0 }}>
      {/* Canvas overlay */}
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          pointerEvents: "none",
        }}
      />

      {/* Frame index label */}
      <div
        style={{
          position: "absolute",
          top: 8,
          left: 8,
          background: "rgba(0,0,0,0.6)",
          color: "white",
          padding: "2px 6px",
          borderRadius: 4,
          fontSize: 12,
          fontFamily: "monospace",
        }}
      >
        Frame #{result.frame_index}
      </div>

      {/* Minimal debug info */}
      {debug && (
        <div
          style={{
            position: "absolute",
            top: 8,
            right: 8,
            background: "rgba(0,0,0,0.6)",
            color: "#0f0",
            padding: "4px 8px",
            borderRadius: 4,
            fontSize: 12,
            fontFamily: "monospace",
          }}
        >
          {detections.length} detections
        </div>
      )}
    </div>
  );
}
