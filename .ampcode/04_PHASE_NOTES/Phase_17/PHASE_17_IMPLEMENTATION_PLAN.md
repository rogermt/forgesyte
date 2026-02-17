# Phase 17 Implementation Plan — Final Migration to ForgeSyte 1.0.0

**Status**: Ready to Execute
**Date**: 2026-02-17
**Total Commits**: 9

---

## Executive Summary

This plan implements the final migration to ForgeSyte 1.0.0 by:

1. **Fixing MP4 Upload** — Replacing legacy `runTool()` with batch job API
2. **Removing Legacy Architecture** — Deleting all Phase 10 plugin/tool code
3. **Finalizing CSS** — Adding production-ready styles
4. **Adding Integration Tests** — Ensuring end-to-end functionality

---

## Current State Assessment

### ✅ Complete
- **Backend Phase 17 Streaming**: 12/12 commits done (WebSocket, session management, backpressure)
- **Frontend Phase 17 Streaming**: 8/8 commits done (useWebSocket, useRealtime, CameraPreview, Overlay, etc.)

### ❌ Broken
- **MP4 Upload**: Uses legacy `runTool()` API instead of Phase 15/16 batch job API
- **App.tsx**: Contains Phase 10 legacy code (PluginSelector, ToolSelector, ResultsPanel, manifest loading, detectToolType)

---

## Critical Decisions (Locked In)

### Decision 1: Pipeline IDs
**🚫 NEVER hardcode pipeline IDs in frontend.**
- The backend chooses the pipeline
- The frontend only uploads the file
- No `pipelineId` prop, no hidden defaults
- This is a **governance rule**, not a preference

### Decision 2: MP4 Upload Endpoint
**Use `/v1/video/submit` directly.**
- It already exists in the backend
- It returns `{ job_id }`
- No backend changes required
- Do NOT create `/api/video/upload` yet

### Decision 3: Hook Strategy
**Create NEW `useMP4Upload` hook.**
- Do NOT modify `useVideoProcessor`
- `useVideoProcessor` remains legacy (Phase 10)
- `useMP4Upload` handles batch jobs (Phase 17)
- Clean separation of concerns

### Decision 4: Implementation Order
**Phase 1 first, verify, then Phase 2-4.**
- Fix MP4 upload first
- Verify it works end-to-end
- Then delete legacy code
- This prevents debugging in a half-deleted environment

### Decision 5: Streaming Scope
**Leave streaming as-is.**
- Phase 17 streaming is already complete
- Focus ONLY on MP4 upload
- Do NOT touch streaming components

### Decision 6: VideoTracker UI
**Remove ALL playback controls.**
- No Play/Pause/FPS/Device selector
- No local video preview
- No overlay toggles
- Just: upload → progress → status → result

### Decision 7: JobList Behavior
**Show only MP4 jobs.**
- Streaming sessions are ephemeral
- They are not persisted
- They do NOT belong in job list

---

## Implementation Plan (9 Commits)

### Phase 1: Fix MP4 Upload (4 commits)

#### Commit 1 — Add `apiClient.uploadVideo()`
**File**: `src/api/client.ts`

**Changes**:
- Add `uploadVideo(file: File)` method
- POST to `/v1/video/submit`
- Returns `{ job_id }`
- No pipelineId sent (backend chooses)

**Diff**:
```diff
+ async uploadVideo(file: File): Promise<{ job_id: string }> {
+   const form = new FormData();
+   form.append("file", file);
+
+   const res = await fetch("/v1/video/submit", {
+     method: "POST",
+     body: form,
+   });
+
+   if (!res.ok) {
+     throw new Error(`Upload failed: ${res.status}`);
+   }
+
+   return res.json();
+ }
```

---

#### Commit 2 — Create new hook `useMP4Upload`
**File**: `src/hooks/useMP4Upload.ts` (NEW)

**Changes**:
- Create new hook for batch job processing
- Upload MP4
- Poll job status
- Track progress, framesProcessed, error
- Support cancellation

