# Phase 17: Session Model Documentation

## Overview

The Session Manager manages per-connection state for real-time video streaming. Each WebSocket connection gets its own SessionManager instance that tracks frames, drops, and backpressure state.

## Session Lifecycle

```
┌─────────────┐
│  Connect    │ → Create SessionManager
└─────────────┘
       ↓
┌─────────────┐
│  Stream     │ → Process frames, track metrics
└─────────────┘
       ↓
┌─────────────┐
│  Disconnect │ → Destroy SessionManager
└─────────────┘
```

## SessionManager Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | UUID | Unique identifier for this session |
| `pipeline_id` | str | Pipeline being used for inference |
| `frame_index` | int | Number of frames processed (starts at 0) |
| `dropped_frames` | int | Number of frames dropped due to backpressure |
| `last_processed_ts` | float | Timestamp of last processed frame (seconds since epoch) |
| `backpressure_state` | enum | Current backpressure state (normal, warning, critical) |
| `drop_threshold` | float | Drop rate threshold (default 0.10) |
| `slowdown_threshold` | float | Slow-down warning threshold (default 0.30) |

## SessionManager Methods

### `increment_frame()`

Increments the frame counter.

```python
session.increment_frame()  # frame_index += 1
```

### `mark_drop()`

Increments the dropped frames counter.

```python
session.mark_drop()  # dropped_frames += 1
```

### `drop_rate()`

Calculates the current drop rate.

```python
rate = session.drop_rate()  # dropped_frames / frame_index
```

### `should_drop_frame(processing_time_ms)`

Determines if a frame should be dropped based on processing time and drop rate.

```python
if session.should_drop_frame(processing_time_ms=50.0):
    # Drop this frame
    pass
```

### `should_slow_down()`

Determines if a slow-down warning should be sent based on drop rate.

```python
if session.should_slow_down():
    # Send slow-down warning
    pass
```

### `now_ms()` (static)

Returns current time in milliseconds.

```python
current_time_ms = SessionManager.now_ms()
```

## Session State

### Normal State

- Drop rate < 10%
- All frames processed
- No warnings sent

### Warning State

- Drop rate > 10% but < 30%
- Some frames dropped
- No slow-down warning yet

### Critical State

- Drop rate > 30%
- Many frames dropped
- Slow-down warning sent

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STREAM_DROP_THRESHOLD` | `0.10` | Drop frames when drop rate exceeds 10% |
| `STREAM_SLOWDOWN_THRESHOLD` | `0.30` | Send slow-down warning when drop rate exceeds 30% |

## Example Usage

```python
from app.services.streaming.session_manager import SessionManager

# Create session
session = SessionManager(pipeline_id="yolo_ocr")

# Process frames
while True:
    frame_bytes = get_frame()
    
    # Increment counter
    session.increment_frame()
    
    # Check if should drop
    processing_time_ms = measure_processing_time(frame_bytes)
    if session.should_drop_frame(processing_time_ms):
        session.mark_drop()
        continue
    
    # Process frame
    result = process_frame(frame_bytes)
    
    # Check if should warn
    if session.should_slow_down():
        send_warning()
    
    # Send result
    send_result(result)
```

## Session Isolation

Each WebSocket connection gets its own SessionManager instance:

- No shared state between connections
- No database persistence
- No cross-session interference
- Fully ephemeral

## Session Destruction

When a WebSocket connection closes:

1. SessionManager is removed from `websocket.state.session`
2. All session data is lost
3. No cleanup required beyond removing the reference

## Testing

See `server/tests/streaming/test_session_manager.py` for comprehensive tests:
- Session creation and initialization
- Frame increment and drop tracking
- Drop rate calculation
- Backpressure decision logic
- Environment variable configuration