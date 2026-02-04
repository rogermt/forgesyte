# Phase 10 — Plugin Inspector Wireframe

UI wireframe and layout specification for PluginInspector.tsx.

This is a **reference wireframe**, not a governance rule. Implementation flexibility is allowed as long as all required elements are present.

---

# 1. Visual Wireframe (ASCII)

## 1.1 Default State (Minimal Data)

```
┌────────────────────────────────────────────────────────────┐
│ # plugin-inspector                                         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  No plugins running                                        │
│                                                            │
│  (waiting for plugin_status messages...)                   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## 1.2 With Single Plugin (Running)

```
┌────────────────────────────────────────────────────────────┐
│ Plugin Inspector                                    ✕ Close │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ Plugin: player_detection                                   │
│ Status: ⚙️ Running (animated spinner)                     │
│ Timing: 145.5 ms                                          │
│                                                            │
│ [████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 145.5 ms     │
│                                                            │
│ ─────────────────────────────────────────────            │
│ Warnings: 0                                                │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## 1.3 With Multiple Plugins (Mixed States)

```
┌────────────────────────────────────────────────────────────┐
│ Plugin Inspector                                    ✕ Close │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ player_detection                       │ Status │ Timing   │
│ ✓ Completed                            │        │ 145.5 ms │
│ [████████████████░░░░░░░░░░░░░░░░░░]   │        │          │
│                                                            │
│ ball_detection                         │ Status │ Timing   │
│ ⚙️ Running                             │        │  98.2 ms │
│ [██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░]  │        │          │
│                                                            │
│ pitch_detection                        │ Status │ Timing   │
│ ⏳ Started                             │        │  12.0 ms │
│ [██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]  │        │          │
│                                                            │
│ ─────────────────────────────────────────────────────────│
│ Warnings: 2                                               │
│ • Pitch corners not detected (pitch_detection)            │
│ • Low confidence in team classification (team_class...)   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## 1.4 With Errors and Warnings

```
┌────────────────────────────────────────────────────────────┐
│ Plugin Inspector                                    ✕ Close │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ ball_detection                                            │
│ ✗ Failed                              │ Timing: N/A        │
│ [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]                     │
│                                                            │
│ ─────────────────────────────────────────────────────────│
│ Warnings: 3                                               │
│ • CRITICAL: Ball detection failed                         │
│ • Pitch detection: Corners not found                      │
│ • Team classification: Low confidence                     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

# 2. Required Elements (Authoritative)

These elements MUST exist for Phase 10 compliance:

### 2.1 Container
- **Element ID:** `#plugin-inspector` (REQUIRED)
- **CSS Class:** `plugin-inspector` (recommended)
- **Display:** Visible when component mounts

### 2.2 Plugin List
- **Display:** One entry per plugin
- **Order:** Execution order (first plugin first)
- **Content per plugin:**
  - Plugin name (string)
  - Status badge (icon + text)
  - Timing (numeric value in ms)

### 2.3 Status Badge
- **Values:** "started", "running", "completed", "failed"
- **Visual Indicators:**
  - ⏳ Started (gray)
  - ⚙️ Running (blue, animated)
  - ✓ Completed (green)
  - ✗ Failed (red)

### 2.4 Timing Display
- **Format:** Numeric value + "ms" unit
- **Precision:** 1 decimal place (e.g., "145.5 ms")
- **Visual:** Bar chart OR numeric list (flexible)

### 2.5 Warnings Section
- **Header:** "Warnings:" label
- **Display:** Unordered list
- **Content:** Each warning shows:
  - Plugin name (if available)
  - Message text
- **Behavior:** Warnings accumulate (not replaced)
- **Scrolling:** If >10 warnings, list becomes scrollable

### 2.6 Empty State
- **Trigger:** No plugins running
- **Message:** "No plugins running" or "Waiting for plugin data..."

---

# 3. Optional / Flexible Elements (NOT Authoritative)

These elements are allowed but not required:

### 3.1 Header / Title
- "Plugin Inspector" label
- Close button (✕)
- Collapse/expand toggle

### 3.2 Layout Variants
- Vertical list (one per line)
- Horizontal tabs (one tab per plugin)
- Tree view (expandable plugins)
- Card layout (grid of plugins)

### 3.3 Visualizations
- Horizontal bar chart (timing comparison)
- Pie chart (timing distribution)
- Timeline view (plugin execution order)
- Color coding (slow/medium/fast plugins)

### 3.4 Metadata Display
- Plugin version
- Model file name
- Input/output format
- Expandable details per plugin

### 3.5 Interactive Features
- Click plugin to expand details
- Sort by timing / status / name
- Filter warnings by severity
- Copy warning text
- Export plugin timings as CSV

---

# 4. Layout Grid (Flexible)

This is a sample responsive grid layout:

```
Desktop (>768px):
┌─────────────────────────────────────────────┐
│ Plugin Inspector                        [✕] │
├──────────────────┬──────────────┬───────────┤
│ Plugin Name      │ Status       │ Timing    │
├──────────────────┼──────────────┼───────────┤
│ player_detection │ ✓ Completed  │ 145.5 ms  │
│ ball_detection   │ ⚙️ Running   │  98.2 ms  │
│ pitch_detection  │ ⏳ Started   │  12.0 ms  │
└──────────────────┴──────────────┴───────────┘

Mobile (<768px):
┌──────────────────────────┐
│ Plugin Inspector     [✕] │
├──────────────────────────┤
│ player_detection         │
│ Status: ✓ Completed      │
│ Timing: 145.5 ms         │
├──────────────────────────┤
│ ball_detection           │
│ Status: ⚙️ Running       │
│ Timing:  98.2 ms         │
├──────────────────────────┤
│ pitch_detection          │
│ Status: ⏳ Started       │
│ Timing:  12.0 ms         │
└──────────────────────────┘
```

---

# 5. Data Model (TypeScript)

```typescript
interface PluginInspectorProps {
  // From useRealtime() context
  pluginTimings: Record<string, number>;           // name -> ms
  pluginMetadata?: Record<string, PluginMetadata>; // optional
  pluginStatus: Record<string, PluginStatus>;      // name -> status
  warnings: Array<{
    plugin: string;
    message: string;
    severity?: 'low' | 'medium' | 'high';
  }>;
}

interface PluginMetadata {
  version: string;
  model: string;
  input_shape?: number[];
  output_format?: string;
  confidence_default?: number;
  capabilities?: string[];
}

type PluginStatus = 'started' | 'running' | 'completed' | 'failed';
```

---

# 6. Behavior Specification

### 6.1 On Component Mount
```
- Read initial state from useRealtime()
- If no plugins: Show empty state message
- If plugins present: Render all with latest data
```

### 6.2 On New `plugin_status` Message
```
- Update pluginStatus[plugin] with new status
- Update pluginTimings[plugin] with timing_ms
- If plugin not in list: Add to list
- Re-render immediately (React state change)
```

### 6.3 On New `warning` Message
```
- Append warning to warnings array
- Do NOT deduplicate (show all warnings)
- Do NOT clear old warnings
- Scroll to show new warning
- Re-render immediately
```

### 6.4 On Job Restart
```
- useRealtime() resets state
- Component receives empty state
- Show empty state message or reset display
```

### 6.5 On WebSocket Disconnect
```
- Component stays visible
- Show "Reconnecting..." indicator (optional)
- Continue displaying last known state
- Resume updates when reconnected
```

---

# 7. Styling Guidelines (Recommendations)

### 7.1 Colors
```css
/* Status colors */
--status-started: #9CA3AF     /* Gray */
--status-running: #3B82F6     /* Blue */
--status-completed: #10B981   /* Green */
--status-failed: #EF4444      /* Red */

/* Timing bars */
--bar-background: #E5E7EB     /* Light gray */
--bar-fill-good: #10B981      /* Green (< 100ms) */
--bar-fill-med: #F59E0B       /* Amber (100-500ms) */
--bar-fill-slow: #EF4444      /* Red (> 500ms) */
```

### 7.2 Typography
```css
/* Plugin name */
font-size: 1rem;
font-weight: 600;
color: #1F2937;

/* Status badge */
font-size: 0.875rem;
font-weight: 500;

/* Timing value */
font-family: monospace;
font-size: 0.875rem;
color: #374151;
```

### 7.3 Spacing
```css
/* Container padding */
padding: 1rem;

/* Plugin item spacing */
margin-bottom: 1rem;

/* Warnings section */
margin-top: 1.5rem;
padding-top: 1rem;
border-top: 1px solid #D1D5DB;
```

---

# 8. Accessibility Requirements

### 8.1 ARIA Labels
```html
<div id="plugin-inspector" role="region" aria-label="Plugin Inspector">
  <!-- Content -->
</div>
```

### 8.2 Status Badges
```html
<!-- Don't rely on color alone; include text -->
<span aria-label="Status: Running">
  ⚙️ Running
</span>
```

### 8.3 Warning List
```html
<ul role="list" aria-label="Plugin warnings">
  <li><!-- warning --></li>
</ul>
```

### 8.4 Timing Bars
```html
<div role="progressbar" aria-valuenow="145" aria-valuemax="500">
  <!-- bar visualization -->
</div>
```

---

# 9. Responsive Breakpoints

```css
/* Mobile (< 640px) */
- Single column layout
- Stacked plugin cards
- Simplified timing display (no bars, just numbers)

/* Tablet (640px - 1024px) */
- Two column layout
- Side-by-side timing bars
- Full warning list visible

/* Desktop (> 1024px) */
- Full table/grid layout
- Optional: Timing chart/visualization
- Optional: Scrollable warning sidebar
```

---

# 10. Error Handling

### 10.1 Missing Data
```
If pluginTimings is undefined:
  → Show "No timing data available"

If pluginStatus is undefined:
  → Show "No plugin data available"

If warnings is empty:
  → Show "No warnings"
```

### 10.2 Invalid Values
```
If timing < 0:
  → Display as "N/A"

If timing > 999999:
  → Display with scientific notation or truncate

If status is unknown:
  → Display as "Unknown"
```

---

# 11. Performance Considerations

### 11.1 Re-render Optimization
```typescript
// Use React.memo to prevent unnecessary re-renders
export const PluginInspector = React.memo(({ ... }) => {
  // Component
});

// Use useMemo for derived data
const sortedPlugins = useMemo(() => {
  return Object.entries(pluginStatus).sort((a, b) => a[0].localeCompare(b[0]));
}, [pluginStatus]);
```

### 11.2 Large Lists
```
If > 100 warnings:
  → Show last 100 and indicator "... and N more"
  → Or: Use virtual scrolling (windowing)

If > 50 plugins:
  → Group by status
  → Or: Use pagination
```

---

# 12. Testing the Wireframe

### 12.1 Rendering Tests
```typescript
it('renders with id="plugin-inspector"', () => {
  const element = screen.getByRole('region', { name: /inspector/i });
  expect(element.id).toBe('plugin-inspector');
});

it('displays all required elements', () => {
  // Check for: plugin names, statuses, timings, warnings
});
```

### 12.2 Data Display Tests
```typescript
it('displays plugins in execution order', () => {
  // Verify plugin order matches data
});

it('updates timings on new plugin_status', () => {
  // Update prop, verify re-render
});

it('accumulates warnings without clearing', () => {
  // Add warning, verify list grows
});
```

### 12.3 Responsive Tests
```typescript
it('adapts layout for mobile viewport', () => {
  // Render at 400px, verify single column
});

it('adapts layout for desktop viewport', () => {
  // Render at 1024px, verify full table
});
```

---

# 13. Summary

PluginInspector is a flexible, real-time display of plugin execution data:

✅ **Required Elements:** Container ID, plugin names, status badges, timings, warnings
✅ **Flexible Layout:** Table, cards, tabs, or custom (choose one)
✅ **Real-Time Updates:** Responds to plugin_status and warning messages
✅ **Accessible:** ARIA labels, semantic HTML, keyboard navigation
✅ **Responsive:** Mobile-friendly, desktop-optimized
✅ **Performant:** Memoized, virtual scrolling for large lists

This wireframe is a **reference**, not a mandate. Implementation details (colors, fonts, exact layout) are left to the developer, as long as all required elements are present and functional.

