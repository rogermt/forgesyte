# Video Tracker Integration — Architecture & Design Plan

**Status:** Ready for implementation  
**Owner:** Roger + Senior Lead  
**Repos:** forgesyte, forgesyte-plugins  

---

## 📊 Executive Summary

**Goal:** Integrate video stream tracking into web-ui without hardcoding plugins.

**Approach:** 
- Two execution paths: async jobs (batch) + sync tools (real-time)
- Plugin-agnostic tool discovery (manifest-driven)
- Generic result rendering with optional plugin hints
- Clear CPU/GPU test separation per AGENTS.md

**Impact:** ~15% backend change, ~25% web-ui change, 0% plugin change.

---

## 🎯 Architectural Decisions (Senior Lead Approved)

### 1. **Async Tool Execution**
- Sync for real-time: `/plugins/{id}/tools/{tool}/run` → immediate JSON
- Async for video: → job_id + polling/WebSocket
- **Why:** Real-time video can't wait for long inference; batch processing needs background jobs

### 2. **Frame Size Limits**
- Frontend: Resize frames before encoding (max 1280×720)
- Backend: Validate + warn if exceeded
- **Why:** Prevent OOM on base64 transport; keep inference fast

### 3. **Manifest Caching**
- Frontend: Cache in React state/context (invalidate on plugin change)
- Backend: In-memory cache with TTL
- **Why:** Avoid repeated file I/O; reduce API calls

### 4. **Result Rendering**
- Generic: Canvas overlays (boxes, circles, lines)
- Plugin-guided: Optional `render_hints` in manifest output schema
- **Why:** UI stays decoupled; plugins can guide rendering without coupling

### 5. **Mid-Stream Error Handling**
- Structured error payloads: `{status: "error", message: "...", recoverable: true}`
- UI: Toast + auto-retry if recoverable
- **Why:** Streaming is fragile; explicit error contract prevents silent failures

### 6. **Batch Processing**
- Future: `/plugins/{id}/batch_run` for video timelines
- Current: Single-frame `/plugins/{id}/tools/{tool}/run` only
- **Why:** Start simple; add batch later when needed

---

## 🗂️ File Structure

### Backend (forgesyte/server)
```
app/
├── api.py                                  ← Add /plugins/{id}/manifest, /plugins/{id}/tools/{tool}/run
├── models.py                               ← Add PluginToolRunRequest, PluginToolRunResponse
├── services/
│   ├── plugin_management_service.py        ← Add get_plugin_manifest(), run_plugin_tool()
│   └── manifest_cache_service.py           ← NEW: Cache manifest with TTL
└── tests/
    ├── api/test_plugins_manifest.py        ← CPU-only tests
    ├── api/test_plugins_run.py             ← CPU-only tests
    └── integration/test_video_stream.py    ← GPU tests (RUN_MODEL_TESTS=1)
```

### Web-UI (forgesyte/web-ui)
```
src/
├── api/
│   └── client.ts                           ← Add getPluginManifest(), runPluginTool()
├── hooks/
│   ├── useVideoProcessor.ts                ← NEW: Extract frames + process
│   ├── useVideoProcessor.test.ts           ← CPU-only tests
│   └── useManifest.ts                      ← NEW: Cache manifest
├── components/
│   ├── ToolSelector.tsx                    ← NEW: Discover tools from manifest
│   ├── ToolSelector.test.tsx               ← CPU-only tests
│   └── ResultOverlay.tsx                   ← NEW: Generic canvas rendering
├── pages/
│   ├── VideoTracker.tsx                    ← NEW: Main video tracker page
│   └── VideoTracker.test.tsx               ← CPU-only tests
└── types/
    └── plugin.ts                           ← NEW: PluginManifest, ToolSchema types
```

### Plugin (forgesyte-plugins/forgesyte-yolo-tracker)
```
src/forgesyte_yolo_tracker/
├── manifest.json                           ← (frozen; no changes)
├── tests/
│   ├── test_player_detection.py            ← Existing (fast CPU tests)
│   └── gpu/
│       └── test_video_streaming.py         ← NEW: GPU video tests (RUN_MODEL_TESTS=1)
└── (rest unchanged)
```

---

## 🧪 Testing Strategy

### CPU-Only Tests (Run Always)
**Location:** `test_*.py` files without GPU requirements  
**Command:** `pytest tests/`  
**What:** Mocked plugins, no YOLO models, no inference  
**Tools:** Mock, patch, fixtures  

**Examples:**
- API endpoint routing (200, 404, 400)
- Plugin discovery (list, manifest schema)
- Component rendering (ToolSelector, ResultOverlay)
- Hook logic (extractFrameBase64, processFrame)

