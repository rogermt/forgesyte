Absolutely, Roger — here is a **clean, authoritative, commit‑ready Phase 9 Developer Contract** written in the exact tone and structure of your `.ampcode` governance files.

This reflects **only what you actually follow**, not the theoretical plan.  
It becomes the **single source of truth** for Phase 9 expectations.

You can drop this directly into:

```
.ampcode/04_PHASE_NOTES/Phase_9/PHASE_9_DEVELOPER_CONTRACT.md
```

---

# **PHASE 9 — DEVELOPER CONTRACT**  
### *The authoritative, minimal, enforceable specification for Phase 9 implementation.*

This contract defines the **required deliverables**, **permitted deviations**, and **explicit non‑requirements** for Phase 9.  
It reflects the *actual* development plan and supersedes any earlier speculative notes.

---

# 1. **Scope**

Phase 9 focuses on stabilising the API surface, adding essential UI controls, and providing minimal DX support.  
This contract defines the **minimum compliance requirements** that must be met before Phase 9 can be considered complete.

---

# 2. **Required Deliverables (MUST)**

These items are **mandatory**.  
Future phases may rely on them.

---

## **2.1 API Requirements (MUST)**

### Typed response models:
- `AnalyzeResponse`
- `JobStatusResponse`
- `JobResultResponse`

### Required fields (MUST appear in all Phase 9 responses):
- `job_id`
- `device_requested`
- `device_used`
- `fallback`
- `frames: list[Any]`

### Notes:
- `frames` MAY remain untyped (`list[Any]`).
- No separate `FrameModel` is required.
- Endpoints MUST return these typed models.

---

## **2.2 UI Requirements (MUST)**

### Device selector:
- Component: `ConfigPanel.tsx`
- ID: `#device-selector`
- Persistence key: `forgesyte_device_preference`

### Overlay toggles:
- IDs:
  - `#toggle-boxes`
  - `#toggle-labels`
  - `#toggle-pitch`
  - `#toggle-radar`

### FPS slider:
- Component: `ConfigPanel.tsx`
- ID: `#fps-slider`
- Persistence key: `forgesyte_fps_target`

### UI states:
- MUST include loading state for analyze flow
- MUST include error state for analyze failures

---

## **2.3 Developer Experience Requirements (MUST)**

### Example plugin outputs:
- File: `server/app/examples/plugin_outputs.py`
- MUST include:
  - `OCR_EXAMPLE`
  - `TRACKING_EXAMPLE`

### Storybook:
- MUST include **one** Storybook story:
  - Component: `OverlayRenderer`
  - Location: `web-ui/src/stories/`

---

## **2.4 Test Requirements (MUST)**

### Playwright tests MUST cover:
- Device selector persistence
- Overlay toggles existence
- FPS slider existence
- (Optional but recommended) basic rendering sanity check

### Notes:
- Existing test governance is sufficient.
- No new governance rules are required.

---

# 3. **Permitted Deviations (MAY)**

These items are **allowed** and do not violate Phase 9.

---

## **3.1 API Flexibility**
- Returning `frames: list[Any]` is acceptable.
- Plugin outputs MAY remain dynamic.
- Raw dicts MAY be used internally, as long as the final response is typed.

---

## **3.2 UI Flexibility**
- Internal component structure MAY change.
- Additional UI controls MAY be added.
- Styling is not governed.

---

## **3.3 DX Flexibility**
- Only one Storybook story is required.
- Additional stories are optional.
- Plugin outputs may be minimal.

---

# 4. **Explicit Non‑Requirements (WILL NOT DO)**

These items are **not required** for Phase 9 and MUST NOT be assumed by future phases.

---

## **4.1 Schema Drift Detection**
- Schema drift detection in CI is NOT required.
- No baseline schema file will be maintained.

---

## **4.2 Full Storybook Coverage**
- Only one Storybook story is required.
- No requirement to document ConfigPanel, FPSSlider, or toggles.

---

## **4.3 FrameModel**
- No separate `FrameModel` will be created.
- `frames` remain untyped.

---

## **4.4 Additional Governance**
- No new test governance rules will be added.
- Existing governance (test count, assertion count, no unapproved skips) is sufficient.

---

# 5. **Completion Criteria**

Phase 9 is complete when:

- All **Required Deliverables** are implemented  
- All **Playwright tests** pass  
- The **OverlayRenderer Storybook story** exists  
- The API returns the required typed fields  
- UI controls exist with the required IDs  
- Example plugin outputs exist  
- No Phase 9 invariants are broken  

---

# 6. **Contract Status**

This contract is **binding** for Phase 9.  
Future phases (Phase 10+) MUST treat these items as the authoritative Phase 9 baseline.

---

Roger, this is the exact file you can commit.  
If you want, I can also generate:

### 🔹 A Phase 9 README  
### 🔹 A Phase 9 merge checklist (aligned with this contract)  
### 🔹 A Phase 10 kickoff tailored to this contract  

Just tell me what you want next.