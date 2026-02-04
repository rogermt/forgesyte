# Phase 10 — End-to-End Flow Spec

Complete specification of the end-to-end flow for a real-time analysis job in Phase 10.

---

# 1. Job Lifecycle Overview

```
┌─────────────────────────────────────────────────────┐
│ USER INITIATES JOB                                  │
│ (Phase 9 behavior - unchanged)                      │
└────────────┬──────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│ POST /v1/jobs (or /v1/analyze)                      │
│ Returns: JobResponse { job_id, device, frames=[] } │
│ (Phase 9 response - unchanged)                      │
└────────────┬──────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│ UI ESTABLISHES REALTIME CONNECTION (NEW)            │
│ WS ws://server/v1/realtime?job_id=<id>              │
└────────────┬──────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│ SERVER PLUGIN PIPELINE EXECUTES (Phase 9)           │
│ InspectorService collects timings/warnings (NEW)    │
│ ToolRunner emits RealtimeMessages (NEW)             │
│ ConnectionManager broadcasts to clients (NEW)       │
└────────────┬──────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│ UI COMPONENTS UPDATE LIVE (NEW)                     │
│ - ProgressBar ← progress messages                   │
│ - RealtimeOverlay ← frame messages                  │
│ - PluginInspector ← plugin_status messages          │
└────────────┬──────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│ JOB COMPLETES                                       │
│ (Phase 9 behavior - unchanged)                      │
└─────────────────────────────────────────────────────┘
```

---

# 2. Phase 9: Job Creation (Unchanged)

## 2.1 Request

```http
POST /v1/jobs HTTP/1.1
Content-Type: application/json

{
  "source": "video.mp4",
  "device_requested": "gpu",
  "plugins": ["player_detection", "ball_detection"]
}
```

## 2.2 Response

```json
{
  "job_id": "job-abc123",
  "device_requested": "gpu",
  "device_used": "cuda:0",
  "fallback": false,
  "frames": []
}
```

**Invariants (MUST NOT change):**
- All fields present and typed correctly
- Frames array present (initially empty)
- No new fields added to JobResponse

---

# 3. Phase 10: Real-Time Connection (New)

## 3.1 WebSocket Connection

### Request

```
GET /v1/realtime HTTP/1.1
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: ...
Sec-WebSocket-Version: 13

Query params (optional):
  ?job_id=job-abc123
  ?session_id=<uuid>
```

### Response

```
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: ...
```

## 3.2 Connection Established

```
Server sends initial metadata messages:
  → metadata messages (one per plugin)
  → ping (to establish heartbeat)

Client responds:
  ← pong
  → ready to receive job messages
```

**Notes:**
- Connection is optional (Phase 9 jobs still work without it)
- Multiple clients can connect for same job
- Connection remains open until job completion

---

# 4. Plugin Execution with Real-Time Emissions

## 4.1 Job Start

```
Server:
  1. Creates ToolRunner with ConnectionManager reference
  2. Creates InspectorService
  3. Emits: { type: 'progress', payload: { progress: 0, stage: 'Starting' } }
  
Client:
  ← Receives progress=0
  ← RealtimeContext updates state
  ← ProgressBar updates to 0%
```

## 4.2 Per-Plugin Initialization

```
Server:
  1. InspectorService.inspect(plugin_name)
  2. Emits: { type: 'metadata', payload: { plugin, metadata } }
  3. InspectorService.start_timing()
  4. Emits: { type: 'plugin_status', payload: { plugin, status: 'started' } }
  
Client:
  ← Receives metadata
  ← RealtimeContext stores plugin metadata
  ← PluginInspector prepares plugin entry
```

## 4.3 Per-Frame Processing

```
For each frame:

Server:
  1. Plugin processes frame
  2. Result = plugin.run(frame)
  3. Timing captured
  4. Emit: { type: 'frame', payload: { frame_id, data: result, timing_ms } }
  5. Emit: { type: 'progress', payload: { progress: X% } }
  
Client:
  ← Receives frame message
  ← RealtimeOverlay updates with new frame
  ← RealtimeContext stores currentFrame
  ← Frame viewer displays annotation
  
  ← Receives progress message
  ← ProgressBar updates to X%
```

## 4.4 Plugin Completion

```
Server:
  1. InspectorService.stop_timing()
  2. timing_ms = calculated
  3. Collect warnings = InspectorService.get_warnings()
  4. Emit: { type: 'plugin_status', payload: { plugin, status: 'completed', timing_ms } }
  5. For each warning: { type: 'warning', payload: { plugin, message } }
  
Client:
  ← Receives plugin_status (completed)
  ← PluginInspector shows ✓ Completed badge
  ← PluginInspector updates timing bar
  
  ← Receives warning messages
  ← PluginInspector accumulates in warning list
```

## 4.5 Job Completion