**Implementation**:
```typescript
import { useEffect, useRef, useState } from "react";
import { apiClient } from "../api/client";

export interface MP4UploadState {
  status: "idle" | "uploading" | "processing" | "completed" | "error" | "cancelled";
  jobId: string | null;
  progress: number;
  framesProcessed: number;
  errorMessage: string | null;
}

export function useMP4Upload(debug = false) {
  const [state, setState] = useState<MP4UploadState>({
    status: "idle",
    jobId: null,
    progress: 0,
    framesProcessed: 0,
    errorMessage: null,
  });

  const cancelled = useRef(false);

  const log = (...args: any[]) => debug && console.log("[MP4Upload]", ...args);

  async function start(file: File) {
    cancelled.current = false;

    try {
      setState((s) => ({ ...s, status: "uploading" }));

      const { job_id } = await apiClient.uploadVideo(file);
      log("Job created:", job_id);

      setState((s) => ({
        ...s,
        status: "processing",
        jobId: job_id,
      }));

      // Poll job status
      while (!cancelled.current) {
        const job = await apiClient.getJob(job_id);

        setState((s) => ({
          ...s,
          progress: job.progress ?? 0,
          framesProcessed: job.frames_processed ?? 0,
        }));

        if (job.status === "completed") {
          setState((s) => ({ ...s, status: "completed" }));
          return;
        }

        if (job.status === "error") {
          setState((s) => ({
            ...s,
            status: "error",
            errorMessage: job.error ?? "Unknown error",
          }));
          return;
        }

        await new Promise((r) => setTimeout(r, 500));
      }

      // If cancelled
      setState((s) => ({ ...s, status: "cancelled" }));
    } catch (err: any) {
      setState((s) => ({
        ...s,
        status: "error",
        errorMessage: err.message ?? "Upload failed",
      }));
    }
  }

  function cancel() {
    cancelled.current = true;
  }

  return { state, start, cancel };
}
```

---

#### Commit 3 — Update `VideoTracker` to use `useMP4Upload`
**File**: `src/components/VideoTracker.tsx`

**Changes**:
- Replace `useVideoProcessor` with `useMP4Upload`
- Remove playback controls
- Remove local video preview
- Remove overlay toggles
- Minimal upload UI

**Diff**:
```diff
- import { useVideoProcessor } from "../hooks/useVideoProcessor";
+ import { useMP4Upload } from "../hooks/useMP4Upload";

- const processor = useVideoProcessor({ file, debug });
+ const upload = useMP4Upload(debug);

- processor.start(file)
+ upload.start(file)

- processor.state.progress
+ upload.state.progress

- processor.state.status
+ upload.state.status
```

**Final VideoTracker.tsx**:
```tsx
import React, { useState } from "react";
import { useMP4Upload } from "../hooks/useMP4Upload";
import { MP4ProcessingProvider } from "../mp4/MP4ProcessingContext";

export function VideoTracker({ debug = false }) {
  const [file, setFile] = useState<File | null>(null);
  const upload = useMP4Upload(debug);

  const mp4State = {
    active: upload.state.status === "processing",
    jobId: upload.state.jobId,
    progress: upload.state.progress,
    framesProcessed: upload.state.framesProcessed,
    error: upload.state.errorMessage,
    status: upload.state.status,
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] ?? null;
    setFile(selected);
    if (selected) upload.start(selected);
  };

  return (
    <MP4ProcessingProvider value={mp4State}>
      <div className="panel">
        <h3>Upload video for analysis</h3>

        <input type="file" accept="video/*" onChange={handleFileChange} />

        {upload.state.status === "idle" && <p>No job started.</p>}
        {upload.state.status === "uploading" && <p>Uploading…</p>}
        {upload.state.status === "processing" && (
          <p>Processing… {mp4State.progress}%</p>
        )}
        {upload.state.status === "completed" && <p>Job completed.</p>}
        {upload.state.status === "error" && (
          <p>Error: {upload.state.errorMessage}</p>
        )}
        {upload.state.status === "cancelled" && <p>Cancelled.</p>}
      </div>
    </MP4ProcessingProvider>
  );
}
```

---

#### Commit 4 — Update `MP4ProcessingContext` + `StreamDebugPanel`
**Files**:
- `src/mp4/MP4ProcessingContext.tsx`
- `src/components/StreamDebugPanel.tsx`

