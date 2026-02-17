# Phase 17 Implementation Plan

**Date**: 2026-02-17
**Status**: Ready for Approval
**Confidence**: 95% (5% uncertainty on specific CSS details)

---

## Executive Summary

This plan addresses two critical issues:

1. **MP4 Upload Not Fully Implemented**: The current `VideoTracker` component uses `useVideoProcessor` which processes frames via `runTool()` (legacy Phase 10 approach). This needs to be migrated to use the Phase 16 batch job API (`POST /v1/video/submit`, `GET /v1/video/status/{job_id}`, `GET /v1/video/results/{job_id}`).

2. **Legacy Phase 10 Architecture Removal**: The frontend still contains Phase 10 legacy code (PluginSelector, ToolSelector, ResultsPanel, manifest loading, detectToolType, old WebSocket endpoint `/v1/stream`) that conflicts with the Phase 17 unified architecture.

---

## Current State Analysis

### ✅ What's Complete (Phase 17 Backend)

**Backend (12/12 commits - 100% COMPLETE)**:
- WebSocket endpoint: `/ws/video/stream` ✅
- SessionManager ✅
- FrameValidator ✅
- Backpressure ✅
- All backend tests passing (60/60) ✅

**Backend MP4 Upload API (Phase 16 - ALREADY EXISTS)**:
- `POST /v1/video/submit` - Submit video for async processing ✅
- `GET /v1/video/status/{job_id}` - Get job status ✅
- `GET /v1/video/results/{job_id}` - Get job results ✅

### ✅ What's Complete (Phase 17 Frontend Components)

**Frontend Streaming Components (Phase 17 - ALREADY IMPLEMENTED)**:
- `useWebSocket.ts` - Extended with binary streaming ✅
- `useRealtime.ts` - Phase 17 streaming hook ✅
- `RealtimeContext.tsx` - Phase 17 context ✅
- `types.ts` - Phase 17 streaming types ✅
- `CameraPreview.tsx` - Webcam capture + streaming ✅
- `RealtimeStreamingOverlay.tsx` - Detection overlay ✅
- `RealtimeErrorBanner.tsx` - Error banner ✅
- `StreamDebugPanel.tsx` - Debug metrics ✅
- `StreamingView.tsx` - Phase 17 streaming view ✅
- `MP4ProcessingContext.tsx` - MP4 state context ✅

### ❌ What's Broken / Legacy (Phase 10)

**App.tsx** - Contains Phase 10 legacy code:
- `PluginSelector` - Phase 10 plugin selection
- `ToolSelector` - Phase 10 tool selection
- `ResultsPanel` - Phase 10 results panel
- `manifest` loading logic
- `detectToolType` utility
- Old WebSocket usage with `/v1/stream` endpoint
- Image upload panel
- `streamEnabled` toggle
- Plugin/tool state management

**Legacy Components** (should be deleted):
- `PluginSelector.tsx`
- `ToolSelector.tsx`
- `ResultsPanel.tsx`
- `PluginInspector.tsx`
- `RecordButton.tsx`
- `OverlayToggles.tsx`
- `ConfidenceSlider.tsx`
- `ConfigPanel.tsx`
- `DeviceSelector.tsx`
- `FPSSlider.tsx`
- `RadarView.tsx`
- `LoadingSpinner.tsx`
- `ProgressBar.tsx`
- `BoundingBoxOverlay.tsx`
- `OverlayRenderer.tsx`
- `ResultOverlay.tsx`

**Legacy Hooks/Utils** (should be deleted):
- `useManifest.ts`
- `useVideoExport.ts`
- `detectToolType.ts`
- `runTool.ts` (used by useVideoProcessor)

**Legacy Types** (should be deleted):
- `types/plugin.ts` (manifest types)

**Legacy Tests** (should be deleted):
- `PluginSelector.test.tsx`
- `ToolSelector.test.tsx`
- `ResultsPanel.test.tsx`
- `ResultsPanel.plugin.test.tsx`
- `useManifest.test.ts`
- `useVideoExport.test.ts`

### ⚠️ What's Incomplete

**MP4 Upload / VideoTracker**:
- Current implementation uses `useVideoProcessor` → `runTool()` (legacy Phase 10)
- Should use Phase 16 batch job API:
  - `POST /v1/video/submit` (multipart/form-data)
  - `GET /v1/video/status/{job_id}` (poll for progress)
  - `GET /v1/video/results/{job_id}` (get results)
