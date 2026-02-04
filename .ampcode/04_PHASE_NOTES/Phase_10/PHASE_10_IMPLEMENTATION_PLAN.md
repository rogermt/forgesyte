# Phase 10 Implementation Plan

Real-Time Insights + Plugin Pipeline Upgrade

---

# Overview

Phase 10 introduces real-time insights, plugin pipeline upgrades, extended job models, and fixes the failing web-ui pre-commit hook.

All changes are **additive** and MUST NOT break any Phase 9 invariants.

---

# 1. Backend Implementation Plan

## 1.1 Real-Time Endpoint

Create:

```
server/app/realtime/websocket_router.py
```

**Responsibilities:**
- Accept WebSocket connections at `/v1/realtime`
- Broadcast messages (frames, progress, timings, warnings)
- Implement heartbeat (ping/pong every 30 seconds)
- Handle client disconnect/reconnect
- Validate all outgoing messages

**Dependencies:**
- FastAPI WebSocket support
- ConnectionManager (see 1.2)

**Tests:**
- `test_websocket_connect.py` - Connection opens
- `test_websocket_broadcast.py` - Messages reach all clients
- `test_websocket_heartbeat.py` - Ping/pong works
- `test_websocket_disconnect.py` - Cleanup on disconnect

---

## 1.2 Connection Manager

Create:

```
server/app/realtime/connection_manager.py
```

**Responsibilities:**
- Track active WebSocket connections
- Route messages to connected clients
- Handle client registration/deregistration
- Implement backpressure (queue size limits)
- Log connection lifecycle

**Public API:**
```python
class ConnectionManager:
    async def connect(self, session_id: str, websocket: WebSocket)
    async def disconnect(self, session_id: str)
    async def broadcast(self, message: RealtimeMessage)
    def is_connected(self, session_id: str) -> bool
```

**Tests:**
- `test_connection_manager_add.py` - Can add connection
- `test_connection_manager_broadcast.py` - Broadcast reaches all
- `test_connection_manager_remove.py` - Cleanup works
- `test_connection_manager_backpressure.py` - Queue limits enforced

---

## 1.3 Real-Time Message Types

Create:

```
server/app/realtime/message_types.py
```

**Defines:**
```python
class RealtimeMessage(BaseModel):
    type: str
    payload: dict
    timestamp: datetime

# Message type constants
class MessageType(str, Enum):
    FRAME = "frame"
    PARTIAL_RESULT = "partial_result"
    PROGRESS = "progress"
    PLUGIN_STATUS = "plugin_status"
    WARNING = "warning"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"
    METADATA = "metadata"
```

**Payload Models:**
- `FramePayload`
- `ProgressPayload`
- `PluginStatusPayload`
- `WarningPayload`
- `ErrorPayload`
- `MetadataPayload`

**Validation:**
- All payloads must be JSON-serializable
- All messages must have type, payload, timestamp
- Required fields per message type enforced

**Tests:**
- `test_message_validation.py` - Invalid messages rejected
- `test_message_serialization.py` - All types serialize to JSON

---

## 1.4 Extended Job Model

Create:

```
server/app/models_phase10.py
```

**Key Classes:**
```python
class ExtendedJobResponse(BaseModel):
    # All Phase 9 fields (unchanged)
    job_id: str
    device_requested: str
    device_used: str
    fallback: bool
    frames: List[FrameData]
    
    # New Phase 10 fields (optional)
    progress: Optional[int] = None
    plugin_timings: Optional[Dict[str, float]] = None
    warnings: Optional[List[str]] = None
```

**Invariants:**
- Phase 9 fields MUST be present and unchanged
- New fields MUST be optional
- Existing `JobResponse` MUST NOT be modified
- Both models can coexist

**Endpoint:**
```
GET /v1/jobs/{job_id}/extended
└─> ExtendedJobResponse
```

**Tests:**
- `test_extended_job_has_phase9_fields.py` - All Phase 9 fields present
- `test_extended_job_optional_fields.py` - New fields optional
- `test_extended_job_backward_compat.py` - Legacy endpoint still works

---

## 1.5 Plugin Pipeline Upgrade

### 1.5.1 Inspector Service

Create:

```
server/app/plugins/inspector/inspector_service.py
```

**Responsibilities:**
- Extract plugin metadata (version, model, capabilities)
- Collect plugin execution timings
- Track plugin warnings
- Manage plugin state during execution

**Public API:**
```python
class InspectorService:
    async def inspect(self, plugin_name: str) -> PluginMetadata
    async def start_timing(self, plugin_name: str)
    async def stop_timing(self, plugin_name: str) -> float
    def collect_timings(self) -> Dict[str, float]
    def collect_warnings(self) -> List[str]
```

**Tests:**
- `test_inspector_metadata.py` - Metadata extraction works
- `test_inspector_timing.py` - Timings collected accurately
- `test_inspector_warnings.py` - Warnings accumulated

