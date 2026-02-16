# Phase 17: Backpressure Design Documentation

## Overview

Backpressure prevents system overload by dropping frames when processing lags. Phase 17 uses a "drop frames" strategy with no queueing.

## Design Philosophy

**No Queueing Policy**

Phase 17 does NOT queue frames. Queueing breaks real-time guarantees. If frames arrive faster than processing, they are dropped.

## Drop-Frame Algorithm

```python
def should_drop_frame(session: SessionManager) -> bool:
    # Condition 1: Processing too slow
    if session.processing_time > frame_interval:
        return True
    
    # Condition 2: Drop rate too high
    total_frames = session.frame_index + session.dropped_frames
    if total_frames > 0:
        drop_rate = session.dropped_frames / total_frames
        if drop_rate > 0.10:  # 10% threshold
            return True
    
    return False
```

## Slow-Down Signal

```python
def should_send_slow_down(session: SessionManager) -> bool:
    total_frames = session.frame_index + session.dropped_frames
    if total_frames > 0:
        drop_rate = session.dropped_frames / total_frames
        if drop_rate > 0.30:  # 30% threshold
            return session.slow_down_sent == False
    
    return False
```

## Backpressure States

| State | Drop Rate | Action |
|-------|-----------|--------|
| Normal | < 10% | Process all frames |
| Warning | 10-30% | Drop frames, no warning |
| Critical | > 30% | Drop frames, send slow-down warning |

## Backpressure Signals

### Drop Signal

Sent when a frame is dropped:

```json
{
  "frame_index": 42,
  "dropped": true
}
```

### Slow-Down Signal

Sent when drop rate exceeds 30% (once per session):

```json
{
  "warning": "slow_down"
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STREAM_DROP_THRESHOLD` | `0.10` | Drop frames when drop rate exceeds 10% |
| `STREAM_SLOWDOWN_THRESHOLD` | `0.30` | Send slow-down warning when drop rate exceeds 30% |
| `STREAM_MAX_FRAME_SIZE_MB` | `5` | Maximum frame size in megabytes |
| `STREAM_MAX_SESSIONS` | `10` | Recommended maximum concurrent sessions (not enforced) |

## Client-Side Response

### Receiving Drop Signal

```python
result = await websocket.recv()
if "dropped" in result and result["dropped"]:
    # Frame was dropped, skip overlay update
    continue
```

### Receiving Slow-Down Signal

```python
result = await websocket.recv()
if "warning" in result and result["warning"] == "slow_down":
    # Reduce frame rate
    reduce_fps()
```

## Trade-offs

### Advantages of Drop Strategy

- **Real-time guarantees**: No lag from queueing
- **Memory efficient**: No buffer accumulation
- **Simple implementation**: No complex queue management

### Disadvantages of Drop Strategy

- **Lost frames**: Some frames are never processed
- **Quality degradation**: Higher drop rates reduce quality
- **Client adaptation required**: Client must handle drop signals

### Why Not Queue?

Queueing breaks real-time guarantees:

- **Lag**: Queue introduces delay between capture and processing
- **Memory**: Queue can grow unbounded
- **Stale data**: Old frames become less valuable over time
- **Complexity**: Queue management adds complexity

## Performance Targets

| Stage | Target |
|-------|--------|
| Frame validation | < 2 ms |
| Pipeline inference | < 30 ms |
| WebSocket send | < 5 ms |
| Total per frame | < 37 ms |

At 30 FPS, each frame has ~33 ms available. The total target is within budget.

## Tuning Thresholds

### Drop Threshold

- **Lower (0.05)**: More aggressive dropping, better quality, higher risk
- **Higher (0.20)**: Less aggressive dropping, lower quality, lower risk

### Slow-Down Threshold

- **Lower (0.20)**: Earlier warnings, more client adaptation
- **Higher (0.40)**: Later warnings, less client adaptation

## Testing

See `server/tests/streaming/test_backpressure_drop.py` and `server/tests/streaming/test_backpressure_slowdown.py` for comprehensive tests:
- Drop decision logic
- Slow-down signal logic
- Environment variable configuration
- Integration with WebSocket endpoint