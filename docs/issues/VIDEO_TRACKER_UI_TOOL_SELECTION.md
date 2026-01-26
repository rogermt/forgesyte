# GitHub Issue: VideoTracker UI - Tool Selection and Overlay Toggles UX

## Summary
The VideoTracker component has two related issues:
1. **Missing Tool Selector**: Users cannot select which tool to run from the plugin's available tools
2. **Confusing UI Labels**: "Tools to use" label is misleading - checkboxes control overlay visibility, not tool selection

## Issue #85: VideoTracker UX - Tool Selection vs Overlay Visibility

### Problem 1: No Tool Selector Dropdown
**Location**: `web-ui/src/components/VideoTracker.tsx`

The VideoTracker component receives `toolName` as a prop but has no dropdown to change it. Users can only run the tool that was pre-selected.

**Expected Behavior**:
- Users should see a dropdown of available tools from the plugin manifest
- Selecting a tool should update the `toolName` passed to `useVideoProcessor`

**Current Code**:
```tsx
export function VideoTracker({ pluginId, toolName }: VideoTrackerProps) {
  // toolName is passed as prop - no way to change it!
```

### Problem 2: Confusing "Tools to use" Label
**Location**: `web-ui/src/components/VideoTracker.tsx` - Overlay toggles section

The checkboxes for Players, Tracking, Ball, Pitch, Radar control **visual overlay visibility**, not tool execution. The current UI doesn't make this clear.

**Current UI**:
```
[Toggle] Players
[Toggle] Tracking
[Toggle] Ball
...
```

**Issues**:
- No section header distinguishing "Overlay Layers" from "Tool Selection"
- No tooltips explaining the purpose of each checkbox
- Checkboxes use same terminology ("Tools") as the actual tool execution

### Crossover with Plugin Lookup Fix
**Related Commits**:
- `ff6fb7f` - Fix: `run_plugin_tool()` now uses `registry.get()` instead of `registry.list().get()`
- This fix ensures the backend can correctly find and execute the selected tool

**Why this matters**:
1. Frontend needs a tool selector dropdown
2. Dropdown selection calls backend API
3. Backend uses `registry.get(plugin_id)` to find plugin instance
4. Plugin instance must have callable methods for tool execution
5. The plugin lookup fix ensures step 3-4 work correctly

Without the lookup fix, even if we add the dropdown, the tool execution would fail.

---

## Proposed Fix

### Phase 1: Add Tool Selector to VideoTracker
**File**: `web-ui/src/components/VideoTracker.tsx`

1. Add `toolList` state loaded from plugin manifest
2. Add tool selector dropdown in the header area
3. Update `toolName` state when user selects a different tool

```tsx
// Add to imports
import { useManifest } from "../hooks/useManifest";

// Add to component state
const { manifest, loading: manifestLoading } = useManifest(pluginId);
const [selectedTool, setSelectedTool] = useState(toolName);

// Add tool selector in header
{manifestLoading ? (
  <span>Loading tools...</span>
) : (
  <select
    value={selectedTool}
    onChange={(e) => setSelectedTool(e.target.value)}
    style={styles.dropdown}
  >
    {Object.keys(manifest?.tools || {}).map((name) => (
      <option key={name} value={name}>{name}</option>
    ))}
  </select>
)}
```

### Phase 2: Improve Overlay UI Labels
**File**: `web-ui/src/components/VideoTracker.tsx`

1. Add section header "Overlay Layers"
2. Add tooltips to each checkbox
3. Move toggles below video controls (already there)

```tsx
{/* Section Header */}
<h4 style={{ margin: "0 0 8px 0", fontSize: "12px", color: "var(--text-secondary)" }}>
  Overlay Layers
</h4>

{/* Toggles with tooltips */}
{OVERLAY_KEYS.map((key) => (
  <div key={key} style={styles.toggleItem}>
    <input
      type="checkbox"
      title={`Toggle ${key} overlay visibility`}
      checked={overlayToggles[key]}
      onChange={() => handleToggle(key)}
    />
    <label title={`Show/hide ${key} in video overlay`}>
      {key.charAt(0).toUpperCase() + key.slice(1)}
    </label>
  </div>
))}
```

### Phase 3: Update Tests
**File**: `web-ui/src/components/VideoTracker.test.tsx`

Add tests for:
- Tool selection dropdown
- Tool selection updates `useVideoProcessor` call
- Overlay toggles don't affect tool execution

```ts
describe("Tool selection", () => {
  it("shows tool selector with available tools", () => {
    render(<VideoTracker pluginId="yolo-tracker" toolName="player_tracking" />);
    expect(screen.getByLabelText(/tool to run/i)).toBeInTheDocument();
  });

  it("updates tool when selection changes", () => {
    render(<VideoTracker pluginId="yolo-tracker" toolName="player_tracking" />);
    // Change selection
    fireEvent.change(screen.getByLabelText(/tool to run/i), {
      target: { value: "ball_tracking" }
    });
    // Verify useVideoProcessor was called with new tool
  });
});

describe("Overlay toggles", () => {
  it("does not affect tool execution", () => {
    const spy = vi.spyOn(useVideoProcessorModule, "useVideoProcessor");
    render(<VideoTracker ... />);
    // Toggle overlay
    fireEvent.click(screen.getByLabelText(/players/i));
    // Tool execution should NOT be called
    expect(spy).not.toHaveBeenCalled();
  });
});
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `web-ui/src/components/VideoTracker.tsx` | Add tool selector, improve overlay labels |
| `web-ui/src/components/VideoTracker.test.tsx` | Add tests for tool selection |
| `web-ui/src/hooks/useVideoProcessor.ts` | May need update to accept dynamic toolName |

## Related Issues
- #83: Plugin 'yolo-tracker' not found (fixed in ff6fb7f)
- #84: VideoTracker endpoint routing

## Labels
- bug
- frontend
- ui
- enhancement
- priority/high

## Test Checklist

- [ ] Tool selector dropdown appears with available tools
- [ ] Selecting a tool updates the backend call
- [ ] Overlay toggles are labeled "Overlay Layers"
- [ ] Checkboxes have tooltips explaining visibility control
- [ ] No cross-wiring between tool selection and overlay toggles
- [ ] Backend plugin lookup works correctly (via registry.get())

