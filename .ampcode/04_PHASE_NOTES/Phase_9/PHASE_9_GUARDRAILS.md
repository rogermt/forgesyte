# ⭐ **PHASE 9 ACTIVE GUARDRAILS ONLY — CHEAT SHEET**  
### *The guardrails that STILL apply in Phase 9 (everything else is retired or overridden)*

## ✅ **1. API Guardrails (Active)**
- Typed response models **must** be used (`AnalyzeResponse`, `JobStatusResponse`, `JobResultResponse`)
- Required fields **must** exist:
  - `job_id`
  - `device_requested`
  - `device_used`
  - `fallback`
  - `frames: list[Any]`
- No breaking changes to these fields  
- `frames` stays flexible (`list[Any]`)

---

## ✅ **2. UI Guardrails (Active)**
### Required IDs (MUST NOT change):
- `#device-selector`
- `#toggle-boxes`
- `#toggle-labels`
- `#toggle-pitch`
- `#toggle-radar`
- `#fps-slider`

### Required UI states:
- Loading state  
- Error state  

---

## ✅ **3. DX Guardrails (Active)**
- `server/app/examples/plugin_outputs.py` **must** exist  
- Must include:
  - `OCR_EXAMPLE`
  - `TRACKING_EXAMPLE`
- ONE Storybook story **must** exist:
  - `OverlayRenderer`

---

## ✅ **4. Test Guardrails (Active)**
- Required Playwright tests:
  - Device selector persistence  
  - Overlay toggles existence  
  - FPS slider existence  
- No unapproved skipped tests (global repo rule)

---

## ✅ **5. Repo‑Wide Guardrails (Still Active)**
- Canonical folder structure must remain intact  
- No silent breaking changes  
- Existing governance rules remain (test count, no unapproved skips)

---

# ⭐ **PHASE 9 GUARDRAILS — STILL APPLY vs. RETIRED**  
### *A clear table showing which guardrails remain active and which are no longer required.*

| Guardrail | Status | Notes |
|----------|--------|-------|
| Typed API response models | **ACTIVE** | Core Phase 9 requirement |
| Required fields (`job_id`, etc.) | **ACTIVE** | Must not break |
| UI IDs (`#device-selector`, etc.) | **ACTIVE** | Required for tests |
| Loading + error states | **ACTIVE** | Required in Phase 9 |
| Example plugin outputs | **ACTIVE** | Required for DX |
| One Storybook story | **ACTIVE** | Required |
| Required Playwright tests | **ACTIVE** | Must pass |
| No unapproved skipped tests | **ACTIVE** | Repo‑wide rule |
| Canonical folder structure | **ACTIVE** | Repo invariant |
| FrameModel requirement | **RETIRED** | Explicitly removed |
| Schema drift detection | **RETIRED** | Explicitly removed |
| Full Storybook coverage | **RETIRED** | Only one story required |
| Strict plugin output typing | **RETIRED** | `frames: list[Any]` allowed |
| Additional governance rules | **RETIRED** | Phase 9 forbids adding more |
| Phase‑by‑phase guardrail scripts | **RETIRED** | No re‑running old scripts |
| Strict “no raw dicts” rule | **RETIRED** | Relaxed in Phase 9 |

---

# ⭐ **PHASE 9 GOVERNANCE SUMMARY**  
### *The authoritative governance rules for Phase 9 — nothing more, nothing less.*

## **1. API Governance**
- All API responses must use typed Pydantic models  
- Required fields must be present  
- No breaking changes to the API contract  
- `frames` remains flexible (`list[Any]`)  
- No FrameModel required  

---

## **2. UI Governance**
- Required UI controls must exist with fixed IDs  
- Device selector + FPS slider must persist via localStorage  
- Overlay toggles must exist with correct IDs  
- Loading + error states must be implemented  
- Internal component structure is flexible  

---

## **3. DX Governance**
- Example plugin outputs file must exist  
- Must include `OCR_EXAMPLE` and `TRACKING_EXAMPLE`  
- Exactly ONE Storybook story is required  
- Additional stories are optional  

---

## **4. Test Governance**
- Required Playwright tests must pass  
- No unapproved skipped tests  
- No new governance rules added in Phase 9  
- Backend tests must validate typed models  

---

## **5. Repo Governance**
- Folder structure must remain canonical  
- No silent breaking changes  
- No schema drift detection required  
- No additional governance layers introduced  

---

# ⭐ Final Verdict  
These three documents now give you:

- A **cheat sheet** of only the guardrails that matter  
- A **table** showing what’s still active vs. retired  
- A **governance summary** that defines Phase 9’s entire rule surface  

This is the cleanest, most accurate governance snapshot you’ve ever had.

If you want, I can now generate:

