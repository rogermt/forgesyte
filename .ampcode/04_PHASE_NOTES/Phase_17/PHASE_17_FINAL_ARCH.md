# ForgeSyte 1.0.0 — Final Architecture Handover Document

This document defines the **final**, **stable**, **supported** architecture for ForgeSyte 1.0.0.
It replaces all previous "phase" terminology and supersedes all earlier UI/FE architecture drafts.

---

## Status: Ready to Execute

**Implementation Plan**: See `PHASE_17_IMPLEMENTATION_PLAN.md`
**Total Commits**: 9
**Backend**: 12/12 Phase 17 commits complete ✅
**Frontend Streaming**: 8/8 Phase 17 commits complete ✅
**MP4 Upload**: Broken - needs migration to batch job API
**Legacy Removal**: Pending (18 components, 10 hooks/utils to delete)

---

## 1. Final Folder Structure (Authoritative)

```
web-ui/
  src/
    App.tsx

    components/
      StreamingView.tsx
      VideoTracker.tsx
      JobList.tsx

      CameraPreview.tsx
      RealtimeStreamingOverlay.tsx
      RealtimeErrorBanner.tsx
      StreamDebugPanel.tsx

    hooks/
      useRealtime.ts
      useMP4Upload.ts (NEW - replaces useVideoProcessor)

    realtime/
      RealtimeContext.tsx

    mp4/
      MP4ProcessingContext.tsx

    api/
      client.ts

    styles/
      globals.css (NEW)
      streaming.css (NEW)
      debug.css (NEW)

    tests/
      integration/
        app.test.tsx (NEW)
```

### ✔ No plugin/tool folders
### ✔ No manifest logic
### ✔ No detectToolType
### ✔ No legacy WebSocket
### ✔ No image upload panel
### ✔ No useVideoProcessor (legacy)
### ✔ No useManifest
### ✔ No runTool

This is the **final** structure.

---

## 2. Final CSS Bundle

### `globals.css`
- Global variables (theme)
- Typography
- Layout
- Header
- Panels

### `streaming.css`
- `.streaming-layout`
- `.stream-main`
- `.stream-debug`
- `.camera-preview`
- `.overlay-canvas`
- `.error-banner`

### `debug.css`
- `.debug-panel`
- `<h4>` styling
- `<hr>` styling

These three files cover **all** UI styling for 1.0.0.

---

## 3. Final TypeScript Types

Located in `src/api/types.ts` and `src/realtime/types.ts`:

```ts
// MP4 Upload Types
export interface MP4UploadState {
  status: "idle" | "uploading" | "processing" | "completed" | "error" | "cancelled";
  jobId: string | null;
  progress: number;
  framesProcessed: number;
  errorMessage: string | null;
}

export interface MP4ProcessingState {
  active: boolean;
  jobId: string | null;
  progress: number;
  framesProcessed: number;
  status: MP4UploadState["status"];
  error: string | null;
}

// Streaming Types
export interface Detection {
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  score: number;
}

export interface RealtimeResult {
  detections: Detection[];
  timestamp: string;
}

// Job Types
export interface Mp4Job {
  id: string;
  status: "queued" | "processing" | "completed" | "error";
  progress: number;
  frames_processed: number;
  error?: string;
}
```

These are the **only** types the frontend needs for 1.0.0.

---

## 4. Final Backend API Contract

This is the **canonical** FE ↔ BE contract.

### WebSocket: `/ws/video/stream`

**Client → Server:**
- Binary JPEG frames (`Blob`)

**Server → Client:**
```json
{
  "frame_index": 42,
  "result": {
    "detections": [
      { "x": 100, "y": 120, "width": 80, "height": 60, "label": "person", "score": 0.94 }
    ]
  }
}
```

### POST `/v1/video/submit`

**Request:**
`multipart/form-data`
field: `file` (MP4)

**Response:**
```json
{ "job_id": "job_123" }
```

### GET `/api/jobs/{job_id}`

**Response:**
```json
{
  "id": "job_123",
  "status": "processing",
  "progress": 42,
  "frames_processed": 1234,
  "error": null
}
```

### GET `/api/jobs`

**Response:**
```json
[
  {
    "id": "job_123",
    "status": "completed",
    "progress": 100,
    "frames_processed": 3456
  }
]
```

---

## 5. Final Architecture Summary (No Phases)

### Top-Level App

`App.tsx` owns:
- `viewMode: "stream" | "upload" | "jobs"`
- `debug: boolean`

Renders:
- **Stream** → `RealtimeProvider` + `StreamingView`
- **Upload** → `VideoTracker`
- **Jobs** → `JobList`

---

### Streaming Path (Live YOLO)

**Components:**
- `CameraPreview`
- `RealtimeStreamingOverlay`
- `RealtimeErrorBanner`
- `StreamDebugPanel`

**Hook:**
- `useRealtime`

**Context:**
- `RealtimeProvider`

**Flow:**
1. CameraPreview captures frames
2. Frames sent via WebSocket
3. Backend returns YOLO detections
4. Overlay draws boxes
5. Debug panel shows metrics

---

### MP4 Upload Path (Async YOLO)

**Components:**
- `VideoTracker`
- `StreamDebugPanel` (MP4 section)

**Hook:**
- `useMP4Upload` (NEW - replaces useVideoProcessor)

**Context:**
- `MP4ProcessingProvider`

**Flow:**
1. User uploads MP4
2. Backend creates job via `/v1/video/submit`
3. Frontend polls job via `/api/jobs/{job_id}`
4. Debug panel shows progress
5. JobList shows history

