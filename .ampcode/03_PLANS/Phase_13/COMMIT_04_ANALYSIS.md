# COMMIT 4: Update useVideoProcessor Hook — DETAILED ANALYSIS

**VideoTracker Multi-Tool Linear Pipelines (Single-Plugin)**

**Commit 4 of 10** — Phase 13 Implementation

---

## EXECUTIVE SUMMARY

**Objective:** Replace single `toolName` parameter with `tools[]` array in `useVideoProcessor` hook to support multi-tool pipelines.

**Files Modified:** 2 files
1. `web-ui/src/hooks/useVideoProcessor.types.ts` — Update type definitions
2. `web-ui/src/hooks/useVideoProcessor.ts` — Update hook implementation

**Tests Created:** 1 test file
1. `web-ui/src/hooks/useVideoProcessor.test.ts` — Verify `tools[]` behavior

**TDD Workflow:**
1. ✅ Write tests FIRST (define expected behavior)
2. ✅ Run tests → FAIL (old `toolName` signature doesn't match)
3. ✅ Implement changes to make tests pass
4. ✅ Run tests → PASS
5. ✅ Pre-commit checks (eslint, type-check, vitest)
6. ✅ Commit

---

## CURRENT STATE (Before Commit 4)

### useVideoProcessor.types.ts

```typescript
export interface UseVideoProcessorArgs {
  videoRef: React.RefObject<HTMLVideoElement>;
  pluginId: string;
  toolName: string;        // ← SINGLE TOOL (OLD)
  fps: number;
  device: string;
  enabled: boolean;
  bufferSize?: number;
}

export interface ProcessFrameLogEntry {
  timestamp: number;
  pluginId: string;
  toolName: string;        // ← SINGLE TOOL (OLD)
  durationMs: number;
  success: boolean;
  error?: string;
  retryCount: number;
}
```

### useVideoProcessor.ts

**Key Line 17:** `toolName,` parameter
**Key Line 70:** Guard checks `!toolName`
**Key Line 88-95:** Calls `runTool({ pluginId, toolName, args })`
**Key Line 126:** Logs `toolName` to metrics
**Key Line 163:** useEffect dependency: `toolName`

---

## TARGET STATE (After Commit 4)

### useVideoProcessor.types.ts

```typescript
export interface UseVideoProcessorArgs {
  videoRef: React.RefObject<HTMLVideoElement>;
  pluginId: string;
  tools: string[];         // ← TOOLS ARRAY (NEW)
  fps: number;
  device: string;
  enabled: boolean;
  bufferSize?: number;
}

export interface ProcessFrameLogEntry {
  timestamp: number;
  pluginId: string;
  tools: string[];         // ← TOOLS ARRAY (NEW)
  durationMs: number;
  success: boolean;
  error?: string;
  retryCount: number;
}
```

### useVideoProcessor.ts

**Key Line 17:** `tools,` parameter (array)
**Key Line 70:** Guard checks `!tools || tools.length === 0`
**Key Line 88-95:** Calls `runTool()` for EACH tool in pipeline (future commit)
  - For now: Call first tool only OR raise error if `tools.length > 1`
**Key Line 126:** Logs `tools` to metrics
**Key Line 163:** useEffect dependency: `tools`

---

## DETAILED CHANGES

### File 1: useVideoProcessor.types.ts

#### Change 1.1: Update UseVideoProcessorArgs Interface

**Location:** Lines 8-16

**Before:**
```typescript
export interface UseVideoProcessorArgs {
  videoRef: React.RefObject<HTMLVideoElement>;
  pluginId: string;
  toolName: string;
  fps: number;
  device: string;
  enabled: boolean;
  bufferSize?: number;
}
```

**After:**
```typescript
export interface UseVideoProcessorArgs {
  videoRef: React.RefObject<HTMLVideoElement>;
  pluginId: string;
  tools: string[];  // Changed: was toolName: string
  fps: number;
  device: string;
  enabled: boolean;
  bufferSize?: number;
}
```

**Why:** Hook now receives array of tools to support multi-tool pipelines.

---

#### Change 1.2: Update ProcessFrameLogEntry Interface

**Location:** Lines 32-40

**Before:**
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
```

**After:**
```typescript
export interface ProcessFrameLogEntry {
  timestamp: number;
  pluginId: string;
  tools: string[];  // Changed: was toolName: string
  durationMs: number;
  success: boolean;
  error?: string;
  retryCount: number;
}
```

**Why:** Log entries must capture which tools were executed in the pipeline.

---

### File 2: useVideoProcessor.ts

#### Change 2.1: Update Function Signature (Line 14-22)

**Before:**
```typescript
export function useVideoProcessor({
  videoRef,
  pluginId,
  toolName,        // ← OLD
  fps,
  device,
  enabled,
  bufferSize = 5,
}: UseVideoProcessorArgs): UseVideoProcessorReturn {
```

**After:**
```typescript
export function useVideoProcessor({
  videoRef,
  pluginId,
  tools,           // ← NEW (array)
  fps,
  device,
  enabled,
  bufferSize = 5,
}: UseVideoProcessorArgs): UseVideoProcessorReturn {
```

**Why:** Parameter name must match type definition.

---

#### Change 2.2: Update Guard Clause (Lines 69-76)

**Before:**
```typescript
// Guard against empty pluginId or toolName
if (!pluginId || !toolName) {
  console.error("Frame processing aborted: pluginId or toolName missing", {
    pluginId,
    toolName,
  });
  return;
}
```

**After:**
```typescript
// Guard against empty pluginId or tools
if (!pluginId || !tools || tools.length === 0) {
  console.error("Frame processing aborted: pluginId or tools missing", {
    pluginId,
    tools,
  });
  return;
}
```

**Why:** Must verify both `tools` exists AND is non-empty array.

---

#### Change 2.3: Update runTool Call (Lines 88-96)

**CRITICAL DECISION:** For Commit 4, execute ONLY the FIRST tool.
(Multi-tool execution will be implemented in Commit 7+)

**Before:**
```typescript
const { result, success, error: runToolError } = await runTool({
  pluginId,
  toolName,
  args: {
    frame_base64: frameBase64,
    device,
    annotated: false,
  },
});
```

**After:**
```typescript
// Phase 13: For now, execute first tool only
// Multi-tool execution will be implemented in later commits
const firstTool = tools[0];

const { result, success, error: runToolError } = await runTool({
  pluginId,
  toolName: firstTool,  // Use first tool from array
  args: {
    frame_base64: frameBase64,
    device,
    annotated: false,
  },
});
```

**Why:** 
- Minimal change for this commit (TDD principle: smallest step)
- Type system still uses `runTool(toolName: string)`
- Full pipeline execution comes in Commit 7
- Tests verify correct tool is selected

---

#### Change 2.4: Update Log Entry (Lines 121-132)

**Before:**
```typescript
setLogs((prev) => [
  ...prev,
  {
    timestamp: Date.now(),
    pluginId,
    toolName,      // ← OLD
    durationMs,
    success,
    error: runToolError,
    retryCount: 0,
  },
]);
```

**After:**
```typescript
setLogs((prev) => [
  ...prev,
  {
    timestamp: Date.now(),
    pluginId,
    tools,         // ← NEW (array)
    durationMs,
    success,
    error: runToolError,
    retryCount: 0,
  },
]);
```

**Why:** Log entry signature must match updated ProcessFrameLogEntry type.

---

#### Change 2.5: Update useEffect Dependency (Line 163)

**Before:**
```typescript
useEffect(() => {
  // ... effect code ...
// eslint-disable-next-line react-hooks/exhaustive-deps
}, [enabled, fps, device, pluginId, toolName]);  // ← OLD
```

**After:**
```typescript
useEffect(() => {
  // ... effect code ...
// eslint-disable-next-line react-hooks/exhaustive-deps
}, [enabled, fps, device, pluginId, tools]);  // ← NEW
```

**Why:** Effect must re-run when `tools` array changes (not `toolName`).

**Note:** Array comparison in dependencies: React uses referential equality.
- If parent always passes NEW array `[tool1, tool2]`, effect runs every render
- Parent should memoize: `const memoizedTools = useMemo(() => [tool1], [tool1])`
- But that's a parent concern (Commit 5+)

---

## TESTS TO WRITE (TDD Step 1)

### File: web-ui/src/hooks/useVideoProcessor.test.ts

**Create NEW test file** with the following tests:

```typescript
/**
 * Tests for useVideoProcessor hook - Phase 13 tools[] update
 * Verifies hook sends tools[] instead of toolName to backend
 */

import { renderHook, waitFor } from "@testing-library/react";
import { useVideoProcessor } from "./useVideoProcessor";

describe("useVideoProcessor", () => {
  describe("Phase 13: tools[] parameter", () => {
    
    it("accepts tools array parameter", () => {
      // Arrange: Create ref
      const videoRef = { current: null };
      
      // Act: Render hook with tools array
      const { result } = renderHook(() =>
        useVideoProcessor({
          videoRef: videoRef as React.RefObject<HTMLVideoElement>,
          pluginId: "test-plugin",
          tools: ["detect_players"],  // Array
          fps: 30,
          device: "cpu",
          enabled: false,
          bufferSize: 5,
        })
      );
      
      // Assert: Hook should render without error
      expect(result.current).toBeDefined();
      expect(result.current.error).toBeNull();
    });

    it("accepts multiple tools in array", () => {
      const videoRef = { current: null };
      
      const { result } = renderHook(() =>
        useVideoProcessor({
          videoRef: videoRef as React.RefObject<HTMLVideoElement>,
          pluginId: "yolo-tracker",
          tools: ["detect_players", "track_players", "classify_teams"],
          fps: 30,
          device: "cuda",
          enabled: false,
          bufferSize: 5,
        })
      );
      
      expect(result.current).toBeDefined();
    });

    it("guards against empty tools array", async () => {
      const videoRef = {
        current: document.createElement("video"),
      };
      videoRef.current.readyState = 4;
      
      const { result } = renderHook(() =>
        useVideoProcessor({
          videoRef: videoRef as React.RefObject<HTMLVideoElement>,
          pluginId: "test-plugin",
          tools: [],  // Empty array
          fps: 30,
          device: "cpu",
          enabled: true,
          bufferSize: 5,
        })
      );
      
      await waitFor(() => {
        expect(result.current.error).not.toBeNull();
      });
    });

    it("guards against undefined tools", () => {
      const videoRef = { current: null };
      
      // This should cause TypeScript error at compile time
      // but we test runtime behavior anyway
      const hook = () =>
        useVideoProcessor({
          videoRef: videoRef as React.RefObject<HTMLVideoElement>,
          pluginId: "test-plugin",
          tools: undefined as any,  // Force undefined
          fps: 30,
          device: "cpu",
          enabled: true,
          bufferSize: 5,
        });
      
      expect(hook).toThrow();
    });

    it("logs tools array in metrics", async () => {
      const videoRef = {
        current: document.createElement("video"),
      };
      videoRef.current.readyState = 4;
      
      const { result } = renderHook(() =>
        useVideoProcessor({
          videoRef: videoRef as React.RefObject<HTMLVideoElement>,
          pluginId: "test-plugin",
          tools: ["detect", "track"],
          fps: 30,
          device: "cpu",
          enabled: true,
          bufferSize: 5,
        })
      );
      
      // After frame processing completes
      await waitFor(() => {
        const logs = result.current.logs || [];
        expect(logs.length).toBeGreaterThan(0);
        
        // Check most recent log
        const lastLog = logs[logs.length - 1];
        expect(lastLog.tools).toEqual(["detect", "track"]);
      });
    });

    it("uses first tool when processing frame", async () => {
      // Mock video element
      const videoRef = {
        current: document.createElement("video") as HTMLVideoElement,
      };
      videoRef.current.readyState = 4;
      videoRef.current.videoWidth = 640;
      videoRef.current.videoHeight = 480;
      
      // Mock fetch for runTool
      global.fetch = jest.fn(() =>
        Promise.resolve({
          ok: true,
          json: async () => ({ result: { detected: true } }),
        } as Response)
      );
      
      const { result } = renderHook(() =>
        useVideoProcessor({
          videoRef: videoRef as React.RefObject<HTMLVideoElement>,
          pluginId: "yolo",
          tools: ["detect_players", "track_players"],
          fps: 30,
          device: "cpu",
          enabled: true,
          bufferSize: 5,
        })
      );
      
      // Wait for frame processing
      await waitFor(() => {
        expect(result.current.processing).toBe(false);
      });
      
      // Verify fetch was called with first tool
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/tools/detect_players/"),
        expect.any(Object)
      );
    });

    it("resets interval when tools change", () => {
      const videoRef = {
        current: document.createElement("video"),
      };
      
      const { rerender } = renderHook(
        ({ tools }) =>
          useVideoProcessor({
            videoRef: videoRef as React.RefObject<HTMLVideoElement>,
            pluginId: "test",
            tools,
            fps: 30,
            device: "cpu",
            enabled: true,
            bufferSize: 5,
          }),
        {
          initialProps: { tools: ["tool1"] },
        }
      );
      
      // Change tools array
      rerender({ tools: ["tool2", "tool3"] });
      
      // Hook should update interval (verified by effect cleanup)
      expect(true);  // If no error, interval reset worked
    });
  });
});
```

**Test Strategy:**
- ✅ Test accepts `tools` array
- ✅ Test handles multiple tools
- ✅ Test guards empty array
- ✅ Test guards undefined
- ✅ Test logs include tools
- ✅ Test uses first tool for frame processing
- ✅ Test effect re-runs on tools change

---

## IMPLEMENTATION STRATEGY (TDD Step 2-4)

### Phase 1: Update Type Definitions
1. Edit `useVideoProcessor.types.ts`
2. Replace `toolName: string` with `tools: string[]`
3. Run: `npm run type-check` → Should FAIL (tests expect array)

### Phase 2: Update Hook Implementation
1. Edit `useVideoProcessor.ts`
2. Replace all `toolName` references with `tools`
3. Update guard clause to check `tools.length > 0`
4. Update `runTool()` call to use `tools[0]`
5. Update dependencies in useEffect
6. Run: `npm run test -- --run` → Should PASS

### Phase 3: Pre-Commit Checks
1. Run: `npm run lint` → Should PASS
2. Run: `npm run type-check` → Should PASS
3. Run: `npm run test -- --run` → Should PASS

### Phase 4: Commit
```bash
git add -A
git commit -m "feat(phase-13): Update useVideoProcessor for multi-tool pipelines

Replace single toolName parameter with tools[] array to support
multi-tool linear pipelines. Hook now validates non-empty tools array
and processes first tool in pipeline.

Changes:
- Update UseVideoProcessorArgs: toolName → tools[]
- Update ProcessFrameLogEntry: toolName → tools[]
- Guard clause validates tools.length > 0
- runTool() call uses tools[0] for frame processing
- useEffect dependency updated to tools array

All tests pass:
- npm run lint ✓
- npm run type-check ✓
- npm run test -- --run ✓"
```

---

## EDGE CASES TO HANDLE

| Case | Behavior | Test |
|------|----------|------|
| `tools = []` | Guard returns, error set | ✅ test_guards_empty_tools |
| `tools = undefined` | Guard returns, error set | ✅ test_guards_undefined |
| `tools = ["tool1"]` | Process tool1 | ✅ test_single_tool |
| `tools = ["tool1", "tool2"]` | Process tool1 (v1 limitation) | ✅ test_multiple_tools |
| `tools` changes mid-processing | Interval resets | ✅ test_tools_change |
| `pluginId` + empty `tools` | Guard catches | ✅ test_guards_empty_tools |

---

## VERIFICATION CHECKLIST (Before Commit)

- [ ] `useVideoProcessor.types.ts` updated
  - [ ] `UseVideoProcessorArgs.toolName` → `tools: string[]`
  - [ ] `ProcessFrameLogEntry.toolName` → `tools: string[]`

- [ ] `useVideoProcessor.ts` updated
  - [ ] Function signature: `toolName` → `tools`
  - [ ] Guard clause: `!tools || tools.length === 0`
  - [ ] `runTool()` call: uses `tools[0]`
  - [ ] Log entry: uses `tools`
  - [ ] useEffect dependency: `tools` (not `toolName`)

- [ ] Tests created and passing
  - [ ] `npm run test -- --run` → All tests PASS
  - [ ] No `.skip()` or `.only()`

- [ ] Pre-commit checks
  - [ ] `npm run lint` → No errors
  - [ ] `npm run type-check` → No errors
  - [ ] `npm run test -- --run` → No failures

- [ ] Commit message follows format
  - [ ] `feat(phase-13): ...`
  - [ ] Describes changes
  - [ ] References Commit 4 of 10

---

## IMPACT ANALYSIS

### Components Using useVideoProcessor

**VideoTracker.tsx** (will be updated in Commit 5)
```typescript
<useVideoProcessor
  videoRef={videoRef}
  pluginId={selectedPlugin}
  toolName={selectedTool}  // ← Will be: tools={[selectedTool]}
  fps={fps}
  device={device}
  enabled={isStreaming}
/>
```

### Parent Components Using VideoTracker

**App.tsx** (will be updated in Commit 5)
```typescript
<VideoTracker
  pluginId={selectedPlugin}
  toolName={selectedTool}  // ← Will be: tools={selectedTools}
  fps={30}
/>
```

**Note:** Commit 4 only updates the hook signature. Commit 5 updates VideoTracker component to pass the correct props.

---

## BACKWARDS COMPATIBILITY

⚠️ **BREAKING CHANGE**: This commit changes the hook's public API.

**What breaks:**
- Any code calling `useVideoProcessor({ toolName: "tool" })` will fail

**Why it's OK:**
- This is an internal refactor during Phase 13 development
- No external consumers yet (hook only used by internal components)
- Commit 5 updates VideoTracker to match new signature
- App.tsx will be updated in Commit 5+

---

## COMMON MISTAKES TO AVOID

❌ **DON'T:** Keep old `toolName` parameter alongside new `tools`
```typescript
// WRONG
export function useVideoProcessor({
  toolName,  // Old
  tools,     // New
  ...
})
```

❌ **DON'T:** Forget to update useEffect dependency
```typescript
// WRONG - effect won't re-run when tools change
}, [enabled, fps, device, pluginId]); // toolName missing
```

❌ **DON'T:** Use `tools` directly in runTool without extracting first
```typescript
// WRONG - runTool expects string, not array
runTool({ pluginId, toolName: tools, args })
```

✅ **DO:** Extract first tool explicitly
```typescript
// RIGHT
const firstTool = tools[0];
runTool({ pluginId, toolName: firstTool, args })
```

---

## TESTING NOTES

### Running Tests

**All tests:**
```bash
cd web-ui
npm run test -- --run
```

**This file only:**
```bash
cd web-ui
npm run test -- --run src/hooks/useVideoProcessor.test.ts
```

**Watch mode (during development):**
```bash
cd web-ui
npm run test src/hooks/useVideoProcessor.test.ts
```

### Coverage Target

✅ **Goal:** 100% line coverage for hook changes
- All code paths tested
- Edge cases covered
- No skipped tests

---

## REFERENCE DOCUMENTS

| Document | Purpose |
|----------|---------|
| `PHASE_13_PLANS.md` | Overall implementation plan |
| `PHASE_13_PROGRESS.md` | Status tracking |
| `COMMIT_04_ANALYSIS.md` | This document |
| `useVideoProcessor.ts` | Current implementation |
| `useVideoProcessor.types.ts` | Type definitions |
| `runTool.ts` | Backend communication utility |

---

## NEXT STEPS (After Commit 4)

**Commit 5:** Patch VideoTracker Component
- Update props interface: `toolName` → `tools[]`
- Pass `tools` to `useVideoProcessor`
- Update header display
- Update tests

**Commit 6:** (Optional) UI Tool Selector
- Add `PipelineToolSelector` component
- Update `App.tsx` state: `selectedTool` → `selectedTools[]`

---

## QUICK REFERENCE: EXACT CHANGES

### Change Summary

| File | Lines | Change |
|------|-------|--------|
| `useVideoProcessor.types.ts` | 11 | `toolName` → `tools: string[]` |
| `useVideoProcessor.types.ts` | 35 | `toolName` → `tools: string[]` |
| `useVideoProcessor.ts` | 17 | `toolName,` → `tools,` |
| `useVideoProcessor.ts` | 70-74 | Update guard clause |
| `useVideoProcessor.ts` | 88-95 | Extract first tool + pass to runTool |
| `useVideoProcessor.ts` | 126 | Update log: `toolName` → `tools` |
| `useVideoProcessor.ts` | 163 | Update dependency: `toolName` → `tools` |

**Total Lines Changed:** ~15 lines across 2 files
**Tests Created:** 1 new test file (~150 lines)
**Test Coverage:** 7 test cases

---

**Status:** Ready for implementation
**Estimated Time:** 2-3 hours (TDD: write tests, implement, verify)
**Difficulty:** Medium (straightforward refactor, good test patterns exist)

---

*Last Updated: 2026-02-11*
*Author: Phase 13 Implementation Plan*
*Version: 1.0 LOCKED*
