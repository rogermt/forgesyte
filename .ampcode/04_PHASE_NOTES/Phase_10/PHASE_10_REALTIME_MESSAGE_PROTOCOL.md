# Phase 10 — Real-Time Message Protocol

Complete specification for real-time messaging in Phase 10.

---

# 1. Base Schema

All messages MUST conform to:

```json
{
  "type": "<message-type>",
  "payload": { },
  "timestamp": "<ISO8601>"
}
```

**Fields:**
- `type` (string, required): Message type identifier
- `payload` (object, required): Type-specific data
- `timestamp` (string, required): ISO 8601 datetime (UTC)

**Example:**
```json
{
  "type": "progress",
  "payload": {
    "job_id": "job-123",
    "progress": 45
  },
  "timestamp": "2025-02-04T15:30:00.123Z"
}
```

---

# 2. Message Types

## 2.1 `frame`

Emitted when a new annotated frame is available from a plugin.

**Payload:**
```json
{
  "frame_id": "frame-001",
  "plugin": "player_detection",
  "data": {
    "boxes": [
      {
        "x": 100,
        "y": 200,
        "width": 50,
        "height": 80,
        "confidence": 0.95,
        "class": "player"
      }
    ],
    "metadata": {}
  },
  "device_used": "cpu",
  "timing_ms": 145.5
}
```

**Fields:**
- `frame_id` (string): Unique identifier for this frame
- `plugin` (string): Name of the plugin that produced this frame
- `data` (object): Plugin-specific frame data
- `device_used` (string): Device used ('cpu', 'gpu', 'cuda')
- `timing_ms` (number): Processing time in milliseconds

**Client Action:**
Update overlay with annotated frame.

---

## 2.2 `partial_result`

Emitted when a plugin produces intermediate results before the job completes.

**Payload:**
```json
{
  "result": {
    "detections": 12,
    "confidence_avg": 0.87,
    "teams_identified": 2
  },
  "plugin": "team_classification",
  "partial": true
}
```

**Fields:**
- `result` (object): Intermediate result data
- `plugin` (string): Plugin name
- `partial` (boolean): Always `true` for this message type

**Client Action:**
Accumulate results; display in plugin inspector.

---

## 2.3 `progress`

Emitted when overall job progress updates.

**Payload:**
```json
{
  "job_id": "job-abc123",
  "progress": 65,
  "stage": "Processing frame 3 of 5",
  "plugin": "player_detection"
}
```

**Fields:**
- `job_id` (string): Job ID
- `progress` (integer): Progress percentage (0–100)
- `stage` (string, optional): Human-readable stage description
- `plugin` (string, optional): Current plugin name

**Client Action:**
Update progress bar. Update current stage label.

---

## 2.4 `plugin_status`

Emitted when a plugin completes or status changes.

**Payload:**
```json
{
  "plugin": "ball_detection",
  "status": "completed",
  "timing_ms": 234.7,
  "frames_processed": 5,
  "warnings_count": 0
}
```

**Fields:**
- `plugin` (string): Plugin name
- `status` (string): One of: `started`, `running`, `completed`, `failed`
- `timing_ms` (number): Total plugin execution time
- `frames_processed` (integer, optional): Number of frames processed
- `warnings_count` (integer, optional): Number of warnings emitted

**Client Action:**
Update plugin inspector with timing & status. Highlight completed plugins.

---

## 2.5 `warning`

Emitted when a plugin emits a non-fatal warning or soft failure.

**Payload:**
```json
{
  "plugin": "pitch_detection",
  "message": "Pitch corners not detected. Using fallback coordinates.",
  "severity": "low",
  "frame_id": "frame-042"
}
```

**Fields:**
- `plugin` (string): Plugin name
- `message` (string): Warning text
- `severity` (string): One of: `low`, `medium`, `high`
- `frame_id` (string, optional): Associated frame ID

**Client Action:**
Accumulate warnings. Display in plugin inspector warning list.

---

## 2.6 `error`

Emitted when a fatal error occurs. Job may still be recoverable.

**Payload:**
```json
{
  "error": "CUDA out of memory",
  "plugin": "player_tracking",
  "details": {
    "error_code": "CUDA_ERROR_OUT_OF_MEMORY",
    "message": "Failed to allocate 2GB on GPU",
    "fallback": "Retrying on CPU"
  },
  "frame_id": "frame-015"
}
```