### GPU Tests (Skip on CPU)
**Location:** `gpu/test_*.py` or mark with `RUN_MODEL_TESTS=1`  
**Command:** `RUN_MODEL_TESTS=1 pytest tests/`  
**What:** Real YOLO models, actual inference on frames  
**Tools:** Real models on Kaggle/GPU  

**Examples:**
- Plugin tool execution (player_detection actually runs)
- Video stream processing (10+ frames, measure latency)
- Motion_detector integration (WebSocket + frame streaming)

**Test Markers (pytest):**
```python
import os
import pytest

RUN_MODEL_TESTS = os.getenv("RUN_MODEL_TESTS", "0") == "1"

@pytest.mark.skipif(
    not RUN_MODEL_TESTS,
    reason="Requires YOLO model (set RUN_MODEL_TESTS=1)"
)
def test_player_detection_with_real_model():
    # Real inference test
    pass
```

---

## 🔄 Execution Flow

### Real-Time Video Stream (Sync Path)
```
1. User uploads video + selects plugin + selects tool
2. Web-UI extracts frames at chosen FPS (e.g., 2 FPS)
3. For each frame:
   a. Resize to max 1280×720
   b. Convert to base64
   c. POST /plugins/{id}/tools/{tool}/run with frame_base64
   d. Backend: Load plugin, call tool function, return result immediately
   e. UI: Parse result, render overlay on canvas
   f. Show processing_time_ms
4. User can stop, adjust FPS, change tool (sync)
```

### Batch Video Processing (Async Path — Future)
```
1. User uploads entire video
2. Web-UI extracts all frames
3. POST /plugins/{id}/batch_run with [frame1, frame2, ...]
4. Backend: Return job_id
5. UI: Poll /jobs/{id} until done
6. UI: Show timeline with results + confidence curve
```

---

## 📋 Implementation Checklist

### Phase 1: Backend Endpoints (Week 1)
- [ ] Add `/plugins/{id}/manifest` endpoint
- [ ] Add `/plugins/{id}/tools/{tool}/run` endpoint
- [ ] Add ManifestCacheService (in-memory + TTL)
- [ ] Write CPU-only tests (mocked plugin, no inference)
- [ ] Document error codes (400, 404, 500)

### Phase 2: Web-UI Hooks & Components (Week 2)
- [ ] Add `useVideoProcessor` hook (frame extraction + API calls)
- [ ] Add `useManifest` hook (manifest caching)
- [ ] Add `ToolSelector` component (discover tools from manifest)
- [ ] Add `ResultOverlay` component (generic canvas rendering)
- [ ] Add `VideoTracker` page (orchestrate above)
- [ ] Write CPU-only tests (mocked API, no inference)
- [ ] Wire to existing `ResultsPanel` + `PluginSelector`

### Phase 3: Integration Tests (Week 3)
- [ ] Backend: Test real plugin tool execution (CPU-only with mocks)
- [ ] Backend: Test video stream with real YOLO (GPU, RUN_MODEL_TESTS=1)
- [ ] Web-UI: Integration test with real server
- [ ] End-to-end: Upload video → process frames → view results

### Phase 4: Motion_Detector Support (Week 4)
- [ ] Detect streaming plugins (look for `start_stream` in manifest)
- [ ] Implement WebSocket streaming handler
- [ ] Test with motion_detector plugin

### Phase 5: Polish & Optimization (Week 5)
- [ ] FPS slider (adjustable real-time)
- [ ] Overlay toggles (show/hide players, ball, pitch, radar)
- [ ] Frame skip support (process every Nth frame)
- [ ] Performance profiling (measure latency per tool)

---

## 🏗️ Data Models & Contracts

### Plugin Manifest Schema
```
{
  "id": "forgesyte-yolo-tracker",
  "name": "YOLO Football Tracker",
  "version": "1.0.0",
  "description": "...",
  "tools": {
    "player_detection": {
      "description": "Detect players in frame",
      "inputs": {
        "frame_base64": "string (base64-encoded JPEG)",
        "device": "string (cpu|cuda)",
        "annotated": "boolean"
      },
      "outputs": {
        "detections": "array<{x1, y1, x2, y2, confidence}>",
        "annotated_frame_base64": "string? (if annotated=true)"
      }
    },
    ...
  }
}
```

### Tool Execution Request/Response
```
POST /plugins/{id}/tools/{tool}/run
{
  "args": {
    "frame_base64": "iVBORw0KGgo...",
    "device": "cpu",
    "annotated": false
  }
}

Response:
{
  "tool_name": "player_detection",
  "plugin_id": "forgesyte-yolo-tracker",
  "result": {
    "detections": [...],
    "annotated_frame_base64": null
  },
  "processing_time_ms": 42
}
```

