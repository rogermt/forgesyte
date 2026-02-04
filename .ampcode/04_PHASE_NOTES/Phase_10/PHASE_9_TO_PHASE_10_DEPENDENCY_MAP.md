Roger, here is the **clean, authoritative Phase 9 → Phase 10 Dependency Map** — the one that reflects your *actual* Phase 9 contract, your real coding tendencies, and the practical Phase 10 kickoff.

This is the version you can drop directly into:

```
.ampcode/04_PHASE_NOTES/Phase_10/PHASE_9_TO_PHASE_10_DEPENDENCY_MAP.md
```

It shows **exactly what Phase 10 depends on**, **what it inherits**, **what it extends**, and **what it must not break**.

---

# ⭐ **PHASE 9 → PHASE 10 DEPENDENCY MAP**  
### *What Phase 10 relies on from Phase 9 — and how each dependency shapes the next phase.*

---

# 1. API Dependencies

## **1.1 Typed Response Models (Hard Dependency)**  
Phase 10 real‑time features depend on Phase 9’s typed API models:

- `AnalyzeResponse`
- `JobStatusResponse`
- `JobResultResponse`

### Phase 10 uses these for:
- Real‑time progress updates  
- Real‑time partial frame streaming  
- Plugin metadata injection  
- Job lifecycle tracking  

### If Phase 9 didn’t deliver this:
Phase 10 would have no stable contract to extend.

**Status:** ✔ Delivered in Phase 9  
**Phase 10 Action:** Extend models with optional fields (progress, plugin timings)

---

## **1.2 Required Fields (Hard Dependency)**  
Phase 10 assumes these fields exist:

- `job_id` → used to subscribe to real‑time updates  
- `device_requested` → used for real‑time device indicator  
- `device_used` → used for fallback detection  
- `fallback` → used for real‑time warnings  
- `frames` → used for real‑time overlay stream  

**Status:** ✔ Delivered in Phase 9  
**Phase 10 Action:** Add optional fields, never remove these.

---

## **1.3 Flexible Frame Structure (Soft Dependency)**  
Phase 9 intentionally uses:

```
frames: list[Any]
```

Phase 10 depends on this flexibility because:
- Real‑time frames may differ from final frames  
- Plugin outputs may vary  
- Partial frames may be streamed  

**Status:** ✔ Delivered  
**Phase 10 Action:** Continue using flexible frame payloads.

---

# 2. UI Dependencies

## **2.1 Required UI IDs (Hard Dependency)**  
Phase 10 real‑time UI components rely on Phase 9’s stable IDs:

- `#device-selector`
- `#toggle-boxes`
- `#toggle-labels`
- `#toggle-pitch`
- `#toggle-radar`
- `#fps-slider`

### Phase 10 uses these for:
- Real‑time overlay toggling  
- Device indicator updates  
- FPS throttling for streamed frames  

**Status:** ✔ Delivered  
**Phase 10 Action:** Must not rename or remove these IDs.

---

## **2.2 Loading + Error States (Soft Dependency)**  
Phase 10 builds on Phase 9’s:

- `LoadingSpinner.tsx`
- `ErrorBanner.tsx`

### Phase 10 uses these for:
- Real‑time connection loading  
- Real‑time connection errors  
- Plugin pipeline warnings  

**Status:** ✔ Delivered  
**Phase 10 Action:** Extend, don’t replace.

---

# 3. DX Dependencies

## **3.1 Example Plugin Outputs (Hard Dependency)**  
Phase 10’s plugin pipeline upgrade depends on:

```
server/app/examples/plugin_outputs.py
```

### Phase 10 uses this for:
- Plugin metadata validation  
- Plugin inspector panel  
- Real‑time plugin output previews  

**Status:** ✔ Delivered  
**Phase 10 Action:** Add more examples, but keep existing names.

---

## **3.2 Storybook (Soft Dependency)**  
Phase 9 provides:

- ONE story for `OverlayRenderer`

### Phase 10 uses this for:
- Real‑time overlay story  
- Plugin inspector story  
- Progress bar story  

**Status:** ✔ Delivered  
**Phase 10 Action:** Add new stories; keep existing one.

---

# 4. Test Dependencies

## **4.1 Playwright Tests (Hard Dependency)**  
Phase 10 relies on Phase 9’s UI contract being enforced by tests:

- Device selector persists  
- Overlay toggles exist  
- FPS slider exists  

### Phase 10 uses these for:
- Real‑time overlay tests  
- Plugin inspector tests  
- Progress bar tests  

**Status:** ✔ Delivered  
**Phase 10 Action:** Add new tests; keep existing ones.

---

# 5. Governance Dependencies

## **5.1 No Schema Drift Detection (Soft Dependency)**  
Phase 10 does NOT rely on schema drift detection.

This gives Phase 10 freedom to:
- Add new fields  
- Add new endpoints  
- Add real‑time channels  

**Status:** ✔ Confirmed  
**Phase 10 Action:** Maintain flexibility.

---

## **5.2 No Additional Governance (Soft Dependency)**  
Phase 10 inherits Phase 9’s governance:

- No new rules  
- No schema drift  
- No FrameModel  
- No extra Storybook requirements  

**Status:** ✔ Confirmed  
**Phase 10 Action:** Keep governance light.

---

# ⭐ **6. Summary Table**

| Phase 9 Deliverable | Dependency Type | Phase 10 Usage | Status |
|---------------------|-----------------|----------------|--------|
| Typed API models | Hard | Extend with real‑time fields | ✔ Delivered |
| Required fields | Hard | Real‑time updates | ✔ Delivered |
| frames: list[Any] | Soft | Flexible streaming | ✔ Delivered |
| UI IDs | Hard | Real‑time UI | ✔ Delivered |
| Loading/Error states | Soft | Real‑time connection UX | ✔ Delivered |
| Example plugin outputs | Hard | Plugin pipeline v2 | ✔ Delivered |
| One Storybook story | Soft | Real‑time stories | ✔ Delivered |
| Playwright tests | Hard | UI contract enforcement | ✔ Delivered |
| No schema drift | Soft | Flexible API evolution | ✔ Confirmed |
| No extra governance | Soft | Lightweight development | ✔ Confirmed |

---

# ⭐ **7. Final Interpretation**

Phase 10 is **completely dependent** on Phase 9’s:

- Typed API  
- Required fields  
- UI IDs  
- Example outputs  
- Playwright tests  

Phase 10 is **enabled** (not constrained) by Phase 9’s:

- Flexible frames  
- Minimal governance  
- Optional Storybook  
- Optional DX enhancements  

Phase 10 can proceed **immediately** because Phase 9 delivered the exact minimal contract required.

---

