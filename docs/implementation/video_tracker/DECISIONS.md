# Architectural Decisions & Rationale

**Approved by:** Senior Lead  
**Date:** Jan 2026  

---

## Decision 1: Frame Buffering (Store Last N Frames)

**Decision:** Maintain ring buffer of last 5–10 frames in UI state  
**Approved:** ✅

### Rationale
1. **Temporal context:** Tracking, radar, pitch detection benefit from multi-frame context
2. **Smoother overlays:** Reduces flicker and jitter in canvas rendering
3. **Future analytics:** Enables speed estimation, possession windows, heatmaps
4. **No backend cost:** Pure UI-side buffering, zero impact on backend

### Implementation
- `useVideoProcessor` hook manages `FrameBuffer` (circular FIFO)
- `ResultOverlay` can reference previous detections
- Track ID mapping stores `{trackId: {x, y, lastSeen: frameIndex}}`

### Test Coverage
- Unit test: Frame buffer maintains correct order
- Unit test: Old frames are evicted correctly
- Unit test: Track map updates with new detections

---

## Decision 2: Confidence Threshold UI (Add Slider)

**Decision:** Add 0.0–1.0 confidence slider, filter client-side  
**Approved:** ✅

### Rationale
1. **User expectation:** Standard in all CV tools
2. **Noise reduction:** Removes low-confidence clutter
3. **Plugin-agnostic:** Works with any tool returning `confidence` field
4. **Performance:** Client-side filtering is instant, no backend round-trip

### Implementation
- `<ConfidenceSlider>` component with range input
- Filter `detections[]` before passing to renderers
- Default threshold: 0.25 (matches plugin defaults)

### Test Coverage
- Unit test: Slider updates state
- Unit test: Detections filtered correctly
- Unit test: Confidence=0.0 shows all, confidence=1.0 shows none

### Limitations
- Doesn't retroactively filter past frames (only current)
- Optional: Could be extended to filter in plugin (pass threshold to backend)

---

## Decision 3: Track ID Persistence (Maintain Across Frames)

**Decision:** UI-side tracking context: `Map<trackId, {x, y, lastSeen}>`  
**Approved:** ✅

### Rationale
1. **Stable tracking:** ByteTrack already provides stable IDs; UI must not "forget" them
2. **Enables metrics:** Foundational for heatmaps, distance, speed, possession
3. **Better UX:** Track IDs don't flicker or restart
4. **No backend cost:** Pure UI-side, zero impact on plugins

### Implementation
- `useVideoProcessor` maintains `trackMap: Map<string, TrackHistory>`
- `TrackHistory = {x, y, lastSeen: frameIndex, fadeOut: boolean}`
- `BoundingBoxRenderer` grays out tracks unseen for >2 frames
- Track removal: evict after 5 frames of not seeing

### Test Coverage
- Unit test: Track map updates correctly
- Unit test: New track IDs are added
- Unit test: Old track IDs are evicted
- Unit test: Fade-out logic works correctly
- Integration test: Track ID persists across 10+ frames

### Future Extensions
- Heatmap: Sum all (x, y) positions per track ID
- Speed: Distance between consecutive positions
- Possession: Track which team has ball (cluster tracks by proximity)

---

## Decision 4: Overlay Composition (Multi-Layer + Toggles)

**Decision:** Single canvas with layered renderers (players, ball, pitch, radar), configurable toggles  
**Approved:** ✅

### Rationale
1. **Plugin-agnostic:** Tools define data; UI defines rendering
2. **Mirrors existing system:** Image overlay toggles already work this way
3. **Extensible:** New tools automatically discoverable from manifest
4. **User control:** Coach can toggle layers on-the-fly

### Implementation
- Single canvas element (1280×720)
- Layer rendering order: pitch → ball → players → radar
- Each renderer is independent:
  - `BoundingBoxRenderer` (players)
  - `BallRenderer` (ball)
  - `PitchRenderer` (pitch lines/keypoints)
  - `RadarRenderer` (already exists, reuse)
- `<OverlayToggles>` controls visibility
- State: `visibleLayers = {players: true, ball: true, pitch: true, radar: false}`

### Test Coverage
- Unit test: Each renderer works independently
- Unit test: Toggles control visibility correctly
- Unit test: Rendering order is correct (no z-fighting)
- Integration test: All layers together (no performance degradation)

### Performance Notes
- Canvas clearing + redrawing on each frame is acceptable (<500ms)
- Optimize later if needed (dirty rectangles, offscreen canvas)

---

## Decision 5: Video Export (UI-Side MediaRecorder First)

**Decision:** Use MediaRecorder API to capture canvas+audio as WebM, UI-side export  
**Approved:** ✅

### Rationale
1. **Zero backend cost:** Works entirely in browser
2. **Huge UX win:** Users can share annotated clips immediately
3. **No complexity:** MediaRecorder is standard browser API
4. **Scalability:** Doesn't require backend video encoding (CPU-intensive)
5. **Immediate ROI:** Available in Week 2, not Week 6

