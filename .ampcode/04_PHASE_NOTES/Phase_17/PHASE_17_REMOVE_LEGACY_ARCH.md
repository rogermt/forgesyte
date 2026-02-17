# Phase 17 — Remove Legacy Phase 10 Architecture

**Status**: Ready to Execute (after Phase 1 verification)
**Files to Delete**: 28 components, hooks, utils, and types
**Implementation**: Commits 6-7 of the 9-commit migration plan

---

## Purpose

This document lists all Phase 10 legacy code that must be removed as part of the ForgeSyte 1.0.0 migration.

**Do NOT execute this cleanup until Phase 1 (MP4 upload fix) is verified and working.**

---

## Files to Delete (28 Total)

### Components (18 files)

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
src/components/RecordButton.tsx
src/components/RecordButton.test.tsx
src/components/OverlayToggles.tsx
src/components/OverlayToggles.test.tsx
src/components/ConfidenceSlider.tsx
src/components/ConfidenceSlider.test.tsx
src/components/FPSSlider.tsx
src/components/DeviceSelector.tsx
src/components/RadarView.tsx
```

### Component Directories (3 directories)

```
src/components/plugins/ (entire directory)
src/components/tools/ (entire directory)
src/components/upload/ (entire directory)
```

### Hooks (7 files)

```
src/hooks/useManifest.ts
src/hooks/useManifest.test.ts
src/hooks/useVideoExport.ts
src/hooks/useVideoExport.test.ts
src/hooks/useVideoProcessor.ts (legacy version - replaced by useMP4Upload)
src/hooks/useVideoProcessor.test.ts (legacy version)
src/hooks/useVideoProcessor.types.ts
```

### Utils (2 files)

```
src/utils/detectToolType.ts
src/utils/runTool.ts
```

### Types (1 file)

```
src/types/plugin.ts
```

### Tests (legacy test files - 5 files)

```
src/components/ResultOverlay.test.tsx
src/components/OverlayRenderer.test.tsx
src/components/ConfigPanel.test.tsx
src/components/LoadingSpinner.test.tsx
src/components/ProgressBar.test.tsx
```

**Total: 28 files + 3 directories**

---

## Pre-Deletion Safety Check

Before deleting any files, run these checks to ensure no active code still references them:

```bash
# Check for plugin/tool imports
rg "PluginSelector" src
rg "ToolSelector" src
rg "ResultsPanel" src
rg "useManifest" src
rg "useVideoExport" src
rg "detectToolType" src
rg "runTool" src
rg "analyzeImage" src
rg "manifest" src
```

**Expected Result**: No matches (or only matches in files being deleted)

If any of these return results in files you're NOT deleting, fix those files first.

---

## Deletion Script

Save as `scripts/delete_legacy_arch.sh`:

```bash
#!/bin/bash

echo "=== Deleting Legacy Phase 10 Architecture ==="
echo ""

# Safety check
echo "Running pre-deletion safety check..."
if rg "PluginSelector|ToolSelector|ResultsPanel|useManifest|useVideoExport|detectToolType|runTool" src | grep -v "\.test\." | grep -v "\.test\.tsx" | grep -v "\.spec\." > /dev/null; then
  echo "❌ ERROR: Found active references to legacy code in non-test files"
  echo "Fix these references before deleting files:"
  rg "PluginSelector|ToolSelector|ResultsPanel|useManifest|useVideoExport|detectToolType|runTool" src | grep -v "\.test\." | grep -v "\.test\.tsx" | grep -v "\.spec\."
  exit 1
fi

echo "✅ Safety check passed - no active references found"
echo ""

# Delete components
echo "Deleting legacy components..."
rm -f src/components/PluginSelector.tsx
rm -f src/components/PluginSelector.test.tsx
rm -f src/components/ToolSelector.tsx
rm -f src/components/ToolSelector.test.tsx
rm -f src/components/ResultsPanel.tsx
rm -f src/components/ResultsPanel.test.tsx
rm -f src/components/ResultsPanel.plugin.test.tsx
rm -f src/components/UploadImagePanel.tsx
rm -f src/components/PluginInspector.tsx
rm -f src/components/RecordButton.tsx
rm -f src/components/RecordButton.test.tsx
rm -f src/components/OverlayToggles.tsx
rm -f src/components/OverlayToggles.test.tsx
rm -f src/components/ConfidenceSlider.tsx
rm -f src/components/ConfidenceSlider.test.tsx
rm -f src/components/FPSSlider.tsx
rm -f src/components/DeviceSelector.tsx
rm -f src/components/RadarView.tsx

# Delete component directories
echo "Deleting legacy component directories..."
rm -rf src/components/plugins
rm -rf src/components/tools
rm -rf src/components/upload

# Delete hooks
echo "Deleting legacy hooks..."
rm -f src/hooks/useManifest.ts
rm -f src/hooks/useManifest.test.ts
rm -f src/hooks/useVideoExport.ts
rm -f src/hooks/useVideoExport.test.ts
rm -f src/hooks/useVideoProcessor.ts
rm -f src/hooks/useVideoProcessor.test.ts
rm -f src/hooks/useVideoProcessor.types.ts

# Delete utils
echo "Deleting legacy utils..."
rm -f src/utils/detectToolType.ts
rm -f src/utils/runTool.ts

# Delete types
echo "Deleting legacy types..."
rm -f src/types/plugin.ts

