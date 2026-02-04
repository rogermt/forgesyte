Roger, you got it — here are **all three corrected Phase 10 documents**, fully aligned with the authoritative sources, with zero drift, zero guesses, and every deviation fixed.

They’re written in the same `.ampcode` style you’ve been using, and they now match:

- **PHASE_10_DEVELOPER_CONTRACT.md**  
- **PHASE_10_FIRST_5_COMMITS.md**  
- **PHASE_10_RED_TESTS.md**  
- **PHASE_10_FINAL_MERGE_PR_TEMPLATE.md**  
- **PHASE_10_UI_SPEC.md**  
- **PHASE_10_REALTIME_MESSAGE_PROTOCOL.md**

Everything below is authoritative and ready to drop into:

```
.ampcode/04_PHASE_NOTES/Phase_10/
```

---

# ⭐ **1. Corrected Phase 10 Implementation Plan (Fully Aligned)**  
### *File:* `PHASE_10_IMPLEMENTATION_PLAN.md`

```md
# Phase 10 — Implementation Plan (Corrected & Authoritative)

This plan is fully aligned with all authoritative Phase 10 documents:
- PHASE_10_DEVELOPER_CONTRACT.md
- PHASE_10_FIRST_5_COMMITS.md
- PHASE_10_RED_TESTS.md
- PHASE_10_UI_SPEC.md
- PHASE_10_REALTIME_MESSAGE_PROTOCOL.md
- PHASE_10_FINAL_MERGE_PR_TEMPLATE.md

No inferred behavior is treated as authoritative. All inferred items are marked.

---

# 1. Backend Implementation

## 1.1 Real-Time Endpoint (Required)
Create:
```
server/app/realtime/websocket_router.py
```
Implements:
- WebSocket/SSE endpoint at `/v1/realtime`
- Accepts connections
- Broadcasts RealtimeMessage objects
- Heartbeat (ping/pong)

## 1.2 Connection Manager (Required)
Create:
```
server/app/realtime/connection_manager.py
```
Responsibilities:
- Track connected clients
- Handle reconnects
- Broadcast messages

## 1.3 Real-Time Message Types (Required)
Create:
```
server/app/realtime/message_types.py
```
Implements message types defined in PHASE_10_REALTIME_MESSAGE_PROTOCOL.md:
- frame
- partial_result
- progress
- plugin_status
- warning
- error
- ping/pong

## 1.4 Extended Job Model (Required)
Create:
```
server/app/models_phase10.py
```
Add optional fields:
- progress: Optional[int]
- plugin_timings: Optional[Dict[str, float]]
- warnings: Optional[List[str]]

Phase 9 models MUST NOT be modified.

## 1.5 Plugin Pipeline Upgrade (Required)
Create:
```
server/app/plugins/inspector/inspector_service.py
server/app/plugins/runtime/tool_runner.py
```
Responsibilities:
- Collect plugin timings
- Emit warnings
- Real-time tool execution

---

# 2. Frontend Implementation

## 2.1 Real-Time Client (Required)
Create:
```
web-ui/src/realtime/RealtimeClient.ts
```
Implements:
- Connection to `/v1/realtime`
- Reconnection strategy (authoritative)
- Message parsing

## 2.2 Realtime Context + Hook (Required)
Create:
```
web-ui/src/realtime/RealtimeContext.tsx
web-ui/src/realtime/useRealtime.ts
```

## 2.3 Real-Time UI Components (Required)
Create:
```
RealtimeOverlay.tsx
ProgressBar.tsx (#progress-bar)
PluginInspector.tsx (#plugin-inspector)
```

## 2.4 Storybook (Required)
Create:
```
RealtimeOverlay.stories.tsx
```

---

# 3. Fixing the Web-UI Pre-Commit Hook (Required)
Commit 5 MUST:
- Fix or replace the failing `web-ui-tests` hook
- Ensure Playwright runs in CI
- Ensure pre-commit does NOT run Playwright locally unless explicitly requested

---

# 4. Testing Plan

## Backend RED → GREEN (Required)
Tests from PHASE_10_RED_TESTS.md:
- test_realtime_endpoint.py
- test_job_progress_field.py
- test_plugin_timing_field.py

## Frontend RED → GREEN (Required)
- realtime_endpoint.spec.ts
- progress_bar.spec.ts
- plugin_inspector.spec.ts

---

# 5. Inferred UI Layout (NOT authoritative)
This layout is inferred from the UI spec and real-time flow diagram:

```
RealtimeOverlay
Frame Viewer
├── ProgressBar
└── PluginInspector
```

This is NOT a contract and MUST NOT be enforced as governance.

---

# 6. Completion Criteria
Phase 10 is complete when:
- Real-time endpoint works
- Real-time UI updates
- Plugin inspector works
- Extended job model implemented
- All RED tests pass
- Pre-commit hook fixed
- No Phase 9 invariants broken
```

---

# ⭐ **2. Corrected Phase 10 Commit Plan**  
### *File:* `PHASE_10_COMMIT_PLAN.md`

```md
# Phase 10 — Corrected Commit Plan

This commit plan matches PHASE_10_FIRST_5_COMMITS.md exactly.

---

## Commit 1 — Create Phase 10 Scaffolding
Add directories:
```
server/app/realtime/
server/app/plugins/inspector/
server/app/plugins/runtime/
server/tests/phase10/
web-ui/src/realtime/
web-ui/tests/phase10/
```
Add placeholder files + __init__.py.

---

## Commit 2 — Backend RED Tests (Authoritative Filenames)
Add:
```
server/tests/phase10/test_realtime_endpoint.py
server/tests/phase10/test_job_progress_field.py
server/tests/phase10/test_plugin_timing_field.py
```
All tests MUST fail.

---

## Commit 3 — Frontend RED Tests (Authoritative Filenames)
Add:
```
web-ui/tests/phase10/realtime_endpoint.spec.ts
web-ui/tests/phase10/progress_bar.spec.ts
web-ui/tests/phase10/plugin_inspector.spec.ts
```
All tests MUST fail.

---

## Commit 4 — Real-Time Endpoint Stub + Extended Models
Add:
```
server/app/realtime/websocket_router.py
server/app/models_phase10.py
```
Backend RED tests begin to pass.

---

## Commit 5 — Fix Web-UI Pre-Commit Hook
Modify:
```
.pre-commit-config.yaml
```
Implement:
- Skip Playwright locally OR
- Run Playwright only in CI OR
- Add environment detection

This commit stabilizes the repo.
```

---

# ⭐ **3. Corrected Phase 10 File Map**  
### *File:* `PHASE_10_FILE_MAP.md`

```md
# Phase 10 — Corrected File Map

This file map matches all authoritative Phase 10 documents.

---

# 1. Backend Files

server/app/realtime/
- __init__.py
- websocket_router.py
- connection_manager.py
- message_types.py

server/app/plugins/inspector/
- __init__.py
- inspector_service.py

server/app/plugins/runtime/
- __init__.py
- tool_runner.py

server/app/models_phase10.py
server/app/api_phase10.py (optional future extension)

server/tests/phase10/
- __init__.py
- test_realtime_endpoint.py
- test_job_progress_field.py
- test_plugin_timing_field.py

---

# 2. Frontend Files

web-ui/src/realtime/
- RealtimeClient.ts
- RealtimeContext.tsx
- useRealtime.ts

web-ui/src/components/
- RealtimeOverlay.tsx
- ProgressBar.tsx
- PluginInspector.tsx

web-ui/src/stories/
- RealtimeOverlay.stories.tsx

web-ui/tests/phase10/
- realtime_endpoint.spec.ts
- progress_bar.spec.ts
- plugin_inspector.spec.ts

---

# 3. Governance Files

.ampcode/04_PHASE_NOTES/Phase_10/
- PHASE_10_DEVELOPER_CONTRACT.md
- PHASE_10_IMPLEMENTATION_PLAN.md
- PHASE_10_FIRST_5_COMMITS.md
- PHASE_10_RED_TESTS.md
- PHASE_10_FINAL_MERGE_PR_TEMPLATE.md
- PHASE_10_REALTIME_MESSAGE_PROTOCOL.md
- PHASE_10_UI_SPEC.md
- PHASE_10_FILE_MAP.md
```

---

Absolutely, Roger — here is **Option 4**, the corrected and fully aligned **Phase 10 UI Architecture Note**, with every inferred element clearly labeled so it never becomes an accidental governance rule.

This document is clean, authoritative, and safe to drop into:

```
.ampcode/04_PHASE_NOTES/Phase_10/PHASE_10_UI_ARCHITECTURE_NOTE.md
```

---

# ⭐ **PHASE 10 UI ARCHITECTURE NOTE (Corrected + Inference‑Labeled)**

```md
# Phase 10 — UI Architecture Note
Corrected, aligned with authoritative Phase 10 specs, and with all inferred
elements explicitly marked as NON‑authoritative.

This document consolidates the UI architecture for Phase 10 based on:

- PHASE_10_UI_SPEC.md
- PHASE_10_REALTIME_MESSAGE_PROTOCOL.md
- PHASE_10_DEVELOPER_CONTRACT.md
- PHASE_10_REALTIME_FLOW_DIAGRAM.md

No new governance rules are introduced. No Phase 9 invariants are modified.

---

# 1. Authoritative UI Components (Required)

These components are explicitly required by the Phase 10 Developer Contract and
UI Spec.

## 1.1 RealtimeOverlay.tsx
**Authoritative**
- Renders real-time overlays from streamed frames.
- Subscribes to RealtimeContext.
- Updates on `frame` messages.

## 1.2 ProgressBar.tsx
**Authoritative**
- Element ID: `#progress-bar`
- Displays job progress (0–100).
- Driven by `progress` messages.

## 1.3 PluginInspector.tsx
**Authoritative**
- Element ID: `#plugin-inspector`
- Displays:
  - plugin name
  - latest timing
  - status
  - warnings
- Driven by `plugin_status` and `warning` messages.

---

# 2. Authoritative Realtime Infrastructure

## 2.1 RealtimeClient.ts
**Authoritative**
- Connects to `/v1/realtime`
- Implements reconnection strategy (documented in UI spec)
- Parses RealtimeMessage objects

## 2.2 RealtimeContext.tsx
**Authoritative**
- Stores:
  - latest frame
  - latest progress
  - plugin timings
  - warnings

## 2.3 useRealtime.ts
**Authoritative**
- Hook for subscribing to realtime state.

---

# 3. Authoritative UI Requirements

- Phase 9 IDs MUST remain unchanged:
  - `#device-selector`
  - `#toggle-*`
  - `#fps-slider`
- New Phase 10 IDs:
  - `#progress-bar`
  - `#plugin-inspector`
- No breaking changes to existing components.
- All new UI is additive.

---

# 4. Inferred UI Layout (NOT authoritative)

The following layout is **inferred** from the UI spec and real-time flow diagram.
It is **NOT** mandated by any authoritative file and MUST NOT be treated as a
governance rule.

```
RealtimeOverlay
Frame Viewer
├── ProgressBar
└── PluginInspector
```

This layout is a reasonable architectural interpretation, but developers may
adjust internal structure as long as:

- Required components exist
- Required IDs remain unchanged
- Required behavior is implemented

---

# 5. Message → UI Mapping (Authoritative)

| Message Type     | UI Component        | Behavior |
|------------------|---------------------|----------|
| `frame`          | RealtimeOverlay     | Update overlay |
| `progress`       | ProgressBar         | Update progress bar |
| `plugin_status`  | PluginInspector     | Update timing + status |
| `warning`        | PluginInspector     | Append warning |
| `error`          | Global UI handler   | Show error banner |
| `ping/pong`      | RealtimeClient      | Connection health |

---

# 6. Storybook Requirements (Authoritative)

A new story MUST exist:

```
RealtimeOverlay.stories.tsx
```

It MUST demonstrate:
- idle state
- streaming state
- error state

---

# 7. Completion Criteria (UI Portion)

Phase 10 UI is complete when:
- RealtimeOverlay renders streamed frames
- ProgressBar updates on progress messages
- PluginInspector displays metadata, timings, warnings
- RealtimeContext updates correctly
- RealtimeClient reconnects correctly
- Storybook story exists and renders
- No Phase 9 UI invariants are broken

---

# End of Document
```

---

