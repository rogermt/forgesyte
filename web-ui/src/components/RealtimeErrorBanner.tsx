import { useRealtimeContext } from "../realtime/RealtimeContext";
import { ErrorBanner } from "./ErrorBanner";

export function RealtimeErrorBanner() {
  const { state, clearError, connect, currentPipelineId } = useRealtimeContext();
  const err = state.lastError;

  if (!err) return null;

  // Map backend error codes → user-friendly messages
  const messageMap: Record<string, string> = {
    invalid_pipeline: "The selected pipeline is not available.",
    invalid_frame: "The video frame could not be processed.",
    frame_too_large: "The video frame is too large.",
    invalid_message: "The server received an unexpected message.",
    pipeline_failure: "The pipeline failed while processing your video.",
    internal_error: "An internal error occurred. Please try again.",
  };

  const friendlyMessage = messageMap[err.error] ?? "An unknown error occurred.";

  const handleRetry = () => {
    clearError();
    if (currentPipelineId) {
      connect(currentPipelineId);
    }
  };

  return (
    <ErrorBanner
      title="Streaming Error"
      message={friendlyMessage}
      showDismiss={true}
      onDismiss={handleRetry}
    />
  );
}
