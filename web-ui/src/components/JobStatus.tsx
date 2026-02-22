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
        const job = await apiClient.getJob(jobId);
        setStatus(job.status as Status);

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
      {error && <div style={{ color: "red" }}>{error}</div>}
      {results && <JobResults results={results} />}
    </div>
  );
};