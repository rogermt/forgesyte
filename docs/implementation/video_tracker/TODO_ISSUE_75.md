# TODO: Issue #75 (Task 4.2) - Wire VideoTracker → useVideoProcessor

## Implementation Plan

### Step 1: Add imports ✅
- [x] Import `useRef, useEffect, useCallback` from React
- [x] Import `useVideoProcessor` from hook
- [x] Import `FrameResult` type from hook

### Step 2: Add state ✅
- [x] Add `videoRef = useRef<HTMLVideoElement>(null)`
- [x] Add `[running, setRunning] = useState(false)` for processing control
- [x] Add `[videoSrc, setVideoSrc] = useState<string | null>(null)` for blob URL

### Step 3: Update file upload ✅
- [x] Modify `handleVideoUpload` to create blob URL with `URL.createObjectURL(file)`
- [x] Add useEffect to revoke blob URL on cleanup

### Step 4: Wire video element ✅
- [x] Pass `ref={videoRef}` to `<video>` element
- [x] Set `src={videoSrc}` on video element

### Step 5: Wire useVideoProcessor hook ✅
- [x] Call hook: `useVideoProcessor({ videoRef, pluginId, toolName, fps, device, enabled: running })`

### Step 6: Wire Play/Pause buttons ✅
- [x] Play button: setRunning(true)
- [x] Pause button: setRunning(false)
- [x] Sync with video playback (play/pause video element too)

### Step 7: Update device dropdown ✅
- [x] Change "gpu" option value to "cuda" (UI shows "GPU", value is "cuda")

### Step 8: Add canvas ref (for future overlay) ✅
- [x] Add `canvasRef = useRef<HTMLCanvasElement>(null)` for overlay rendering
- [x] Pass canvas ref to canvas element

### Step 9: Add status indicators ✅
- [x] Processing state indicator
- [x] Last request duration display
- [x] Error display

## Testing ✅
- [x] Verify video upload creates blob URL
- [x] Verify Play/Pause controls processing state
- [x] Verify device dropdown sends "cuda" to backend
- [x] Run existing tests to ensure no regressions (all 9 tests pass)
- [x] Type-check passes for VideoTracker.tsx
- [x] Lint passes for VideoTracker.tsx

## Out of Scope (separate tasks)
- [ ] ResultOverlay component (Task 5.1)
- [ ] Drawing detections on canvas