**Changes**:
- Add `status` and `error` fields to MP4ProcessingContext
- Update StreamDebugPanel to show MP4 metrics

**MP4ProcessingContext.tsx**:
```tsx
import React, { createContext, useContext } from "react";

export interface MP4ProcessingState {
  active: boolean;
  jobId: string | null;
  progress: number;
  framesProcessed: number;
  status: "idle" | "uploading" | "processing" | "completed" | "error" | "cancelled";
  error: string | null;
}

const MP4ProcessingContext = createContext<MP4ProcessingState | null>(null);

export const MP4ProcessingProvider = MP4ProcessingContext.Provider;

export function useMP4ProcessingContext() {
  return useContext(MP4ProcessingContext);
}
```

**StreamDebugPanel.tsx**:
```tsx
import React from "react";
import { useRealtime } from "../hooks/useRealtime";
import { useMP4ProcessingContext } from "../mp4/MP4ProcessingContext";

export function StreamDebugPanel() {
  const realtime = useRealtime();
  const mp4 = useMP4ProcessingContext();

  return (
    <div className="debug-panel">
      <h4>Streaming Debug</h4>
      <div>Connected: {String(realtime.connected)}</div>
      <div>FPS (send): {realtime.metrics.sendFps}</div>
      <div>FPS (recv): {realtime.metrics.recvFps}</div>
      <div>Dropped frames: {realtime.metrics.droppedFrames}</div>

      <hr />

      <h4>MP4 Processing</h4>
      {mp4?.active ? (
        <>
          <div>Job ID: {mp4.jobId}</div>
          <div>Status: {mp4.status}</div>
          <div>Progress: {mp4.progress}%</div>
          <div>Frames processed: {mp4.framesProcessed}</div>
        </>
      ) : (
        <div>No MP4 processing</div>
      )}
    </div>
  );
}
```

---

### Phase 2: Remove Legacy Architecture (3 commits)

#### Commit 5 — Simplify `App.tsx`
**File**: `src/App.tsx`

**Changes**:
- Remove PluginSelector, ToolSelector, ResultsPanel
- Remove manifest loading
- Remove detectToolType
- Remove analyzeImage
- Remove old WebSocket logic
- Remove image upload panel
- Add final Stream/Upload/Jobs layout

**Final App.tsx**:
```tsx
import React, { useState } from "react";
import { RealtimeProvider } from "./realtime/RealtimeContext";
import { StreamingView } from "./components/StreamingView";
import { VideoTracker } from "./components/VideoTracker";
import { JobList } from "./components/JobList";

export default function App() {
  const [viewMode, setViewMode] = useState<"stream" | "upload" | "jobs">("stream");
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

---

#### Commit 6 — Delete legacy components (18 files)
**Files to delete**:
```
src/components/PluginSelector.tsx
src/components/PluginSelector.test.tsx
src/components/ToolSelector.tsx
src/components/ToolSelector.test.tsx
src/components/ResultsPanel.tsx
src/components/ResultsPanel.test.tsx
src/components/ResultsPanel.plugin.test.tsx
src/components/UploadImagePanel.tsx
src/components/PluginInspector.tsx
src/components/plugins/ (entire directory)
src/components/tools/ (entire directory)
src/components/upload/ (entire directory)
```

---

#### Commit 7 — Delete legacy hooks/utils/types
**Files to delete**:
```
src/hooks/useManifest.ts
src/hooks/useManifest.test.ts
src/hooks/useVideoExport.ts
src/hooks/useVideoExport.test.ts
src/hooks/useVideoProcessor.ts (legacy version)
src/hooks/useVideoProcessor.test.ts (legacy version)
src/hooks/useVideoProcessor.types.ts
src/utils/detectToolType.ts
src/utils/runTool.ts
src/types/plugin.ts
```

**Note**: `useVideoProcessor` will be replaced by the new `useMP4Upload` hook.

---

### Phase 3: Final CSS (1 commit)

#### Commit 8 — Add final CSS bundle
**Files to create**:
- `src/styles/globals.css`
- `src/styles/streaming.css`
- `src/styles/debug.css`

**globals.css**:
```css
:root {
  --bg-primary: #05060a;
  --bg-secondary: #11131a;
  --border-light: #2a2d3a;
  --text-primary: #f5f5f7;
  --text-secondary: #b0b3c0;
  --accent: #4f46e5;
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
  background: #05060a;
}

