// web-ui/src/App.tsx

/**
 * ForgeSyte 1.0.0 - Final Unified Architecture
 *
 * Three modes:
 * - Stream: Live YOLO inference via WebSocket
 * - Upload: MP4 upload with async job processing
 * - Jobs: Historical job list
 *
 * No plugins. No tools. No manifests. No phases.
 */

import React, { useState } from "react";
import { RealtimeProvider } from "./realtime/RealtimeContext";
import { StreamingView } from "./components/StreamingView";
import { VideoTracker } from "./components/VideoTracker";
import { JobList } from "./components/JobList";

type ViewMode = "stream" | "upload" | "jobs";

function App() {
  const [viewMode, setViewMode] = useState<ViewMode>("stream");
  const [debug, setDebug] = useState(false);

  return (
    <div className="app-container">
      <header className="header">
        <div className="logo">🔧 ForgeSyte</div>

        <nav className="nav">
          <button
            className={viewMode === "stream" ? "active" : ""}
            onClick={() => setViewMode("stream")}
          >
            Stream
          </button>
          <button
            className={viewMode === "upload" ? "active" : ""}
            onClick={() => setViewMode("upload")}
          >
            Upload
          </button>
          <button
            className={viewMode === "jobs" ? "active" : ""}
            onClick={() => setViewMode("jobs")}
          >
            Jobs
          </button>
        </nav>

        <div className="top-right-controls">
          <label>
            <input
              type="checkbox"
              checked={debug}
              onChange={(e) => setDebug(e.target.checked)}
            />
            Debug
          </label>
        </div>
      </header>

      {viewMode === "stream" && (
        <RealtimeProvider debug={debug}>
          <StreamingView debug={debug} />
        </RealtimeProvider>
      )}

      {viewMode === "upload" && <VideoTracker debug={debug} />}

      {viewMode === "jobs" && <JobList />}
    </div>
  );
}

export default App;