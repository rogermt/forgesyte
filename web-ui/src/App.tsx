/**
 * Main application component for ForgeSyte
 *
 * Best practices used:
 * - Derived UI state from a single connectionStatus indicator (no contradictory UI).
 * - Functional state updates for toggles.
 * - Stable callbacks with useCallback.
 */

// New feature branch commit demonstration

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { CameraPreview } from "./components/CameraPreview";
import { PluginSelector } from "./components/PluginSelector";
import { ToolSelector } from "./components/ToolSelector";
import { JobList } from "./components/JobList";
import { ResultsPanel } from "./components/ResultsPanel";
import { VideoTracker } from "./components/VideoTracker";
import { useWebSocket, FrameResult } from "./hooks/useWebSocket";
import { apiClient, Job } from "./api/client";
import { detectToolType } from "./utils/detectToolType";
import type { PluginManifest } from "./types/plugin";

const WS_BACKEND_URL = import.meta.env.VITE_WS_BACKEND_URL || "ws://localhost:8000";

type ViewMode = "stream" | "upload" | "jobs";

function App() {
  const [viewMode, setViewMode] = useState<ViewMode>("stream");
  const [selectedPlugin, setSelectedPlugin] = useState<string>("");
  const [selectedTool, setSelectedTool] = useState<string>("");
  const [streamEnabled, setStreamEnabled] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [uploadResult, setUploadResult] = useState<Job | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [manifest, setManifest] = useState<PluginManifest | null>(null);
  const [manifestError, setManifestError] = useState<string | null>(null);
  const [manifestLoading, setManifestLoading] = useState(false);

  // Compute tool list from manifest
  const toolList = useMemo(() => {
    if (!manifest) return [];
    return Object.keys(manifest.tools);
  }, [manifest]);

  const {
    isConnected,
    connectionStatus,
    attempt,
    error: wsError,
    sendFrame,
    switchPlugin,
    reconnect,
    latestResult,
  } = useWebSocket({
    url: `${WS_BACKEND_URL}/v1/stream`,
    plugin: selectedPlugin,
    onResult: (result: FrameResult) => {
      console.log("Frame result:", result);
    },
    onError: (error: string) => {
      console.error("WebSocket error:", error);
    },
    // Optional: tune UX (prevents flash; defaults already safe)
    reconnectErrorDisplayDelayMs: 800,
  });

  useEffect(() => {
    if (!selectedPlugin) {
      setManifest(null);
      setManifestError(null);
      setManifestLoading(false);
      return;
    }

    async function loadManifest() {
      setManifestLoading(true);
      setManifestError(null);

      try {
        // Use API client for consistent error handling
        const manifestData = await apiClient.getPluginManifest(selectedPlugin);
        setManifest(manifestData);
        setManifestError(null);
        console.log("[App] Manifest loaded successfully for plugin:", selectedPlugin);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Unknown error loading manifest";
        console.error("Manifest load failed:", errorMessage);
        // Check if it's a JSON parse error (HTML response)
        if (errorMessage.includes("<!DOCTYPE") || errorMessage.includes("Unexpected token")) {
          setManifestError("Server returned HTML instead of JSON. Check that the server is running and the plugin exists.");
        } else {
          setManifestError(errorMessage);
        }
        setManifest(null);
      } finally {
        setManifestLoading(false);
      }
    }

    loadManifest();
  }, [selectedPlugin]);

  const statusText = useMemo(() => {
    switch (connectionStatus) {
      case "connected":
        return "Connected";
      case "connecting":
        return "Connecting...";
      case "reconnecting":
        return attempt > 0 ? `Reconnecting... (attempt ${attempt})` : "Reconnecting...";
      case "failed":
        return "Connection failed";
      case "disconnected":
        return "Disconnected";
      default:
        return "Disconnected";
    }
  }, [connectionStatus, attempt]);

  const indicatorColor = useMemo(() => {
    switch (connectionStatus) {
      case "connected":
        return "#28a745";
      case "connecting":
        return "#ffc107";
      case "reconnecting":
        return "#fd7e14"; // orange distinct from connecting
      case "failed":
        return "#dc3545";
      case "disconnected":
        return "#dc3545";
      default:
        return "#dc3545";
    }
  }, [connectionStatus]);

  const handleFrame = useCallback(
    (imageData: string) => {
      if (isConnected && streamEnabled) {
        sendFrame(imageData, undefined, { tool: selectedTool });
      }
    },
    [isConnected, streamEnabled, sendFrame, selectedTool]
  );

  const handlePluginChange = useCallback(
    (pluginName: string) => {
      setSelectedPlugin(pluginName);
      if (isConnected) {
        switchPlugin(pluginName);
      }
    },
    [isConnected, switchPlugin]
  );

  const handleToolChange = useCallback((toolName: string) => {
    setSelectedTool(toolName);
  }, []);

  // Auto-select first tool when manifest loads and no tool is selected
  useEffect(() => {
    if (manifest && !selectedTool && toolList.length > 0) {
      // Auto-select the first tool from the manifest
      setSelectedTool(toolList[0]);
    }
  }, [manifest, selectedTool, toolList]);

  const handleFileUpload = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;
      if (!selectedPlugin) return;
      if (!selectedTool) return;

      setIsUploading(true);
      try {
        const response = await apiClient.analyzeImage(
          file,
          selectedPlugin,
          selectedTool
        );
        const job = await apiClient.pollJob(response.job_id);
        setUploadResult(job);
        setSelectedJob(job);
      } catch (err) {
        console.error("Upload failed:", err);
      } finally {
        setIsUploading(false);
      }
    },
    [selectedPlugin, selectedTool]
  );

  const styles: Record<string, React.CSSProperties> = {
    app: {
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      backgroundColor: "var(--bg-primary)",
    },
    header: {
      padding: "16px 24px",
      backgroundColor: "var(--bg-primary)",
      borderBottom: "1px solid var(--border-color)",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
    },
    logo: {
      fontSize: "20px",
      fontWeight: 700,
      color: "var(--text-primary)",
    },
    nav: {
      display: "flex",
      gap: "8px",
    },
    navButton: {
      padding: "8px 16px",
      border: "1px solid transparent",
      borderRadius: "4px",
      cursor: "pointer",
      fontSize: "14px",
      transition: "all 0.2s",
      color: "var(--text-primary)",
      fontWeight: 500,
    },
    status: {
      display: "flex",
      alignItems: "center",
      gap: "12px",
      fontSize: "13px",
      color: "var(--text-secondary)",
    },
    indicator: {
      width: "8px",
      height: "8px",
      borderRadius: "50%",
    },
    main: {
      flex: 1,
      display: "grid",
      gridTemplateColumns: "300px 1fr 350px",
      gap: "16px",
      padding: "16px",
    },
    sidebar: {
      display: "flex",
      flexDirection: "column",
      gap: "16px",
    },
    panel: {
      backgroundColor: "var(--bg-secondary)",
      borderRadius: "8px",
      padding: "16px",
      border: "1px solid var(--border-light)",
    },
    content: {
      display: "flex",
      flexDirection: "column",
      gap: "16px",
    },
    errorBox: {
      padding: "12px",
      backgroundColor: "rgba(220, 53, 69, 0.1)",
      border: "1px solid var(--accent-red)",
      borderRadius: "4px",
      color: "var(--accent-red)",
      whiteSpace: "pre-wrap",
    },
  };

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <div style={styles.logo} data-testid="app-logo">
          🔧 ForgeSyte
        </div>

        <nav style={styles.nav}>
          {(["stream", "upload", "jobs"] as ViewMode[]).map((mode) => (
            <button
              key={mode}
              style={{
                ...styles.navButton,
                backgroundColor:
                  viewMode === mode
                    ? "var(--accent-orange)"
                    : "var(--bg-tertiary)",
                borderColor:
                  viewMode === mode
                    ? "var(--accent-orange)"
                    : "var(--border-light)",
              }}
              onClick={() => setViewMode(mode)}
            >
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
            </button>
          ))}
        </nav>

        <div style={styles.status}>
          <div
            data-testid="connection-status-indicator"
            style={{
              ...styles.indicator,
              backgroundColor: indicatorColor,
            }}
          />
          <span data-testid="connection-status-text">{statusText}</span>
        </div>
      </header>

      <main style={styles.main}>
        <aside style={styles.sidebar}>
          <div style={styles.panel}>
            <PluginSelector
              selectedPlugin={selectedPlugin}
              onPluginChange={handlePluginChange}
              disabled={streamEnabled}
            />
          </div>

          <div style={styles.panel}>
            <ToolSelector
              pluginId={selectedPlugin}
              selectedTool={selectedTool}
              onToolChange={handleToolChange}
              disabled={streamEnabled}
            />
          </div>


          {viewMode === "jobs" && (
            <div style={styles.panel}>
              <JobList onJobSelect={setSelectedJob} />
            </div>
          )}
        </aside>

        <section style={styles.content}>
          {viewMode === "stream" && (
            <div style={styles.panel}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "12px",
                }}
              >
                <h3 style={{ margin: 0 }}>Stream</h3>

                <button
                  onClick={() => setStreamEnabled((v) => !v)}
                  disabled={!isConnected}
                  style={{
                    padding: "8px 16px",
                    backgroundColor: streamEnabled
                      ? "var(--accent-green)"
                      : "var(--bg-tertiary)",
                    color: "var(--text-primary)",
                    border: "1px solid var(--border-light)",
                    borderRadius: "4px",
                    cursor: isConnected ? "pointer" : "not-allowed",
                    fontWeight: 500,
                    fontSize: "13px",
                    transition: "all 0.2s",
                    opacity: isConnected ? 1 : 0.6,
                  }}
                >
                  {streamEnabled ? "Stop Streaming" : "Start Streaming"}
                </button>
              </div>

              <CameraPreview
                onFrame={handleFrame}
                enabled={streamEnabled}
                captureInterval={200}
              />
            </div>
          )}

          {viewMode === "upload" && manifest && selectedTool && (
            <>
              {detectToolType(manifest, selectedTool) === "frame" ? (
                <VideoTracker
                  pluginId={selectedPlugin}
                  toolName={selectedTool}
                />
              ) : (
                <div style={styles.panel}>
                  <p>Upload image for analysis</p>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    disabled={isUploading || !selectedPlugin || !selectedTool}
                  />
                  {isUploading && <p>Analyzing...</p>}
                </div>
              )}
            </>
          )}

          {viewMode === "upload" && (!manifest || !selectedTool) && (
            <div style={styles.panel}>
              {!selectedPlugin ? (
                <p>Select a plugin first</p>
              ) : manifestError ? (
                <div style={styles.errorBox}>
                  <strong>Manifest Error:</strong>
                  <br />
                  {manifestError}
                  <br />
                  <br />
                  <small>
                    Check that the plugin is loaded and the server is running.
                  </small>
                </div>
              ) : manifestLoading ? (
                <p>Loading manifest...</p>
              ) : !manifest ? (
                <p>Manifest not available</p>
              ) : !selectedTool ? (
                <p>Select a tool</p>
              ) : null}
            </div>
          )}

          {viewMode === "jobs" && (
            <div style={{ ...styles.panel, flex: 1 }}>
              <h3>Job Details</h3>
              {selectedJob ? (
                <pre>{JSON.stringify(selectedJob, null, 2)}</pre>
              ) : (
                <p>Select a job</p>
              )}
            </div>
          )}

          {wsError && (
            <div style={styles.errorBox} data-testid="ws-error-box">
              WebSocket Error: {wsError}
              {(connectionStatus === "failed" || connectionStatus === "disconnected") && (
                <div style={{ marginTop: 12 }}>
                  <button
                    onClick={reconnect}
                    style={{
                      padding: "6px 12px",
                      borderRadius: 4,
                      border: "1px solid var(--border-light)",
                      backgroundColor: "var(--bg-tertiary)",
                      cursor: "pointer",
                      color: "var(--text-primary)",
                      fontWeight: 600,
                    }}
                  >
                    Reconnect
                  </button>
                </div>
              )}
            </div>
          )}
        </section>

        <aside>
          <ResultsPanel
            mode={viewMode === "stream" ? "stream" : "job"}
            streamResult={latestResult}
            job={viewMode === "upload" ? uploadResult : selectedJob}
          />
        </aside>
      </main>
    </div>
  );
}

export default App;
