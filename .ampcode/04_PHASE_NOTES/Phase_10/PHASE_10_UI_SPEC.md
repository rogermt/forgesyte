# Phase 10 UI Spec

Complete UI specification for Phase 10.

All changes are additive and MUST NOT break Phase 9 UI contract.

---

# 1. New Components

## 1.1 RealtimeOverlay.tsx

**Purpose:**
Main container for all real-time UI elements (frame viewer, progress, inspector).

**Location:**
```
web-ui/src/components/RealtimeOverlay.tsx
```

**Props:**
```typescript
interface RealtimeOverlayProps {
  isVisible: boolean;
  onClose: () => void;
}
```

**Responsibilities:**
- Subscribe to RealtimeContext
- Render frame viewer (when frame messages arrive)
- Render progress bar (when progress messages arrive)
- Render plugin inspector (when plugin_status messages arrive)
- Handle layout (flex, responsive)
- Display errors/warnings prominently

**Layout:**
```
┌─────────────────────────────────┐
│   Real-Time Overlay             │
├─────────────────────────────────┤
│                                 │
│  [Frame Viewer]                 │
│  (animated overlays)            │
│                                 │
├─────────────────────────────────┤
│  [Progress Bar] (id=progress-bar)│
├─────────────────────────────────┤
│  [Plugin Inspector]             │
│  (id=plugin-inspector)          │
└─────────────────────────────────┘
```

**Behavior:**
- Component is hidden by default (`isVisible={false}`)
- Click close button calls `onClose()`
- Updates in real-time as messages arrive
- Does NOT block UI if WebSocket disconnects

**Tests:**
- `test_realtime_overlay_renders.spec.ts` - Component renders when visible
- `test_realtime_overlay_closes.spec.ts` - Close button works
- `test_realtime_overlay_updates.spec.ts` - Updates on frame message
- `test_realtime_overlay_error.spec.ts` - Shows error gracefully

---

## 1.2 ProgressBar.tsx

**Purpose:**
Display job progress (0-100%) with stage label.

**Location:**
```
web-ui/src/components/ProgressBar.tsx
```

**Props:**
```typescript
interface ProgressBarProps {
  progress: number;  // 0-100
  stage?: string;    // e.g., "Processing frame 3 of 5"
  plugin?: string;   // e.g., "player_detection"
}
```

**DOM Element:**
```html
<div id="progress-bar" class="progress-bar">
  <div class="progress-bar-fill" style="width: {progress}%"></div>
  <p class="progress-bar-label">{stage || plugin || 'Processing...'}</p>
</div>
```

**Requirements:**
- Element ID MUST be `#progress-bar` (not `#progress-bar-v2`, etc.)
- Bar MUST smoothly animate progress changes
- Progress value MUST be validated (0-100)
- Label text MUST update without flickering
- Bar MUST be accessible (aria-label, role="progressbar")

**CSS Classes:**
- `.progress-bar` - Container
- `.progress-bar-fill` - Animated fill
- `.progress-bar-label` - Stage text

**Behavior:**
- On `progress` message: Update bar and label
- If progress goes backward: Log warning but still update (graceful)
- If progress invalid (< 0 or > 100): Use closest valid value (0 or 100)

**Accessibility:**
```typescript
<div
  id="progress-bar"
  role="progressbar"
  aria-valuemin={0}
  aria-valuemax={100}
  aria-valuenow={progress}
  aria-label={stage}
>
```

