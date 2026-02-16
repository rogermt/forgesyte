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
