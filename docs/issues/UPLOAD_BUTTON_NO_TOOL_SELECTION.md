# Issue: Upload Button Shows "Select tools" Instead of Upload UI

## Summary
When clicking the "Upload" tab, the UI shows "Select tools" instead of allowing users to select a tool and upload an image/file.

## Root Cause Analysis

### Missing ToolSelector Component

The `App.tsx` component is missing the `ToolSelector` component which allows users to select a tool from the loaded plugin's manifest.

**Current State:**
- `ToolSelector` component exists at `web-ui/src/components/ToolSelector.tsx`
- Component is NOT imported or used in `App.tsx`
- `selectedTool` state is defined but never updated (`const [selectedTool] = useState<string>("")`)

### Historical Context

Commit `d5f08b2` removed `setSelectedTool` variable:
```
d5f08b2 fix(app): Remove unused setSelectedTool variable
```

This broke tool selection because:
1. The state setter was removed
2. `ToolSelector` component was never added to render the tool selector UI
3. Users have no way to change `selectedTool` from empty string

### Code Evidence

**App.tsx line ~37:**
```javascript
const [selectedTool] = useState<string>("");  // No setter - can't update!
```

**App.tsx sidebar (lines ~180-195):**
```jsx
<aside style={styles.sidebar}>
  <div style={styles.panel}>
    <PluginSelector
      selectedPlugin={selectedPlugin}
      onPluginChange={handlePluginChange}
      disabled={streamEnabled}
    />
  </div>
  {/* ToolSelector is MISSING here! */}
</aside>
```

**Upload view logic (lines ~254-264):**
```jsx
{viewMode === "upload" && manifest && selectedTool && (
  // Only renders if BOTH manifest AND selectedTool exist
  // But selectedTool is always empty string!
  ...
)}
```

## Expected Behavior
1. User selects a plugin → manifest loads
2. User selects a tool from ToolSelector → selectedTool updates
3. Upload view shows the appropriate upload/VideoTracker UI

## Actual Behavior
1. User selects a plugin → manifest loads
2. No tool selector UI exists → selectedTool stays empty
3. Upload view shows "Select tools" message

## Fix Required

### 1. Import ToolSelector in App.tsx
```javascript
import { ToolSelector } from "./components/ToolSelector";
```

### 2. Fix selectedTool state
```javascript
const [selectedTool, setSelectedTool] = useState<string>("");
```

### 3. Add handleToolChange callback
```javascript
const handleToolChange = useCallback((toolName: string) => {
  setSelectedTool(toolName);
}, []);
```

### 4. Render ToolSelector in sidebar
```jsx
<div style={styles.panel}>
  <ToolSelector
    pluginId={selectedPlugin}
    selectedTool={selectedTool}
    onToolChange={handleToolChange}
    disabled={streamEnabled}
  />
</div>
```

## Affected Files
- `web-ui/src/App.tsx` - Missing ToolSelector import and rendering

## Test Status
- Unit tests: Unknown (may not catch this UI issue)
- E2E tests: May fail for upload flow

## Priority
**High** - This breaks core functionality of the upload feature

## Labels
- bug
- frontend
- ui
- critical

