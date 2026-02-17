/**
 * Phase-7 Stream Debug Panel Component
 *
 * Displays streaming performance and connection metrics:
 * - Connection status
 * - WebSocket URL
 * - Frames sent and FPS
 * - Dropped frames and drop rate
 * - Slow-down warnings
 * - Last 5 frame sizes
 * - Last 5 latencies
 * - Last frame index
 * - FE-8: MP4 processing state
 */

import { useRealtimeContext } from "../realtime/RealtimeContext";
import { useMP4ProcessingContext } from "../mp4/MP4ProcessingContext";

export interface StreamDebugPanelProps {
  debug: boolean;
}

export function StreamDebugPanel({ debug }: StreamDebugPanelProps) {
  // Call hooks before any early returns (Rules of Hooks)
  const { state, wsUrl, currentPipelineId } = useRealtimeContext();
  const mp4 = useMP4ProcessingContext();
  const {
    connectionStatus,
    framesSent,
    startTime,
    droppedFrames,
    slowDownWarnings,
    lastFrameSizes,
    lastLatencies,
    currentFps,
    lastResult,
  } = state;

  // Early return after hooks are called
  if (!debug) return null;

  const elapsedSeconds =
    startTime != null ? (performance.now() - startTime) / 1000 : 0;

  const approxFps =
    elapsedSeconds > 0 ? (framesSent / elapsedSeconds).toFixed(1) : "0.0";

  const dropRate =
    framesSent > 0
      ? ((droppedFrames / framesSent) * 100).toFixed(1) + "%"
      : "0%";

  return (
    <div
      className="stream-debug-panel"
      style={{
        position: "fixed",
        bottom: "16px",
        right: "16px",
        width: "320px",
        backgroundColor: "rgba(0, 0, 0, 0.9)",
        color: "#0f0",
        padding: "16px",
        borderRadius: "8px",
        fontFamily: "monospace",
        fontSize: "12px",
        zIndex: 10000,
        maxHeight: "80vh",
        overflowY: "auto",
        border: "1px solid #0f0",
      }}
    >
      <div style={{ fontWeight: "bold", marginBottom: "8px" }}>
        Phase-17 Debug Panel
      </div>
      <hr style={{ borderColor: "#0f0", margin: "8px 0" }} />

      <div>Status: {connectionStatus}</div>
      <div>Pipeline: {currentPipelineId ?? "none"}</div>
      <div style={{ wordBreak: "break-all" }}>WS URL: {wsUrl}</div>

      <hr style={{ borderColor: "#0f0", margin: "8px 0" }} />

      <div>Frames Sent: {framesSent}</div>
      <div>FPS (approx): {approxFps}</div>
      <div>Throttler FPS: {currentFps}</div>

      <hr style={{ borderColor: "#0f0", margin: "8px 0" }} />

      <div>Dropped Frames: {droppedFrames}</div>
      <div>Drop Rate: {dropRate}</div>
      <div>Slow-Down Warnings: {slowDownWarnings}</div>

      <hr style={{ borderColor: "#0f0", margin: "8px 0" }} />

      <div>Last 5 Frame Sizes:</div>
      <ul style={{ margin: "4px 0", paddingLeft: "20px" }}>
        {lastFrameSizes.length === 0 ? (
          <li style={{ color: "#888" }}>none</li>
        ) : (
          lastFrameSizes.slice(-5).map((s, i) => (
            <li key={i}>{s} bytes</li>
          ))
        )}
      </ul>

      <div>Last 5 Latencies:</div>
      <ul style={{ margin: "4px 0", paddingLeft: "20px" }}>
        {lastLatencies.length === 0 ? (
          <li style={{ color: "#888" }}>none</li>
        ) : (
          lastLatencies.slice(-5).map((l, i) => (
            <li key={i}>{l.toFixed(1)} ms</li>
          ))
        )}
      </ul>

      <hr style={{ borderColor: "#0f0", margin: "8px 0" }} />

      <div>
        Last Frame Index: {lastResult?.frame_index ?? "none"}
      </div>

      {/* FE-8: MP4 Processing Section */}
      <hr style={{ borderColor: "#0f0", margin: "8px 0" }} />

      <div style={{ fontWeight: "bold", marginBottom: "4px" }}>
        MP4 Processing
      </div>
      {mp4 && mp4.active ? (
        <>
          <div>Status: Active</div>
          <div>Progress: {mp4.progress}%</div>
          <div>Frames Processed: {mp4.framesProcessed}</div>
        </>
      ) : (
        <div style={{ color: "#888" }}>No MP4 processing</div>
      )}
    </div>
  );
}