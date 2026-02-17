/**
 * Phase 17 StreamDebugPanel Component
 *
 * Shows streaming metrics and MP4 job state
 */

import { useRealtime } from "../realtime/useRealtime";
import { useMP4ProcessingContext } from "../mp4/MP4ProcessingContext";

export function StreamDebugPanel() {
  const realtime = useRealtime();
  const mp4 = useMP4ProcessingContext();

  // Calculate derived metrics
  const elapsedSeconds = realtime.state.startTime
    ? (Date.now() - realtime.state.startTime) / 1000
    : 0;
  const fps = elapsedSeconds > 0 ? realtime.state.framesSent / elapsedSeconds : 0;
  const dropRate =
    realtime.state.framesSent > 0
      ? realtime.state.droppedFrames / realtime.state.framesSent
      : 0;

  return (
    <div className="debug-panel">
      <h4>Streaming Debug</h4>
      <div>Status: {realtime.state.status}</div>
      <div>FPS: {fps.toFixed(1)}</div>
      <div>Frames sent: {realtime.state.framesSent}</div>
      <div>Dropped frames: {realtime.state.droppedFrames}</div>
      <div>Drop rate: {(dropRate * 100).toFixed(1)}%</div>
      <div>Slow-down warnings: {realtime.state.slowDownWarnings}</div>
      {realtime.state.lastResult && (
        <div>Last frame: {realtime.state.lastResult.frame_index}</div>
      )}

      <hr />

      <h4>MP4 Processing</h4>
      {mp4?.active ? (
        <>
          <div>Job ID: {mp4.jobId}</div>
          <div>Progress: {mp4.progress}%</div>
          <div>Frames processed: {mp4.framesProcessed}</div>
        </>
      ) : (
        <div>No MP4 processing</div>
      )}
    </div>
  );
}

export default StreamDebugPanel;