# Migration Plan: Job Pipeline Cleanup (Issue #146)

**Status**: Awaiting approval  
**Branch**: `refactor/web-ui-job-pipeline-cleanup`  
**GitHub Issue**: [#146](https://github.com/rogermt/forgesyte/issues/146)

---

## Overview

This document details the **step-by-step migration** from the old tool-runner execution system to the unified job pipeline.

**Goal**: Make `/v1/analyze` + job polling the **only** execution path in the Web-UI.

**Scope**: 
- ❌ Remove 3 files
- ✅ Add 2 new components  
- ⚙️ Update 3 existing components
- 📋 Provide migration helper script

**Time estimate**: ~2 hours (implementation) + ~1 hour (testing)

---

## Prerequisite Understanding

### Current State (Before)

```
UploadPanel → runTool(toolId, file) 
              ↓
           /v1/tools/{id}/run (SYNC)
              ↓
          Result (immediate)
              ↓
ResultsPanel (detectToolType decides what to show)
```

**Problems:**
- `runTool` blocks the UI thread
- `detectToolType` adds branching complexity
- `ToolSelector` is only used once (at startup)
- Video tracker can't share execution logic

### Target State (After)

```
UploadPanel → apiClient.analyzeImage(file, pluginId)
              ↓
           /v1/analyze (ASYNC, returns job_id)
              ↓
         apiClient.pollJob(job_id)
              ↓
        [JobStatusIndicator] (queued/running/done/error)
              ↓
       ResultsPanel (generic, no branching)
              ↓
       [JobError] (if needed)
```

**Benefits:**
- Non-blocking, proper async/await
- Unified execution path
- Clear state transitions
- Reusable across components (UploadPanel, VideoTracker, etc.)

---

## Part 1: Deletions (Clean Slate)

### 1.1 Delete `ToolSelector.tsx`

**Why**: Tool selection is now handled via plugin discovery API (separate endpoint). The `ToolSelector` component was tightly coupled to the old direct-execution model.

**File**: `web-ui/src/components/ToolSelector.tsx`

```bash
cd web-ui
git rm src/components/ToolSelector.tsx
```

**Affected imports**: Search and remove from:
- `src/pages/AnalyzePage.tsx` (or wherever it's imported)
- Tests: `src/components/__tests__/ToolSelector.test.tsx` (if exists)

**Replacement**: If you need a plugin selector dropdown, add it directly to `AnalyzePage.tsx` or create a minimal `PluginSelector.tsx` that uses `apiClient.listPlugins()`.

---

### 1.2 Delete `detectToolType.ts`

**Why**: This utility existed to map `plugin_id` → render logic (OCR → show text, YOLO → show boxes, etc.). The new job result structure is uniform across all plugins; the plugin-specific rendering is the plugin's responsibility.

**File**: `web-ui/src/utils/detectToolType.ts`

```bash
cd web-ui
git rm src/utils/detectToolType.ts
```

**Affected imports**: Search and remove from:
- `src/components/ResultsPanel.tsx`
- Any tests that reference it
- Remove the branching logic (OCR if/else, YOLO if/else, etc.)

**Replacement**: Simplify `ResultsPanel.tsx` to display `job.result` generically, or let each plugin type define its own result renderer (future enhancement).

---

### 1.3 Delete `toolRunner.ts`

**Why**: `runTool()` was the direct-execution interface. It's now replaced by `apiClient.analyzeImage()` + `apiClient.pollJob()`, which are already in `apiClient.ts`.

**File**: `web-ui/src/api/toolRunner.ts` (or `web-ui/src/utils/toolRunner.ts`)

```bash
cd web-ui
git rm src/api/toolRunner.ts  # adjust path if needed
```

**Affected imports**: Search and remove from:
- `src/components/UploadPanel.tsx`
- `src/components/VideoTracker.tsx` (if present)
- Any tests

**Replacement**: Use `apiClient.analyzeImage()` and `apiClient.pollJob()` instead (these should already exist in `apiClient.ts`).

---

## Part 2: New Components

### 2.1 Create `JobStatusIndicator.tsx`

**Why**: Show the user the current job state. Replaces implicit feedback from synchronous execution.

**File**: `web-ui/src/components/JobStatusIndicator.tsx`

**Responsibilities**:
- Display: "Queued", "Running", "Done", "Error"
- Return `null` if status is "idle" (no DOM clutter)
- Use CSS class names for styling

**Code** (see `WEB-UI_ISSUE_146.md` for full version)

**Usage**:
```tsx
<JobStatusIndicator status={job?.status ?? "idle"} />
```

**Tests to add**:
- ✅ Renders null when idle
- ✅ Renders "Queued" when status is "queued"
- ✅ Renders "Running" when status is "running"
- ✅ Renders "Done" when status is "done"
- ✅ Renders "Error" when status is "error"

---

### 2.2 Create `JobError.tsx`

**Why**: Display error messages from job failures. Optional retry button for UX.

**File**: `web-ui/src/components/JobError.tsx`

**Responsibilities**:
- Display error message
- Optional retry button callback
- Return `null` if no error (no DOM clutter)

**Code** (see `WEB-UI_ISSUE_146.md` for full version)

**Usage**:
```tsx
<JobError 
  error={error ?? job?.error ?? null} 
  onRetry={handleRetry} 
/>
```

**Tests to add**:
- ✅ Renders null when no error
- ✅ Renders error message
- ✅ Calls onRetry when button clicked

---

## Part 3: Component Updates

### 3.1 Update `UploadPanel.tsx`

**Current pattern** (OLD):
```tsx
const onFileSelected = async (file: File) => {
  try {
    const result = await runTool(selectedPluginId, { file });
    setJob({ status: "done", result });
  } catch (e) {
    setError(e.message);
  }
};
```

**New pattern** (JOB PIPELINE):
```tsx
const onFileSelected = async (file: File) => {
  try {
    const { job_id } = await apiClient.analyzeImage(file, selectedPluginId);
    const job = await apiClient.pollJob(job_id);
    setJob(job);
  } catch (e) {
    setError(e.message);
  }
};
```

**Changes**:
- Import `apiClient` instead of `runTool`
- Call `analyzeImage()` → get `job_id`
- Call `pollJob(job_id)` → poll until done
- Store full job object (includes status, result, error)

**Tests to update**:
- Mock `apiClient.analyzeImage()` to return `{ job_id: "123" }`
- Mock `apiClient.pollJob()` to return `{ status: "done", result: { ... } }`
- Verify error handling still works

---

### 3.2 Update `ResultsPanel.tsx`

**Current pattern** (OLD):
```tsx
const toolType = detectToolType(job.plugin_id);

return (
  <>
    {toolType === "ocr" && <OcrResults result={job.result} />}
    {toolType === "yolo" && <YoloResults result={job.result} />}
  </>
);
```

**New pattern** (GENERIC):
```tsx
return <GenericJobResults result={job.result} />;
```

**Alternatives** (pick one):

**Option A: Fully generic**
```tsx
<pre>{JSON.stringify(job.result, null, 2)}</pre>
```

**Option B: Simple card layout**
```tsx
<div className="job-result">
  {job.result && Object.entries(job.result).map(([k, v]) => (
    <div key={k}><strong>{k}:</strong> {String(v)}</div>
  ))}
</div>
```

**Option C: Plugin-specific renderers (future)**
```tsx
const renderer = resultRenderers[job.plugin_id];
return renderer ? renderer(job.result) : <GenericJobResults result={job.result} />;
```

**Tests to update**:
- Remove `detectToolType` references
- Test that `GenericJobResults` renders the result

---

### 3.3 Update `VideoTracker.tsx` (if exists)

**Current pattern** (OLD):
```tsx
const processFrame = async (frame: Frame) => {
  const result = await runTool(pluginId, { frame });
  drawOverlays(result);
};
```

**New pattern** (JOB PIPELINE):
```tsx
const processFrame = async (frame: Frame) => {
  const { job_id } = await apiClient.analyzeImage(frameAsBlob, pluginId);
  const job = await apiClient.pollJob(job_id);
  drawOverlays(job.result);
};
```

**See full implementation in `WEB-UI_ISSUE_146.md`**

---

## Part 4: Tests

### Strategy

**Test levels**:

1. **Unit Tests** (no API calls)
   - `JobStatusIndicator.test.tsx` (new)
   - `JobError.test.tsx` (new)

2. **Component Tests** (mock API)
   - `UploadPanel.test.tsx` (update)
   - `ResultsPanel.test.tsx` (update)
   - `VideoTracker.test.tsx` (update if exists)

3. **Integration Tests** (full flow)
   - `npm run test:integration` (if available)

### Test Files to Add

```
web-ui/src/components/__tests__/
  ├── JobStatusIndicator.test.tsx (NEW)
  ├── JobError.test.tsx (NEW)
  ├── UploadPanel.test.tsx (UPDATE)
  ├── ResultsPanel.test.tsx (UPDATE)
  └── VideoTracker.test.tsx (UPDATE if exists)
```

### Example Test (JobStatusIndicator)

```tsx
// JobStatusIndicator.test.tsx
import { render, screen } from "@testing-library/react";
import { JobStatusIndicator } from "../JobStatusIndicator";

describe("JobStatusIndicator", () => {
  it("returns null when idle", () => {
    const { container } = render(<JobStatusIndicator status="idle" />);
    expect(container.firstChild).toBeNull();
  });

  it("renders Queued when queued", () => {
    render(<JobStatusIndicator status="queued" />);
    expect(screen.getByText("Queued")).toBeInTheDocument();
  });

  it("renders Running when running", () => {
    render(<JobStatusIndicator status="running" />);
    expect(screen.getByText("Running")).toBeInTheDocument();
  });

  it("renders Done when done", () => {
    render(<JobStatusIndicator status="done" />);
    expect(screen.getByText("Done")).toBeInTheDocument();
  });

  it("renders Error when error", () => {
    render(<JobStatusIndicator status="error" />);
    expect(screen.getByText("Error")).toBeInTheDocument();
  });

  it("applies correct CSS class", () => {
    const { container } = render(<JobStatusIndicator status="running" />);
    expect(container.firstChild).toHaveClass("job-status--running");
  });
});
```

---

## Part 5: Execution Checklist

Follow this order:

### Phase 1: Prep (15 min)
- [ ] Create feature branch (already done)
- [ ] Read this plan carefully
- [ ] Run script to find all references: `./migrate_to_job_pipeline.sh`
- [ ] Document any edge cases not covered here

### Phase 2: Deletions (10 min)
- [ ] Delete `ToolSelector.tsx`
- [ ] Remove `ToolSelector` imports
- [ ] Delete `detectToolType.ts`
- [ ] Remove `detectToolType` imports
- [ ] Delete `toolRunner.ts`
- [ ] Remove `runTool()` imports

### Phase 3: New Components (20 min)
- [ ] Create `JobStatusIndicator.tsx`
- [ ] Create `JobStatusIndicator.test.tsx`
- [ ] Create `JobError.tsx`
- [ ] Create `JobError.test.tsx`
- [ ] Run tests: `npm run test -- --run`

### Phase 4: Updates (30 min)
- [ ] Update `UploadPanel.tsx` (use `apiClient` instead of `runTool`)
- [ ] Update `UploadPanel.test.tsx`
- [ ] Update `ResultsPanel.tsx` (remove branching)
- [ ] Update `ResultsPanel.test.tsx`
- [ ] Update `VideoTracker.tsx` if exists
- [ ] Update `VideoTracker.test.tsx` if exists

### Phase 5: Verification (15 min)
- [ ] Run all tests: `npm run test -- --run`
- [ ] Run type check: `npm run type-check`
- [ ] Run lint: `npm run lint`
- [ ] No TypeScript errors
- [ ] No ESLint warnings

### Phase 6: Commit (5 min)
- [ ] Stage all changes: `git add .`
- [ ] Commit with message (see below)
- [ ] Push: `git push -u origin refactor/web-ui-job-pipeline-cleanup`

---

## Commit Message

```
refactor(web-ui): Remove tool runner and complete job pipeline migration

BREAKING: Old execution paths (runTool, ToolSelector, detectToolType) removed.
All execution now goes through /v1/analyze endpoint with job polling.

Changes:
- Delete ToolSelector component (plugin selection via API now)
- Delete detectToolType utility (job results are uniform)
- Delete toolRunner.ts (use apiClient.analyzeImage + pollJob)
- Add JobStatusIndicator component (show queued/running/done/error)
- Add JobError component (display error messages)
- Update UploadPanel to use job pipeline
- Update ResultsPanel to remove tool-type branching
- Update VideoTracker to use job pipeline

All tests passing, type-check clean, lint clean.

Closes #146
```

---

## Rollback Plan

If something breaks during implementation:

```bash
# Abort and reset to branch start
git reset --hard HEAD~1

# Or fully reset to main
git checkout main
git branch -D refactor/web-ui-job-pipeline-cleanup
```

---

## Questions for Approval

Before I start implementing, please confirm:

1. **Plugin Selection**: Is plugin selection handled via API (e.g., dropdown with `apiClient.listPlugins()`)? Or should we keep a basic selector component?

2. **Result Rendering**: Can `ResultsPanel` just display `job.result` generically (as JSON or simple cards)? Or do you need plugin-specific renderers?

3. **Video Overlay**: Should `VideoTracker` draw its own overlays (bounding boxes, etc.), or pass `job.result` to a separate component?

4. **Testing**: Should new tests use Vitest + React Testing Library (matches current setup)?

5. **Feature Flags**: Do you want a feature flag to gradually roll out the job pipeline, or is this a full cutover?

---

## Success Metrics

After implementation:

```
✅ All tests pass: npm run test -- --run
✅ Type-check clean: npm run type-check
✅ Lint clean: npm run lint
✅ No `runTool` anywhere in code
✅ No `ToolSelector` imports
✅ No `detectToolType` usage
✅ `VideoTracker` uses job pipeline
✅ `UploadPanel` uses job pipeline
✅ Job status visible to user (queued/running/done)
✅ Errors displayed with optional retry
```

---

## Related Issues

- #145 Server job pipeline endpoint (`/v1/analyze`)
- #144 Job polling API (`/v1/jobs/{id}`)
- #143 Job status schema

---

## References

- Architecture: See `WEB-UI_ISSUE_146.md` for full before/after diagrams
- Code: See `WEB-UI_ISSUE_146.md` for exact diffs and component code
- Script: `migrate_to_job_pipeline.sh` to find references

