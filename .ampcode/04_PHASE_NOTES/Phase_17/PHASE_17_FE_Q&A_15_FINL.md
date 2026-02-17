 What I Need Clarified Before We Start
I have one question that I'm not 90% confident about:

Q1: How should useVideoProcessor work for MP4 batch jobs?
Current behavior: useVideoProcessor processes frames locally in the browser using runTool().

Desired behavior (Phase 17): useVideoProcessor should:

Upload MP4 to backend via POST /v1/video/submit
Poll job status via GET /v1/video/status/{job_id}
Display progress
OR should we create a NEW hook called useMP4Upload for batch jobs and keep useVideoProcessor as-is for local frame processing?

✅ Everything Else is Correct
Your plan correctly identifies:

All 18 legacy components to delete
All 7 legacy hooks/utils to delete
All 13 legacy tests to delete
App.tsx simplification approach
CSS structure
TDD workflow
Test log strategy
🎯 My Recommendation
Answer Q1 above, and I'll start implementation immediately.

Option A: Modify useVideoProcessor to support both local processing AND MP4 batch upload
Option B: Create new useMP4Upload hook, keep useVideoProcessor unchanged

Which do you prefer?

Roger — this is the *one* question that absolutely must be answered correctly before you begin implementation, because it determines the shape of the entire MP4 upload architecture.

Let’s cut straight to the truth.

---

# ⭐ **Final Answer: Option B — Create a new hook `useMP4Upload` and keep `useVideoProcessor` unchanged.**

This is the only option that is:

- **Architecturally correct**
- **Governance‑aligned**
- **Future‑proof**
- **Non‑breaking**
- **Consistent with Phase 17**
- **Consistent with your “no pipeline IDs in FE” rule**
- **Consistent with your long‑term product direction**

Let me explain why with absolute clarity.

---

# 🧠 **Why NOT modify `useVideoProcessor`?**

Because `useVideoProcessor` was originally designed for:

- Local frame processing  
- Local playback  
- Local overlays  
- Local stepping through frames  
- Local FPS control  
- Local device selection  
- Local canvas rendering  

It is a **Phase 10 artifact**.

Even if you strip out `runTool()`, the name and semantics imply:

> “Process video frames locally in the browser.”

That is **not** what MP4 batch jobs do.

Batch jobs:

- Upload the entire MP4  
- Run server‑side  
- Produce no local frames  
- Produce no local overlays  
- Produce no local playback  
- Produce no local stepping  
- Produce no local FPS  
- Produce no local canvas  

These are **completely different domains**.

If you merge them into one hook, you create:

- Confusion  
- API ambiguity  
- Hidden coupling  
- Future migration pain  
- A hook that does two unrelated things  
- A violation of your governance rule:  
  **“Every workflow must be deterministic and explicit.”**

---

# 🧱 **Why `useMP4Upload` is the correct solution**

Because MP4 batch jobs are:

- A different workflow  
- A different API  
- A different lifecycle  
- A different UI  
- A different state machine  
- A different user story  

And they deserve their own hook.

### `useMP4Upload` should:

- Upload MP4  
- Poll job  
- Track progress  
- Track framesProcessed  
- Track error  
- Expose status  
- Expose jobId  
- Expose cancel()  

### `useVideoProcessor` should remain:

- A Phase 10 local video processor  
- Eventually deprecated  
- Eventually removed in Phase 18 or 19  

This separation keeps your architecture clean and future‑proof.

---

# 🧩 **How this fits into your Phase 17 plan**

Your Phase 17 plan already assumes:

- MP4 upload is a **batch job**
- Streaming is **real‑time**
- Local video processing is **legacy**

So the correct mapping is:

| Workflow | Hook | Status |
|----------|------|--------|
| Real‑time streaming | `useRealtime` | Phase 17 |
| MP4 batch jobs | **`useMP4Upload`** | Phase 17 (new) |
| Local video processing | `useVideoProcessor` | Legacy (Phase 10) |

This is clean.  
This is explicit.  
This is governed.  
This is future‑proof.

---

# 🧭 **What this means for your implementation**

### ✔ Create a new hook:

```
src/hooks/useMP4Upload.ts
```

### ✔ Move all batch job logic into it:

- uploadVideo()
- pollJob()
- state machine
- progress
- framesProcessed
- error
- cancel()

### ✔ Update VideoTracker to use `useMP4Upload`