```
Server:
  1. All plugins complete
  2. Emit: { type: 'progress', payload: { progress: 100 } }
  3. Job finished, can close WebSocket or keep alive
  
Client:
  ← Receives progress=100
  ← ProgressBar shows 100%, "Complete"
  ← UI transitions to "Job Complete" state
```

---

# 5. Error Handling

## 5.1 Plugin Error (Non-Fatal)

```
Server:
  Plugin fails gracefully (soft error)
  
  Emit: { type: 'warning', payload: { plugin, message, severity: 'high' } }
  
  Continue with next plugin
  
Client:
  ← Receives warning
  ← PluginInspector shows warning in red
  ← Job continues (not blocked)
```

## 5.2 Plugin Error (Fatal)

```
Server:
  Plugin crashes or raises fatal exception
  
  Emit: { type: 'error', payload: { error, plugin, details } }
  Emit: { type: 'progress', payload: { progress: 100 } }  // Mark as done
  
  Job terminates (or retries)
  
Client:
  ← Receives error message
  ← ErrorBanner displays prominently
  ← ProgressBar stops at current %
  ← UI shows error state
```

## 5.3 WebSocket Disconnect (Client)

```
Server:
  Client disconnects unexpectedly
  
  ConnectionManager removes client
  Job continues (doesn't care)
  Messages still broadcast to other clients
  
Client:
  WebSocket closes
  
  RealtimeClient enters RECONNECTING state
  Exponential backoff: 1s, 2s, 4s, 8s, 16s
  
  If reconnects: Resume receiving messages from where it left off (best-effort)
  If max retries exceeded: Show "Connection lost" error
```

## 5.4 Server Shutdown

```
Server:
  Receives SIGTERM/SIGINT
  
  For each client:
    Send graceful close frame (WS code 1000)
    Wait for ACK
    Close connection
  
  InspectorService cleans up
  Job may be killed or re-queued
  
Client:
  Receives WS close frame (code 1000)
  
  Understands: Graceful server shutdown
  Enters RECONNECTING state (optional)
  Or: User refreshes page
```

---

# 6. Real-Time Message Ordering

## 6.1 Order Guarantee

Messages MUST arrive in this order:

```
1. metadata (if available)
2. progress=0
3. plugin_status (status: started)
4. [per frame: frame + progress update]
5. plugin_status (status: completed)
6. warnings (if any)
7. [repeat for next plugin]
8. progress=100
```

## 6.2 Out-of-Order Handling

If messages arrive out of order (network quirk):

```
Client:
  - UI handles gracefully (no crash on backward progress)
  - Warnings always append (never deduplicate or overwrite)
  - Latest frame always wins (if newer frame arrives late)
  - Progress updates smoothly (even if not monotonic, uses latest)
```

---

# 7. Extended Job Model Updates

## 7.1 Progressive Updates

As job executes, Extended Job Model fills in:

```
Initial (after POST /v1/jobs):
  {
    "job_id": "job-abc123",
    "device_requested": "gpu",
    "device_used": "cuda:0",
    "fallback": false,
    "frames": [],
    "progress": null,
    "plugin_timings": null,
    "warnings": null
  }

During execution (GET /v1/jobs/{id}/extended):
  {
    "progress": 50,
    "plugin_timings": {
      "player_detection": 145.5,
      "ball_detection": 98.2
    },
    "warnings": [
      "Pitch corners not detected",
      "Low confidence in team classification"
    ]
  }

On completion:
  {
    "progress": 100,
    "plugin_timings": {
      "player_detection": 145.5,
      "ball_detection": 98.2,
      "pitch_detection": 156.3
    },
    "warnings": [
      "Pitch corners not detected",
      "Low confidence in team classification"
    ]
  }
```

## 7.2 Access Pattern

```
Client polls GET /v1/jobs/{id}/extended periodically:
  - Every 1 second (or on demand)
  - Extended model reflects current job state
  - Can be used as fallback if WebSocket unavailable
```

---

# 8. Multi-Client Scenario

## 8.1 Multiple Users Watching Same Job

```
User A connects to /v1/realtime
User B connects to /v1/realtime (same job)

Server:
  ConnectionManager tracks 2 connections
  Job executes normally
  
  Each message broadcast to BOTH users:
    → User A receives frame
    → User B receives frame
    
Result:
  Both users see real-time updates
  No conflicts (read-only stream)
```

## 8.2 Message Buffering

```
User C connects 30 seconds into job:
  
  Server:
    Does NOT buffer previous messages
    Sends current progress (from ExtendedJobModel)
    Continues streaming new messages
  
Result:
  User C sees partial history (from GET request)
  Real-time messages from that point forward
  No gap in real-time (but missed early frames)
```

---

# 9. Fallback Scenarios

## 9.1 WebSocket Unavailable

