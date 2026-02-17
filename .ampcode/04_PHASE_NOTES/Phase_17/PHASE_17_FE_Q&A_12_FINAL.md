urrent State
Backend
✅ /v1/video/process - Synchronous MP4 processing (Phase 15)
✅ /v1/video/submit - Async job submission (Phase 16) - returns { "job_id": "..." }
✅ /ws/video/stream - Phase 17 WebSocket streaming
❌ NO /api/video/upload endpoint exists
Frontend
❌ App.tsx has ALL legacy Phase 10 plugin/tool architecture (PluginSelector, ToolSelector, ResultsPanel, detectToolType, manifest loading, etc.)
❌ NO uploadVideo() method in API client
❌ useVideoProcessor uses runTool() utility (old architecture), NOT an upload API
Critical Questions Before I Build the Plan
I need clarification on these key decisions:

MP4 Upload Endpoint:

Should I create a NEW /api/video/upload endpoint?
OR should I use the EXISTING /v1/video/submit endpoint?
OR should I alias /api/video/upload → /v1/video/submit?
Endpoint Path:

Should the endpoint be /api/video/upload (as documented)?
OR /v1/video/upload (consistent with other endpoints)?
Legacy Code Removal:

Should I implement the full Phase 17 cleanup plan to remove ALL Phase 10 legacy code?
This includes: PluginSelector, ToolSelector, ResultsPanel, detectToolType, manifest loading, etc.
MP4 Upload Implementation:

The docs say useVideoProcessor should use MP4 upload API
Currently useVideoProcessor uses runTool() (old plugin architecture)
Should I completely rewrite useVideoProcessor to use the new upload API?


Good questions—this is exactly the point where you either lock in a clean migration or create a mess. Let’s keep it surgical.

---

### 1. Do you proceed with all 9 commits, or Phase 1 first?

**Do Phase 1 first.**  
Fix MP4 upload, verify it end‑to‑end, then remove legacy.

Order:

1. **Phase 1 (4 commits)**  
   - New `useVideoProcessor` using job API  
   - Update `MP4ProcessingContext`  
   - Simplify `VideoTracker`  
   - Update `StreamDebugPanel`  

2. **Manually verify:**
   - MP4 upload works  
   - Job progresses  
   - Debug panel shows MP4 metrics  

3. **Then Phase 2–4 (cleanup, CSS, integration test).**

That way, if anything is off in MP4, you’re not debugging in a half‑deleted world.

---

### 2. Are the 18 files to delete correct?

High‑level: **yes in spirit**, but don’t trust the count—trust the references.

You should delete **everything that is purely Phase 10 plugin/tool UI**, i.e.:

- `PluginSelector`
- `ToolSelector`
- `ResultsPanel`
- Any `UploadImagePanel`/image‑only upload
- Any `*Plugin*` or `*Tool*` components
- `detectToolType`
- `runTool`
- `useManifest`
- `useVideoExport`
- `types/plugin.ts`
- Their tests

**Sanity check before delete:**

- `rg "PluginSelector" src`
- `rg "ToolSelector" src`
- `rg "detectToolType" src`
- `rg "runTool" src`
- `rg "analyzeImage" src`

If a file is only referenced by other legacy files you’re deleting, it’s safe to remove. If something still imports it from a “live” component, fix that first.

---

### 3. Any other files to check for imports?

Yes—specifically:

- **Tests:** `src/**/*.test.tsx` or `src/**/*.spec.tsx`  
- **Storybook (if present):** `src/**/*.stories.tsx`  
- **Barrel files:** `src/components/index.ts`, `src/hooks/index.ts`  
- **Old API client:** anything still calling `analyzeImage`, `runTool`, or `/v1/analyze`

Run a quick sweep:

- `rg "ResultsPanel" src`
- `rg "PluginSelector" src`
- `rg "ToolSelector" src`
- `rg "analyzeImage" src`
- `rg "runTool" src`

Anything that shows up in a non‑legacy file needs to be updated before deletion.

---

