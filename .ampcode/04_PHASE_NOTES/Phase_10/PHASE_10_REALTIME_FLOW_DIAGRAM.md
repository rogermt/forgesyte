# Phase 10 — Real-Time Flow Diagram

Complete data flow and interactions for Phase 10 real-time system.

---

# 1. High-Level System Flow

```
User Interface
    │
    │ 1. Start Job
    ▼
┌─────────────────────────────────────────────────┐
│ POST /v1/jobs (Phase 9 endpoint)                │
│ Returns: JobResponse { job_id, ... }            │
└────────────────┬────────────────────────────────┘
                 │
                 │ 2. Store job_id
                 ▼
┌─────────────────────────────────────────────────┐
│ WS /v1/realtime (Phase 10 endpoint)             │
│ Connect: WebSocket handshake                    │
└────────────────┬────────────────────────────────┘
                 │
                 │ 3. Register connection
                 ▼
┌─────────────────────────────────────────────────┐
│ ConnectionManager.connect(session_id, ws)       │
│ Tracks active WebSocket connections             │
└────────────────┬────────────────────────────────┘
                 │
                 │ 4. Start receiving messages
                 ▼
┌─────────────────────────────────────────────────┐
│ Plugin Pipeline Execution                       │
│ (Runs job asynchronously)                       │
└────────────────┬────────────────────────────────┘
                 │
                 │ 5. Emit RealtimeMessage objects
                 ▼
┌─────────────────────────────────────────────────┐
│ RealtimeMessage {                               │
│   type: "frame" | "progress" | ...              │
│   payload: { ... }                              │
│   timestamp: "ISO8601"                          │
│ }                                               │
└────────────────┬────────────────────────────────┘
                 │
                 │ 6. Broadcast to all clients
                 ▼
┌─────────────────────────────────────────────────┐
│ ConnectionManager.broadcast(message)             │
│ For each connected WebSocket:                    │
│   send(message)                                 │
└────────────────┬────────────────────────────────┘
                 │
                 │ 7. Send to client
                 ▼
┌─────────────────────────────────────────────────┐
│ RealtimeClient.onMessage(message)               │
│ Parse and validate message schema               │
└────────────────┬────────────────────────────────┘
                 │
                 │ 8. Dispatch to context
                 ▼
┌─────────────────────────────────────────────────┐
│ RealtimeContext.dispatch({                      │
│   type: 'MESSAGE_RECEIVED',                     │
│   payload: message                              │
│ })                                              │
└────────────────┬────────────────────────────────┘
                 │
                 │ 9. Update state
                 ▼
┌─────────────────────────────────────────────────┐
│ realtimeReducer(state, action)                  │
│ Updates:                                        │
│   - progress                                    │
│   - currentFrame                                │
│   - pluginTimings                               │
│   - warnings                                    │
└────────────────┬────────────────────────────────┘
                 │
                 │ 10. Component re-render
                 ▼
┌─────────────────────────────────────────────────┐
│ RealtimeOverlay                                 │
│   ├─ ProgressBar (updated)                      │
│   ├─ FrameViewer (updated)                      │
│   └─ PluginInspector (updated)                  │
└─────────────────────────────────────────────────┘
```

---

# 2. Detailed Message Flow

## 2.1 Job Execution with Real-Time Messages

```
Timeline:
  0ms  │ Job starts
       │
 10ms  │ ┌─────────────────────┐
       │ │ MESSAGE: progress   │
       │ │ progress: 5         │
       │ │ stage: "Starting"   │
       │ └─────────────────────┘
       │
 20ms  │ ┌─────────────────────┐
       │ │ MESSAGE: metadata   │
       │ │ plugin: player_det  │
       │ │ metadata: {...}     │
       │ └─────────────────────┘
       │
 30ms  │ ┌─────────────────────┐
       │ │ MESSAGE: plug_stat  │
       │ │ plugin: player_det  │
       │ │ status: "started"   │
       │ └─────────────────────┘
       │
100ms  │ ┌─────────────────────┐
       │ │ MESSAGE: frame      │
       │ │ frame_id: f-001     │
       │ │ data: {...}         │
       │ │ timing_ms: 70       │
       │ └─────────────────────┘
       │
130ms  │ ┌─────────────────────┐
       │ │ MESSAGE: progress   │
       │ │ progress: 25        │
       │ └─────────────────────┘
       │
200ms  │ ┌─────────────────────┐
       │ │ MESSAGE: frame      │
       │ │ frame_id: f-002     │
       │ │ data: {...}         │
       │ │ timing_ms: 70       │
       │ └─────────────────────┘
       │
250ms  │ ┌─────────────────────┐
       │ │ MESSAGE: warning    │
       │ │ plugin: pitch_det   │
       │ │ message: "corners..." │
       │ └─────────────────────┘
       │
280ms  │ ┌─────────────────────┐
       │ │ MESSAGE: progress   │
       │ │ progress: 50        │
       │ └─────────────────────┘
       │
 ...
```

---

## 2.2 Connection Lifecycle