- Need to implement proper `useVideoProcessor` that uses batch jobs
- Need to update `VideoTracker` to use new `useVideoProcessor`

---

## Backend API Contract (Phase 16 - Already Exists)

### POST /v1/video/submit

Submit a video file for async processing.

**Request**:
- Method: `POST`
- URL: `/v1/video/submit?pipeline_id={pipeline_id}`
- Body: `multipart/form-data`
  - `file`: MP4 video file

**Response**:
```json
{
  "job_id": "uuid"
}
```

### GET /v1/video/status/{job_id}

Get status of a job.

**Response**:
```json
{
  "job_id": "uuid",
  "status": "pending" | "running" | "completed" | "failed",
  "progress": 0.0 | 0.5 | 1.0,
  "created_at": "2025-02-17T...",
  "updated_at": "2025-02-17T..."
}
```

### GET /v1/video/results/{job_id}

Get results of a completed job.

**Response**:
```json
{
  "job_id": "uuid",
  "results": { ... },
  "created_at": "2025-02-17T...",
  "updated_at": "2025-02-17T..."
}
```

---

## Implementation Plan

### Phase 1: Fix MP4 Upload (TDD - 4 Commits)

**Goal**: Implement proper MP4 upload using Phase 16 batch job API.

#### Commit 1: Implement useVideoProcessor with Batch Jobs

**File**: `web-ui/src/hooks/useVideoProcessor.ts`

**Changes**:
- Remove `runTool()` imports and usage
- Remove `videoRef`, `pluginId`, `tools`, `fps`, `device` props (not needed for batch jobs)
- Implement `uploadVideo(file: File, pipelineId: string)` → `POST /v1/video/submit`
- Implement `pollJob(jobId: string)` → `GET /v1/video/status/{job_id}`
- Implement `fetchResults(jobId: string)` → `GET /v1/video/results/{job_id}`
- State: `status`, `currentJobId`, `progress`, `error`, `results`
- Methods: `start(file: File, pipelineId: string)`, `cancel()`

**New API**:
```typescript
interface UseVideoProcessorArgs {
  file?: File | null;
  pipelineId?: string;
  debug?: boolean;
}

interface UseVideoProcessorReturn {
  state: {
    status: "idle" | "uploading" | "processing" | "completed" | "error";
    currentJobId: string | null;
    progress: number;
    framesProcessed: number;
    error?: string;
    results?: Record<string, unknown>;
  };
  start: (file: File, pipelineId: string) => void;
  cancel: () => void;
}
```

**Tests**:
- `useVideoProcessor.test.ts`:
  - Upload creates job
  - Poll updates progress
  - Error handling
  - Cancel stops polling
  - Results fetched on completion

**TDD Workflow**:
1. Write failing tests
2. Verify tests fail
3. Implement code
4. Verify tests pass
5. Run lint, type-check, all tests
6. Save test logs
7. Commit

---

#### Commit 2: Update VideoTracker to Use New useVideoProcessor

**File**: `web-ui/src/components/VideoTracker.tsx`

**Changes**:
- Remove `pluginId`, `tools` props (use `pipelineId` instead)
- Add `debug` prop
- Use new `useVideoProcessor` API:
  - `processor.start(file, pipelineId)` on file upload
  - Display progress from `processor.state.progress`
  - Display status from `processor.state.status`
  - Display results from `processor.state.results`
- Simplify UI: Remove playback controls (Play/Pause/FPS/Device), overlay toggles
- Keep: Upload button, progress display, results display

**New API**:
```typescript
interface VideoTrackerProps {
  pipelineId?: string;
  debug?: boolean;
}
```

**Tests**:
- `VideoTracker.test.tsx`:
  - File upload starts job
  - Progress updates
  - Error display
  - Results display
  - Debug mode shows metrics

**TDD Workflow**:
1. Write failing tests
2. Verify tests fail
3. Implement code
4. Verify tests pass
5. Run lint, type-check, all tests
6. Save test logs
7. Commit

---

#### Commit 3: Update MP4ProcessingContext

**File**: `web-ui/src/mp4/MP4ProcessingContext.tsx`

