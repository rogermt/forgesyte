import React, { useState, useMemo } from "react";
import { apiClient } from "../api/client";
import type { PluginManifest } from "../types/plugin";

interface VideoUploadProps {
  pluginId: string | null;
  manifest?: PluginManifest | null;
  selectedTools?: string[];
  // v0.10.1: deterministic tool locking
  lockedTools?: string[] | null;
  // Called when video has been uploaded and server returns a path
  onVideoUploaded?: (videoPath: string) => void;
  // User choices after upload
  onStartStreaming?: () => void;
  onRunJob?: () => void;
}

export const VideoUpload: React.FC<VideoUploadProps> = ({
  pluginId,
  manifest,
  lockedTools,
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

  // v0.9.5: Show fallback if no video tools available
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

  const onUpload = async () => {
    if (!file) return;
    if (!pluginId) {
      setError("Please select a plugin first.");
      return;
    }

    setError(null);
    setUploading(true);
    setProgress(0);

    try {
      // v0.10.1: Upload-only, no job submission here
      const { video_path } = await apiClient.submitVideoUpload(
        file,
        pluginId,
        (p) => setProgress(p)
      );

      if (onVideoUploaded) {
        onVideoUploaded(video_path);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const canUpload = file && pluginId;

  return (
    <div style={{ padding: "20px", maxWidth: "800px", margin: "0 auto" }}>
      <h2>Video Upload</h2>

      <p style={{ color: "var(--text-secondary)", fontSize: "13px", marginBottom: "12px" }}>
        Using tool: <strong>{videoTool.title || videoTool.id}</strong>
      </p>

      <label htmlFor="video-upload">Upload video:</label>
      <input id="video-upload" type="file" accept="video/mp4" onChange={onFileChange} />

      {error && <div style={{ color: "red", marginTop: "10px" }}>{error}</div>}

      {uploading && (
        <div style={{ marginTop: "10px" }}>
          Uploading… {progress.toFixed(0)}%
        </div>
      )}

      <button
        onClick={onUpload}
        disabled={!canUpload || uploading}
        style={{
          marginTop: "10px",
          padding: "10px 20px",
          cursor: canUpload && !uploading ? "pointer" : "not-allowed",
        }}
      >
        Upload Video
      </button>

      {/* v0.10.1: After upload → tools locked in App → user chooses streaming or job */}
      {lockedTools && !uploading && (
        <div style={{ marginTop: "20px", display: "flex", gap: "10px" }}>
          <button
            onClick={onStartStreaming}
            disabled={!onStartStreaming}
            style={{ padding: "8px 16px" }}
          >
            Start Streaming
          </button>
          <button
            onClick={onRunJob}
            disabled={!onRunJob}
            style={{ padding: "8px 16px" }}
          >
            Run Job
          </button>
        </div>
      )}
    </div>
  );
};
