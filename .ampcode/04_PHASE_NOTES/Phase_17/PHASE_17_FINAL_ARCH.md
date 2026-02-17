# 🔥 ForgeSyte 1.0.0 — Final Architecture Implementation Plan

**Purpose**: Complete MP4 upload functionality and remove all legacy Phase 10 plugin/tool architecture.

**Status**: READY TO IMPLEMENT

**Governance Rules**:
- ❌ NO HARDCODED PIPELINE IDs - backend chooses pipeline
- ❌ NO PLUGIN IDs in frontend code
- ❌ NO TOOL IDs in frontend code
- ✅ Frontend uploads MP4 file only
- ✅ Backend infers and executes appropriate pipeline

---

## Executive Summary

### What This Plan Does

1. **Fixes MP4 Upload**: Implements proper MP4 upload with job polling and progress tracking
2. **Removes Legacy Architecture**: Deletes all Phase 10 plugin/tool code
3. **Simplifies App.tsx**: Reduces from 400+ lines to ~80 lines
4. **Leaves Streaming Intact**: Does NOT touch streaming functionality

### What This Plan Does NOT Do

- ❌ Implement Phase 17 streaming changes (useWebSocket extension, etc.)
- ❌ Update StreamingView.tsx
- ❌ Add results viewer for completed jobs
- ❌ Add retry buttons for errors
- ❌ Add pipeline selection UI

---

## Implementation Phases

### Phase 1: Fix MP4 Upload (4 commits)
**Goal**: Get MP4 upload working with proper API integration

#### Commit 1: Add uploadVideo() to apiClient
- File: `web-ui/src/api/client.ts`
- Add `uploadVideo(file: File)` method
- POST to `/v1/video/submit`
- Returns `{ job_id: string }`
- NO pipelineId sent (backend chooses)

#### Commit 2: Rewrite useVideoProcessor
- File: `web-ui/src/hooks/useVideoProcessor.ts`
- Remove `runTool()` import
- Remove videoRef, fps, device parameters
- Use `uploadVideo()` + `pollJob()`
- Track: status, currentJobId, progress, framesProcessed, error
- Simplified interface: `{ state, start }`

#### Commit 3: Update MP4ProcessingContext
- File: `web-ui/src/mp4/MP4ProcessingContext.tsx`
- Ensure it provides: `{ active, jobId, progress, framesProcessed }`
- Used by StreamDebugPanel for MP4 metrics

#### Commit 4: Simplify VideoTracker
- File: `web-ui/src/components/VideoTracker.tsx`
- Remove: pluginId, tools props
- Remove: playback controls (Play, Pause, FPS, Device)
- Remove: local video preview with canvas
- Remove: overlay toggles
- Keep: file upload, progress display, status display
- Use new useVideoProcessor interface

---

### Phase 2: Remove Legacy Architecture (3 commits)
**Goal**: Delete all Phase 10 plugin/tool code

#### Commit 5: Simplify App.tsx
- File: `web-ui/src/App.tsx`
- Remove: PluginSelector, ToolSelector imports
- Remove: manifest loading logic
- Remove: detectToolType import
- Remove: useWebSocket import and usage
- Remove: ResultsPanel import
- Remove: image upload panel
- Remove: all plugin/tool state
- Replace with: simple 3-mode structure (Stream, Upload, Jobs)
- Add: debug toggle

**New App.tsx structure**:
```tsx
- viewMode: "stream" | "upload" | "jobs"
- debug: boolean
- Renders: StreamingView | VideoTracker | JobList
```

#### Commit 6: Delete legacy components
Delete files:
- `src/components/PluginSelector.tsx`
- `src/components/ToolSelector.tsx`
- `src/components/ResultsPanel.tsx`
- `src/components/UploadImagePanel.tsx` (if exists)
- `src/components/plugins/` directory
- `src/components/tools/` directory
- `src/components/upload/` directory

#### Commit 7: Delete legacy hooks/utils/types
Delete files:
- `src/hooks/useManifest.ts`
- `src/hooks/useVideoExport.ts`
- `src/hooks/useWebSocket.ts` (old plugin/tool version)
- `src/utils/detectToolType.ts`
- `src/utils/runTool.ts`
- `src/types/plugin.ts`

---

### Phase 3: Add Final CSS (3 commits)
**Goal**: Create clean, modern styling

#### Commit 8: Create globals.css
- File: `web-ui/src/styles/globals.css`
- Global variables (colors, fonts)
- Layout styles
- Header styles
- Panel styles

#### Commit 9: Create streaming.css
- File: `web-ui/src/styles/streaming.css`
- `.streaming-layout`
- `.stream-main`
- `.stream-debug`
- `.camera-preview`
- `.overlay-canvas`
- `.error-banner`

#### Commit 10: Create debug.css
- File: `web-ui/src/styles/debug.css`
- `.debug-panel`
- `<h4>` styling
- `<hr>` styling

---

### Phase 4: Integration Testing (1 commit)
**Goal**: Verify end-to-end functionality