### Implementation
- `<RecordButton>` component with MediaRecorder
- Capture video stream + canvas overlay simultaneously
- Export as WebM (or MP4 via browser codec if available)
- User downloads file directly

### Limitations & Future Work
- MP4 export may require additional codec (not in all browsers)
- Large file sizes (optimize compression later)
- **Option B (future, Week 6):** Backend batch export with ffmpeg
  - Upload entire video
  - Backend processes all frames
  - Returns MP4 with burned-in annotations

### Test Coverage
- Unit test: RecordButton creates MediaRecorder correctly
- Unit test: Start/stop recording works
- Integration test: Exported file is valid WebM
- Manual test: Exported video plays in browser

---

## Decision 6: Async Tool Execution (Use Jobs for Batch, Sync for Real-Time)

**Decision:** 
- Real-time (single frame): `/plugins/{id}/tools/{tool}/run` → immediate JSON
- Batch (future): `/plugins/{id}/batch_run` → job_id + polling

**Approved:** ✅

### Rationale
1. **Real-time:** Single frames must be fast; can't wait for job queue
2. **Batch:** Video files are large; background processing makes sense
3. **Clean separation:** Two paths, not one trying to do both
4. **Current scope:** Implement sync path now; batch is Phase 2 (future)

### Implementation
- Sync tool execution (this PR):
  ```
  POST /plugins/{id}/tools/{tool}/run
  {"args": {"frame_base64": "...", "device": "cpu", ...}}
  → {tool_name, result, processing_time_ms} (immediate)
  ```

- Async batch execution (future Phase 2):
  ```
  POST /plugins/{id}/batch_run
  {"frames": [...], "tool": "..."}
  → {job_id} (immediate)
  
  Then poll: GET /jobs/{job_id}
  ```

### Test Coverage
- Unit test: Sync execution works
- Unit test: Error handling on invalid plugin/tool
- Integration test: Real plugin execution (CPU mock)
- GPU test: Real YOLO execution (RUN_MODEL_TESTS=1)

### Performance Expectations
- CPU: 100–500ms per frame (reasonable)
- GPU: 20–100ms per frame (great)
- 2 FPS = 1 frame every 500ms → acceptable for real-time viewing

---

## Decision 7: Manifest Caching (Frontend + Backend)

**Decision:** Cache manifest in both UI and backend with TTL  
**Approved:** ✅

### Rationale
1. **Frontend:** Cache in React state to avoid repeated API calls
2. **Backend:** In-memory cache with 5-minute TTL to avoid file I/O
3. **Invalidation:** Clear on plugin reload
4. **Performance:** Manifest discovery is instant after first load

### Implementation
- Backend: `ManifestCacheService` with TTL
- Frontend: `useManifest(pluginId)` hook with React context
- Both: Clear cache when plugin is reloaded

### Test Coverage
- Unit test: Cache returns correct manifest
- Unit test: TTL expiration works
- Unit test: Cache invalidation on reload
- Integration test: No repeated file reads

---

## Decision 8: Generic Result Rendering (No Plugin Coupling)

**Decision:** Generic canvas overlays + optional `render_hints` in manifest  
**Approved:** ✅

### Rationale
1. **Decoupling:** UI doesn't hardcode plugin-specific renderers
2. **Extensibility:** New tools can add rendering hints without UI changes
3. **Flexibility:** Plugins guide rendering without coupling

### Implementation
- Generic renderers for common types:
  - Bounding boxes (x1, y1, x2, y2, label, confidence)
  - Circles (x, y, radius, label)
  - Lines/points (for pitch keypoints)
  - Radar (already exists)

- Optional `render_hints` in tool output schema:
  ```json
  "outputs": {
    "detections": {
      "render_hints": {
        "overlay_type": "bounding_box",
        "color": "#00ff00",
        "label_field": "class_name",
        "confidence_field": "confidence"
      }
    }
  }
  ```

### Test Coverage
- Unit test: Generic renderers work with sample data
- Unit test: Render hints are parsed correctly
- Integration test: Real plugin output renders correctly

### Future Extensions
- Custom renderers per tool (plugin.json entrypoint)
- Annotation palette (user-adjustable colors)
- Glow/shadow effects for better visibility

---

## Summary Table

| Decision | Choice | Reason | Impact |
|----------|--------|--------|--------|
| Frame buffering | Last N frames (5–10) | Smoother, future metrics | Low (UI-side only) |
| Confidence slider | Yes, client-side | User control, standard UX | Low |
| Track persistence | Map UI-side | Stable tracking, metrics | Low |
| Overlay composition | Multi-layer + toggles | Plugin-agnostic, extensible | Medium (new components) |
| Video export | MediaRecorder (UI-side) | Zero backend cost, high ROI | Medium (new component) |
| Async execution | Sync now, batch later | Real-time + batch coverage | Medium (two paths) |
| Manifest caching | TTL cache (UI + backend) | Performance + reliability | Low |
| Result rendering | Generic + hints | No coupling, extensible | Medium (new renderers) |

---

**All decisions are locked. Ready for implementation.**
