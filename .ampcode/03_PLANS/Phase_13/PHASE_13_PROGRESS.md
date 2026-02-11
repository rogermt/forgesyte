# PHASE 13 — PROGRESS
**VideoTracker Multi-Tool Linear Pipelines (Single-Plugin)**

## TDD WORKFLOW (MANDATORY)

For EVERY commit:
1. ✅ **WRITE TEST FIRST** - Test must FAIL (red)
2. ✅ **RUN TEST** - Verify it fails
3. ✅ **IMPLEMENT CODE** - Make test pass (green)
4. ✅ **RUN TEST** - Verify it passes
5. ✅ **RUN PRE-COMMIT** - All checks pass
6. ✅ **COMMIT** - With passing tests

**NO EXCEPTIONS. NO SHORTCUTS. TESTS FIRST.**

---

## Overall Status: IN PROGRESS (5/10 completed)

## 5 Key Decisions (Canonical Answers)
| Question | Answer |
|---------|--------|
| WS frame uses `tools[]`? | ✅ YES - mandatory |
| Inject VideoPipelineService? | ✅ YES - inject in `__init__` |
| `selectedTool` → `selectedTools[]`? | ✅ YES - required |
| Remove fallback logic? | ✅ YES for Phase 13 paths |
| REST endpoint location? | ✅ YES - `routes_pipeline.py` |

---

## 10-Commit Implementation Order (TDD)

| # | Status | Commit | Notes |
|---|--------|--------|-------|
| 1 | ✅ | VideoPipelineService Skeleton | Done |
| 2 | ✅ | REST Pipeline Endpoint | Done |
| 3 | ✅ | Artifact Cleanup | Done |
| 4 | ✅ | Update useVideoProcessor Hook | Done | - Frontend Only |
| 5 | ✅ | Patch VideoTracker Component | Done | |
| 6 | ❌ | UI Tool Selector (optional) | NOT DONE |
| 7 | ❌ | Add Pipeline Logging to VideoPipelineService | NOT DONE |
| 8 | ❌ | Add Regression Test Suite | NOT DONE |
| 9 | ❌ | Add Plugin Validation Tools | NOT DONE |
| 10 | ❌ | Remove Fallback Logic from VisionAnalysisService | NOT DONE |

---

## Summary: Completed vs Not Completed
### ✅ COMPLETED (5 commits)
| # | Commit | Status |
|---|--------|--------|
| 1 | VideoPipelineService Skeleton | ✅ Done |
| 2 | REST Pipeline Endpoint | ✅ Done |
| 3 | Artifact Cleanup | ✅ Done |
| 4 | Update useVideoProcessor hook (toolName → tools[]) | ✅ Done |
| 5 | Patch VideoTracker component | ✅ Done |

### ❌ NOT COMPLETED (5 commits)
| # | Commit | Status |
|---|--------|--------|
| 6 | UI Tool Selector (optional) | ❌ NOT DONE |
| 7 | Add pipeline logging to VideoPipelineService | ❌ NOT DONE |
| 8 | Add regression test suite | ❌ NOT DONE |
| 9 | Add plugin validation tools | ❌ NOT DONE |

## 🔴 CRITICAL MISSING ITEMS
These must be completed to finish Phase 13:

1. **VisionAnalysisService NOT patched** - Must inject VideoPipelineService and switch from single tool → tools[]
2. **No WS integration** - VisionAnalysisService still uses old single-tool path
3. **Web-UI not updated** - useVideoProcessor, VideoTracker, App.tsx still use old toolName/selectedTool

---

## Progress by Commit (TDD)

### COMMIT 1: VideoPipelineService Skeleton
**Status:** ✅ DONE

**Completed:**
- Test: `server/tests/test_video_pipeline_service.py` ✅
- Implementation: `server/app/services/video_pipeline_service.py` ✅
- Helpers: `server/tests/helpers.py` (FakeRegistry, FakePlugin) ✅
- Pre-commit checks passed ✅

### COMMIT 2: REST Pipeline Endpoint
**Status:** ✅ DONE

