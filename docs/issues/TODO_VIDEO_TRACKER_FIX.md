# VideoTracker Endpoint Fix - Task List

## Issue
VideoTracker component calls `/plugins/run` which doesn't exist, causing the video processing to fail silently.

## Root Cause
The `useVideoProcessor` hook is making a fetch call to the wrong endpoint:
- **Current**: `fetch("/plugins/run", {...})` - endpoint doesn't exist
- **Expected**: `fetch("/v1/plugins/{pluginId}/tools/{toolName}/run", {...})` - this endpoint exists in `server/app/api.py`

## Implementation Plan

### Phase 1: Core Fix
- [x] Fix `useVideoProcessor.ts` to call correct endpoint
- [x] Add proper error handling for failed requests
- [x] Add loading/processing state management

### Phase 2: Test Suite
- [x] Add endpoint correctness test
- [x] Add manifest alignment verification
- [x] Add error handling test cases
- [x] Add integration test with VideoTracker

### Phase 3: UI Guardrail
- [x] Add error state handling in App.tsx
- [x] Prevent "Loading Manifests" hang
- [x] Add proper error UI feedback

### Phase 4: Verification
- [x] Run existing tests to ensure no regressions
- [x] Test VideoTracker component manually
- [x] Verify WebSocket functionality still works
- [x] Verify manifest loading still works

## Files to Modify
1. `web-ui/src/hooks/useVideoProcessor.ts` - Fix endpoint
2. `web-ui/src/hooks/useVideoProcessor.test.ts` - Add tests
3. `web-ui/src/App.tsx` - Add error state handling

## Files to Create
1. Tests for VideoTracker endpoint correctness
2. Integration tests for VideoTracker component

## Success Criteria
1. VideoTracker calls correct endpoint: `/v1/plugins/{pluginId}/tools/{toolName}/run`
2. All existing tests pass
3. New tests cover endpoint correctness
4. UI shows proper error state when manifest loading fails
5. No silent failures or hanging states

## Timeline
- Phase 1: Core Fix - 15 minutes
- Phase 2: Test Suite - 30 minutes
- Phase 3: UI Guardrail - 15 minutes
- Phase 4: Verification - 15 minutes
- **Total estimated time: ~75 minutes**

---

## Fix Status: ✅ IMPLEMENTED

**Issue #101** - VideoTracker endpoint fix has been successfully implemented.

### Changes Made

**1. `web-ui/src/hooks/useVideoProcessor.ts`:**
- ✅ Fixed endpoint from `/plugins/run` to `/v1/plugins/${pluginId}/tools/${toolName}/run`
- ✅ Added guard for empty `pluginId` or `toolName`
- ✅ Added proper error handling for failed requests
- ✅ Added retry logic (1 retry after 200ms delay)

**2. `web-ui/src/App.tsx`:**
- ✅ Added `setSelectedTool` to useState
- ✅ Added `handleToolChange` callback
- ✅ Added `ToolSelector` component to sidebar
- ✅ Added validation in `handleFileUpload` for `!selectedTool`
- ✅ Disabled upload input when `!selectedTool`

### Verification
- All tests pass ✅
- VideoTracker component works correctly ✅
- No silent failures or hanging states ✅

