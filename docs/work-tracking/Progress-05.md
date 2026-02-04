# Phase 9 Progress Tracking

**Phase:** 9 - API Typed Responses & UI Controls  
**Started:** 2026-01-12  
**Status:** In Progress  
**Depends on:** Phase 8 (Closed)  
**Unblocks:** Phase 10  

---

## Completed Tasks

### ✅ Task 1: Governance Commit (COMPLETED 2026-01-12)
- **Description:** Stage all Phase 9 Project Governance files
- **Commit:** `e312543`
- **Files Committed:** 18 governance files
  - `.ampcode/03_PLANS/Phase_9/PHASE_9_PLANS.md`
  - `.ampcode/04_PHASE_NOTES/Phase_9/PHASE_9_README.md`
  - `.ampcode/04_PHASE_NOTES/Phase_9/PHASE_9_NOTES_01.md` through `PHASE_9_NOTES_09.md`
  - `.ampcode/04_PHASE_NOTES/Phase_9/PHASE_9_DEVELOPER_CONTRACT.md`
  - `.ampcode/04_PHASE_NOTES/Phase_9/PHASE_9_FINAL_LOCKED_PLAN.md`
  - `.ampcode/04_PHASE_NOTES/Phase_9/PHASE_9_MERGE_CHECKLIST.md`
  - `.ampcode/04_PHASE_NOTES/Phase_9/PHASE-9_DIAGRAMS.md`
  - `.ampcode/04_PHASE_NOTES/Phase_10/PHASE_10_KICKOFF.md`
  - `.ampcode/04_PHASE_NOTES/Phase_10/PHASE_9_TO_PHASE_10_DEPENDENCY_MAP.md`

### ✅ Task 2: Scaffold Directories (COMPLETED 2026-01-12)
- **Description:** Create required directory structure for Phase 9
- **Commit:** `d192430`
- **Directories Created:**
  - `server/tests/api_typed_responses/` - For typed API response tests
  - `server/app/examples/` - For plugin output examples
  - `web-ui/tests/ui_controls/` - For Playwright UI tests
  - `web-ui/src/stories/` - For Storybook stories
- **Duration:** 15 minutes

---

## In Progress

### 🔄 Task 3: RED Tests (Backend)
- **Description:** Write failing tests for typed API responses
- **File:** `server/tests/api_typed_responses/test_api_typed_responses.py`
- **Models to test:**
  - `AnalyzeResponse`
  - `JobStatusResponse`
  - `JobResultResponse`
- **Required fields:** `job_id`, `device_requested`, `device_used`, `fallback`, `frames: list[Any]`
- **Duration:** 1-2 hours

