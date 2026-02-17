# Phase 17 Legacy Cleanup Plan

**Status**: Ready to Execute
**Date**: 2026-02-17
**Purpose**: Remove all Phase 10 legacy code to complete ForgeSyte 1.0.0

---

## Executive Summary

**What's Already Done ✅**
- App.tsx: Already using final Phase 17 architecture (Stream/Upload/Jobs modes)
- MP4ProcessingContext.tsx: Implemented and working
- VideoTracker.tsx: Updated to use Phase 17 architecture
- useVideoProcessor.ts: Phase 17 version with async job polling
- All Phase 17 streaming components: Implemented
- Phase 10 component files (PluginSelector, ToolSelector, ResultsPanel, useManifest): Already deleted

**What Needs to Be Done ❌**
- Delete Phase 10 test files that mock deleted components
- Delete Phase 10 UI components not used in Phase 17
- Delete Phase 10 utility components
- Clean up Storybook files
- Verify final architecture

---

## Current State Analysis

### ✅ Phase 17 Components (KEEP)
```
web-ui/src/
├── App.tsx                              ✅ Final unified architecture
├── components/
│   ├── StreamingView.tsx               ✅ Phase 17 streaming view
│   ├── VideoTracker.tsx                ✅ Phase 17 MP4 upload
│   ├── JobList.tsx                     ✅ Job list view
│   ├── CameraPreview.tsx               ✅ Camera capture
│   ├── RealtimeStreamingOverlay.tsx    ✅ Detection overlay
│   ├── RealtimeErrorBanner.tsx         ✅ Error display
│   ├── StreamDebugPanel.tsx            ✅ Debug metrics
│   ├── PipelineSelector.tsx            ✅ Pipeline selection
│   ├── ErrorBanner.tsx                 ✅ Generic error banner
│   ├── BoundingBoxOverlay.tsx          ✅ Bounding box rendering
│   ├── OverlayRenderer.tsx             ✅ Overlay rendering
│   ├── ProgressBar.tsx                 ✅ Progress indicator
│   ├── LoadingSpinner.tsx              ✅ Loading state
│   └── FPSSlider.tsx                   ✅ FPS control
├── hooks/
│   ├── useVideoProcessor.ts            ✅ Phase 17 MP4 upload hook
│   ├── useVideoExport.ts               ✅ Video export (keep for now)
│   └── useWebSocket.ts                 ✅ Phase 17 WebSocket hook
├── realtime/
│   ├── RealtimeContext.tsx             ✅ Phase 17 realtime context
│   ├── useRealtime.ts                  ✅ Phase 17 realtime hook
│   └── types.ts                        ✅ Phase 17 types
└── mp4/
    └── MP4ProcessingContext.tsx        ✅ Phase 17 MP4 context
```

### ❌ Phase 10 Components (DELETE)
```
web-ui/src/
├── components/
│   ├── ConfigPanel.tsx                 ❌ Phase 10 plugin config
│   ├── ConfigPanel.test.tsx            ❌ Phase 10 test
│   ├── RecordButton.tsx                ❌ Stream recording (not in Phase 17)
│   ├── RecordButton.test.tsx           ❌ Phase 10 test
│   ├── RecordButton.module.css         ❌ Phase 10 styles
│   ├── RadarView.tsx                   ❌ Sports radar view (not in Phase 17)
│   ├── DeviceSelector.tsx              ❌ Device selection (not in Phase 17)
│   ├── OverlayToggles.tsx              ❌ Overlay toggles (not in Phase 17)
│   ├── OverlayToggles.test.tsx         ❌ Phase 10 test
│   ├── OverlayToggles.module.css       ❌ Phase 10 styles
│   ├── ConfidenceSlider.tsx            ❌ Confidence slider (not used)
│   └── ConfidenceSlider.test.tsx       ❌ Phase 10 test
├── App.tdd.test.tsx                    ❌ Tests Phase 10 plugin/tool architecture
└── App.integration.test.tsx            ❌ Tests Phase 10 plugin/tool architecture
```

---

## Cleanup Tasks

### Task 1: Delete Phase 10 Test Files
**Files to delete:**
```
web-ui/src/App.tdd.test.tsx
web-ui/src/App.integration.test.tsx
web-ui/src/components/ConfigPanel.test.tsx
web-ui/src/components/RecordButton.test.tsx
web-ui/src/components/OverlayToggles.test.tsx
web-ui/src/components/ConfidenceSlider.test.tsx
```

**Reason:** These tests mock Phase 10 components (PluginSelector, ToolSelector, ResultsPanel) that no longer exist.

---

### Task 2: Delete Phase 10 UI Components
**Files to delete:**
```
web-ui/src/components/ConfigPanel.tsx
web-ui/src/components/RecordButton.tsx
web-ui/src/components/RecordButton.module.css
web-ui/src/components/RadarView.tsx
web-ui/src/components/DeviceSelector.tsx
web-ui/src/components/OverlayToggles.tsx
web-ui/src/components/OverlayToggles.module.css
web-ui/src/components/ConfidenceSlider.tsx
```

**Reason:** These components are not used in Phase 17 architecture:
- ConfigPanel: Plugin configuration not needed in Phase 17
- RecordButton: Stream recording not in Phase 17 scope
- RadarView: Sports-specific visualization not in Phase 17
- DeviceSelector: Device selection not needed for Phase 17
- OverlayToggles: Overlay controls not in Phase 17 UI
- ConfidenceSlider: Confidence adjustment not in Phase 17 UI

---

### Task 3: Clean Up Storybook Files
**Files to check:**
```
web-ui/src/stories/RealtimeOverlay.stories.tsx
```

