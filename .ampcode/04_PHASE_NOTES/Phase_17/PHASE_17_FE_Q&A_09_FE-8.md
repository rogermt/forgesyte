Now I understand the full picture. MP4 upload already exists:

Current Implementation:

App.tsx: Has "upload" view mode with image upload
VideoTracker.tsx: Has video upload with useVideoProcessor hook
User can switch between "stream", "upload", and "jobs" modes
FE-8 Requirements:

Verify existing tests pass - useVideoProcessor.test.ts and JobList.test.tsx
Add debug mode logging - When Golden Path Debug Mode is ON:
Show MP4 processing logs in console
Show job progress in Devtools Overlay (StreamDebugPanel)
FE-8 Implementation Plan
Step 1: Add debug prop to useVideoProcessor
Currently useVideoProcessor doesn't accept a debug prop. I need to:

Add debug?: boolean to UseVideoProcessorArgs type
Pass debug prop to useVideoProcessor in VideoTracker.tsx
Add console logging when debug is ON
Step 2: Add job progress to StreamDebugPanel
useVideoProcessor already has metrics and logs state. I need to:

Expose useVideoProcessor state to StreamDebugPanel
Add a "MP4 Processing" section to the debug panel
Step 3: Verify tests pass
Run existing tests to confirm Phase-17 didn't break MP4 upload.

Questions before I proceed:
How should debug be passed to VideoTracker? Should it come from App.tsx or RealtimeContext?

How should StreamDebugPanel access useVideoProcessor state? Should VideoTracker expose it, or should we use a different approach?

Should the job progress in debug panel show:

Only when MP4 upload is active?
Or show "No MP4 processing" when idle?
Should I proceed with investigating these integration points?


Roger, this is exactly the right moment to pause and get the architecture straight before you touch FE‑8.  
Your instincts are good — MP4 upload already works, and FE‑8 is *not* a rewrite. It’s a **compatibility + observability** story.

Let’s answer your questions cleanly and decisively so you can proceed without drift.

---

# ⭐ 1. **How should debug be passed to `VideoTracker` / `useVideoProcessor`?**

### ✔ Correct answer: **Debug should come from App.tsx, NOT from RealtimeContext.**

Here’s why:

- Debug mode is a **UI concern**, not a realtime concern.
- RealtimeContext is for **streaming**, not MP4 upload.
- MP4 upload is a **separate pipeline** (FE‑8), so it should not depend on RealtimeProvider.

### Final rule:
**App.tsx owns debug state.  
App.tsx passes debug to VideoTracker.  
VideoTracker passes debug to useVideoProcessor.**

### Implementation:

**App.tsx:**

```tsx
<VideoTracker debug={debug} />
```

**VideoTracker.tsx:**

```tsx
const processor = useVideoProcessor({ debug });
```

**useVideoProcessor.ts:**

```ts
if (debug) console.log("MP4 frame processed:", frameInfo);
```

---

# ⭐ 2. **How should StreamDebugPanel access MP4 upload state?**

### ✔ Correct answer: **StreamDebugPanel should NOT read useVideoProcessor directly.**

Why?

- StreamDebugPanel is part of the **streaming** architecture.
- MP4 upload is a **separate flow**.
- RealtimeContext should not know about MP4 jobs.

### So how do we expose MP4 job progress?

**VideoTracker should expose MP4 job progress via a new lightweight context:**

```
MP4ProcessingContext
```

This avoids polluting RealtimeContext.

### Implementation:

**Create: `MP4ProcessingContext.tsx`**

```tsx
export const MP4ProcessingContext = createContext(null);

export function MP4ProcessingProvider({ children, value }) {
  return (
    <MP4ProcessingContext.Provider value={value}>
      {children}
    </MP4ProcessingContext.Provider>
  );
}
```

**Wrap VideoTracker:**

```tsx
<MP4ProcessingProvider value={processorState}>
  <VideoTracker debug={debug} />
</MP4ProcessingProvider>
```