```
┌─────────────────────────────────────────────────────┐
│ CLIENT                 CONNECTION                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  WebSocket                                          │
│  connect()                                          │
│     │                                               │
│     └──────────────────────┐                        │
│                            │                        │
│                      HANDSHAKE                      │
│                            │                        │
│                    Server accepts                   │
│                    Sends metadata                   │
│                            │                        │
│     ┌──────────────────────┘                        │
│     │                                               │
│ CONNECTED                                           │
│ (listening for messages)                            │
│     │                                               │
│     │   ◄─ PROGRESS                                 │
│     │                                               │
│     │   ◄─ FRAME                                    │
│     │                                               │
│     │   ◄─ PLUGIN_STATUS                            │
│     │                                               │
│     │   ◄─ PING ──────► PONG ─────┐                │
│     │                            │                │
│     │                     (latency measured)       │
│     │                                               │
│     │   ◄─ WARNING                                  │
│     │                                               │
│     │   ◄─ PROGRESS (100%)                          │
│     │                                               │
│ DONE                                                │
│ Job completed                                       │
│ (connection stays open for next job)                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

# 3. Component Update Flow

## 3.1 RealtimeContext → Components

```
RealtimeContext.state
    │
    ├─ isConnected: boolean
    │
    ├─ progress: number
    │   └──► ProgressBar ◄──────────────────┐
    │       Updates width and label         │
    │                                       │
    ├─ currentFrame: FrameData | null       │
    │   └──► RealtimeOverlay ◄──────────────┤
    │       Updates frame viewer            │
    │                                       │
    ├─ pluginTimings: Record<str, num>      │
    │   └──► PluginInspector ◄──────────────┤
    │       Updates timing bars             │
    │                                       │
    ├─ pluginStatus: Record<str, status>    │
    │   └──► PluginInspector ◄──────────────┤
    │       Updates status badges           │
    │                                       │
    ├─ warnings: string[]                   │
    │   └──► PluginInspector ◄──────────────┤
    │       Updates warning list            │
    │                                       │
    └─ errors: string[]
        └──► ErrorBanner ◄───────────────────┘
             Shows error message
```

## 3.2 Reducer Logic (Detail)

```
RealtimeContext
    │
    │ useReducer(realtimeReducer, initialState)
    │
    ▼
EVENT: MESSAGE_RECEIVED
    │
    ├─ message.type === 'progress'
    │   │
    │   └──► state.progress = message.payload.progress
    │
    ├─ message.type === 'frame'
    │   │
    │   └──► state.currentFrame = message.payload.data
    │
    ├─ message.type === 'plugin_status'
    │   │
    │   ├──► state.pluginTimings[plugin] = timing_ms
    │   │
    │   └──► state.pluginStatus[plugin] = status
    │
    ├─ message.type === 'warning'
    │   │
    │   └──► state.warnings.push(message.payload.message)
    │
    ├─ message.type === 'error'
    │   │
    │   └──► state.errors.push(message.payload.error)
    │
    └─ [other types] ──► no state change
```

---

# 4. Plugin Execution Flow with Inspector

```
ToolRunner.execute(tool, frames, context)
    │
    ├─ 1. Create InspectorService
    │   │
    │   └─► inspector = InspectorService(tool_name)
    │
    ├─ 2. Inspect metadata
    │   │
    │   └─► metadata = inspector.inspect()
    │
    │       Emit MESSAGE: metadata
    │       {
    │         type: 'metadata',
    │         payload: { plugin, metadata }
    │       }
    │
    ├─ 3. Start timing
    │   │
    │   └─► inspector.start_timing()
    │
    ├─ 4. Execute tool
    │   │
    │   └─► for frame in frames:
    │          result = tool.process(frame)
    │
    │          ┌─────────────────────────────┐
    │          │ EMIT: frame message         │
    │          │ {                           │
    │          │   type: 'frame',            │
    │          │   payload: {                │
    │          │     frame_id,               │
    │          │     data: result,           │
    │          │     timing_ms: ...          │
    │          │   }                         │
    │          │ }                           │
    │          └─────────────────────────────┘
    │
    ├─ 5. Stop timing
    │   │
    │   └─► timing_ms = inspector.stop_timing()
    │
    ├─ 6. Collect warnings (if any)
    │   │
    │   └─► warnings = inspector.get_warnings()
    │
    │       For each warning:
    │       Emit MESSAGE: warning
    │       {
    │         type: 'warning',
    │         payload: {
    │           plugin,
    │           message,
    │           severity
    │         }
    │       }
    │
    ├─ 7. Emit final plugin_status
    │   │
    │   └─► Emit MESSAGE: plugin_status
    │       {
    │         type: 'plugin_status',
    │         payload: {
    │           plugin,
    │           status: 'completed',
    │           timing_ms,
    │           warnings_count: len(warnings)
    │         }
    │       }
    │
    └─ 8. Return results
        │
        └──► results, timings, warnings
```

---

# 5. Network Flow (Packet Level)

```
CLIENT                                    SERVER

1. WebSocket Upgrade
   ├─ GET /v1/realtime HTTP/1.1
   ├─ Upgrade: websocket
   └─ Sec-WebSocket-Key: ...
                                          HTTP 101 Switching Protocols
                                          Upgrade: websocket
                                          Sec-WebSocket-Accept: ...

