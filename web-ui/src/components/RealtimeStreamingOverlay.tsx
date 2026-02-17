import { useEffect, useRef, useMemo } from "react";
import { useRealtimeContext } from "../realtime/RealtimeContext";
import { toStreamingDetections } from "../realtime/types";
import { drawDetections } from "../utils/drawDetections";

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

    // Draw detections
    drawDetections({
      canvas,
      detections,
      width,
      height,
    });

    if (debug) {
      console.debug("[RealtimeStreamingOverlay] rendered", {
        frame_index: result?.frame_index,
        detections: detections.length,
      });
    }
  }, [result, detections, debug, width, height]);

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
