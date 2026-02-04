Absolutely, Roger — let’s build Phase 9 the way you run your repo: **explicit, deterministic, mechanically governed, and impossible to drift**.  
Below are the two artifacts you asked for, written in the same style as your Phase 6B/7/8 governance system.

These drop directly into:

```
.ampcode/04_PHASE_NOTES/Phase_9/
```

---

# ⭐ **PHASE 9 IMPLEMENTATION PLAN**  
File: `PHASE_9_IMPLEMENTATION_PLAN.md`

```md
# Phase 9 — Implementation Plan
## API Cleanup + UX Polish + Developer Experience

Phase 9 is intentionally smaller than Phase 8.  
It focuses on stabilising the public API, improving UI ergonomics, and enhancing developer experience.

This plan defines the exact implementation order, the RED→GREEN→REFACTOR cycles, and the atomic deliverables required to complete the milestone.

---

# 1. Implementation Order

## 1.1 Step 1 — API Cleanup (Backend)
### RED
- Add failing tests for:
  - AnalyzeResponse model
  - JobStatusResponse model
  - JobResultResponse model
  - Required fields: job_id, device_requested, device_used, fallback, frames
  - Removal of deprecated fields
  - OpenAPI schema correctness

### GREEN
- Introduce new Pydantic models
- Update `/v1/analyze` to return typed model
- Update `/v1/job/{id}` to return typed model
- Remove legacy fields
- Add missing fields to all responses

### REFACTOR
- Consolidate response models
- Remove dead code paths
- Improve schema documentation
- Add schema validation tests

---

## 1.2 Step 2 — UI Polish (Frontend)
### RED
- Add failing Playwright tests for:
  - Device selector persistence
  - Overlay toggles (boxes, labels, pitch, radar)
  - FPS slider
  - Improved error messages
  - Loading states
  - Unified video + overlay layout

### GREEN
- Implement minimal UI changes
- Wire up new API fields
- Add toggles + slider
- Add loading indicators
- Improve error handling

### REFACTOR
- Extract reusable components
- Improve layout consistency
- Add Storybook entries

---

## 1.3 Step 3 — Developer Experience
### RED
- Add failing tests for:
  - Example plugin outputs
  - Storybook rendering
  - API schema docs generation

### GREEN
- Add example plugin outputs
- Add Storybook stories
- Add schema docs

### REFACTOR
- Clean up folder structure
- Improve onboarding docs

---

# 2. Deliverables

## Backend
- Typed API response models
- Cleaned OpenAPI schema
- Removal of deprecated fields
- Consistent response shapes across all endpoints

## Frontend
- Device selector persistence
- Overlay toggles
- FPS slider
- Improved error and loading states
- Unified video + overlay layout

## Developer Experience
- Storybook for core components
- Example plugin outputs
- Updated onboarding
- API schema documentation

---

# 3. Exit Criteria

Phase 9 is complete when:
- All API responses are typed, stable, and documented
- UI includes device selector, overlay toggles, FPS slider, improved UX
- Storybook is available for core components
- Example plugin outputs exist and are used in tests
- No legacy endpoints or inconsistent response shapes remain
- All Phase 9 tests pass (backend + UI)
```

---

# ⭐ **PHASE 9 GOVERNANCE RULES**  
File: `PHASE_9_GOVERNANCE_RULES.md`

```md
# Phase 9 — Governance Rules
## API Stability + UI Consistency + Developer Experience

Phase 9 introduces governance rules to prevent drift, enforce consistency, and ensure that all API and UI changes are explicit, reviewable, and mechanically validated.

---

# 1. API Governance

## 1.1 Typed Response Enforcement
- All API responses MUST use typed Pydantic models.
- No endpoint may return raw dicts.
- All responses MUST include:
  - job_id
  - device_requested
  - device_used
  - fallback
  - frames (normalised)

## 1.2 Schema Governance
- OpenAPI schema MUST be valid and complete.
- All fields MUST have descriptions.
- Deprecated fields MUST be removed.
- Schema drift tests MUST pass.

## 1.3 Backwards Compatibility
- No breaking changes without:
  - explicit migration notes
  - version bump
  - test coverage

---

# 2. UI Governance

## 2.1 Device Selector
- Device selector MUST persist across reloads.
- Device selector MUST default to CPU if no preference exists.

## 2.2 Overlay Toggles
- All toggles MUST be present:
  - boxes
  - labels
  - pitch
  - radar
- Toggles MUST be wired to overlay renderer.

## 2.3 FPS Slider
- FPS slider MUST exist and control throttling.

## 2.4 Error + Loading States
- All job submissions MUST show loading state.
- All errors MUST show user-friendly messages.

---

# 3. Developer Experience Governance

## 3.1 Storybook
- All UI components MUST have Storybook entries.
- OverlayRenderer and VideoTracker MUST have interactive stories.

## 3.2 Example Plugin Outputs
- Example outputs MUST exist for:
  - OCR
  - Tracking
  - Radar
- Tests MUST use example outputs.

## 3.3 Onboarding
- Onboarding docs MUST be updated to reflect:
  - new API models
  - new UI controls
  - new DX tools

---

# 4. Test Governance

## 4.1 Test Count
- Test file count MUST NOT decrease.
- Assertion count MUST NOT decrease.

## 4.2 Skipped Tests
- Skipped tests MUST include:
  - `# APPROVED:` comment
  - justification

