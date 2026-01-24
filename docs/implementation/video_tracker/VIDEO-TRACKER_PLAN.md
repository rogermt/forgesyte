You’re right to be angry—that feeling of “I gave you the map and you still drove into a ditch” is real.

Let’s do what should’ve been done from the start: a **phased plan**, broken into **small, reviewable tasks**, each with **clear sign‑off criteria**. No “Week 4”, no vague blobs—just concrete steps you can approve one by one.

I’ll assume the current reality is:

- `forgesyte` = monorepo (Python server + React UI)  
- `forgesyte-plugins` = plugin repo (YOLO tracker etc.)  
- The Video Tool Runner does **not** exist in working form.

---

### Phase 0 — Ground truth & guardrails

**Goal:** Make sure no one can “interpret” the spec again.

- **Task 0.1 — Lock the UI diagram into the repo**
  - **Repo:** `forgesyte`
  - Add `docs/video-tool-runner.md` with the ASCII diagram you pasted and a short description.
  - **Sign‑off:** File exists, diagram matches exactly, no mention of export/record/extra features.

- **Task 0.2 — Add “scope guard” note**
  - **Repo:** `forgesyte`
  - In that doc, add a short “Out of scope” section:
    - No export
    - No record button
    - No model selector
    - No WS selector
  - **Sign‑off:** You read it and agree “yes, this is the only scope”.

---

### Phase 1 — Backend plugin manifest sanity

**Goal:** Ensure the UI can correctly identify the tool as frame‑based.

- **Task 1.1 — Fix YOLO tracker manifest**
  - **Repo:** `forgesyte-plugins`
  - File: `forgesyte_yolo_tracker/manifest.json`
  - Ensure the tool you want to use has:
    - `inputs.frame_base64`
    - `inputs.device`
    - `inputs.annotated`
  - **Sign‑off:** You open the manifest and see those keys exactly; no extra nonsense.

- **Task 1.2 — Add a tiny manifest check script**
  - **Repo:** `forgesyte-plugins`
  - Script (Python or Node) that:
    - Loads the manifest
    - Asserts `frame_base64` exists for the chosen tool
  - **Sign‑off:** Running the script prints “OK” or exits with error if broken.

---

### Phase 2 — App.tsx: manifest + tool type only

**Goal:** App.tsx knows which tool is frame‑based and routes to a placeholder VideoTracker.

- **Task 2.1 — Add `PluginManifest` type**
  - **Repo:** `forgesyte`
  - File: `webui/src/types/plugin.ts` (or similar)
  - Define:
    ```ts
    export interface PluginManifest {
      id: string;
      name: string;
      version: string;
      entrypoint: string;
      tools: Record<string, { inputs: Record<string, string>; outputs: Record<string, string> }>;
    }
    ```
  - **Sign‑off:** Type exists, no duplicate manifest types elsewhere.

- **Task 2.2 — Manifest state + loader in App.tsx**
  - **Repo:** `forgesyte`
  - File: `webui/src/App.tsx`
  - Add:
    - `const [manifest, setManifest] = useState<PluginManifest | null>(null);`
    - `useEffect` that fetches `/plugins/{selectedPlugin}/manifest`, sets `manifest` or `null` on error.
  - **Sign‑off:** You see:
    - Correct URL
    - `try/catch`
    - `setManifest(null)` on failure

- **Task 2.3 — `detectToolType` utility**
  - **Repo:** `forgesyte`
  - File: `webui/src/utils/detectToolType.ts`
  - Logic:
    ```ts
    if ("stream_id" in inputs) return "stream";
    if ("frame_base64" in inputs) return "frame";
    return "image";
    ```
  - **Sign‑off:** No hardcoded tool names, only key existence.

- **Task 2.4 — Route to `<VideoTracker>` placeholder**
  - **Repo:** `forgesyte`
  - File: `webui/src/App.tsx`
  - If `toolType === "frame"`, render `<VideoTracker pluginId={selectedPlugin} toolName={selectedTool} />`.
  - For now, VideoTracker can just render “VideoTracker placeholder”.
  - **Sign‑off:** Selecting the YOLO tool shows the placeholder component.

---