**Action:** Remove references to `PluginInspector` if present.

---

### Task 4: Verify No Remaining Phase 10 References
**Search patterns to verify:**
```
PluginSelector
ToolSelector
ResultsPanel
useManifest
detectToolType
PluginInspector
ConfigPanel
RecordButton
RadarView
DeviceSelector
OverlayToggles
ConfidenceSlider
```

**Expected result:** No matches in code (only in deletion list)

---

## Execution Order

### Step 1: Delete Phase 10 Test Files
```bash
cd /home/rogermt/forgesyte/web-ui/src
rm -f App.tdd.test.tsx
rm -f App.integration.test.tsx
rm -f components/ConfigPanel.test.tsx
rm -f components/RecordButton.test.tsx
rm -f components/OverlayToggles.test.tsx
rm -f components/ConfidenceSlider.test.tsx
```

### Step 2: Delete Phase 10 UI Components
```bash
cd /home/rogermt/forgesyte/web-ui/src/components
rm -f ConfigPanel.tsx
rm -f RecordButton.tsx
rm -f RecordButton.module.css
rm -f RadarView.tsx
rm -f DeviceSelector.tsx
rm -f OverlayToggles.tsx
rm -f OverlayToggles.module.css
rm -f ConfidenceSlider.tsx
```

### Step 3: Clean Up Storybook
```bash
# Check and update stories file
# Remove PluginInspector references
```

### Step 4: Verify Cleanup
```bash
# Search for any remaining Phase 10 references
cd /home/rogermt/forgesyte/web-ui/src
rg "PluginSelector|ToolSelector|ResultsPanel|useManifest|detectToolType|PluginInspector|ConfigPanel|RecordButton|RadarView|DeviceSelector|OverlayToggles|ConfidenceSlider"
```

### Step 5: Run Tests (AFTER cleanup complete)
```bash
cd /home/rogermt/forgesyte/web-ui
npm run lint
npm run type-check
npm run test -- --run
```

---

## Final Architecture (After Cleanup)

### Folder Structure
```
web-ui/src/
├── App.tsx                              # Final unified architecture
├── components/
│   ├── StreamingView.tsx               # Live streaming view
│   ├── VideoTracker.tsx                # MP4 upload view
│   ├── JobList.tsx                     # Job history view
│   ├── CameraPreview.tsx               # Camera capture
│   ├── RealtimeStreamingOverlay.tsx    # Detection overlay
│   ├── RealtimeErrorBanner.tsx         # Error display
│   ├── StreamDebugPanel.tsx            # Debug metrics
│   ├── PipelineSelector.tsx            # Pipeline selection
│   ├── ErrorBanner.tsx                 # Generic error banner
│   ├── BoundingBoxOverlay.tsx          # Bounding box rendering
│   ├── OverlayRenderer.tsx             # Overlay rendering
│   ├── ProgressBar.tsx                 # Progress indicator
│   ├── LoadingSpinner.tsx              # Loading state
│   └── FPSSlider.tsx                   # FPS control
├── hooks/
│   ├── useVideoProcessor.ts            # MP4 upload hook
│   ├── useVideoExport.ts               # Video export
│   └── useWebSocket.ts                 # WebSocket hook
├── realtime/
│   ├── RealtimeContext.tsx             # Realtime context
│   ├── useRealtime.ts                  # Realtime hook
│   └── types.ts                        # Realtime types
├── mp4/
│   └── MP4ProcessingContext.tsx        # MP4 processing context
├── api/
│   └── client.ts                       # API client
└── styles/
    ├── globals.css                     # Global styles
    └── streaming.css                   # Streaming styles
```

### App Architecture
```
App.tsx
├── viewMode: "stream" | "upload" | "jobs"
├── debug: boolean
└── Renders:
    ├── Stream → RealtimeProvider + StreamingView
    ├── Upload → VideoTracker
    └── Jobs → JobList
```

---

## Success Criteria

### ✅ Cleanup Complete When:
1. All Phase 10 test files deleted
2. All Phase 10 UI components deleted
3. No Phase 10 references in codebase
4. App.tsx uses only Phase 17 components
5. No import errors
6. No type errors
7. Tests pass (after cleanup)

### ❌ Cleanup Failed If:
1. Any Phase 10 component still imported
2. Any test still references deleted components
3. Import errors after cleanup
4. Type errors after cleanup

---

## Notes

### What About useVideoExport?
`useVideoExport.ts` is kept for now. It's not part of Phase 17 core but may be useful for future features. Can be removed later if not needed.

### What About Storybook?
Storybook files should be checked and updated to remove Phase 10 references. This is a separate cleanup task.

### What About CSS Files?
Only the CSS files explicitly listed in the deletion list should be removed. Global CSS files (`globals.css`, `streaming.css`) should be kept.

---

## Rollback Plan

If cleanup causes issues:
1. Restore from git: `git checkout -- .`
2. Identify problematic files
3. Delete files one at a time
4. Test after each deletion

---

## Next Steps

1. Execute cleanup (Steps 1-4)
2. Verify no Phase 10 references remain
3. Run tests (Step 5)
4. Fix any issues that arise
5. Commit cleanup

**Commit Message:**
```
refactor(frontend): Remove Phase 10 legacy architecture

- Delete Phase 10 test files (App.tdd.test.tsx, App.integration.test.tsx)
- Delete Phase 10 UI components (ConfigPanel, RecordButton, RadarView, etc.)
- Delete Phase 10 utility components (DeviceSelector, OverlayToggles, ConfidenceSlider)
- Clean up Storybook references
- Verify final Phase 17 architecture

Phase 17: Real-Time Streaming Inference
ForgeSyte 1.0.0: Final Unified Architecture
```