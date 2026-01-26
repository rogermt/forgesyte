# UI Drift Issue: Tool Selection Not Wired to Upload Flow

## Summary
Users see "Select a tool" message even after selecting a tool. The UI hangs after pressing "Upload" because the `selectedTool` state is not properly wired into the upload flow.

## Symptoms
- **"Select a tool"** message persists even after user selects a tool
- UI hangs when pressing Upload button
- API calls fail with malformed endpoints like `/v1/plugins/yolo-tracker/tools//run` (double slash = null toolName)

## Root Cause Analysis

### 1. `App.tsx` - selectedTool state is never updated (Critical)
```tsx
// Line 31 - Missing setSelectedTool setter!
const [selectedTool] = useState<string>("");  // ❌ Cannot update state
```

The `selectedTool` state is declared but **never updated** because the setter is not captured from `useState`.

### 2. `App.tsx` - ToolSelector component is missing from UI (Critical)
The sidebar panel only has `PluginSelector` and `JobList` components. **There is no `ToolSelector` component rendered**, so users cannot select a tool at all!

```tsx
// Sidebar only has PluginSelector - ToolSelector is MISSING
<div style={styles.panel}>
  <PluginSelector
    selectedPlugin={selectedPlugin}
    onPluginChange={handlePluginChange}
    disabled={streamEnabled}
  />
</div>

{viewMode === "jobs" && (
  <div style={styles.panel}>
    <JobList onJobSelect={setSelectedJob} />
  </div>
)}
```

### 3. `App.tsx` - Upload handler lacks validation
```tsx
const handleFileUpload = useCallback(
  async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!selectedPlugin) return;  // ✅ Checks plugin
    // ❌ Missing check for !selectedTool
    // ... continues to attempt upload with empty toolName
  },
  [selectedPlugin]
);
```

### 4. `useVideoProcessor.ts` - No validation for empty toolName
```tsx
const processFrame = async () => {
  // ...
  const endpoint = `/v1/plugins/${pluginId}/tools/${toolName}/run`;
  // ❌ No guard if toolName is empty - builds malformed URL
  // → /v1/plugins/p/tools//run
};
```

## Expected vs Actual Behavior

### Expected Flow
```
1. User selects plugin → selectedPlugin = "yolo-tracker"
2. User selects tool from ToolSelector → selectedTool = "detect_players"
3. VideoTracker renders (because manifest && selectedTool are truthy)
4. User uploads video → handleFileUpload validates both pluginId and toolName
5. API calls /v1/plugins/yolo-tracker/tools/detect_players/run ✅
```

### Actual Flow
```
1. User selects plugin → selectedPlugin = "yolo-tracker"
2. User cannot find ToolSelector (component not rendered) ❌
3. Even if tool selected programmatically, selectedTool = "" (never updates) ❌
4. Upload attempts with toolName = "" → malformed endpoint ❌
5. 404 error → UI hangs ❌
```

## Impact
- **Critical**: Users cannot complete video uploads
- **UX Failure**: "Select a tool" message appears even when tool is logically selected
- **API Errors**: Malformed endpoints cause 404 errors
- **Silent Failure**: No error message displayed to user

## Severity
🔴 **Critical** - Blocks core functionality

## Affected Files
- `web-ui/src/App.tsx` - Lines 31, sidebar rendering, handleFileUpload
- `web-ui/src/hooks/useVideoProcessor.ts` - processFrame function
- `web-ui/src/components/ToolSelector.tsx` - Already exists but not used

## Proposed Fix

### 1. Fix selectedTool state in App.tsx
```tsx
// Before
const [selectedTool] = useState<string>("");

// After
const [selectedTool, setSelectedTool] = useState<string>("");
```

### 2. Add ToolSelector to sidebar in App.tsx
```tsx
<div style={styles.panel}>
  <PluginSelector
    selectedPlugin={selectedPlugin}
    onPluginChange={handlePluginChange}
    disabled={streamEnabled}
  />
</div>

{/* ADD ToolSelector */}
<div style={styles.panel}>
  <ToolSelector
    pluginId={selectedPlugin}
    selectedTool={selectedTool}
    onToolChange={setSelectedTool}
    disabled={streamEnabled}
  />
</div>
```

### 3. Add validation in handleFileUpload
```tsx
const handleFileUpload = useCallback(
  async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!selectedPlugin) {
      console.error("Upload aborted: plugin not selected");
      return;
    }
    if (!selectedTool) {
      console.error("Upload aborted: tool not selected");
      return;
    }
    // ... continue with upload
  },
  [selectedPlugin, selectedTool]
);
```

### 4. Add guard in useVideoProcessor.ts
```tsx
const processFrame = async () => {
  if (!pluginId || !toolName) {
    console.error("Frame processing aborted: pluginId or toolName missing");
    return;
  }
  // ... continue processing
};
```

### 5. Disable upload input until tool is selected
```tsx
<input
  type="file"
  accept="image/*"
  onChange={handleFileUpload}
  disabled={isUploading || !selectedPlugin || !selectedTool}
/>
```

## Testing Checklist

### Unit Tests
- [ ] `App.tsx` - Test that setSelectedTool is called when ToolSelector changes
- [ ] `App.tsx` - Test that handleFileUpload returns early when !selectedTool
- [ ] `useVideoProcessor.ts` - Test early return when toolName is empty

### Integration Tests
- [ ] End-to-end flow: Plugin selection → Tool selection → Upload → Success
- [ ] Upload button disabled until both plugin and tool selected
- [ ] Error message displayed when upload fails due to missing tool

### Manual Verification
- [ ] ToolSelector appears in sidebar when plugin is selected
- [ ] Tool dropdown shows available tools from manifest
- [ ] Upload works with valid plugin + tool combination
- [ ] Upload gracefully fails with clear error when tool not selected

## Related Documentation
- `docs/implementation/video_tracker/TODO_TASK_6_3.md` - Overlay toggles implementation
- `ARCHITECTURE.md` - Overall component architecture
- `docs/design/PLUGIN_WEB_UI.md` - UI design spec

## References
- Component: `ToolSelector.tsx` - Already implements ToolSelector component
- Hook: `useManifest.ts` - Loads plugin manifest for tool list
- Hook: `useVideoProcessor.ts` - Processes video frames with selected tool

---

**Labels:** bug, critical, frontend, ui, regression
**Priority:** P0

