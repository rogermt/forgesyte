import React, { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import { JobResults } from "./JobResults";
import { ProgressBar } from "./ProgressBar";

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
  const [status, setStatus] = useState<Status>("pending");
  const [progress, setProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<VideoJobResults | null>(null);

  useEffect(() => {
    let timer: number | undefined;

    const poll = async () => {
      try {
        const job = await apiClient.getJob(jobId);
        setStatus(job.status as Status);
        setProgress(job.progress ?? null);
        setError(null); // Clear any previous error on successful fetch

        if (job.status === "completed" && job.results) {
          setResults(job.results as VideoJobResults);
          return;
        }

        if (job.status === "failed") {
          setError(job.error_message || job.error || "Job failed.");
          return;
        }

        timer = window.setTimeout(poll, 2000);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Status polling failed.");
      }
    };

    poll();

    return () => {
      if (timer) window.clearTimeout(timer);
    };
  }, [jobId]);

  return (
    <div style={{ marginTop: "10px" }}>
      <div>Status: {status}</div>

      {/* v0.9.6: Show progress bar when running and progress is available */}
      {status === "running" && progress !== null && (
        <div style={{ marginTop: "10px", marginBottom: "10px" }}>
          <ProgressBar progress={progress} max={100} showPercentage />
        </div>
      )}

      {/* Show indeterminate progress when running but no progress data yet */}
      {status === "running" && progress === null && (
        <div style={{ marginTop: "10px", marginBottom: "10px", color: "#666" }}>
          Processing... (progress not available)
        </div>
      )}

      {error && <div style={{ color: "red" }}>{error}</div>}
      {results && <JobResults results={results} />}
    </div>
  );
};