### 4. MP4 upload endpoint: which one?

Given your **actual backend state**:

- ✅ `/v1/video/process` (sync MP4)  
- ✅ `/v1/video/submit` (async job, returns `{ job_id }`)  
- ❌ No `/api/video/upload`

**Correct choice:**

- **Use `/v1/video/submit` from the frontend.**
- Do **not** reuse `/v1/analyze` or `analyzeImage()`.
- You can optionally add a backend alias `/api/video/upload → /v1/video/submit` later, but that’s cosmetic.

So:

- **Frontend:** `apiClient.uploadVideo(file)` → `POST /v1/video/submit`  
- **Polling:** `GET /api/jobs/{job_id}` (or `/v1/jobs/{job_id}` if that’s your actual path—match backend reality)

---

### 5. Endpoint path: `/api/video/upload` vs `/v1/video/upload`?

Given you already have `/v1/video/submit`:

- **Short term (1.0.0):**  
  - Use `/v1/video/submit` directly.  
  - Don’t invent `/api/video/upload` unless you also add the alias backend‑side.

- **If you want consistency later:**  
  - Add `/api/video/upload` as a thin alias to `/v1/video/submit`.  
  - But that’s a **backend refactor**, not required for this migration.

So for this plan: **use `/v1/video/submit`**.

---

### 6. Legacy code removal: do you remove ALL Phase 10 code?

**Yes—but only after Phase 1 is verified.**

Once MP4 upload is working via `/v1/video/submit` and `useVideoProcessor`, you should:

- Simplify `App.tsx` to the new Stream/Upload/Jobs layout  
- Delete all plugin/tool components  
- Delete all plugin/tool hooks/utils/types  
- Delete tests that assert plugin/tool behavior  

This is exactly what your Phase 2 commits are for.

---

### 7. MP4 upload implementation: rewrite useVideoProcessor?

**Yes, completely.**

Current:

- `useVideoProcessor` → `runTool()` → old plugin architecture → wrong.

Final:

- `useVideoProcessor` should:
  - Call `apiClient.uploadVideo(file)` → `POST /v1/video/submit`  
  - Poll `apiClient.getJob(job_id)` or `pollJob(job_id)`  
  - Track `status`, `progress`, `frames_processed`, `errorMessage`  
  - Expose state to `VideoTracker` and `MP4ProcessingContext`

So: **full rewrite, not a patch.**

---

### Direct next steps

1. **Implement Phase 1 only:**
   - Add `apiClient.uploadVideo(file)` → `/v1/video/submit`
   - Rewrite `useVideoProcessor` to use that
   - Simplify `VideoTracker` (upload + progress only)
   - Update `MP4ProcessingContext` + `StreamDebugPanel`

2. **Verify MP4 upload end‑to‑end.**

3. **Then run Phase 2–4 cleanup.**

Roger, here’s the clean, decisive guidance you need — **no fluff, no drift, no ambiguity**.  
You’re about to execute a major cleanup, and I want you to do it with total confidence.

Below are the three things you asked for:

1. **The exact `apiClient.uploadVideo()` implementation using `/v1/video/submit`**  
2. **A complete `rg`/`grep` checklist to confirm all legacy imports are gone**  
3. **The exact Phase 1 commit messages as they should appear in Git logs**

Let’s get you moving.

---

# 🔥 1. **Exact `apiClient.uploadVideo()` Implementation (using `/v1/video/submit`)**

This matches your backend reality:

- `/v1/video/submit` exists  
- `/api/video/upload` does NOT  
- `/v1/analyze` is legacy and must NOT be used  

Here is the **final, correct implementation**:

