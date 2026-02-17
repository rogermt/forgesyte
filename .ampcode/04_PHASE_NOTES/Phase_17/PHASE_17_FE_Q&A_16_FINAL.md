Critical Questions:
MP4 Upload Issue: What specifically is "not done fully" about the MP4 upload? Is it:

The upload itself doesn't work?
The job tracking doesn't work?
The results don't display?
Something else?
Current State: The codebase currently has BOTH new Phase 17 components AND legacy Phase 10 components. Should I:

Option A: Keep existing Phase 17 components (StreamingView, VideoTracker, etc.) and just remove legacy stuff (PluginSelector, ToolSelector, ResultsPanel)?
Option B: Delete EVERYTHING in components/ and rebuild from scratch using the specs in PHASE_17_FINAL_ARCH.md?
CSS Files: The docs reference creating src/styles/globals.css, streaming.css, and debug.css. I see src/index.css exists. Should I:

Replace index.css with the new structure?
Keep index.css and add new files alongside it?
Pipeline Loading: The docs say "no hardcoded pipelines" but PipelineSelector.tsx exists. Should it:

Dynamically load pipelines from the backend API (/api/pipelines)?
Remove pipeline selection entirely and have the user specify it in the WebSocket URL?
Backend Status: The docs say backend is 12/12 complete with WebSocket /ws/video/stream. Is the backend actually deployed and accessible? I need to know this to plan frontend integration tests.

---

### 1. What’s “not done fully” about MP4 upload?

The gap is **not** “can the browser send a file”, it’s the **end‑to‑end batch job flow**:

- **Upload path is wrong / legacy**  
  - `VideoTracker` → `useVideoProcessor` → `runTool()` = Phase 10 local processing, not Phase 15/16 jobs.
- **No proper job tracking**  
  - It doesn’t consistently use `POST /v1/video/submit` + `GET /api/jobs/{id}`.
- **No canonical state model**  
  - No single, authoritative hook for: `status`, `jobId`, `progress`, `framesProcessed`, `error`.
- **Debug/Context not wired**  
  - MP4ProcessingContext + StreamDebugPanel aren’t fully wired to a real job pipeline.

So:  
**The upload itself may “kind of” work, but the proper Phase 15/16 job‑based MP4 pipeline is not implemented as a first‑class, governed flow.**

That’s what we’re fixing with `useMP4Upload` + VideoTracker + MP4ProcessingContext.

---

### 2. Current state: keep Phase 17 components or rebuild everything?

**Correct choice: Option A.**

- **Keep** existing Phase 17 components:
  - `StreamingView`, `RealtimeContext`, `useRealtime`, `CameraPreview`, overlays, debug panel, etc.
- **Remove** Phase 10 legacy:
  - `PluginSelector`, `ToolSelector`, `ResultsPanel`, manifest loading, `detectToolType`, plugin/tool types, etc.

**Do NOT** delete everything in `components/` and rebuild from scratch—that would throw away already‑aligned Phase 17 work and massively increase risk and scope.

---

### 3. CSS: index.css vs globals.css / streaming.css / debug.css

**Keep `src/index.css` as the entry point.**

- **Do this:**
  - Create `src/styles/globals.css`, `streaming.css`, `debug.css`.
  - Import them from `index.css`, e.g.:

    ```css
    @import "./styles/globals.css";
    @import "./styles/streaming.css";
    @import "./styles/debug.css";
    ```

- **Do NOT:**
  - Delete `index.css` (it’s usually wired into the bundler/entry).
  - Split entry wiring across multiple places.

So: `index.css` becomes the single import hub; the real styles live in the three new files.

---

### 4. Pipeline loading / PipelineSelector.tsx

Given your governance rule—**no hardcoded pipelines, no pipeline selection in FE**—the answer is:

- **PipelineSelector should be removed.**
- **Frontend should not:**
  - Hardcode pipeline IDs.
  - Dynamically load pipelines.
  - Let the user pick pipelines.
  - Encode pipelines into WebSocket URLs.

**Backend chooses the pipeline.**  
Frontend just:

- Opens `/ws/video/stream` for streaming.
- Calls `/v1/video/submit` for MP4 upload.

PipelineSelector is a Phase 10/early‑Phase‑17 artifact and should be deleted along with other legacy components.

---

### 5. Backend status: is `/ws/video/stream` actually live?

On paper:  
- “12/12 backend commits complete” and `/ws/video/stream` exists.

In reality:  
- You still need to verify **environment + deployment**.