2. Connection Established
   Connected WebSocket                   ConnectionManager tracks session

3. Server Emits Progress (Frame 0 of 5)
                                          ┌─────────────────────┐
                                          │ TYPE: progress      │
                                          │ progress: 0         │
                                          │ stage: "Starting"   │
                                          └─────────────────────┘
                                                    │
                                                    │ WebSocket send
                                                    ▼
   RealtimeClient receives
   Parses JSON message
   Calls onMessage handler
   
4. Server Emits Frame
                                          ┌─────────────────────┐
                                          │ TYPE: frame         │
                                          │ data: {...}         │
                                          │ timing: 145.5ms     │
                                          └─────────────────────┘
                                                    │
                                                    │ WebSocket send
                                                    ▼
   RealtimeClient receives
   Dispatches to context
   Context updates state
   Component renders

5. Server Emits Progress
                                          ┌─────────────────────┐
                                          │ TYPE: progress      │
                                          │ progress: 25        │
                                          └─────────────────────┘
                                                    │
                                                    │ WebSocket send
                                                    ▼
   (repeats)

6. Server Emits Ping
                                          ┌─────────────────────┐
                                          │ TYPE: ping          │
                                          └─────────────────────┘
                                                    │
                                                    │ WebSocket send
                                                    ▼
   RealtimeClient receives
   Auto-responds with pong
                                          ◄─────────────────────
                                          TYPE: pong
                                          
   Server measures latency
   Logs heartbeat

7. Job Complete
                                          ┌─────────────────────┐
                                          │ TYPE: progress      │
                                          │ progress: 100       │
                                          └─────────────────────┘
                                                    │
                                                    │ WebSocket send
                                                    ▼
   Final state update
   Job shown as complete
```

---

# 6. Error Scenarios

## 6.1 WebSocket Disconnect During Job

```
WebSocket connected
    │
Job in progress ◄─ Emitting messages
    │
    │ Network issue
    │
WebSocket disconnects
    │
RealtimeClient detects disconnect
    │
Client calls onError()
    │
RealtimeContext receives error
    │
UI shows "Reconnecting..."
    │
[Exponential backoff: 1s, 2s, 4s, 8s, 16s]
    │
    ├─ Attempt 1 ──► Fail (server still restarting)
    │
    ├─ Attempt 2 ──► Fail (network down)
    │
    ├─ Attempt 3 ──► Success! WebSocket reconnects
    │
UI hides "Reconnecting..."
    │
Job may continue (if still running on server)
    │
OR
    │
Max attempts (5) exceeded
    │
UI shows "Connection lost"
    │
User must manually retry or reload
```

## 6.2 Plugin Emits Warning

```
ToolRunner executing plugin
    │
Plugin processing frame
    │
    │ Soft failure detected
    │ (e.g., confidence too low)
    │
Plugin emits warning
    │
InspectorService captures warning
    │
ToolRunner continues (does not crash)
    │
Emit MESSAGE: warning
{
  type: 'warning',
  payload: {
    plugin: 'ball_detection',
    message: 'Confidence too low',
    severity: 'medium'
  }
}
    │
RealtimeClient sends to UI
    │
PluginInspector appends warning
    │
User sees warning in warnings list
    │
Job continues normally
```

---

# 7. Performance Characteristics

## 7.1 Latency Budget (per message)

```
Event happens on server
    │ (1ms)
    ▼
Message created
    │ (0.1ms)
    ▼
Serialized to JSON
    │ (1ms)
    ▼
Sent over WebSocket
    │ (10-50ms network latency)
    ▼
Received by client
    │ (0.1ms)
    ▼
Parsed by RealtimeClient
    │ (0.5ms)
    ▼
Dispatched to context
    │ (0.1ms)
    ▼
Reducer processes action
    │ (0.5ms)
    ▼
Component renders
    │ (5-20ms React render)
    ▼
User sees update

Total: 10-50ms latency (p95)
```

## 7.2 Message Throughput

```
Job with 1000 frames
Assume 5 plugins
Total messages:
  - progress: ~100 (every 10%)
  - frame: ~1000 * 5 = 5000
  - plugin_status: ~5 per plugin = 25
  - warning: ~10-50 (estimated)
  - metadata: ~5 (on connect)
  ─────────────
  Total: ~5,100-5,200 messages

Duration: ~15-30 seconds (job processing)
Throughput: ~170-345 messages/second

Server queue limits:
  - Per connection: 1000 messages max
  - If queue exceeds 1000: Drop lowest-priority messages (e.g., frame)
  - Server NEVER blocks on message send
```

---

# 8. Summary

Phase 10 real-time flow is:

✅ **Asynchronous**: Server does not wait for client ACK
✅ **Resilient**: Auto-reconnect with backoff
✅ **Scalable**: Multiple clients per job
✅ **Low-latency**: <50ms (p95) message-to-UI
✅ **Graceful**: Handles errors without crashing
✅ **Observable**: Full traceability of messages

