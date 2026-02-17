// web-ui/src/App.tsx

/**
 * ForgeSyte 1.0.0 - Phase 17 Unified Architecture
 *
 * Three modes:
 * - Stream: Live YOLO inference via WebSocket (binary JPEG frames)
 * - Upload: MP4 upload with async job processing
 * - Jobs: Historical job list
 *
 * No plugins. No tools. No manifests. No pipeline selection.
 * Backend chooses the pipeline automatically.
 */

import React, { useState } from "react";
import { JobList } from "./components/JobList";
import { VideoTracker } from "./components/VideoTracker";
import { StreamingView } from "./components/StreamingView";
import { RealtimeProvider } from "./realtime/RealtimeContext";

type ViewMode = "stream" | "upload" | "jobs";

function App() {
  const [viewMode, setViewMode] = useState<ViewMode>("stream");
  const [debug, setDebug] = useState(false);
  const [streamEnabled, setStreamEnabled] = useState(false);

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
      position: "relative",
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
      backgroundColor: "transparent",
    },
    navButtonActive: {
      backgroundColor: "var(--accent-primary)",
      color: "white",
    },
    debugToggle: {
      position: "absolute",
      top: "16px",
      right: "24px",
      display: "flex",
      alignItems: "center",
      gap: "8px",
      fontSize: "13px",
      color: "var(--text-secondary)",
    },
    main: {
      flex: 1,
      display: "grid",
      gridTemplateColumns: "300px 1fr",
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
  };

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <div style={styles.logo}>🔧 ForgeSyte</div>

        <nav style={styles.nav}>
          <button
            style={{
              ...styles.navButton,
              ...(viewMode === "stream" ? styles.navButtonActive : {}),
            }}
            onClick={() => setViewMode("stream")}
          >
            Stream
          </button>
          <button
            style={{
              ...styles.navButton,
              ...(viewMode === "upload" ? styles.navButtonActive : {}),
            }}
            onClick={() => setViewMode("upload")}
          >
            Upload
          </button>
          <button
            style={{
              ...styles.navButton,
              ...(viewMode === "jobs" ? styles.navButtonActive : {}),
            }}
            onClick={() => setViewMode("jobs")}
          >
            Jobs
          </button>
        </nav>

        <div style={styles.debugToggle}>
          <label style={{ display: "flex", alignItems: "center", gap: "6px", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={debug}
              onChange={(e) => setDebug(e.target.checked)}
            />
            Debug
          </label>
        </div>
      </header>

      <main style={styles.main}>
        <aside style={styles.sidebar}>
          {viewMode === "jobs" && (
            <div style={styles.panel}>
              <JobList />
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
                  style={{
                    padding: "8px 16px",
                    backgroundColor: streamEnabled
                      ? "var(--accent-red)"
                      : "var(--accent-green)",
                    color: "white",
                    border: "none",
                    borderRadius: "4px",
                    cursor: "pointer",
                    fontWeight: 500,
                    fontSize: "13px",
                    transition: "all 0.2s",
                  }}
                >
                  {streamEnabled ? "Stop Streaming" : "Start Streaming"}
                </button>
              </div>

              <RealtimeProvider debug={debug}>
                <StreamingView debug={debug} enabled={streamEnabled} />
              </RealtimeProvider>
            </div>
          )}

          {viewMode === "upload" && (
            <VideoTracker debug={debug} />
          )}

          {viewMode === "jobs" && (
            <div style={{ ...styles.panel, flex: 1 }}>
              <h3 style={{ marginTop: 0 }}>Job Details</h3>
              <p style={{ color: "var(--text-secondary)" }}>
                Select a job from the list to view details
              </p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;