## 4.3 No Silent Changes
- Any test change MUST include:
  - `TEST-CHANGE:` justification in commit message

---

# 5. CI Governance

## 5.1 Required Checks
- Backend tests
- UI tests
- Mypy
- Pre-commit
- Schema validation
- Storybook build

## 5.2 No Direct DB Writes
- Only metrics writer may write to DuckDB.
- All other DB writes MUST fail CI.

---

# 6. Exit Criteria

Phase 9 governance is satisfied when:
- All governance rules pass in CI
- No skipped tests without approval
- No schema drift
- No API inconsistencies
- No UI regressions
- No DX regressions
```

---

Roger, let’s build Phase 9 the same way you’ve built every milestone so far: **explicit scaffolding, atomic first commits, deterministic RED tests, and a PR template that enforces governance from the first line.**  
This is the full Phase 9 starter pack — drop‑in ready.

---

# ⭐ **1. Phase 9 Folder Scaffolding**

Create:

```
.ampcode/
└── 04_PHASE_NOTES/
    └── Phase_9/
        ├── PHASE_9_KICKOFF.md
        ├── PHASE_9_IMPLEMENTATION_PLAN.md
        ├── PHASE_9_GOVERNANCE_RULES.md
        ├── PHASE_9_MIGRATION_CHECKLIST.md
        ├── api_cleanup/
        │   ├── API_MODELS_REFACTOR.md
        │   ├── ENDPOINTS_TO_REMOVE.md
        │   ├── RESPONSE_MODEL_MATRIX.md
        │   └── OPENAPI_CLEANUP_NOTES.md
        ├── ui_polish/
        │   ├── DEVICE_SELECTOR_NOTES.md
        │   ├── OVERLAY_TOGGLES_SPEC.md
        │   ├── FPS_SLIDER_SPEC.md
        │   └── ERROR_STATES_AND_LOADING.md
        └── developer_experience/
            ├── STORYBOOK_PLAN.md
            ├── EXAMPLE_PLUGIN_OUTPUTS.md
            └── ONBOARDING_UPDATES.md
```

This mirrors Phase 6B/7/8 and keeps everything deterministic and reviewable.

---

# ⭐ **2. Phase 9 First Commits (Atomic, Reviewable, Drift‑Proof)**

These are the **first three commits** you should make — nothing else.

---

## **Commit 1 — Add Phase 9 scaffolding**

```
chore(phase9): add Phase 9 scaffolding and planning documents

- Added Phase_9 folder under .ampcode/04_PHASE_NOTES
- Added kickoff, implementation plan, governance rules, and migration checklist
- Added subfolders for api_cleanup, ui_polish, and developer_experience
- Added placeholder spec files for each subsystem
```

---

## **Commit 2 — Add Phase 9 RED tests (backend + UI + DX)**

```
test(phase9): add initial RED tests for API cleanup, UI polish, and DX improvements

- Added failing tests for typed API responses
- Added failing tests for device selector persistence
- Added failing tests for overlay toggles and FPS slider
- Added failing tests for example plugin outputs
- Added failing tests for Storybook presence
```

---

## **Commit 3 — Add Phase 9 test governance markers**

```
chore(phase9): register Phase 9 tests in governance and CI

- Ensured new tests counted in test file and assertion governance
- Added Phase 9 tests to CI matrix
- Added Phase 9 folder to test discovery
```

These three commits establish the milestone and lock the RED state.

---

# ⭐ **3. Phase 9 RED Tests as Actual Files**

Below are the **exact files** you can drop into your repo.

---

## **File 1: server/tests/phase9/test_api_typed_response.py**

```python
def test_analyze_returns_typed_response(client):
    resp = client.post("/v1/analyze", json={"video_url": "x", "device": "cpu"})
    data = resp.json()

    # RED: these fields do not exist yet
    assert "job_id" in data
    assert "device_requested" in data
    assert "device_used" in data
    assert "fallback" in data
    assert "frames" in data
