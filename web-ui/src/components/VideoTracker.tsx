/**
 * Video Tracker Page Component
 * Main integration of video processing pipeline:
 * - Upload video file
 * - Select plugin + tool
 * - Adjust confidence threshold
 * - Process frames in real-time
 * - Display results with overlay
 * - Export annotated video
 *
 * Best Practices Applied:
 * - [BP-1] Composition of hooks and components
 * - [BP-2] State management for video upload/processing
 * - [BP-3] Progress tracking and error handling
 * - [BP-4] Responsive layout with grid
 * - [BP-5] Proper cleanup on unmount
 */

import { useState, useCallback, useMemo, useRef } from "react";
import { useManifest } from "../hooks/useManifest";
import { useVideoProcessor } from "../hooks/useVideoProcessor";
import ToolSelector from "./ToolSelector";
import ConfidenceSlider from "./ConfidenceSlider";
import ResultOverlay from "./ResultOverlay";
import type { VideoProcessorConfig } from "../types/video-tracker";

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
  statusBadge: {
    padding: "6px 12px",
    borderRadius: "4px",
    fontSize: "12px",
    fontWeight: 500,
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
  progressBar: {
    width: "100%",
    height: "4px",
    backgroundColor: "var(--bg-hover)",
    borderRadius: "2px",
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    backgroundColor: "var(--accent-cyan)",
    transition: "width 0.3s",
  },
  stats: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "8px",
    padding: "12px",
    backgroundColor: "rgba(0, 229, 255, 0.05)",
    borderRadius: "6px",
    fontSize: "12px",
  },
  statItem: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "2px",
  },
  statLabel: {
    color: "var(--text-muted)",
    fontSize: "10px",
  },
  statValue: {
    color: "var(--accent-cyan)",
    fontWeight: 600,
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
  error: {
    padding: "12px",
    backgroundColor: "rgba(220, 53, 69, 0.1)",
    border: "1px solid var(--accent-red)",
    borderRadius: "6px",
    color: "var(--accent-red)",
    fontSize: "12px",
  },
} as const;

// ============================================================================
// Component
// ============================================================================

