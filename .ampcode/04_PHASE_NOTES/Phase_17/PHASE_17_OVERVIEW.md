# Phase 17: Real-Time Streaming Inference - Overview

## Purpose

Phase 17 introduces a real-time streaming layer on top of the stable Phase 15/16 batch + async foundations.

## Core Change

- **From**: Jobs (long-running, persistent, asynchronous)
- **To**: Sessions (ephemeral, real-time, stateful per connection)

## Key Deliverables

- WebSocket endpoint: `/ws/video/stream`
- Session manager (one per connection)
- Real-time inference loop (frame → pipeline → result)
- Backpressure (drop frames / slow-down signals)
- Ephemeral results (no persistence, no job table)

## Non-Goals (Explicitly Out of Scope)

- Recording or storing streams
- Historical queries
- Multi-client fan-out
- GPU scheduling
- Distributed workers
- Multi-pipeline DAGs
- Authentication or rate limiting
- Any `/v1/*` endpoint additions (Phase 18 migration)

## Architecture

### Components

1. **WebSocket Endpoint**
   - Path: `/ws/video/stream`
   - Protocol: WebSocket (bidirectional)
   - Accepts: Binary JPEG frames
   - Sends: JSON inference results
   - Persistence: None (ephemeral)

2. **Session Manager**
   - File: `server/app/services/streaming/session_manager.py`
   - Lifecycle: Created on connect, destroyed on disconnect
   - State: In-memory only (no database)
   - Fields:
     - `session_id` (UUID)
     - `frame_index` (int)
     - `dropped_frames` (int)
     - `last_processed_ts` (float)
     - `backpressure_state` (enum)

3. **Frame Validator**
   - File: `server/app/services/streaming/frame_validator.py`
   - Purpose: Ensure incoming frames are valid JPEG
   - Checks:
     - JPEG SOI marker (`0xFF 0xD8`)
     - JPEG EOI marker (`0xFF 0xD9`)
     - Size limit (< 5MB)
   - Response: Raises structured exceptions on failure

4. **Real-Time Inference Loop**
   - Process per frame:
     1. Validate frame
     2. Increment frame_index
     3. Apply backpressure logic
     4. Run Phase 15 pipeline
     5. Send result or drop notification
   - No persistence
   - No queueing

5. **Backpressure Mechanism**
   - File: `server/app/services/streaming/backpressure.py`
   - Strategy: Drop frames (no queueing)
   - Trigger: Processing time > frame interval OR dropped_frames > threshold
   - Signals:
     - Drop: `{ "frame_index": N, "dropped": true }`
     - Slow-down: `{ "warning": "slow_down" }` (when drop rate > 30%)

6. **No Database Writes**
   - No DuckDB writes
   - No Alembic migrations
   - No job table updates
   - Fully ephemeral

## Data Flow

```
Client → WebSocket → Session Manager → Frame Validator → Pipeline → WebSocket → Client
```

## Relationship to Phase 16

- **Phase 16**: Asynchronous jobs, persistent state, worker queue
- **Phase 17**: Real-time sessions, ephemeral state, no queue
- **Coexistence**: They operate independently without interference

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STREAM_DROP_THRESHOLD` | `0.10` | Drop frames when drop rate exceeds 10% |
| `STREAM_SLOWDOWN_THRESHOLD` | `0.30` | Send slow-down warning when drop rate exceeds 30% |
| `STREAM_MAX_FRAME_SIZE_MB` | `5` | Maximum frame size in megabytes |
| `STREAM_MAX_SESSIONS` | `10` | Recommended maximum concurrent sessions (not enforced) |

## Progress

**Backend**: 12/12 commits completed (100%)
**Frontend**: 0/8 commits completed (0%)
**Total**: 12/20 commits completed (60%)

## Next Steps

After Phase 17 backend completion:
1. Begin Phase 17 frontend implementation (FE-1 through FE-8)
2. Implement WebSocket client integration
3. Add camera capture and streaming
4. Create real-time overlay rendering
5. Add pipeline selection UI
6. Implement error handling UI
7. Add debug/metrics panel
8. Ensure MP4 upload fallback still works