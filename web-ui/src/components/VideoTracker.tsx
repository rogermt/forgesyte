/**
 * VideoTracker Component - Phase 17
 *
 * MP4 upload for async YOLO inference:
 * - Upload MP4 to backend via /v1/video/submit
 * - Backend creates job and returns job_id
 * - Poll job status until completion
 * - Display progress and errors
 *
 * Critical Rule: NEVER hardcode pipeline IDs. The backend chooses the pipeline.
 */

import React, { useState } from "react";
import { useVideoProcessor } from "../hooks/useVideoProcessor";
import { drawDetections, type OverlayToggles } from "./ResultOverlay";
import type { Detection } from "../types/plugin";
import { MP4ProcessingProvider } from "../mp4/MP4ProcessingContext";

// ============================================================================
// Types
// ============================================================================

export interface VideoTrackerProps {
  pluginId: string;   // routing only
  tools: string[];   // routing only
  debug?: boolean;    // FE-8: Golden Path Debug Mode
}

export function VideoTracker({ debug }: VideoTrackerProps) {
  const [file, setFile] = useState<File | null>(null);

const styles = {
  container: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "20px",
    padding: "20px",
    maxWidth: "1400px",
    margin: "0 auto",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "20px",
    paddingBottom: "20px",
    borderBottom: "1px solid var(--border-light)",
  },
  title: {
    margin: 0,
    fontSize: "24px",
    fontWeight: 600,
    color: "var(--text-primary)",
  },
  subtitle: {
    fontSize: "12px",
    color: "var(--text-secondary)",
  },
  uploadRow: {
    display: "flex",
    gap: "12px",
    alignItems: "center",
  },
  button: {
    padding: "10px 16px",
    borderRadius: "6px",
    fontSize: "13px",
    fontWeight: 500,
    border: "1px solid var(--border-light)",
    backgroundColor: "var(--bg-tertiary)",
    color: "var(--text-primary)",
    cursor: "pointer",
    transition: "all 0.2s",
  },
  buttonActive: {
    backgroundColor: "var(--accent-primary)",
    color: "white",
    borderColor: "var(--accent-primary)",
  },
  videoSection: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "12px",
  },
  videoContainer: {
    position: "relative" as const,
    backgroundColor: "black",
    borderRadius: "8px",
    overflow: "hidden",
    border: "1px solid var(--border-light)",
    aspectRatio: "16 / 9",
    width: "100%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  video: {
    width: "100%",
    height: "100%",
    display: "block",
  },
  canvas: {
    position: "absolute" as const,
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
  },
  placeholderText: {
    color: "var(--text-muted)",
    margin: 0,
  },
  controlsRow: {
    display: "flex",
    gap: "12px",
    alignItems: "center",
    flexWrap: "wrap" as const,
  },
  dropdown: {
    padding: "8px 12px",
    borderRadius: "6px",
    fontSize: "13px",
    border: "1px solid var(--border-light)",
    backgroundColor: "var(--bg-tertiary)",
    color: "var(--text-primary)",
    cursor: "pointer",
  },
  divider: {
    height: "1px",
    backgroundColor: "var(--border-light)",
  },
  togglesRow: {
    display: "flex",
    gap: "20px",
    alignItems: "center",
    flexWrap: "wrap" as const,
  },
  toggleItem: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
  },
  toggleLabel: {
    fontSize: "13px",
    color: "var(--text-primary)",
    userSelect: "none" as const,
  },
  fileNameLabel: {
    fontSize: "12px",
    color: "var(--text-secondary)",
  },
  statusRow: {
    display: "flex",
    gap: "20px",
    alignItems: "center",
    fontSize: "12px",
    color: "var(--text-secondary)",
  },
  statusItem: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
  },
  processingIndicator: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    backgroundColor: "var(--accent-warning)",
  },
  processingIndicatorActive: {
    backgroundColor: "var(--accent-success)",
  },
} as const;

// ============================================================================
// Constants
// ============================================================================

const FPS_OPTIONS = [5, 10, 15, 24, 30, 45, 60];
const OVERLAY_KEYS = ["players", "tracking", "ball", "pitch", "radar"] as const;

