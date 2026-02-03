# Web-UI Issue #146: Job Pipeline Cleanup & Migration

**Branch**: `refactor/web-ui-job-pipeline-cleanup`  
**GitHub Issue**: [#146](https://github.com/rogermt/forgesyte/issues/146)

---

## Executive Summary

Remove obsolete tool-runner execution system and consolidate on job pipeline. Six focused deletions/rewires replace direct tool calls with `/v1/analyze` + job polling.

---

## Architecture: Before & After

### BEFORE (Old System)

```
User Upload
    ↓
[UploadPanel] 
    ↓
runTool(toolId, file)
    ↓
/v1/tools/{id}/run (DIRECT, SYNCHRONOUS)
    ↓
Result (immediate)
    ↓
[ResultsPanel] + detectToolType branching
```

**Problems:**
- Synchronous execution blocks UI
- Tool selection via ToolSelector component (obsolete)
- Type detection logic scattered (`detectToolType`)
- Video tracker calls tools directly

---

### AFTER (New System)

```
User Upload
    ↓
[UploadPanel]
    ↓
apiClient.analyzeImage(file, pluginId)
    ↓
/v1/analyze (JOB ENDPOINT, RETURNS job_id)
    ↓
apiClient.pollJob(job_id)
    ↓
[JobStatusIndicator] queued → running → done
    ↓
[ResultsPanel] (generic, uses job.result directly)
    ↓
[JobError] (on failure)
```

**Benefits:**
- Non-blocking job queue
- Unified execution path (no special cases)
- UI reflects actual server state (queued/running/done/error)
- Video tracker uses same pipeline

---

## Exact PR Diffs

### 1.1 Delete `ToolSelector.tsx`

**File path**: `web-ui/src/components/ToolSelector.tsx`

```diff
diff --git a/web-ui/src/components/ToolSelector.tsx b/web-ui/src/components/ToolSelector.tsx
deleted file mode 100644
index abcdef0..0000000
--- a/web-ui/src/components/ToolSelector.tsx
+++ /dev/null
@@ -1,100 +0,0 @@
-// ToolSelector component - OBSOLETE
-// Tool selection is now handled via plugin discovery endpoints
-// No longer needed since execution is unified via /v1/analyze job pipeline
```

**Remove from any imports** (example):

```diff
diff --git a/web-ui/src/pages/AnalyzePage.tsx b/web-ui/src/pages/AnalyzePage.tsx
index 1234567..89abcde 100644
--- a/web-ui/src/pages/AnalyzePage.tsx
+++ b/web-ui/src/pages/AnalyzePage.tsx
@@ -1,7 +1,6 @@
 import React from "react";
-import { ToolSelector } from "../components/ToolSelector";
 import { UploadPanel } from "../components/UploadPanel";
 import { ResultsPanel } from "../components/ResultsPanel";
@@ -20,11 +19,6 @@ export const AnalyzePage: React.FC = () => {
   const [selectedPluginId, setSelectedPluginId] = React.useState<string | null>(null);
 
   return (
-    <div className="analyze-layout">
-      <ToolSelector
-        selectedPluginId={selectedPluginId}
-        onSelectPlugin={setSelectedPluginId}
-      />
-      <UploadPanel selectedPluginId={selectedPluginId} />
-      <ResultsPanel />
-    </div>
+    <div className="analyze-layout">
+      <UploadPanel selectedPluginId={selectedPluginId} />
+      <ResultsPanel />
+    </div>
   );
 };
```

---

### 1.2 Delete `detectToolType.ts`

**File path**: `web-ui/src/utils/detectToolType.ts`

```diff
diff --git a/web-ui/src/utils/detectToolType.ts b/web-ui/src/utils/detectToolType.ts
deleted file mode 100644
index abcdef0..0000000
--- a/web-ui/src/utils/detectToolType.ts
+++ /dev/null
@@ -1,80 +0,0 @@
-// detectToolType - OBSOLETE
-// Tool-type branching is no longer needed
-// Job results structure is uniform across all plugins
```

**Remove from ResultsPanel** (or similar):

```diff
diff --git a/web-ui/src/components/ResultsPanel.tsx b/web-ui/src/components/ResultsPanel.tsx
index 2345678..9abcdea 100644
--- a/web-ui/src/components/ResultsPanel.tsx
+++ b/web-ui/src/components/ResultsPanel.tsx
@@ -1,6 +1,5 @@
 import React from "react";
-import { detectToolType } from "../utils/detectToolType";
 import { JobStatusIndicator } from "./JobStatusIndicator";
 import { JobError } from "./JobError";
@@ -20,13 +19,7 @@ export const ResultsPanel: React.FC<Props> = ({ job }) => {
   if (!job) return null;
 
-  const toolType = detectToolType(job.plugin_id);
-
   return (
     <div className="results-panel">
-      {toolType === "ocr" && <OcrResults result={job.result} />}
-      {toolType === "yolo" && <YoloResults result={job.result} />}
-      {/* etc... */}
+      <GenericJobResults result={job.result} />
     </div>
   );
 };
```

---

### 1.3 Delete `toolRunner.ts` (or mark deprecated)

**File path**: `web-ui/src/api/toolRunner.ts`

```diff
diff --git a/web-ui/src/api/toolRunner.ts b/web-ui/src/api/toolRunner.ts
deleted file mode 100644
index abcdef0..0000000
--- a/web-ui/src/api/toolRunner.ts
+++ /dev/null
@@ -1,60 +0,0 @@
-// runTool - OBSOLETE
-// Direct tool execution via /v1/tools/{id}/run is deprecated
-// Use apiClient.analyzeImage() + apiClient.pollJob() instead
```

**Replace usages in UploadPanel**:

```diff
diff --git a/web-ui/src/components/UploadPanel.tsx b/web-ui/src/components/UploadPanel.tsx
index 3456789..abcdeff 100644
--- a/web-ui/src/components/UploadPanel.tsx
+++ b/web-ui/src/components/UploadPanel.tsx
@@ -1,8 +1,8 @@
 import React from "react";
-import { runTool } from "../api/toolRunner";
+import { apiClient } from "../api/apiClient";
 import { JobStatusIndicator } from "./JobStatusIndicator";
 
   const onFileSelected = async (file: File) => {
     if (!selectedPluginId) return;
     setError(null);
     try {
-      const result = await runTool(selectedPluginId, { file });
-      setJob({ status: "done", result });
+      const { job_id } = await apiClient.analyzeImage(file, selectedPluginId);
+      const job = await apiClient.pollJob(job_id);
+      setJob(job);
     } catch (e: any) {
       setError(e.message ?? "Failed to analyze image");
     }
   };
```

---

## New Components to Add

### 2. `JobStatusIndicator.tsx`

**File path**: `web-ui/src/components/JobStatusIndicator.tsx`

```typescript
import React from "react";

export type JobStatus = "idle" | "queued" | "running" | "done" | "error";

interface Props {
  status: JobStatus;
}

export const JobStatusIndicator: React.FC<Props> = ({ status }) => {
  if (status === "idle") return null;

  const label =
    status === "queued"
      ? "Queued"
      : status === "running"
      ? "Running"
      : status === "done"
      ? "Done"
      : status === "error"
      ? "Error"
      : status;

  return (
    <span className={`job-status job-status--${status}`}>
      {label}
    </span>
  );
};
```

**Why this approach:**
- Minimal, testable, single responsibility
- CSS classes for styling flexibility
- Returns null when idle (no DOM clutter)

---

### 3. `JobError.tsx`

**File path**: `web-ui/src/components/JobError.tsx`

```typescript
import React from "react";

interface Props {
  error: string | null;
  onRetry?: () => void;
}

export const JobError: React.FC<Props> = ({ error, onRetry }) => {
  if (!error) return null;

  return (
    <div className="job-error">
      <strong>Error:</strong> {error}
      {onRetry && (
        <button onClick={onRetry} className="job-error-retry">
          Retry
        </button>
      )}
    </div>
  );
};
```

**Why this approach:**
- Clean, minimal error display
- Optional retry callback for UX flexibility
- CSS class for styling

---

### 4. Updated `VideoTracker.tsx`

**File path**: `web-ui/src/components/VideoTracker.tsx`

```typescript
import React from "react";
import { apiClient } from "../api/apiClient";
import { JobStatusIndicator, type JobStatus } from "./JobStatusIndicator";
import { JobError } from "./JobError";

interface Job {
  id: string;
  status: JobStatus;
  result: any;
  error?: string;
}

interface VideoTrackerProps {
  pluginId: string; // e.g. "forgesyte-yolo-tracker"
}

export const VideoTracker: React.FC<VideoTrackerProps> = ({ pluginId }) => {
  const videoRef = React.useRef<HTMLVideoElement | null>(null);
  const canvasRef = React.useRef<HTMLCanvasElement | null>(null);

  const [job, setJob] = React.useState<Job | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [isRunning, setIsRunning] = React.useState(false);

  const captureFrameAsBlob = async (): Promise<Blob | null> => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return null;

    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    return new Promise((resolve) => {
      canvas.toBlob((blob) => resolve(blob), "image/png");
    });
  };

  const processFrame = React.useCallback(async () => {
    if (!pluginId) return;
    const frameBlob = await captureFrameAsBlob();
    if (!frameBlob) return;

    setError(null);
    setJob((prev) =>
      prev ? { ...prev, status: "queued" } : { id: "", status: "queued", result: null }
    );

    try {
      const file = new File([frameBlob], "frame.png", { type: "image/png" });
      const { job_id } = await apiClient.analyzeImage(file, pluginId);

      setJob({ id: job_id, status: "running", result: null });

      const jobResult = await apiClient.pollJob(job_id);
      setJob({
        id: job_id,
        status: jobResult.status as JobStatus,
        result: jobResult.result,
        error: jobResult.error,
      });

      // TODO: draw overlays based on jobResult.result
      // e.g. bounding boxes for YOLO player_detection
    } catch (e: any) {
      setError(e.message ?? "Failed to process frame");
      setJob((prev) => (prev ? { ...prev, status: "error" } : null));
    }
  }, [pluginId]);

  React.useEffect(() => {
    if (!isRunning) return;

    let frameId: number;
    const loop = async () => {
      await processFrame();
      // simple throttling: one frame every 500ms
      setTimeout(() => {
        frameId = requestAnimationFrame(loop);
      }, 500);
    };

    frameId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(frameId);
  }, [isRunning, processFrame]);

  const handleRetry = () => {
    setError(null);
    processFrame();
  };

  return (
    <div className="video-tracker">
      <video ref={videoRef} autoPlay muted playsInline />
      <canvas ref={canvasRef} style={{ display: "none" }} />

      <div className="video-tracker-controls">
        <button onClick={() => setIsRunning((v) => !v)}>
          {isRunning ? "Stop Tracking" : "Start Tracking"}
        </button>
        <JobStatusIndicator status={job?.status ?? "idle"} />
        <JobError error={error ?? job?.error ?? null} onRetry={handleRetry} />
      </div>

      {/* TODO: overlay component that reads job?.result and draws on canvas */}
    </div>
  );
};
```

**Why this approach:**
- Uses job pipeline exclusively (no direct tool calls)
- Frame capture per 500ms (throttled)
- Status & error display via new components
- TODO: overlay rendering left to caller (not this component's concern)

---

## Files to Delete (Summary)

| File | Reason |
|------|--------|
| `web-ui/src/components/ToolSelector.tsx` | Tool selection is obsolete; job pipeline is unified |
| `web-ui/src/utils/detectToolType.ts` | Type detection branches removed; job.result is uniform |
| `web-ui/src/api/toolRunner.ts` | Direct tool execution replaced by job pipeline |

---

## Files to Add

| File | Purpose |
|------|---------|
| `web-ui/src/components/JobStatusIndicator.tsx` | Show queued/running/done/error status |
| `web-ui/src/components/JobError.tsx` | Display error messages with optional retry |
| **Update**: `web-ui/src/components/VideoTracker.tsx` | Use job pipeline instead of direct tool calls |
| **Update**: `web-ui/src/components/UploadPanel.tsx` | Replace `runTool()` with `analyzeImage()` + `pollJob()` |
| **Update**: `web-ui/src/components/ResultsPanel.tsx` | Remove `detectToolType` branching |

---

## Migration Checklist

- [ ] Delete `ToolSelector.tsx`
- [ ] Remove `ToolSelector` imports from `AnalyzePage.tsx` (or wherever)
- [ ] Delete `detectToolType.ts`
- [ ] Remove `detectToolType` imports from `ResultsPanel.tsx`
- [ ] Simplify `ResultsPanel.tsx` to use generic result display
- [ ] Delete `toolRunner.ts` or deprecate it
- [ ] Update `UploadPanel.tsx` to use `apiClient.analyzeImage()` + `apiClient.pollJob()`
- [ ] Add `JobStatusIndicator.tsx`
- [ ] Add `JobError.tsx`
- [ ] Update `VideoTracker.tsx` to use job pipeline
- [ ] Run tests: `npm run test -- --run`
- [ ] Run lint + type-check: `npm run check`
- [ ] Commit with proper message

---

## Pre-Implementation Questions

**Please review and approve:**

1. **Deletion of `ToolSelector`**: Is plugin selection handled elsewhere now? Or should we add a plugin selector dropdown to `AnalyzePage.tsx`?

2. **`detectToolType` removal**: Does your `ResultsPanel` have type-specific rendering, or can we just render `job.result` generically?

3. **Video overlay rendering**: Should `VideoTracker` render bounding boxes itself, or pass `job.result` to a separate overlay component?

4. **Error retry behavior**: Should retry button clear the error and re-process the same frame, or submit to upload panel again?

5. **Test updates**: Do you have existing tests for `ToolSelector`, `runTool()`, `detectToolType`? Should we update or delete them?

---

## Success Criteria

After implementation, the following should be true:

✅ All imports of `ToolSelector`, `detectToolType`, `runTool` removed  
✅ All file executions go through `apiClient.analyzeImage()` + `apiClient.pollJob()`  
✅ `VideoTracker` uses job pipeline  
✅ Job status & error UI components present  
✅ Tests pass: `npm run test -- --run`  
✅ Type check clean: `npm run type-check`  
✅ Lint clean: `npm run lint`  
✅ No `TODO` comments except overlay rendering  

---

## Notes

- **MVP-grade**: Only what's needed for job pipeline to be the sole execution path
- **No styling**: CSS classes are set up, but actual styles are a separate pass
- **Overlay TODO**: Video tracking overlay rendering is intentionally not included; that's a separate component
- **Backwards compatibility**: We're not maintaining old execution paths; this is a full cutover

