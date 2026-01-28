# **ForgeSyte WebSocket Protocol Specification (Updated for BasePlugin + Tools)**  
**Last Updated:** 2026‑01‑28  
**Status:** Fully aligned with new plugin architecture  
**Version:** 2.0.0  

---

# 🧭 Overview

The WebSocket protocol enables **real‑time frame streaming** from the Web‑UI to the backend for live tool execution.

This is used for:

- YOLO player detection  
- YOLO ball detection  
- Motion detection  
- Future real‑time plugins  

The WebSocket layer is now **tool‑based**, not `analyze()`‑based.

---

# 🔌 Endpoint

```
ws://localhost:8000/v1/stream?plugin=<plugin>&tool=<tool>&api_key=<optional>
```

### Query Parameters

| Parameter | Required | Description |
|----------|----------|-------------|
| `plugin` | Yes | Plugin name (e.g., `yolo-tracker`) |
| `tool` | Yes | Tool name (e.g., `player_detection`) |
| `api_key` | No | Optional API key |

### Why plugin + tool?

Because all real‑time analysis is now routed through:

```
plugin.run_tool(tool_name, args)
```

This matches the REST endpoint:

```
POST /v1/plugins/<plugin>/tools/<tool>/run
```

---

# 🔄 Connection Lifecycle

```
Client                                      Server
  |                                           |
  |------ WebSocket Connect ----------------->|
  |                                           |
  |<----- connected (plugin, tool) -----------|
  |                                           |
  |------ frame (frame_id, image, args) ----->|
  |                                           |
  |<----- result (frame_id, result) ----------|
  |                                           |
  |------ switch (plugin, tool) ------------->|
  |                                           |
  |<----- switched (plugin, tool) ------------|
  |                                           |
  |------ close ----------------------------->|
```

---

# 📡 Message Protocol

All messages are JSON.

## Generic Format

```json
{
  "type": "string",
  "payload": {},
  "timestamp": "ISO-8601"
}
```

---

# 📥 Client → Server Messages

## 1. `frame`

Send a frame for analysis.

```json
{
  "type": "frame",
  "frame_id": "uuid",
  "image_base64": "<base64>",
  "args": {
    "threshold": 0.5
  }
}
```

### Notes

- `args` must match the tool’s `input_schema`
- Server calls:

```
plugin.run_tool(tool, args)
```

---

## 2. `switch`

Switch plugin or tool mid‑stream.

```json
{
  "type": "switch",
  "plugin": "yolo-tracker",
  "tool": "ball_detection"
}
```

Server validates:

- plugin exists  
- tool exists  
- tool has valid schema  

---

## 3. `ping`

Keep‑alive.

```json
{
  "type": "ping"
}
```

---

# 📤 Server → Client Messages

## 1. `connected`

Sent immediately after connection.

```json
{
  "type": "connected",
  "payload": {
    "client_id": "uuid",
    "plugin": "yolo-tracker",
    "tool": "player_detection",
    "tool_schema": {
      "input_schema": {...},
      "output_schema": {...}
    }
  }
}
```

---

## 2. `result`

Sent when a frame has been processed.

```json
{
  "type": "result",
  "payload": {
    "frame_id": "uuid",
    "plugin": "yolo-tracker",
    "tool": "player_detection",
    "result": {
      "detections": [...]
    },
    "processing_time_ms": 42.1
  }
}
```

---

## 3. `error`

```json
{
  "type": "error",
  "payload": {
    "error": "Tool 'xyz' not found",
    "frame_id": "uuid"
  }
}
```

---

## 4. `switched`

```json
{
  "type": "switched",
  "payload": {
    "plugin": "yolo-tracker",
    "tool": "ball_detection",
    "tool_schema": {...}
  }
}
```

---

## 5. `pong`

```json
{
  "type": "pong"
}
```

---

# 🧠 Server Behavior (Updated)

### Server now:

- Validates plugin exists  
- Validates tool exists  
- Validates input schema  
- Calls `plugin.run_tool(tool, args)`  
- Returns JSON result  
- Never returns raw 500s  
- Always wraps errors in JSON  

### Server files involved:

- `websocket_manager.py`  
- `services/vision_analysis.py`  
- `plugin_loader.py`  
- `BasePlugin` contract  

---

# 🧩 Client Behavior (Updated)

The Web‑UI uses:

- `useWebSocket()`  
- `runTool()`  
- `uiPluginManager`  
- Dynamic plugin + tool selection  

### Web‑UI responsibilities:

- Send frames  
- Handle results  
- Handle errors  
- Switch tools  
- Render results generically  

---

# 🧪 Testing

### Unit tests

- Connection lifecycle  
- Plugin/tool switching  
- Error handling  
- Frame routing  

### Integration tests

- Real plugin execution  
- Real tool invocation  
- Schema validation  

---

# 🚀 Future Enhancements

- Frame batching  
- Compression  
- Adaptive frame rate  
- Multi‑plugin multiplexing  
- Server‑side throttling  

---

# 🎯 Summary

This updated WebSocket protocol:

- Matches the BasePlugin + tools architecture  
- Matches the REST `/run` endpoint  
- Supports dynamic plugin + tool switching  
- Powers real‑time YOLO + OCR + future plugins  
- Eliminates all hardcoded plugin assumptions  
- Keeps UI fully plugin‑agnostic  

