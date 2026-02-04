# ⭐ Phase 10 Plans (Authoritative + Inferred Clearly Labeled)

**Status:** Planned → Active  
**Owner:** Roger  
**Depends on:** Phase 9 (Closed)  
**Unblocks:** Phase 11  

---

# Legend

- 🟩 **AUTHORITATIVE** - Content from Phase 10 note files (required)
- 🟦 **INFERRED** - Derived from authoritative files (helpful but not binding)
- 🟨 **ORGANIZATIONAL** - Execution scaffolding (not part of contract)

**Authoritative Sources:**
- PHASE_10_KICKOFF.md
- PHASE_10_DEVELOPER_CONTRACT.md
- PHASE_10_API_SPEC.md
- PHASE_10_UI_SPEC.md
- PHASE_10_FIRST_5_COMMITS.md
- PHASE_10_RED_TESTS.md
- PHASE_10_REALTIME_MESSAGE_PROTOCOL.md
- PHASE_10_REALTIME_FLOW_DIAGRAM.md
- PHASE_10_GOVERNANCE_ADDENDUM.md
- PHASE_10_FINAL_MERGE_PR_TEMPLATE.md

---

# 1. 🟩 AUTHORITATIVE: Requirements

## 1.1 API Requirements (From PHASE_10_API_SPEC.md)

- WebSocket/SSE endpoint at `/v1/realtime`
- Typed message schema: `RealtimeMessage` with `type`, `payload`, `timestamp`
- ExtendedJobResponse model with optional fields:
  - `progress` (int, 0-100)
  - `plugin_timings` (Dict[str, float])
  - `warnings` (List[str])
- New endpoint: `GET /v1/jobs/{job_id}/extended`

## 1.2 UI Requirements (From PHASE_10_UI_SPEC.md)

### Required IDs:
- `#progress-bar` - Progress bar container
- `#plugin-inspector` - Plugin inspector panel

### Required Components:
- `RealtimeOverlay.tsx` - Main container for real-time UI
- `ProgressBar.tsx` - Job progress display (0-100%)
- `PluginInspector.tsx` - Plugin metadata, timings, warnings display
- `RealtimeClient.ts` - WebSocket client with auto-reconnect
- `RealtimeContext.tsx` + `useRealtime.ts` - State management

## 1.3 Real-Time Requirements (From PHASE_10_DEVELOPER_CONTRACT.md)

- ConnectionManager for WebSocket connections
- Message types: frame, partial_result, progress, plugin_status, warning, error, ping, pong, metadata
- InspectorService for plugin metadata extraction
- Real-time message broadcasting

## 1.4 Storybook (From PHASE_10_UI_SPEC.md)

- ONE story: `RealtimeOverlay.stories.tsx`

## 1.5 Pre-Commit Hook Fix (From PHASE_10_IMPLEMENTATION_PLAN.md)

- Fix/replace failing `web-ui-tests` hook
- Skip Playwright tests locally, run in CI only

---

# 2. 🟦 INFERRED: What I Will Add (Permitted Deviations)

These are execution helpers, not requirements:

- Progress bar animations and styling
- Plugin timing bar chart (horizontal bars with ms labels)
- Status badges (started/running/completed/failed)
- Warning accumulation list
- Error banner integration
- Exponential backoff for WebSocket reconnection (1s, 2s, 4s, 8s, 16s)
- TypeScript interfaces for all props and state
- CSS modules or styled-components

---

# 3. 🟦 INFERRED: What I Will Skip (Explicit Non-Requirements)

- Schema drift detection
- Full Storybook coverage for all new components
- Additional governance rules (beyond Phase 10 Addendum)
- Server-Sent Events (SSE) fallback (WebSocket preferred)
- Custom error codes beyond documented error messages
- Full plugin pipeline refactoring (only inspector service additions)

---

# 4. 🟨 ORGANIZATIONAL: Work Streams

These streams organize implementation but are NOT authoritative:

- 4.1 Real-Time Infrastructure
- 4.2 Extended Job Model
- 4.3 Plugin Pipeline Upgrade
- 4.4 Frontend Real-Time Client
- 4.5 Frontend State Management
- 4.6 Frontend UI Components
- 4.7 Storybook
- 4.8 Pre-Commit Hook Fix
- 4.9 Tests

---

# 5. 🟩 AUTHORITATIVE: First 5 Commits (From PHASE_10_FIRST_5_COMMITS.md)

Commit 1 - Create Phase 10 Scaffolding

Directories:
```
server/app/realtime/
server/app/plugins/inspector/
server/tests/realtime/
web-ui/src/realtime/
web-ui/tests/realtime/
web-ui/src/components/
web-ui/src/stories/
```

Placeholder files with `__init__.py` and TODO comments.

## Commit 2 - Backend RED Tests

Files:
```
server/tests/realtime/test_realtime_endpoint.py
server/tests/realtime/test_job_progress_field.py
server/tests/realtime/test_plugin_timing_field.py
server/tests/realtime/test_connection_manager.py
server/tests/realtime/test_inspector_service.py
```

All tests MUST FAIL (RED).

## Commit 3 - Frontend RED Tests

Files:
```
web-ui/tests/realtime/realtime_endpoint.spec.ts
web-ui/tests/realtime/progress_bar.spec.ts
web-ui/tests/realtime/plugin_inspector.spec.ts
web-ui/tests/realtime/realtime_client.spec.ts
web-ui/tests/realtime/realtime_context.spec.ts
```

All tests MUST FAIL (RED).

## Commit 4 - Real-Time Endpoint Stub + Extended Models

Implement:
```
server/app/realtime/message_types.py
server/app/models_phase10.py
server/app/realtime/connection_manager.py
server/app/realtime/websocket_router.py
```

