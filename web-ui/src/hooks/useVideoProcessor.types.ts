/**
 * Type definitions for useVideoProcessor hook
 * Used for logging, metrics, and unified tool runner integration
 */

export type FrameResult = Record<string, unknown>;

export interface UseVideoProcessorArgs {
  videoRef: React.RefObject<HTMLVideoElement>;
  pluginId: string;
  toolName: string;
  fps: number;
  device: string;
  enabled: boolean;
  bufferSize?: number;
}

export interface UseVideoProcessorReturn {
  latestResult: FrameResult | null;
  buffer: FrameResult[];
  processing: boolean;
  error: string | null;
  lastTickTime: number | null;
  lastRequestDuration: number | null;
  metrics?: ProcessFrameMetrics;
  logs?: ProcessFrameLogEntry[];
}

/**
 * Log entry for each frame processing attempt
 */
export interface ProcessFrameLogEntry {
  timestamp: number;
  pluginId: string;
  toolName: string;
  durationMs: number;
  success: boolean;
  error?: string;
  retryCount: number;
}

/**
 * Aggregated metrics for frame processing
 */
export interface ProcessFrameMetrics {
  totalFrames: number;
  successfulFrames: number;
  failedFrames: number;
  averageDurationMs: number;
  lastError?: string;
}
