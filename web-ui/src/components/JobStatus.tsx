import React, { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import { JobResults } from "./JobResults";
import { ProgressBar } from "./ProgressBar";
import { useJobProgress } from "../hooks/useJobProgress";

type Props = {
  jobId: string;
};

type Status = "pending" | "running" | "completed" | "failed";

type VideoJobResults = {
  job_id: string;
  results: {
    text?: string;
    detections?: Array<{
      label: string;
      confidence: number;
      bbox: number[];
    }>;
  } | null;
  created_at: string;
  updated_at: string;
};

export const JobStatus: React.FC<Props> = ({ jobId }) => {
  // WebSocket progress (primary source)
  const {
    progress: wsProgress,
    status: wsStatus,
    error: wsError,
    isConnected,
  } = useJobProgress(jobId);

  // HTTP polling fallback
  const [pollProgress, setPollProgress] = useState<number | null>(null);
  const [pollStatus, setPollStatus] = useState<Status>("pending");
  const [results, setResults] = useState<VideoJobResults | null>(null);
  const [pollError, setPollError] = useState<string | null>(null);

  // Determine which source to use
  const useWebSocket = isConnected && wsStatus !== "pending";
  const currentProgress = useWebSocket ? wsProgress?.percent ?? null : pollProgress;
  const currentStatus = useWebSocket ? wsStatus : pollStatus;
  const currentError = wsError || pollError;

  // HTTP polling fallback (when WebSocket not connected)
  useEffect(() => {
    if (isConnected || !jobId) return;

    let timer: number | undefined;

    const poll = async () => {
      try {
        const job = await apiClient.getJob(jobId);
        setPollStatus(job.status as Status);
        setPollProgress(job.progress ?? null);
        setPollError(null);

        if (job.status === "completed" && job.results) {
          setResults(job.results as VideoJobResults);
          return;
        }

        if (job.status === "failed") {
          setPollError(job.error_message || job.error || "Job failed.");
          return;
        }

        timer = window.setTimeout(poll, 2000);
      } catch (e: unknown) {
        setPollError(e instanceof Error ? e.message : "Status polling failed.");
      }
    };

    poll();

    return () => {
      if (timer) window.clearTimeout(timer);
    };
  }, [jobId, isConnected]);

  // Render progress info from WebSocket
  const renderProgressInfo = () => {
    if (!wsProgress) return null;

    return (
      <div style={{ marginTop: "8px", fontSize: "13px", color: "var(--text-secondary, #666)" }}>
        <span>Frame: {wsProgress.current_frame} / {wsProgress.total_frames}</span>
        {wsProgress.current_tool && (
          <span style={{ marginLeft: "12px" }}>
            Tool: <strong>{wsProgress.current_tool}</strong>
          </span>
        )}
        {wsProgress.tools_total && wsProgress.tools_total > 1 && (
          <span style={{ marginLeft: "12px" }}>
            Tool: {wsProgress.tools_completed !== undefined ? wsProgress.tools_completed + 1 : "?"} of {wsProgress.tools_total}
          </span>
        )}
      </div>
    );
  };

  return (
    <div style={{ marginTop: "10px" }}>
      {/* Connection indicator */}
      <div style={{ marginBottom: "8px", fontSize: "12px" }}>
        {isConnected ? (
          <span title="WebSocket connected" style={{ color: "#22c55e" }}>
            ● Live
          </span>
        ) : (
          <span title="Using HTTP polling" style={{ color: "#f59e0b" }}>
            ○ Polling
          </span>
        )}
      </div>

      {/* Status display */}
      <div>Status: {currentStatus}</div>

      {/* Progress bar */}
      {currentStatus === "running" && currentProgress !== null && (
        <div style={{ marginTop: "10px", marginBottom: "10px" }}>
          <ProgressBar progress={currentProgress} max={100} showPercentage />
          {useWebSocket && renderProgressInfo()}
        </div>
      )}

      {/* Indeterminate progress */}
      {currentStatus === "running" && currentProgress === null && (
        <div style={{ marginTop: "10px", marginBottom: "10px", color: "#666" }}>
          Processing... (progress not available)
        </div>
      )}

      {/* Error display */}
      {currentError && <div style={{ color: "red" }}>{currentError}</div>}
      
      {/* Results display */}
      {currentStatus === "completed" && results && <JobResults results={results} />}
    </div>
  );
};