So the safe assumption is:

- **Code is complete**, but you must:
  - Confirm the target environment (dev/stage/prod).
  - Manually hit:
    - `POST /v1/video/submit` with a small MP4.
    - `GET /api/jobs` and `GET /api/jobs/{id}`.
    - `ws://<host>/ws/video/stream` from a simple test client or the existing StreamingView.

Until you’ve done that, treat backend availability as **unknown**, and structure Phase 1 so that:

- MP4 upload code is correct and testable locally.
- Integration tests that depend on a live backend are clearly marked and can be toggled/pointed at the right env.

---

Absolutely, Roger — here is the **clean, authoritative “Decisions” section** you requested, fully integrated into your Phase 17 plan, plus the **updated deletion lists** that now explicitly include `PipelineSelector.tsx` and all pipeline‑related tests.

This is written exactly the way you’d include it in your migration document — crisp, governed, and unambiguous.

---

# 🔥 **Phase 17 – Decisions (Inline Section for Your Plan)**

## **Decisions (Final, Authoritative, Governance‑Aligned)**

These decisions resolve all open architectural questions and lock the direction for the Phase 17 migration.

---

### **1. MP4 Upload – What Was “Not Fully Done”?**

The MP4 upload pipeline was incomplete because:

- The frontend still used **Phase 10 local processing** (`runTool()`), not the Phase 15/16 batch job API.
- There was **no canonical hook** for job upload + polling.
- `VideoTracker` did not use the job API.
- `MP4ProcessingContext` and `StreamDebugPanel` were not wired to real job state.

**Decision:**  
MP4 upload must use the Phase 15/16 batch job API:

- `POST /v1/video/submit`
- `GET /api/jobs/{job_id}`
- `GET /api/jobs`

And must be implemented via a new hook: **`useMP4Upload`**.

---

### **2. Phase 17 Components – Keep or Rebuild?**

The codebase contains both Phase 17 and Phase 10 components.

**Decision:**  
✔ **Keep all Phase 17 components**  
❌ **Delete all Phase 10 components**

We do **not** rebuild StreamingView, RealtimeContext, overlays, or debug panels.  
We only remove legacy Phase 10 architecture.

---

### **3. CSS Structure – How to Organize?**

The plan introduces:

- `globals.css`
- `streaming.css`
- `debug.css`

**Decision:**  
✔ Keep `src/index.css` as the entry point  
✔ Add the new CSS files  
✔ Import them from `index.css`

This keeps the bundler stable and the structure clean.

---

### **4. Pipeline Loading – Should the FE Load Pipelines?**

PipelineSelector.tsx exists, but your governance rule is:

> **No pipeline IDs in the frontend. Ever.  
> Backend chooses the pipeline.**

**Decision:**  
✔ Remove PipelineSelector.tsx  
✔ Remove all pipeline‑related UI  
✔ Remove all pipeline‑related tests  
✔ Frontend never loads pipelines from `/api/pipelines`  
✔ Frontend never encodes pipelines in WebSocket URLs

Streaming uses `/ws/video/stream`.  
MP4 upload uses `/v1/video/submit`.  
Backend decides the pipeline.

---

### **5. Backend Status – Is `/ws/video/stream` Live?**

Backend is “12/12 complete” on paper, but deployment must be verified.

**Decision:**  
✔ Treat backend as complete in code  
✔ Verify environment manually before integration tests  
✔ Integration tests should be environment‑configurable

---

# 🔥 **Updated File Deletion Lists (Phase 2)**  
Now including **PipelineSelector.tsx** and all pipeline‑related tests.

---

## **Phase 2 – Commit 6: Delete Legacy Components**

### **Delete these Phase 10 components:**

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
web-ui/src/components/PipelineSelector.tsx   ← **NEW**
```

---

## **Phase 2 – Commit 6: Delete Legacy Tests**

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
web-ui/src/components/PipelineSelector.test.tsx   ← **NEW**
```

---

## **Phase 2 – Commit 7: Delete Legacy Hooks, Utils, Types**

```
web-ui/src/hooks/useManifest.ts
web-ui/src/hooks/useVideoExport.ts
web-ui/src/hooks/useManifest.test.ts
web-ui/src/hooks/useVideoExport.test.ts
web-ui/src/utils/detectToolType.ts
web-ui/src/utils/runTool.ts
web-ui/src/types/plugin.ts
```

---

# 🎯 **Roger — your Phase 17 plan is now fully updated, governed, and ready for execution.**