### ✔ Leave `useVideoProcessor` untouched  
(It will be deleted in Phase 18 when local video processing is removed.)

### ✔ MP4ProcessingContext should wrap `useMP4Upload` state

### ✔ StreamDebugPanel should read from MP4ProcessingContext

---

# 🎯 **Final Decision (Copy/Paste into your plan)**

```
We will NOT modify useVideoProcessor.

We will create a new hook called useMP4Upload for Phase 17 batch job processing.

useVideoProcessor remains a legacy Phase 10 hook and will be removed in a later phase.

VideoTracker will be updated to use useMP4Upload.

MP4ProcessingContext will wrap useMP4Upload state.

This keeps the architecture clean, explicit, and aligned with governance rules.
```

---

Roger, here is the complete, corrected, governance‑aligned package you asked for — **fully updated to reflect the decision to create `useMP4Upload` instead of modifying `useVideoProcessor`**, and fully aligned with your Phase‑17 architecture and your strict rule:

> **No pipeline IDs, no plugin IDs, no tool IDs in the frontend. Ever.**

Everything below is clean, explicit, deterministic, and future‑proof.

---

# 🔥 **1. Full `useMP4Upload` Implementation (Final, Correct, Pipeline‑Agnostic)**

This hook is:

- 100% Phase‑17 aligned  
- 100% pipeline‑agnostic  
- 100% plugin‑free  
- 100% deterministic  
- 100% backend‑driven  

It handles:

- Upload  
- Polling  
- Progress  
- Frames processed  
- Errors  
- Cancellation  

```ts
// src/hooks/useMP4Upload.ts
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

# 🔥 **2. Updated `VideoTracker` Using `useMP4Upload` (Final, Correct)**

This version:

- Uses `useMP4Upload`
- Has **no pipelineId**
- Has **no plugin/tool logic**
- Has **no playback controls**
- Has **no local video processing**
- Is Phase‑17 aligned
- Is minimal and deterministic

```tsx
// src/components/VideoTracker.tsx
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

# 🔥 **3. Updated Phase 1 Diffs (Reflecting `useMP4Upload`)**

### Commit 1 — Add `uploadVideo()` to API client  
*(unchanged from earlier)*

### Commit 2 — Add new hook `useMP4Upload`

```diff
+ src/hooks/useMP4Upload.ts
+ (full implementation above)
```

### Commit 3 — Update `VideoTracker` to use `useMP4Upload`

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

### Commit 4 — Update MP4ProcessingContext + StreamDebugPanel

```diff
+ status
+ error
+ framesProcessed
+ jobId
+ progress
```

---

# 🔥 **4. Updated Migration Plan (Phase 1–4, Corrected)**

Here is the corrected, final, authoritative migration plan.

---

## **PHASE 1 — Fix MP4 Upload (4 commits)**

### **Commit 1 — Add `apiClient.uploadVideo()`**
- POST `/v1/video/submit`
- No pipelineId
- No plugin/tool logic

### **Commit 2 — Add new hook `useMP4Upload`**
- Upload MP4
- Poll job
- Track progress
- Track framesProcessed
- Track error
- Cancel support

### **Commit 3 — Update `VideoTracker`**
- Replace `useVideoProcessor` with `useMP4Upload`
- Remove playback controls
- Remove local video processing
- Remove pipelineId
- Minimal upload UI

### **Commit 4 — Update MP4ProcessingContext + StreamDebugPanel**
- Add status, error, framesProcessed
- Display MP4 metrics in debug panel

---

## **PHASE 2 — Remove Legacy Architecture (3 commits)**

### **Commit 5 — Simplify App.tsx**
- Remove PluginSelector, ToolSelector, ResultsPanel
- Remove manifest loading
- Remove detectToolType
- Remove old WebSocket
- Add Stream / Upload / Jobs layout

### **Commit 6 — Delete legacy components**
- 18 components removed

### **Commit 7 — Delete legacy hooks/utils/types**
- 7 files removed

---

## **PHASE 3 — Final CSS (1 commit)**

### **Commit 8 — Add globals.css, streaming.css, debug.css**

---

## **PHASE 4 — Integration Test (1 commit)**

### **Commit 9 — Add App integration test**
- Navigation
- Debug toggle
- Stream mode
- Upload mode
- Jobs mode
- No legacy UI

---

# Roger — this is now the **final, correct, governed, Phase‑17‑aligned implementation plan**.

