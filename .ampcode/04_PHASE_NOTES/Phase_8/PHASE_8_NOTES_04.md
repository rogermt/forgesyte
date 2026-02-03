Absolutely, Roger — here is **Phase 8 — Step 3**, written in the same authoritative, atomic, governance‑driven style as Steps 1 and 2.  
Step 3 is the **Normalisation Layer**, the backbone that makes overlays, metrics, and plugins consistent.

This is the *exact* doc you would place in:

```
.ampcode/PROJECT_RECOVERY/PHASE_8_STEP_3_TDD.md
```

---

# ⭐ **PHASE_8_STEP_3_TDD.md — Normalisation Layer**  
### *Phase 8 — Step 3: Canonical Normalisation Layer (TDD)*

Phase 8 Step 3 introduces the **canonical normalisation layer** that all plugin outputs must pass through before reaching:

- overlays  
- metrics  
- job results  
- UI  
- downstream tools  

This step ensures ForgeSyte has **one unified schema**, regardless of plugin quirks.

---

# 1. **Purpose of Step 3**

The normalisation layer must:

- convert plugin‑specific outputs → canonical schema  
- validate structure, types, and required fields  
- enforce consistency across all plugins  
- prevent malformed data from reaching overlays or metrics  
- provide predictable, testable output for the UI  

This is the **data contract** for the entire system.

---

# 2. **TDD Cycle for Step 3**

## **RED → First failing test**

### Test file:
```
server/tests/normalisation/test_normalisation_basic.py
```

### Test:
- `test_normalisation_produces_canonical_schema`

### Assertions:
- output contains: `boxes`, `scores`, `labels`
- `boxes` is a list of dicts with keys `{x1, y1, x2, y2}`
- `scores` is a list of floats
- `labels` is a list of strings

This test must fail initially.

---

## **GREEN → Minimal implementation**

Create:

```
server/app/schemas/normalisation.py
```

Implement:

- `normalise_output(raw)`  
- minimal transformation to satisfy the test  
- no validation yet  
- no multi‑frame support yet  

---

## **REFACTOR → Introduce validation**

Add:

- type validation  
- shape validation  
- coordinate validation  
- score validation  
- label validation  

Add new tests:

- `test_normalisation_rejects_missing_fields`
- `test_normalisation_rejects_invalid_types`
- `test_normalisation_rejects_invalid_coordinates`

---

# 3. **Step 3 Test Suite**

Place in:

```
server/tests/normalisation/
```

### **3.1 Basic schema tests**
- `test_normalisation_produces_canonical_schema`
- `test_normalisation_boxes_are_dicts`
- `test_normalisation_scores_are_floats`
- `test_normalisation_labels_are_strings`

### **3.2 Validation tests**
- `test_normalisation_rejects_missing_fields`
- `test_normalisation_rejects_invalid_types`
- `test_normalisation_rejects_invalid_coordinates`
- `test_normalisation_rejects_negative_scores`
- `test_normalisation_rejects_empty_outputs`

### **3.3 Multi‑frame tests**
- `test_normalisation_handles_multi_frame_outputs`
- `test_normalisation_preserves_frame_index`
- `test_normalisation_validates_each_frame_individually`

### **3.4 Plugin‑specific tests**
(These ensure plugins conform to the canonical schema.)

- `test_ocr_output_normalises_correctly`
- `test_pose_output_normalises_correctly`
- `test_ball_tracking_normalises_correctly`

---

# 4. **Canonical Schema Definition**

This belongs in:

```
.ampcode/04_PHASE_NOTES/Phase_8/PHASE_8_NORMALISATION_SCHEMA.md
```

### Canonical schema:

```
{
  "frames": [
    {
      "frame_index": int,
      "boxes": [
        { "x1": float, "y1": float, "x2": float, "y2": float }
      ],
      "scores": [float],
      "labels": [string]
    }
  ]
}
```

### Rules:

- All plugins must output **frames**, even if only one frame exists  
- Boxes must be **absolute pixel coordinates**  
- Scores must be **0–1 floats**  
- Labels must be **strings**  
- Missing fields → validation error  
- Extra fields → ignored or stripped  

---

# 5. **CI Guardrails for Step 3**

Add a CI script:

```
ci/test_normalisation_guardrails.py
```

### Guardrails:

- All plugin outputs must pass `normalise_output()`  
- No plugin may return raw, unnormalised data  
- Normalisation errors must fail CI  
- Normalisation schema must match `.ampcode` spec  
- No plugin‑specific normalisation logic allowed outside `normalisation.py`

This prevents drift and plugin‑specific hacks.

---

# 6. **Integration Points**

After Step 3 is complete:

- job pipeline → normalisation  
- plugin wrapper → normalisation  
- overlay renderer → consumes normalised schema  
- metrics writer → uses normalised schema  
- UI → receives normalised schema  

This step unlocks Step 4 (Overlays) and Step 5 (Performance).

---

# 7. **Exit Criteria for Step 3**

- All Step 3 tests green  
- Normalisation layer implemented  
- Validation implemented  
- Multi‑frame support implemented  
- CI guardrails active  
- `.ampcode` schema matches runtime schema  
- All plugins updated to use normalisation  
- No plugin returns raw output  

Once these are met, Step 3 is complete and Step 4 (Overlay Renderer) is unblocked.

---

Got it, Roger — **from now on, all Phase 8 docs live ONLY in:**

```
/home/rogermt/forgesyte/.ampcode/04_PHASE_NOTES/Phase_8/
```

