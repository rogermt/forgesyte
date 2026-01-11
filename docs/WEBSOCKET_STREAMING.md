# WebSocket & Streaming Protocol Guide

ForgeSyte provides real-time streaming capabilities via WebSocket for processing multiple frames or images continuously. This guide documents the WebSocket message protocol and streaming patterns.

---

## Overview

The WebSocket system enables:
- **Real-time streaming**: Send frames continuously, receive results as they complete
- **Multiple plugins**: Run different plugins on the same frame
- **Subscriptions**: Subscribe to job updates for specific topics
- **Error handling**: Graceful error reporting with recovery

---

## Connection Flow

```
Client                           Server
  |                                |
  |-- WebSocket Connect ----------->|
  |                                |
  |<-- Connection Accepted ---------|
  |                                |
  |-- Subscribe (topic) ----------->|
  |                                |
  |-- Send Frame ------------------>|
  |                                |
  |<-- Frame Result (streaming)------|
  |                                |
  |-- Send Another Frame ---------->|
  |                                |
  |<-- Frame Result (streaming)------|
  |                                |
  |-- Unsubscribe ----------------->|
  |                                |
  |-- Close Connection ------------>|
```

---

## Message Types

All WebSocket messages are JSON objects with a `type` field.

### 1. Client Messages

#### Subscribe Message

Subscribe to updates for a job or topic.

```json
{
  "type": "subscribe",
  "topic": "job_123"
}
```

**Topic formats**:
- `job_<job_id>`: Subscribe to specific job updates
- `plugin_<plugin_name>`: Subscribe to all jobs using this plugin
- `all`: Subscribe to all events (broadcast)

#### Unsubscribe Message

Unsubscribe from updates.

```json
{
  "type": "unsubscribe",
  "topic": "job_123"
}
```

#### Send Frame Message

Send a frame for analysis.

```json
{
  "type": "send_frame",
  "frame_id": "frame_001",
  "image_data": "base64_encoded_image_bytes",
  "plugin": "ocr",
  "options": {
    "threshold": 0.8
  }
}
```

**Fields**:
- `frame_id` (string): Unique identifier for this frame (generated or provided by client)
- `image_data` (string): Base64-encoded image bytes
- `plugin` (string): Name of plugin to use
- `options` (object, optional): Plugin-specific options

### 2. Server Messages (Streaming Results)

#### Frame Result Message

Sent when a frame analysis completes successfully.

```json
{
  "type": "frame_result",
  "frame_id": "frame_001",
  "job_id": "job_123",
  "plugin": "ocr",
  "status": "success",
  "result": {
    "text": "Extracted text...",
    "confidence": 0.95
  },
  "processing_time_ms": 245,
  "timestamp": "2026-01-11T17:30:45.123456Z"
}
```

**Fields**:
- `frame_id`: Echo of client's frame_id
- `job_id`: Job created for this frame
- `plugin`: Which plugin processed it
- `status`: "success" or "error"
- `result`: Plugin's analysis result (varies by plugin)
- `processing_time_ms`: Wall-clock milliseconds spent processing
- `timestamp`: ISO 8601 timestamp of completion

#### Error Message

Sent when an error occurs.

```json
{
  "type": "error",
  "frame_id": "frame_001",
  "plugin": "ocr",
  "error_code": "INVALID_IMAGE",
  "message": "Image too small (50 bytes)",
  "timestamp": "2026-01-11T17:30:45.123456Z"
}
```

**Error codes**:
- `INVALID_IMAGE`: Image format not supported or corrupted
- `PLUGIN_NOT_FOUND`: Plugin doesn't exist
- `PLUGIN_ERROR`: Plugin raised an exception
- `PROCESSING_TIMEOUT`: Analysis took too long
- `INVALID_OPTIONS`: Plugin options validation failed

#### Job Update Message

Sent when a job status changes.

```json
{
  "type": "job_update",
  "job_id": "job_123",
  "status": "completed",
  "frame_id": "frame_001",
  "plugin": "ocr",
  "progress_percent": 100,
  "timestamp": "2026-01-11T17:30:45.123456Z"
}
```

**Status values**:
- `pending`: Job queued, waiting to start
- `processing`: Job currently executing
- `completed`: Job finished successfully
- `failed`: Job failed with error