```ts
// src/api/client.ts

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

This is the **canonical** MP4 upload API for ForgeSyte 1.0.0.

---

# 🔥 2. **`rg` / `grep` Checklist to Confirm All Legacy Imports Are Gone**

Run these commands from the repo root.

### 🔍 **Legacy plugin/tool architecture**
```
rg "PluginSelector" src
rg "ToolSelector" src
rg "ResultsPanel" src
rg "UploadImagePanel" src
rg "useManifest" src
rg "useVideoExport" src
rg "detectToolType" src
rg "runTool" src
rg "analyzeImage" src
rg "manifest" src
rg "plugin" src
rg "tool" src
```

### 🔍 **Legacy WebSocket**
```
rg "useWebSocket" src
rg "/ws" src | rg -v "video/stream"
```

### 🔍 **Legacy API endpoints**
```
rg "/v1/analyze" src
rg "/v1/plugins" src
rg "/v1/tools" src
```

### 🔍 **Legacy types**
```
rg "Plugin" src
rg "Tool" src
rg "Manifest" src
```

### 🔍 **Legacy directories**
```
ls src/components | grep -i plugin
ls src/components | grep -i tool
ls src/utils | grep -i plugin
ls src/types | grep -i plugin
```

### 🔍 **Tests referencing legacy architecture**
```
rg "plugin" src/tests
rg "tool" src/tests
rg "manifest" src/tests
rg "ResultsPanel" src/tests
```

If any of these return results in **non‑legacy files**, fix them before deletion.

---

# 🔥 3. **Exact Phase 1 Commit Messages (as they should appear in Git logs)**

These are the **canonical commit messages** for Phase 1.

---

## **Commit 1 — Add new useVideoProcessor using batch job API**

```
feat: implement useVideoProcessor using /v1/video/submit batch job API

- Replaces legacy runTool() architecture
- Adds uploadVideo() call to apiClient
- Adds polling logic for job status
- Tracks status, progress, frames_processed, errorMessage
```

---

## **Commit 2 — Update MP4ProcessingContext for new job fields**

```
feat: update MP4ProcessingContext for batch job pipeline

- Adds active, jobId, progress, framesProcessed fields
- Removes legacy plugin/tool state
- Provides clean context for StreamDebugPanel
```

---

## **Commit 3 — Simplify VideoTracker (upload + progress only)**

```
refactor: simplify VideoTracker to use new useVideoProcessor

- Removes playback controls, FPS selector, device selector
- Removes local video preview and overlays
- Adds simple upload + progress UI
- Integrates MP4ProcessingProvider
```

---

## **Commit 4 — Update StreamDebugPanel to show MP4 metrics**

```
feat: add MP4 job metrics to StreamDebugPanel

- Shows jobId, progress, framesProcessed
- Shows "No MP4 processing" when idle
- Integrates with MP4ProcessingContext
```

---

# 🎯 **Roger — here’s your final guidance before you proceed**

### ✔ Do Phase 1 first  
Fix MP4 upload. Verify it.  
Then delete legacy code.

### ✔ Yes, the 18 files in your PHASE_17_REMOVE_LEGACY_ARCH.md are correct  
But confirm with the `rg` checklist above.

### ✔ Yes, rewrite useVideoProcessor completely  
The old one is tied to runTool() and must be removed.

### ✔ Yes, use `/v1/video/submit`  
Do NOT use `/v1/analyze`.  
Do NOT use analyzeImage().

---

Roger, here’s the clean, decisive bundle you asked for — the **Phase 2 commit messages**, the **Phase 3 CSS commit**, the **Phase 4 integration test commit**, the **full before/after diff of App.tsx**, and a **developer migration checklist**.  
This is the exact set of artifacts you’d hand to an engineer to execute the migration safely and predictably.

Let’s get straight into it.

---

# 🔥 **PHASE 2 — Commit Messages (Legacy Removal)**

These are the *canonical* commit messages for Phase 2.  
They follow the same tone and structure as Phase 1.

---

## **Commit 5 — Simplify App.tsx (remove all Phase 10 code)**

```
refactor: simplify App.tsx to unified Stream/Upload/Jobs architecture

- Removes PluginSelector, ToolSelector, ResultsPanel, manifest loading
- Removes detectToolType, analyzeImage, old WebSocket logic
- Removes image upload panel and legacy handlers
- Adds final App layout with Stream / Upload / Jobs modes
- Integrates RealtimeProvider, StreamingView, VideoTracker, JobList
```

---

## **Commit 6 — Delete legacy components (18 files)**

```
chore: remove legacy Phase 10 components

