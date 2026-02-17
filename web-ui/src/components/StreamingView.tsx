/**
 * StreamingView Component
 *
 * Final Phase 17 architecture:
 * - CameraPreview: Captures webcam frames
 * - RealtimeStreamingOverlay: Renders detection boxes
 * - RealtimeErrorBanner: Shows streaming errors
 * - StreamDebugPanel: Shows metrics (debug only)
 */

import React from "react";
import { CameraPreview } from "./CameraPreview";
import { RealtimeStreamingOverlay } from "./RealtimeStreamingOverlay";
import { RealtimeErrorBanner } from "./RealtimeErrorBanner";
import { StreamDebugPanel } from "./StreamDebugPanel";

export interface StreamingViewProps {
  debug?: boolean;
}

export function StreamingView({ debug }: StreamingViewProps) {
  return (
    <div className="streaming-layout">
      <div className="stream-main">
        <CameraPreview />
        <RealtimeStreamingOverlay />
        <RealtimeErrorBanner />
      </div>

      {debug && (
        <aside className="stream-debug">
          <StreamDebugPanel />
        </aside>
      )}
    </div>
  );
}

export default StreamingView;