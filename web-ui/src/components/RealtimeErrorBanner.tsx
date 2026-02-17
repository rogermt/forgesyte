/**
 * Phase 17 RealtimeErrorBanner Component
 *
 * Shows streaming errors with user-friendly messages
 */

import { useRealtime } from "../realtime/useRealtime";

const ERROR_MESSAGES: Record<string, string> = {
  invalid_pipeline: "The selected pipeline is not available.",
  invalid_frame: "The video frame could not be processed.",
  frame_too_large: "The video frame is too large.",
  invalid_message: "The server received an unexpected message.",
  pipeline_failure: "The pipeline failed while processing your video.",
  internal_error: "An internal error occurred. Please try again.",
};

export function RealtimeErrorBanner() {
  const realtime = useRealtime();
  const error = realtime.state.lastError;

  if (!error) return null;

  const message = ERROR_MESSAGES[error.error] || error.detail || "Unknown error";

  return (
    <div className="error-banner">
      <strong>Error:</strong> {message}
    </div>
  );
}

export default RealtimeErrorBanner;