**Changes**:
- Ensure it works with new `useVideoProcessor` state
- Add `results` field to state
- Add `status` field to state (full enum)

**New API**:
```typescript
interface MP4State {
  active: boolean;
  jobId: string | null;
  progress: number;
  framesProcessed: number;
  status: "idle" | "uploading" | "processing" | "completed" | "error";
  results?: Record<string, unknown>;
  error?: string;
}
```

**Tests**:
- Verify context provides correct state
- Verify context updates on job progress
- Verify context updates on job completion

**TDD Workflow**:
1. Write failing tests
2. Verify tests fail
3. Implement code
4. Verify tests pass
5. Run lint, type-check, all tests
6. Save test logs
7. Commit

---

#### Commit 4: Update StreamDebugPanel for MP4 Metrics

**File**: `web-ui/src/components/StreamDebugPanel.tsx`

**Changes**:
- Ensure MP4 section shows:
  - Job ID
  - Status
  - Progress
  - Frames processed
  - Error (if any)
  - Results (if available)
- Read from `MP4ProcessingContext`

**Tests**:
- `StreamDebugPanel.test.tsx`:
  - MP4 section displays correctly
  - Updates on job progress
  - Shows results when available
  - Shows errors when available

**TDD Workflow**:
1. Write failing tests
2. Verify tests fail
3. Implement code
4. Verify tests pass
5. Run lint, type-check, all tests
6. Save test logs
7. Commit

---

### Phase 2: Remove Legacy Phase 10 Architecture (TDD - 3 Commits)

**Goal**: Remove all Phase 10 legacy code and implement final unified App.

#### Commit 5: Simplify App.tsx (Remove Phase 10 Legacy)

**File**: `web-ui/src/App.tsx`

**Remove**:
- `PluginSelector` import and usage
- `ToolSelector` import and usage
- `ResultsPanel` import and usage
- `useWebSocket`, `FrameResult` imports (keep for CameraPreview if needed)
- `detectToolType` import
- `PluginManifest` type import
- State: `selectedPlugin`, `selectedTools`, `streamEnabled`, `selectedJob`, `uploadResult`, `isUploading`, `manifest`, `manifestError`, `manifestLoading`
- `useWebSocket` hook usage
- Manifest loading effect
- Tool reset effect
- Tool auto-select effect
- Handlers: `handlePluginChange`, `handleToolChange`, `handleFileUpload`
- Left sidebar (PluginSelector, ToolSelector)
- Image upload panel
- Job Details panel
- ResultsPanel
- WebSocket error box (keep RealtimeErrorBanner in StreamingView)
- streamEnabled toggle
- Connection status indicator

**Replace with**:
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

**Tests**:
- `App.test.tsx`:
  - Navigation works (Stream/Upload/Jobs)
  - Debug toggle works
  - StreamingView renders in Stream mode
  - VideoTracker renders in Upload mode
  - JobList renders in Jobs mode

**TDD Workflow**:
1. Write failing tests
2. Verify tests fail
3. Implement code
4. Verify tests pass
5. Run lint, type-check, all tests
6. Save test logs
7. Commit

---

#### Commit 6: Delete Legacy Components

**Files to Delete**:
```
web-ui/src/components/PluginSelector.tsx
web-ui/src/components/ToolSelector.tsx
web-ui/src/components/ResultsPanel.tsx
web-ui/src/components/PluginInspector.tsx
web-ui/src/components/RecordButton.tsx
web-ui/src/components/OverlayToggles.tsx
web-ui/src/components/ConfidenceSlider.tsx
web-ui/src/components/ConfigPanel.tsx
web-ui/src/components/DeviceSelector.tsx
web-ui/src/components/FPSSlider.tsx
web-ui/src/components/RadarView.tsx
web-ui/src/components/LoadingSpinner.tsx
web-ui/src/components/ProgressBar.tsx
web-ui/src/components/BoundingBoxOverlay.tsx
web-ui/src/components/OverlayRenderer.tsx
web-ui/src/components/ResultOverlay.tsx
```

