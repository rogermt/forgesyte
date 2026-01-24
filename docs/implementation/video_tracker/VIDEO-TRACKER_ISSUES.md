Absolutely, Roger — let’s turn your phased plan into **clean, atomic GitHub issues**, each with **explicit acceptance criteria** so your developer cannot drift, reinterpret, or “half‑follow” anything.

These issues are written so you can literally paste them into GitHub **as-is**.

Every issue is:

- small  
- unambiguous  
- testable  
- reviewable  
- impossible to “interpret creatively”  

And each one ends with **Sign‑off Criteria** so you can approve or reject the work instantly.

---

# 🟦 **PHASE 0 — Ground Truth & Guardrails**

---

## **Issue 0.1 — Add Video Tool Runner UI Spec to Repo**

**Repo:** `forgesyte`  
**Title:** Add canonical Video Tool Runner UI spec (source of truth)

**Description:**  
Create a new file `docs/video-tool-runner.md` containing the exact ASCII UI diagram and description of the Video Tool Runner. This document becomes the authoritative reference for all UI work.

**Content to include:**

```
┌──────────────────────────────────────────────────────────────┐
│                Video Tool Runner (Generic)                    │
├──────────────────────────────────────────────────────────────┤
│  Video Source:                                                │
│  [ Upload Video ]  [ Use Webcam ]                             │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  <video> element showing the match                     │   │
│  │                                                        │   │
│  │  <canvas overlay> draws:                               │   │
│  │   - player boxes                                       │   │
│  │   - track IDs                                          │   │
│  │   - ball                                               │   │
│  │   - pitch lines                                        │   │
│  │   - radar (small corner)                               │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                               │
│  Controls:                                                    │
│  [ Play ] [ Pause ] [ FPS: 5 ▼ ] [ Device: CPU ▼ ]           │
│  [ Players ✓ ] [ Tracking ✓ ] [ Ball ✓ ] [ Pitch ✓ ] [ Radar ✓ ] │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

Also add a section:

**Out of Scope:**
- No record button  
- No export  
- No model selector  
- No WS selector  
- No extra panels  

**Acceptance Criteria:**
- File exists at `docs/video-tool-runner.md`
- ASCII diagram matches exactly  
- Out-of-scope list included  
- No additional features mentioned  

---

## **Issue 0.2 — Add Scope Guardrails to README**

**Repo:** `forgesyte`  
**Title:** Add “Scope Guardrails” section to README

**Description:**  
Add a section to the main README that explicitly states what is *not* part of the Video Tool Runner.

**Acceptance Criteria:**
- README contains a “Scope Guardrails” section  
- Section lists: no export, no record, no model selector, no WS selector  
- No additional features listed  

---

# 🟩 **PHASE 1 — Backend Plugin Manifest Sanity**

---

## **Issue 1.1 — Fix YOLO Tracker Manifest**

**Repo:** `forgesyte-plugins`  
**Title:** Ensure YOLO tracker manifest declares frame-based inputs

**Description:**  
Update the manifest for the YOLO tracker so the UI can detect it as a frame-based tool.

**Required manifest structure:**

```json
"inputs": {
  "frame_base64": "string",
  "device": "string",
  "annotated": "boolean"
},
"outputs": {
  "detections": "array",
  "annotated_frame_base64": "string?"
}
```

**Acceptance Criteria:**
- Manifest contains `frame_base64`, `device`, `annotated`  
- No extra or missing fields  
- Plugin loads successfully in the server  

---

## **Issue 1.2 — Add Manifest Validation Script**

**Repo:** `forgesyte-plugins`  
**Title:** Add simple manifest validation script

**Description:**  
Add a small Python script `validate_manifest.py` that loads the YOLO manifest and asserts that `frame_base64` exists.

**Acceptance Criteria:**
- Running `python validate_manifest.py` prints “OK”  
- Script fails if `frame_base64` is missing  
- No external dependencies  

---

# 🟦 **PHASE 2 — App.tsx Manifest + Tool Type**

---

## **Issue 2.1 — Add PluginManifest Type**

**Repo:** `forgesyte`  
**Title:** Add PluginManifest Type Definition

**Description:**  
Create `webui/src/types/plugin.ts` with:

```ts
export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  entrypoint: string;
  tools: Record<string, {
    inputs: Record<string, string>;
    outputs: Record<string, string>;
  }>;
}
```

**Acceptance Criteria:**
- File exists  
- No duplicate manifest types elsewhere  
- App.tsx imports this type  

---

## **Issue 2.2 — Implement Manifest Loader in App.tsx**

**Repo:** `forgesyte`  
**Title:** Implement manifest loading logic in App.tsx

**Description:**  
Add:

- `manifest` state  
- `useEffect` that fetches `/plugins/{selectedPlugin}/manifest`  
- `try/catch`  
- `setManifest(null)` on error  

**Acceptance Criteria:**
- Correct URL used  
- Errors logged  
- Manifest set on success  
- Manifest reset on failure  
- No infinite loops  

---

## **Issue 2.3 — Implement detectToolType()**

**Repo:** `forgesyte`  
**Title:** Add detectToolType utility

**Description:**  
Create `webui/src/utils/detectToolType.ts` with:

```ts
if ("stream_id" in inputs) return "stream";
if ("frame_base64" in inputs) return "frame";
return "image";
```

**Acceptance Criteria:**
- No hardcoded tool names  
- Only key existence used  
- Unit tests included  

---

## **Issue 2.4 — Route to VideoTracker Placeholder**

**Repo:** `forgesyte`  
**Title:** Route frame-based tools to VideoTracker placeholder

**Description:**  
In App.tsx:

- If toolType === "frame", render `<VideoTracker />`  
- VideoTracker can be a placeholder for now  

**Acceptance Criteria:**
- Selecting YOLO tool shows “VideoTracker placeholder”  
- No errors in console  

---

# 🟩 **PHASE 3 — VideoTracker Skeleton**

---

## **Issue 3.1 — Create VideoTracker Component Skeleton**

**Repo:** `forgesyte`  
**Title:** Create VideoTracker component skeleton

**Description:**  
Add `webui/src/components/VideoTracker.tsx` with:

- Props: pluginId, toolName  
- Internal state:
  - videoFile  
  - running  
  - fps  
  - device  
  - overlayToggles  

**Acceptance Criteria:**
- Component renders without errors  
- No backend calls yet  

---

## **Issue 3.2 — Add Layout: Video + Canvas + Controls**

**Repo:** `forgesyte`  
**Title:** Implement VideoTracker layout (no logic)

**Description:**  
Add:

- Upload Video button  
- Use Webcam button (can be stubbed)  
- `<video>` element  
- `<canvas>` overlay  
- Controls row:
  - Play  
  - Pause  
  - FPS dropdown  
  - Device dropdown  
  - Overlay toggles  

**Acceptance Criteria:**
- UI visually matches ASCII diagram  
- No functionality required yet  

---

# 🟧 **PHASE 4 — Frame Loop + Backend Wiring**

---

## **Issue 4.1 — Implement useVideoProcessor Hook**

**Repo:** `forgesyte`  
**Title:** Implement useVideoProcessor (frame extraction + backend)

**Description:**  
Hook responsibilities:

- Extract current frame  
- Send to backend  
- Maintain small buffer  
- Return detections  

**Acceptance Criteria:**
- Hook compiles  
- No UI integration yet  
- No drift from responsibilities  

---

## **Issue 4.2 — Wire VideoTracker to useVideoProcessor**

**Repo:** `forgesyte`  
**Title:** Connect VideoTracker to useVideoProcessor

**Description:**  
- On Play: start loop  
- On Pause: stop loop  
- On each tick: call hook  

**Acceptance Criteria:**
- Network calls visible when playing  
- No calls when paused  

---

# 🟦 **PHASE 5 — Overlays**

---

## **Issue 5.1 — Implement ResultOverlay Drawing Module**

**Repo:** `forgesyte`  
**Title:** Implement ResultOverlay drawing logic

**Description:**  
Draw:

- player boxes  
- track IDs  
- ball  
- pitch lines  
- radar  

**Acceptance Criteria:**
- With mocked data, overlay draws correctly  
- No performance issues  

---

## **Issue 5.2 — Connect ResultOverlay to Real Detections**

**Repo:** `forgesyte`  
**Title:** Wire backend detections to ResultOverlay

**Description:**  
Pass detections from hook → VideoTracker → ResultOverlay.

**Acceptance Criteria:**
- Real detections appear on canvas  
- Toggling overlays hides/shows layers  

---

# 🟩 **PHASE 6 — Controls**

---

## **Issue 6.1 — FPS Selector Logic**

**Repo:** `forgesyte`  
**Title:** Implement FPS selector logic

**Acceptance Criteria:**
- Changing FPS changes tick rate  
- Verified via network inspector  

---

## **Issue 6.2 — Device Selector Logic**

**Repo:** `forgesyte`  
**Title:** Implement device selector logic

**Acceptance Criteria:**
- Backend receives correct device value  
- No UI drift  

---

## **Issue 6.3 — Overlay Toggle Logic**

**Repo:** `forgesyte`  
**Title:** Implement overlay toggle logic

**Acceptance Criteria:**
- Each toggle hides/shows its layer  
- No side effects  

---

# 🟦 **PHASE 7 — Scope Lock**

---

## **Issue 7.1 — Scope Audit**

**Repo:** `forgesyte`  
**Title:** Verify no out-of-scope features exist

**Acceptance Criteria:**
- No record button  
- No export  
- No model selector  
- No WS selector  
- No extra panels  
- You personally confirm  

---

Roger, this is the **cleanest, safest, most controlled plan** you can possibly run.

Each issue is:

- atomic  
- reviewable  
- testable  
- impossible to misinterpret  

If you want, I can also generate:

- a GitHub Project board  
- labels  
- milestones  
- or a “developer contract” they must sign before starting.

Just tell me.