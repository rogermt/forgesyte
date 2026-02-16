# Phase 17: WebSocket Streaming Endpoint Documentation

## WebSocket Endpoint: `/ws/video/stream`

### Connection

```
ws://<host>/ws/video/stream?pipeline_id=<pipeline_id>
```

**Query Parameters:**
- `pipeline_id` (required): ID of the pipeline to use for inference (e.g., `yolo_ocr`)
- Validated via `VideoFilePipelineService.is_valid_pipeline()`
- Connection rejected if invalid or missing

### Incoming Messages

- **Type**: Binary
- **Format**: JPEG bytes
- **Constraints**:
  - Max size: 5MB
  - Must contain SOI (`0xFF 0xD8`) and EOI (`0xFF 0xD9`)
  - Recommended resolution: 640×480
  - Recommended quality: 0.7-0.8

### Outgoing Messages

#### Success Response
```json
{
  "frame_index": 42,
  "result": { ... pipeline output ... }
}
```

#### Dropped Frame
```json
{
  "frame_index": 42,
  "dropped": true
}
```

#### Slow-Down Warning
```json
{
  "warning": "slow_down"
}
```

#### Error Response
```json
{
  "error": "invalid_frame",
  "detail": "Not a valid JPEG image"
}
```

or

```json
{
  "error": "frame_too_large",
  "detail": "Frame exceeds 5MB"
}
```

or

```json
{
  "error": "invalid_pipeline",
  "detail": "Unknown pipeline_id: yolo_foo"
}
```

or

```json
{
  "error": "invalid_message",
  "detail": "Expected binary frame payload"
}
```

or

```json
{
  "error": "pipeline_failure",
  "detail": "YOLO inference failed"
}
```

or

```json
{
  "error": "internal_error",
  "detail": "Unexpected error occurred"
}
```

### Close Conditions

- Client disconnects
- Server detects invalid frame
- Server detects frame too large
- Server detects pipeline failure
- Server detects overload (optional)

### Session Lifecycle

```
connect → stream frames → receive results → disconnect → session destroyed
```

### Error Codes

| Code | Description |
|------|-------------|
| `invalid_message` | Expected binary frame payload, received text message |
| `invalid_frame` | Not a valid JPEG image |
| `frame_too_large` | Frame exceeds 5MB limit |
| `invalid_pipeline` | Unknown pipeline_id |
| `pipeline_failure` | Pipeline execution failed |
| `internal_error` | Unexpected error occurred |

### Example Usage

```python
import asyncio
import websockets

async def stream_video():
    uri = "ws://localhost:8000/ws/video/stream?pipeline_id=yolo_ocr"
    
    async with websockets.connect(uri) as websocket:
        # Read JPEG frame from file
        with open("frame.jpg", "rb") as f:
            frame_bytes = f.read()
        
        # Send frame
        await websocket.send(frame_bytes)
        
        # Receive result
        result = await websocket.recv()
        print(f"Result: {result}")
```

### Testing

See `server/tests/streaming/` for comprehensive test coverage:
- `test_connect.py` - Connection tests
- `test_session_manager.py` - Session management tests
- `test_frame_validator.py` - Frame validation tests
- `test_receive_frames.py` - Frame reception tests
- `test_pipeline_integration.py` - Pipeline integration tests
- `test_backpressure_drop.py` - Backpressure drop tests
- `test_backpressure_slowdown.py` - Backpressure slow-down tests
- `test_error_handling.py` - Error handling tests
- `test_logging_and_metrics.py` - Logging and metrics tests