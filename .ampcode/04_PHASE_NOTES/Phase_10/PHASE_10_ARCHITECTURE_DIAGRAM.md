# Phase 10 Architecture Diagram

Real-Time Insights + Plugin Pipeline Upgrade

---

## System Architecture

```
                          ┌────────────────────────────┐
                          │        Client (UI)          │
                          │  React + RealtimeContext    │
                          └───────────────┬─────────────┘
                                          │
                                          │ WebSocket/SSE
                                          │ /v1/realtime
                                          ▼
                          ┌────────────────────────────┐
                          │   Real-Time Endpoint        │
                          │  (websocket_router.py)      │
                          │  - Frame streaming          │
                          │  - Progress updates         │
                          │  - Plugin timings           │
                          │  - Warnings/errors          │
                          └───────────────┬─────────────┘
                                          │
                                          │ dispatches messages
                                          ▼
                          ┌────────────────────────────┐
                          │  ConnectionManager          │
                          │  - tracks clients           │
                          │  - broadcasts messages      │
                          │  - handles reconnection     │
                          └───────────────┬─────────────┘
                                          │
                                          │ pulls updates from
                                          ▼
                          ┌────────────────────────────┐
                          │ Plugin Inspector Service    │
                          │  (inspector_service.py)     │
                          │  - metadata extraction      │
                          │  - timing collection        │
                          │  - warning emission         │
                          └───────────────┬─────────────┘
                                          │
                                          │ executes tools via
                                          ▼
                          ┌────────────────────────────┐
                          │      Tool Runner            │
                          │  - real-time plugin exec    │
                          │  - progress tracking        │
                          │  - error handling           │
                          └───────────────┬─────────────┘
                                          │
                                          │ produces
                                          ▼
                          ┌────────────────────────────┐
                          │   RealtimeMessage           │
                          │  - frame                    │
                          │  - partial_result           │
                          │  - progress                 │
                          │  - plugin_status            │
                          │  - warning                  │
                          │  - error                    │
                          └────────────────────────────┘
```

---

## Frontend Component Hierarchy

```
App
├── RealtimeContext
│   ├── RealtimeClient (connection logic)
│   └── RealtimeProvider (state management)
│
├── RealtimeOverlay
│   ├── ProgressBar (#progress-bar)
│   ├── PluginInspector (#plugin-inspector)
│   │   ├── PluginMetadata
│   │   ├── TimingChart
│   │   └── WarningList
│   └── FrameRenderer
│
└── [Existing Components]
    ├── DeviceSelector
    ├── ControlPanel
    └── JobStatus
```

---

## Backend Service Architecture

```
app/
├── api/
│   ├── realtime/
│   │   ├── websocket_router.py
│   │   ├── connection_manager.py
│   │   └── message_handler.py
│   └── jobs.py (updated)
│
├── services/
│   ├── plugins/
│   │   ├── inspector_service.py (NEW)
│   │   ├── plugin_executor.py (updated)
│   │   └── plugin_registry.py
│   └── jobs.py
│
├── models/
│   ├── job.py (Phase 9 unchanged)
│   ├── extended_job.py (NEW)
│   └── realtime_message.py (NEW)
│
└── core/
    └── config.py
```

---

## Data Flow: Real-Time Job Execution

```
1. Client connects to /v1/realtime
   └─> ConnectionManager registers session

2. Client starts job
   └─> POST /v1/jobs (Phase 9 unchanged)

3. Server creates PluginInspector
   └─> Inspects plugin metadata

4. ToolRunner executes plugins
   ├─> EmitMessage(type='progress', progress=25)
   ├─> ProcessFrame → EmitMessage(type='frame', data={...})
   ├─> EmitMessage(type='plugin_status', timing_ms=150)
   └─> EmitMessage(type='progress', progress=100)

5. ConnectionManager broadcasts to all connected clients
   ├─> Message: RealtimeMessage
   └─> Client receives → Updates UI state

6. Job completes
   └─> EmitMessage(type='complete') [optional]
```

---

## Phase 9 vs Phase 10: API Invariants

### Phase 9 (Unchanged)
```
GET /v1/jobs/{job_id}
└─> JobResponse
    ├── job_id: str
    ├── device_requested: str
    ├── device_used: str
    ├── fallback: bool
    └── frames: List[FrameData]
```

### Phase 10 (Additive)
```
GET /v1/jobs/{job_id}  (unchanged)
└─> JobResponse (unchanged)

GET /v1/jobs/{job_id}/extended  (NEW, optional)
└─> ExtendedJobResponse
    ├── [all Phase 9 fields]
    ├── progress: Optional[int]
    ├── plugin_timings: Optional[Dict[str, float]]
    └── warnings: Optional[List[str]]

WebSocket /v1/realtime  (NEW, optional)
└─> RealtimeMessage
    ├── type: str
    ├── payload: dict
    └── timestamp: datetime
```

---

## Message Flow Example: Processing a Frame

```
Client                          Server                      Plugin
  │                               │                            │
  │────── start job ─────────────>│                            │
  │                               │──── create inspector ──────>│
  │                               │<──── metadata returned ─────│
  │                               │                            │
  │                               │──── execute tool ─────────>│
  │<────── progress: 10 ──────────│                            │
  │                               │                            │
  │                               │<──── frame + timing ───────│
  │<────── frame data ────────────│                            │
  │<────── timing: 45ms ──────────│                            │
  │<────── progress: 50 ──────────│                            │
  │                               │                            │
  │                               │──── next tool ────────────>│
  │<────── progress: 60 ──────────│                            │
  │                               │<──── frame + warning ──────│
  │<────── frame data ────────────│                            │
  │<────── warning: "..." ────────│                            │
  │<────── progress: 100 ─────────│                            │
  │                               │                            │
```

---

## Connection Management

```
ConnectionManager
├── active_connections: Dict[session_id, WebSocket]
├── broadcast(message: RealtimeMessage)
│   └─> For each connection, send JSON message
├── add_connection(session_id, ws)
├── remove_connection(session_id)
└── is_connected(session_id)
```

---

## Timing Collection

```
PluginInspector
├── inspect(plugin_name) -> PluginMetadata
├── start_timing(plugin_name)
├── stop_timing(plugin_name) -> float (ms)
└── collect_timings() -> Dict[str, float]
```

---

## Error Handling

```
Phase 10 errors are ALWAYS non-breaking:

✓ Plugin fails → emit warning message
✓ Connection drops → client reconnects
✓ Real-time disabled → job continues in Phase 9 mode
✓ Inspector unavailable → proceed without metadata
```

---

## UI State Management

```
RealtimeContext
├── state: {
│   ├── isConnected: boolean
│   ├── progress: number (0-100)
│   ├── currentFrame: FrameData | null
│   ├── pluginTimings: Dict<string, number>
│   ├── warnings: Array<string>
│   └── errors: Array<string>
│   }
├── dispatch(action)
└── subscribe(listener)
```

---

## Backward Compatibility

Phase 10 maintains 100% Phase 9 compatibility:

- Phase 9 jobs work unchanged
- Phase 9 API responses unchanged
- Phase 9 UI IDs unchanged
- Real-time is purely additive
- If real-time unavailable, system degrades gracefully

