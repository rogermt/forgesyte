# PR #76 Plan: Wire Backend Detections → ResultOverlay

## 📋 Overview

This PR implements **Task 5.2** - wiring backend detections from `useVideoProcessor` to the `ResultOverlay` component for drawing on the canvas.

## 📊 Information Gathered

### Current State Analysis

| File | Current State | Required Changes |
|------|---------------|------------------|
| `VideoTracker.tsx` | Has `canvasRef`, `overlayToggles`; destructures only `processing`, `error`, `lastRequestDuration` from hook | Extract `latestResult`, `buffer`; add `useEffect` to call `ResultOverlay` |
| `useVideoProcessor.ts` | Returns `latestResult: FrameResult`, `buffer: FrameResult[]` | No changes needed |
| `ResultOverlay.tsx` | React component managing its own canvas | Refactor to pure drawing function |
| `ResultOverlay.test.tsx` | Tests for React component | Update tests for pure function |

### Type Analysis

- `useVideoProcessor` returns:
  - `latestResult: FrameResult | null` (where `FrameResult = Record<string, unknown>`)
  - `buffer: FrameResult[]`

- `ResultOverlay` must accept raw JSON from plugin (plugin-agnostic at VideoTracker level)

## 🎯 Plan

### Step 1: Refactor `ResultOverlay.tsx` → `ResultOverlay.ts`
**File:** `web-ui/src/components/ResultOverlay.ts`

Convert from React component to pure drawing function:

```typescript
export interface OverlayToggles {
  players: boolean;
  tracking: boolean;
  ball: boolean;
  pitch: boolean;
  radar: boolean;
}

export interface ResultOverlayArgs {
  canvas: HTMLCanvasElement;
  frameWidth: number;
  frameHeight: number;
  detections: any;      // raw plugin JSON
  buffer: any[];        // recent frames
  overlayToggles: OverlayToggles;
}

export function ResultOverlay(args: ResultOverlayArgs): void {
  // Drawing logic here
}
```

**Key Changes:**
- Remove all React imports (`useState`, `useEffect`, `useRef`, `useMemo`)
- Remove JSX return statement
- Accept `canvas` as parameter instead of creating internal ref
- Resize canvas to match video dimensions
- Keep existing YOLO-specific logic (schema boundary is correct here)

### Step 2: Update `ResultOverlay.test.ts`
**File:** `web-ui/src/components/ResultOverlay.test.ts`

Update tests for pure function architecture:
- Mock `HTMLCanvasElement.prototype.getContext`
- Test canvas clearing
- Test detection drawing with toggles
- Test all overlay types (players, tracking, ball, pitch, radar)
- Test toggle behavior

### Step 3: Update `VideoTracker.tsx`
**File:** `web-ui/src/components/VideoTracker.tsx`

**Changes:**

1. **Import ResultOverlay function:**
   ```typescript
   import { ResultOverlay } from "./ResultOverlay";
   ```

2. **Extract `latestResult` and `buffer` from hook:**
   ```typescript
   const {
     latestResult,
     buffer,
     processing,
     error,
     lastRequestDuration,
   } = useVideoProcessor({...});
   ```

3. **Add `useEffect` for overlay rendering:**
   ```typescript
   useEffect(() => {
     if (!canvasRef.current || !videoRef.current) return;
     if (!latestResult) return;

     canvasRef.current.width = videoRef.current.videoWidth;
     canvasRef.current.height = videoRef.current.videoHeight;

     ResultOverlay({
       canvas: canvasRef.current,
       frameWidth: videoRef.current.videoWidth,
       frameHeight: videoRef.current.videoHeight,
       detections: latestResult,
       buffer,
       overlayToggles,
     });
   }, [latestResult, buffer, overlayToggles]);
   ```

4. **Remove inline canvas styles that set `width={0} height={0}`** (canvas will be sized by effect)

### Step 4: Update VideoTracker Tests
**File:** `web-ui/src/components/VideoTracker.test.tsx`

Add tests for:
- Overlay rendering with real detections
- Canvas ref is properly attached
- Effect runs when `latestResult` changes
- No schema parsing in VideoTracker

## 📁 Files to Modify

| File | Action |
|------|--------|
| `web-ui/src/components/ResultOverlay.tsx` | Rename to `.ts` and refactor to pure function |
| `web-ui/src/components/ResultOverlay.test.tsx` | Rename to `.ts` and update for pure function |
| `web-ui/src/components/VideoTracker.tsx` | Wire `latestResult`, `buffer`, add `useEffect` |
| `web-ui/src/components/VideoTracker.test.tsx` | Add integration tests |

## 🚫 What MUST NOT Be Implemented

- ❌ No YOLO-specific parsing in VideoTracker
- ❌ No bounding box math in VideoTracker
- ❌ No drawing logic in VideoTracker
- ❌ No scaling logic in VideoTracker
- ❌ No FPS logic changes
- ❌ No device logic changes
- ❌ No new UI controls
- ❌ No WebSockets
- ❌ No export/record features

## ✅ Sign-off Criteria

1. ✅ Upload video → Video displays normally
2. ✅ Click Play → Backend calls begin, `latestResult` updates, canvas overlay updates
3. ✅ Real detections visible → Player boxes, track IDs, ball, pitch lines, radar
4. ✅ Toggle overlays → Each toggle hides/shows its layer
5. ✅ No schema assumptions in VideoTracker → Only `ResultOverlay` interprets JSON
6. ✅ No drawing in VideoTracker → Canvas drawing exclusively in `ResultOverlay`

## 🔄 Dependencies

- None (this PR is self-contained)
- `ResultOverlay` implementation already exists (being refactored)
- `useVideoProcessor` already returns required data

## 📝 Follow-up Steps

1. **Run tests:** `npm test` in `web-ui/` directory
2. **Run linter:** `npm run lint` in `web-ui/` directory
3. **Verify no regressions:** All existing tests pass
4. **Manual testing:**
   - Upload a video
   - Click Play
   - Verify overlay appears
   - Test each toggle

