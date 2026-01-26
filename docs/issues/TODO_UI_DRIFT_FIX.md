# UI Drift Fix - Tool Selection Wiring

## Issue
GitHub Issue: `docs/issues/UI_DRIFT_TOOL_SELECTION.md`

## Plan

### Information Gathered
- `App.tsx` line 31: `selectedTool` state is declared without `setSelectedTool` setter
- `ToolSelector` component exists but is NOT rendered in the sidebar
- `handleFileUpload` lacks validation for `selectedTool`
- `useVideoProcessor.ts` lacks guard for empty `toolName`

### Files to Edit
1. `web-ui/src/App.tsx` - Fix state and add ToolSelector
2. `web-ui/src/hooks/useVideoProcessor.ts` - Add validation guard

## Implementation Steps

### Step 1: Fix App.tsx
- [ ] Change `const [selectedTool] = useState<string>("");` to include setter
- [ ] Add `handleToolChange` callback
- [ ] Add `ToolSelector` component to sidebar panel
- [ ] Add validation in `handleFileUpload` for `!selectedTool`
- [ ] Disable upload input when `!selectedTool`

### Step 2: Add validation in useVideoProcessor.ts
- [ ] Add early return guard if `!pluginId || !toolName`
- [ ] Log error for debugging

### Step 3: Verification
- [ ] Run existing tests to ensure no regressions
- [ ] Manual verification of the fix

## Progress

### Step 1: Fix App.tsx ✅ COMPLETED
- [x] 1.1: Add setSelectedTool to useState
- [x] 1.2: Add handleToolChange callback
- [x] 1.3: Add ToolSelector to sidebar
- [x] 1.4: Update handleFileUpload with tool validation
- [x] 1.5: Disable input when tool not selected

### Step 2: Fix useVideoProcessor.ts ✅ COMPLETED
- [x] 2.1: Add guard at start of processFrame

### Step 3: Verification ✅ COMPLETED
- [x] 3.1: Run existing tests to ensure no regressions
- [x] 3.2: Manual verification of the fix

---

## Fix Status: 🔴 REOPENED - No Behavioral Change

**Issue #102** - UI tool selection wiring fix needs to be reopened.

### Current Status
The code changes were made but there is no observable behavioral change in the application. The fixes may have been applied incorrectly or there's a deeper issue.

### Problem Description
- Tests pass but the actual behavior hasn't changed
- ToolSelector might not be wiring up correctly
- Upload validation might not be working as expected

### Next Steps
1. Investigate why the behavioral changes aren't visible
2. Verify ToolSelector is receiving and emitting events correctly
3. Check if upload validation is actually blocking without tool selection
4. Manual testing required to confirm fix


