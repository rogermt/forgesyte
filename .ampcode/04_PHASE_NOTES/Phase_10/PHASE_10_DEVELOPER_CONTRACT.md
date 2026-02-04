# Phase 10 Developer Contract
Real-Time Insights + Plugin Pipeline Upgrade

This contract defines the required deliverables, invariants, and guardrails for
Phase 10. All requirements are additive and MUST NOT break any Phase 9
invariants.

---

# 1. Scope

Phase 10 introduces:
- Real-time insights (WebSocket/SSE)
- Extended job model (progress, plugin timings, warnings)
- Plugin pipeline upgrade (metadata, inspector, real-time execution)
- Real-time UI components (overlay, progress bar, inspector)
- Fixing the failing web-ui pre-commit hook

Phase 10 MUST NOT:
- Break Phase 9 API fields
- Break Phase 9 UI IDs
- Add new governance rules
- Introduce schema drift detection

---

# 2. Backend Requirements

## 2.1 Real-Time Endpoint (MUST)
A real-time endpoint MUST exist at:

```
/v1/realtime
```

It MAY be implemented using:
- WebSocket
- Server-Sent Events (SSE)

The endpoint MUST support:
- Streaming frames
- Streaming progress updates
- Streaming plugin timings
- Streaming warnings/errors

---

## 2.2 Extended Job Model (MUST)
A new additive model MUST be created:

```
ExtendedJobResponse
```

It MUST include:
- All Phase 9 required fields
- New optional fields:
  - progress: Optional[int]
  - plugin_timings: Optional[Dict[str, float]]
  - warnings: Optional[List[str]]

Phase 9 models MUST NOT be modified.

---

## 2.3 Real-Time Message Types (MUST)
A new message schema MUST exist:

```
RealtimeMessage
```

It MUST support:
- type: str
- payload: dict
- timestamp: datetime

Allowed message types:
- frame
- partial_result
- progress
- plugin_status
- warning
- error
- ping
- pong

---

## 2.4 Plugin Pipeline Upgrade (MUST)
Plugins MUST support:
- Extended metadata
- Real-time execution via tool runner
- Timing collection
- Warning emission

A new service MUST exist:

```
plugins/inspector/inspector_service.py
```

---

# 3. Frontend Requirements

## 3.1 Real-Time Client (MUST)
A client MUST exist:

```
src/realtime/RealtimeClient.ts
```

It MUST:
- Connect to /v1/realtime
- Reconnect on failure
- Dispatch messages to context

---

## 3.2 Real-Time UI Components (MUST)
The following components MUST exist:

- RealtimeOverlay.tsx
- ProgressBar.tsx (#progress-bar)
- PluginInspector.tsx (#plugin-inspector)

---

## 3.3 Storybook (MUST)
A new Storybook story MUST exist:

```
RealtimeOverlay.stories.tsx
```

---

# 4. Test Requirements

## 4.1 Backend RED → GREEN (MUST)
Tests MUST cover:
- Real-time endpoint existence
- progress field
- plugin_timings field

## 4.2 Frontend RED → GREEN (MUST)
Tests MUST cover:
- Real-time connection opens
- Progress bar renders
- Plugin inspector loads

---

# 5. Pre-Commit Hook Fix (MUST)
The failing `web-ui-tests` hook MUST be:
- Fixed, OR
- Replaced, OR
- Isolated to CI only

It MUST NOT block development after Phase 10.

---

# 6. Invariants (MUST NOT BREAK)

## 6.1 Phase 9 API invariants
- job_id
- device_requested
- device_used
- fallback
- frames

## 6.2 Phase 9 UI IDs
- #device-selector
- #toggle-*
- #fps-slider

## 6.3 Governance
- No new governance rules
- No schema drift detection
- No breaking changes

---

# 7. Completion Criteria

Phase 10 is complete when:
- Real-time endpoint works
- Real-time UI updates
- Plugin inspector works
- Extended job model implemented
- All RED tests pass
- Pre-commit hook fixed
- No Phase 9 invariants broken
