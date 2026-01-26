// web-ui/src/hooks/useVideoProcessor.ts
import { useEffect, useRef, useState } from "react";

export type FrameResult = Record<string, unknown>;

interface UseVideoProcessorArgs {
  videoRef: React.RefObject<HTMLVideoElement>;
  pluginId: string;
  toolName: string;
  fps: number;
  device: string;
  enabled: boolean;
  bufferSize?: number; // default = 5
}

interface UseVideoProcessorReturn {
  latestResult: FrameResult | null;
  buffer: FrameResult[];
  processing: boolean;
  error: string | null;
  lastTickTime: number | null;
  lastRequestDuration: number | null;
}

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

  // Extract current frame as base64
  const extractFrame = (): string | null => {
    const video = videoRef.current;
    if (!video || video.readyState < 2) return null;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg");
  };

  const processFrame = async () => {
    if (requestInFlight.current) return;
    
    // Guard against empty pluginId or toolName
    if (!pluginId || !toolName) {
      console.error("Frame processing aborted: pluginId or toolName missing");
      return;
    }

    const frameBase64 = extractFrame();
    if (!frameBase64) return;

    requestInFlight.current = true;
    setProcessing(true);
    setLastTickTime(Date.now());

    // Build the correct endpoint URL
    const endpoint = `/v1/plugins/${pluginId}/tools/${toolName}/run`;
    
    // Payload structure matching the API spec in server/app/api.py
    const payload = {
      args: {
        frame_base64: frameBase64,
        device,
        annotated: false,
      },
    };

    const attempt = async (): Promise<Response | null> => {
      try {
        return await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      } catch (err) {
        console.error("Frame processing fetch error:", err);
        return null;
      }
    };

    const start = performance.now();
    let response = await attempt();

    if (!response) {
      // Retry once after 200ms delay
      await new Promise((r) => setTimeout(r, 200));
      response = await attempt();
    }

    const duration = performance.now() - start;
    setLastRequestDuration(duration);

    if (!response) {
      setError("Failed to connect to video processing service");
      requestInFlight.current = false;
      setProcessing(false);
      return;
    }

    try {
      const json = await response.json();
      
      // Handle different response formats
      if (response.ok && json.success !== false) {
        // Success - extract result based on API response structure
        const result = json.result || json;
        setLatestResult(result);
        setBuffer((prev) => {
          const next = [...prev, result];
          return next.length > bufferSize ? next.slice(-bufferSize) : next;
        });
        setError(null);
      } else {
        // API returned an error
        setError(json.detail || json.error || `HTTP ${response.status}: Request failed`);
      }
    } catch {
      setError("Invalid response from video processing service");
    }

    requestInFlight.current = false;
    setProcessing(false);
  };

  useEffect(() => {
    if (!enabled) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = null;
      return;
    }

    const interval = Math.max(1, Math.floor(1000 / fps));
    intervalRef.current = window.setInterval(processFrame, interval);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, fps, device, pluginId, toolName]);

  return {
    latestResult,
    buffer,
    processing,
    error,
    lastTickTime,
    lastRequestDuration,
  };
}