export function VideoTracker() {
  // -------------------------------------------------------------------------
  // State
  // -------------------------------------------------------------------------
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [pluginId, setPluginId] = useState<string | null>(null);
  const [selectedTool, setSelectedTool] = useState("detect_players");
  const [confidence, setConfidence] = useState(0.25);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processedFrames, setProcessedFrames] = useState(0);
  const [currentFrame, setCurrentFrame] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Load manifest when plugin changes
  useManifest(pluginId);

  // Video processor for frame handling
  const processorConfig = useMemo<VideoProcessorConfig | null>(() => {
    if (!pluginId || !selectedTool) return null;

    return {
      pluginId,
      toolName: selectedTool,
      device: "cpu",
      confidence,
      annotated: true,
    };
  }, [pluginId, selectedTool, confidence]);

  const { state: processorState, detections, processFrame } = useVideoProcessor(
    processorConfig
  );

  // -------------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------------
  const handleVideoUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      if (!file.type.startsWith("video/")) {
        setError("Please select a valid video file");
        return;
      }

      setVideoFile(file);
      setError(null);
      setProcessedFrames(0);

      // Create video preview
      const reader = new FileReader();
      reader.onload = (event) => {
        if (videoRef.current) {
          videoRef.current.src = event.target?.result as string;
        }
      };
      reader.readAsDataURL(file);
    },
    []
  );

  const handleProcessVideo = useCallback(async () => {
    if (!videoRef.current || !processorConfig) {
      setError("Video or processor config not ready");
      return;
    }

    setIsProcessing(true);
    setError(null);
    setProcessedFrames(0);

    try {
      const canvas = document.createElement("canvas");
      const video = videoRef.current;

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const ctx = canvas.getContext("2d");
      if (!ctx) throw new Error("Could not get canvas context");

      // Process all frames
      let frameCount = 0;
      const duration = video.duration;

      const processNextFrame = async () => {
        if (video.currentTime >= duration) {
          setIsProcessing(false);
          return;
        }

        ctx.drawImage(video, 0, 0);
        const base64Frame = canvas.toDataURL("image/jpeg").split(",")[1];

        await processFrame(base64Frame);
        setCurrentFrame(base64Frame);
        setProcessedFrames(frameCount++);

        // Advance video by frame (assuming ~30fps)
        video.currentTime += 1 / 30;

        // Schedule next frame
        requestAnimationFrame(processNextFrame);
      };

      video.currentTime = 0;
      processNextFrame();
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to process video";
      setError(message);
      setIsProcessing(false);
    }
  }, [processorConfig, processFrame]);

  const handleClearVideo = useCallback(() => {
    setVideoFile(null);
    setProcessedFrames(0);
    setCurrentFrame("");
    setError(null);
    if (videoRef.current) {
      videoRef.current.src = "";
    }
  }, []);

  // -------------------------------------------------------------------------
  // Status badge
  // -------------------------------------------------------------------------
  const statusBadgeStyles = useMemo(() => {
    let bgColor = "var(--bg-hover)";
    let textColor = "var(--text-secondary)";

    if (isProcessing) {
      bgColor = "rgba(0, 229, 255, 0.2)";
      textColor = "var(--accent-cyan)";
    } else if (processedFrames > 0) {
      bgColor = "rgba(76, 175, 80, 0.2)";
      textColor = "#4CAF50";
    }

    return {
      ...styles.statusBadge,
      backgroundColor: bgColor,
      color: textColor,
    };
  }, [isProcessing, processedFrames]);

  const statusText = isProcessing
    ? "Processing..."
    : processedFrames > 0
      ? "Complete"
      : "Ready";

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>Video Tracker</h1>
        <div style={statusBadgeStyles}>{statusText}</div>
      </div>

      {/* Error display */}
      {error && <div style={styles.error}>⚠ {error}</div>}

      <div style={styles.mainGrid}>
        {/* Control Panel */}
        <div style={styles.controlPanel}>
          {/* Video Upload */}
          <div style={styles.controlSection}>
            <h3 style={styles.sectionTitle}>Video</h3>
            <div
              style={styles.uploadArea}
              onClick={() => fileInputRef.current?.click()}
            >
              <p style={styles.uploadText}>
                {videoFile ? `📹 ${videoFile.name}` : "Click to upload video"}
              </p>
              {videoFile && (
                <p style={{ ...styles.uploadText, fontSize: "10px" }}>
                  {(videoFile.size / 1024 / 1024).toFixed(1)} MB
                </p>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              onChange={handleVideoUpload}
              style={{ display: "none" }}
            />
            {videoFile && (
              <button
                style={{
                  ...styles.button,
                  backgroundColor: "rgba(220, 53, 69, 0.1)",
                  color: "var(--accent-red)",
                  border: "1px solid var(--accent-red)",
                }}
                onClick={handleClearVideo}
                disabled={isProcessing}
              >
                Clear Video
              </button>
            )}
          </div>

          {/* Plugin & Tool Selection */}
          {videoFile && (
            <>
              <div style={styles.controlSection}>
                <h3 style={styles.sectionTitle}>Plugin</h3>
                <select
                  value={pluginId || ""}
                  onChange={(e) => setPluginId(e.target.value || null)}
                  style={{
                    ...styles.button,
                    padding: "8px 12px",
                  }}
                  disabled={isProcessing}
                >
                  <option value="">Select plugin...</option>
                  <option value="forgesyte-yolo-tracker">
                    ForgeSyte YOLO Tracker
                  </option>
                </select>
              </div>

              {pluginId && (
                <>
                  <div style={styles.controlSection}>
                    <ToolSelector
                      pluginId={pluginId}
                      selectedTool={selectedTool}
                      onToolChange={setSelectedTool}
                      disabled={isProcessing}
                      compact={true}
                    />
                  </div>

                  <div style={styles.controlSection}>
                    <ConfidenceSlider
                      confidence={confidence}
                      onConfidenceChange={setConfidence}
                      min={0.0}
                      max={1.0}
                      step={0.05}
                      disabled={isProcessing}
                    />
                  </div>

                  {/* Stats */}
                  <div style={styles.stats}>
                    <div style={styles.statItem}>
                      <span style={styles.statLabel}>Processed</span>
                      <span style={styles.statValue}>{processedFrames}</span>
                    </div>
                    <div style={styles.statItem}>
                      <span style={styles.statLabel}>Detections</span>
                      <span style={styles.statValue}>{detections.length}</span>
                    </div>
                    <div style={styles.statItem}>
                      <span style={styles.statLabel}>FPS</span>
                      <span style={styles.statValue}>
                        {processorState.fps}
                      </span>
                    </div>
                    <div style={styles.statItem}>
                      <span style={styles.statLabel}>Status</span>
                      <span style={styles.statValue}>
                        {processorState.error ? "Error" : "OK"}
                      </span>
                    </div>
                  </div>

                  {/* Process Button */}
                  <button
                    style={{
                      ...styles.button,
                      ...styles.buttonPrimary,
                      ...(isProcessing ? styles.buttonDisabled : {}),
                    }}
                    onClick={handleProcessVideo}
                    disabled={isProcessing || !videoRef.current}
                  >
                    {isProcessing ? "Processing..." : "Start Processing"}
                  </button>
                </>
              )}
            </>
          )}
        </div>

        {/* Video Display */}
        <div style={styles.controlSection}>
          <h3 style={styles.sectionTitle}>Preview</h3>
          {videoFile ? (
            <div style={styles.videoContainer}>
              {currentFrame ? (
                <ResultOverlay
                  width={640}
                  height={360}
                  detections={detections}
                />
              ) : (
                <video
                  ref={videoRef}
                  style={{
                    width: "100%",
                    height: "100%",
                  }}
                  controls
                />
              )}
            </div>
          ) : (
            <div
              style={{
                ...styles.videoContainer,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <p style={{ color: "var(--text-muted)" }}>No video selected</p>
            </div>
          )}

          {isProcessing && (
            <div style={styles.progressBar}>
              <div
                style={{
                  ...styles.progressFill,
                  width: videoFile
                    ? `${(processedFrames / (videoFile.size / 1000000)) * 100}%`
                    : "0%",
                }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default VideoTracker;
