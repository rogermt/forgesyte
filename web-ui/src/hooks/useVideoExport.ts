/**
 * useVideoExport Hook
 * Records canvas overlays and exports as MP4 video
 *
 * Features:
 * - Records canvas stream to MediaRecorder
 * - Converts to MP4/WebM blob
 * - Auto-download or return blob for custom handling
 * - Frame rate control (30fps default)
 */

import { useCallback, useRef, useState } from "react";

// ============================================================================
// Types
// ============================================================================

export interface VideoExportConfig {
  width: number;
  height: number;
  fps?: number;
  mimeType?: string;
}

export interface VideoExportState {
  isRecording: boolean;
  error?: string;
  progress: number; // 0-100
}

// ============================================================================
// Hook
// ============================================================================

export function useVideoExport(config: VideoExportConfig | null) {
  const [state, setState] = useState<VideoExportState>({
    isRecording: false,
    progress: 0,
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startTimeRef = useRef<number>(0);
  const frameCountRef = useRef<number>(0);

  // -------------------------------------------------------------------------
  // Start recording
  // -------------------------------------------------------------------------
  const startRecording = useCallback(
    (canvas: HTMLCanvasElement) => {
      if (!config) {
        setState((prev) => ({
          ...prev,
          error: "No export config provided",
        }));
        return;
      }

      try {
        canvasRef.current = canvas;
        chunksRef.current = [];
        frameCountRef.current = 0;
        startTimeRef.current = Date.now();

        // Get canvas stream
        const stream = canvas.captureStream(config.fps || 30);

        // Determine MIME type
        const mimeType = config.mimeType || "video/webm;codecs=vp9";
        const supportedMimeTypes = [
          "video/webm;codecs=vp9",
          "video/webm;codecs=vp8",
          "video/webm",
          "video/mp4",
        ];

        let selectedMimeType = mimeType;
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          selectedMimeType = supportedMimeTypes.find((type) =>
            MediaRecorder.isTypeSupported(type)
          ) || "video/webm";
        }

        // Create media recorder
        const mediaRecorder = new MediaRecorder(stream, {
          mimeType: selectedMimeType,
        });

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            chunksRef.current.push(event.data);
          }
        };

        mediaRecorder.onerror = (event) => {
          setState((prev) => ({
            ...prev,
            error: `Recording error: ${event.error}`,
            isRecording: false,
          }));
        };

        mediaRecorderRef.current = mediaRecorder;
        mediaRecorder.start();

        setState({
          isRecording: true,
          progress: 0,
        });
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to start recording";
        setState((prev) => ({
          ...prev,
          error: message,
        }));
      }
    },
    [config]
  );

  // -------------------------------------------------------------------------
  // Stop recording and export
  // -------------------------------------------------------------------------
  const stopRecording = useCallback(
    async (
      filename: string = "video-tracker.webm"
    ): Promise<Blob | null> => {
      return new Promise((resolve) => {
        const mediaRecorder = mediaRecorderRef.current;
        if (!mediaRecorder) {
          setState((prev) => ({
            ...prev,
            error: "Not recording",
          }));
          resolve(null);
          return;
        }

        mediaRecorder.onstop = () => {
          try {
            // Create blob from chunks
            const mimeType = mediaRecorder.mimeType || "video/webm";
            const blob = new Blob(chunksRef.current, { type: mimeType });

            // Auto-download
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);

            setState({
              isRecording: false,
              progress: 100,
            });

            resolve(blob);
          } catch (err) {
            const message =
              err instanceof Error ? err.message : "Failed to export video";
            setState((prev) => ({
              ...prev,
              error: message,
              isRecording: false,
            }));
            resolve(null);
          }
        };

        mediaRecorder.stop();
      });
    },
    []
  );

  // -------------------------------------------------------------------------
  // Update progress
  // -------------------------------------------------------------------------
  const updateProgress = useCallback((current: number, total: number) => {
    const progress = Math.round((current / total) * 100);
    setState((prev) => ({
      ...prev,
      progress,
    }));
  }, []);

  // -------------------------------------------------------------------------
  // Cancel recording
  // -------------------------------------------------------------------------
  const cancelRecording = useCallback(() => {
    const mediaRecorder = mediaRecorderRef.current;
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
      chunksRef.current = [];
    }
    setState({
      isRecording: false,
      progress: 0,
    });
  }, []);

  return {
    state,
    startRecording,
    stopRecording,
    cancelRecording,
    updateProgress,
  };
}

export default useVideoExport;
