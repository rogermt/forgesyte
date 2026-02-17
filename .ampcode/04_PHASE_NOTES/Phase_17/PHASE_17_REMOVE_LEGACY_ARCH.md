# 🔥 Phase 17: Remove Legacy Architecture - Detailed Implementation

**Purpose**: Detailed diffs and cleanup instructions for removing Phase 10 plugin/tool architecture.

**Status**: READY TO IMPLEMENT

---

## Phase 1: Fix MP4 Upload (Detailed Diffs)

### Commit 1: Add uploadVideo() to apiClient

**File**: `web-ui/src/api/client.ts`

**Add this method to ForgeSyteAPIClient class**:

```typescript
async uploadVideo(file: File): Promise<{ job_id: string }> {
  const formData = new FormData();
  formData.append("file", file);

  // IMPORTANT: Do NOT send pipelineId
  // Backend infers and chooses the appropriate pipeline
  const response = await fetch(`${this.baseUrl}/video/submit`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<{ job_id: string }>;
}
```

**Location**: Add after `runPluginTool()` method, before `export const apiClient`.

---

### Commit 2: Rewrite useVideoProcessor

**File**: `web-ui/src/hooks/useVideoProcessor.ts`

**Complete rewrite**:

```typescript
import { useState } from "react";
import { apiClient } from "../api/client";

export interface UseVideoProcessorState {
  status: "idle" | "processing" | "completed" | "error";
  currentJobId: string | null;
  progress: number;
  framesProcessed: number;
  errorMessage: string | null;
}

export interface UseVideoProcessorProps {
  file: File | null;
  debug?: boolean;
}

export function useVideoProcessor({ file, debug = false }: UseVideoProcessorProps) {
  const [state, setState] = useState<UseVideoProcessorState>({
    status: "idle",
    currentJobId: null,
    progress: 0,
    framesProcessed: 0,
    errorMessage: null,
  });

  const log = (...args: unknown[]) => {
    if (debug) {
      console.log("[MP4]", ...args);
    }
  };

  const start = async (fileToUpload: File) => {
    try {
      setState((s) => ({ ...s, status: "processing" }));
      log("Starting upload:", fileToUpload.name);

      // Step 1: Upload file (backend chooses pipeline)
      const { job_id } = await apiClient.uploadVideo(fileToUpload);
      log("Job created:", job_id);
      setState((s) => ({ ...s, currentJobId: job_id }));

      // Step 2: Poll job status
      while (true) {
        const job = await apiClient.getJob(job_id);

        setState((s) => ({
          ...s,
          progress: job.progress ?? 0,
          framesProcessed: (job as any).frames_processed ?? 0,
        }));

        log("Job status:", job.status, "Progress:", job.progress);

        if (job.status === "done" || job.status === "completed") {
          setState((s) => ({ ...s, status: "completed" }));
          log("Job completed");
          break;
        }

        if (job.status === "error") {
          setState((s) => ({
            ...s,
            status: "error",
            errorMessage: job.error || "Job failed",
          }));
          log("Job error:", job.error);
          break;
        }

        // Wait before next poll
        await new Promise((resolve) => setTimeout(resolve, 500));
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      setState((s) => ({
        ...s,
        status: "error",
        errorMessage,
      }));
      log("Upload error:", errorMessage);
    }
  };

  return { state, start };
}
```

**Changes**:
- ❌ Remove `runTool` import
- ❌ Remove `videoRef`, `pluginId`, `tools`, `fps`, `device`, `enabled` parameters
- ❌ Remove `extractFrame()`, `processFrame()` functions
- ❌ Remove interval-based frame processing
- ✅ Add `uploadVideo()` + `pollJob()` approach
- ✅ Simplified state structure
- ✅ Debug logging

---

### Commit 3: Update MP4ProcessingContext

**File**: `web-ui/src/mp4/MP4ProcessingContext.tsx`

**Ensure it provides this interface**:

```typescript
import { createContext, useContext, ReactNode } from "react";

export interface MP4ProcessingState {
  active: boolean;
  jobId: string | null;
  progress: number;
  framesProcessed: number;
}

const MP4ProcessingContext = createContext<MP4ProcessingState | null>(null);

export function MP4ProcessingProvider({
  value,
  children,
}: {
  value: MP4ProcessingState;
  children: ReactNode;
}) {
  return (
    <MP4ProcessingContext.Provider value={value}>
      {children}
    </MP4ProcessingContext.Provider>
  );
}

export function useMP4ProcessingContext(): MP4ProcessingState {
  const context = useContext(MP4ProcessingContext);
  if (!context) {
    return {
      active: false,
      jobId: null,
      progress: 0,
      framesProcessed: 0,
    };
  }
  return context;
}
```

