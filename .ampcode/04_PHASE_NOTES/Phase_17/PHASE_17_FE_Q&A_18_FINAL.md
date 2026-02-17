Phase 17 Status Summary
Backend: ✅ COMPLETE (12/12 commits)
WebSocket endpoint: /ws/video/stream ✅
Session Manager ✅
Frame Validator ✅
Pipeline Integration ✅
Backpressure ✅
Error Handling ✅
Logging + Metrics ✅
Frontend: 🔄 PARTIAL - Legacy Cleanup Needed
What's DONE (Phase 17 components exist):

✅ StreamingView.tsx
✅ VideoTracker.tsx
✅ CameraPreview.tsx
✅ RealtimeStreamingOverlay.tsx
✅ RealtimeErrorBanner.tsx
✅ StreamDebugPanel.tsx
✅ useRealtime.ts + RealtimeContext.tsx
✅ MP4ProcessingContext.tsx
✅ PipelineSelector.tsx
What REMAINS (Legacy Phase 10 architecture to remove):

❌ PluginSelector.tsx + test
❌ ToolSelector.tsx + test
❌ ResultsPanel.tsx + tests
❌ detectToolType.ts (not found in hooks, may exist elsewhere)
❌ Old useWebSocket.ts (needs verification if it's the Phase 17 version)
❌ useManifest.ts + test
❌ PluginInspector.tsx
❌ Legacy upload panels
❌ Phase 10 sidebar layout CSS
Key Issue:
The documentation says Phase 17 is 100% complete, but legacy Phase 10 components still exist in the codebase. This means:

Phase 17 components are built ✅
Legacy cleanup was NOT done ❌
App.tsx may still reference legacy components ❓
What You Asked For:
You want to:

Remove old Phase 10 architecture ✅
Ensure MP4 upload is fully working ✅
Build a plan to implement the changes ✅
Next Steps - I Need to Ask You Questions:
Should I verify the current App.tsx to see which components it's using? (This will tell us if we need to refactor App.tsx to use only Phase 17 components)

Should I check if the existing useWebSocket.ts is the Phase 17 version or the old legacy version?

Do you want me to create a detailed TDD plan for the legacy cleanup? (Following the Phase 17 TDD workflow: write tests first, verify RED, implement, verify GREEN)

Should I verify the MP4 upload flow is working end-to-end before we start cleanup?

Which of these should I tackle first?





Roger — here’s the truth, clean and decisive, so you can stop second‑guessing and move forward with confidence.

You **do NOT** need to roll back Phase 17.  
You **do NOT** need to start from scratch.  
You **DO** need to finish the MP4 upload and remove the Phase 10 leftovers.

Your dev is *close* — the backend is fully Phase 17, the frontend is *partially* Phase 17, and the only thing missing is:

- **A correct MP4 upload pipeline**
- **Removal of Phase 10 architecture**
- **Ensuring App.tsx uses ONLY Phase 17 components**

Let me answer your questions in the exact order that will unblock your dev.

---

# ✅ **1. Should you roll back MP4 upload or Phase 17 entirely?**

### **No. Absolutely not.**

Rolling back would:

- Throw away completed Phase 17 backend work  
- Throw away completed Phase 17 frontend components  
- Force you to rebuild everything again  
- Waste weeks of work  

The correct move is:

### **Keep Phase 17.  
Finish MP4 upload.  
Delete Phase 10.**

This is the fastest, safest, cleanest path.

---

# ✅ **2. What should you do RIGHT NOW to help the dev finish MP4 upload?**

Here is the exact order of operations:

---

## **Step 1 — Verify App.tsx is using Phase 17 components only**

You must confirm:

- `StreamingView` is used for streaming  
- `VideoTracker` is used for MP4 upload  
- `JobList` is used for job history  
- `RealtimeProvider` wraps streaming  
- `Debug` toggle exists  
- No PluginSelector  
- No ToolSelector  
- No ResultsPanel  
- No manifest loading  
- No detectToolType  

If App.tsx still references ANY Phase 10 component → fix that first.

---

## **Step 2 — Verify useWebSocket.ts**

You must check:

- Does it use `/ws/video/stream`?  
- Does it handle binary JPEG frames?  
- Does it decode detection metadata?  
- Does it match the Phase 17 backend protocol?  

If yes → keep it.  
If no → replace it with the Phase 17 version.

---

## **Step 3 — Implement MP4 upload correctly**

Your dev must:

### ❌ NOT use `useVideoProcessor`  
(it’s Phase 10 local processing)

### ✔ Use the new hook `useMP4Upload`  
(upload → poll → progress → complete)

### ✔ Wire it into `VideoTracker`  
(no playback controls, no FPS, no overlays)

### ✔ Wire it into `MP4ProcessingContext`  
(status, jobId, progress, framesProcessed, error)

### ✔ Wire it into `StreamDebugPanel`  
(MP4 metrics section)

This is the missing piece.

---

## **Step 4 — Delete Phase 10 architecture**

You must delete:

- PluginSelector  
- ToolSelector  
- ResultsPanel  
- detectToolType  
- useManifest  
- useVideoExport  
- useWebSocket (if legacy)  
- All Phase 10 overlays  
- All Phase 10 tests  
- All Phase 10 CSS  

This is cleanup, not reconstruction.

---

# ✅ **3. Should I verify App.tsx?**

### **Yes — this is the FIRST thing you should do.**

App.tsx is the root of truth.  
If it still references Phase 10 components, the entire app is in hybrid mode.

---

# ✅ **4. Should I check useWebSocket.ts?**

### **Yes — this is the SECOND thing you should do.**

If it’s the Phase 10 version, streaming will break.  
If it’s the Phase 17 version, streaming is already correct.

---

# ✅ **5. Should I create a TDD plan for legacy cleanup?**

### **Yes — but AFTER MP4 upload is working.**

The correct order is:

1. Fix MP4 upload  
2. Verify App.tsx  
3. Verify useWebSocket  
4. Delete legacy components  
5. Delete legacy tests  
6. Add integration tests  
7. Add CSS  
8. Final verification  

---

# ✅ **6. Should I verify MP4 upload end‑to‑end before cleanup?**

### **Yes — this is the THIRD thing you should do.**

You must confirm:

- Upload works  
- Job is created  
- Progress increments  
- Job completes  
- Debug panel updates  

If MP4 upload is broken, cleanup will make debugging harder.

---

# 🎯 **What should you tackle first?**

Here is the correct order:

---

# 🔥 **1. Verify App.tsx uses ONLY Phase 17 components**  
(If not, fix it immediately)

# 🔥 **2. Verify useWebSocket.ts is Phase 17**  
(If not, replace it)

# 🔥 **3. Implement MP4 upload using useMP4Upload**  
(This is the missing piece)

# 🔥 **4. Delete Phase 10 architecture**  
(Once MP4 upload + streaming are stable)

---

Here’s a tight, battle-ready bundle you can drop straight into your repo / Notion for the dev.

---

### Phase 17 Rescue Plan – Step‑by‑step for your dev

**Goal:** Keep all Phase 17 work, finish MP4 upload, and remove Phase 10 without chaos.

1. **Lock the architecture**
   - **Keep:** `App.tsx`, `StreamingView.tsx`, `VideoTracker.tsx`, `RealtimeContext.tsx`, `useRealtime.ts`, `MP4ProcessingContext.tsx`, `CameraPreview.tsx`, `RealtimeStreamingOverlay.tsx`, `RealtimeErrorBanner.tsx`, `StreamDebugPanel.tsx`, `JobList.tsx`.
   - **Treat as legacy:** `PluginSelector`, `ToolSelector`, `ResultsPanel`, `useManifest`, `useVideoProcessor`, `runTool`, old `useWebSocket`, all Phase 10 overlays and sliders.

2. **Fix the root: App.tsx**
   - Ensure App.tsx uses **only** Phase 17 components (checklist below).
   - No plugin/tool/manifest logic anywhere.

3. **Verify streaming path**
   - Confirm `useWebSocket.ts` is Phase 17 (checklist below).
   - Confirm `StreamingView` works with `/ws/video/stream`.

4. **Implement MP4 upload properly**
   - Add `useMP4Upload` hook (upload → poll → progress → error).
   - Wire `VideoTracker` to `useMP4Upload`.
   - Wire `MP4ProcessingContext` + `StreamDebugPanel` to `useMP4Upload` state.
   - Run the MP4 end‑to‑end test script (below).

5. **Delete Phase 10**
   - Remove all legacy components, hooks, utils, types, tests.
   - Run full test suite + lint + typecheck.

6. **Final integration pass**
   - Manually test: Stream, Upload, Jobs, Debug.
   - Confirm no references to plugins, tools, manifests, or pipeline IDs.

---

### 🔥 What to check in App.tsx (diff checklist)

Open `App.tsx` and verify:

**Must NOT exist:**

- **Imports:**
  - `PluginSelector`
  - `ToolSelector`
  - `ResultsPanel`
  - `useManifest`
  - `detectToolType`
  - `runTool`
  - `PluginInspector`
  - Any `plugin`/`tool` types or manifests

- **State:**
  - `selectedPlugin`
  - `selectedTools`
  - `manifest`, `manifestError`, `manifestLoading`
  - `streamEnabled`
  - `uploadResult`, `selectedJob` (if tied to Phase 10 UI)

- **JSX:**
  - Any `<PluginSelector ... />`
  - Any `<ToolSelector ... />`
  - Any `<ResultsPanel ... />`
  - Any manifest loading spinners
  - Any “plugin” or “tool” sidebars
  - Any image upload panel from Phase 10

**Must exist:**

- **Imports:**
  - `StreamingView`
  - `VideoTracker`
  - `JobList`
  - `RealtimeProvider` (or equivalent)
  - React `useState`

- **State:**
  - `viewMode: "stream" | "upload" | "jobs"`
  - `debug: boolean`

- **JSX layout:**
  - Header with:
    - App name (e.g., “ForgeSyte”)
    - Buttons: `Stream`, `Upload`, `Jobs`
    - Debug checkbox
  - Conditional rendering:
    - `viewMode === "stream"` → `<RealtimeProvider><StreamingView /></RealtimeProvider>`
    - `viewMode === "upload"` → `<VideoTracker />`
    - `viewMode === "jobs"` → `<JobList />`

If anything from the “Must NOT exist” list is present → remove it.

---

### 🔥 How to verify useWebSocket.ts is Phase 17

Open `useWebSocket.ts` and check:

**Must be true for Phase 17:**

- **Endpoint:**
  - Uses `/ws/video/stream` (not `/v1/stream`, not `/ws` generic).
- **Binary frames:**
  - WebSocket is opened with `binaryType = "arraybuffer"` or similar.
  - Incoming messages are handled as binary (ArrayBuffer / Blob), not just JSON with base64 images.
- **Message structure:**
  - Decodes detection metadata from a structured message (e.g., JSON header + JPEG payload, or protobuf, depending on your backend spec).
- **Error handling:**
  - Handles disconnects, retries, and error states in a way that matches Phase 17 docs.
- **Integration:**
  - Feeds into `RealtimeContext` / `useRealtime` (not into old `RealtimeOverlay` or Phase 10 state).

**Red flags (legacy):**

- Uses `/v1/stream` or `/v1/ws` or any non‑Phase‑17 URL.
- Expects JSON messages with `image_base64` fields.
- References plugin/tool IDs or manifests.
- Feeds into `RealtimeOverlay.tsx` instead of `RealtimeStreamingOverlay.tsx`.

If you see any red flags → treat it as Phase 10 and replace it with the Phase 17 version.

---

### 🔥 MP4 Upload End‑to‑End Test Script

Run this **after** `useMP4Upload` + `VideoTracker` are wired.

1. **Preconditions**
   - Backend is running with:
     - `POST /v1/video/submit`
     - `GET /api/jobs`
     - `GET /api/jobs/{id}`
   - Frontend is running with:
     - `VideoTracker` using `useMP4Upload`
     - `MP4ProcessingContext` wired
     - `StreamDebugPanel` showing MP4 metrics

2. **Test 1 – Basic upload**
   - Open app.
   - Switch to **Upload** mode.
   - Select a small MP4 file.
   - Expect:
     - Status transitions: `idle → uploading → processing → completed`.
     - No console errors.
   - If it stays on `uploading` or `processing` forever → check polling + backend.

3. **Test 2 – Job creation**
   - After upload, check network tab:
     - `POST /v1/video/submit` returns `{ job_id: "..." }`.
     - `GET /api/jobs/{job_id}` is called repeatedly.
   - Confirm `job_id` in responses matches the one stored in state.

4. **Test 3 – Progress + framesProcessed**
   - While job is running:
     - `progress` should increase from 0 → 100.
     - `frames_processed` should increase (if backend supports it).
   - Confirm `StreamDebugPanel` shows:
     - MP4 job ID
     - Status
     - Progress
     - Frames processed

5. **Test 4 – Error handling**
   - Upload a deliberately bad file (e.g., rename a `.txt` to `.mp4`).
   - Expect:
     - Job transitions to `error`.
     - Error message displayed in `VideoTracker`.
     - Error visible in debug panel.

6. **Test 5 – Jobs view**
   - Switch to **Jobs** mode.
   - Confirm:
     - The completed job appears in `JobList`.
     - Status matches backend.

7. **Test 6 – No pipeline/tool leakage**
   - Search the codebase for:
     - `pipelineId`
     - `plugin`
     - `tool`
     - `detectToolType`
   - Confirm none of these are used in the MP4 upload path.

If all of these pass, MP4 upload is **truly** done, not just “kind of working”.

---
Here you go, Roger — a **clean, actionable GitHub Issue Checklist** your dev can follow step‑by‑step to rescue Phase 17, finish MP4 upload, and remove all Phase 10 legacy code.

This is written exactly in GitHub‑issue style: clear, atomic, and impossible to misinterpret.

---

# ✅ **GitHub Issue: Phase 17 Rescue & MP4 Upload Completion Checklist**

**Goal:**  
Stabilize Phase 17, complete MP4 upload, and remove all Phase 10 legacy architecture.

---

# **📌 Phase 1 — Verify Root Architecture (App.tsx)**

### **☑️ 1.1 Remove all Phase 10 imports**
- [ ] `PluginSelector`
- [ ] `ToolSelector`
- [ ] `ResultsPanel`
- [ ] `useManifest`
- [ ] `detectToolType`
- [ ] `runTool`
- [ ] `PluginInspector`
- [ ] Any `plugin` or `tool` types

### **☑️ 1.2 Remove all Phase 10 state**
- [ ] `selectedPlugin`
- [ ] `selectedTools`
- [ ] `manifest`, `manifestLoading`, `manifestError`
- [ ] `streamEnabled`
- [ ] `uploadResult`
- [ ] `selectedJob`

### **☑️ 1.3 Remove all Phase 10 JSX**
- [ ] `<PluginSelector />`
- [ ] `<ToolSelector />`
- [ ] `<ResultsPanel />`
- [ ] Manifest loading UI
- [ ] Phase 10 sidebar layout
- [ ] Phase 10 image upload panel

### **☑️ 1.4 Ensure App.tsx uses ONLY Phase 17 components**
- [ ] `<StreamingView />`
- [ ] `<VideoTracker />`
- [ ] `<JobList />`
- [ ] `<RealtimeProvider />`
- [ ] Debug toggle
- [ ] Navigation: Stream / Upload / Jobs

---

# **📌 Phase 2 — Verify useWebSocket.ts is Phase 17**

### **☑️ 2.1 Endpoint must be correct**
- [ ] Uses `/ws/video/stream`
- [ ] NOT `/v1/stream`
- [ ] NOT `/ws` generic

### **☑️ 2.2 Binary streaming must be enabled**
- [ ] `ws.binaryType = "arraybuffer"` or `"blob"`

### **☑️ 2.3 Message format must be Phase 17**
- [ ] Handles binary JPEG frames
- [ ] Handles detection metadata
- [ ] No base64 images
- [ ] No JSON frames from Phase 10

### **☑️ 2.4 Integration must be Phase 17**
- [ ] Feeds into `useRealtime`
- [ ] Feeds into `RealtimeContext`
- [ ] NOT into `RealtimeOverlay.tsx` (Phase 10)

If any item fails → replace with Phase 17 version.

---

# **📌 Phase 3 — Implement MP4 Upload Correctly**

### **☑️ 3.1 Add new hook `useMP4Upload`**
- [ ] Upload MP4 via `POST /v1/video/submit`
- [ ] Poll job via `GET /api/jobs/{id}`
- [ ] Track:
  - [ ] `status`
  - [ ] `jobId`
  - [ ] `progress`
  - [ ] `framesProcessed`
  - [ ] `errorMessage`
- [ ] Support `cancel()`

### **☑️ 3.2 Update VideoTracker**
- [ ] Replace `useVideoProcessor` with `useMP4Upload`
- [ ] Remove:
  - [ ] Playback controls
  - [ ] FPS slider
  - [ ] Device selector
  - [ ] Overlays
  - [ ] Local video processing
- [ ] Show:
  - [ ] Upload button
  - [ ] Status
  - [ ] Progress
  - [ ] Error

### **☑️ 3.3 Wire MP4ProcessingContext**
- [ ] Provide MP4 job state to context
- [ ] Provide to StreamDebugPanel

### **☑️ 3.4 Update StreamDebugPanel**
- [ ] Show MP4:
  - [ ] Job ID
  - [ ] Status
  - [ ] Progress
  - [ ] Frames processed
  - [ ] Error

---

# **📌 Phase 4 — Delete Phase 10 Architecture**

### **☑️ 4.1 Delete Phase 10 components**
```
PluginSelector.tsx
ToolSelector.tsx
ResultsPanel.tsx
PluginInspector.tsx
RecordButton.tsx
OverlayToggles.tsx
ConfidenceSlider.tsx
ConfigPanel.tsx
DeviceSelector.tsx
FPSSlider.tsx
RadarView.tsx
LoadingSpinner.tsx
ProgressBar.tsx
BoundingBoxOverlay.tsx
OverlayRenderer.tsx
ResultOverlay.tsx
PipelineSelector.tsx
RealtimeOverlay.tsx
```

### **☑️ 4.2 Delete Phase 10 tests**
```
PluginSelector.test.tsx
ToolSelector.test.tsx
ResultsPanel.test.tsx
ResultsPanel.plugin.test.tsx
RecordButton.test.tsx
OverlayToggles.test.tsx
ConfidenceSlider.test.tsx
ConfigPanel.test.tsx
LoadingSpinner.test.tsx
ProgressBar.test.tsx
BoundingBoxOverlay.test.tsx
OverlayRenderer.test.tsx
ResultOverlay.test.tsx
PipelineSelector.test.tsx
RealtimeOverlay.test.tsx
VideoTracker.test.tsx (skipped → delete)
```

### **☑️ 4.3 Delete Phase 10 hooks/utils/types**
```
useManifest.ts
useVideoExport.ts
useWebSocket.ts (if legacy)
useManifest.test.ts
useVideoExport.test.ts
useWebSocket.test.ts
detectToolType.ts
runTool.ts
types/plugin.ts
```

---

# **📌 Phase 5 — MP4 Upload End‑to‑End Test**

### **☑️ 5.1 Upload test**
- [ ] Upload MP4
- [ ] Status: idle → uploading → processing → completed
- [ ] No console errors

### **☑️ 5.2 Job creation**
- [ ] `POST /v1/video/submit` returns `{ job_id }`
- [ ] Polling hits `GET /api/jobs/{id}`

### **☑️ 5.3 Progress**
- [ ] Progress increments
- [ ] Frames processed increments

### **☑️ 5.4 Error handling**
- [ ] Bad file → error state shown

### **☑️ 5.5 Jobs view**
- [ ] Job appears in JobList

### **☑️ 5.6 No pipeline/tool leakage**
- [ ] Search codebase for:
  - `pipelineId`
  - `plugin`
  - `tool`
  - `detectToolType`
- [ ] Confirm none exist

---

# **📌 Phase 6 — Final Integration Pass**

### **☑️ 6.1 Stream mode**
- [ ] WebSocket connects
- [ ] Frames stream
- [ ] Overlay renders
- [ ] Debug panel updates

### **☑️ 6.2 Upload mode**
- [ ] MP4 upload works end‑to‑end

### **☑️ 6.3 Jobs mode**
- [ ] Job list loads correctly

### **☑️ 6.4 Debug mode**
- [ ] Streaming metrics correct
- [ ] MP4 metrics correct

### **☑️ 6.5 No legacy UI**
- [ ] No plugin/tool UI
- [ ] No Phase 10 overlays
- [ ] No manifest loading

---


Just say the word.