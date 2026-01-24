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

    const frameBase64 = extractFrame();
    if (!frameBase64) return;

    requestInFlight.current = true;
    setProcessing(true);
    setLastTickTime(Date.now());

    const payload = {
      plugin_id: pluginId,
      tool_name: toolName,
      inputs: {
        frame_base64: frameBase64,
        device,
        annotated: false,
      },
    };

    const attempt = async (): Promise<Response | null> => {
      try {
        return await fetch("/plugins/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      } catch {
        return null;
      }
    };

    const start = performance.now();
    let response = await attempt();

    if (!response) {
      await new Promise((r) => setTimeout(r, 200));
      response = await attempt();
    }

    const duration = performance.now() - start;
    setLastRequestDuration(duration);

    if (!response) {
      setError("Failed to process frame");
      requestInFlight.current = false;
      setProcessing(false);
      return;
    }

    try {
      const json = await response.json();
      if (json.success) {
        setLatestResult(json.result);
        setBuffer((prev) => {
          const next = [...prev, json.result];
          return next.length > bufferSize ? next.slice(-bufferSize) : next;
        });
        setError(null);
      } else {
        setError(json.error || "Unknown backend error");
      }
    } catch {
      setError("Invalid JSON response");
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