# Delete legacy tests
echo "Deleting legacy tests..."
rm -f src/components/ResultOverlay.test.tsx
rm -f src/components/OverlayRenderer.test.tsx
rm -f src/components/ConfigPanel.test.tsx
rm -f src/components/LoadingSpinner.test.tsx
rm -f src/components/ProgressBar.test.tsx

echo ""
echo "✅ Legacy architecture cleanup complete!"
echo "Deleted: 28 files + 3 directories"
```

Run:
```bash
chmod +x scripts/delete_legacy_arch.sh
./scripts/delete_legacy_arch.sh
```

---

## Files to Keep (Do NOT Delete)

### Streaming Components (Phase 17 - Keep)

```
src/components/StreamingView.tsx
src/components/CameraPreview.tsx
src/components/CameraPreview.test.tsx
src/components/RealtimeStreamingOverlay.tsx
src/components/RealtimeStreamingOverlay.test.tsx
src/components/RealtimeErrorBanner.tsx
src/components/RealtimeErrorBanner.test.tsx
src/components/StreamDebugPanel.tsx
src/components/StreamDebugPanel.test.tsx
src/components/BoundingBoxOverlay.tsx
src/components/OverlayRenderer.tsx
```

### MP4 Components (Phase 17 - Keep)

```
src/components/VideoTracker.tsx
src/components/VideoTracker.test.tsx (will be updated)
src/components/JobList.tsx
src/components/JobList.test.tsx
src/components/ProgressBar.tsx (reused for MP4 progress)
```

### Hooks (Phase 17 - Keep)

```
src/hooks/useRealtime.ts
src/hooks/useRealtime.test.ts
src/hooks/useMP4Upload.ts (NEW - replaces useVideoProcessor)
src/hooks/useWebSocket.ts (Phase 17 streaming - keep)
```

### Contexts (Phase 17 - Keep)

```
src/realtime/RealtimeContext.tsx
src/mp4/MP4ProcessingContext.tsx
```

### API (Phase 17 - Keep)

```
src/api/client.ts (will be updated with uploadVideo)
src/api/types.ts
```

---

## App.tsx Changes

Before deleting legacy components, `App.tsx` must be simplified to remove all legacy imports.

### Legacy Imports to Remove:

```tsx
// DELETE THESE IMPORTS
import { PluginSelector } from "./components/PluginSelector";
import { ToolSelector } from "./components/ToolSelector";
import { ResultsPanel } from "./components/ResultsPanel";
import { UploadImagePanel } from "./components/UploadImagePanel";
import { useManifest } from "./hooks/useManifest";
import { detectToolType } from "./utils/detectToolType";
import { analyzeImage } from "./api/client";
import { useWebSocket } from "./hooks/useWebSocket";
```

### New Imports to Keep:

```tsx
// KEEP THESE IMPORTS
import { RealtimeProvider } from "./realtime/RealtimeContext";
import { StreamingView } from "./components/StreamingView";
import { VideoTracker } from "./components/VideoTracker";
import { JobList } from "./components/JobList";
```

### Legacy State to Remove:

```tsx
// DELETE THIS STATE
const [selectedPlugin, setSelectedPlugin] = useState(null);
const [selectedTools, setSelectedTools] = useState([]);
const [manifest, manifestError] = useManifest(selectedPlugin);
```

### New State to Keep:

```tsx
// KEEP THIS STATE
const [viewMode, setViewMode] = useState<"stream" | "upload" | "jobs">("stream");
const [debug, setDebug] = useState(false);
```

---

## Post-Deletion Verification

After deletion, run these checks:

### 1. Verify No Legacy Imports Remain

```bash
rg "PluginSelector" src
rg "ToolSelector" src
rg "ResultsPanel" src
rg "useManifest" src
rg "useVideoExport" src
rg "detectToolType" src
rg "runTool" src
rg "analyzeImage" src
```

**Expected**: No results

### 2. Verify All Tests Pass

```bash
cd web-ui
npm run lint
npm run type-check
npm run test -- --run
```

**Expected**: All tests pass

### 3. Verify App Builds

```bash
npm run build
```

**Expected**: Build succeeds

### 4. Manual QA

- [ ] App loads without errors
- [ ] Stream mode works
- [ ] Upload mode works
- [ ] Jobs mode works
- [ ] Debug toggle works
- [ ] No legacy UI appears

---

## Rollback Plan

If deletion causes issues, restore from Git:

```bash
# Undo the deletion commit
git revert <commit-hash>

# Or reset to before deletion
git reset --hard HEAD~1
```

---

## Summary

**Before Deletion**:
- 28 legacy files + 3 directories
- Phase 10 plugin/tool architecture
- Mixed responsibilities
- Confusing UI

**After Deletion**:
- Clean, minimal codebase
- Phase 17 architecture only
- Explicit workflows
- Deterministic behavior

**Files Remaining**:
- Streaming: 11 components
- MP4: 4 components
- Hooks: 3 hooks
- Contexts: 2 contexts
- Total: ~20 active files

---

## Next Steps

1. **Complete Phase 1** (Fix MP4 upload)
2. **Verify Phase 1** (MP4 upload works)
3. **Run deletion script** (Commits 6-7)
4. **Verify post-deletion** (All checks pass)
5. **Proceed to Phase 3-4** (CSS + integration tests)

---

## Questions?

Refer to:
- `PHASE_17_IMPLEMENTATION_PLAN.md` — Complete implementation plan
- `PHASE_17_FINAL_ARCH.md` — Final architecture
- `PHASE_17_Q&A_*.md` — Q&A clarifications