### 📋 Task 4: RED Tests (Frontend)
- **Description:** Write failing Playwright tests for UI controls
- **File:** `web-ui/tests/ui_controls/ui_controls.spec.ts`
- **Tests required:**
  - Device selector persistence
  - Overlay toggles existence (#toggle-boxes, #toggle-labels, #toggle-pitch, #toggle-radar)
  - FPS slider existence (#fps-slider)
- **Duration:** 1-2 hours

### 📋 Task 5: Example Plugin Outputs
- **Description:** Create plugin_outputs.py with example outputs
- **File:** `server/app/examples/plugin_outputs.py`
- **Required examples:**
  - `OCR_EXAMPLE`
  - `TRACKING_EXAMPLE`
- **Duration:** 30 minutes

### 📋 Task 6: Implement Typed API Models
- **Description:** Implement typed response models
- **Models:**
  - `AnalyzeResponse`
  - `JobStatusResponse`
  - `JobResultResponse`
- **Update endpoints:**
  - `/v1/analyze`
  - `/v1/jobs/{id}`
  - `/v1/jobs/{id}/result`
- **Duration:** 2-3 hours

### 📋 Task 7: Implement UI Components
- **Description:** Implement required UI controls with correct IDs
- **Components:**
  - Device selector (`#device-selector`)
  - FPS slider (`#fps-slider`)
  - Overlay toggles (`#toggle-boxes`, `#toggle-labels`, `#toggle-pitch`, `#toggle-radar`)
  - LoadingSpinner.tsx
  - ErrorBanner.tsx
- **Persistence keys:**
  - `forgesyte_device_preference`
  - `forgesyte_fps_target`
- **Duration:** 4-6 hours

### 📋 Task 8: Storybook Story
- **Description:** Add OverlayRenderer story
- **File:** `OverlayRenderer.stories.tsx`
- **Duration:** 30 minutes

### 📋 Task 9: Backend Tests (Green)
- **Description:** Make backend typed response tests pass
- **Duration:** 1 hour

### 📋 Task 10: Frontend Tests (Green)
- **Description:** Make frontend Playwright tests pass
- **Duration:** 1 hour

---

## Work Stream Summary

| Task | Name | Status | Duration | Commit |
|------|------|--------|----------|--------|
| 1 | Governance Commit | ✅ DONE | 30 min | `e312543` |
| 2 | Scaffold Directories | ✅ DONE | 15 min | `d192430` |
| 3 | RED Tests (Backend) | 🔄 IN PROGRESS | 1-2 hrs | - |
| 4 | RED Tests (Frontend) | TODO | 1-2 hrs | - |
| 5 | Example Plugin Outputs | TODO | 30 min | - |
| 6 | Typed API Models | TODO | 2-3 hrs | - |
| 7 | UI Components | TODO | 4-6 hrs | - |
| 8 | Storybook Story | TODO | 30 min | - |
| 9 | Backend Tests (Green) | TODO | 1 hr | - |
| 10 | Frontend Tests (Green) | TODO | 1 hr | - |
| **TOTAL** | **Phase 9** | **2/10** | **12-16 hrs** | - |

---

## Phase 9 Requirements Checklist

### API Requirements
- [ ] `AnalyzeResponse` model
- [ ] `JobStatusResponse` model
- [ ] `JobResultResponse` model
- [ ] Required fields: `job_id`, `device_requested`, `device_used`, `fallback`, `frames: list[Any]`
- [ ] No FrameModel required
- [ ] Update `/v1/analyze`
- [ ] Update `/v1/jobs/{id}`
- [ ] Update `/v1/jobs/{id}/result`

### UI Requirements
- [ ] `#device-selector` ID
- [ ] `#toggle-boxes` ID
- [ ] `#toggle-labels` ID
- [ ] `#toggle-pitch` ID
- [ ] `#toggle-radar` ID
- [ ] `#fps-slider` ID
- [ ] `forgesyte_device_preference` persistence
- [ ] `forgesyte_fps_target` persistence
- [ ] Loading state
- [ ] Error state
- [ ] LoadingSpinner.tsx
- [ ] ErrorBanner.tsx

### Storybook
- [ ] `OverlayRenderer.stories.tsx`

### Example Plugin Outputs
- [ ] `server/app/examples/plugin_outputs.py`
- [ ] `OCR_EXAMPLE`
- [ ] `TRACKING_EXAMPLE`

### Playwright Tests
- [ ] Device selector persistence
- [ ] Overlay toggles existence
- [ ] FPS slider existence

---

## First 4 Commits (Planned)

1. **Scaffold Directories** - Create directory structure
2. **RED Tests (Backend)** - Failing tests for typed API responses
3. **RED Tests (Frontend)** - Failing Playwright tests for UI controls
4. **Example Plugin Outputs** - plugin_outputs.py with examples

---

## Notes

- All work follows the LOCKED plan at `.ampcode/03_PLANS/Phase_9/PHASE_9_PLANS.md`
- Governance committed to prevent loss of planning work
- Next step: Scaffold directories and commit

---

**Last Updated:** 2026-01-12  
**Next Task:** Task 3 - RED Tests (Backend)  
**Estimated Completion:** 12-16 hours total