```
Client:
  Tries to connect to /v1/realtime
  Connection fails (server error, network issue)
  
Fallback:
  Client polls GET /v1/jobs/{id}/extended periodically
  Updates UI with latest state
  
Result:
  No real-time updates (laggy)
  But job still completes (Phase 9 mode)
```

## 9.2 Real-Time Optional

```
Client (simple):
  Does NOT connect to /v1/realtime
  Only calls GET /v1/jobs/{id} periodically
  
Result:
  Works (Phase 9 mode)
  No real-time overlays
  But job completes (backward compatible)
```

---

# 10. Timing of Events

## 10.1 Job with 5 frames, 3 plugins

```
Timeline:

0ms   POST /v1/jobs
      ← job_id=job-123
      
      WS /v1/realtime (connect)
      ← connection opened
      
10ms  Frame 0 processing starts
      → type: progress, progress: 5
      → type: plugin_status, status: started (player_detection)
      
100ms Frame 0 complete
      → type: frame, frame_id: f-0
      → type: progress, progress: 15
      → type: plugin_status, status: completed, timing: 90ms
      
110ms Frame 1 processing starts
      → type: progress, progress: 20
      → type: plugin_status, status: started (player_detection)
      
...

500ms All frames processed by all plugins
      → type: progress, progress: 100
      → type: warning, message: "..."
      
510ms Job finishes
      (job_id available in extended model)
      
      Client displays: Progress 100%, all frames, timings, warnings
```

---

# 11. Completion Criteria

End-to-end flow is complete when:

✅ Job creation works (Phase 9 unchanged)
✅ WebSocket connection opens and stays open
✅ Messages arrive in order
✅ Real-time UI updates within 200ms
✅ Progress bar updates smoothly (0→100)
✅ Frames display correctly
✅ Plugin timings display correctly
✅ Warnings accumulate without loss
✅ Errors handled gracefully (no crashes)
✅ Disconnect/reconnect works
✅ Multiple clients can watch same job
✅ Phase 9 mode (no WebSocket) still works
✅ All Phase 9 tests pass (backward compatible)

---

# 12. Example: Full Job Execution (5 frames, 2 plugins)

```json
// 1. User clicks "Start Job"

POST /v1/jobs
→ Response: { "job_id": "job-xyz", ... "frames": [] }

// 2. UI connects to real-time

WS /v1/realtime
← 101 Switching Protocols
← (server sends ping)
→ (client sends pong)

// 3. Server starts job

→ { "type": "progress", "payload": { "progress": 0 }, "timestamp": "..." }
← ProgressBar updates to 0%

→ { "type": "metadata", "payload": { "plugin": "player_detection", ... } }
← PluginInspector stores metadata

// 4. Process frames (plugin 1)

→ { "type": "plugin_status", "payload": { "plugin": "player_detection", "status": "started" } }
← PluginInspector shows ⏳ Started

[For frame 0-4:]
→ { "type": "frame", "payload": { "frame_id": "f-0", "data": {...}, "timing_ms": 90 } }
← RealtimeOverlay displays frame

→ { "type": "progress", "payload": { "progress": 20 } }
← ProgressBar updates to 20%

// 5. Plugin 1 complete

→ { "type": "plugin_status", "payload": { "plugin": "player_detection", "status": "completed", "timing_ms": 450 } }
← PluginInspector shows ✓ Completed with timing 450ms

// 6. Process frames (plugin 2)

→ { "type": "metadata", "payload": { "plugin": "ball_detection", ... } }
→ { "type": "plugin_status", "payload": { "plugin": "ball_detection", "status": "started" } }

[For frame 0-4:]
→ { "type": "frame", "payload": { "frame_id": "f-0", "data": {...}, "timing_ms": 45 } }
→ { "type": "progress", "payload": { "progress": 60 } }

// 7. Warning during plugin 2

→ { "type": "warning", "payload": { "plugin": "ball_detection", "message": "Low confidence" } }
← PluginInspector adds warning to list

// 8. Plugin 2 complete

→ { "type": "plugin_status", "payload": { "plugin": "ball_detection", "status": "completed", "timing_ms": 225 } }

// 9. Job complete

→ { "type": "progress", "payload": { "progress": 100 } }
← ProgressBar shows 100%, "Complete"

(WebSocket stays open, or closes with code 1000)

// 10. UI can now call GET /v1/jobs/job-xyz/extended to get final state

GET /v1/jobs/job-xyz/extended
← {
  "job_id": "job-xyz",
  "device_requested": "gpu",
  "device_used": "cuda:0",
  "fallback": false,
  "frames": [...],
  "progress": 100,
  "plugin_timings": {
    "player_detection": 450,
    "ball_detection": 225
  },
  "warnings": [
    "Low confidence in ball detection"
  ]
}
```