### Phase 3 — VideoTracker skeleton (no backend yet)

**Goal:** UI shell matches your diagram, but no real processing.

- **Task 3.1 — Create `VideoTracker.tsx`**
  - **Repo:** `forgesyte`
  - File: `webui/src/components/VideoTracker.tsx`
  - Props:
    ```ts
    interface VideoTrackerProps {
      pluginId: string;
      toolName: string;
    }
    ```
  - Internal state:
    - `videoFile`
    - `running`
    - `fps`
    - `device`
    - `overlayToggles` (players, tracking, ball, pitch, radar)
  - **Sign‑off:** Component compiles and renders.

- **Task 3.2 — Layout: video + canvas + controls**
  - **Repo:** `forgesyte`
  - In `VideoTracker.tsx`:
    - File input: `[ Upload Video ]`
    - (Webcam button can be stubbed or hidden initially)
    - `<video>` element
    - `<canvas>` overlay positioned on top
    - Controls row:
      - [Play] [Pause] [FPS ▼] [Device ▼]
      - [Players ✓] [Tracking ✓] [Ball ✓] [Pitch ✓] [Radar ✓]
  - **Sign‑off:** Visually matches your ASCII diagram (even if controls don’t do anything yet).

---

### Phase 4 — Frame loop + backend wiring

**Goal:** Play/pause + FPS + device actually drive calls to the backend and update overlays.

- **Task 4.1 — `useVideoProcessor` hook**
  - **Repo:** `forgesyte`
  - File: `webui/src/hooks/useVideoProcessor.ts`
  - Responsibilities:
    - Given `<video>` and current settings:
      - Extract current frame as base64
      - Call `/plugins/run` with `pluginId`, `toolName`, `frame_base64`, `device`, `annotated=false`
      - Maintain a small buffer of recent results (for tracking/fade)
  - **Sign‑off:** You see:
    - No preloading
    - One frame per tick
    - Retry logic (if you want it now or later)

- **Task 4.2 — Wire VideoTracker → useVideoProcessor**
  - **Repo:** `forgesyte`
  - `VideoTracker`:
    - On Play: start loop (e.g. `requestAnimationFrame` or `setInterval` based on FPS)
    - On Pause: stop loop
    - On each tick: call hook to process frame, store results in state
  - **Sign‑off:** When you click Play, you see network calls; Pause stops them.

---

### Phase 5 — Overlays (visuals only)

**Goal:** Draw the things you care about: players, tracks, ball, pitch, radar.

- **Task 5.1 — `ResultOverlay` module**
  - **Repo:** `forgesyte`
  - File: `webui/src/components/ResultOverlay.ts`
  - Given:
    - `canvas`
    - `frameWidth`, `frameHeight`
    - `detections`
    - `overlayToggles`
  - Draw:
    - Player boxes
    - Track IDs
    - Ball
    - Pitch lines
    - Radar in corner
  - **Sign‑off:** With mocked data, you see boxes, IDs, ball, pitch, radar.

- **Task 5.2 — Wire backend detections → ResultOverlay**
  - **Repo:** `forgesyte`
  - `VideoTracker` passes latest detections to `ResultOverlay`.
  - **Sign‑off:** Real detections from the plugin appear on the canvas.

---

### Phase 6 — Controls correctness

**Goal:** Every control does what it says, nothing more.

- **Task 6.1 — FPS selector**
  - Changes the interval/tick rate.
  - **Sign‑off:** Lower FPS → fewer backend calls; higher FPS → more.

- **Task 6.2 — Device selector**
  - Sends `device` in backend payload.
  - **Sign‑off:** You can see `device: "cpu"` vs `"cuda"` in network inspector.

- **Task 6.3 — Overlay toggles**
  - Each toggle hides/shows its layer.
  - **Sign‑off:** Toggling “Players” hides/shows boxes, etc.

---

### Phase 7 — Hard “no drift” check

**Goal:** Ensure no one sneaks in extra features.

- **Task 7.1 — Scope audit**
  - **Repo:** `forgesyte`
  - You (or SL) check:
    - No export
    - No record button
    - No model selector
    - No WS selector
    - No extra panels
  - **Sign‑off:** You literally grep the repo and confirm.

---
