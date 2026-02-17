/**
 * Phase 17 CameraPreview Component
 *
 * Captures webcam frames and sends binary JPEG data via WebSocket
 */

import { useEffect, useRef, useState } from "react";
import { useRealtime } from "../realtime/useRealtime";

export interface CameraPreviewProps {
  enabled?: boolean;
}

export function CameraPreview({ enabled = true }: CameraPreviewProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number>();

  const [error, setError] = useState<string | null>(null);
  const [fps, setFps] = useState(15);

  const realtime = useRealtime();

  // Start camera stream
  useEffect(() => {
    if (!enabled) return;

    let stream: MediaStream | null = null;

    async function startCamera() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 1280, height: 720 },
          audio: false,
        });

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
          setError(null);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to access camera");
      }
    }

    startCamera();

    return () => {
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, [enabled]);

  // Capture and send frames
  useEffect(() => {
    if (!enabled || !videoRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let lastFrameTime = 0;
    const frameInterval = 1000 / fps;

    function captureFrame(timestamp: number) {
      if (!enabled || !videoRef.current || !canvasRef.current) return;

      const elapsed = timestamp - lastFrameTime;

      if (elapsed >= frameInterval) {
        lastFrameTime = timestamp - (elapsed % frameInterval);

        // Draw video frame to canvas
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);

        // Convert to JPEG blob
        canvas.toBlob(
          (blob) => {
            if (blob) {
              blob.arrayBuffer().then((buffer) => {
                const uint8Array = new Uint8Array(buffer);
                realtime.sendFrame(uint8Array);
              });
            }
          },
          "image/jpeg",
          0.8
        );
      }

      animationFrameRef.current = requestAnimationFrame(captureFrame);
    }

    animationFrameRef.current = requestAnimationFrame(captureFrame);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [enabled, fps, realtime]);

  // Handle slow-down warnings
  useEffect(() => {
    if (realtime.state.slowDownWarnings > 0) {
      setFps(5); // Reduce FPS on slow-down
    } else {
      setFps(15); // Restore FPS
    }
  }, [realtime.state.slowDownWarnings]);

  return (
    <div className="camera-preview">
      {error && (
        <div className="error-message">{error}</div>
      )}
      <video
        ref={videoRef}
        className="camera-video"
        autoPlay
        playsInline
        muted
      />
      <canvas ref={canvasRef} style={{ display: "none" }} />
      <div className="camera-status">
        {realtime.state.status === "connected" ? (
          <span className="status-connected">● Streaming ({fps} FPS)</span>
        ) : (
          <span className="status-disconnected">○ Not connected</span>
        )}
      </div>
    </div>
  );
}

export default CameraPreview;