### Render Hints (Plugin-Guided Rendering)
```
"outputs": {
  "detections": {
    "type": "array",
    "render_hints": {
      "overlay_type": "bounding_box",
      "color": "#00ff00",
      "label_field": "class_name",
      "confidence_field": "confidence",
      "line_width": 2
    }
  }
}
```

---

## 🚀 Success Criteria

✅ **Backend:**
- `/plugins/{id}/manifest` returns tool schemas
- `/plugins/{id}/tools/{tool}/run` executes tools immediately
- ManifestCacheService caches manifest with 5min TTL
- All endpoints tested (CPU-only, no GPU required)
- Error handling: 400 (bad args), 404 (plugin/tool not found), 500 (execution failed)

✅ **Web-UI:**
- ToolSelector discovers tools from manifest dynamically
- VideoTracker extracts frames, resizes to 1280×720, sends to backend
- ResultOverlay renders boxes + radar (generic)
- Components fully typed (no `any`)
- All hooks/components tested (CPU-only, no API calls in unit tests)

✅ **Integration:**
- Upload video → process 10 frames → view results (end-to-end)
- GPU tests: Real YOLO inference on 5+ frames (RUN_MODEL_TESTS=1)
- Performance: <500ms per frame on CPU (reasonable expectation)

✅ **No Hardcoding:**
- No plugin names in web-ui code (all from manifest)
- No tool names hardcoded (all from manifest)
- No result parsing logic (generic overlay + render_hints)

---

## ✅ Architectural Decisions (Senior Lead Answers)

### 1. Frame Buffering
**Decision:** Store last N frames (5–10, configurable)  
**Why:** Smoother overlays, temporal context for future analytics (speed, possession)  
**Impact:** UI maintains ring buffer in `useVideoProcessor` hook  
**Backend:** No change

### 2. Confidence Threshold UI
**Decision:** Add slider (0.0–1.0), filter client-side  
**Why:** User control, noise reduction, plugin-agnostic  
**Impact:** Add `<ConfidenceSlider>` component, filter `detections[]` before rendering  
**Backend:** No change

### 3. Track ID Persistence
**Decision:** Maintain `trackId → lastSeen` map UI-side, persist across frames  
**Why:** Stable tracking, enables future metrics (heatmaps, distance, speed)  
**Impact:** Add tracking context to `ResultOverlay` component  
**Backend:** No change (plugin already returns track IDs)

### 4. Overlay Composition
**Decision:** Stack multiple tools on one canvas (players + ball + pitch + radar), configurable toggles  
**Why:** Plugin-agnostic layering, mirrors existing image overlay system  
**Impact:** Single canvas with layered renderers + tool toggles  
**Backend:** No change

### 5. Video Export
**Decision:** UI-side export first (MediaRecorder to capture canvas+video as MP4/WebM)  
**Why:** Huge UX win, zero backend cost, works in browser immediately  
**Impact:** Add "Record" button + MediaRecorder API  
**Backend:** No change (Option B with ffmpeg is future phase)

---

## 📊 Updated Component Diagram

```
VideoTracker (Page)
├── PluginSelector (existing)
├── ToolSelector (NEW, discovers tools from manifest)
├── ConfidenceSlider (NEW, filters client-side)
├── OverlayToggles (NEW, players/ball/pitch/radar)
├── RecordButton (NEW, MediaRecorder export)
├── VideoElement
└── ResultOverlay (UPDATED)
    ├── BoundingBoxRenderer (NEW, with track ID persistence)
    ├── BallRenderer (NEW)
    ├── PitchRenderer (NEW)
    └── RadarRenderer (existing, reused)

State:
├── frames: FrameBuffer (last N frames)
├── confidenceThreshold: number
├── trackMap: Map<trackId, lastSeen>
├── visibleLayers: {players, ball, pitch, radar}
└── isRecording: boolean
```

---

## 📋 Updated Implementation Checklist

### Phase 1: Backend Endpoints (Week 1)
- [ ] Add `/plugins/{id}/manifest` endpoint
- [ ] Add `/plugins/{id}/tools/{tool}/run` endpoint
- [ ] Add ManifestCacheService
- [ ] CPU-only tests (mocked plugin)
- [ ] Error handling + documentation

### Phase 2: Web-UI Core (Week 2)
- [ ] Add `useVideoProcessor` hook (frame extraction + buffer)
- [ ] Add `useManifest` hook (manifest caching)
- [ ] Add `ToolSelector` component
- [ ] Add `ConfidenceSlider` component (NEW)
- [ ] Add `OverlayToggles` component (NEW)
- [ ] Add `ResultOverlay` component (updated: track persistence, multi-layer)
- [ ] Add `VideoTracker` page (orchestrates above)
- [ ] CPU-only tests for all

