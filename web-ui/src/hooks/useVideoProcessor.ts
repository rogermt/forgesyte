// web-ui/src/hooks/useVideoProcessor.ts
import { useEffect, useRef, useState } from "react";
import { runTool } from "../utils/runTool";
import type {
  FrameResult,
  UseVideoProcessorArgs,
  UseVideoProcessorReturn,
  ProcessFrameLogEntry,
  ProcessFrameMetrics,
} from "./useVideoProcessor.types";

export type { FrameResult };

export function useVideoProcessor({
  videoRef,
  pluginId,
  tools,
  fps,
  device,
  enabled,
  bufferSize = 5,
  debug = false,
}: UseVideoProcessorArgs): UseVideoProcessorReturn {
  const [latestResult, setLatestResult] = useState<FrameResult | null>(null);
  const [buffer, setBuffer] = useState<FrameResult[]>([]);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastTickTime, setLastTickTime] = useState<number | null>(null);
  const [lastRequestDuration, setLastRequestDuration] = useState<number | null>(null);

  // Metrics and logging state
  const [metrics, setMetrics] = useState<ProcessFrameMetrics>({
    totalFrames: 0,
    successfulFrames: 0,
    failedFrames: 0,
    averageDurationMs: 0,
    lastError: undefined,
  });

  const [logs, setLogs] = useState<ProcessFrameLogEntry[]>([]);

  const intervalRef = useRef<number | null>(null);
  const requestInFlight = useRef(false);

  // Debug logging helper
  const log = (...args: unknown[]) => {
    if (debug) {
      console.log("[MP4]", ...args);
    }
  };

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

    // Get data URL and strip the prefix to get raw base64
    // The backend expects raw base64, not data:image/jpeg;base64,...
    const dataUrl = canvas.toDataURL("image/jpeg");
    const rawBase64 = dataUrl.split(",", 2)[1];

    return rawBase64;
  };

  const processFrame = async () => {
    if (requestInFlight.current) return;

    // Guard against empty pluginId or tools
    if (!pluginId || !tools || tools.length === 0) {
      console.error("Frame processing aborted: pluginId or tools missing", {
        pluginId,
        tools,
      });
      return;
    }

    const frameBase64 = extractFrame();
    if (!frameBase64) return;

    requestInFlight.current = true;
    setProcessing(true);

    const frameStartTime = performance.now();
    setLastTickTime(Date.now());

    log("Frame processing started", { pluginId, tool: tools[0] });

    // Use unified runTool with logging and retry
    // Phase 13: For now, execute ONLY the first tool
    const firstTool = tools[0];

    const { result, success, error: runToolError } = await runTool({
      pluginId,
      toolName: firstTool,
      args: {
        frame_base64: frameBase64,
        device,
        annotated: false,
      },
    });

    const durationMs = performance.now() - frameStartTime;
    setLastRequestDuration(durationMs);

    log("Frame processed", { success, durationMs: durationMs.toFixed(1) + "ms" });

    // Update metrics
    setMetrics((prev) => {
      const totalFrames = prev.totalFrames + 1;
      const successfulFrames = prev.successfulFrames + (success ? 1 : 0);
      const failedFrames = prev.failedFrames + (!success ? 1 : 0);
      const averageDurationMs =
        totalFrames === 1
          ? durationMs
          : (prev.averageDurationMs * prev.totalFrames + durationMs) / totalFrames;

      return {
        totalFrames,
        successfulFrames,
        failedFrames,
        averageDurationMs,
        lastError: success ? prev.lastError : runToolError ?? prev.lastError,
      };
    });

    // Add log entry
    setLogs((prev) => [
      ...prev,
      {
        timestamp: Date.now(),
        pluginId,
        tools,
        durationMs,
        success,
        error: runToolError,
        retryCount: 0, // Retry handled internally by runTool
      },
    ]);

    if (success && result) {
      log("Frame result received", result);
      setLatestResult(result);
      setBuffer((prev) => {
        const next = [...prev, result];
        return next.length > bufferSize ? next.slice(-bufferSize) : next;
      });
      setError(null);
    } else if (!success) {
      log("Frame processing failed", { error: runToolError });
      setError(runToolError ?? "Frame processing failed");
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
  }, [enabled, fps, device, pluginId, tools]);

  return {
    latestResult,
    buffer,
    processing,
    error,
    lastTickTime,
    lastRequestDuration,
    metrics,
    logs,
  };
}

