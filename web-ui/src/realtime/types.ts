/**
 * Phase 17 Realtime Types
 *
 * Types for WebSocket streaming messages and state
 */

// ============================================================================
// Streaming Message Types
// ============================================================================

export interface StreamingResultPayload {
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

export interface StreamingDroppedPayload {
  frame_index: number;
  dropped: true;
}

export interface StreamingSlowDownPayload {
  warning: "slow_down";
}

export interface StreamingErrorPayload {
  error: string;
  detail?: string;
}

export type StreamingMessage =
  | StreamingResultPayload
  | StreamingDroppedPayload
  | StreamingSlowDownPayload
  | StreamingErrorPayload;

// ============================================================================
// Detection Type (Frontend)
// ============================================================================

export interface Detection {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  confidence?: number;
}

// ============================================================================
// Converter Functions
// ============================================================================

export function toDetections(result: StreamingResultPayload["result"]): Detection[] {
  if (!result || !Array.isArray(result.detections)) return [];
  return result.detections.map((d) => ({
    x: d.x,
    y: d.y,
    width: d.w,
    height: d.h,
    label: d.label,
    confidence: d.score,
  }));
}

// ============================================================================
// Realtime State
// ============================================================================

export type ConnectionStatus = "connecting" | "connected" | "disconnected";

export interface RealtimeState {
  status: ConnectionStatus;
  lastResult: StreamingResultPayload | null;
  droppedFrames: number;
  slowDownWarnings: number;
  lastError: StreamingErrorPayload | null;
  framesSent: number;
  startTime: number | null;
}