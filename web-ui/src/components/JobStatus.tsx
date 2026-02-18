import React, { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import { JobResults } from "./JobResults";

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
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<VideoJobResults | null>(null);

  useEffect(() => {
    let timer: number | undefined;

    const poll = async () => {
      try {
        const s = await apiClient.getVideoJobStatus(jobId);
        setStatus(s.status);

        if (s.status === "completed") {
          const r = await apiClient.getVideoJobResults(jobId);
          setResults(r as VideoJobResults);
          return;
        }

        if (s.status === "failed") {
          setError("Job failed.");
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
      {error && <div style={{ color: "red" }}>{error}</div>}
      {results && <JobResults results={results} />}
    </div>
  );
};