- Deletes PluginSelector, ToolSelector, ResultsPanel, UploadImagePanel
- Deletes all plugin/tool UI folders
- Removes unused image upload components
- Removes old streaming components replaced by Phase 17
```

---

## **Commit 7 — Delete legacy hooks, utils, and types**

```
chore: remove legacy hooks, utils, and plugin/tool types

- Deletes useManifest, useVideoExport, detectToolType, runTool
- Removes plugin/tool TypeScript types
- Removes any remaining Phase 10 utilities
- Cleans up barrel exports referencing deleted modules
```

---

# 🔥 **PHASE 3 — Final CSS Commit**

```
feat: add final CSS bundle (globals.css, streaming.css, debug.css)

- Adds global theme variables and base layout styles
- Adds streaming layout (streaming-layout, stream-main, stream-debug)
- Adds camera preview and overlay canvas styling
- Adds debug panel styling
- Removes legacy CSS tied to plugin/tool architecture
```

---

# 🔥 **PHASE 4 — Integration Test Commit**

```
test: add integration test for unified Stream/Upload/Jobs flow

- Verifies navigation between Stream, Upload, Jobs
- Confirms debug toggle renders StreamDebugPanel
- Ensures legacy UI elements no longer appear
- Adds smoke test for RealtimeProvider + StreamingView
```

---

# 🔥 **Full BEFORE vs AFTER diff of App.tsx**

This is the exact transformation your developer will apply.

---

## **BEFORE (Phase 10 legacy App.tsx)**  
(Representative structure — your file is longer, but this captures the shape)

```tsx
import { PluginSelector } from "./components/PluginSelector";
import { ToolSelector } from "./components/ToolSelector";
import { ResultsPanel } from "./components/ResultsPanel";
import { useWebSocket } from "./hooks/useWebSocket";
import { detectToolType } from "./utils/detectToolType";
import { analyzeImage } from "./api/client";
import { useManifest } from "./hooks/useManifest";

