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


