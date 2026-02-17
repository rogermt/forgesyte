/**
 * Phase 17: Real-Time Streaming Types
 *
 * Shared types for WebSocket streaming messages between frontend and backend.
 */

export type StreamingResultPayload = {
  frame_index: number;
  result: unknown;
};

export type StreamingDroppedPayload = {
  frame_index: number;
  dropped: true;
};

export type StreamingSlowDownPayload = {
  warning: "slow_down";
};

export type StreamingErrorPayload = {
  error: string;
  detail: string;
};

export type StreamingMessage =
  | StreamingResultPayload
  | StreamingDroppedPayload
  | StreamingSlowDownPayload
  | StreamingErrorPayload;

export type StreamingConnectionStatus = "connecting" | "connected" | "disconnected";

/**
 * Detection type for Phase-17 streaming
 * Matches Phase-10 Detection type for compatibility
 */
export interface Detection {
  x: number;
  y: number;
  width: number;
  height: number;
  class: string;
  confidence: number;
  track_id?: number;
}

/**
 * Extended StreamingResultPayload with detections array
 */
export interface StreamingResultPayloadWithDetections {
  frame_index: number;
  result: {
    detections: Array<{
      x: number;
      y: number;
      w: number;
      h: number;
      label: string;
      score: number;
    }>;
  };
}

/**
 * Convert Phase-17 backend detections → Phase-10 Detection type.
 *
 * Backend format: { x, y, w, h, label, score }
 * Frontend Detection: { x, y, width, height, class, confidence }
 */
export function toStreamingDetections(
  payload: StreamingResultPayload
): Detection[] {
  const result = payload.result as StreamingResultPayloadWithDetections["result"];
  
  if (!result?.detections) return [];

  return result.detections.map((d) => ({
    x: d.x,
    y: d.y,
    width: d.w,      // Backend uses 'w', frontend uses 'width'
    height: d.h,     // Backend uses 'h', frontend uses 'height'
    class: d.label,  // Backend uses 'label', frontend uses 'class'
    confidence: d.score,  // Backend uses 'score', frontend uses 'confidence'
  }));
}