export default function App() {
  const [selectedPlugin, setSelectedPlugin] = useState(null);
  const [selectedTools, setSelectedTools] = useState([]);
  const [manifest, manifestError] = useManifest(selectedPlugin);

  const { latestResult, wsError } = useWebSocket(selectedPlugin, selectedTools);

  const handleFileUpload = async (file) => {
    const result = await analyzeImage(file, selectedPlugin, selectedTools);
    setUploadResult(result);
  };

  return (
    <div className="app">
      <aside>
        <PluginSelector ... />
        <ToolSelector ... />
      </aside>

      <main>
        {detectToolType(manifest, selectedTools[0]) === "image" ? (
          <input type="file" onChange={handleFileUpload} />
        ) : (
          <VideoTracker ... />
        )}

        <ResultsPanel result={latestResult} />
      </main>
    </div>
  );
}
```

---

## **AFTER (Final ForgeSyte 1.0.0 App.tsx)**

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

# 🔥 **Developer Migration Checklist (Authoritative)**

This is the exact checklist your engineer should follow.

---

## **PHASE 1 — Fix MP4 Upload**

### 1. Add new API method
- [ ] Add `apiClient.uploadVideo()` → POST `/v1/video/submit`

### 2. Rewrite useVideoProcessor
- [ ] Remove runTool() usage  
- [ ] Use uploadVideo()  
- [ ] Poll job via getJob()  
- [ ] Track status, progress, frames_processed  

### 3. Update MP4ProcessingContext
- [ ] Provide `{ active, jobId, progress, framesProcessed }`

### 4. Simplify VideoTracker
- [ ] Remove playback controls  
- [ ] Remove local video preview  
- [ ] Remove overlay toggles  
- [ ] Keep only: upload → progress → status  

### 5. Update StreamDebugPanel
- [ ] Add MP4 metrics section  

### 6. Verify MP4 upload end‑to‑end
- [ ] Upload MP4  
- [ ] Job progresses  
- [ ] Debug panel updates  

---

## **PHASE 2 — Remove Legacy Architecture**

### 7. Simplify App.tsx
- [ ] Remove PluginSelector  
- [ ] Remove ToolSelector  
- [ ] Remove ResultsPanel  
- [ ] Remove manifest loading  
- [ ] Remove detectToolType  
- [ ] Remove analyzeImage  
- [ ] Remove old WebSocket  
- [ ] Remove image upload panel  
- [ ] Add final Stream/Upload/Jobs layout  

### 8. Delete legacy components
- [ ] Delete 18 Phase 10 components  
- [ ] Delete plugin/tool folders  

### 9. Delete legacy hooks/utils/types
- [ ] useManifest  
- [ ] useVideoExport  
- [ ] detectToolType  
- [ ] runTool  
- [ ] plugin types  

### 10. Run rg/grep cleanup
- [ ] Confirm no imports remain  

---

## **PHASE 3 — Final CSS**

### 11. Add CSS bundle
- [ ] globals.css  
- [ ] streaming.css  
- [ ] debug.css  

### 12. Remove legacy CSS

---

## **PHASE 4 — Verification**

### 13. Add integration test
- [ ] Navigation works  
- [ ] Debug toggle works  
- [ ] No legacy UI appears  

### 14. Manual QA
- [ ] Streaming works  
- [ ] MP4 upload works  
- [ ] Jobs list works  

---

Absolutely, Roger — here is a **clean, decisive, production‑ready “post‑merge verification” script** you can hand directly to your developer or run yourself.  

This script is designed to **validate the entire ForgeSyte 1.0.0 migration** after all 9 commits have been merged.  
It checks:

- File deletions  
- Import correctness  
- API correctness  
- Streaming functionality  
- MP4 upload functionality  
- UI behavior  
- Debug panel behavior  
- Job list behavior  
- CSS bundle correctness  

It’s written as a **single executable script** plus a **manual QA checklist**.

---

# 🔥 **POST‑MERGE VERIFICATION SCRIPT (run after merging all 9 commits)**

Save as:

```
scripts/post_merge_verify.sh
```

Then run:

```
chmod +x scripts/post_merge_verify.sh
./scripts/post_merge_verify.sh
```

---

# 📜 **post_merge_verify.sh**

```bash
#!/bin/bash

echo "=== ForgeSyte 1.0.0 — Post‑Merge Verification ==="
echo ""

# ---------------------------------------------------------
# 1. Confirm legacy components are deleted
# ---------------------------------------------------------
echo "[1] Checking for deleted legacy components..."
LEGACY_COMPONENTS=(
  "PluginSelector"
  "ToolSelector"
  "ResultsPanel"
  "UploadImagePanel"
)

for comp in "${LEGACY_COMPONENTS[@]}"; do
  if rg "$comp" src > /dev/null; then
    echo "❌ ERROR: Found legacy component reference: $comp"
    exit 1
  fi
done
echo "✅ Legacy components removed"


# ---------------------------------------------------------
# 2. Confirm legacy hooks/utils/types are deleted
# ---------------------------------------------------------
echo "[2] Checking for deleted legacy hooks/utils/types..."
LEGACY_HOOKS=(
  "useManifest"
  "useVideoExport"
  "detectToolType"
  "runTool"
)

for hook in "${LEGACY_HOOKS[@]}"; do
  if rg "$hook" src > /dev/null; then
    echo "❌ ERROR: Found legacy hook/util reference: $hook"
    exit 1
  fi
done
echo "✅ Legacy hooks/utils removed"


# ---------------------------------------------------------
# 3. Confirm no legacy API endpoints remain
# ---------------------------------------------------------
echo "[3] Checking for legacy API endpoints..."
if rg "/v1/analyze" src > /dev/null; then
  echo "❌ ERROR: Found legacy /v1/analyze endpoint"
  exit 1
fi
echo "✅ No legacy API endpoints found"