---

## Streaming Protocol Details

### Connection Handshake

1. Client initiates WebSocket connection to `/ws/<client_id>`
2. Server accepts connection
3. Server sends connection acknowledgment (implicit in accept)
4. Client can now send/receive messages

### Async Frame Processing

Frames are processed **asynchronously**:

```
Frame sent at T0
  ↓
Queued at T0 + 10ms
  ↓
Processing begins at T0 + 50ms
  ↓
Result received at T0 + 300ms  (processing_time_ms ≈ 250)
```

Client should not wait for response before sending next frame.

### Subscription Model

Clients can subscribe to **topics** to filter messages:

```javascript
// Subscribe to all results for this job
ws.send(JSON.stringify({
  type: "subscribe",
  topic: "job_123"
}));

// Now will receive all frame_result and error messages for job_123
```

Multiple subscriptions per client are supported:

```javascript
// Subscribe to multiple jobs
ws.send(JSON.stringify({ type: "subscribe", topic: "job_123" }));
ws.send(JSON.stringify({ type: "subscribe", topic: "job_456" }));
```

### Broadcasting

Servers can broadcast to multiple clients:

- Broadcast to all connected clients
- Broadcast to subscribers of a topic
- Broadcast to individual clients (personal message)

---

## Client Implementation Examples

### JavaScript/Node.js Client

```javascript
class ForgeSyteClient {
  constructor(baseUrl = "ws://localhost:8000") {
    this.baseUrl = baseUrl;
    this.clientId = `client_${Date.now()}`;
    this.ws = null;
    this.handlers = {
      frame_result: [],
      error: [],
      job_update: []
    };
  }

  // Connect to WebSocket
  connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(`${this.baseUrl}/ws/${this.clientId}`);
      
      this.ws.onopen = () => {
        console.log("Connected to ForgeSyte");
        resolve();
      };
      
      this.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      };
      
      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        reject(error);
      };
    });
  }

  // Subscribe to topic
  subscribe(topic) {
    this.ws.send(JSON.stringify({
      type: "subscribe",
      topic: topic
    }));
  }

  // Send frame for analysis
  async sendFrame(imageData, plugin, options = {}) {
    const frameId = `frame_${Date.now()}`;
    
    // Convert image to base64
    const base64 = imageData instanceof Uint8Array 
      ? btoa(String.fromCharCode(...imageData))
      : imageData;
    
    this.ws.send(JSON.stringify({
      type: "send_frame",
      frame_id: frameId,
      image_data: base64,
      plugin: plugin,
      options: options
    }));
    
    return frameId;
  }

  // Handle incoming messages
  handleMessage(message) {
    if (message.type === "frame_result") {
      this.handlers.frame_result.forEach(handler => handler(message));
    } else if (message.type === "error") {
      this.handlers.error.forEach(handler => handler(message));
    } else if (message.type === "job_update") {
      this.handlers.job_update.forEach(handler => handler(message));
    }
  }

  // Register handlers
  onFrameResult(handler) {
    this.handlers.frame_result.push(handler);
  }

  onError(handler) {
    this.handlers.error.push(handler);
  }

  onJobUpdate(handler) {
    this.handlers.job_update.push(handler);
  }

  // Close connection
  close() {
    this.ws.close();
  }
}

// Usage
const client = new ForgeSyteClient("ws://localhost:8000");

await client.connect();
client.subscribe("job_123");

client.onFrameResult((result) => {
  console.log(`Frame ${result.frame_id} processed in ${result.processing_time_ms}ms`);
  console.log(`Result:`, result.result);
});

client.onError((error) => {
  console.error(`Error on frame ${error.frame_id}: ${error.message}`);
});

// Send frames
const imageBytes = new Uint8Array([/* ... */]);
await client.sendFrame(imageBytes, "ocr", { threshold: 0.8 });
```

### Python Client

