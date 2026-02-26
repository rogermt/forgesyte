/**
 * React hook for subscribing to job progress via WebSocket.
 *
 * v0.10.0: Real-time progress streaming for video jobs.
 *
 * Features:
 * - WebSocket connection to /ws/jobs/{job_id}
 * - Auto-reconnect on connection loss
 * - Progress event handling
 * - Job status transitions
 */

import { useEffect, useState, useCallback, useRef } from "react";

export interface ProgressEvent {
  job_id: string;
  current_frame: number;
  total_frames: number;
  percent: number;
  current_tool?: string;
  tools_total?: number;
  tools_completed?: number;
}

export interface UseJobProgressResult {
  progress: ProgressEvent | null;
  status: "pending" | "running" | "completed" | "failed";
  error: string | null;
  isConnected: boolean;
}

const RECONNECT_DELAY_MS = 2000;
const PING_INTERVAL_MS = 30000;

/**
 * Hook for subscribing to real-time job progress updates via WebSocket.
 *
 * @param jobId - The job ID to subscribe to, or null to disconnect
 * @returns Progress state and connection status
 */
export function useJobProgress(jobId: string | null): UseJobProgressResult {
  const [progress, setProgress] = useState<ProgressEvent | null>(null);
  const [status, setStatus] = useState<"pending" | "running" | "completed" | "failed">("pending");
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const manualCloseRef = useRef(false);

  const clearTimers = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!jobId) return;

    clearTimers();
    manualCloseRef.current = false;

    // Build WebSocket URL
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/jobs/${jobId}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
      
      // Start ping interval to keep connection alive
      pingIntervalRef.current = setInterval(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: "ping" }));
        }
      }, PING_INTERVAL_MS);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Ignore messages for other jobs (shouldn't happen, but be defensive)
        if (data.job_id && data.job_id !== jobId) return;

        // Handle completion
        if (data.status === "completed") {
          setStatus("completed");
          return;
        }

        // Handle error
        if (data.status === "error") {
          setStatus("failed");
          setError(data.message || "Job failed");
          return;
        }

        // Handle progress
        if (data.current_frame !== undefined) {
          setProgress(data as ProgressEvent);
          setStatus("running");
        }

        // Handle pong (keepalive) - no state change needed
        if (data.type === "pong") {
          // Connection is alive
        }
      } catch (e) {
        console.error("Failed to parse WebSocket message:", e);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      
      // Clear ping interval
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }

      // Don't reconnect if manually closed
      if (manualCloseRef.current) return;

      // Attempt reconnect after delay
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, RECONNECT_DELAY_MS);
    };

    ws.onerror = () => {
      setError("WebSocket connection error");
    };
  }, [jobId, clearTimers]);

  // Effect: Connect/disconnect based on jobId
  useEffect(() => {
    if (!jobId) {
      // Reset state when jobId is null
      setProgress(null);
      setStatus("pending");
      setError(null);
      setIsConnected(false);
      return;
    }

    // Reset state for new jobId
    setProgress(null);
    setStatus("pending");
    setError(null);

    connect();

    // Cleanup on unmount or jobId change
    return () => {
      manualCloseRef.current = true;
      clearTimers();
      
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [jobId, connect, clearTimers]);

  return {
    progress,
    status,
    error,
    isConnected,
  };
}

export default useJobProgress;
