# ForgeSyte WebSocket Protocol Specification

**Reverse-engineered from:** `server/app/main.py` and `web-ui/src/hooks/useWebSocket.ts`

**Status:** Implementation Complete (with bug fixes)

---

## Overview

The WebSocket protocol enables real-time streaming of video frames from the Web UI to the backend server for live analysis using vision plugins.

**Protocol:** WebSocket (`ws://` or `wss://`)  
**Endpoint:** `/v1/stream`  
**Backend Port:** 8000 (default)  
**Frontend Port:** 3000 (dev server)

---

## Connection Details

### Endpoint

```
ws://localhost:8000/v1/stream?plugin={plugin_name}&api_key={optional_key}
```

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `plugin` | string | Yes | `motion_detector` | Plugin name for analysis |
| `api_key` | string | No | None | Optional API authentication key |

### Connection Flow

1. **Client initiates connection** to `ws://localhost:8000/v1/stream?plugin=motion_detector`
2. **Server accepts connection** and generates unique `client_id`
3. **Server sends "connected" message** with client_id and plugin metadata
4. **Client receives "connected"** and sets `isConnected = true`
5. **Connection stays open** - client sends frames, server responds with results

### Connection Lifecycle

```
Client                                    Server
  |                                        |
  |-------- WebSocket Connect ------------>|
  |                                        |
  |<------- "connected" message -----------|  (payload: client_id, plugin)
  |                                        |
  |                                        | (awaiting messages)
  |-------- "frame" message ------------->|
  |                                        |
  |<------- "result" message --------------|  (payload: frame_id, plugin, result)
  |                                        |
  |-------- "switch_plugin" message ----->|
  |                                        |
  |<------- "plugin_switched" message ----|  (payload: plugin)
  |                                        |
  |-------- Close ----------------------->|
  |                                        |
```

---

## Message Protocol

All messages are JSON-encoded with the following structure:

### Generic Message Format

```typescript
{
    "type": string,
    "payload": object,
    "timestamp"?: string  // ISO 8601 format
}
```

---

## Message Types

### 1. Connected (Server → Client)

**Sent immediately after connection is accepted.**

```json
{
    "type": "connected",
    "payload": {
        "client_id": "550e8400-e29b-41d4-a716-446655440000",
        "plugin": "motion_detector"
    },
    "timestamp": "2026-01-12T18:20:04.509000+00:00"
}
```

**Payload Fields:**
- `client_id` (string): Unique identifier for this WebSocket connection
- `plugin` (string): Name of the currently active plugin

---

### 2. Frame (Client → Server)

**Sent to submit a video frame for analysis.**

```json
{
    "type": "frame",
    "frame_id": "frame-uuid-12345",
    "image_data": "base64_encoded_jpeg_or_png_data",
    "options": {
        "threshold": 0.5
    }
}
```

**Fields:**
- `type` (string): Always `"frame"`
- `frame_id` (string): Unique identifier for this frame (UUID)
- `image_data` (string): Base64-encoded image data (PNG, JPEG, etc.)
- `options` (object, optional): Plugin-specific analysis options

**Server Response:**
- Processes frame asynchronously
- Responds with `"result"` message when complete
- On error, responds with `"error"` message

---

### 3. Result (Server → Client)

**Sent when frame analysis is complete.**

```json
{
    "type": "result",
    "payload": {
        "frame_id": "frame-uuid-12345",
        "plugin": "motion_detector",
        "result": {
            "motion_detected": true,
            "motion_score": 0.87,
            "regions": [
                {"x": 100, "y": 150, "width": 200, "height": 200, "confidence": 0.92}
            ]
        },
        "processing_time_ms": 45.2
    },
    "timestamp": "2026-01-12T18:20:04.650000+00:00"
}
```

**Payload Fields:**
- `frame_id` (string): Matches the original frame request
- `plugin` (string): Which plugin processed this frame
- `result` (object): Plugin-specific analysis results
- `processing_time_ms` (number): Time taken to analyze frame (milliseconds)

---

### 4. Error (Server → Client)

**Sent when an error occurs.**

```json
{
    "type": "error",
    "payload": {
        "error": "Plugin 'invalid_plugin' not found",
        "frame_id": "frame-uuid-12345"
    },
    "timestamp": "2026-01-12T18:20:04.700000+00:00"
}
```

**Payload Fields:**
- `error` (string): Error message
- `frame_id` (string, optional): Frame ID if error is frame-specific, null otherwise

---

### 5. Switch Plugin (Client → Server)

**Request to switch analysis plugin mid-stream.**

```json
{
    "type": "switch_plugin",
    "plugin": "object_detection"
}
```

**Server Response:**
- If plugin exists: Sends `"plugin_switched"` message
- If plugin not found: Sends `"error"` message

---

### 6. Plugin Switched (Server → Client)

**Confirms plugin switch.**

```json
{
    "type": "plugin_switched",
    "payload": {
        "plugin": "object_detection"
    },
    "timestamp": "2026-01-12T18:20:04.750000+00:00"
}
```