**No changes needed if already exists** - just verify the interface matches.

---

### Commit 4: Simplify VideoTracker

**File**: `web-ui/src/components/VideoTracker.tsx`

**Complete rewrite**:

```typescript
import { useState } from "react";
import { useVideoProcessor } from "../hooks/useVideoProcessor";
import { MP4ProcessingProvider } from "../mp4/MP4ProcessingContext";

interface VideoTrackerProps {
  debug?: boolean;
}

export function VideoTracker({ debug = false }: VideoTrackerProps) {
  const [file, setFile] = useState<File | null>(null);

  const processor = useVideoProcessor({ file, debug });

  const mp4State = {
    active: processor.state.status === "processing",
    jobId: processor.state.currentJobId,
    progress: processor.state.progress,
    framesProcessed: processor.state.framesProcessed,
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0] ?? null;
    setFile(selected);
    if (selected) {
      processor.start(selected);
    }
  };

  return (
    <MP4ProcessingProvider value={mp4State}>
      <div className="panel">
        <h3>Upload video for analysis</h3>
        <input
          type="file"
          accept="video/*"
          onChange={handleFileChange}
        />

        {processor.state.status === "idle" && <p>No job started.</p>}
        {processor.state.status === "processing" && (
          <p>Processing… {mp4State.progress}% ({mp4State.framesProcessed} frames)</p>
        )}
        {processor.state.status === "completed" && (
          <p>Job completed successfully.</p>
        )}
        {processor.state.status === "error" && (
          <p style={{ color: "var(--error)" }}>
            Error: {processor.state.errorMessage}
          </p>
        )}
      </div>
    </MP4ProcessingProvider>
  );
}
```

**Changes**:
- ❌ Remove `pluginId`, `tools` props
- ❌ Remove video playback controls (Play, Pause, FPS, Device)
- ❌ Remove local video preview with canvas
- ❌ Remove overlay toggles
- ✅ Simple file upload + progress display
- ✅ Error display

---

## Phase 2: Remove Legacy Architecture (Detailed Diffs)

### Commit 5: Simplify App.tsx

**File**: `web-ui/src/App.tsx`

**Complete rewrite**:

```typescript
import React, { useState } from "react";
import { RealtimeProvider } from "./realtime/RealtimeContext";
import { StreamingView } from "./components/StreamingView";
import { VideoTracker } from "./components/VideoTracker";
import { JobList } from "./components/JobList";

type ViewMode = "stream" | "upload" | "jobs";

export default function App() {
  const [viewMode, setViewMode] = useState<ViewMode>("stream");
  const [debug, setDebug] = useState(false);

  return (
    <div className="app-container">
      <header className="header">
        <div className="logo">ForgeSyte</div>

        <nav className="nav">
          <button onClick={() => setViewMode("stream")}>Stream</button>
          <button onClick={() => setViewMode("upload")}>Upload</button>
          <button onClick={() => setViewMode("jobs")}>Jobs</button>
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
```

**Lines removed**: ~320 lines
**Lines added**: ~40 lines
**Net reduction**: ~280 lines

**Removed imports**:
- `PluginSelector`
- `ToolSelector`
- `ResultsPanel`
- `useWebSocket`, `FrameResult`
- `apiClient`, `Job`
- `detectToolType`
- `PluginManifest`

**Removed state**:
- `selectedPlugin`
- `selectedTools`
- `streamEnabled`
- `selectedJob`
- `uploadResult`
- `isUploading`
- `manifest`, `manifestError`, `manifestLoading`

**Removed effects**:
- Manifest loading
- Tool reset
- Tool auto-select

**Removed handlers**:
- `handlePluginChange`
- `handleToolChange`
- `handleFileUpload`

**Removed UI**:
- Left sidebar (PluginSelector, ToolSelector)
- Image upload panel
- Job Details panel
- ResultsPanel
- WebSocket error box
- StreamEnabled toggle

---

### Commit 6: Delete legacy components

**Run these commands**:

