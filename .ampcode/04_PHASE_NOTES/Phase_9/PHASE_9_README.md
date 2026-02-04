Roger, here are the two artifacts — **clean, authoritative, and fully aligned with your Phase 9 Developer Contract**.  
They’re written in the exact style your `.ampcode` folder expects and are ready to commit as‑is.

---

# 📘 **PHASE 9 README**  
**File:** `.ampcode/04_PHASE_NOTES/Phase_9/README.md`

```md
# Phase 9 — API Stabilisation + Essential UI Controls + Minimal DX

Phase 9 establishes a stable, typed API surface and introduces the essential UI
controls required for consistent user interaction. It also provides minimal DX
support (example plugin outputs + one Storybook story) and a small set of UI
tests to enforce the Phase 9 contract.

This README reflects the *actual* Phase 9 Developer Contract and supersedes any
earlier speculative notes.

---

## 1. Scope

Phase 9 focuses on:
- Typed API responses with required fields
- Essential UI controls (device selector, overlay toggles, FPS slider)
- Minimal DX support (example plugin outputs, one Storybook story)
- Playwright tests for UI invariants

This is the minimal, stable foundation required for Phase 10.

---

## 2. Required Deliverables

### 2.1 API (Required)
Typed response models:
- `AnalyzeResponse`
- `JobStatusResponse`
- `JobResultResponse`

Required fields (must appear in all Phase 9 responses):
- `job_id`
- `device_requested`
- `device_used`
- `fallback`
- `frames: list[Any]`

Notes:
- `frames` may remain untyped (`list[Any]`).
- No separate `FrameModel` is required.

---

### 2.2 UI (Required)

#### Device Selector
- Component: `ConfigPanel.tsx`
- ID: `#device-selector`
- Persistence key: `forgesyte_device_preference`

#### Overlay Toggles
IDs:
- `#toggle-boxes`
- `#toggle-labels`
- `#toggle-pitch`
- `#toggle-radar`

#### FPS Slider
- Component: `ConfigPanel.tsx`
- ID: `#fps-slider`
- Persistence key: `forgesyte_fps_target`

#### UI States
- Loading state for analyze flow
- Error state for analyze failures

---

### 2.3 Developer Experience (Required)

#### Example Plugin Outputs
File:
```
server/app/examples/plugin_outputs.py
```
Must include:
- `OCR_EXAMPLE`
- `TRACKING_EXAMPLE`

#### Storybook
- One Storybook story for `OverlayRenderer`
- Location: `web-ui/src/stories/`

---

### 2.4 Tests (Required)

Playwright tests must cover:
- Device selector persistence
- Overlay toggles existence
- FPS slider existence
- (Optional) basic rendering sanity check

Existing test governance is sufficient.

---

## 3. Explicit Non‑Requirements

These items are *not* required for Phase 9:
- Schema drift detection in CI
- Full Storybook coverage
- Typed `FrameModel`
- Additional governance rules
- Stories for ConfigPanel, FPSSlider, or toggles

---

## 4. Completion Criteria

Phase 9 is complete when:
- Typed API responses are implemented
- Required UI controls exist with correct IDs
- Example plugin outputs exist
- One Storybook story exists
- Playwright tests pass
- No Phase 9 invariants are broken

---

## 5. Next Phase

Phase 10 builds on this foundation with:
- Real-time insights
- Plugin pipeline upgrades
- Enhanced job model
- Real-time UI components

See `../Phase_10/PHASE_10_KICKOFF.md` for details.
```