**Completed:**
- Schema: `server/app/schemas/pipeline.py` (PipelineRequest) ✅
- Route: `server/app/routes_pipeline.py` (`POST /video/pipeline`) ✅
- Test: `server/tests/test_pipeline_rest.py` ✅
- Pre-commit checks passed ✅

### COMMIT 3: Artifact Cleanup
**Status:** ✅ DONE

**Completed:**
- Removed `<parameter*` files from git tracking ✅

---

### COMMIT 4: Update useVideoProcessor Hook (Frontend Only)
**Status:** ❌ NOT STARTED

**Source of Truth:** `.ampcode/04_PHASE_NOTES/Phase_13/PHASE_13_COMMIT_4.md`

**FILES TO MODIFY (3 total):**

1. **`web-ui/src/hooks/useVideoProcessor.types.ts`**
   - Change `toolName: string` → `tools: string[]` in `UseVideoProcessorArgs`
   - Change `toolName: string` → `tools: string[]` in `ProcessFrameLogEntry`

2. **`web-ui/src/hooks/useVideoProcessor.ts`**
   - Function signature: `toolName` → `tools`
   - Guard clause: `!toolName` → `!tools || tools.length === 0`
   - runTool call: Extract `firstTool = tools[0]` and pass to runTool
   - Log entry: `toolName` → `tools`
   - useEffect dependency: `toolName` → `tools`

3. **`web-ui/src/hooks/useVideoProcessor.test.ts`** (NEW FILE)
   - 7 test cases as specified in PHASE_13_COMMIT_4.md

**FILES NOT MODIFIED IN COMMIT 4:**
- VideoTracker.tsx → Commit 5
- App.tsx → Commit 6
- Backend files → Not this commit

---

### COMMIT 5: Patch VideoTracker Component
**Status:** ❌ NOT STARTED

**TDD Steps:**
1. [ ] Write test: `web-ui/scripts/test_components.py`
2. [ ] Run test → FAIL
3. [ ] Modify: `web-ui/src/components/VideoTracker.tsx`
   - Update props interface: `toolName` → `tools[]`
   - Update header display
4. [ ] Run test → PASS
5. [ ] Pre-commit checks
6. [ ] Commit

---

### COMMIT 6: (Optional) UI Tool Selector
**Status:** ❌ NOT STARTED (Optional)

**TDD Steps:**
1. [ ] Create `web-ui/src/components/PipelineToolSelector.tsx`
2. [ ] Modify `web-ui/src/App.tsx`
   - Replace `selectedTool` → `selectedTools[]`
3. [ ] Tests verify selector works
4. [ ] Pre-commit checks
5. [ ] Commit

---

### COMMIT 7: Add Pipeline Logging
**Status:** ❌ NOT STARTED

**TDD Steps:**
1. [ ] Write test for logging
2. [ ] Modify: `VideoPipelineService.run_pipeline()` to add structured logging
3. [ ] Run test → PASS
4. [ ] Pre-commit checks
5. [ ] Commit

---

### COMMIT 8: Add Regression Test Suite
**Status:** ❌ NOT STARTED

**TDD Steps:**
1. [ ] Create `server/tests/test_pipeline_regression.py`
2. [ ] Test tools execute in order, output chaining, validation edge cases
3. [ ] Run tests → PASS
4. [ ] Pre-commit checks
5. [ ] Commit

---

### COMMIT 9: Add Plugin Validation Tools
**Status:** ❌ NOT STARTED

**TDD Steps:**
1. [ ] Create `server/scripts/validate_plugin_manifest.py`
2. [ ] Tests verify validator catches common issues
3. [ ] Pre-commit checks
4. [ ] Commit

---

### COMMIT 10: Remove Fallback Logic
**Status:** ❌ NOT STARTED

**TDD Steps:**
1. [ ] Write test verifying no fallback exists
2. [ ] Modify: `vision_analysis.py` - remove fallback code
3. [ ] Modify: `tasks.py` - remove fallback code
4. [ ] Run test → PASS
5. [ ] Pre-commit checks
6. [ ] Commit

---

## Source of Truth Documents