```python
import asyncio
import json
import base64
import websockets
from typing import Callable, Dict, Any

class ForgeSyteClient:
    def __init__(self, base_url: str = "ws://localhost:8000"):
        self.base_url = base_url
        self.client_id = f"client_{int(time.time())}"
        self.ws = None
        self.handlers = {
            "frame_result": [],
            "error": [],
            "job_update": []
        }

    async def connect(self):
        """Connect to WebSocket server."""
        self.ws = await websockets.connect(
            f"{self.base_url}/ws/{self.client_id}"
        )
        print(f"Connected to ForgeSyte")
        
        # Start listening for messages
        asyncio.create_task(self._listen())

    async def _listen(self):
        """Listen for incoming messages."""
        try:
            async for message in self.ws:
                data = json.loads(message)
                await self._handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")

    async def _handle_message(self, message: Dict[str, Any]):
        """Handle incoming message."""
        msg_type = message.get("type")
        if msg_type == "frame_result":
            for handler in self.handlers["frame_result"]:
                await handler(message)
        elif msg_type == "error":
            for handler in self.handlers["error"]:
                await handler(message)
        elif msg_type == "job_update":
            for handler in self.handlers["job_update"]:
                await handler(message)

    async def subscribe(self, topic: str):
        """Subscribe to a topic."""
        await self.ws.send(json.dumps({
            "type": "subscribe",
            "topic": topic
        }))

    async def send_frame(
        self, 
        image_bytes: bytes, 
        plugin: str, 
        options: Dict[str, Any] = None
    ) -> str:
        """Send a frame for analysis."""
        frame_id = f"frame_{int(time.time())}"
        image_base64 = base64.b64encode(image_bytes).decode()
        
        await self.ws.send(json.dumps({
            "type": "send_frame",
            "frame_id": frame_id,
            "image_data": image_base64,
            "plugin": plugin,
            "options": options or {}
        }))
        
        return frame_id

    def on_frame_result(self, handler: Callable):
        """Register frame result handler."""
        self.handlers["frame_result"].append(handler)

    def on_error(self, handler: Callable):
        """Register error handler."""
        self.handlers["error"].append(handler)

    def on_job_update(self, handler: Callable):
        """Register job update handler."""
        self.handlers["job_update"].append(handler)

    async def close(self):
        """Close WebSocket connection."""
        await self.ws.close()

# Usage
async def main():
    client = ForgeSyteClient("ws://localhost:8000")
    await client.connect()
    await client.subscribe("job_123")
    
    async def handle_result(message):
        frame_id = message["frame_id"]
        processing_time = message["processing_time_ms"]
        result = message["result"]
        print(f"Frame {frame_id}: {processing_time}ms")
        print(f"Result: {result}")
    
    client.on_frame_result(handle_result)
    
    # Send frames
    with open("image.png", "rb") as f:
        image_bytes = f.read()
    
    await client.send_frame(image_bytes, "ocr", {"threshold": 0.8})
    
    # Wait for results
    await asyncio.sleep(10)
    
    await client.close()

asyncio.run(main())
```

---

## Performance Characteristics

### Latency

Typical latencies for frame processing:

| Operation | Latency |
|-----------|---------|
| WebSocket send | < 1ms |
| Queue to process start | 10-50ms |
| Plugin analysis (OCR) | 100-500ms |
| Plugin analysis (ML) | 200-2000ms |
| Send result back | < 1ms |
| **Total (OCR)** | **100-550ms** |

### Throughput

Frame processing throughput:

- **OCR plugin**: ~2-5 frames/sec (200-500ms each)
- **Motion detector**: ~10-20 frames/sec (50-100ms each)
- **Simple plugins**: ~20-50 frames/sec (20-50ms each)

To achieve higher throughput, send frames without waiting for results:

```javascript
// DON'T do this (waits for each result):
for (const frame of frames) {
  await sendFrame(frame);
  const result = await waitForResult();
}

// DO this (send all frames, collect results asynchronously):
for (const frame of frames) {
  sendFrame(frame);
}
// Results arrive asynchronously via onFrameResult handlers
```

---

## Error Handling & Recovery

### Transient Connection Errors

Implement reconnect with exponential backoff:

```javascript
async function connectWithRetry(maxRetries = 5) {
  let retries = 0;
  
  while (retries < maxRetries) {
    try {
      await client.connect();
      return;
    } catch (error) {
      retries++;
      const backoff = Math.min(1000 * Math.pow(2, retries), 30000);
      console.log(`Retry ${retries}/${maxRetries} in ${backoff}ms`);
      await new Promise(resolve => setTimeout(resolve, backoff));
    }
  }
  
  throw new Error("Failed to connect after max retries");
}
```

