import React from "react";
import { useJobProgress } from "../hooks/useJobProgress";
import { ProgressBar } from "./ProgressBar";

type Props = {
  jobId: string;
};

export const ProgressDisplay: React.FC<Props> = ({ jobId }) => {
  const { progress: wsProgress, status: wsStatus, error: wsError } = useJobProgress(jobId);

  if (!wsProgress && wsStatus === "pending") {
    return <div style={{ fontSize: "13px", color: "var(--text-secondary, #666)" }}>Waiting to start...</div>;
  }

  return (
    <div style={{ marginTop: "12px", padding: "12px", backgroundColor: "var(--bg-secondary, #f5f5f5)", borderRadius: "4px" }}>
      {/* Status */}
      <div style={{ marginBottom: "8px", fontSize: "13px", fontWeight: 600 }}>
        Status: {wsStatus}
      </div>

      {/* Progress bar */}
      {wsStatus === "running" && wsProgress && wsProgress.percent !== null && (
        <div style={{ marginBottom: "12px" }}>
          <ProgressBar progress={wsProgress.percent} max={100} showPercentage />
        </div>
      )}

      {/* Frame progress */}
      {wsProgress && (
        <div style={{ fontSize: "13px", color: "var(--text-secondary, #666)" }}>
          <div style={{ marginBottom: "8px" }}>
            Frame: <strong>{wsProgress.current_frame} / {wsProgress.total_frames}</strong>
          </div>

          {/* Current tool */}
          {wsProgress.current_tool && (
            <div style={{ marginBottom: "8px" }}>
              Tool: <strong>{wsProgress.current_tool}</strong>
            </div>
          )}

          {/* Multi-tool progress */}
          {wsProgress.tools_total && wsProgress.tools_total > 1 && (
            <div>
              Tools: {(wsProgress.tools_completed ?? 0) + 1} of {wsProgress.tools_total}
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {wsError && <div style={{ marginTop: "8px", color: "var(--accent-red, #dc3545)" }}>{wsError}</div>}

      {/* Completed */}
      {wsStatus === "completed" && (
        <div style={{ color: "var(--accent-green, #28a745)" }}>✓ Completed</div>
      )}

      {/* Failed */}
      {wsStatus === "failed" && (
        <div style={{ color: "var(--accent-red, #dc3545)" }}>✗ Failed</div>
      )}
    </div>
  );
};
