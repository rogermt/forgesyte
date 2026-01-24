/**
 * VideoTracker Component (Plugin-Agnostic Skeleton)
 *
 * This is a generic UI shell for all frame-based tools.
 * It does NOT contain assumptions about:
 * - YOLO tracker
 * - detection schema
 * - class names
 * - bounding box formats
 * - pitch/radar formats
 * - plugin internals
 *
 * Props (pluginId, toolName) are routing parameters only,
 * used to call the backend API. They do NOT influence UI structure.
 */

import { useState } from "react";

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
  mainGrid: {
    display: "grid",
    gridTemplateColumns: "350px 1fr",
    gap: "20px",
    alignItems: "start",
  },
  controlPanel: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "16px",
    padding: "16px",
    backgroundColor: "var(--bg-secondary)",
    borderRadius: "8px",
    border: "1px solid var(--border-light)",
  },
  controlSection: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "12px",
  },
  sectionTitle: {
    fontSize: "13px",
    fontWeight: 600,
    color: "var(--text-secondary)",
    textTransform: "uppercase" as const,
    letterSpacing: "0.5px",
    margin: 0,
  },
  videoContainer: {
    position: "relative" as const,
    backgroundColor: "black",
    borderRadius: "8px",
    overflow: "hidden",
    border: "1px solid var(--border-light)",
    aspectRatio: "16 / 9",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  uploadArea: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "12px",
    padding: "16px",
    border: "2px dashed var(--border-light)",
    borderRadius: "8px",
    textAlign: "center" as const,
    cursor: "pointer",
    transition: "all 0.2s",
  },
  uploadText: {
    fontSize: "12px",
    color: "var(--text-secondary)",
    margin: 0,
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
  buttonPrimary: {
    backgroundColor: "var(--accent-cyan)",
    color: "#000",
    border: "none",
  },
  buttonDisabled: {
    opacity: 0.5,
    cursor: "not-allowed",
  },
  placeholderText: {
    color: "var(--text-muted)",
  },
  toggleGroup: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "8px",
  },
  toggleItem: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "8px",
    borderRadius: "4px",
    backgroundColor: "var(--bg-hover)",
  },
  toggleLabel: {
    fontSize: "13px",
    color: "var(--text-primary)",
  },
} as const;

// ============================================================================
// Component
// ============================================================================

export function VideoTracker({ pluginId, toolName }: VideoTrackerProps) {
  // -------------------------------------------------------------------------
  // State (generic, not plugin-specific)
  // -------------------------------------------------------------------------
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [running, setRunning] = useState(false);
  const [fps, setFps] = useState(30);
  const [device, setDevice] = useState("cpu");
  const [overlayToggles, setOverlayToggles] = useState<OverlayToggles>({
    players: true,
    tracking: true,
    ball: true,
    pitch: true,
    radar: true,
  });

  // -------------------------------------------------------------------------
  // Handlers (placeholder)
  // -------------------------------------------------------------------------

  const handleToggle = (
    key: keyof OverlayToggles,
    value: boolean
  ) => {
    setOverlayToggles((prev) => ({ ...prev, [key]: value }));
  };

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>VideoTracker</h1>
        <div style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
          Plugin: <strong>{pluginId}</strong> | Tool: <strong>{toolName}</strong>
        </div>
      </div>

      <div style={styles.mainGrid}>
        {/* Control Panel */}
        <div style={styles.controlPanel}>
          {/* Video Upload Section */}
          <div style={styles.controlSection}>
            <h3 style={styles.sectionTitle}>Video</h3>
            <div
              style={styles.uploadArea}
              onClick={() => {
                const input = document.createElement("input");
                input.type = "file";
                input.accept = "video/*";
                input.onchange = (e) => {
                  const file = (e.target as HTMLInputElement).files?.[0];
                  if (file && file.type.startsWith("video/")) {
                    setVideoFile(file);
                  }
                };
                input.click();
              }}
            >
              <p style={styles.uploadText}>
                {videoFile ? `📹 ${videoFile.name}` : "Click to upload video"}
              </p>
            </div>
          </div>

          {/* FPS Control */}
          <div style={styles.controlSection}>
            <h3 style={styles.sectionTitle}>FPS</h3>
            <input
              type="range"
              min="1"
              max="60"
              value={fps}
              onChange={(e) => setFps(Number(e.target.value))}
              style={{ width: "100%" }}
            />
            <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
              {fps} fps
            </span>
          </div>

          {/* Device Selection */}
          <div style={styles.controlSection}>
            <h3 style={styles.sectionTitle}>Device</h3>
            <select
              value={device}
              onChange={(e) => setDevice(e.target.value)}
              style={{
                ...styles.button,
                padding: "8px 12px",
              }}
            >
              <option value="cpu">CPU</option>
              <option value="gpu">GPU</option>
            </select>
          </div>

          {/* Overlay Toggles */}
          <div style={styles.controlSection}>
            <h3 style={styles.sectionTitle}>Overlays</h3>
            <div style={styles.toggleGroup}>
              {(Object.keys(overlayToggles) as Array<keyof OverlayToggles>).map(
                (key) => (
                  <div key={key} style={styles.toggleItem}>
                    <input
                      type="checkbox"
                      checked={overlayToggles[key]}
                      onChange={(e) => handleToggle(key, e.target.checked)}
                      id={`toggle-${key}`}
                    />
                    <label
                      htmlFor={`toggle-${key}`}
                      style={styles.toggleLabel}
                    >
                      {key.charAt(0).toUpperCase() + key.slice(1)}
                    </label>
                  </div>
                )
              )}
            </div>
          </div>

          {/* Placeholder Controls */}
          <div style={styles.controlSection}>
            <button
              style={{
                ...styles.button,
                ...styles.buttonPrimary,
                ...(running ? styles.buttonDisabled : {}),
              }}
              onClick={() => setRunning(!running)}
              disabled={!videoFile || running}
            >
              {running ? "Processing..." : "Start"}
            </button>
          </div>
        </div>

        {/* Video Display Section */}
        <div style={styles.controlSection}>
          <h3 style={styles.sectionTitle}>Preview</h3>
          <div style={styles.videoContainer}>
            {videoFile ? (
              <video
                style={{
                  width: "100%",
                  height: "100%",
                }}
                controls
              />
            ) : (
              <p style={styles.placeholderText}>No video selected</p>
            )}
          </div>

          {/* Canvas Overlay (placeholder) */}
          <canvas
            style={{
              display: "none",
              position: "absolute",
              top: 0,
              left: 0,
            }}
          />
        </div>
      </div>
    </div>
  );
}

export default VideoTracker;