```

---

## **File 2: server/tests/phase9/test_ui_device_selector.py**

```python
def test_device_selector_persists_across_sessions(page):
    page.goto("/")

    page.select_option("#device-selector", "gpu")
    page.reload()

    # RED: UI does not persist this yet
    assert page.locator("#device-selector").input_value() == "gpu"
```

---

## **File 3: server/tests/phase9/test_ui_overlay_toggles.py**

```python
def test_overlay_toggles_exist(page):
    page.goto("/")

    assert page.locator("#toggle-boxes").is_visible()
    assert page.locator("#toggle-labels").is_visible()
    assert page.locator("#toggle-pitch").is_visible()
    assert page.locator("#toggle-radar").is_visible()
```

---

## **File 4: server/tests/phase9/test_ui_fps_slider.py**

```python
def test_fps_slider_exists(page):
    page.goto("/")
    assert page.locator("#fps-slider").is_visible()
```

---

## **File 5: server/tests/phase9/test_example_plugin_outputs.py**

```python
def test_example_plugin_outputs_exist():
    from app.examples import plugin_outputs

    # RED: module does not exist yet
    assert hasattr(plugin_outputs, "OCR_EXAMPLE")
    assert hasattr(plugin_outputs, "TRACKING_EXAMPLE")
```

---

## **File 6: server/tests/phase9/test_storybook_presence.py**

```python
def test_storybook_build_exists():
    # RED: Storybook not built yet
    import os
    assert os.path.exists("web/storybook-static")
```

These tests define the Phase 9 contract.

---

# ⭐ **4. Phase 9 PR Template**

Place in:

```
.ampcode/04_PHASE_NOTES/Phase_9/PHASE_9_PR_TEMPLATE.md
```

```md
# Phase 9 — API Cleanup + UX Polish

## Summary
This PR implements Phase 9, focusing on API cleanup, UI polish, and developer
experience improvements. It stabilises the public API, improves ergonomics in
the UI, and removes legacy inconsistencies.

---

## What’s Included

### 1. API Cleanup
- Typed response models for analyze, job status, and job results
- Consolidated `/v1/analyze` response shape
- Removed deprecated fields
- Added job_id, device_requested, device_used, fallback to all responses
- Updated OpenAPI schema

### 2. UI Polish
- Device selector persistence
- Overlay toggles (boxes, labels, pitch, radar)
- FPS slider
- Improved error messages
- Loading states for job submission
- Unified video + overlay layout

### 3. Developer Experience
- Storybook for OverlayRenderer + VideoTracker
- Example plugin outputs
- Updated onboarding docs
- API schema documentation

---

## Tests
- Added Phase 9 RED tests for API, UI, and DX
- Updated integration tests
- All tests passing (backend + UI)
- Assertion count maintained or increased

---

## Migration Notes
See `.ampcode/04_PHASE_NOTES/Phase_9/PHASE_9_MIGRATION_CHECKLIST.md`.

---

## Status
Phase 9 is complete and ready for review.
```

---

Roger, this gives you:

- **Phase 9 scaffolding**  
- **Phase 9 first commits**  
- **Phase 9 RED tests**  
- **Phase 9 PR template**  

### Phase 9 GREEN implementation

#### 1. API cleanup (backend)

**Implement typed response models**

Create `app/api/models.py`:

```python
from pydantic import BaseModel
from typing import List, Literal, Any

class Frame(BaseModel):
    index: int
    timestamp_ms: int
    overlays: Any  # refine later

class AnalyzeResponse(BaseModel):
    job_id: str
    device_requested: Literal["cpu", "gpu"]
    device_used: Literal["cpu", "gpu"]
    fallback: bool
    frames: List[Frame]

class JobStatusResponse(BaseModel):
    job_id: str
    status: Literal["pending", "running", "completed", "failed"]

class JobResultResponse(AnalyzeResponse):
    status: Literal["completed", "failed"]
```

**Wire `/v1/analyze` to typed model**

In your analyze handler:

```python
from app.api.models import AnalyzeResponse

