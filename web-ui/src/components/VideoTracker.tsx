/**
 * VideoTracker Component
 *
 * This component implements the VideoTracker layout:
 * - Upload video file
 * - Display video with canvas overlay
 * - Playback controls (Play, Pause, FPS, Device)
 * - Overlay toggles (Players, Tracking, Ball, Pitch, Radar)
 *
 * Frame processing uses useVideoProcessor hook.
 */

import { useState, useRef, useEffect, useCallback } from "react";
import { useVideoProcessor } from "../hooks/useVideoProcessor";

// ============================================================================
// Types
// ============================================================================

export interface VideoTrackerProps {
  pluginId: string;   // routing only
  toolName: string;   // routing only
}

export interface OverlayToggles {
  players: boolean;
  tracking: boolean;
  ball: boolean;
  pitch: boolean;
  radar: boolean;
}

// ============================================================================
// Styles
// ============================================================================

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

export function VideoTracker({ pluginId, toolName }: VideoTrackerProps) {
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
  const [device, setDevice] = useState("cpu"); 
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
  // Note: latestResult is available for future overlay rendering (Task 5.1)
  const {
    processing,
    error,
    lastRequestDuration,
  } = useVideoProcessor({
    videoRef,
    pluginId,
    toolName,
    fps,
    device,
    enabled: running,
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

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>VideoTracker</h1>
        <div style={styles.subtitle}>
          Plugin: <strong>{pluginId}</strong> | Tool: <strong>{toolName}</strong>
        </div>
      </div>

      {/* Upload Row */}
      <div style={styles.uploadRow}>
        <button
          style={styles.button}
          onClick={handleVideoUpload}
        >
          Upload Video
        </button>
        {videoFile && (
          <span style={styles.fileNameLabel}>
            📹 {videoFile.name}
          </span>
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
                width={0}
                height={0}
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
          disabled={!videoFile}
        >
          ▶ Play
        </button>
        <button
          style={styles.button}
          onClick={handlePause}
          disabled={!videoFile}
        >
          ⏸ Pause
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
          value={device}
          onChange={(e) => setDevice(e.target.value)}
          style={styles.dropdown}
          disabled={!videoFile}
        >
          <option value="cuda">GPU</option>
          <option value="cpu">CPU</option>
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
              {key.charAt(0).toUpperCase() + key.slice(1)} ✓
            </label>
          </div>
        ))}
      </div>
    </div>
  );
}

export default VideoTracker;

