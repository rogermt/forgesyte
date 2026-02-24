import React, { useState, useMemo, useEffect } from "react";
import { apiClient } from "../api/client";
import { JobStatus } from "./JobStatus";
import type { PluginManifest, Tool } from "../types/plugin";

interface VideoUploadProps {
  pluginId: string | null;
  manifest?: PluginManifest | null;
}

// Tool entry with id for filtering
interface ToolEntry extends Tool {
  id: string;
}

export const VideoUpload: React.FC<VideoUploadProps> = ({ pluginId, manifest }) => {
  const [file, setFile] = useState<File | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<number>(0);
  // v0.9.7: Track selected tools (multi-select)
  const [selectedTools, setSelectedTools] = useState<string[]>([]);

  // v0.9.7: Auto-select first tool if only one available (backward compatibility)
  // This effect runs once on mount when manifest changes
  useEffect(() => {
    const tools = manifest?.tools;
    if (!tools) return; // Skip if no tools
    const toolEntries = Object.entries(tools).map(([id, tool]) => ({ id, ...tool }));
    const videoTools = toolEntries.filter((tool) => tool.input_types?.includes("video"));
    // Auto-select first tool if only one available
    if (videoTools.length === 1 && selectedTools.length === 0) {
      setSelectedTools([videoTools[0].id]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [manifest]);

  // v0.9.5: Filter tools that support video input
  const availableVideoTools = useMemo((): ToolEntry[] => {
    if (!manifest?.tools) return [];

    const tools = manifest.tools;
    const toolEntries: ToolEntry[] = Object.entries(tools).map(([id, tool]) => ({ id, ...tool }));

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

  // v0.9.7: Handle tool selection toggle (multi-select)
  const handleToolToggle = (toolId: string) => {
    setSelectedTools((prev) => {
      if (prev.includes(toolId)) {
        // Deselect tool
        return prev.filter((t) => t !== toolId);
      } else {
        // Select tool
        return [...prev, toolId];
      }
    });
  };

  // v0.9.7: Handle "Select All" for convenience
  const handleSelectAll = () => {
    if (selectedTools.length === availableVideoTools.length) {
      setSelectedTools([]); // Deselect all
    } else {
      setSelectedTools(availableVideoTools.map((t) => t.id));
    }
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setError(null);
    setJobId(null);
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

    // v0.9.7: Validate at least one tool is selected
    if (selectedTools.length === 0) {
      setError("Please select at least one tool.");
      return;
    }

    setError(null);
    setUploading(true);
    setProgress(0);

    try {
      // v0.9.7: Pass selected tools array to API
      // If only one tool selected, still pass as array for consistency
      const toolsToSubmit = selectedTools.length === 1 
        ? selectedTools[0] 
        : selectedTools;
      
      const { job_id } = await apiClient.submitVideo(
        file,
        pluginId,
        toolsToSubmit,
        (p) => setProgress(p)
      );
      setJobId(job_id);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const canUpload = file && pluginId && selectedTools.length > 0;

  return (
    <div style={{ padding: "20px", maxWidth: "800px", margin: "0 auto" }}>
      <h2>Video Upload</h2>

      {/* v0.9.7: Multi-select tool selection */}
      <div style={{ marginBottom: "16px" }}>
        <div style={{ marginBottom: "8px", fontWeight: "500" }}>
          Select tools to run:
        </div>
        
        {/* Select All button */}
        <button
          type="button"
          onClick={handleSelectAll}
          style={{
            marginBottom: "8px",
            padding: "4px 12px",
            fontSize: "12px",
            cursor: "pointer",
          }}
        >
          {selectedTools.length === availableVideoTools.length ? "Deselect All" : "Select All"}
        </button>

        {/* Tool checkboxes */}
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          {availableVideoTools.map((tool) => (
            <label
              key={tool.id}
              style={{
                display: "flex",
                alignItems: "center",
                cursor: "pointer",
                padding: "4px 8px",
                borderRadius: "4px",
                backgroundColor: selectedTools.includes(tool.id) ? "var(--highlight, #e3f2fd)" : "transparent",
              }}
            >
              <input
                type="checkbox"
                checked={selectedTools.includes(tool.id)}
                onChange={() => handleToolToggle(tool.id)}
                style={{ marginRight: "8px" }}
              />
              <span style={{ fontWeight: 500 }}>{tool.title || tool.id}</span>
              {tool.description && (
                <span style={{ marginLeft: "8px", color: "var(--text-secondary, #666)", fontSize: "12px" }}>
                  - {tool.description}
                </span>
              )}
            </label>
          ))}
        </div>

        {/* Selection summary */}
        {selectedTools.length > 0 && (
          <div style={{ marginTop: "8px", fontSize: "13px", color: "var(--text-secondary, #666)" }}>
            {selectedTools.length} tool{selectedTools.length !== 1 ? "s" : ""} selected
            {selectedTools.length > 1 && " (will run sequentially)"}
          </div>
        )}
      </div>

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
        Upload
      </button>

      {jobId && (
        <div style={{ marginTop: "20px" }}>
          <div>Job ID: {jobId}</div>
          <JobStatus jobId={jobId} />
        </div>
      )}
    </div>
  );
};