.logo {
  font-weight: 600;
}

.nav button {
  margin-right: 8px;
}

.panel {
  padding: 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: 8px;
}
```

**streaming.css**:
```css
.streaming-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 16px;
  width: 100%;
  height: 100%;
  padding: 16px;
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
}
```

**debug.css**:
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
```

---

### Phase 4: Verification (1 commit)

#### Commit 9 — Add integration test
**File**: `src/tests/integration/app.test.tsx` (NEW)

**Implementation**:
```tsx
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import App from "../../App";

describe("ForgeSyte 1.0.0 App", () => {
  it("renders Stream, Upload, Jobs navigation", () => {
    render(<App />);
    expect(screen.getByText("Stream")).toBeInTheDocument();
    expect(screen.getByText("Upload")).toBeInTheDocument();
    expect(screen.getByText("Jobs")).toBeInTheDocument();
  });

  it("switches between Stream, Upload, and Jobs views", () => {
    render(<App />);

    fireEvent.click(screen.getByText("Upload"));
    expect(screen.getByText(/Upload video/i)).toBeInTheDocument();

    fireEvent.click(screen.getByText("Jobs"));
    expect(screen.getByText(/Jobs/i)).toBeInTheDocument();

    fireEvent.click(screen.getByText("Stream"));
    expect(screen.getByText(/Stream/i)).toBeInTheDocument();
  });

  it("toggles debug mode", () => {
    render(<App />);
    const debugCheckbox = screen.getByLabelText("Debug");
    expect(debugCheckbox).toBeInTheDocument();
    fireEvent.click(debugCheckbox);
    expect(debugCheckbox).toBeChecked();
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

## Verification Checklist

### Phase 1 Verification (After Commit 4)
- [ ] MP4 upload works end-to-end
- [ ] Upload hits `/v1/video/submit`
- [ ] Job polling works
- [ ] Progress updates correctly
- [ ] Debug panel shows MP4 metrics
- [ ] No `runTool()` references remain
- [ ] No pipelineId hardcoded anywhere

### Phase 2 Verification (After Commit 7)
- [ ] App.tsx simplified to Stream/Upload/Jobs
- [ ] No PluginSelector references
- [ ] No ToolSelector references
- [ ] No ResultsPanel references
- [ ] No manifest loading
- [ ] No detectToolType
- [ ] No analyzeImage
- [ ] All legacy components deleted
- [ ] All legacy hooks deleted

### Phase 3 Verification (After Commit 8)
- [ ] globals.css loaded
- [ ] streaming.css loaded
- [ ] debug.css loaded
- [ ] No legacy CSS remains

### Phase 4 Verification (After Commit 9)
- [ ] Integration tests pass
- [ ] Navigation works
- [ ] Debug toggle works
- [ ] No legacy UI appears

---

## Pre-Commit Verification Script

Save as `scripts/pre_commit_verify.sh`:

```bash
#!/bin/bash

echo "=== Pre-Commit Verification ==="

# Check for legacy imports
LEGACY_PATTERNS=(
  "PluginSelector"
  "ToolSelector"
  "ResultsPanel"
  "useManifest"
  "useVideoExport"
  "detectToolType"
  "runTool"
  "analyzeImage"
  "pipelineId"
)

for pattern in "${LEGACY_PATTERNS[@]}"; do
  if rg "$pattern" src > /dev/null; then
    echo "❌ ERROR: Found legacy reference: $pattern"
    exit 1
  fi
done

echo "✅ No legacy references found"

# Check for correct API usage
if ! rg "/v1/video/submit" src/api/client.ts > /dev/null; then
  echo "❌ ERROR: uploadVideo() does not call /v1/video/submit"
  exit 1
fi

echo "✅ MP4 upload uses /v1/video/submit"

# Check for useMP4Upload
if ! rg "useMP4Upload" src/components/VideoTracker.tsx > /dev/null; then
  echo "❌ ERROR: VideoTracker does not use useMP4Upload"
  exit 1
fi

