# Implementation Plan - Issue #101: Unify OCR + YOLO Flows

## Overview
Create unified tool runner with logging + retry to replace divergent fetch patterns in OCR and YOLO flows.

## PHASE 1: CLEAN ENVIRONMENT & BRANCH SETUP

### Step 1.1: Clean working directory
```bash
git status  # Check for uncommitted changes
git stash   # Stash any uncommitted work
```
**Why:** Ensures clean slate, prevents merge conflicts.

### Step 1.2: Create feature branch
```bash
git checkout -b blackboxai/feature/101-unify-flows
```
**Why:** Isolates changes, enables code review via PR.

---

## PHASE 2: TDD - WRITE TESTS FIRST

### Step 2.1: Type Definitions Tests
**File:** `web-ui/src/hooks/useVideoProcessor.types.ts`

**What to add:**
```typescript
export interface ProcessFrameLogEntry {
  timestamp: number;
  pluginId: string;
  toolName: string;
  durationMs: number;
  success: boolean;
  error?: string;
  retryCount: number;
}

export interface ProcessFrameMetrics {
  totalFrames: number;
  successfulFrames: number;
  failedFrames: number;
  averageDurationMs: number;
  lastError?: string;
}
```
**Why:** TypeScript types must exist before implementation uses them.

---

### Step 2.2: runTool Tests ⭐ CORE PIECE
**File:** `web-ui/src/utils/runTool.test.ts`

**Test cases:**
1. `runTool` - calls correct endpoint with args
2. `runTool` - returns error when server responds with non-OK
3. `runTool` - returns error when JSON is invalid
4. `withRetry` - retries on failure
5. `withRetry` - throws after max retries
6. `withLogging` - logs before/after function call
7. `withLogging` - logs errors

**Why:** Tests define expected behavior before implementation.

---

### Step 2.3: useVideoProcessor Integration Tests
**File:** `web-ui/src/hooks/useVideoProcessor.test.ts`

**Add tests for:**
1. Logs frame metrics on success
2. Logs frame metrics on failure
3. Retries when runTool fails
4. Tracks request timing metrics

**Why:** Validates integration of runTool into the hook.

---

### Step 2.4: Manifest Regression Test
**File:** `web-ui/src/hooks/useManifest.test.ts`

**Tests added:**
1. `should always fetch manifest when pluginId changes` - Verify manifest is fetched on pluginId change
2. `should not use stale cache after TTL expires` - Verify cache invalidation behavior
3. `should fetch manifest even when switching to same pluginId after unmount` - Verify hook instance behavior

**Why:** Locks in invariant: **plugin selection → manifest fetch (always)**

---

## PHASE 3: IMPLEMENTATION (Pass the Tests)

### Step 3.1: Create runTool.ts
**File:** `web-ui/src/utils/runTool.ts`

**Functions:**
1. `runTool({pluginId, toolName, args})` - Unified tool execution
2. `withLogging(fn, context)` - Structured logging wrapper
3. `withRetry(fn, options)` - Exponential backoff retry

**Why:** Centralizes fetch logic, removes duplication between OCR/YOLO flows.

### Step 3.2: Update useVideoProcessor.ts
**Changes:**
1. Import `runTool`, `ProcessFrameLogEntry`, `ProcessFrameMetrics`
2. Add `metrics` state: `{ totalFrames, successfulFrames, failedFrames, averageDurationMs, lastError }`
3. Add `logs` state: `ProcessFrameLogEntry[]`
4. Replace inline fetch with `runTool()`
5. Update return to include `metrics` and `logs`

**Why:** Hook now uses unified runner + tracks metrics.

---

## PHASE 4: VERIFY

### Step 4.1: Run tests
```bash
cd web-ui && npm test
```

### Step 4.2: Run build
```bash
cd web-ui && npm run build
```

### Step 4.3: Stage & commit
```bash
git add -A
git commit -m "feat(web-ui): Unify OCR+YOLO flows with runTool (#101)

- Create runTool.ts with logging and retry
- Add ProcessFrameLogEntry and ProcessFrameMetrics types
- Integrate runTool into useVideoProcessor
- Add manifest regression tests
- All 43 tests pass"
```

### Step 4.4: Create PR
Use `.github/pull_request_template.md` with:
- Summary of changes
- Test change justification
- Checklist completion

---

## SUMMARY OF FILES CHANGED

| File | Action | Purpose |
|------|--------|---------|
| `useVideoProcessor.types.ts` | Modified | Add logging/metrics types |
| `runTool.ts` | Created | Unified tool runner |
| `runTool.test.ts` | Created | Tests for runTool |
| `useVideoProcessor.ts` | Modified | Use runTool, add metrics |
| `useVideoProcessor.test.ts` | Modified | Test metrics/logging |
| `useManifest.ts` | Modified | Export `clearManifestCache()` for testing |
| `useManifest.test.ts` | Modified | Add regression tests |

---

## CHECKLIST

- [x] Phase 1: Clean environment, create branch
- [x] Phase 2: Write tests (types, runTool, useVideoProcessor, manifest)
- [x] Phase 3: Implement runTool.ts
- [x] Phase 3: Update useVideoProcessor.ts
- [x] Phase 4: Run tests (43 tests pass)
- [x] Phase 4: Verify build (build successful)
- [ ] Phase 4: Create PR