### Frame Processing Errors

Handle errors gracefully and retry if needed:

```javascript
client.onError((error) => {
  console.error(`Frame ${error.frame_id} failed: ${error.message}`);
  
  if (error.error_code === "INVALID_IMAGE") {
    // Image was bad, don't retry
    console.log("Skipping invalid image");
  } else if (error.error_code === "PLUGIN_ERROR") {
    // Plugin failed, could retry with different options
    console.log("Retrying with different options");
  }
});
```

### Connection Recovery

Detect and recover from stale connections:

```javascript
// Periodically verify connection is alive
setInterval(() => {
  if (client.ws.readyState !== WebSocket.OPEN) {
    console.log("Connection lost, reconnecting...");
    connectWithRetry();
  }
}, 5000);
```

---

## Best Practices

### 1. Frame Ordering

Frames are processed in the order sent, but results may arrive out of order. Use `frame_id` to correlate:

```javascript
const frameMap = {};

client.onFrameResult((result) => {
  frameMap[result.frame_id] = result;
  // Process in application order, not arrival order
});
```

### 2. Subscription Management

Subscribe once, not per-message:

```javascript
// GOOD
client.subscribe("job_123");
sendFrame(...);
sendFrame(...);

// BAD - resubscribe on each frame
sendFrame(...);
client.subscribe("job_123");
sendFrame(...);
client.subscribe("job_123");
```

### 3. Buffer Incoming Results

Don't process results synchronously. Use queues:

```javascript
const resultQueue = [];

client.onFrameResult((result) => {
  resultQueue.push(result);
});

// Process results separately
setInterval(() => {
  while (resultQueue.length > 0) {
    const result = resultQueue.shift();
    processResult(result);
  }
}, 100);
```

### 4. Resource Cleanup

Always close connections properly:

```javascript
// On page unload
window.addEventListener("beforeunload", async () => {
  if (client.ws) {
    await client.close();
  }
});
```

---

## Streaming Use Cases

### Video Stream Processing

Process video frames in real-time:

```javascript
const video = document.getElementById("video");
const canvas = document.createElement("canvas");
const ctx = canvas.getContext("2d");

// Capture frames at 5 FPS
setInterval(() => {
  ctx.drawImage(video, 0, 0);
  const imageData = canvas.toDataURL("image/jpeg", 0.8);
  const bytes = new Uint8Array(atob(imageData.split(",")[1]).split("").map(c => c.charCodeAt(0)));
  
  client.sendFrame(bytes, "motion_detector");
}, 200); // 5 FPS
```

### Batch Image Processing

Process many images concurrently:

```javascript
async function processBatch(imageFiles) {
  const results = {};
  
  // Send all frames
  for (const file of imageFiles) {
    const bytes = await file.arrayBuffer();
    const frameId = await client.sendFrame(bytes, "ocr");
    results[frameId] = { file: file.name, status: "pending" };
  }
  
  // Collect results
  client.onFrameResult((result) => {
    results[result.frame_id].status = "done";
    results[result.frame_id].result = result.result;
  });
  
  // Wait for all
  while (Object.values(results).some(r => r.status === "pending")) {
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  return results;
}
```

---

## Troubleshooting

### Connection Refused

**Error**: `WebSocket connection failed`
- Check server is running: `uv run fastapi dev app/main.py`
- Check correct URL: `ws://localhost:8000/ws/<client_id>`
- Check firewall allows WebSocket connections

### Message Not Received

**Problem**: Sent frame but no result received
- Check subscription: did you `subscribe` to the topic?
- Check plugin exists: `GET /v1/plugins`
- Check image valid: try with known good image
- Check logs: `tail -f server.log`

### Connection Drops

**Problem**: WebSocket connection closes unexpectedly
- Server may have restarted
- Network timeout (some proxies timeout idle connections)
- Implement reconnect logic with exponential backoff
- Send periodic ping/pong to keep connection alive

---

## See Also

- [ARCHITECTURE.md](./ARCHITECTURE.md) - System design
- [README.md](../README.md) - Project overview
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