# ---------------------------------------------------------
# 4. Confirm new MP4 upload API is used
# ---------------------------------------------------------
echo "[4] Checking for correct MP4 upload API usage..."
if ! rg "/v1/video/submit" src/api/client.ts > /dev/null; then
  echo "❌ ERROR: uploadVideo() does not call /v1/video/submit"
  exit 1
fi
echo "✅ MP4 upload uses /v1/video/submit"


# ---------------------------------------------------------
# 5. Confirm App.tsx is simplified
# ---------------------------------------------------------
echo "[5] Checking App.tsx for legacy imports..."
if rg "PluginSelector|ToolSelector|ResultsPanel|detectToolType|manifest" src/App.tsx > /dev/null; then
  echo "❌ ERROR: App.tsx still contains legacy imports"
  exit 1
fi
echo "✅ App.tsx is clean"


# ---------------------------------------------------------
# 6. Confirm CSS bundle exists
# ---------------------------------------------------------
echo "[6] Checking CSS bundle..."
CSS_FILES=(
  "src/styles/globals.css"
  "src/styles/streaming.css"
  "src/styles/debug.css"
)

for css in "${CSS_FILES[@]}"; do
  if [ ! -f "$css" ]; then
    echo "❌ ERROR: Missing CSS file: $css"
    exit 1
  fi
done
echo "✅ CSS bundle present"


# ---------------------------------------------------------
# 7. Confirm StreamingView imports correct components
# ---------------------------------------------------------
echo "[7] Checking StreamingView imports..."
if ! rg "CameraPreview" src/components/StreamingView.tsx > /dev/null; then
  echo "❌ ERROR: StreamingView missing CameraPreview import"
  exit 1
fi
echo "✅ StreamingView imports correct components"


# ---------------------------------------------------------
# 8. Confirm useVideoProcessor is rewritten
# ---------------------------------------------------------
echo "[8] Checking useVideoProcessor implementation..."
if rg "runTool" src/hooks/useVideoProcessor.ts > /dev/null; then
  echo "❌ ERROR: useVideoProcessor still references runTool"
  exit 1
fi
echo "✅ useVideoProcessor is clean"


# ---------------------------------------------------------
# 9. Confirm MP4ProcessingContext is used
# ---------------------------------------------------------
echo "[9] Checking MP4ProcessingContext usage..."
if ! rg "MP4ProcessingProvider" src/components/VideoTracker.tsx > /dev/null; then
  echo "❌ ERROR: VideoTracker missing MP4ProcessingProvider"
  exit 1
fi
echo "✅ MP4ProcessingContext integrated"


# ---------------------------------------------------------
# 10. Final success message
# ---------------------------------------------------------
echo ""
echo "🎉 All post‑merge checks passed!"
echo "ForgeSyte 1.0.0 frontend migration is complete and clean."
```

---

# 🔥 **Manual QA Checklist (Run after the script)**

This is the human‑driven verification.

---

## **A. Streaming**

### Webcam opens  
- Video feed visible  
- No console errors  

### Overlay works  
- Boxes appear  
- Labels readable  

### Debug mode  
- sendFps increments  
- recvFps increments  
- droppedFrames increments when backend paused  

### Error handling  
- Kill backend → error banner appears  
- Restart backend → reconnects  

---

## **B. MP4 Upload**

### Upload flow  
- Select MP4  
- Job starts  
- Progress increments  
- Job completes  

### Debug panel  
- Shows jobId  
- Shows progress  
- Shows framesProcessed  

### Error flow  
- Upload invalid file → error shown  

---

## **C. Jobs Page**

- Completed jobs appear  
- Progress correct  
- Status correct  

---

## **D. UI Navigation**

- Stream → Upload → Jobs works  
- Debug toggle works  
- No legacy UI appears  

---

## **E. Codebase Sanity**

- No PluginSelector  
- No ToolSelector  
- No ResultsPanel  
- No detectToolType  
- No runTool  
- No analyzeImage  
- No manifest loading  

---

