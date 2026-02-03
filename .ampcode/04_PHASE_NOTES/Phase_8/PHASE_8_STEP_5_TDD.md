# Phase 8 — Step 5 TDD
## FPS Throttling + Performance Controls

**Status:** Planned  
**Depends on:** Step 4 (Overlay Renderer) → Must use OverlayRenderer  
**Unlocks:** Step 6 (Device Selector)

---

## Purpose

Ensure overlays render smoothly and deterministically across devices:
- ✅ FPS capping (target: 30 FPS on video, 60 FPS on static)
- ✅ Frame skipping when render time exceeds budget
- ✅ Performance metrics → DuckDB
- ✅ No jank, no dropped frames (unless intentional)

---

## TDD Cycle

### 1. RED — First Failing Test

**File:** `web-ui/src/components/__tests__/performance/FPSThrottler.test.ts`

**Test:**
```ts
test('respects fpsLimit of 15 fps', () => {
  const throttler = new FPSThrottler(15);
  const timestamps: number[] = [];
  
  for (let i = 0; i < 30; i++) {
    throttler.throttle(() => {
      timestamps.push(performance.now());
    });
    // Simulate 33ms per frame (30 FPS supply)
    jest.advanceTimersByTime(33);
  }
  
  // Calculate actual FPS
  const deltas = timestamps.slice(1).map((t, i) => t - timestamps[i]);
  const avgDelta = deltas.reduce((a, b) => a + b) / deltas.length;
  const actualFps = 1000 / avgDelta;
  
  expect(actualFps).toBeLessThanOrEqual(15);
  expect(actualFps).toBeGreaterThan(14); // Some tolerance
});
```

This test **must fail** (throttler doesn't exist).

---

### 2. GREEN — Minimal Implementation

**File:** `web-ui/src/utils/FPSThrottler.ts`

**Minimal code:**
```ts
export class FPSThrottler {
  private lastFrameTime = 0;
  private frameInterval: number;
  
  constructor(maxFps: number) {
    this.frameInterval = 1000 / maxFps;
  }
  
  throttle(callback: () => void): void {
    const now = performance.now();
    
    if (now - this.lastFrameTime >= this.frameInterval) {
      callback();
      this.lastFrameTime = now;
    }
  }
}
```

**Goal:** Make test pass with minimal frame-skipping logic.

---

### 3. REFACTOR — Add Metrics + Frame Skipping

**Additional tests:**

#### Test: Skips frames when render is slow
```ts
test('skips frames when render time exceeds budget', () => {
  const throttler = new FPSThrottler(30, { renderBudget: 10 });
  const renderedFrames: number[] = [];
  
  let frameNum = 0;
  throttler.throttle(() => {
    renderedFrames.push(frameNum);
    // Simulate slow render (15ms, exceeds 10ms budget)
    jest.advanceTimersByTime(15);
  });
  
  frameNum++;
  throttler.throttle(() => {
    renderedFrames.push(frameNum);
  });
  
  // Second frame should be skipped (still within interval)
  expect(renderedFrames).toEqual([0]); // Only first frame rendered
});
```

#### Test: Reports metrics
```ts
test('emits render metrics', () => {
  const metrics = [];
  const throttler = new FPSThrottler(30, {
    onMetric: (m) => metrics.push(m)
  });
  
  throttler.throttle(() => {
    // Fast render
  });
  
  expect(metrics).toContainEqual({
    render_time_ms: expect.any(Number),
    dropped_frames: 0,
    fps: expect.any(Number)
  });
});
```

#### Test: Handles high load gracefully
```ts
test('maintains stable fps under high load', () => {
  const throttler = new FPSThrottler(15);
  
  // Simulate 100 frames at 60 FPS supply
  for (let i = 0; i < 100; i++) {
    throttler.throttle(() => {
      // Heavy computation
      const result = Array(10000).fill(0).reduce((a, b) => a + b);
    });
  }
  
  // Should never exceed 15 FPS
});
```

---

### 4. Integration Tests

**File:** `web-ui/src/components/__tests__/integration/VideoTracker.fps.test.tsx`

#### Test: VideoTracker passes fpsLimit prop
```tsx
test('VideoTracker passes fpsLimit to OverlayRenderer', () => {
  const { rerender } = render(
    <VideoTracker job={job} fpsLimit={30} />
  );
  
  // Should not drop frames at 30 FPS
  jest.advanceTimersByTime(5000); // 5 seconds
  
  // Should render ~150 frames (5s × 30 FPS)
});
```

#### Test: DuckDB receives overlay_metrics
```tsx
test('overlay_metrics written to DuckDB', async () => {
  render(<VideoTracker job={job} />);
  
  // Simulate some frames
  jest.advanceTimersByTime(1000);
  
  // Query metrics
  const metrics = await db.query(
    'SELECT COUNT(*) as count FROM overlay_metrics'
  );
  
  expect(metrics[0].count).toBeGreaterThan(0);
});
```

---

## Exit Criteria

✅ FPS throttling works (test passes)  
✅ Frame skipping occurs under load  
✅ Metrics emitted on every render  
✅ Stable FPS (no jank, no dropped frames unless intended)  
✅ Metrics → DuckDB (overlay_metrics table)  
✅ Performance degradation visible in DuckDB queries  

Once these criteria are met, Step 5 is complete and **Step 6 (Device Selector)** is unblocked.

---

## Performance Targets

| Scenario | Target FPS | Render Budget |
|----------|-----------|--------------|
| Static image (OCR) | 60 | 16ms |
| Video playback | 30 | 33ms |
| Live stream | 24 | 42ms |
| Low-end device | 15 | 67ms |

---

## Metrics Stored in DuckDB

```sql
SELECT
  job_id,
  frame_index,
  render_time_ms,
  dropped_frames,
  fps,
  created_at
FROM overlay_metrics
WHERE job_id = 'job-123'
ORDER BY frame_index;
```

**Usage:** Analyze performance regression, identify bottlenecks, device-specific profiling.