Backend RED tests begin to PASS (GREEN).

## Commit 5 - Fix Web-UI Pre-Commit Hook

Modify `.pre-commit-config.yaml`:
```yaml
- id: web-ui-tests
  entry: bash -c 'if [ "$CI" != "true" ]; then echo "Skipping Playwright tests locally"; exit 0; fi && npm run test:e2e'
```

---

# 6. 🟦 INFERRED: Additional Commits (Not Authoritative)

These commits are execution planning beyond the authoritative first 5:

- Commit 6: Frontend Realtime Implementation
- Commit 7: UI Components Implementation
- Commit 8: Backend Integration
- Commit 9: Integration Tests

---

# 7. 🟩 AUTHORITATIVE: Success Criteria (From PHASE_10_KICKOFF.md)

Phase 10 is complete when:

- [ ] Real-time WebSocket endpoint functional at `/v1/realtime`
- [ ] ExtendedJobResponse returns at `/v1/jobs/{job_id}/extended`
- [ ] Progress bar component exists with `#progress-bar` ID
- [ ] Plugin inspector component exists with `#plugin-inspector` ID
- [ ] RealtimeClient auto-reconnects on disconnect
- [ ] RealtimeContext manages state for all message types
- [ ] One Storybook story exists for RealtimeOverlay
- [ ] All backend RED tests pass
- [ ] All frontend RED tests pass
- [ ] Pre-commit hook no longer blocks development
- [ ] No Phase 9 invariants broken
- [ ] All Phase 9 tests still pass

---

# 8. 🟩 AUTHORITATIVE: Phase 11 Dependencies (From PHASE_10_KICKOFF.md)

Phase 11 depends on:
- Real-time WebSocket infrastructure
- ExtendedJobResponse model
- Plugin InspectorService
- ProgressBar and PluginInspector components
- RealtimeContext state management
- ConnectionManager for multiple clients

Phase 11 inherits:
- WebSocket/SSE channel
- Typed real-time messages
- Plugin pipeline v2 (lifecycle-based)
- Optional real-time fields
- Minimal governance

---

# 9. 🟦 INFERRED: Descriptive File Naming

**Authoritative filenames from PHASE_10_RED_TESTS.md:**

| Purpose | Authoritative Filename |
|---------|----------------------|
| Realtime endpoint tests | `test_realtime_endpoint.py` |
| Progress field tests | `test_job_progress_field.py` |
| Plugin timing tests | `test_plugin_timing_field.py` |
| Connection manager tests | `test_connection_manager.py` |
| Inspector service tests | `test_inspector_service.py` |

---

# 10. 🟩 AUTHORITATIVE: Real-Time Message Types (From PHASE_10_REALTIME_MESSAGE_PROTOCOL.md)

All messages conform to:
```json
{
  "type": "<message-type>",
  "payload": { },
  "timestamp": "<ISO8601>"
}
```

### Message Types:
- `frame` - Annotated frame from plugin
- `partial_result` - Intermediate plugin result
- `progress` - Job progress update (0-100)
- `plugin_status` - Plugin execution status
- `warning` - Non-fatal plugin warning
- `error` - Fatal error message
- `ping` - Heartbeat from server
- `pong` - Heartbeat response from client
- `metadata` - Plugin metadata on connection

---

# 11. 🟦 INFERRED: UI Component Layout

This diagram is derived from PHASE_10_UI_SPEC.md but is NOT authoritative:

```
RealtimeOverlay
├── ProgressBar
│   └── #progress-bar
└── PluginInspector
    └── #plugin-inspector
```

---

# 12. 🟩 AUTHORITATIVE: Realtime Client State Machine (From PHASE_10_REALTIME_CLIENT_STATE_MACHINE.md)

### States:
- **IDLE** - Client initialized but not attempting connection
- **CONNECTING** - Attempting to establish WebSocket connection
- **CONNECTED** - WebSocket connection active and ready
- **DISCONNECTED** - Connection closed unexpectedly
- **RECONNECTING** - Attempting to reconnect after unexpected disconnect
- **CLOSED** - Client intentionally shut down

### Backoff Schedule:
```
Attempt 1: 1 second
Attempt 2: 2 seconds
Attempt 3: 4 seconds
Attempt 4: 8 seconds
Attempt 5: 16 seconds
Attempt 6+: CLOSED (max attempts exceeded)
```

---

# 13. 🟩 AUTHORITATIVE: Plugin Timing Algorithm (From PHASE_10_PLUGIN_TIMING_ALGORITHM_SPEC.md)

### Clock Selection:
- MUST use monotonic clock (not system clock)

### Precision:
- Unit: Milliseconds (ms)
- Precision: 1 decimal place (e.g., 145.5 ms)
- Type: Float

### Measurement:
```python
start = time.monotonic()
result = plugin.run(frame)
end = time.monotonic()
timing_ms = (end - start) * 1000.0
```

---

# 14. 🟩 AUTHORITATIVE: Governance Addendum (From PHASE_10_GOVERNANCE_ADDENDUM.md)

### Scope:
- server/app/realtime/
- server/app/models_phase10.py
- server/app/plugins/inspector/
- web-ui/src/realtime/
- web-ui/src/components/ (3 new components)
- web-ui/src/stories/ (1 new story)

### Forbidden Changes:
- Modify any Phase 9 API field
- Modify any Phase 9 model
- Remove any Phase 9 endpoint
- Remove any Phase 9 UI ID
- Remove any Phase 9 test
- Add schema drift detection
- Add new governance rules

---

Roger, let Phase 10 begin with clarity, structure, and mechanical governance.