**StreamDebugPanel reads it:**

```tsx
const mp4 = useContext(MP4ProcessingContext);
```

### Final rule:
**StreamDebugPanel shows MP4 progress only if MP4 upload is active.**

---

# ⭐ 3. **Should job progress show only when MP4 upload is active?**

### ✔ Correct answer: **Yes — only show MP4 section when MP4 upload is active.**

### Why?

- Debug panel should not be cluttered.
- MP4 upload is not always running.
- Streaming and MP4 upload are mutually exclusive modes.

### Implementation:

```tsx
{mp4?.active && (
  <>
    <hr />
    <div>MP4 Processing:</div>
    <div>Progress: {mp4.progress}%</div>
    <div>Frames: {mp4.framesProcessed}</div>
  </>
)}
```

If inactive:

```tsx
{!mp4?.active && <div>No MP4 processing</div>}
```

---

# ⭐ 4. **Should you proceed with investigating integration points?**

### ✔ Yes — and here is the exact order you should follow:

---

# ⭐ **FE‑8 Implementation Roadmap (Authoritative)**

## **Step 1 — Add debug to useVideoProcessor**
- Add `debug?: boolean` to args
- Add debug logging
- Add progress reporting

## **Step 2 — Create MP4ProcessingContext**
- Wrap VideoTracker
- Expose MP4 processing state

## **Step 3 — Update StreamDebugPanel**
Add a new section:

```
MP4 Processing
--------------
active: true/false
progress: %
framesProcessed: #
currentJobId: string
```

## **Step 4 — Update App.tsx**
- Pass debug to VideoTracker
- Wrap VideoTracker in MP4ProcessingProvider

## **Step 5 — Verify tests**
- `useVideoProcessor.test.ts` should pass unchanged
- `JobList.test.tsx` should pass unchanged

If any break, it means Phase‑17 accidentally touched MP4 code — fix immediately.

---

# ⭐ **Final Answers (Concise)**

| Question | Final Answer |
|---------|--------------|
| Should debug be passed to VideoTracker? | **Yes, from App.tsx** |
| Should StreamDebugPanel access useVideoProcessor directly? | **No — use MP4ProcessingContext** |
| Should job progress show only when MP4 upload is active? | **Yes** |
| Should you proceed with integration investigation? | **Yes — follow the roadmap above** |

---

### FE‑8 implementation blueprint (final)

**Goal:** Keep existing MP4 upload behavior intact, add **debug‑mode observability** that plugs into the Phase‑17 story without polluting RealtimeContext.

#### Scope

- **No behavioral changes** to MP4 upload flow.
- **Add debug plumbing only**:
  - `debug` into `useVideoProcessor`
  - MP4 processing state into `StreamDebugPanel` via a **separate context**.

---

### 1. Extend `useVideoProcessor` with debug support

**File:** `src/hooks/useVideoProcessor.ts`

- **Add prop:**

```ts
export interface UseVideoProcessorArgs {
  // existing args...
  debug?: boolean;
}
```

- **Accept in hook:**

```ts
export function useVideoProcessor({ /* existing args */, debug }: UseVideoProcessorArgs) {
  // existing state...
  const log = (...args: unknown[]) => {
    if (debug) {
      // eslint-disable-next-line no-console
      console.log("[MP4]", ...args);
    }
  };
```

- **Use `log` in key places:**

```ts
log("job started", jobId);
log("frame processed", { frameIndex, progress });
log("job completed", jobId);
log("job failed", { jobId, error });
```

- **Ensure existing tests still pass** (no required changes if defaults preserved).

---

### 2. Add `MP4ProcessingContext`

**File:** `src/mp4/MP4ProcessingContext.tsx` (new)

