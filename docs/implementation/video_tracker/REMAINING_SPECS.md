# Remaining Specification Files (To Be Created)

Due to length constraints, the following 8 files need to be created following the same pattern as existing specs.

---

## Web-UI Hooks (2 files)

### 1. HOOK_USE_MANIFEST.md
**File:** `forgesyte/web-ui/src/hooks/useManifest.ts`

**What it does:**
- Fetch plugin manifest from backend
- Cache in React context (avoid repeated API calls)
- Clear cache on plugin change
- Handle loading/error states

**Key features:**
- Uses `useEffect` to fetch on plugin_id change
- Stores in context for global access
- Returns `{manifest, loading, error}`
- Caching with optional TTL

**Tests:** CPU-only (mocked API calls)

---

### 2. HOOK_USE_VIDEO_PROCESSOR.md
**File:** `forgesyte/web-ui/src/hooks/useVideoProcessor.ts`

**What it does:**
- Extract frames from `<video>` element
- Convert to base64 (JPEG)
- Maintain ring buffer (last N frames)
- Send frames to backend via `/plugins/run`
- Update track ID map (persistence)
- Filter by confidence threshold

**Key features:**
- `extractFrameBase64(videoElement): string`
- Frame buffer: `FrameBuffer` class (FIFO, max 10)
- Track map: `Map<trackId, {x, y, lastSeen, fadeOut}>`
- Confidence filtering before rendering
- Returns: `{isProcessing, frames, trackMap, error, extractFrameBase64, processFrame}`

**Tests:** CPU-only (mocked API calls)

---

## Web-UI Components (5 files)

### 3. COMPONENT_TOOL_SELECTOR.md
**File:** `forgesyte/web-ui/src/components/ToolSelector.tsx`

**What it does:**
- Discover tools from plugin manifest
- User selects which tool to run
- Show tool description

**Props:**
```typescript
interface ToolSelectorProps {
  pluginId: string;
  selectedTool: string;
  onToolChange: (toolName: string) => void;
  disabled?: boolean;
}
```

**Tests:** CPU-only (mocked manifest)

---

### 4. COMPONENT_CONFIDENCE_SLIDER.md
**File:** `forgesyte/web-ui/src/components/ConfidenceSlider.tsx`

**What it does:**
- Range slider (0.0–1.0)
- User adjusts confidence threshold
- Default: 0.25

**Props:**
```typescript
interface ConfidenceSliderProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
}
```

**Tests:** CPU-only (slider state)

---

### 5. COMPONENT_OVERLAY_TOGGLES.md
**File:** `forgesyte/web-ui/src/components/OverlayToggles.tsx`

**What it does:**
- Checkboxes to toggle: players, ball, pitch, radar
- Update parent state
- Show which layers are visible

**Props:**
```typescript
interface OverlayTogglesProps {
  visibleLayers: {players: boolean, ball: boolean, pitch: boolean, radar: boolean};
  onChange: (layers: object) => void;
}
```

**Tests:** CPU-only (toggle state)

---

### 6. COMPONENT_RESULT_OVERLAY.md
**File:** `forgesyte/web-ui/src/components/ResultOverlay.tsx`

**What it does:**
- Canvas renderer for detections
- Multi-layer rendering (players, ball, pitch, radar)
- Track ID persistence (fade old detections)
- Filter by confidence threshold

**Props:**
```typescript
interface ResultOverlayProps {
  canvas: HTMLCanvasElement;
  frameWidth: number;
  frameHeight: number;
  detections: BoundingBox[];
  trackMap: Map<string, TrackHistory>;
  visibleLayers: {players: boolean, ball: boolean, pitch: boolean, radar: boolean};
  confidenceThreshold: number;
}
```

**Rendering:**
- Draw boxes with labels + confidence
- Color code by track ID (or fade if old)
- Layer composition: pitch → ball → players → radar

**Tests:** CPU-only (canvas mocking, canvas context tests)

---

### 7. COMPONENT_RECORD_BUTTON.md
**File:** `forgesyte/web-ui/src/components/RecordButton.tsx`