| Document | Purpose |
|----------|---------|
| `PHASE_13_PLANS.md` | Authoritative plan with all specifications |
| `PHASE_13_CHECKLIST.md` | Apply-in-this-order checklist |
| `PHASE_13_COMMIT_4.md` | Detailed Commit 4 analysis - Frontend |
| `PHASE_13_NOTES_01.md` | Developer specifications |
| `PHASE_13_NOTES_02.md` | Integration specs |
| `PHASE_13_NOTES_03.md` | Plugin developer pack, troubleshooting |
| `PHASE_13_NOTES_05.md` | Canonical answers to 5 key questions |
| `TDD_PLAN.md` | TDD methodology |

---

## STRICT REQUIREMENTS (Non-Negotiable)

1. ✅ **TDD MANDATORY** - Write tests FIRST, then implement
2. ✅ **MUST BE GREEN BEFORE CODING** - Run ALL tests, lint, typecheck before writing code
3. ✅ **FIX ALL PRE-EXISTING FAILURES** - No test failures allowed
4. ✅ **NO MAKING UP CODE** - Ask questions if requirements unclear
5. ✅ **NO COMMITTING FAILING TESTS** - Always run tests before commit
6. ✅ **10-COMMIT WORKFLOW** - Follow the 10-commit implementation order exactly

---

## Pre-Commit Checklist (Run Before Each Commit)

| # | Check | Command |
|---|-------|---------|
| 1 | Server tests pass | `cd server && uv run pytest -q` |
| 2 | Web-UI tests pass | `cd web-ui && npm install && npm test` |
| 3 | Black lint pass | `cd server && black --check .` |
| 4 | Ruff lint pass | `cd server && ruff check .` |
| 5 | MyPy typecheck pass | `cd server && mypy .` |
| 6 | ESLint pass | `cd web-ui && npx eslint src --ext ts,tsx --max-warnings=0` |
| 7 | No skipped tests | Verify no `it.skip`, `describe.skip`, `test.skip` |

---

## Notes

- **Commits 1-5 COMPLETED** - VideoPipelineService, REST endpoint, artifact cleanup, useVideoProcessor hook done
- **Commit 4 COMPLETED** - Frontend-only changes to useVideoProcessor hook
- **Commits 5-10 NOT DONE** - VisionAnalysisService and remaining Web-UI updates pending
- Each commit must pass pre-commit checklist before proceeding
- Tests must be written BEFORE implementation (TDD)
- Progress tracker updated after each commit

---

## Current Working Files (Evidence of Completion)

### Web UI Files (Evidence of Commits 4-5)
| File | Status |
|------|--------|
| `web-ui/src/hooks/useVideoProcessor.ts` | ✅ Updated: toolName → tools[] |
| `web-ui/src/hooks/useVideoProcessor.types.ts` | ✅ Updated: tools[] type |
### Server Files (Evidence of Commits 1-3)
| File | Status |
|------|--------|
| `server/app/services/video_pipeline_service.py` | ✅ Created |
| `server/app/schemas/pipeline.py` | ✅ Created |
| `server/app/routes_pipeline.py` | ✅ Created |
| `server/tests/test_video_pipeline_service.py` | ✅ Created |
| `server/tests/test_pipeline_rest.py` | ✅ Created |
| `server/tests/helpers.py` | ✅ Updated |

### Files Pending Update (Commit 6+)
| File | Status |
|------|--------|
| `server/app/services/vision_analysis.py` | ❌ Patch to inject VideoPipelineService + tools[] |
| `web-ui/src/components/PipelineToolSelector.tsx` | ❌ Create in Commit 6 (optional) |
| `server/tests/test_pipeline_rest.py` | ✅ Created |
| `server/tests/helpers.py` | ✅ Updated |

### Files Pending Update (Commit 5+)
| File | Status |
|------|--------|
| `web-ui/src/components/VideoTracker.tsx` | ❌ Update in Commit 5 |
| `web-ui/src/App.tsx` | ❌ Update in Commit 6 |
---

## Last Updated
Last Updated: [Current Session] - Progress updated with Commit 4 details from PHASE_13_COMMIT_4.md
PHASE_13_PROGRESS.md and PHASE_13_PLANS.md are now the single source of truth.
Reference documents in `.ampcode/04_PHASE_NOTES/Phase_13/` are supporting documents.