**Tests to Delete**:
```
web-ui/src/components/PluginSelector.test.tsx
web-ui/src/components/ToolSelector.test.tsx
web-ui/src/components/ResultsPanel.test.tsx
web-ui/src/components/ResultsPanel.plugin.test.tsx
web-ui/src/components/RecordButton.test.tsx
web-ui/src/components/OverlayToggles.test.tsx
web-ui/src/components/ConfidenceSlider.test.tsx
web-ui/src/components/ConfigPanel.test.tsx
web-ui/src/components/LoadingSpinner.test.tsx
web-ui/src/components/ProgressBar.test.tsx
web-ui/src/components/BoundingBoxOverlay.test.tsx
web-ui/src/components/OverlayRenderer.test.tsx
web-ui/src/components/ResultOverlay.test.tsx
```

**TDD Workflow**:
1. Delete files
2. Run all tests - ensure no test failures
3. Run lint, type-check
4. Save test logs
5. Commit

---

#### Commit 7: Delete Legacy Hooks, Utils, and Types

**Files to Delete**:
```
web-ui/src/hooks/useManifest.ts
web-ui/src/hooks/useVideoExport.ts
web-ui/src/hooks/useManifest.test.ts
web-ui/src/hooks/useVideoExport.test.ts
web-ui/src/utils/detectToolType.ts
web-ui/src/utils/runTool.ts
web-ui/src/types/plugin.ts
```

**TDD Workflow**:
1. Delete files
2. Run all tests - ensure no test failures
3. Run lint, type-check
4. Save test logs
5. Commit

---

### Phase 3: Final CSS and Styling (TDD - 1 Commit)

#### Commit 8: Final CSS Bundle

**Files**:
- `web-ui/src/styles/globals.css` (update)
- `web-ui/src/styles/streaming.css` (create/update)
- `web-ui/src/styles/debug.css` (create/update)

**globals.css**:
- Global variables
- Typography
- Layout
- Header (`.header`, `.logo`, `.nav`, `.top-right-controls`)
- Panels (`.panel`)

**streaming.css**:
- `.streaming-layout`
- `.stream-main`
- `.stream-debug`
- `.camera-preview`
- `.overlay-canvas`
- `.error-banner`

**debug.css**:
- `.debug-panel`
- `<h4>` styling
- `<hr>` styling

**Tests**:
- Verify all CSS classes are applied correctly
- Verify responsive layout
- Run frontend-tester to verify UI

**TDD Workflow**:
1. Write CSS
2. Run frontend-tester to verify UI
3. Run lint, type-check, all tests
4. Save test logs
5. Commit

---

### Phase 4: Final Verification (1 Commit)

#### Commit 9: Full Integration Test

**Actions**:
1. Run all tests (frontend)
2. Run lint, type-check
3. Manual testing:
   - Stream mode: WebSocket connection, frame streaming, overlay rendering
   - Upload mode: MP4 upload, job creation, progress tracking, results display
   - Jobs mode: Job list display
   - Debug mode: Debug panel metrics for both streaming and MP4
4. Save test logs
5. Commit

---

## Test Log Locations

All test logs will be saved to `/tmp/`:

```
/tmp/phase17_implementation_commit_01_final.log      # useVideoProcessor batch jobs
/tmp/phase17_implementation_commit_02_final.log      # VideoTracker update
/tmp/phase17_implementation_commit_03_final.log      # MP4ProcessingContext
/tmp/phase17_implementation_commit_04_final.log      # StreamDebugPanel MP4
/tmp/phase17_implementation_commit_05_final.log      # App.tsx simplification
/tmp/phase17_implementation_commit_06_final.log      # Delete legacy components
/tmp/phase17_implementation_commit_07_final.log      # Delete legacy hooks/utils
/tmp/phase17_implementation_commit_08_final.log      # Final CSS
/tmp/phase17_implementation_commit_09_final.log      # Full integration test
```

---

## Pre-Commit Verification Checklist (Frontend)

Before each commit, run:

```bash
cd web-ui

# 1. Run linter
npm run lint > /tmp/phase17_implementation_commit_<N>_lint.log 2>&1

# 2. Run type check
npm run type-check > /tmp/phase17_implementation_commit_<N>_typecheck.log 2>&1

# 3. Run tests
npm run test -- --run > /tmp/phase17_implementation_commit_<N>_test.log 2>&1

# 4. Verify all logs show success
grep -q "passed" /tmp/phase17_implementation_commit_<N>_lint.log
grep -q "passed" /tmp/phase17_implementation_commit_<N>_typecheck.log
grep -q "passed" /tmp/phase17_implementation_commit_<N>_test.log
```

