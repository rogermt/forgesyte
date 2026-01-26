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
3. `web-ui/src/App.test.tsx` - Add tests for the fixes

## Implementation Steps

### Step 1: Fix selectedTool state in App.tsx
- [x] Change `const [selectedTool] = useState<string>("");` to include setter
- [x] Add `ToolSelector` component to sidebar panel
- [x] Add validation in `handleFileUpload` for `!selectedTool`
- [x] Disable upload input when `!selectedTool`

### Step 2: Add validation in useVideoProcessor.ts
- [x] Add early return guard if `!pluginId || !toolName`
- [x] Log error for debugging

### Step 3: Update tests
- [ ] Add test for ToolSelector rendering in App.tsx
- [ ] Add test for handleFileUpload validation
- [ ] Add test for useVideoProcessor guard

### Step 4: Verify
- [ ] Run existing tests to ensure no regressions
- [ ] Manual verification of the fix

## Progress

### Step 1: Fix App.tsx ✅ COMPLETED
- [x] Read App.tsx to understand current structure
- [x] Add setSelectedTool to useState
- [x] Import ToolSelector
- [x] Add ToolSelector to sidebar
- [x] Update handleFileUpload with tool validation
- [x] Disable input when tool not selected

### Step 2: Fix useVideoProcessor.ts ✅ COMPLETED
- [x] Read useVideoProcessor.ts
- [x] Add guard at start of processFrame

### Step 3: Update tests
- [ ] Read App.test.tsx
- [ ] Add mock for ToolSelector
- [ ] Add tests for the fixes

### Step 4: Verification
- [ ] Run test suite
- [ ] Verify all tests pass