@router.post("/v1/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    # existing pipeline call
    result = run_pipeline(...)
    return AnalyzeResponse(
        job_id=result.job_id,
        device_requested=result.device_requested,
        device_used=result.device_used,
        fallback=result.fallback,
        frames=result.frames,
    )
```

Do the same for job status/result endpoints with `JobStatusResponse` and `JobResultResponse`.

---

#### 2. UI polish (frontend)

**Device selector persistence**

In your main UI JS/TS:

```ts
const DEVICE_KEY = "analyze_device";

function initDeviceSelector() {
  const select = document.querySelector("#device-selector") as HTMLSelectElement;
  const saved = window.localStorage.getItem(DEVICE_KEY) || "cpu";
  select.value = saved;
  select.addEventListener("change", () => {
    window.localStorage.setItem(DEVICE_KEY, select.value);
  });
}
```

Call `initDeviceSelector()` on page load.

**Overlay toggles + FPS slider**

Add controls in HTML:

```html
<input type="checkbox" id="toggle-boxes">
<input type="checkbox" id="toggle-labels">
<input type="checkbox" id="toggle-pitch">
<input type="checkbox" id="toggle-radar">
<input type="range" id="fps-slider" min="1" max="60" value="30">
```

Wire them into your overlay renderer and throttler:

```ts
overlay.setOptions({
  showBoxes: boxesCheckbox.checked,
  showLabels: labelsCheckbox.checked,
  showPitch: pitchCheckbox.checked,
  showRadar: radarCheckbox.checked,
});

fpsThrottler.setTargetFps(parseInt(fpsSlider.value, 10));
```

**Loading + error states**

Wrap analyze call:

```ts
async function submitJob() {
  setLoading(true);
  clearError();
  try {
    const resp = await fetch("/v1/analyze", { ... });
    if (!resp.ok) throw new Error("Request failed");
    const data = await resp.json();
    renderResult(data);
  } catch (e) {
    showError("Something went wrong while analyzing the video.");
  } finally {
    setLoading(false);
  }
}
```

---

#### 3. Developer experience

**Example plugin outputs**

Create `app/examples/plugin_outputs.py`:

```python
OCR_EXAMPLE = {
    "frames": [
        {"index": 0, "timestamp_ms": 0, "overlays": [...]},
    ]
}

TRACKING_EXAMPLE = {
    "frames": [
        {"index": 0, "timestamp_ms": 0, "overlays": [...]},
    ]
}
```

**Storybook**

Add stories for `OverlayRenderer` and `VideoTracker` in `web/.storybook` or `web/src/stories`:

```tsx
export const BasicOverlay = () => (
  <OverlayRenderer frames={exampleFrames} options={{ showBoxes: true }} />
);
```

---

### Phase 9 REFACTOR steps

#### 1. API models

- **Consolidate** duplicated response shapes into shared base classes (e.g. `BaseJobResponse`).
- **Remove** any legacy response dict construction; always use Pydantic models.
- **Inline** any now-redundant serializers.

#### 2. UI components

- **Extract** `DeviceSelector`, `OverlayControls`, `FpsSlider`, `ErrorBanner`, `LoadingSpinner` into separate components.
- **Normalize props** so they all consume the same typed API response shape.
- **Clean up layout**: single “Video + Overlay + Controls” container.

#### 3. DX

- **Move** example outputs into a dedicated `examples/` package.
- **Refine** types for overlays and frames.
- **Tighten** Storybook stories to cover edge cases (no frames, many frames, error states).

---

### Phase 9 CI guardrails

Add/extend scripts/hooks so they enforce Phase 9 invariants:

#### 1. API invariants

- **Schema check step** in CI:
  - Run `pytest` test that loads OpenAPI schema and asserts:
    - `/v1/analyze` response contains required fields.
    - No deprecated fields present.
- **Static check**:
  - Grep for `return {` in API handlers and fail if found (force Pydantic models).

#### 2. UI invariants

- **Playwright suite** must include:
  - Device selector persistence test.
  - Overlay toggles visibility test.
  - FPS slider presence test.
- CI fails if any Phase 9 UI test is skipped without `APPROVED` tag.

#### 3. DX invariants

- **Storybook build** step:
  - `npm run build-storybook` (or equivalent) must succeed.
- **Example outputs**:
  - Test that imports `app.examples.plugin_outputs` and asserts required symbols exist.

#### 4. Global governance

- Keep existing:
  - **Test file count** must not decrease.
  - **Assertion count** must not decrease.
  - **No skipped tests without APPROVED comment.**
- Add Phase 9‑specific label/check:
  - PRs touching API or UI must reference Phase 9 and link to the relevant `.ampcode` notes.

