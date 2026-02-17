/**
 * useMP4Upload Hook - Phase 17
 *
 * Handles MP4 video upload for async YOLO inference:
 * 1. Upload MP4 to backend via /v1/video/submit
 * 2. Backend creates job and returns job_id
 * 3. Poll job status via /api/jobs/{job_id}
 * 4. Update progress and state
 *
 * Critical Rule: NEVER hardcode pipeline IDs. The backend chooses the pipeline.
 */

import { useRef, useState } from "react";
import { apiClient } from "../api/client";

export type MP4UploadStatus =
  | "idle"
  | "uploading"
  | "processing"
  | "completed"
  | "error"
  | "cancelled";

export interface MP4UploadState {
  status: MP4UploadStatus;
  jobId: string | null;
  progress: number;
  framesProcessed: number;
  errorMessage: string | null;
}

export function useMP4Upload(debug = false) {
  const [state, setState] = useState<MP4UploadState>({
    status: "idle",
    jobId: null,
    progress: 0,
    framesProcessed: 0,
    errorMessage: null,
  });

  const cancelled = useRef(false);

  const log = (...args: unknown[]) => {
    if (debug) {
      console.log("[useMP4Upload]", ...args);
    }
  };

  async function start(file: File) {
    cancelled.current = false;

    try {
      setState((s) => ({ ...s, status: "uploading" }));

      log("Uploading MP4:", file.name, file.size);

      // Step 1: Upload file to backend
      const { job_id } = await apiClient.uploadVideo(file);
      log("Job created:", job_id);

      setState((s) => ({
        ...s,
        status: "processing",
        jobId: job_id,
      }));

      // Step 2: Poll job status until completion
      while (!cancelled.current) {
        const job = await apiClient.getJob(job_id);

        setState((s) => ({
          ...s,
          progress: job.progress ?? 0,
          framesProcessed: job.frames_processed ?? 0,
        }));

        log("Job status:", job.status, "Progress:", job.progress);

        if (job.status === "done") {
          setState((s) => ({ ...s, status: "completed" }));
          log("Job completed:", job_id);
          return;
        }

        if (job.status === "error") {
          setState((s) => ({
            ...s,
            status: "error",
            errorMessage: job.error ?? "Unknown error",
          }));
          log("Job error:", job.error);
          return;
        }

        // Wait before next poll
        await new Promise((resolve) => setTimeout(resolve, 500));
      }

      // If cancelled
      setState((s) => ({ ...s, status: "cancelled" }));
      log("Job cancelled:", job_id);
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Upload failed";
      setState((s) => ({
        ...s,
        status: "error",
        errorMessage,
      }));
      log("Upload error:", errorMessage);
    }
  }

  function cancel() {
    cancelled.current = true;
    log("Cancelling upload...");
  }

  function reset() {
    cancelled.current = false;
    setState({
      status: "idle",
      jobId: null,
      progress: 0,
      framesProcessed: 0,
      errorMessage: null,
    });
    log("Reset state");
  }

  return {
    state,
    start,
    cancel,
    reset,
  };
}

export default useMP4Upload;