### 1.5.2 Tool Runner (Updated)

Update:

```
server/app/plugins/runtime/tool_runner.py
```

**Changes:**
- Call `InspectorService` before executing tool
- Emit `progress` messages during execution
- Emit `plugin_status` messages on start/complete
- Emit `frame` messages as frames are produced
- Emit `warning` messages if plugin soft-fails
- Pass `ConnectionManager` for broadcast

**Invariants:**
- Phase 9 tool execution MUST NOT change
- Tool return values MUST NOT change
- Tool signatures MUST NOT change
- Timing/warning collection is pure overhead

**Tests:**
- `test_tool_runner_emits_progress.py` - Progress messages sent
- `test_tool_runner_emits_frames.py` - Frame messages sent
- `test_tool_runner_emits_warnings.py` - Warnings collected

---

## 1.6 Jobs Endpoint (Updated)

Update:

```
server/app/api/jobs.py
```

**Changes:**
- Add `/v1/jobs/{job_id}/extended` endpoint
- Integrate `InspectorService` and `ToolRunner` updates
- Pass `ConnectionManager` to job execution

**Invariants:**
- Existing `/v1/jobs/{job_id}` endpoint MUST NOT change
- Legacy job response format MUST NOT change
- Job execution flow MUST NOT change

**Tests:**
- `test_jobs_extended_endpoint.py` - New endpoint works
- `test_jobs_legacy_still_works.py` - Old endpoint still works

---

# 2. Frontend Implementation Plan

## 2.1 Real-Time Client

Create:

```
web-ui/src/realtime/RealtimeClient.ts
```

**Responsibilities:**
- Connect to `/v1/realtime` WebSocket
- Implement automatic reconnect with exponential backoff
- Parse and validate messages
- Dispatch messages to context
- Handle network errors gracefully

**Public API:**
```typescript
class RealtimeClient {
  connect(url: string): Promise<void>
  disconnect(): void
  isConnected(): boolean
  send(message: RealtimeMessage): void
  onMessage(handler: (msg: RealtimeMessage) => void): void
  onError(handler: (error: Error) => void): void
}
```

**Reconnection Strategy:**
- Attempts: 5
- Delays: 1s, 2s, 4s, 8s, 16s
- Exponential backoff with jitter

**Tests:**
- `test_realtime_client_connect.spec.ts` - Connection opens
- `test_realtime_client_reconnect.spec.ts` - Auto-reconnect works
- `test_realtime_client_parse.spec.ts` - Messages parsed correctly
- `test_realtime_client_backoff.spec.ts` - Exponential backoff works

---

## 2.2 Real-Time Context + Hook

Create:

```
web-ui/src/realtime/RealtimeContext.tsx
web-ui/src/realtime/useRealtime.ts
```

**RealtimeContext:**
```typescript
interface RealtimeState {
  isConnected: boolean
  progress: number  // 0-100
  currentFrame: FrameData | null
  pluginTimings: Record<string, number>
  warnings: string[]
  errors: string[]
  pluginMetadata: Record<string, PluginMetadata>
}

interface RealtimeContextType {
  state: RealtimeState
  dispatch: (action: RealtimeAction) => void
}
```

**useRealtime Hook:**
- Subscribe to state changes
- Auto-cleanup on unmount
- TypeScript-first design

**Tests:**
- `test_realtime_context_initial_state.spec.ts` - Initial state correct
- `test_realtime_context_dispatch.spec.ts` - Actions work
- `test_realtime_hook_subscription.spec.ts` - Hook updates work

---

## 2.3 Real-Time UI Components

Create three new components:

### 2.3.1 RealtimeOverlay.tsx

**Responsibilities:**
- Main container for real-time UI
- Renders frame viewer
- Renders progress bar
- Renders plugin inspector
- Manages layout

**Props:**
```typescript
interface RealtimeOverlayProps {
  isVisible: boolean
  onClose: () => void
}
```

**Tests:**
- `test_realtime_overlay_renders.spec.ts` - Component renders
- `test_realtime_overlay_updates.spec.ts` - Updates on message

### 2.3.2 ProgressBar.tsx

**Responsibilities:**
- Display job progress (0-100)
- Show current stage/plugin name
- Smooth animation
- Accessibility labels

**Props:**
```typescript
interface ProgressBarProps {
  progress: number
  stage?: string
  plugin?: string
}
```

**DOM:**
- `<div id="progress-bar">` (must exist)

**Tests:**
- `test_progress_bar_renders.spec.ts` - Component renders
- `test_progress_bar_updates.spec.ts` - Updates on progress change
- `test_progress_bar_animation.spec.ts` - Animation works

### 2.3.3 PluginInspector.tsx

**Responsibilities:**
- Display plugin metadata
- Show plugin timings (bar chart or list)
- Display warnings/errors per plugin
- Show plugin status (started/running/completed)