---

### 7. Ping (Client → Server)

**Keep-alive ping to prevent connection timeout.**

```json
{
    "type": "ping"
}
```

**Server Response:** Sends `"pong"` message

---

### 8. Pong (Server → Client)

**Response to ping message.**

```json
{
    "type": "pong"
}
```

---

## Implementation Details

### Server (FastAPI)

**Location:** `server/app/main.py` (lines 216-317)

**Key Features:**
- Uses `@app.websocket("/v1/stream")` decorator
- Delegates to `VisionAnalysisService` for frame processing
- Thread-safe connection management via `ConnectionManager`
- Structured logging with `logging` module
- Graceful error handling and cleanup

**Dependencies:**
- `WebSocket` from FastAPI
- `ConnectionManager` from `websocket_manager.py`
- `VisionAnalysisService` from `services/vision_analysis.py`

### Client (React/TypeScript)

**Location:** `web-ui/src/hooks/useWebSocket.ts`

**Hook Interface:**
```typescript
useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn
```

**Options:**
```typescript
{
    url: string;              // Full WebSocket URL (e.g., "ws://localhost:8000/v1/stream")
    plugin?: string;          // Plugin name (default: "motion_detector")
    apiKey?: string;          // Optional API key
    onResult?: (result: FrameResult) => void;
    onError?: (error: string) => void;
    onConnect?: (clientId: string, metadata: object) => void;
    reconnectInterval?: number;        // Default: 3000ms
    maxReconnectAttempts?: number;     // Default: 5
}
```

**Return Value:**
```typescript
{
    isConnected: boolean;
    isConnecting: boolean;
    error: string | null;
    sendFrame: (imageData: string, frameId?: string, options?: object) => void;
    switchPlugin: (pluginName: string) => void;
    disconnect: () => void;
    reconnect: () => void;
    latestResult: FrameResult | null;
    stats: { framesProcessed: number; avgProcessingTime: number };
}
```

---

## Error Handling

### Connection Errors

If WebSocket fails to connect:
- Client attempts reconnection up to `maxReconnectAttempts` times
- Waits `reconnectInterval` ms between attempts (default: 3000ms)
- After max retries exhausted: Sets error message with URL and diagnostic info

**Error Message Format:**
```
Max reconnection attempts reached (5). Unable to connect to ws://localhost:8000/v1/stream. Ensure backend server is running on port 8000.
```

### Frame Processing Errors

If server encounters error during frame analysis:
- Sends `"error"` message with description
- Connection remains open
- Client can continue sending frames

### Connection Cleanup

- **Server:** Disconnects client, removes from subscriptions (in `websocket_manager.py`)
- **Client:** Stops reconnection attempts after max retries

---

## Configuration

### Environment Variables (Frontend)

```bash
# .env or passed at runtime
VITE_WS_BACKEND_URL=ws://localhost:8000    # WebSocket backend URL
VITE_API_URL=http://localhost:8000/v1     # REST API URL
VITE_API_KEY=optional_api_key              # Optional API authentication
```

### Environment Variables (Backend)

```bash
# .env or passed at runtime
FORGESYTE_PLUGINS_DIR=./example_plugins    # Directory containing plugins
```

---

## Testing

### Unit Tests
- **Location:** `server/tests/websocket/test_websocket_manager.py`
- **Coverage:** 97% (45 tests)
- **What's Tested:** Connection lifecycle, subscriptions, message sending, concurrency

### Integration Tests
- **Location:** `server/tests/websocket/test_websocket_integration.py`
- **Coverage:** 8 tests
- **What's Tested:** Actual endpoint connectivity, message protocol, error conditions

### E2E Tests
- **Location:** `./e2e.test.sh`
- **What's Tested:** 
  - REST API health check
  - WebSocket endpoint verification
  - Frontend integration with real backend

---

## Known Issues & Fixes

### Issue #17: "Max reconnection attempts reached"

**Root Cause:** `useWebSocket` effect dependency array included `connect` and `disconnect`, causing infinite reconnections.

**Fix:** Changed effect dependency to empty array `[]` so connection only established on mount.

**Commit:** (Fixed in this session)

---

## Future Enhancements

- [ ] Implement message batching for high-frequency frame streaming
- [ ] Add compression for large image data
- [ ] Implement automatic heartbeat/keep-alive mechanism
- [ ] Add frame queue management on client side
- [ ] Support for multiple simultaneous plugins
- [ ] Implement server-side frame rate limiting
- [ ] Add connection statistics/metrics endpoint

---

## References

- **FastAPI WebSocket Docs:** https://fastapi.tiangolo.com/advanced/testing-websockets/
- **WebSocket API (MDN):** https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
- **Related Files:**
  - `server/app/websocket_manager.py` - Connection management
  - `server/app/services/vision_analysis.py` - Frame processing logic
  - `web-ui/src/components/CameraPreview.tsx` - UI integration
