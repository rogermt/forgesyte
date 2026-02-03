# ⭐ **3. Phase 9 Kickoff Plan (API cleanup + UX polish)**  
Place in:

```
.ampcode/04_PHASE_NOTES/Phase_9/PHASE_9_KICKOFF.md
```

```md
# Phase 9 — API Cleanup + UX Polish
## Kickoff Plan

Phase 9 focuses on stabilising the public API, improving UI ergonomics,
and removing legacy inconsistencies introduced before Phase 6.

---

# 1. Goals

## 1.1 API Cleanup
- Consolidate `/v1/analyze` request/response models
- Remove unused fields from legacy endpoints
- Introduce typed response models for:
  - job submission
  - job status
  - job results
- Ensure all API responses include:
  - job_id
  - device_requested
  - device_used
  - fallback
  - normalised frames

## 1.2 UI Polish
- Device selector dropdown
- Overlay toggles (boxes, labels, pitch, radar)
- FPS slider
- Improved error messages
- Loading states for job submission
- Unified video + overlay layout

## 1.3 Developer Experience
- Add Storybook for OverlayRenderer + VideoTracker
- Add API schema docs (OpenAPI cleanup)
- Add example plugin outputs for testing

---

# 
