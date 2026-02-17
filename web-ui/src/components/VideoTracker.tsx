/**
 * VideoTracker Component
 *
 * Final Phase 17 architecture:
 * - MP4 upload for async YOLO inference
 * - Uses useVideoProcessor hook
 * - MP4ProcessingProvider exposes state to StreamDebugPanel
 */

import React, { useState } from "react";
import { useVideoProcessor } from "../hooks/useVideoProcessor";
import { MP4ProcessingProvider } from "../mp4/MP4ProcessingContext";

export interface VideoTrackerProps {
  debug?: boolean;
}

export function VideoTracker({ debug }: VideoTrackerProps) {
  const [file, setFile] = useState<File | null>(null);

  const processor = useVideoProcessor({
    file,
    debug,
  });

  const mp4State = {
    active: processor.state.status === "processing",
    jobId: processor.state.currentJobId ?? null,
    progress: processor.state.progress ?? 0,
    framesProcessed: processor.state.framesProcessed ?? 0,
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0] ?? null;
    setFile(selected);
    if (selected) {
      processor.start(selected);
    }
  };

  return (
    <MP4ProcessingProvider value={mp4State}>
      <div className="panel">
        <h3>Upload video for analysis</h3>
        <input
          type="file"
          accept="video/*"
          onChange={handleFileChange}
        />

        {processor.state.status === "idle" && <p>No job started.</p>}
        {processor.state.status === "processing" && (
          <p>Processing… {mp4State.progress}%</p>
        )}
        {processor.state.status === "completed" && <p>Job completed.</p>}
        {processor.state.status === "error" && (
          <p>Error: {processor.state.errorMessage}</p>
        )}
      </div>
    </MP4ProcessingProvider>
  );
}

export default VideoTracker;