```bash
cd web-ui/src/components

# Delete legacy component files
rm -f PluginSelector.tsx
rm -f ToolSelector.tsx
rm -f ResultsPanel.tsx
rm -f UploadImagePanel.tsx

# Delete legacy directories
rm -rf plugins
rm -rf tools
rm -rf upload
```

**Or create a cleanup script**:

```bash
#!/bin/bash
# cleanup-legacy-components.sh

echo "Removing legacy plugin/tool components..."

cd web-ui/src/components

rm -f PluginSelector.tsx
rm -f ToolSelector.tsx
rm -f ResultsPanel.tsx
rm -f UploadImagePanel.tsx

rm -rf plugins tools upload

echo "Legacy components removed."
```

---

### Commit 7: Delete legacy hooks/utils/types

**Run these commands**:

```bash
cd web-ui/src

# Delete legacy hooks
rm -f hooks/useManifest.ts
rm -f hooks/useVideoExport.ts
rm -f hooks/useWebSocket.ts

# Delete legacy utils
rm -f utils/detectToolType.ts
rm -f utils/runTool.ts

# Delete legacy types
rm -f types/plugin.ts
```

**Or create a cleanup script**:

```bash
#!/bin/bash
# cleanup-legacy-code.sh

echo "Removing legacy hooks, utils, and types..."

cd web-ui/src

rm -f hooks/useManifest.ts
rm -f hooks/useVideoExport.ts
rm -f hooks/useWebSocket.ts

rm -f utils/detectToolType.ts
rm -f utils/runTool.ts

rm -f types/plugin.ts

echo "Legacy code removed."
```

---

## Phase 3: Add Final CSS (Detailed Diffs)

### Commit 8: Create globals.css

**File**: `web-ui/src/styles/globals.css` (new file)

```css
:root {
  --bg-primary: #05060a;
  --bg-secondary: #11131a;
  --bg-tertiary: #1a1d26;
  --border-light: #2a2d3a;
  --border-color: #2a2d3a;
  --text-primary: #f5f5f7;
  --text-secondary: #b0b3c0;
  --text-muted: #6b7280;
  --accent: #4f46e5;
  --accent-primary: #4f46e5;
  --accent-orange: #f97316;
  --accent-green: #22c55e;
  --accent-warning: #f59e0b;
  --accent-danger: #ef4444;
  --accent-red: #ef4444;
  --error: #f97373;
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
  background: var(--bg-primary);
}

.logo {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.nav {
  display: flex;
  gap: 8px;
}

.nav button {
  padding: 8px 16px;
  border: 1px solid var(--border-light);
  border-radius: 4px;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.nav button:hover {
  background: var(--border-light);
}

.top-right-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.top-right-controls label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
}

.panel {
  padding: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: 8px;
}

.panel h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.panel p {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.panel input[type="file"] {
  width: 100%;
  padding: 8px;
  border: 1px solid var(--border-light);
  border-radius: 4px;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  cursor: pointer;
}
```

---

### Commit 9: Create streaming.css

**File**: `web-ui/src/styles/streaming.css` (new file)

```css
.streaming-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 16px;
  width: 100%;
  height: 100%;
  padding: 16px;
  box-sizing: border-box;
}

.streaming-layout.no-debug {
  grid-template-columns: 1fr;
}

.stream-main {
  position: relative;
  width: 100%;
  height: 100%;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  overflow: hidden;
}

.stream-debug {
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  padding: 12px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 13px;
  color: var(--text-secondary);
}

.camera-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.overlay-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.error-banner {
  position: absolute;
  bottom: 8px;
  left: 8px;
  right: 8px;
  padding: 8px 12px;
  background: rgba(249, 115, 115, 0.1);
  border: 1px solid var(--error);
  border-radius: 6px;
  font-size: 13px;
  color: var(--error);
}
```

---

### Commit 10: Create debug.css

**File**: `web-ui/src/styles/debug.css` (new file)

```css
.debug-panel {
  font-family: monospace;
  font-size: 12px;
  color: var(--text-secondary);
}

.debug-panel h4 {
  margin: 8px 0 4px;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-primary);
}

.debug-panel hr {
  border: none;
  border-top: 1px solid var(--border-light);
  margin: 8px 0;
}

.debug-panel div {
  margin: 4px 0;
}
```

---

### Commit 11: Add integration tests

**File**: `web-ui/src/tests/integration/app.test.tsx` (new file)

