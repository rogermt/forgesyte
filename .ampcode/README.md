# Issue #146: Job Pipeline Cleanup & Migration Pack

**Issue**: [#146 - Remove old execution system and complete job pipeline migration](https://github.com/rogermt/forgesyte/issues/146)  
**Branch**: `refactor/web-ui-job-pipeline-cleanup`  
**Status**: ✋ **AWAITING APPROVAL** (pre-implementation)  
**Location**: `/home/rogermt/forgesyte/.ampcode/`

---

## Quick Start

This is a **focused, approval-first migration pack** for the Web-UI job pipeline refactoring. Before implementation, review and approve the plan.

### Files in This Pack

| File | Purpose | Read Time |
|------|---------|-----------|
| **[README.md](./README.md)** | This file — overview & approval checklist | 5 min |
| **[WEB-UI_ISSUE_146.md](./WEB-UI_ISSUE_146.md)** | Main plan with exact PR diffs & new components | 20 min |
| **[ARCHITECTURE_BEFORE_AFTER.md](./ARCHITECTURE_BEFORE_AFTER.md)** | Visual diagrams & detailed comparison | 15 min |
| **[MIGRATION_PLAN.md](./MIGRATION_PLAN.md)** | Step-by-step execution phases | 15 min |
| **[IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md)** | Task-by-task checklist (use during coding) | reference |
| **[migrate_to_job_pipeline.sh](./migrate_to_job_pipeline.sh)** | Helper script to find old code references | run it |

---

## What This Migration Does

### Goals

✅ Remove obsolete tool-runner execution system  
✅ Consolidate on unified job pipeline (`/v1/analyze` + job polling)  
✅ Improve user feedback (show job states: queued → running → done)  
✅ Enable code reuse (VideoTracker + UploadPanel use same logic)  
✅ Simplify component structure (no type branching)  

### Deletions (3 files)

```
❌ web-ui/src/components/ToolSelector.tsx
❌ web-ui/src/utils/detectToolType.ts
❌ web-ui/src/api/toolRunner.ts
```

### Additions (2 components)

```
✅ web-ui/src/components/JobStatusIndicator.tsx  (show queued/running/done/error)
✅ web-ui/src/components/JobError.tsx           (display error messages)
```

### Updates (3-4 components)

```
⚙️  web-ui/src/components/UploadPanel.tsx        (use apiClient.analyzeImage + pollJob)
⚙️  web-ui/src/components/ResultsPanel.tsx       (remove detectToolType branching)
⚙️  web-ui/src/components/VideoTracker.tsx       (use job pipeline)
⚙️  web-ui/src/pages/AnalyzePage.tsx             (replace ToolSelector with dropdown)
```

---

## Approval Checklist (MUST COMPLETE BEFORE CODING)

### Read & Understand

- [ ] Read [WEB-UI_ISSUE_146.md](./WEB-UI_ISSUE_146.md) — main plan with diffs
- [ ] Read [ARCHITECTURE_BEFORE_AFTER.md](./ARCHITECTURE_BEFORE_AFTER.md) — visual comparison
- [ ] Read [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) — detailed phases

### Answer Design Questions

**1. Plugin Selection** — How do users pick a plugin?
- [ ] A) Add dropdown to AnalyzePage using `apiClient.listPlugins()`
- [ ] B) Keep minimal `PluginSelector` component
- [ ] C) Other: _____________

**2. Result Rendering** — How should ResultsPanel display results?
- [ ] A) Generic JSON pretty-print
- [ ] B) Simple card layout (key/value pairs)
- [ ] C) Keep plugin-specific renderers (OCR, YOLO, etc.)
- [ ] D) Other: _____________

**3. Video Overlay** — Where does overlay rendering happen?
- [ ] A) Inside VideoTracker component
- [ ] B) Separate VideoOverlay component
- [ ] C) Not implemented yet (TODO)
- [ ] D) Other: _____________

**4. Error Retry** — What should "Retry" button do?
- [ ] A) Re-process same file/frame
- [ ] B) Clear error and wait for new upload
- [ ] C) Optional (callback passed by parent)
- [ ] D) Other: _____________

**5. Testing** — Confirm test setup
- [ ] A) Vitest + React Testing Library (current)
- [ ] B) Jest + Enzyme (different)
- [ ] C) Other: _____________

### Approval Sign-Off

**Approver Name**: ________________________  
**Date**: ________________________  
**Approved**: [ ] **YES** (proceed with implementation)  [ ] **NO** (revise plan)  

**Notes/Changes**: 
```
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```

---

## Current State (Before Migration)

### Problems

❌ **Synchronous Execution**: UI blocks while processing  
❌ **Type Branching**: Complex if/else for OCR vs YOLO vs Ball vs Pitch  
❌ **ToolSelector Coupling**: Only used once, tightly coupled to execution  
❌ **No Job Queue**: Can't see queued/running/done states  
❌ **VideoTracker Mismatch**: Can't reuse UploadPanel logic  