**All four MUST PASS before committing.**

---

## Final Architecture (After Implementation)

### Folder Structure

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
      useVideoProcessor.ts
      useWebSocket.ts

    realtime/
      RealtimeContext.tsx
      types.ts

    mp4/
      MP4ProcessingContext.tsx

    api/
      client.ts
      types.ts

    styles/
      globals.css
      streaming.css
      debug.css
```

### App.tsx

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

### VideoTracker.tsx

```tsx
import React, { useState } from "react";
import { useVideoProcessor } from "../hooks/useVideoProcessor";
import { MP4ProcessingProvider } from "../mp4/MP4ProcessingContext";

interface VideoTrackerProps {
  pipelineId?: string;
  debug?: boolean;
}

export function VideoTracker({ pipelineId, debug }: VideoTrackerProps) {
  const [file, setFile] = useState<File | null>(null);

  const processor = useVideoProcessor({
    file,
    pipelineId,
    debug,
  });

  const mp4State = {
    active: processor.state.status === "uploading" || processor.state.status === "processing",
    jobId: processor.state.currentJobId ?? null,
    progress: processor.state.progress,
    framesProcessed: processor.state.framesProcessed,
    status: processor.state.status,
    results: processor.state.results,
    error: processor.state.error,
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0] ?? null;
    setFile(selected);
    if (selected && pipelineId) {
      processor.start(selected, pipelineId);
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
        {processor.state.status === "uploading" && <p>Uploading…</p>}
        {processor.state.status === "processing" && (
          <p>Processing… {processor.state.progress}%</p>
        )}
        {processor.state.status === "completed" && <p>Job completed.</p>}
        {processor.state.status === "error" && (
          <p>Error: {processor.state.error}</p>
        )}
      </div>
    </MP4ProcessingProvider>
  );
}
```

---

## Risk Assessment

**High Risk**:
- Breaking changes to `useVideoProcessor` may affect other components (mitigated by TDD)

**Medium Risk**:
- Deleting legacy components may break tests (mitigated by running all tests after each deletion)
- CSS changes may affect layout (mitigated by frontend-tester verification)

**Low Risk**:
- App.tsx simplification (well-defined target)
- Deleting unused files
- MP4 upload API already exists on backend

**Mitigation**:
- TDD approach ensures tests guide implementation
- Commit frequently to enable rollback
- Ask user questions before high-risk changes

---

## Success Criteria

1. ✅ MP4 upload works end-to-end (upload → job → progress → result)
2. ✅ Streaming works end-to-end (WebSocket → frame → result → overlay)
3. ✅ No Phase 10 legacy code remains
4. ✅ All tests pass (frontend)
5. ✅ Lint and type-check pass
6. ✅ Debug mode shows correct metrics for both streaming and MP4
7. ✅ Clean folder structure (no legacy files)

---

## Next Steps

1. **User Approval**: Review this plan
2. **Start Implementation**: Begin with Phase 1, Commit 1
3. **TDD Compliance**: Follow TDD workflow for every commit
4. **Test Logs**: Save all test logs as proof of GREEN status

---

## Questions for User (Before Implementation)

**I am 95% confident in this plan. The only areas where I need clarification are:**

1. **Pipeline Selection in Upload Mode**: How should users select which pipeline to use for MP4 upload? Should we add a `PipelineSelector` component in `VideoTracker`? Or should it be passed as a prop from App.tsx?

2. **JobList Component**: Should `JobList` show both MP4 jobs and streaming sessions, or just MP4 jobs? (Streaming sessions are ephemeral and not persisted)

3. **CSS Variables**: Do you have a specific design system or CSS variable definitions you want to use? Or should I use the existing variables from the codebase?

4. **VideoTracker Results Display**: How should `VideoTracker` display results after job completion? Should it show a summary, or allow playback with overlay?

**Please answer these questions before I start implementation.**

---

**Confidence Level**: 95%

**Uncertainty Areas** (5%):
- Specific CSS variable names and values
- Pipeline selection UI in Upload mode
- JobList component behavior with mixed job types
- VideoTracker results display approach

**Will Ask User**: Before implementing high-risk changes