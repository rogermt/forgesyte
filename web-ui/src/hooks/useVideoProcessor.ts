// web-ui/src/hooks/useVideoProcessor.ts
import { useCallback, useEffect, useRef, useState } from "react";

import type {
  FrameResult,
  UseVideoProcessorArgs,
  UseVideoProcessorReturn,
} from "./useVideoProcessor.types";

export type { FrameResult };

export function useVideoProcessor({
  videoRef,
  pluginId,
  toolName,
  fps,
  device,
  enabled,
  bufferSize = 5,
}: UseVideoProcessorArgs): UseVideoProcessorReturn {
  const [latestResult, setLatestResult] = useState<FrameResult | null>(null);
  const [buffer, setBuffer] = useState<FrameResult[]>([]);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastTickTime, setLastTickTime] = useState<number | null>(null);
  const [lastRequestDuration, setLastRequestDuration] = useState<number | null>(null);

  const intervalRef = useRef<number | null>(null);
  const requestInFlight = useRef(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const mountedRef = useRef(true);

  // Extract current frame as base64 - reuse canvas
  const extractFrame = useCallback((): string | null => {
    const video = videoRef.current;
    if (!video || video.readyState < 2) return null;

    // Reuse or create canvas
    if (!canvasRef.current) {
      canvasRef.current = document.createElement("canvas");
    }
    const canvas = canvasRef.current;

    // Only resize if dimensions changed
    if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
    }

    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const dataUrl = canvas.toDataURL("image/jpeg", 0.8); // Quality 0.8 for smaller payloads
    const rawBase64 = dataUrl.split(",", 2)[1];

    return rawBase64;
  }, [videoRef]);

  const processFrame = useCallback(async () => {
    if (requestInFlight.current) return;

    if (!pluginId || !toolName) {
      return;
    }

    const frameBase64 = extractFrame();
    if (!frameBase64) return;

    requestInFlight.current = true;

    if (mountedRef.current) {
      setProcessing(true);
      setLastTickTime(Date.now());
    }

    const endpoint = `/v1/plugins/${pluginId}/tools/${toolName}/run`;

    const payload = {
      args: {
        frame_base64: frameBase64,
        device,
        annotated: false,
      },
    };

    // Create new AbortController for this request
    abortControllerRef.current = new AbortController();

    const attempt = async (): Promise<Response | null> => {
      try {
        return await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: abortControllerRef.current?.signal,
        });
      } catch (err) {
        if (err instanceof Error && err.name === "AbortError") {
          return null; // Request was cancelled, don't log as error
        }
        console.error("Frame processing fetch error:", err);
        return null;
      }
    };

    const start = performance.now();
    let response = await attempt();

    if (!response && mountedRef.current && !abortControllerRef.current?.signal.aborted) {
      // Retry once after 200ms delay
      await new Promise((r) => setTimeout(r, 200));
      response = await attempt();
    }

    const duration = performance.now() - start;

    // Guard all state updates with mounted check
    if (!mountedRef.current) {
      requestInFlight.current = false;
      return;
    }

    setLastRequestDuration(duration);

    if (!response) {
      if (!abortControllerRef.current?.signal.aborted) {
        setError("Failed to connect to video processing service");
      }
      requestInFlight.current = false;
      setProcessing(false);
      return;
    }

    try {
      const json = await response.json();

      if (!mountedRef.current) {
        requestInFlight.current = false;
        return;
      }

      if (response.ok && json.success !== false) {
        const result = json.result || json;
        setLatestResult(result);
        setBuffer((prev) => {
          const next = [...prev, result];
          return next.length > bufferSize ? next.slice(-bufferSize) : next;
        });
        setError(null);
      } else {
        setError(json.detail || json.error || `HTTP ${response.status}: Request failed`);
      }
    } catch {
      if (mountedRef.current) {
        setError("Invalid response from video processing service");
      }
    }

    requestInFlight.current = false;
    if (mountedRef.current) {
      setProcessing(false);
    }
  }, [pluginId, toolName, device, bufferSize, extractFrame]);

  useEffect(() => {
    mountedRef.current = true;

    return () => {
      mountedRef.current = false;
      // Cancel any in-flight request on unmount
      abortControllerRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    if (!enabled) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      // Cancel in-flight request when disabled
      abortControllerRef.current?.abort();
      return;
    }

    const interval = Math.max(1, Math.floor(1000 / fps));
    intervalRef.current = window.setInterval(processFrame, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [enabled, fps, processFrame, bufferSize]);

  return {
    latestResult,
    buffer,
    processing,
    error,
    lastTickTime,
    lastRequestDuration,
  };
}