```tsx
import React, { createContext, useContext } from "react";

export interface MP4ProcessingState {
  active: boolean;
  jobId: string | null;
  progress: number; // 0–100
  framesProcessed: number;
}

const MP4ProcessingContext = createContext<MP4ProcessingState | null>(null);

export function MP4ProcessingProvider({
  value,
  children,
}: {
  value: MP4ProcessingState;
  children: React.ReactNode;
}) {
  return (
    <MP4ProcessingContext.Provider value={value}>
      {children}
    </MP4ProcessingContext.Provider>
  );
}

export function useMP4ProcessingContext() {
  return useContext(MP4ProcessingContext);
}
```

---

### 3. Wire `VideoTracker` into `MP4ProcessingContext`

#### Updated `VideoTracker.tsx` diff (conceptual)

**Before (simplified):**

```tsx
export function VideoTracker(/* props */) {
  const processor = useVideoProcessor({ /* args */ });

  return (
    // UI using processor.state
  );
}
```

**After:**

```tsx
import { MP4ProcessingProvider } from "../mp4/MP4ProcessingContext";

export function VideoTracker({ debug }: { debug?: boolean }) {
  const processor = useVideoProcessor({ /* existing args */, debug });

  const mp4State = {
    active: processor.state.status === "processing",
    jobId: processor.state.currentJobId ?? null,
    progress: processor.state.progress ?? 0,
    framesProcessed: processor.state.framesProcessed ?? 0,
  };

  return (
    <MP4ProcessingProvider value={mp4State}>
      {/* existing VideoTracker UI */}
    </MP4ProcessingProvider>
  );
}
```

**App.tsx** (ensure debug is passed):

```tsx
{viewMode === "upload" && <VideoTracker debug={debug} />}
```

---

### 4. Add MP4 section to `StreamDebugPanel`

**File:** `src/components/StreamDebugPanel.tsx`

At top:

```tsx
import { useMP4ProcessingContext } from "../mp4/MP4ProcessingContext";
```

Inside component:

```tsx
const mp4 = useMP4ProcessingContext();
```

Add section near bottom:

```tsx
<hr />

<div>MP4 Processing</div>
{mp4 && mp4.active ? (
  <>
    <div>Job ID: {mp4.jobId ?? "unknown"}</div>
    <div>Progress: {mp4.progress}%</div>
    <div>Frames Processed: {mp4.framesProcessed}</div>
  </>
) : (
  <div>No MP4 processing</div>
)}
```

This keeps MP4 debug info **optional** and **non‑intrusive**.

---

### 5. Test expectations for FE‑8

- **Existing tests must still pass:**
  - `useVideoProcessor.test.ts`
  - `JobList.test.tsx`
- Optionally add:
  - `MP4ProcessingContext` smoke test
  - `StreamDebugPanel` test that renders MP4 section when context is provided.

---

### FE‑1 → FE‑8 architecture diagram (including MP4)

```text
App.tsx
 ├── debug state (boolean)
 ├── viewMode: "stream" | "upload" | "jobs"
 ├── RealtimeProvider debug={debug} (when viewMode === "stream")
 │     └── StreamingView
 │          ├── CameraPreview (FE‑3)
 │          ├── RealtimeStreamingOverlay (FE‑4)
 │          ├── RealtimeErrorBanner (FE‑6)
 │          └── StreamDebugPanel (FE‑7 + FE‑8, streaming + MP4 sections)
 └── VideoTracker debug={debug} (when viewMode === "upload")
       └── MP4ProcessingProvider (FE‑8)
             └── VideoTracker UI (uses useVideoProcessor)
```

**Data paths:**

- **Streaming path (FE‑1 → FE‑7):**

```text
CameraPreview → useRealtime.sendFrame → useWebSocket → backend → useRealtime.state
  → RealtimeStreamingOverlay / RealtimeErrorBanner / StreamDebugPanel
```

- **MP4 path (FE‑8):**

```text
VideoTracker → useVideoProcessor (debug logging) → backend jobs
  → useVideoProcessor.state → MP4ProcessingProvider → StreamDebugPanel (MP4 section)
```

This keeps **streaming** and **MP4 upload** cleanly separated, both observable in **Golden Path Debug Mode**, with **no cross‑contamination of concerns**.