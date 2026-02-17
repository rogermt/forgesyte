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

import React from "react";
import { useMP4Upload } from "../hooks/useMP4Upload";
import { MP4ProcessingProvider } from "../mp4/MP4ProcessingContext";

// ============================================================================
// Types
// ============================================================================

export interface VideoTrackerProps {
  pluginId?: string;   // routing only - not used in Phase 17
  tools?: string[];   // routing only - not used in Phase 17
  debug?: boolean;    // FE-8: Golden Path Debug Mode
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
    maxWidth: "800px",
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
  uploadSection: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "16px",
    padding: "20px",
    backgroundColor: "var(--bg-secondary)",
    borderRadius: "8px",
    border: "1px solid var(--border-light)",
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
    backgroundColor: "var(--accent-primary)",
    color: "white",
    borderColor: "var(--accent-primary)",
  },
  buttonDisabled: {
    opacity: 0.5,
    cursor: "not-allowed",
  },
  fileInput: {
    display: "none",
  },
  statusBox: {
    padding: "12px",
    borderRadius: "6px",
    fontSize: "13px",
  },
  statusBoxIdle: {
    backgroundColor: "var(--bg-tertiary)",
    color: "var(--text-secondary)",
  },
  statusBoxUploading: {
    backgroundColor: "rgba(255, 193, 7, 0.1)",
    color: "var(--accent-warning)",
    border: "1px solid var(--accent-warning)",
  },
  statusBoxProcessing: {
    backgroundColor: "rgba(0, 123, 255, 0.1)",
    color: "var(--accent-primary)",
    border: "1px solid var(--accent-primary)",
  },
  statusBoxCompleted: {
    backgroundColor: "rgba(40, 167, 69, 0.1)",
    color: "var(--accent-success)",
    border: "1px solid var(--accent-success)",
  },
  statusBoxError: {
    backgroundColor: "rgba(220, 53, 69, 0.1)",
    color: "var(--accent-red)",
    border: "1px solid var(--accent-red)",
  },
  progressBarContainer: {
    width: "100%",
    height: "8px",
    backgroundColor: "var(--bg-tertiary)",
    borderRadius: "4px",
    overflow: "hidden",
    marginTop: "8px",
  },
  progressBar: {
    height: "100%",
    backgroundColor: "var(--accent-primary)",
    transition: "width 0.3s ease",
  },
  infoRow: {
    display: "flex",
    gap: "20px",
    fontSize: "12px",
    color: "var(--text-secondary)",
    marginTop: "8px",
  },
  fileNameLabel: {
    fontSize: "13px",
    color: "var(--text-primary)",
    fontWeight: 500,
  },
} as const;

// ============================================================================
// Component
// ============================================================================

export function VideoTracker({ debug = false }: VideoTrackerProps) {
  const upload = useMP4Upload(debug);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      upload.start(file);
    }
  };

  const handleReset = () => {
    upload.reset();
  };

  const handleCancel = () => {
    upload.cancel();
  };

  // Calculate MP4 processing state for context
  const mp4State = {
    active: upload.state.status === "processing",
    jobId: upload.state.jobId,
    progress: upload.state.progress,
    framesProcessed: upload.state.framesProcessed,
  };

  const getStatusBoxStyle = () => {
    switch (upload.state.status) {
      case "idle":
        return styles.statusBoxIdle;
      case "uploading":
        return styles.statusBoxUploading;
      case "processing":
        return styles.statusBoxProcessing;
      case "completed":
        return styles.statusBoxCompleted;
      case "error":
        return styles.statusBoxError;
      case "cancelled":
        return styles.statusBoxIdle;
      default:
        return styles.statusBoxIdle;
    }
  };

  const getStatusText = () => {
    switch (upload.state.status) {
      case "idle":
        return "Ready to upload";
      case "uploading":
        return "Uploading video to server...";
      case "processing":
        return `Processing video... ${upload.state.progress}%`;
      case "completed":
        return "✅ Processing completed successfully";
      case "error":
        return `❌ Error: ${upload.state.errorMessage}`;
      case "cancelled":
        return "Upload cancelled";
      default:
        return "Unknown status";
    }
  };

  const canUpload = upload.state.status === "idle";
  const canCancel = upload.state.status === "uploading" || upload.state.status === "processing";
  const canReset = upload.state.status === "completed" || upload.state.status === "error" || upload.state.status === "cancelled";

  return (
    <MP4ProcessingProvider value={mp4State}>
      <div style={styles.container}>
        {/* Header */}
        <div style={styles.header}>
          <h1 style={styles.title}>Video Upload</h1>
          <div style={styles.subtitle}>
            Phase 17 MP4 Upload Pipeline
          </div>
        </div>

        {/* Upload Section */}
        <div style={styles.uploadSection}>
          <input
            type="file"
            accept="video/*"
            onChange={handleFileSelect}
            disabled={!canUpload}
            style={styles.fileInput}
            id="video-upload-input"
          />

          <label
            htmlFor="video-upload-input"
            style={{
              ...styles.button,
              ...(canUpload ? styles.buttonPrimary : styles.buttonDisabled),
            }}
          >
            Select Video File
          </label>

          {/* Status Box */}
          <div style={{ ...styles.statusBox, ...getStatusBoxStyle() }}>
            <div style={{ fontWeight: 600 }}>{getStatusText()}</div>

            {/* Progress Bar */}
            {(upload.state.status === "uploading" || upload.state.status === "processing") && (
              <>
                <div style={styles.progressBarContainer}>
                  <div
                    style={{
                      ...styles.progressBar,
                      width: `${upload.state.progress}%`,
                    }}
                  />
                </div>

                {/* Info Row */}
                <div style={styles.infoRow}>
                  {upload.state.jobId && (
                    <span>Job ID: {upload.state.jobId}</span>
                  )}
                  {upload.state.framesProcessed > 0 && (
                    <span>Frames: {upload.state.framesProcessed}</span>
                  )}
                </div>
              </>
            )}

            {/* Error Details */}
            {upload.state.status === "error" && upload.state.errorMessage && (
              <div style={{ marginTop: "8px", fontSize: "12px" }}>
                {upload.state.errorMessage}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div style={{ display: "flex", gap: "12px" }}>
            {canCancel && (
              <button
                onClick={handleCancel}
                style={styles.button}
              >
                Cancel
              </button>
            )}
            {canReset && (
              <button
                onClick={handleReset}
                style={{ ...styles.button, ...styles.buttonPrimary }}
              >
                Upload Another Video
              </button>
            )}
          </div>
        </div>

        {/* Debug Info */}
        {debug && (
          <div style={{
            padding: "12px",
            backgroundColor: "var(--bg-tertiary)",
            borderRadius: "6px",
            fontSize: "12px",
            fontFamily: "monospace",
            color: "var(--text-secondary)",
          }}>
            <div><strong>Debug Info:</strong></div>
            <div>Status: {upload.state.status}</div>
            <div>Job ID: {upload.state.jobId || "N/A"}</div>
            <div>Progress: {upload.state.progress}%</div>
            <div>Frames: {upload.state.framesProcessed}</div>
            <div>Error: {upload.state.errorMessage || "None"}</div>
          </div>
        )}
      </div>
    </MP4ProcessingProvider>
  );
}

export default VideoTracker;