**Tests:**
- `test_progress_bar_renders.spec.ts` - Component renders
- `test_progress_bar_has_id.spec.ts` - ID is correct (#progress-bar)
- `test_progress_bar_updates.spec.ts` - Updates on progress change
- `test_progress_bar_animation.spec.ts` - Animates smoothly
- `test_progress_bar_validation.spec.ts` - Invalid values clamped
- `test_progress_bar_accessibility.spec.ts` - ARIA attributes correct

---

## 1.3 PluginInspector.tsx

**Purpose:**
Display plugin metadata, timings, warnings, and status in real-time.

**Location:**
```
web-ui/src/components/PluginInspector.tsx
```

**Props:**
```typescript
interface PluginInspectorProps {
  pluginTimings: Record<string, number>;       // name -> ms
  pluginMetadata: Record<string, PluginMetadata>;
  pluginStatus: Record<string, PluginStatus>;  // name -> status
  warnings: string[];
}

interface PluginMetadata {
  version: string;
  model: string;
  capabilities: string[];
}

type PluginStatus = 'started' | 'running' | 'completed' | 'failed';
```

**DOM Element:**
```html
<div id="plugin-inspector" class="plugin-inspector">
  <div class="plugin-inspector-header">Plugin Inspector</div>
  <div class="plugin-inspector-content">
    <!-- Plugin list -->
    <!-- Timing chart -->
    <!-- Warnings -->
  </div>
</div>
```

**Requirements:**
- Element ID MUST be `#plugin-inspector`
- Display all plugins in order of execution
- Show timing bar chart (horizontal bars, labeled in ms)
- Show status badge per plugin (started/running/completed/failed)
- Collect and display all warnings in a list
- Update in real-time as `plugin_status` and `warning` messages arrive

**Layout:**
```
┌─────────────────────────────────┐
│ Plugin Inspector                │
├─────────────────────────────────┤
│ Plugin Name    | Timing | Status│
├─────────────────────────────────┤
│ player_detect  |████░░░░| 145ms│ ✓
│ ball_detect    |██░░░░░░|  98ms│ ✓
│ pitch_detect   |█████░░░| 156ms│ ✓
├─────────────────────────────────┤
│ Warnings:                       │
│ • Pitch corners not found       │
│ • Low confidence in team colors │
└─────────────────────────────────┘
```

**Features:**
- **Timing Bar Chart**: Show ms per plugin as horizontal bars
  - Scale: Max plugin timing determines bar width
  - Color code: green (good), yellow (medium), red (slow)
- **Status Badges**: Visual indicator (icon + color)
  - started: ⏳ Gray
  - running: ⚙️ Blue (spinner animation)
  - completed: ✓ Green
  - failed: ✗ Red
- **Warnings List**: Scrollable list of all warnings
  - Each warning shows plugin name and message
  - Warnings are accumulated (not replaced)

**Behavior:**
- On `plugin_status` message: Update timing and status
- On `warning` message: Append to warnings list
- If no plugins: Show "No plugins running"
- If no timings: Show "Waiting for timing data"
- Live updates: No need to refresh or reload

**Tests:**
- `test_plugin_inspector_renders.spec.ts` - Component renders
- `test_plugin_inspector_has_id.spec.ts` - ID is correct (#plugin-inspector)
- `test_plugin_inspector_timing_display.spec.ts` - Timings display correctly
- `test_plugin_inspector_status_badge.spec.ts` - Status badges show correctly
- `test_plugin_inspector_warnings.spec.ts` - Warnings accumulate and display
- `test_plugin_inspector_empty.spec.ts` - Shows graceful empty state

---

# 2. Real-Time Client & Context

## 2.1 RealtimeClient.ts

**Purpose:**
Low-level WebSocket client for Phase 10 real-time channel.

**Location:**
```
web-ui/src/realtime/RealtimeClient.ts
```

**Public API:**
```typescript
class RealtimeClient {
  constructor(url: string);
  
  // Connection management
  async connect(): Promise<void>;
  disconnect(): void;
  isConnected(): boolean;
  
  // Message handling
  onMessage(handler: (message: RealtimeMessage) => void): void;
  onError(handler: (error: Error) => void): void;
  onConnectionChange(handler: (connected: boolean) => void): void;
  
  // Sending (for client heartbeat)
  async send(data: unknown): Promise<void>;
}
```

**Responsibilities:**
- Connect to `/v1/realtime` WebSocket
- Handle reconnection on disconnect (exponential backoff)
  - Attempts: 5
  - Delays: 1s, 2s, 4s, 8s, 16s
- Parse and validate incoming messages (RealtimeMessage schema)
- Dispatch parsed messages to listeners
- Handle network errors gracefully
- Implement automatic ping/pong heartbeat

**Behavior:**
- On successful connect: Call `onConnectionChange(true)`
- On disconnect: Auto-reconnect with backoff
- On max reconnect attempts: Call `onError()` and stop retrying
- On malformed message: Log error but continue listening
- On `ping` message: Auto-respond with `pong`

**Implementation Details:**
```typescript
// Exponential backoff with jitter
const delay = BASE_DELAY * Math.pow(2, attempt) + Math.random() * 1000;

// Validate message schema
if (!message.type || !message.payload || !message.timestamp) {
  throw new Error('Invalid RealtimeMessage');
}

// Handle ping automatically
if (message.type === 'ping') {
  await this.send({ type: 'pong', timestamp: new Date().toISOString() });
}
```

**Tests:**
- `test_realtime_client_connect.spec.ts` - Connect opens WebSocket
- `test_realtime_client_disconnect.spec.ts` - Disconnect closes WebSocket
- `test_realtime_client_parse.spec.ts` - Messages parsed correctly
- `test_realtime_client_reconnect.spec.ts` - Auto-reconnect works
- `test_realtime_client_backoff.spec.ts` - Exponential backoff correct
- `test_realtime_client_heartbeat.spec.ts` - Ping/pong works
- `test_realtime_client_error_handling.spec.ts` - Errors handled gracefully

---

## 2.2 RealtimeContext.tsx + useRealtime.ts

**Purpose:**
React Context and hook for real-time state management.

**Location:**
```
web-ui/src/realtime/RealtimeContext.tsx
web-ui/src/realtime/useRealtime.ts
```

**State Shape:**
```typescript
interface RealtimeState {
  isConnected: boolean;
  progress: number;  // 0-100
  currentFrame: FrameData | null;
  pluginTimings: Record<string, number>;       // name -> ms
  pluginMetadata: Record<string, PluginMetadata>;
  pluginStatus: Record<string, PluginStatus>;  // name -> status
  warnings: string[];
  errors: string[];
}

interface RealtimeContextType {
  state: RealtimeState;
  dispatch: (action: RealtimeAction) => void;
}
```

**Hook Usage:**
```typescript
function MyComponent() {
  const { state } = useRealtime();
  
  return <div>Progress: {state.progress}%</div>;
}
```

**Context Provider:**
```typescript
export function RealtimeProvider({ children }) {
  const [state, dispatch] = useReducer(realtimeReducer, initialState);
  const clientRef = useRef<RealtimeClient | null>(null);
  
  useEffect(() => {
    // Connect on mount
    clientRef.current = new RealtimeClient('ws://localhost:8000/v1/realtime');
    
    // Listen to messages
    clientRef.current.onMessage((message) => {
      dispatch({ type: 'MESSAGE_RECEIVED', payload: message });
    });
    
    clientRef.current.connect();
    
    return () => {
      clientRef.current?.disconnect();
    };
  }, []);
  
  return (
    <RealtimeContext.Provider value={{ state, dispatch }}>
      {children}
    </RealtimeContext.Provider>
  );
}
```

**Reducer Logic:**
```typescript
function realtimeReducer(state: RealtimeState, action: RealtimeAction): RealtimeState {
  switch (action.type) {
    case 'MESSAGE_RECEIVED': {
      const message = action.payload as RealtimeMessage;
      
      if (message.type === 'progress') {
        return { ...state, progress: message.payload.progress };
      }
      
      if (message.type === 'frame') {
        return { ...state, currentFrame: message.payload.data };
      }
      
      if (message.type === 'plugin_status') {
        return {
          ...state,
          pluginTimings: {
            ...state.pluginTimings,
            [message.payload.plugin]: message.payload.timing_ms,
          },
          pluginStatus: {
            ...state.pluginStatus,
            [message.payload.plugin]: message.payload.status,
          },
        };
      }
      
      if (message.type === 'warning') {
        return {
          ...state,
          warnings: [...state.warnings, message.payload.message],
        };
      }
      
      return state;
    }
    
    default:
      return state;
  }
}
```

**Tests:**
- `test_realtime_context_initial_state.spec.ts` - Initial state correct
- `test_realtime_context_dispatch.spec.ts` - Dispatch works
- `test_realtime_context_progress_update.spec.ts` - Progress updates
- `test_realtime_context_frame_update.spec.ts` - Frame updates
- `test_realtime_context_warning_accumulation.spec.ts` - Warnings accumulate
- `test_realtime_hook_subscription.spec.ts` - Hook updates on state change
- `test_realtime_hook_disconnect.spec.ts` - Cleanup on unmount

---

# 3. Storybook

## 3.1 RealtimeOverlay.stories.tsx

**Purpose:**
Storybook stories for RealtimeOverlay component (with mock context).

**Location:**
```
web-ui/src/stories/RealtimeOverlay.stories.tsx
```

**Stories to Create:**
1. **Idle State** - No activity
2. **Loading State** - Progress 0-10%
3. **In Progress** - Progress 50%
4. **Completing** - Progress 95%
5. **Complete** - Progress 100%
6. **With Warnings** - Showing warning list
7. **With Error** - Error banner visible
8. **With Timings** - Plugin inspector visible
9. **Dark Mode** - Dark theme variant

**Story Template:**
```typescript
import { Meta, StoryObj } from '@storybook/react';
import { RealtimeOverlay } from '@/components/RealtimeOverlay';
import { RealtimeProvider } from '@/realtime/RealtimeContext';

const meta: Meta<typeof RealtimeOverlay> = {
  title: 'Components/RealtimeOverlay',
  component: RealtimeOverlay,
  decorators: [
    (Story) => (
      <RealtimeProvider>
        <Story />
      </RealtimeProvider>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    isVisible: true,
    onClose: () => console.log('Close clicked'),
  },
};

export const WithProgress: Story = {
  args: {
    isVisible: true,
    onClose: () => console.log('Close clicked'),
  },
  decorators: [
    (Story) => {
      // Mock RealtimeContext with progress=50
      return <Story />;
    },
  ],
};
```

**Tests:**
- `test_realtime_overlay_stories_all_render.spec.ts` - All stories render

---

# 4. Phase 9 UI Invariants

### 4.1 Phase 9 IDs (MUST NOT CHANGE)

These IDs are part of the Phase 9 contract and MUST remain unchanged:

- `#device-selector` - Device selection dropdown
- `#toggle-play-pause` - Play/pause toggle
- `#toggle-fullscreen` - Fullscreen toggle
- `#toggle-overlay` - Overlay toggle
- `#fps-slider` - FPS slider control
- Any other Phase 9 IDs

### 4.2 Phase 9 Components (MUST NOT REMOVE)

Do NOT remove or significantly alter:
- DeviceSelector
- ControlPanel
- FrameViewer
- JobStatus
- ErrorBanner

### 4.3 Phase 10 IDs (NEW, MUST EXIST)

Phase 10 introduces:
- `#progress-bar` - Progress bar container
- `#plugin-inspector` - Plugin inspector container

---

# 5. UX Guidelines

## 5.1 Real-Time Updates

- Updates MUST appear within 200ms of message receipt (p95)
- No blocking UI operations
- State updates MUST not cause full page re-renders
- Use React memo/useMemo to prevent unnecessary re-renders

## 5.2 Error Handling

- If WebSocket disconnects: Show "Reconnecting..." message (graceful)
- If reconnect fails after 5 attempts: Show "Connection lost" error
- Do NOT crash the app on WebSocket error
- Do NOT block other functionality if real-time unavailable

## 5.3 Accessibility

- All components MUST have proper ARIA labels
- Progress bar MUST have role="progressbar"
- Status badges MUST be descriptive (not just colors)
- Warnings/errors MUST be readable by screen readers

## 5.4 Mobile Responsiveness

- Components MUST work on mobile (small screens)
- Progress bar MUST remain visible
- Plugin inspector MUST be scrollable if needed
- Close button MUST be accessible on touch devices

---

# 6. Summary

Phase 10 UI adds:

✅ RealtimeOverlay (main container)
✅ ProgressBar (#progress-bar)
✅ PluginInspector (#plugin-inspector)
✅ RealtimeClient (WebSocket client)
✅ RealtimeContext + useRealtime (state management)
✅ RealtimeOverlay.stories.tsx (Storybook)

All components are:
- Fully typed (TypeScript)
- Tested (RED → GREEN)
- Accessible (ARIA)
- Backward compatible (Phase 9 unchanged)

