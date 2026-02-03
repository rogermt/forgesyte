# Phase 8 — Step 4 TDD
## Overlay Renderer (Unified, Deterministic, Plugin-Agnostic)

**Status:** Planned  
**Depends on:** Step 3 (Normalisation) ✅ Complete  
**Unlocks:** Step 5 (FPS controls)

---

## Purpose

Create a single, canonical overlay renderer in the Web UI that consumes the normalised schema and renders:
- ✅ Bounding boxes
- ✅ Labels
- ✅ Track IDs
- ✅ Pitch lines
- ✅ Radar overlays

All rendering must be **plugin-agnostic** and deterministic.

---

## TDD Cycle

### 1. RED — First Failing Test

**File:** `web-ui/src/components/__tests__/overlay/OverlayRenderer.test.tsx`

**Test:**
```tsx
test('renders bounding boxes with correct coordinates', () => {
  const normalised = {
    frames: [
      {
        frame_index: 0,
        boxes: [{ x1: 10, y1: 20, x2: 30, y2: 40 }],
        scores: [0.95],
        labels: ['player']
      }
    ]
  };

  render(<OverlayRenderer data={normalised} width={640} height={480} />);
  
  const rect = screen.getByRole('graphics-symbol');
  expect(rect).toHaveAttribute('x', '10');
  expect(rect).toHaveAttribute('y', '20');
  expect(rect).toHaveAttribute('width', '20');
  expect(rect).toHaveAttribute('height', '20');
});
```

This test **must fail** initially (component doesn't exist).

---

### 2. GREEN — Minimal Implementation

**File:** `web-ui/src/components/OverlayRenderer.tsx`

**Minimal code:**
```tsx
import React from 'react';

interface NormalisedFrame {
  frame_index: number;
  boxes: Array<{ x1: number; y1: number; x2: number; y2: number }>;
  scores: number[];
  labels: string[];
}

interface OverlayRendererProps {
  data: { frames: NormalisedFrame[] };
  width: number;
  height: number;
}

export const OverlayRenderer: React.FC<OverlayRendererProps> = ({
  data,
  width,
  height
}) => {
  const frame = data.frames[0]; // Single frame for now
  
  return (
    <svg width={width} height={height} style={{ position: 'absolute' }}>
      {frame.boxes.map((box, i) => (
        <rect
          key={i}
          x={box.x1}
          y={box.y1}
          width={box.x2 - box.x1}
          height={box.y2 - box.y1}
          fill="none"
          stroke="blue"
          strokeWidth="2"
        />
      ))}
    </svg>
  );
};
```

**Goal:** Make the test pass with minimal code.

---

### 3. REFACTOR — Add Features Incrementally

**Implementation Note:** Labels + toggles were added in a single REFACTOR commit instead of incremental commits. Tests still cover each feature independently (9 tests total, see `OverlayRenderer.test.tsx`). This batching decision maintained test isolation while reducing commit overhead.

**Additional tests:**

#### Test: Renders labels
```tsx
test('renders labels inside boxes', () => {
  // ... normalised data ...
  const text = screen.getByText('player');
  expect(text).toBeInTheDocument();
});
```

#### Test: Respects toggles
```tsx
test('hides boxes when toggle is off', () => {
  render(<OverlayRenderer ... showBoxes={false} />);
  // boxes should not render
});
```

#### Test: Renders track IDs
```tsx
test('renders track IDs if present', () => {
  // Add track_id to schema for future support
});
```

#### Test: Renders pitch lines
```tsx
test('renders pitch lines when enabled', () => {
  // Separate logic for pitch detection
});
```

#### Test: Renders radar
```tsx
test('renders radar overlay', () => {
  // Radar as optional feature
});
```

---

### 4. Integration Tests

**File:** `web-ui/src/components/__tests__/integration/VideoTracker.integration.test.tsx`

#### Test: VideoTracker uses OverlayRenderer
```tsx
test('VideoTracker delegates rendering to OverlayRenderer', () => {
  const job = { id: 'job-1', frames: [...] };
  render(<VideoTracker job={job} />);
  
  // OverlayRenderer should be rendered
  expect(screen.getByRole('graphics-symbol')).toBeInTheDocument();
});
```

#### Test: Receives normalised frames
```tsx
test('OverlayRenderer receives normalised frames from job pipeline', () => {
  const normalised = normalise_output(raw_plugin_output);
  const { container } = render(<OverlayRenderer data={normalised} ... />);
  
  const svg = container.querySelector('svg');
  expect(svg).toBeInTheDocument();
});
```

#### Test: Logs render time
```tsx
test('logs render_time_ms to metrics', () => {
  const start = performance.now();
  render(<OverlayRenderer ... />);
  const duration = performance.now() - start;
  
  // Emit to DuckDB (via WebSocket)
  expect(metricsWriter.write_overlay_metric).toHaveBeenCalled();
});
```

---

## Exit Criteria

✅ All overlay tests green  
✅ OverlayRenderer is the only overlay code path (centralised)  
✅ No plugin-specific overlay logic in UI  
✅ Renders boxes, labels, toggles functional  
✅ Optional: track IDs, pitch lines, radar  
✅ Render time logged to metrics  

Once these criteria are met, Step 4 is complete and **Step 5 (FPS controls)** is unblocked.

---

## Architecture Notes

**Why centralise?**
- Prevents plugin-specific rendering logic in UI
- Makes overlay logic testable and deterministic
- Enables consistent styling across all plugins
- Simplifies metrics collection

**What OverlayRenderer consumes:**
- Normalised output from `app.schemas.normalisation`
- Canvas dimensions (width, height)
- Toggle flags (showBoxes, showLabels, showPitch, etc.)

**What OverlayRenderer emits:**
- SVG overlay on top of video frame
- Render time metrics → DuckDB