```typescript
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import App from "../../App";

describe("ForgeSyte 1.0.0 App Integration", () => {
  it("renders Stream, Upload, Jobs navigation", () => {
    render(<App />);
    expect(screen.getByText("Stream")).toBeInTheDocument();
    expect(screen.getByText("Upload")).toBeInTheDocument();
    expect(screen.getByText("Jobs")).toBeInTheDocument();
  });

  it("switches between Stream, Upload, and Jobs views", async () => {
    render(<App />);

    // Default view is Stream
    expect(screen.getByText("Stream")).toBeInTheDocument();

    // Switch to Upload
    fireEvent.click(screen.getByText("Upload"));
    await waitFor(() => {
      expect(screen.getByText(/Upload video/i)).toBeInTheDocument();
    });

    // Switch to Jobs
    fireEvent.click(screen.getByText("Jobs"));
    await waitFor(() => {
      expect(screen.getByText(/Jobs/i)).toBeInTheDocument();
    });

    // Switch back to Stream
    fireEvent.click(screen.getByText("Stream"));
    await waitFor(() => {
      expect(screen.getByText(/Stream/i)).toBeInTheDocument();
    });
  });

  it("toggles debug mode", () => {
    render(<App />);
    const debugCheckbox = screen.getByLabelText("Debug");
    expect(debugCheckbox).toBeInTheDocument();
    expect(debugCheckbox).not.toBeChecked();

    fireEvent.click(debugCheckbox);
    expect(debugCheckbox).toBeChecked();

    fireEvent.click(debugCheckbox);
    expect(debugCheckbox).not.toBeChecked();
  });

  it("does not render legacy plugin/tool UI", () => {
    render(<App />);
    expect(screen.queryByText(/PluginSelector/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/ToolSelector/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/ResultsPanel/i)).not.toBeInTheDocument();
  });
});
```

---

## Import CSS in App.tsx

**File**: `web-ui/src/index.css` (or main.tsx)

**Add these imports**:

```css
@import "./styles/globals.css";
@import "./styles/streaming.css";
@import "./styles/debug.css";
```

---

## Verification Steps

### After Phase 1 (MP4 Upload Fix)
1. ✅ Upload MP4 file
2. ✅ Verify job is created
3. ✅ Verify progress updates
4. ✅ Verify completion status
5. ✅ Verify error messages

### After Phase 2 (Legacy Removal)
1. ✅ No plugin selector in UI
2. ✅ No tool selector in UI
3. ✅ No manifest loading in console
4. ✅ No detectToolType errors
5. ✅ App.tsx is < 100 lines

### After Phase 3 (CSS)
1. ✅ Styles apply correctly
2. ✅ Layout is responsive
3. ✅ Dark mode works
4. ✅ Debug panel looks good

### After Phase 4 (Tests)
1. ✅ All tests pass
2. ✅ Integration tests pass
3. ✅ Manual testing confirms functionality

---

## Pre-Commit Checklist

Before each commit, run:

```bash
cd web-ui

# 1. Lint
npm run lint

# 2. Type check
npm run type-check

# 3. Tests
npm run test -- --run
```

**All three MUST PASS before committing.**

---

## Commit Messages Template

```bash
# Phase 1 - Commit 1
feat(api): Add uploadVideo() method for MP4 upload

- Add uploadVideo(file) to apiClient
- POST to /v1/video/submit
- Returns { job_id }
- NO pipelineId sent (backend chooses)

Tests passed: X passed
```

```bash
# Phase 1 - Commit 2
refactor(hooks): Rewrite useVideoProcessor for MP4 upload

- Remove runTool dependency
- Use uploadVideo() + pollJob() approach
- Simplified state structure
- Added debug logging

Tests passed: X passed
```

```bash
# Phase 2 - Commit 5
refactor(app): Simplify App.tsx - remove legacy plugin/tool architecture

- Remove PluginSelector, ToolSelector, ResultsPanel
- Remove manifest loading logic
- Remove detectToolType, useWebSocket
- Simplified 3-mode structure (Stream, Upload, Jobs)
- Reduced from 400+ lines to ~80 lines

Tests passed: X passed
```

---

## Summary

**Total Commits**: 11
**Files Modified**: 8
**Files Deleted**: 10+
**Lines Added**: ~300
**Lines Removed**: ~600
**Net Reduction**: ~300 lines

**Risk Level**: LOW
**Estimated Time**: 2-3 hours

---

**Document Version**: 1.0
**Last Updated**: 2026-02-17
**Status**: READY FOR IMPLEMENTATION