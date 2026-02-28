// web-ui/src/App.tsx

/**
 * Main application component for ForgeSyte
 *
 * Fixes included:
 * - Reset selectedTool whenever selectedPlugin changes (prevents sending old tool to new plugin)
 * - Auto-select first valid tool from the newly loaded manifest
 *
 * Notes:
 * - v0.9.3: Uses unified job system with submitImage and getJob
 */

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { CameraPreview } from "./components/CameraPreview";
import { PluginSelector } from "./components/PluginSelector";
import { ToolSelector } from "./components/ToolSelector";
import { JobList } from "./components/JobList";
import { ResultsPanel } from "./components/ResultsPanel";
import { VideoTracker } from "./components/VideoTracker";
import { VideoUpload } from "./components/VideoUpload";
import { useWebSocket, FrameResult } from "./hooks/useWebSocket";
import { apiClient, Job } from "./api/client";
import { detectToolType } from "./utils/detectToolType";
import type { PluginManifest } from "./types/plugin";

const WS_BACKEND_URL =
  import.meta.env.VITE_WS_BACKEND_URL || "ws://localhost:8000";

type ViewMode = "stream" | "upload" | "jobs" | "video-upload";

function App() {
  // -------------------------------------------------------------------------
  // State
  // -------------------------------------------------------------------------
  const [viewMode, setViewMode] = useState<ViewMode>("stream");
  const [selectedPlugin, setSelectedPlugin] = useState<string>("");
  const [selectedTools, setSelectedTools] = useState<string[]>([]);

  const [streamEnabled, setStreamEnabled] = useState(false);

  // v0.10.1: Tools become locked after upload to prevent mid-session changes
  const [lockedTools, setLockedTools] = useState<string[] | null>(null);

  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [uploadResult, setUploadResult] = useState<Job | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const [manifest, setManifest] = useState<PluginManifest | null>(null);
  const [manifestError, setManifestError] = useState<string | null>(null);
  const [manifestLoading, setManifestLoading] = useState(false);

  // -------------------------------------------------------------------------
  // Compute tool list from manifest
  // FIX: Handle both Phase-12 array and legacy object formats
  // -------------------------------------------------------------------------
  const toolList = useMemo(() => {
    if (!manifest) return [];

    // Phase-12 format: tools is an array of objects with id property
    if (Array.isArray(manifest.tools)) {
      return manifest.tools.map((tool: { id: string }) => tool.id);
    }

    // Legacy format: tools is an object where keys are tool names
    return Object.keys(manifest.tools);
  }, [manifest]);

  // -------------------------------------------------------------------------
  // WebSocket connection
  // -------------------------------------------------------------------------
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
    tools: lockedTools ?? selectedTools,  // v0.10.1: Use locked tools if available
    onResult: (result: FrameResult) => {
      console.log("Frame result:", result);
    },
    onError: (error: string) => {
      console.error("WebSocket error:", error);
    },
    reconnectErrorDisplayDelayMs: 800,
  });

  // -------------------------------------------------------------------------
  // Load manifest when plugin changes
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!selectedPlugin) {
      setManifest(null);
      setManifestError(null);
      setManifestLoading(false);
      return;
    }

    let cancelled = false;

    async function loadManifest() {
      setManifestLoading(true);
      setManifestError(null);

      try {
        const manifestData = await apiClient.getPluginManifest(selectedPlugin);
        if (cancelled) return;

        setManifest(manifestData);
        setManifestError(null);
        console.log(
          "[App] Manifest loaded successfully for plugin:",
          selectedPlugin
        );
      } catch (err) {
        if (cancelled) return;

        const errorMessage =
          err instanceof Error ? err.message : "Unknown error loading manifest";
        console.error("Manifest load failed:", errorMessage);

        if (
          errorMessage.includes("<!DOCTYPE") ||
          errorMessage.includes("Unexpected token")
        ) {
          setManifestError(
            "Server returned HTML instead of JSON. Check that the server is running and the plugin exists."
          );
        } else {
          setManifestError(errorMessage);
        }

        setManifest(null);
      } finally {
        if (!cancelled) setManifestLoading(false);
      }
    }

    loadManifest();

    return () => {
      cancelled = true;
    };
  }, [selectedPlugin]);

  // -------------------------------------------------------------------------
  // FIX: Reset tool selection when plugin changes
  //
  // Prevents: plugin=ocr&tool=radar (radar was from yolo-tracker)
  // v0.10.1: Also reset lockedTools to allow new tool selection
  // -------------------------------------------------------------------------
  useEffect(() => {
    setSelectedTools([]);
    setUploadResult(null);
    setSelectedJob(null);
    setLockedTools(null);  // v0.10.1: Reset lock when plugin changes
  }, [selectedPlugin]);

  // -------------------------------------------------------------------------
  // Ensure we always have a valid tool for the current manifest
  // - If none selected, select first
  // - If selected tool doesn't exist in this plugin, select first
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!manifest) return;

    if (toolList.length === 0) {
      setSelectedTools([]);
      return;
    }

    if (selectedTools.length === 0 || !selectedTools.every((t) => toolList.includes(t))) {
      setSelectedTools([toolList[0]]);
    }
  }, [manifest, toolList, selectedTools]);

  const statusText = useMemo(() => {
    switch (connectionStatus) {
      case "connected":
        return "Connected";
      case "connecting":
        return "Connecting...";
      case "reconnecting":
        return attempt > 0
          ? `Reconnecting... (attempt ${attempt})`
          : "Reconnecting...";
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
        return "#fd7e14";
      case "failed":
        return "#dc3545";
      case "disconnected":
        return "#dc3545";
      default:
        return "#dc3545";
    }
  }, [connectionStatus]);

  // -------------------------------------------------------------------------
  // Event handlers
  // -------------------------------------------------------------------------
  const handleFrame = useCallback(
    (imageData: string) => {
      if (isConnected && streamEnabled) {
        // Tools are passed via useWebSocket options, no need for extra payload
        sendFrame(imageData);
      }
    },
    [isConnected, streamEnabled, sendFrame]
  );

  const handlePluginChange = useCallback(
    (pluginName: string) => {
      setSelectedPlugin(pluginName);

      // If already connected, tell WS server to switch plugin too
      if (isConnected) {
        switchPlugin(pluginName);
      }
    },
    [isConnected, switchPlugin]
  );

  const handleToolChange = useCallback((toolNames: string[]) => {
    setSelectedTools(toolNames);
  }, []);

  const handleFileUpload = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;
      if (!selectedPlugin) return;
      if (selectedTools.length === 0) return;

      // v0.10.1: Lock tools for this session
      setLockedTools(selectedTools);

      // v0.10.1: Pause streaming if active
      if (streamEnabled) setStreamEnabled(false);

      setIsUploading(true);
      try {
        // v0.9.4: Pass all selected tools (not just first) for multi-tool support
        const response = await apiClient.submitImage(
          file,
          selectedPlugin,
          selectedTools  // CHANGED: was selectedTools[0]
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
    [selectedPlugin, selectedTools, streamEnabled]
  );

  // -------------------------------------------------------------------------
  // Styles
  // -------------------------------------------------------------------------
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

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <div style={styles.logo} data-testid="app-logo">
          🔧 ForgeSyte
        </div>

        <nav style={styles.nav}>
          {(["stream", "upload", "jobs", "video-upload"] as ViewMode[]).map((mode) => (
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
              {mode === "video-upload" ? "Upload Video" : mode.charAt(0).toUpperCase() + mode.slice(1)}
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
              selectedTools={lockedTools ?? selectedTools}
              onToolChange={handleToolChange}
              disabled={lockedTools !== null}  // v0.10.1: Disable after upload
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

          {viewMode === "upload" && manifest && selectedTools.length > 0 && (
            <>
              {detectToolType(manifest, selectedTools[0]) === "frame" ? (
                <VideoTracker pluginId={selectedPlugin} tools={selectedTools} />
              ) : (
                <div style={styles.panel}>
                  <p>Upload image for analysis</p>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    disabled={isUploading || !selectedPlugin || selectedTools.length === 0}
                  />
                  {isUploading && <p>Analyzing...</p>}
                </div>
              )}
            </>
          )}

          {viewMode === "upload" && (!manifest || selectedTools.length === 0) && (
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
                  <small>Check that the plugin is loaded and the server is running.</small>
                </div>
              ) : manifestLoading ? (
                <p>Loading manifest...</p>
              ) : !manifest ? (
                <p>Manifest not available</p>
              ) : selectedTools.length === 0 ? (
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

          {viewMode === "video-upload" && (
            <div style={{ ...styles.panel, flex: 1 }}>
              <VideoUpload
                pluginId={selectedPlugin}
                manifest={manifest}
                selectedTools={selectedTools}
              />
            </div>
          )}

          {wsError && (
            <div style={styles.errorBox} data-testid="ws-error-box">
              WebSocket Error: {wsError}
              {(connectionStatus === "failed" ||
                connectionStatus === "disconnected") && (
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