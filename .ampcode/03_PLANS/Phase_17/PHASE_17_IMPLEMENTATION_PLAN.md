# Phase 17 Implementation Plan

**Date**: 2026-02-17
**Status**: Ready for Review
**Confidence**: 95% (5% uncertainty on specific CSS details)

---

## Executive Summary

This plan addresses two critical issues:

1. **MP4 Upload Not Fully Implemented**: The current `VideoTracker` component uses `useVideoProcessor` which processes frames via `runTool()` (legacy Phase 10 approach). This needs to be migrated to use the Phase 15/16 batch job API (`POST /api/video/upload`, `GET /api/jobs/{id}`).

2. **Legacy Phase 10 Architecture Removal**: The frontend still contains Phase 10 legacy code (PluginSelector, ToolSelector, ResultsPanel, manifest loading, detectToolType, old WebSocket endpoint) that conflicts with the Phase 17 unified architecture.

---

## Current State Analysis

### ✅ What's Complete (Phase 17)

**Backend (12/12 commits)**:
- WebSocket endpoint: `/ws/video/stream` ✅
- SessionManager ✅
- FrameValidator ✅
- Backpressure ✅
- All tests passing (60/60) ✅

**Frontend (Phase 17 components)**:
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
- Current implementation uses `useVideoProcessor` → `runTool()` (legacy)
- Should use Phase 15/16 batch job API:
  - `POST /api/video/upload` (multipart/form-data)
  - `GET /api/jobs/{job_id}` (poll for progress)
  - `GET /api/jobs` (list jobs)
- Need to implement proper `useVideoProcessor` that uses batch jobs
- Need to update `VideoTracker` to use new `useVideoProcessor`

---

## Implementation Plan

### Phase 1: Fix MP4 Upload (TDD - 4 Commits)

**Goal**: Implement proper MP4 upload using Phase 15/16 batch job API.

#### Commit 1: Implement useVideoProcessor with Batch Jobs

**File**: `web-ui/src/hooks/useVideoProcessor.ts`

**Changes**:
- Replace `runTool()` calls with batch job API
- Implement `uploadVideo(file: File)` → `POST /api/video/upload`
- Implement `pollJob(jobId: string)` → `GET /api/jobs/{job_id}`
- State: `status`, `currentJobId`, `progress`, `framesProcessed`, `error`
- Methods: `start(file: File)`, `cancel()`

**Tests**:
- `useVideoProcessor.test.ts`:
  - Upload creates job
  - Poll updates progress
  - Error handling
  - Cancel stops polling

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
- Remove `pluginId`, `tools` props (not needed for batch jobs)
- Add `debug` prop
- Use new `useVideoProcessor` API:
  - `processor.start(file)` on file upload
  - Display progress from `processor.state.progress`
  - Display status from `processor.state.status`
- Keep playback controls (Play/Pause/FPS)
- Keep overlay toggles

**Tests**:
- `VideoTracker.test.tsx`:
  - File upload starts job
  - Progress updates
  - Error display
  - Playback controls

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
- Add `error` field to state
- Add `status` field to state

**Tests**:
- Verify context provides correct state
- Verify context updates on job progress

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
- Read from `MP4ProcessingContext`

**Tests**:
- `StreamDebugPanel.test.tsx`:
  - MP4 section displays correctly
  - Updates on job progress

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
- `useWebSocket`, `FrameResult` imports
- `apiClient`, `Job` imports (keep for JobList)
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
- WebSocket error box
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

**TDD Workflow**:
1. Write CSS
2. Run frontend tester to verify UI
3. Run lint, type-check, all tests
4. Save test logs
5. Commit

---

### Phase 4: Final Verification (1 Commit)

#### Commit 9: Full Integration Test

**Actions**:
1. Run all tests (backend + frontend)
2. Run lint, type-check
3. Manual testing:
   - Stream mode: WebSocket connection, frame streaming, overlay rendering
   - Upload mode: MP4 upload, job creation, progress tracking
   - Jobs mode: Job list display
   - Debug mode: Debug panel metrics
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

## Questions for User (Before Implementation)

1. **MP4 Upload API**: Does the backend have `POST /api/video/upload` and `GET /api/jobs/{id}` endpoints implemented? Or do we need to implement these first?

2. **JobList Component**: Should `JobList` show both streaming sessions and MP4 jobs, or just MP4 jobs?

3. **Pipeline Selection**: In the final App, how should users select which pipeline to use for streaming? Should we add a `PipelineSelector` component (as mentioned in FE-5 user stories)?

4. **CSS Variables**: Do you have a specific design system or CSS variable definitions you want to use? Or should I use the existing variables from the codebase?

5. **VideoTracker Playback Controls**: Should `VideoTracker` keep the playback controls (Play/Pause/FPS/Device) after migration to batch jobs? Or should it just be a simple upload + progress display?

---

## Risk Assessment

**High Risk**:
- MP4 upload API may not be implemented on backend
- Breaking changes to `useVideoProcessor` may affect other components

**Medium Risk**:
- Deleting legacy components may break tests
- CSS changes may affect layout

**Low Risk**:
- App.tsx simplification (well-defined target)
- Deleting unused files

**Mitigation**:
- TDD approach ensures tests guide implementation
- Commit frequently to enable rollback
- Ask user questions before high-risk changes

---

## Success Criteria

1. ✅ MP4 upload works end-to-end (upload → job → progress → result)
2. ✅ Streaming works end-to-end (WebSocket → frame → result → overlay)
3. ✅ No Phase 10 legacy code remains
4. ✅ All tests pass (frontend + backend)
5. ✅ Lint and type-check pass
6. ✅ Debug mode shows correct metrics for both streaming and MP4
7. ✅ Clean folder structure (no legacy files)

---

## Next Steps

1. **User Approval**: Review this plan and answer the questions
2. **Backend Verification**: Confirm MP4 upload API exists
3. **Start Implementation**: Begin with Phase 1, Commit 1
4. **TDD Compliance**: Follow TDD workflow for every commit
5. **Test Logs**: Save all test logs as proof of GREEN status

---

**Confidence Level**: 95%

**Uncertainty Areas** (5%):
- Specific CSS variable names and values
- MP4 upload API exact response format
- JobList component behavior with mixed job types

**Will Ask User**: Before implementing high-risk changes