### Phase 3: Video Export (Week 2.5)
- [ ] Add `RecordButton` component with MediaRecorder
- [ ] Capture canvas + audio from video element
- [ ] Export as WebM/MP4
- [ ] Test export flow

### Phase 4: Integration Tests (Week 3)
- [ ] Backend: Test real plugin tool execution (CPU mocks)
- [ ] Backend: Test video stream with real YOLO (GPU)
- [ ] Web-UI: End-to-end integration test
- [ ] Export: Test annotated video output

### Phase 5: Polish & Motion_Detector (Week 4)
- [ ] Motion_detector WebSocket streaming
- [ ] Performance profiling
- [ ] FPS slider refinement
- [ ] Track fade-out animation

---

## 🎬 Enhanced Execution Flow (Real-Time Video)

```
1. User uploads video → VideoTracker page
2. SelectPlugin → ToolSelector shows tools from manifest
3. SelectTool (e.g., player_tracking)
4. Adjust ConfidenceSlider (default 0.25)
5. Enable/disable OverlayToggles
6. Click "Start Processing"
7. Frames extracted at 2 FPS:
   a. Resize to 1280×720
   b. Convert to base64
   c. POST /plugins/{id}/tools/{tool}/run
   d. Result arrives: {detections, track_ids, ...}
   e. Filter detections by confidence threshold
   f. Update trackMap (ID persistence)
   g. Frame stored in ring buffer (last 10)
   h. ResultOverlay renders on canvas:
      - BoundingBoxRenderer (with track IDs, fade old ones)
      - Track persistence: gray out detections older than 2 frames
   i. User sees real-time overlay with boxes + IDs
8. OverlayToggles allow showing/hiding layers
9. Click "Record" → MediaRecorder captures canvas+audio → exports MP4
10. User downloads annotated video
```

---

## 🏗️ Updated File Structure

### Backend (forgesyte/server)
```
app/
├── api.py
├── models.py
├── services/
│   ├── plugin_management_service.py
│   └── manifest_cache_service.py (NEW)
└── tests/
    ├── api/
    │   ├── test_plugins_manifest.py (CPU-only)
    │   └── test_plugins_run.py (CPU-only)
    └── integration/
        └── test_video_stream.py (GPU, RUN_MODEL_TESTS=1)
```

### Web-UI (forgesyte/web-ui)
```
src/
├── api/client.ts
├── hooks/
│   ├── useVideoProcessor.ts (NEW: with frame buffer + track map)
│   ├── useVideoProcessor.test.ts (CPU-only)
│   ├── useManifest.ts (NEW)
│   └── useManifest.test.ts (CPU-only)
├── components/
│   ├── ToolSelector.tsx (NEW)
│   ├── ToolSelector.test.tsx (CPU-only)
│   ├── ConfidenceSlider.tsx (NEW)
│   ├── ConfidenceSlider.test.tsx (CPU-only)
│   ├── OverlayToggles.tsx (NEW)
│   ├── OverlayToggles.test.tsx (CPU-only)
│   ├── ResultOverlay.tsx (UPDATED: multi-layer, track persistence)
│   ├── ResultOverlay.test.tsx (CPU-only)
│   ├── RecordButton.tsx (NEW: MediaRecorder)
│   ├── RecordButton.test.tsx (CPU-only)
│   ├── BoundingBoxRenderer.tsx (NEW)
│   ├── BallRenderer.tsx (NEW)
│   └── PitchRenderer.tsx (NEW)
├── pages/
│   ├── VideoTracker.tsx (NEW)
│   └── VideoTracker.test.tsx (CPU-only)
└── types/
    └── plugin.ts (NEW)
```

---

## ✅ Success Criteria (Updated)

✅ **Backend:**
- `/plugins/{id}/manifest` returns tool schemas
- `/plugins/{id}/tools/{tool}/run` executes tools immediately
- ManifestCacheService caches with 5min TTL
- All endpoints tested (CPU-only, no GPU required)

✅ **Web-UI Core:**
- ToolSelector discovers tools dynamically
- VideoTracker extracts frames, resizes, processes
- ConfidenceSlider filters detections client-side
- OverlayToggles control visibility
- ResultOverlay renders with track ID persistence + fade-out
- Frame buffer maintains last 10 frames
- No hardcoded plugin/tool names

✅ **Video Export:**
- RecordButton captures canvas + audio
- Exports as WebM (or MP4 via browser codec)
- User downloads annotated video

✅ **Integration:**
- Upload video → process frames → view overlays → export MP4
- GPU tests: Real YOLO on 5+ frames (RUN_MODEL_TESTS=1)
- Performance: <500ms per frame on CPU

---

**Next:** Create separate code specification files for each component, ready for implementation.