### Architecture

```
UploadPanel 
    ↓
runTool(toolId, file) [SYNCHRONOUS]
    ↓
/v1/tools/{id}/run [BLOCKS UI]
    ↓
ResultsPanel
    ↓
detectToolType() branching
    ├─ OCR: show text
    ├─ YOLO: show boxes
    └─ etc...
```

---

## Target State (After Migration)

### Benefits

✅ **Async/Non-blocking**: Returns job_id immediately  
✅ **Unified Execution**: All plugins use same pipeline  
✅ **Job States**: User sees queued → running → done → error  
✅ **Generic Rendering**: No branching, uniform result display  
✅ **Code Reuse**: VideoTracker uses same execution logic  

### Architecture

```
UploadPanel
    ↓
apiClient.analyzeImage(file, pluginId)  [NON-BLOCKING]
    ↓
/v1/analyze [returns job_id immediately]
    ↓
apiClient.pollJob(job_id)  [async polling]
    ↓
Job State Machine: queued → running → done → error
    ↓
JobStatusIndicator (shows current state)
    ↓
ResultsPanel (generic, no branching)
    ↓
JobError (if needed)
```

---

## Implementation Timeline

**Estimated**: ~2.5 hours

| Phase | Task | Time |
|-------|------|------|
| 1 | Prep & understanding | 15 min |
| 2 | Delete 3 obsolete files | 10 min |
| 3 | Create 2 new components | 20 min |
| 4 | Update 3-4 existing components | 30 min |
| 5 | Tests, lint, type-check | 15 min |
| 6 | Commit & push | 5 min |
| 7 | Create PR | 3 min |

---

## How to Use This Pack

### Step 1: Review (You Are Here)

Read this README and decide:
- [ ] Plan looks good → proceed to Step 2
- [ ] Need clarification → ask questions
- [ ] Need changes → request revisions

### Step 2: Answer Questions

Fill out the **Approval Checklist** above. Get sign-off before proceeding.

### Step 3: Implement

Use **[IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md)** as your task list:

```bash
# First, run the helper script to find old code:
cd /home/rogermt/forgesyte
./.ampcode/migrate_to_job_pipeline.sh
```

Then follow the checklist step-by-step:
1. ✋ Phase 1: Preparation
2. 🗑️ Phase 2: File Deletions
3. ➕ Phase 3: Add New Components
4. ⚙️ Phase 4: Update Existing Components
5. ✅ Phase 5: Verification
6. 📝 Phase 6: Commit & Push
7. 🔗 Phase 7: Pull Request

### Step 4: Review & Merge

Once PR is created:
- Get review approval
- Merge to main
- Delete feature branch

---

## Document Map

### For Planning (Read First)

1. **README.md** ← You are here
2. **WEB-UI_ISSUE_146.md** — Full plan with exact diffs
3. **ARCHITECTURE_BEFORE_AFTER.md** — Visual diagrams

### For Implementation (Use While Coding)

4. **IMPLEMENTATION_CHECKLIST.md** — Task-by-task checklist
5. **MIGRATION_PLAN.md** — Detailed phases

### For Discovery

6. **migrate_to_job_pipeline.sh** — Find old code references

---

## Key Decisions (From WEB-UI_ISSUE_146.md)

| Decision | Value | Notes |
|----------|-------|-------|
| Execution Model | Job Pipeline | `/v1/analyze` + polling |
| UI Blocking | No | Returns job_id immediately |
| Type Detection | Removed | Job results are uniform |
| New Components | 2 | JobStatusIndicator, JobError |
| Files to Delete | 3 | ToolSelector, detectToolType, toolRunner |
| MVP-Grade | Yes | Only what's needed, no fluff |
| Code Reuse | High | VideoTracker uses same pipeline as UploadPanel |

---

## Pre-Implementation Verification

Before coding, run this script to check current state:

```bash
cd /home/rogermt/forgesyte
./.ampcode/migrate_to_job_pipeline.sh
```

**Output will show:**
- ✅ All references to `runTool()`
- ✅ All references to `ToolSelector`
- ✅ All references to `detectToolType`
- ✅ Obsolete files present
- ✅ New components status

---

## Success Criteria

After implementation, these should all be true:

```
✅ No runTool() in codebase
✅ No ToolSelector imports
✅ No detectToolType usage
✅ JobStatusIndicator component exists and used
✅ JobError component exists and used
✅ UploadPanel uses apiClient.analyzeImage() + pollJob()
✅ ResultsPanel uses generic result display
✅ VideoTracker uses job pipeline
✅ All tests passing: npm run test -- --run
✅ Type-check clean: npm run type-check
✅ Lint clean: npm run lint
✅ PR created and linked to #146
```

