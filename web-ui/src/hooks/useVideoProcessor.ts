/**
 * useVideoProcessor Hook
 *
 * Generic frame-processing hook for video-based tools.
 * - Extracts current frame from <video> as base64
 * - Sends to /plugins/run endpoint
 * - Maintains rolling buffer of results
 * - One frame per tick (no parallel requests)
 * - Plugin-agnostic (no YOLO assumptions)
 */

import { useRef, useEffect, useCallback, useState } from "react";

// ============================================================================
// Types
// ============================================================================

export type FrameResult = Record<string, unknown>;

export interface UseVideoProcessorArgs {
  videoRef: React.RefObject<HTMLVideoElement>;
  pluginId: string;
  toolName: string;
  fps: number;
  device: string;
  enabled: boolean;
  bufferSize?: number; // default 5
}

export interface UseVideoProcessorReturn {
  latestResult: FrameResult | null;
  buffer: FrameResult[];
  processing: boolean;
  error: string | null;
}

// ============================================================================
// Hook
// ============================================================================

export function useVideoProcessor({
  videoRef,
  pluginId,
  toolName,
  fps,
  device,
  enabled,
  bufferSize = 5,
}: UseVideoProcessorArgs): UseVideoProcessorReturn {
  // -------------------------------------------------------------------------
  // State
  // -------------------------------------------------------------------------

  const [latestResult, setLatestResult] = useState<FrameResult | null>(null);
  const [buffer, setBuffer] = useState<FrameResult[]>([]);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // -------------------------------------------------------------------------
  // Refs (not re-render state)
  // -------------------------------------------------------------------------

  const requestInFlightRef = useRef(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // -------------------------------------------------------------------------
  // Frame extraction utility
  // -------------------------------------------------------------------------

  const extractFrameAsBase64 = useCallback((): string | null => {
    const video = videoRef.current;
    if (!video) return null;

    // Check if video has enough data to draw a frame
    if (video.readyState < 2) return null;

    // Create offscreen canvas if needed
    if (!canvasRef.current) {
      canvasRef.current = document.createElement("canvas");
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw current frame
    try {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      return canvas.toDataURL("image/jpeg");
    } catch (err) {
      console.error("Failed to extract frame:", err);
      return null;
    }
  }, [videoRef]);

  // -------------------------------------------------------------------------
  // Backend call
  // -------------------------------------------------------------------------

  const sendFrameToBackend = useCallback(
    async (frameBase64: string): Promise<FrameResult | null> => {
      try {
        const response = await fetch(`/plugins/${pluginId}/tools/${toolName}/run`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            plugin_id: pluginId,
            tool_name: toolName,
            inputs: {
              frame_base64: frameBase64,
              device,
              annotated: false,
            },
          }),
        });

        if (!response.ok) {
          throw new Error(`Backend error: ${response.statusText}`);
        }

        const result = (await response.json()) as FrameResult;
        return result;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error";
        throw new Error(`Failed to process frame: ${message}`);
      }
    },
    [pluginId, toolName, device]
  );

  // -------------------------------------------------------------------------
  // Retry logic
  // -------------------------------------------------------------------------

  const sendFrameWithRetry = useCallback(
    async (frameBase64: string): Promise<FrameResult | null> => {
      try {
        return await sendFrameToBackend(frameBase64);
      } catch (firstErr) {
        setError(`Request failed: ${firstErr}`);

        // Retry once after 200ms
        await new Promise((resolve) => setTimeout(resolve, 200));

        try {
          const result = await sendFrameToBackend(frameBase64);
          setError(null); // Clear error on success
          return result;
        } catch (retryErr) {
          setError(
            `Retry failed: ${retryErr instanceof Error ? retryErr.message : "Unknown error"}`
          );
          return null;
        }
      }
    },
    [sendFrameToBackend]
  );

  // -------------------------------------------------------------------------
  // Main processing loop
  // -------------------------------------------------------------------------

  const processFrame = useCallback(async () => {
    // Skip if already processing
    if (requestInFlightRef.current) return;

    // Extract frame
    const frameBase64 = extractFrameAsBase64();
    if (!frameBase64) return;

    // Mark as in-flight
    requestInFlightRef.current = true;
    setProcessing(true);

    try {
      const result = await sendFrameWithRetry(frameBase64);

      if (result) {
        // Update latest result
        setLatestResult(result);

        // Update rolling buffer
        setBuffer((prev) => {
          const updated = [result, ...prev];
          return updated.slice(0, bufferSize);
        });
      }
    } finally {
      requestInFlightRef.current = false;
      setProcessing(false);
    }
  }, [extractFrameAsBase64, sendFrameWithRetry, bufferSize]);

  // -------------------------------------------------------------------------
  // Interval management
  // -------------------------------------------------------------------------

  useEffect(() => {
    // Clean up existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    if (!enabled) return;

    // Calculate interval (clamp fps to minimum 1)
    const clampedFps = Math.max(1, fps);
    const interval = Math.max(1, Math.floor(1000 / clampedFps));

    // Start processing loop
    intervalRef.current = setInterval(() => {
      processFrame();
    }, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [enabled, fps, processFrame]);

  // -------------------------------------------------------------------------
  // Cleanup on unmount
  // -------------------------------------------------------------------------

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  // -------------------------------------------------------------------------
  // Return
  // -------------------------------------------------------------------------

  return {
    latestResult,
    buffer,
    processing,
    error,
  };
}

export default useVideoProcessor;