#### Commit 11: Add integration tests
- File: `web-ui/src/tests/integration/app.test.tsx`
- Test: navigation between Stream, Upload, Jobs
- Test: debug toggle
- Test: MP4 upload flow
- Test: legacy components NOT rendered

---

## API Contract

### MP4 Upload

**POST `/v1/video/submit`**

Request:
```
Content-Type: multipart/form-data
file: <MP4 file>
```

Response:
```json
{
  "job_id": "job_123"
}
```

### Job Status

**GET `/v1/jobs/{job_id}`**

Response:
```json
{
  "job_id": "job_123",
  "status": "processing",
  "progress": 42,
  "frames_processed": 1234,
  "error": null
}
```

### Job List

**GET `/v1/jobs`**

Response:
```json
{
  "jobs": [
    {
      "job_id": "job_123",
      "status": "completed",
      "progress": 100,
      "frames_processed": 3456
    }
  ]
}
```

---

## Component API

### apiClient.uploadVideo(file)
```typescript
async uploadVideo(file: File): Promise<{ job_id: string }>
```

### useVideoProcessor
```typescript
{
  state: {
    status: "idle" | "processing" | "completed" | "error",
    currentJobId: string | null,
    progress: number,
    framesProcessed: number,
    errorMessage: string | null
  },
  start(file: File): void
}
```

### VideoTracker
```typescript
interface VideoTrackerProps {
  debug?: boolean;
}
```

### MP4ProcessingContext
```typescript
{
  active: boolean,
  jobId: string | null,
  progress: number,
  framesProcessed: number
}
```

---

## File Structure After Migration

```
web-ui/
  src/
    App.tsx (simplified)

    components/
      StreamingView.tsx (unchanged)
      VideoTracker.tsx (simplified)
      JobList.tsx (unchanged)

      CameraPreview.tsx (unchanged)
      RealtimeStreamingOverlay.tsx (unchanged)
      RealtimeErrorBanner.tsx (unchanged)
      StreamDebugPanel.tsx (unchanged)

    hooks/
      useRealtime.ts (unchanged)
      useVideoProcessor.ts (rewritten)

    realtime/
      RealtimeContext.tsx (unchanged)

    mp4/
      MP4ProcessingContext.tsx (unchanged)

    api/
      client.ts (extended with uploadVideo)

    styles/
      globals.css (new)
      streaming.css (new)
      debug.css (new)
```

---

## Testing Strategy

### Before Each Commit
```bash
cd web-ui
npm run lint
npm run type-check
npm run test -- --run
```

### All three MUST PASS before committing.

### Test Files to Update
- `src/hooks/useVideoProcessor.test.ts` - Rewrite for new interface
- `src/components/VideoTracker.test.tsx` - Rewrite for simplified component
- `src/App.test.tsx` - Rewrite for simplified App

---

## Rollback Plan

If any commit causes issues:

1. **Identify the breaking commit** via git bisect
2. **Revert the commit**: `git revert <commit>`
3. **Verify tests pass**
4. **Document the issue** in PHASE_17_Q&A.md

---

## Success Criteria

### Phase 1 Complete
- ✅ MP4 upload creates job
- ✅ Job polling works
- ✅ Progress updates correctly
- ✅ Completion status displayed
- ✅ Errors displayed correctly

### Phase 2 Complete
- ✅ No plugin selector in UI
- ✅ No tool selector in UI
- ✅ No manifest loading
- ✅ No detectToolType usage
- ✅ No runTool usage
- ✅ App.tsx < 100 lines

### Phase 3 Complete
- ✅ CSS files exist
- ✅ Styles apply correctly
- ✅ Responsive layout works

### Phase 4 Complete
- ✅ All integration tests pass
- ✅ Manual testing confirms functionality

---

## Questions & Clarifications

### Q: Should we add a pipeline selector for MP4 upload?
**A: NO.** Backend chooses the pipeline. Frontend sends only the file.

### Q: Should we display job results (detections, etc.)?
**A: NO.** Just show completion status. Results viewer is a separate feature.

### Q: Should we add retry button for upload errors?
**A: NO.** Just display error. User can re-upload.

### Q: Should we update StreamingView.tsx?
**A: NO.** Leave streaming as-is. This is Phase 17 FE work, separate from MP4 upload fix.

### Q: Should we implement Phase 17 streaming changes now?
**A: NO.** Focus ONLY on MP4 upload. Streaming is already working.

---

## Next Steps

1. **Review this plan** and confirm all decisions
2. **Create feature branch**: `git checkout -b fix/mp4-upload-remove-legacy`
3. **Execute Phase 1** (4 commits)
4. **Execute Phase 2** (3 commits)
5. **Execute Phase 3** (3 commits)
6. **Execute Phase 4** (1 commit)
7. **Run full test suite**
8. **Create PR**

---

**Total Commits**: 11
**Estimated Time**: 2-3 hours
**Risk Level**: LOW (changes are isolated to MP4 upload path)

---

**Document Version**: 1.0
**Last Updated**: 2026-02-17
**Status**: READY FOR IMPLEMENTATION