No more `PROJECT_RECOVERY` references.  
No drift.  
No ambiguity.  
Locked.

Below are the five things you asked for, written in your exact Phase‑7/Phase‑8 governance style.

---

# ⭐ **1. Step 4 Docs — Overlay Renderer TDD**  
`/home/rogermt/forgesyte/.ampcode/04_PHASE_NOTES/Phase_8/PHASE_8_STEP_4_TDD.md`

```md
# Phase 8 — Step 4 TDD
## Overlay Renderer (Unified, Deterministic, Plugin-Agnostic)

### Purpose
Create a single, canonical overlay renderer in the Web UI that consumes the normalised schema and renders:
- bounding boxes
- labels
- track IDs
- pitch lines
- radar overlays

### TDD Cycle

## 1. RED — First failing test
File: web-ui/src/components/__tests__/overlay/test_overlay_renders_boxes.tsx

Test:
- Given normalised detections, OverlayRenderer renders SVG rects with correct coordinates.

## 2. GREEN — Minimal implementation
- Create OverlayRenderer.tsx
- Render `<svg>` with `<rect>` for each box
- No styling, no labels, no transforms yet

## 3. REFACTOR — Add features incrementally
Tests:
- test_overlay_renders_labels
- test_overlay_renders_track_ids
- test_overlay_respects_toggles
- test_overlay_renders_pitch_lines
- test_overlay_renders_radar

## 4. Integration tests
- VideoTracker uses OverlayRenderer
- OverlayRenderer receives normalised frames
- OverlayRenderer logs render_time_ms → DuckDB

### Exit Criteria
- All overlay tests green
- OverlayRenderer is the only overlay code path
- No plugin-specific overlay logic in UI
```

---

# ⭐ **2. Step 5 Docs — FPS + Performance Controls**  
`/home/rogermt/forgesyte/.ampcode/04_PHASE_NOTES/Phase_8/PHASE_8_STEP_5_TDD.md`

```md
# Phase 8 — Step 5 TDD
## FPS Throttling + Performance Controls

### Purpose
Ensure overlays render smoothly and deterministically across devices.

### TDD Cycle

## 1. RED — First failing test
File: web-ui/src/components/__tests__/performance/test_fps_throttling.ts

Test:
- When FPS limit = 15, renderer never exceeds 15 frames/sec.

## 2. GREEN — Minimal implementation
- Add requestAnimationFrame loop with timestamp gating
- Add fpsLimit prop to OverlayRenderer

## 3. REFACTOR — Add frame skipping
Tests:
- test_frame_skipping_occurs_when_render_slow
- test_render_time_logged_to_metrics

## 4. Integration tests
- VideoTracker passes fpsLimit from UI
- DuckDB receives overlay_metrics rows

### Exit Criteria
- Stable FPS under load
- No dropped frames unless expected
- Overlay metrics logged
```

---

# ⭐ **3. Step 6 Docs — Device Selector**  
`/home/rogermt/forgesyte/.ampcode/04_PHASE_NOTES/Phase_8/PHASE_8_STEP_6_TDD.md`

```md
# Phase 8 — Step 6 TDD
## Device Selector (CPU/GPU + Fallback Logging)

### Purpose
Allow users to choose CPU/GPU and log fallback behaviour.

### TDD Cycle

## 1. RED — First failing test
File: server/tests/device_selector/test_device_selector_propagates.py

Test:
- When device="gpu", run_job receives device="gpu".

## 2. GREEN — Minimal implementation
- Add device param to /v1/analyze
- Pass through job pipeline

## 3. REFACTOR — Add fallback logic
Tests:
- test_gpu_failure_falls_back_to_cpu
- test_fallback_logged_with_job_id
- test_device_usage_metric_written

## 4. Integration tests
- UI → API → pipeline → plugin → metrics

### Exit Criteria
- Device selector works end-to-end
- Fallback logged with correlation IDs
- DuckDB device_usage table populated
```

---

# ⭐ **4. Canonical Normalisation Schema File**  
`/home/rogermt/forgesyte/.ampcode/04_PHASE_NOTES/Phase_8/PHASE_8_NORMALISATION_SCHEMA.md`

```md
# Canonical Normalisation Schema (Phase 8)

All plugin outputs MUST normalise to this schema.

{
  "frames": [
    {
      "frame_index": int,
      "boxes": [
        { "x1": float, "y1": float, "x2": float, "y2": float }
      ],
      "scores": [float],
      "labels": [string]
    }
  ]
}

### Rules
- frames[] always present (even for single-frame plugins)
- boxes use absolute pixel coordinates
- scores ∈ [0, 1]
- labels are strings
- Missing fields → validation error
- Extra fields → ignored
- Multi-frame plugins must preserve frame_index
```

---

# ⭐ **5. First Failing Test for Step 3 (Normalisation)**  
`server/tests/normalisation/test_normalisation_basic.py`

```python
from server.app.schemas.normalisation import normalise_output
import pytest

def test_normalisation_produces_canonical_schema():
    raw = {
        "boxes": [[10, 20, 30, 40]],
        "scores": [0.9],
        "labels": ["player"]
    }

    out = normalise_output(raw)

    assert "frames" in out, "Normalised output must contain frames[]"
    assert len(out["frames"]) == 1

    frame = out["frames"][0]

    assert "boxes" in frame
    assert "scores" in frame
    assert "labels" in frame

    box = frame["boxes"][0]
    assert set(box.keys()) == {"x1", "y1", "x2", "y2"}, "Boxes must be dicts with canonical keys"
```

This test **must fail** until you implement the minimal normalisation layer.


