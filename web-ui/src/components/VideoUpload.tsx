import React, { useState, useMemo, useCallback } from "react";
import { apiClient } from "../api/client";
import type { PluginManifest } from "../types/plugin";

interface VideoUploadProps {
  pluginId: string | null;
  manifest?: PluginManifest | null;
  selectedTools?: string[];
  // v0.13.11: Removed lockedTools - now determined internally
  // Called when video has been uploaded and user chooses an action
  onVideoUploaded?: (videoPath: string, file: File) => void;
  onStartStreaming?: () => void;
  onRunJob?: () => void;
}

export const VideoUpload: React.FC<VideoUploadProps> = ({
  pluginId,
  manifest,
  onVideoUploaded,
  onStartStreaming,
  onRunJob,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<number>(0);

  // v0.9.5: Filter tools that support video input
  const availableVideoTools = useMemo(() => {
    if (!manifest?.tools) return [];

    const tools = manifest.tools;
    const toolEntries = Array.isArray(tools)
      ? tools
      : Object.entries(tools).map(([id, tool]) => ({ id, ...tool }));

    return toolEntries.filter(
      (tool) => tool.input_types?.includes("video")
    );
  }, [manifest]);

  // v0.13.11: Upload video and return path
  // Must be defined before early return to satisfy hooks rules
  const uploadVideo = useCallback(async (): Promise<string | null> => {
    if (!file) return null;
    if (!pluginId) {
      setError("Please select a plugin first.");
      return null;
    }

    setError(null);
    setUploading(true);
    setProgress(0);

    try {
      const result = await apiClient.submitVideoUpload(
        file,
        pluginId,
        (p) => setProgress(p)
      );

      return result.video_path;
    } catch (e: unknown) {
      const errorMsg = e instanceof Error ? e.message : "Upload failed.";
      setError(errorMsg);
      return null;
    } finally {
      setUploading(false);
    }
  }, [file, pluginId]);

  // v0.13.11: Upload then start streaming
  const handleStartStreaming = useCallback(async () => {
    const path = await uploadVideo();
    if (path && file && onVideoUploaded) {
      onVideoUploaded(path, file);
    }
    if (path && onStartStreaming) {
      onStartStreaming();
    }
  }, [uploadVideo, file, onVideoUploaded, onStartStreaming]);

  // v0.13.11: Upload then run job
  const handleRunJob = useCallback(async () => {
    const path = await uploadVideo();
    if (path && file && onVideoUploaded) {
      onVideoUploaded(path, file);
    }
    if (path && onRunJob) {
      onRunJob();
    }
  }, [uploadVideo, file, onVideoUploaded, onRunJob]);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setError(null);
    setProgress(0);

    if (!f) {
      setFile(null);
      return;
    }

    if (f.type !== "video/mp4") {
      setError("Only MP4 videos are supported.");
      setFile(null);
      return;
    }

    setFile(f);
  };

  // v0.9.5: Show fallback if no video tools available
  // Must come AFTER all hooks to satisfy react-hooks/rules-of-hooks
  if (availableVideoTools.length === 0) {
    return (
      <div style={{ padding: "20px", maxWidth: "800px", margin: "0 auto" }}>
        <h2>Video Upload</h2>
        <p>No video-compatible tools available for this plugin.</p>
      </div>
    );
  }

  // Display the first tool for UI purposes
  const videoTool = availableVideoTools[0];
  const canAct = file && pluginId && !uploading;

  return (
    <div style={{ padding: "20px", maxWidth: "800px", margin: "0 auto" }}>
      <h2>Video Upload</h2>

      <p style={{ color: "var(--text-secondary)", fontSize: "13px", marginBottom: "12px" }}>
        Using tool: <strong>{videoTool.title || videoTool.id}</strong>
      </p>

      <label htmlFor="video-upload">Select video:</label>
      <input id="video-upload" type="file" accept="video/mp4" onChange={onFileChange} />

      {error && <div style={{ color: "red", marginTop: "10px" }}>{error}</div>}

      {uploading && (
        <div style={{ marginTop: "10px" }}>
          Uploading… {progress.toFixed(0)}%
        </div>
      )}

      {/* v0.13.11: Show action buttons immediately after file selection */}
      {file && !uploading && (
        <div style={{ marginTop: "20px", display: "flex", gap: "10px" }}>
          <button
            onClick={handleStartStreaming}
            disabled={!canAct || !onStartStreaming}
            style={{
              padding: "10px 20px",
              cursor: canAct && onStartStreaming ? "pointer" : "not-allowed",
              opacity: canAct && onStartStreaming ? 1 : 0.6,
            }}
          >
            Start Streaming
          </button>
          <button
            onClick={handleRunJob}
            disabled={!canAct || !onRunJob}
            style={{
              padding: "10px 20px",
              cursor: canAct && onRunJob ? "pointer" : "not-allowed",
              opacity: canAct && onRunJob ? 1 : 0.6,
            }}
          >
            Run Job
          </button>
        </div>
      )}

      {/* Show selected file info */}
      {file && !uploading && (
        <div style={{ marginTop: "10px", fontSize: "12px", color: "var(--text-secondary)" }}>
          Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
        </div>
      )}
    </div>
  );
};