**Props:**
```typescript
interface PluginInspectorProps {
  pluginTimings: Record<string, number>
  pluginMetadata: Record<string, PluginMetadata>
  warnings: string[]
  pluginStatus: Record<string, 'started' | 'running' | 'completed' | 'failed'>
}
```

**DOM:**
- `<div id="plugin-inspector">` (must exist)

**Tests:**
- `test_plugin_inspector_renders.spec.ts` - Component renders
- `test_plugin_inspector_timing_display.spec.ts` - Timings display
- `test_plugin_inspector_warnings.spec.ts` - Warnings display

---

## 2.4 Storybook

Create:

```
web-ui/src/stories/RealtimeOverlay.stories.tsx
```

**Stories:**
- Default (with sample data)
- Loading (progress 0)
- In Progress (progress 50)
- Complete (progress 100)
- With Warnings (warning list visible)
- With Errors (error banner visible)
- Dark Mode (if applicable)

**Tests:**
- `test_realtime_overlay_stories.spec.ts` - All stories render

---

# 3. Fixing the Web-UI Pre-Commit Hook

## Problem
The `web-ui-tests` hook in `.pre-commit-config.yaml` runs Playwright tests locally, but:
- Playwright requires browser installation
- Many developers don't have browsers installed
- Playwright tests should run only in CI

## Solution
Choose ONE of:

### Option A: Skip Playwright Locally (Recommended)

Modify `.pre-commit-config.yaml`:
```yaml
- repo: local
  hooks:
    - id: web-ui-tests
      name: web-ui tests
      entry: bash -c 'if [ "$CI" != "true" ]; then echo "Skipping Playwright tests locally"; exit 0; fi && npm run test:e2e'
      language: system
      pass_filenames: false
```

**Pros:** Simple, zero configuration
**Cons:** CI must set `CI=true`

### Option B: Check for Playwright Installation

Create `scripts/check-playwright.sh`:
```bash
#!/bin/bash
if ! npm list @playwright/test &>/dev/null; then
  echo "Playwright not installed. Skipping E2E tests."
  exit 0
fi
npm run test:e2e
```

Update `.pre-commit-config.yaml`:
```yaml
- id: web-ui-tests
  entry: bash scripts/check-playwright.sh
```

**Pros:** Graceful degradation
**Cons:** Extra script file

### Option C: Move to CI Only

Remove from `.pre-commit-config.yaml` entirely.
Add to CI workflow (GitHub Actions):
```yaml
- name: E2E Tests
  run: npm run test:e2e
```

**Pros:** Clear separation of concerns
**Cons:** Less feedback before push

## Recommendation
**Use Option A** (skip locally if not in CI).

---

# 4. Testing Plan

## Backend RED → GREEN Tests

Create in `server/tests/phase10/`:

```
test_realtime_endpoint_exists.py
test_job_progress_field.py
test_job_plugin_timings_field.py
test_job_warnings_field.py
test_connection_manager.py
test_inspector_service.py
test_tool_runner_emits_messages.py
```

All tests **MUST fail** initially (RED).
Tests pass when implementation complete (GREEN).

## Frontend RED → GREEN Tests

Create in `web-ui/tests/phase10/`:

```
realtime_client_connects.spec.ts
realtime_context_dispatch.spec.ts
progress_bar_renders.spec.ts
progress_bar_updates.spec.ts
plugin_inspector_renders.spec.ts
plugin_inspector_updates.spec.ts
realtime_overlay_integrates.spec.ts
```

All tests **MUST fail** initially (RED).
Tests pass when implementation complete (GREEN).

## Integration Tests

```
test_realtime_job_with_frames.py
test_realtime_with_warnings.py
test_realtime_with_timings.py
test_ui_updates_on_progress.spec.ts
test_ui_updates_on_warning.spec.ts
```

---

# 5. Completion Criteria

Phase 10 is complete when:

✓ Real-time endpoint works at `/v1/realtime`
✓ Extended job model responds at `/v1/jobs/{job_id}/extended`
✓ Real-time UI components render (overlay, progress bar, inspector)
✓ Plugin inspector displays timings and warnings
✓ All RED → GREEN tests pass
✓ All Phase 9 tests still pass
✓ Pre-commit hook fixed (no blocking Playwright locally)
✓ No Phase 9 invariants broken
✓ Full backward compatibility maintained

---

# 6. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Breaking Phase 9 API | High | All Phase 9 fields untouched; separate new model |
| Connection manager bugs | Medium | Thorough unit tests; mock clients in tests |
| Real-time lag/backpressure | Medium | Queue size limits; message dropping strategy |
| Frontend reconnect loops | Medium | Exponential backoff; max 5 attempts |
| Missing browser in CI | Medium | Use Option A (skip locally) |

---

# 7. Success Metrics

- 100% of RED tests → GREEN
- 100% of Phase 9 tests still pass
- Real-time latency < 200ms (p95)
- Backlog queue < 1000 messages
- Zero breaking changes
- Pre-commit hook does not block development