**Critical Rule:**
- 🚫 NEVER hardcode pipeline IDs
- The backend chooses the pipeline
- The frontend only uploads the file

---

### Jobs Path

**Component:**
- `JobList`

**API:**
- `apiClient.listJobs()`

**Scope:**
- Shows only MP4 upload jobs
- Streaming sessions are ephemeral and not persisted

---

## 6. Migration Script (Safe Cleanup)

Create `cleanup.sh`:

```bash
#!/bin/bash

echo "Removing legacy plugin/tool architecture..."

rm -f src/components/PluginSelector.tsx
rm -f src/components/ToolSelector.tsx
rm -f src/components/ResultsPanel.tsx
rm -f src/components/UploadImagePanel.tsx
rm -f src/components/PluginInspector.tsx

rm -f src/hooks/useManifest.ts
rm -f src/hooks/useVideoExport.ts
rm -f src/hooks/useVideoProcessor.ts
rm -f src/hooks/useVideoProcessor.types.ts
rm -f src/utils/detectToolType.ts
rm -f src/utils/runTool.ts
rm -f src/types/plugin.ts

rm -rf src/components/plugins
rm -rf src/components/tools
rm -rf src/components/upload

echo "Cleanup complete."
```

Run:
```
chmod +x cleanup.sh
./cleanup.sh
```

---

## 7. Final App.tsx

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

## 8. Final VideoTracker.tsx

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

## 9. Final useMP4Upload Hook

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

## 10. Final apiClient

```typescript
export const apiClient = {
  async uploadVideo(file: File): Promise<{ job_id: string }> {
    const form = new FormData();
    form.append("file", file);

    const res = await fetch("/v1/video/submit", {
      method: "POST",
      body: form,
    });

    if (!res.ok) {
      throw new Error(`Upload failed: ${res.status}`);
    }

    return res.json();
  },

  async getJob(jobId: string) {
    const res = await fetch(`/api/jobs/${jobId}`);
    if (!res.ok) throw new Error("Failed to fetch job");
    return res.json();
  },

  async pollJob(jobId: string) {
    while (true) {
      const job = await this.getJob(jobId);
      if (job.status === "completed" || job.status === "error") {
        return job;
      }
      await new Promise((r) => setTimeout(r, 500));
    }
  },

  async listJobs() {
    const res = await fetch("/api/jobs");
    if (!res.ok) throw new Error("Failed to list jobs");
    return res.json();
  },
};
```

---

## 11. Critical Governance Rules

### Rule 1: No Pipeline IDs in Frontend
**🚫 NEVER hardcode pipeline IDs, plugin IDs, tool IDs, or model IDs anywhere in ForgeSyte.**

- Not in VideoTracker
- Not in App.tsx
- Not in hooks
- Not in contexts
- Not in API calls
- Not even temporarily

**The backend chooses the pipeline. The frontend only uploads the file.**

### Rule 2: No Plugin/Tool Architecture
**🚫 The plugin/tool architecture is permanently removed.**

- No PluginSelector
- No ToolSelector
- No manifest loading
- No detectToolType
- No runTool
- No analyzeImage

### Rule 3: Deterministic Workflows
**Every workflow must be explicit and deterministic.**

- Streaming → useRealtime
- MP4 Upload → useMP4Upload
- Jobs → apiClient.listJobs()

No mixed responsibilities. No hidden behavior.

---

## 12. Implementation Roadmap

See `PHASE_17_IMPLEMENTATION_PLAN.md` for the complete 9-commit implementation plan.

**Phase 1: Fix MP4 Upload (4 commits)**
1. Add `apiClient.uploadVideo()`
2. Create `useMP4Upload` hook
3. Update `VideoTracker`
4. Update `MP4ProcessingContext` + `StreamDebugPanel`

**Phase 2: Remove Legacy Architecture (3 commits)**
5. Simplify `App.tsx`
6. Delete legacy components (18 files)
7. Delete legacy hooks/utils/types (10 files)

**Phase 3: Final CSS (1 commit)**
8. Add globals.css, streaming.css, debug.css

**Phase 4: Verification (1 commit)**
9. Add integration test

---

## 13. Verification Checklist

### Pre-Commit
- [ ] No legacy imports remain
- [ ] `/v1/video/submit` is used for MP4 upload
- [ ] `useMP4Upload` is used in VideoTracker
- [ ] No pipelineId hardcoded anywhere

### Post-Merge
- [ ] Streaming works (webcam, overlay, debug)
- [ ] MP4 upload works (upload → progress → complete)
- [ ] Jobs list works (shows completed jobs)
- [ ] Debug toggle works
- [ ] No legacy UI appears
- [ ] All tests pass

---

## 14. Reference Documents

- `PHASE_17_IMPLEMENTATION_PLAN.md` — Complete 9-commit implementation plan
- `PHASE_17_REMOVE_LEGACY_ARCH.md` — List of files to delete
- `PHASE_17_OVERVIEW.md` — Phase 17 overview
- `PHASE_17_BACKEND_USER_STORIES.md` — Backend implementation details
- `PHASE_17_FRONTEND_USER_STORIES` — Frontend user stories
- `PHASE_17_Q&A_*.md` — Q&A clarifications (10-15)

---

## 15. Success Criteria

ForgeSyte 1.0.0 is complete when:

✅ MP4 upload works via `/v1/video/submit`
✅ Streaming works via `/ws/video/stream`
✅ Jobs list shows MP4 upload history
✅ No legacy plugin/tool code remains
✅ No pipeline IDs in frontend
✅ All tests pass
✅ Manual QA passes
✅ CSS is finalized

---

This is the **complete**, **final**, **release‑ready** ForgeSyte 1.0.0 architecture.