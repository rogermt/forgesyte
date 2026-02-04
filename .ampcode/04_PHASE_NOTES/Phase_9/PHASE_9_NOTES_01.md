Roger, let’s build Phase 9 the way you always run your phases: **explicit structure, deterministic tests, and a migration plan that prevents drift**.  
Below are the four deliverables you asked for — all written in the same Phase‑6/7/8 style so they drop straight into `.ampcode/` without friction.

---

# ⭐ **1. Phase 9 Folder Structure**

Place this under:

```
.ampcode/04_PHASE_NOTES/Phase_9/
```

Recommended structure:

```
Phase_9/
├── PHASE_9_KICKOFF.md
├── PHASE_9_TDD_PLAN.md
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

This mirrors the Phase 6B/7/8 structure:  
- **Kickoff**  
- **TDD plan**  
- **Migration checklist**  
- **Sub‑folders for each subsystem**  

Everything is explicit and reviewable.

---

# ⭐ **2. Phase 9 First Failing Tests (RED Phase)**

These are the *first failing tests* you should write before touching any implementation.  
They define the contract for Phase 9.

Place in:

```
server/tests/phase9/
```

### **Test 1 — API returns typed response model**

`test_api_returns_typed_response.py`

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

### **Test 2 — UI device selector persists**

`test_ui_device_selector_persistence.py`

```python
def test_device_selector_persists_across_sessions(page):
    page.goto("/")

    page.select_option("#device-selector", "gpu")
    page.reload()

    # RED: UI does not persist this yet
    assert page.locator("#device-selector").input_value() == "gpu"
```

---

### **Test 3 — Overlay toggles exist**

`test_ui_overlay_toggles.py`

```python
def test_overlay_toggles_exist(page):
    page.goto("/")

    assert page.locator("#toggle-boxes").is_visible()
    assert page.locator("#toggle-labels").is_visible()
    assert page.locator("#toggle-pitch").is_visible()
    assert page.locator("#toggle-radar").is_visible()
```

---

### **Test 4 — FPS slider exists**

`test_ui_fps_slider.py`

```python
def test_fps_slider_exists(page):
    page.goto("/")
    assert page.locator("#fps-slider").is_visible()
```

---

### **Test 5 — Example plugin outputs available**

`test_example_plugin_outputs.py`

```python
def test_example_plugin_outputs_exist():
    from app.examples import plugin_outputs

    # RED: module does not exist yet
    assert hasattr(plugin_outputs, "OCR_EXAMPLE")
    assert hasattr(plugin_outputs, "TRACKING_EXAMPLE")
```

These tests define the Phase 9 contract.

---

# ⭐ **3. Phase 9 Migration Checklist**

Place in:

```
.ampcode/04_PHASE_NOTES/Phase_9/PHASE_9_MIGRATION_CHECKLIST.md
```

```md
# Phase 9 Migration Checklist

## 1. API Cleanup
- [ ] Create new typed response models (AnalyzeResponse, JobStatusResponse, JobResultResponse)
- [ ] Update `/v1/analyze` to return typed model
- [ ] Update `/v1/job/{id}` to return typed model
- [ ] Remove deprecated fields from legacy endpoints
- [ ] Add job_id, device_requested, device_used, fallback to all responses
- [ ] Update OpenAPI schema
- [ ] Add schema validation tests

## 2. UI Polish
- [ ] Add device selector persistence (localStorage)
- [ ] Add overlay toggles (boxes, labels, pitch, radar)
- [ ] Add FPS slider
- [ ] Add improved error messages
- [ ] Add loading states for job submission
- [ ] Unify video + overlay layout
- [ ] Add UI tests for all new controls

## 3. Developer Experience
- [ ] Add Storybook for OverlayRenderer
- [ ] Add Storybook for VideoTracker
- [ ] Add example plugin outputs
- [ ] Add onboarding updates
- [ ] Add API schema docs

## 4. Governance
- [ ] Ensure test count does not decrease
- [ ] Ensure assertion count does not decrease
- [ ] Ensure no skipped tests without APPROVED comments
- [ ] Ensure no direct DB writes outside metrics writer

## 5. Final Verification
- [ ] All Phase 9 tests passing
- [ ] UI tests passing
- [ ] OpenAPI schema validated
- [ ] Manual smoke test of device selector + toggles + FPS slider
```

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

- A **canonical Phase 9 folder structure**  
- The **first failing tests** to drive the milestone  
- A **migration checklist** that prevents drift  
- A **PR template** that matches your Phase‑8 style  

If you want, I can now generate:

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