**What it does:**
- Start/stop recording video + canvas
- Use MediaRecorder API
- Export as WebM/MP4
- Trigger download

**Props:**
```typescript
interface RecordButtonProps {
  canvas: HTMLCanvasElement;
  videoElement: HTMLVideoElement;
  filename?: string;
}
```

**Logic:**
- Create MediaRecorder for canvas stream + audio
- `ondataavailable` collects chunks
- On stop: create Blob → download

**Tests:** CPU-only (recorder state, blob creation)

---

## Web-UI Page (1 file)

### 8. PAGE_VIDEO_TRACKER.md
**File:** `forgesyte/web-ui/src/pages/VideoTracker.tsx`

**What it does:**
- Main orchestration page
- Combines all above components
- Manages state: plugin, tool, video, frames, tracks
- Handles video upload

**Layout:**
```
[PluginSelector] [ToolSelector] [ConfidenceSlider]
[OverlayToggles] [RecordButton]
[Video Element]
[Results: Frames + Overlay]
```

**State:**
```typescript
const [selectedPlugin, setSelectedPlugin] = useState('');
const [selectedTool, setSelectedTool] = useState('');
const [videoFile, setVideoFile] = useState<File | null>(null);
const [confidenceThreshold, setConfidenceThreshold] = useState(0.25);
const [visibleLayers, setVisibleLayers] = useState({
  players: true, ball: true, pitch: true, radar: false
});
```

**Tests:** CPU-only (component integration)

---

## Web-UI Tests (1 file)

### 9. TESTS_WEBUI_CPU.md
**Files:** 
- `forgesyte/web-ui/src/hooks/useManifest.test.ts`
- `forgesyte/web-ui/src/hooks/useVideoProcessor.test.ts`
- `forgesyte/web-ui/src/components/*.test.tsx`
- `forgesyte/web-ui/src/pages/VideoTracker.test.tsx`

**What to test:**
- Hook state updates
- Component rendering
- Props changes
- User interactions (clicks, inputs)
- API calls (mocked)

**Pattern:** All use vitest + mocking, NO actual API calls

---

## Template for Remaining Files

Each file should follow this structure:

```markdown
# [Title]

**File:** [path]
**Purpose:** [one-liner]
**Status:** Ready to implement

---

## Overview

[What it does, why, key features]

---

## Implementation

[Complete, copy-paste-ready code]

**Location:** [file path]

```typescript
// Full code here
```

[Explanation of key functions/logic]

---

## Testing

[Test file + code]

**Location:** [test file path]

```typescript
// Full test code
```

**Run tests:**
```bash
npm run test -- [file]
```

---

## Props/Types

[Interface definitions]

---

## Related Files

[Links to related specs]
```

---

## Implementation Order

1. **TYPES_PLUGIN.md** ✅ (done)
2. HOOK_USE_MANIFEST.md
3. HOOK_USE_VIDEO_PROCESSOR.md
4. COMPONENT_TOOL_SELECTOR.md
5. COMPONENT_CONFIDENCE_SLIDER.md
6. COMPONENT_OVERLAY_TOGGLES.md
7. COMPONENT_RESULT_OVERLAY.md
8. COMPONENT_RECORD_BUTTON.md
9. PAGE_VIDEO_TRACKER.md
10. TESTS_WEBUI_CPU.md

---

## Quick Start

To create each file:

1. Copy the template structure
2. Replace [Title], [File], [Purpose]
3. Write the complete implementation (copy-paste ready)
4. Write comprehensive tests
5. Add usage examples
6. Link to related files

Each file should be **self-contained** and include:
- Imports
- Types/interfaces
- Complete code (no pseudocode)
- Tests (CPU-only)
- How to run/verify
- Related files

---

## Current Status

✅ Architecture & decisions finalized  
✅ Backend specs complete (5 files done)  
✅ Backend tests specs complete (2 files done)  
✅ Types defined (1 file done)  
⏳ Web-UI hooks & components (8 files remaining)  

---

**Ready to continue with remaining specs?**