echo "✅ VideoTracker uses useMP4Upload"

echo "🎉 All pre-commit checks passed!"
```

---

## Migration Safety Net

Before deleting any files, run:

```bash
# Check for imports of files about to be deleted
rg "PluginSelector" src
rg "ToolSelector" src
rg "ResultsPanel" src
rg "useManifest" src
rg "useVideoExport" src
rg "detectToolType" src
rg "runTool" src
```

If any of these return results in non-legacy files, fix them before deletion.

---

## Post-Merge Verification

After all 9 commits are merged, run:

1. **Manual QA**:
   - Test streaming (webcam opens, overlay works)
   - Test MP4 upload (upload → progress → complete)
   - Test Jobs list (shows completed jobs)
   - Test debug toggle (shows debug panel)
   - Verify no legacy UI appears

2. **Automated Tests**:
   ```bash
   cd web-ui
   npm run lint
   npm run type-check
   npm run test -- --run
   ```

3. **Legacy Reference Check**:
   ```bash
   rg "PluginSelector|ToolSelector|ResultsPanel|manifest|runTool" src
   ```
   Should return no results.

---

## Commit Messages

### Commit 1
```
feat: add uploadVideo() to apiClient using /v1/video/submit

- Adds uploadVideo(file) method
- POST to /v1/video/submit
- Returns { job_id }
- No pipelineId sent (backend chooses)
```

### Commit 2
```
feat: add useMP4Upload hook for batch job processing

- Creates new hook for MP4 batch jobs
- Uploads MP4 to backend
- Polls job status
- Tracks progress, framesProcessed, error
- Supports cancellation
- Pipeline-agnostic (backend chooses)
```

### Commit 3
```
refactor: migrate VideoTracker to use useMP4Upload

- Replaces useVideoProcessor with useMP4Upload
- Removes playback controls
- Removes local video preview
- Removes overlay toggles
- Minimal upload UI
- No pipelineId
```

### Commit 4
```
feat: update MP4ProcessingContext and StreamDebugPanel

- Adds status and error fields to MP4ProcessingContext
- Updates StreamDebugPanel to show MP4 metrics
- Shows jobId, status, progress, framesProcessed
```

### Commit 5
```
refactor: simplify App.tsx to unified Stream/Upload/Jobs architecture

- Removes PluginSelector, ToolSelector, ResultsPanel
- Removes manifest loading
- Removes detectToolType
- Removes analyzeImage
- Removes old WebSocket logic
- Removes image upload panel
- Adds final Stream/Upload/Jobs layout
```

### Commit 6
```
chore: remove legacy Phase 10 components

- Deletes PluginSelector, ToolSelector, ResultsPanel
- Deletes UploadImagePanel, PluginInspector
- Deletes plugins/, tools/, upload/ directories
- Removes 18 legacy component files
```

### Commit 7
```
chore: remove legacy hooks, utils, and types

- Deletes useManifest, useVideoExport
- Deletes legacy useVideoProcessor
- Deletes detectToolType, runTool
- Deletes plugin types
- Removes 10 legacy files
```

### Commit 8
```
feat: add final CSS bundle for ForgeSyte 1.0.0

- Adds globals.css with theme variables
- Adds streaming.css with streaming layout
- Adds debug.css with debug panel styles
- Removes legacy CSS
```

### Commit 9
```
test: add integration test for unified Stream/Upload/Jobs flow

- Verifies navigation between views
- Confirms debug toggle works
- Ensures no legacy UI appears
- Adds smoke test for RealtimeProvider
```

---

## Next Steps

1. **Execute Phase 1** (Commits 1-4)
2. **Verify MP4 upload** end-to-end
3. **Execute Phase 2** (Commits 5-7)
4. **Execute Phase 3** (Commit 8)
5. **Execute Phase 4** (Commit 9)
6. **Run full verification** (manual + automated)
7. **Merge to main**

---

## Questions?

If any questions arise during implementation, refer to:
- `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_FE_Q&A_10_FINAL.md` through `PHASE_17_FE_Q&A_15_FINL.md`
- `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_FINAL_ARCH.md`
- `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_OVERVIEW.md`

All critical decisions are locked in and documented in the Q&A files.