// ============================================================================
// Component
// ============================================================================

export function VideoTracker({ pluginId, tools, debug = false }: VideoTrackerProps) {
  // -------------------------------------------------------------------------
  // Refs
  // -------------------------------------------------------------------------
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // -------------------------------------------------------------------------
  // State
  // -------------------------------------------------------------------------
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoSrc, setVideoSrc] = useState<string | null>(null);
  const [fps, setFps] = useState(30);
  const [device, setDevice] = useState<"cpu" | "cuda">("cpu");
  const [running, setRunning] = useState(false);
  const [overlayToggles, setOverlayToggles] = useState<OverlayToggles>({
    players: true,
    tracking: true,
    ball: true,
    pitch: true,
    radar: true,
  });

  // -------------------------------------------------------------------------
  // Video processing hook
  // -------------------------------------------------------------------------
  const {
    latestResult,
    buffer,
    processing,
    error,
    lastRequestDuration,
    metrics,
  } = useVideoProcessor({
    videoRef,
    pluginId,
    tools,
    fps,
    device,
    enabled: running,
    debug,
  });

  // -------------------------------------------------------------------------
  // Effects
  // -------------------------------------------------------------------------

  // Revoke blob URL on cleanup
  useEffect(() => {
    return () => {
      if (videoSrc) {
        URL.revokeObjectURL(videoSrc);
      }
    };
  }, [videoSrc]);

  // Draw overlay when latestResult changes
  useEffect(() => {
    if (!canvasRef.current || !videoRef.current) return;
    if (!latestResult) return;

    // Ensure canvas matches video resolution
    canvasRef.current.width = videoRef.current.videoWidth;
    canvasRef.current.height = videoRef.current.videoHeight;

    // Extract detections array from the result
    // The API returns { detections: Detection[] } or Detection[] directly
    const detections = Array.isArray(latestResult)
      ? latestResult
      : (latestResult as Record<string, unknown>).detections as Detection[];

    if (!detections || detections.length === 0) return;

    // Extract pitch lines from the result if available
    const pitchLines = (latestResult as Record<string, unknown>)?.pitch as Array<{ x1: number; y1: number; x2: number; y2: number }> | undefined;

    // Call drawDetections function to draw on the canvas
    drawDetections({
      canvas: canvasRef.current,
      detections,
      width: videoRef.current.videoWidth,
      height: videoRef.current.videoHeight,
      overlayToggles,
      pitchLines,
    });
  }, [latestResult, buffer, overlayToggles]);

  // -------------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------------

  const handleVideoUpload = useCallback(() => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "video/*";
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file && file.type.startsWith("video/")) {
        // Revoke previous URL if exists
        if (videoSrc) {
          URL.revokeObjectURL(videoSrc);
        }
        const newSrc = URL.createObjectURL(file);
        setVideoFile(file);
        setVideoSrc(newSrc);
        setRunning(false); // Stop processing on new video
      }
    };
    input.click();
  }, [videoSrc]);

  const handlePlay = useCallback(() => {
    setRunning(true);
    videoRef.current?.play();
  }, []);

  const handlePause = useCallback(() => {
    setRunning(false);
    videoRef.current?.pause();
  }, []);

  const handleToggle = (key: typeof OVERLAY_KEYS[number]) => {
    setOverlayToggles((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0] ?? null;
    if (selected) {
      upload.start(selected);
    }
  };

  // Calculate MP4 processing state for debug panel
  const mp4State = {
    active: processing,
    jobId: null, // MP4 upload doesn't use job IDs in the same way as streaming
    progress: metrics ? (metrics.totalFrames > 0 ? Math.round((metrics.successfulFrames / metrics.totalFrames) * 100) : 0) : 0,
    framesProcessed: metrics?.totalFrames ?? 0,
  };

  return (
    <MP4ProcessingProvider value={mp4State}>
      <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>VideoTracker</h1>
        <div style={styles.subtitle}>
          Plugin: <strong>{pluginId}</strong> | Tools: <strong>{tools.join(", ")}</strong>
        </div>
      </div>

        {upload.state.status === "idle" && (
          <div>
            <input
              type="file"
              accept="video/*"
              onChange={handleFileChange}
              disabled={upload.state.status !== "idle"}
            />
            <p>No job started.</p>
          </div>
        )}

        {upload.state.status === "uploading" && (
          <div>
            <p>Uploading video…</p>
          </div>
        )}

        {upload.state.status === "processing" && (
          <div>
            <p>Processing… {mp4State.progress}%</p>
            <p>Frames processed: {mp4State.framesProcessed}</p>
            {mp4State.jobId && <p>Job ID: {mp4State.jobId}</p>}
          </div>
        )}

        {upload.state.status === "completed" && (
          <div>
            <p>✅ Job completed.</p>
            {mp4State.jobId && <p>Job ID: {mp4State.jobId}</p>}
            <button onClick={handleReset}>Upload another video</button>
          </div>
        )}

        {upload.state.status === "error" && (
          <div>
            <p style={{ color: "var(--accent-red)" }}>
              ❌ Error: {upload.state.errorMessage}
            </p>
            <button onClick={handleReset}>Try again</button>
          </div>
        )}

        {upload.state.status === "cancelled" && (
          <div>
            <p>Upload cancelled.</p>
            <button onClick={handleReset}>Start new upload</button>
          </div>
        )}
      </div>

      {/* Status Row */}
      {videoFile && (
        <div style={styles.statusRow}>
          <div style={styles.statusItem}>
            <div
              style={{
                ...styles.processingIndicator,
                ...(processing ? styles.processingIndicatorActive : {}),
              }}
            />
            <span>{processing ? "Processing..." : "Idle"}</span>
          </div>
          {lastRequestDuration !== null && (
            <div style={styles.statusItem}>
              <span>Last request: {lastRequestDuration.toFixed(0)}ms</span>
            </div>
          )}
          {error && (
            <div style={styles.statusItem}>
              <span style={{ color: "var(--accent-danger)" }}>Error: {error}</span>
            </div>
          )}
        </div>
      )}

      {/* Video + Canvas Section */}
      <div style={styles.videoSection}>
        <div style={styles.videoContainer}>
          {videoFile && videoSrc ? (
            <>
              <video
                ref={videoRef}
                style={styles.video}
                src={videoSrc}
                controls
                playsInline
              />
              <canvas
                ref={canvasRef}
                style={styles.canvas}
              />
            </>
          ) : (
            <p style={styles.placeholderText}>No video selected</p>
          )}
        </div>
      </div>

      {/* Playback Controls Row */}
      <div style={styles.controlsRow}>
        <button
          style={{ ...styles.button, ...(running ? styles.buttonActive : {}) }}
          onClick={handlePlay}
        >
          Play
        </button>
        <button
          style={styles.button}
          onClick={handlePause}
        >
          Pause
        </button>

        <select
          value={fps}
          onChange={(e) => setFps(Number(e.target.value))}
          style={styles.dropdown}
          disabled={!videoFile}
        >
          {FPS_OPTIONS.map((val) => (
            <option key={val} value={val}>
              {val} FPS
            </option>
          ))}
        </select>

        <select
          aria-label="Device"
          value={device}
          onChange={(e) => setDevice(e.target.value as "cpu" | "cuda")}
          style={styles.dropdown}
          disabled={!videoFile}
        >
          <option value="cpu">CPU</option>
          <option value="cuda">GPU</option>
        </select>
      </div>

      {/* Divider */}
      <div style={styles.divider} />

      {/* Overlay Toggles Row */}
      <div style={styles.togglesRow}>
        {OVERLAY_KEYS.map((key) => (
          <div key={key} style={styles.toggleItem}>
            <input
              type="checkbox"
              checked={overlayToggles[key]}
              onChange={() => handleToggle(key)}
              id={`toggle-${key}`}
              disabled={!videoFile}
            />
            <label
              htmlFor={`toggle-${key}`}
              style={styles.toggleLabel}
            >
              {key.charAt(0).toUpperCase() + key.slice(1)}
            </label>
          </div>
        ))}
      </div>
      </div>
    </MP4ProcessingProvider>
  );
}

export default VideoTracker;