---

## Getting Help

### Questions About the Plan?

- Review [ARCHITECTURE_BEFORE_AFTER.md](./ARCHITECTURE_BEFORE_AFTER.md) — has detailed diagrams
- Check [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) section "Questions for Approval"
- Ask for clarification before starting

### Stuck During Implementation?

- See [IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md) → Troubleshooting section
- Run `./.ampcode/migrate_to_job_pipeline.sh` to find references
- Check exact code in [WEB-UI_ISSUE_146.md](./WEB-UI_ISSUE_146.md)

### Tests Failing?

- Check mock setup (apiClient mocks)
- Verify assertion expectations
- Update test to match new job pipeline flow

---

## Files in This Pack (Details)

### WEB-UI_ISSUE_146.md
**What**: Main plan document with exact PR diffs  
**Contains**:
- Executive summary
- Architecture diagrams (before/after)
- Exact git diffs for each deletion
- Complete source code for new components
- Complete source code for updated components
- File summary table
- Pre-implementation questions

**Use**: Read this first to understand the full scope

---

### ARCHITECTURE_BEFORE_AFTER.md
**What**: Visual comparison and detailed architecture  
**Contains**:
- Component diagrams (before/after)
- Data flow diagrams
- Lifecycle comparisons
- File structure changes
- Server contract documentation
- Summary table
- Testing strategy
- Timeline

**Use**: Read this to understand the "why" and see visual flow

---

### MIGRATION_PLAN.md
**What**: Detailed execution phases  
**Contains**:
- Overview and prerequisite understanding
- Part 1: Deletions (detailed for each file)
- Part 2: New components (testing strategy)
- Part 3: Component updates (patterns and examples)
- Part 4: Test structure
- Part 5: Execution checklist
- Commit message template
- Rollback plan
- Questions for approval

**Use**: Read this for the detailed "how to" before coding

---

### IMPLEMENTATION_CHECKLIST.md
**What**: Step-by-step task checklist  
**Contains**:
- Pre-implementation approval section
- 7 phases with detailed checkboxes
  - Phase 1: Preparation
  - Phase 2: File Deletions
  - Phase 3: Add New Components
  - Phase 4: Update Existing Components
  - Phase 5: Verification
  - Phase 6: Commit & Push
  - Phase 7: Pull Request
- Troubleshooting guide
- Sign-off section

**Use**: During implementation — follow step-by-step

---

### migrate_to_job_pipeline.sh
**What**: Bash helper script  
**Does**:
1. Finds all `runTool()` usage
2. Finds all `ToolSelector` references
3. Finds all `detectToolType` usage
4. Lists obsolete files
5. Offers to delete them
6. Prints manual checklist

**Use**: Run before and after coding to verify

```bash
chmod +x migrate_to_job_pipeline.sh
./migrate_to_job_pipeline.sh
```

---

## Next Steps

### ✋ STOP HERE UNTIL APPROVED

1. **Read** the approval checklist at the top of this page
2. **Answer** all design questions (5 questions)
3. **Get** sign-off from decision maker
4. **Proceed** to implementation once approved

### Once Approved

1. **Use** [IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md) as your task list
2. **Follow** the 7 phases sequentially
3. **Run** tests after each phase
4. **Commit** with proper message format
5. **Create** PR and link to #146

---

## Troubleshooting: Common Questions

**Q: Do I need to modify the server?**  
A: No. The server endpoints (`/v1/analyze`, `/v1/jobs/{id}`) already exist.

**Q: Will this break existing functionality?**  
A: No. This is a full cutover; there's no backwards compatibility needed. Old system is being removed.

**Q: What about the video tracker overlay rendering?**  
A: Left as TODO in the plan. The component processes frames correctly; overlay rendering is a separate concern.

**Q: Can I test locally before the PR?**  
A: Yes, see Phase 5 → "Manual Testing (Optional)" in the checklist.

**Q: What if tests fail?**  
A: See Troubleshooting section in [IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md).

---

## Summary

This is a **complete, ready-to-implement migration pack** for Issue #146:

✅ **Approval-first approach**: Review and sign-off before coding  
✅ **MVP-grade**: Only what's needed, no fluff  
✅ **Exact diffs**: Copy-paste ready code  
✅ **Test strategy**: Included and detailed  
✅ **Checklists**: Step-by-step, verification at each phase  
✅ **Helper script**: Find old code references automatically  

**Status**: Awaiting approval (see checklist at top)  
**When approved**: Follow IMPLEMENTATION_CHECKLIST.md step-by-step  
**Time estimate**: ~2.5 hours  

---

**Last updated**: Feb 1, 2026  
**Issue**: [#146](https://github.com/rogermt/forgesyte/issues/146)  
**Branch**: `refactor/web-ui-job-pipeline-cleanup`