**Fields:**
- `error` (string): Error title
- `plugin` (string, optional): Plugin that raised the error
- `details` (object, optional): Error details
  - `error_code` (string): Machine-readable error code
  - `message` (string): Detailed message
  - `fallback` (string, optional): Recovery action
- `frame_id` (string, optional): Associated frame ID

**Client Action:**
Display error banner. Optionally pause playback. Log error.

---

## 2.7 `ping`

Sent by server to check connection health.

**Payload:**
```json
{
  "interval_seconds": 30
}
```

**Fields:**
- `interval_seconds` (number, optional): Server's ping interval

**Client Action:**
Respond with `pong` message.

---

## 2.8 `pong`

Sent by client in response to server `ping`.

**Payload:**
```json
{
  "timestamp": "2025-02-04T15:30:00.123Z"
}
```

**Fields:**
- `timestamp` (string): Client timestamp (for latency measurement)

**Client Action:**
Server records latency; no further action needed.

---

## 2.9 `metadata`

Sent once when plugin metadata becomes available.

**Payload:**
```json
{
  "plugin": "player_detection",
  "metadata": {
    "version": "3.0",
    "model": "football-player-detection-v3.pt",
    "input_shape": [640, 480, 3],
    "output_format": "boxes",
    "confidence_default": 0.25,
    "capabilities": ["detection", "tracking"]
  }
}
```

**Fields:**
- `plugin` (string): Plugin name
- `metadata` (object): Plugin-specific metadata
  - `version` (string): Plugin version
  - `model` (string): Model file name
  - `input_shape` (array): Expected input dimensions
  - `output_format` (string): Output format type
  - `confidence_default` (number): Default confidence threshold
  - `capabilities` (array): Plugin capabilities

**Client Action:**
Store in plugin inspector. Display in UI when requested.

---

# 3. Message Ordering and Delivery

## 3.1 Ordering Guarantees

- Messages **MUST** be delivered in order within a single WebSocket connection
- **Exception**: `ping` and `pong` messages may arrive out of order
- Frame numbering (`frame_id`) determines true ordering for frames

## 3.2 Delivery Semantics

- **At-most-once**: Messages are sent once; server does NOT retry on client disconnect
- **Best-effort**: Network failures may drop messages
- **No buffering**: Server does NOT buffer messages for clients that reconnect

## 3.3 Backpressure

Server SHOULD implement backpressure:
- If client cannot receive messages fast enough
- Server MAY drop low-priority messages (e.g., frame updates)
- Server MUST NOT drop error messages

---

# 4. Connection Lifecycle

## 4.1 Connection Establishment

```
Client                                  Server
  │
  │────── WebSocket CONNECT ─────────────>│
  │                                       │
  │<────── metadata message ──────────────│
  │<────── metadata message ──────────────│
  │
  │────── (ready to receive) ────────────>│
  │
```

## 4.2 Active Session

```
Server                                  Client
  │
  │────── progress, 25 ─────────────────>│
  │────── frame data ───────────────────>│
  │────── plugin_status ────────────────>│
  │────── progress, 50 ─────────────────>│
  │────── warning ──────────────────────>│
  │
  │<────── pong ────────────────────────│
  │
  │────── progress, 100 ────────────────>│
  │────── complete (optional) ─────────>│
  │
```

## 4.3 Disconnection

```
Client                                  Server
  │
  │────── close connection ──────────────>│
  │                                       │
  │<────── close ACK ─────────────────────│
  │                                       │
  (client may reconnect)
```

---

# 5. Client Responsibilities

The frontend MUST:

1. **Connect and Reconnect**
   - Connect to `/v1/realtime` on app startup
   - Automatically reconnect on disconnect (exponential backoff)
   - Max reconnection attempts: 5, with delays: 1s, 2s, 4s, 8s, 16s

2. **Handle Messages**
   - Parse all message types
   - Validate required fields
   - Handle unknown message types gracefully (ignore)

3. **Respond to Ping**
   - Listen for `ping` messages
   - Respond immediately with `pong`
   - Include timestamp for latency measurement

4. **Update UI**
   - Update progress bar on `progress` messages
   - Update overlay on `frame` messages
   - Display warnings on `warning` messages
   - Show errors on `error` messages
   - Update plugin inspector on `plugin_status` messages

5. **Error Handling**
   - Log all errors and warnings
   - Display errors in error banner
   - Do NOT crash on malformed messages
   - Do NOT break if real-time unavailable

---

# 6. Server Responsibilities

The backend MUST:

1. **Accept Connections**
   - Listen on `/v1/realtime`
   - Accept WebSocket OR SSE connections
   - Support concurrent clients

2. **Send Heartbeat**
   - Send `ping` every 30 seconds
   - Timeout clients after 60 seconds without response

3. **Broadcast Messages**
   - Route plugin output to all connected clients
   - Do NOT wait for all clients to receive before moving on
   - Implement backpressure if queue exceeds threshold

4. **Validate Messages**
   - Ensure all messages have `type`, `payload`, `timestamp`
   - Reject messages with missing required fields
   - Use consistent timestamp format (ISO 8601)

5. **Cleanup**
   - Remove disconnected clients from broadcast list
   - Log connection lifecycle events
   - Never block plugin execution on message send

---

# 7. Error Codes

| Code | Message | Recoverable |
|------|---------|-------------|
| `MSG_INVALID_JSON` | Message is not valid JSON | Yes (skip) |
| `MSG_MISSING_FIELD` | Required field missing | Yes (skip) |
| `PLUGIN_TIMEOUT` | Plugin execution timed out | Yes (retry) |
| `PLUGIN_CRASH` | Plugin process crashed | No (fail job) |
| `DEVICE_UNAVAILABLE` | Requested device not available | Yes (fallback) |
| `CONNECTION_LOST` | Server lost connection to client | Yes (reconnect) |

---

# 8. Example Conversation

```json
=== CLIENT CONNECTS ===
(WebSocket handshake)

=== SERVER SENDS METADATA ===
{
  "type": "metadata",
  "payload": {
    "plugin": "player_detection",
    "metadata": {
      "version": "3.0",
      "model": "football-player-detection-v3.pt"
    }
  },
  "timestamp": "2025-02-04T15:30:00Z"
}

=== JOB STARTS ===
{
  "type": "progress",
  "payload": {
    "job_id": "job-abc123",
    "progress": 0,
    "stage": "Starting job"
  },
  "timestamp": "2025-02-04T15:30:01Z"
}

{
  "type": "plugin_status",
  "payload": {
    "plugin": "player_detection",
    "status": "started"
  },
  "timestamp": "2025-02-04T15:30:02Z"
}

=== FRAME PROCESSING ===
{
  "type": "progress",
  "payload": {
    "job_id": "job-abc123",
    "progress": 25,
    "stage": "Processing frame 1 of 4"
  },
  "timestamp": "2025-02-04T15:30:03Z"
}

{
  "type": "frame",
  "payload": {
    "frame_id": "frame-001",
    "plugin": "player_detection",
    "data": { "boxes": [...] },
    "device_used": "cpu",
    "timing_ms": 145.5
  },
  "timestamp": "2025-02-04T15:30:04Z"
}

{
  "type": "plugin_status",
  "payload": {
    "plugin": "player_detection",
    "status": "running",
    "frames_processed": 1
  },
  "timestamp": "2025-02-04T15:30:05Z"
}

=== HEARTBEAT ===
{
  "type": "ping",
  "payload": {
    "interval_seconds": 30
  },
  "timestamp": "2025-02-04T15:30:30Z"
}

{
  "type": "pong",
  "payload": {
    "timestamp": "2025-02-04T15:30:30.001Z"
  },
  "timestamp": "2025-02-04T15:30:30.001Z"
}

=== JOB COMPLETES ===
{
  "type": "progress",
  "payload": {
    "job_id": "job-abc123",
    "progress": 100,
    "stage": "Complete"
  },
  "timestamp": "2025-02-04T15:30:45Z"
}

{
  "type": "plugin_status",
  "payload": {
    "plugin": "player_detection",
    "status": "completed",
    "timing_ms": 12345.0,
    "frames_processed": 4
  },
  "timestamp": "2025-02-04T15:30:46Z"
}
```

---

# 9. Testing the Protocol

## 9.1 Mock Server for Frontend Testing

```typescript
// src/testing/mockRealtimeServer.ts
export function setupMockRealtimeServer() {
  const ws = new WebSocket('ws://localhost:8000/v1/realtime');
  // Emit test messages to client
}
```

## 9.2 Protocol Validation

```python
# server/tests/test_realtime_protocol.py
def test_frame_message_valid():
    message = {
        "type": "frame",
        "payload": { "frame_id": "f1", ... },
        "timestamp": "2025-02-04T15:30:00Z"
    }
    assert validate_message(message) is True
```

---

# End of Protocol

