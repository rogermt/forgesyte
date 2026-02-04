Roger, this is **the final, consolidated, contract‑aligned Phase 9 plan** — exactly as the developer (you) will execute it, exactly as the architecture expects it, and exactly as Phase 10 depends on it.

This is the **single source of truth**.  
It merges:

- The Developer Contract  
- The README  
- The Compliance Matrix  
- The Dependency Map  
- Your explicit “I WILL follow / I WILL add / I WILL skip” declarations  
- The attached document you provided  

Nothing is theoretical.  
Nothing is idealised.  
This is the **real Phase 9 plan**.

---

# ⭐ **FINAL PHASE 9 PLAN (Developer‑Aligned, Contract‑Aligned, Architecture‑Aligned)**  
### *This is the authoritative Phase 9 execution plan.*

---

# 1. **WHAT I WILL FOLLOW EXACTLY (Hard Requirements)**  
These come directly from the **Phase 9 Developer Contract** and are **non‑negotiable**.

## ✔ API Requirements  
From *PHASE_9_DEVELOPER_CONTRACT.md — Section 2.1*:

- Implement typed models:
  - `AnalyzeResponse`
  - `JobStatusResponse`
  - `JobResultResponse`
- Include required fields:
  - `job_id`
  - `device_requested`
  - `device_used`
  - `fallback`
  - `frames: list[Any]`
- No FrameModel required  
- `frames` stays flexible (`list[Any]`)
- Update `/v1/analyze`, `/v1/jobs/{id}`, `/v1/jobs/{id}/result` to return typed models

**Status:** WILL FOLLOW EXACTLY

---

## ✔ UI Requirements  
From *PHASE_9_DEVELOPER_CONTRACT.md — Section 2.2*:

### Required UI controls with fixed IDs:
- `#device-selector`
- `#toggle-boxes`
- `#toggle-labels`
- `#toggle-pitch`
- `#toggle-radar`
- `#fps-slider`

### Required persistence keys:
- `forgesyte_device_preference`
- `forgesyte_fps_target`

### Required UI states:
- Loading state  
- Error state  

**Status:** WILL FOLLOW EXACTLY

---

## ✔ Storybook Requirements  
From *Section 2.3*:

- ONE Storybook story is required:
  - `OverlayRenderer.stories.tsx`

**Status:** WILL FOLLOW EXACTLY

---

## ✔ Example Plugin Outputs  
From *Section 2.3*:

- File: `server/app/examples/plugin_outputs.py`
- Must include:
  - `OCR_EXAMPLE`
  - `TRACKING_EXAMPLE`

**Status:** WILL FOLLOW EXACTLY

---

## ✔ Required Playwright Tests  
From *Section 2.4*:

- Device selector persistence  
- Overlay toggles existence  
- FPS slider existence  

**Status:** WILL FOLLOW EXACTLY

---

# 2. **WHAT I WILL ADD (Permitted Deviations — Allowed & Safe)**  
These are **explicitly allowed** by Section 3.2 (“Internal component structure MAY change”).

## ✔ LoadingSpinner.tsx  
- Satisfies required loading state  
- Allowed deviation

## ✔ ErrorBanner.tsx  
- Satisfies required error state  
- Allowed deviation

## ✔ Additional Storybook stories (optional)  
- ConfigPanel  
- DeviceSelector  
- FPSSlider  

Allowed by Section 3.3 (“Additional stories are optional”).

## ✔ TypeScript interfaces for props  
Allowed — internal structure.

## ✔ CSS modules / styled-components  
Allowed — internal structure.

## ✔ ErrorBoundary  
Allowed — internal structure.

## ✔ PropTypes / runtime validation  
Allowed — internal structure.

**Status:** ALL PERMITTED AND SAFE

---

# 3. **WHAT I WILL SKIP (Explicit Non‑Requirements)**  
These are **explicitly listed as NOT required** in Section 4.

## ❌ Schema drift detection  
Not required.

## ❌ FrameModel  
Not required.

## ❌ Full Storybook coverage  
Only one story required.

## ❌ Additional governance rules  
Not required.

## ❌ Extra Playwright tests  
Only the three required tests must be written.

**Status:** ALL SKIPS ARE FULLY COMPLIANT

---

# 4. **WORK STREAMS (Final, Developer‑Aligned)**

## 4.1 API Models  
- Add typed models  
- Update endpoints  
- Keep frames flexible  

## 4.2 UI Components  
- Add device selector  
- Add FPS slider  
- Add overlay toggles  
- Add LoadingSpinner  
- Add ErrorBanner  
- Add persistence  

## 4.3 Developer Experience  
- Add example plugin outputs  
- Add ONE Storybook story  

## 4.4 Tests  
- Add required Playwright tests  
- Add minimal backend tests for typed models  

---

# 5. **FIRST 4 COMMITS (Final)**

### **Commit 1 — Scaffold directories**
```
server/tests/phase9/
server/app/examples/
web-ui/tests/phase9/
web-ui/src/stories/
```

### **Commit 2 — RED tests (backend)**
- Typed model tests

### **Commit 3 — RED tests (frontend)**
- Device selector  
- Overlay toggles  
- FPS slider  

### **Commit 4 — Example plugin outputs**
- `OCR_EXAMPLE`
- `TRACKING_EXAMPLE`

---

# 6. **SUCCESS CRITERIA (Final)**  
Phase 9 is complete when:

- Typed API responses implemented  
- Required UI controls exist with correct IDs  
- Loading + error states implemented  
- Example plugin outputs exist  
- ONE Storybook story exists  
- Required Playwright tests pass  
- No Phase 9 invariants broken  

---

# 7. **PHASE 10 DEPENDENCIES (Final)**  
Phase 10 depends on:

- Typed API models  
- Required fields  
- UI IDs  
- Example plugin outputs  
- Playwright tests  

Phase 10 inherits:

- Flexible frames  
- Minimal governance  
- Optional Storybook coverage  

---

# ⭐ **FINAL VERDICT**  
This is the **final, authoritative Phase 9 plan**.  
It matches:

- What the contract requires  
- What the architecture expects  
- What Phase 10 depends on  
- What you will actually implement  

Nothing is missing.  
Nothing is contradictory.  
Nothing is over‑promised.

Roger — Phase 9 is now fully locked.

