/**
 * Phase-17 Streaming View Component
 *
 * Groups all Phase-17 streaming UI components:
 * - CameraPreview: Captures and streams webcam frames
 * - RealtimeStreamingOverlay: Draws detection overlays
 * - RealtimeErrorBanner: Displays streaming errors
 * - StreamDebugPanel: Shows debug metrics (when debug=true)
 */

import { CameraPreview } from "./CameraPreview";
import { RealtimeStreamingOverlay } from "./RealtimeStreamingOverlay";
import { RealtimeErrorBanner } from "./RealtimeErrorBanner";
import { StreamDebugPanel } from "./StreamDebugPanel";
import { useRealtime } from "../realtime/useRealtime";

export interface StreamingViewProps {
  debug: boolean;
  enabled?: boolean;
}

export function StreamingView({ debug, enabled = true }: StreamingViewProps) {
  return (
    <>
      <CameraPreview enabled={enabled} />
      <RealtimeStreamingOverlay width={640} height={480} debug={debug} />
      <RealtimeErrorBanner />
      <StreamDebugPanel debug={debug} />
    </>
  );
}