# Phase 10 API Spec

Complete API specification for Phase 10.

All changes are additive and MUST NOT break Phase 9 invariants.

---

# 1. Endpoints

## 1.1 WebSocket /v1/realtime

**Purpose:**
Real-time channel for frames, progress, plugin timings, warnings.

**Protocol:**
- WebSocket (preferred)
- Server-Sent Events (SSE) as fallback

**Connection:**
```
WS ws://localhost:8000/v1/realtime?session_id=<uuid>
```

**Handshake:**
```
Client connects
   ↓
Server accepts connection
   ↓
Server sends initial metadata messages
   ↓
Connection ready to receive messages
```

**Behavior:**
- Accept WebSocket connection
- Stream RealtimeMessage objects (JSON)
- Maintain heartbeat (ping/pong every 30 seconds)
- Close gracefully on disconnect or server shutdown

**Example Connection (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8000/v1/realtime');

ws.onopen = () => {
  console.log('Connected to real-time endpoint');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from real-time endpoint');
};
```

**Status Codes:**
- `1000`: Normal close
- `1006`: Abnormal close (network error, server crash)
- `4000`: Custom: Invalid session ID
- `4001`: Custom: Server capacity exceeded

---

## 1.2 GET /v1/jobs/{job_id}/extended

**Purpose:**
Get extended job response with Phase 10 fields (progress, timings, warnings).

**Path Parameters:**
- `job_id` (string, required): Job identifier

**Response:**
```json
{
  "job_id": "job-abc123",
  "device_requested": "gpu",
  "device_used": "cuda:0",
  "fallback": false,
  "frames": [ /* Phase 9 frames */ ],
  "progress": 75,
  "plugin_timings": {
    "player_detection": 145.5,
    "ball_detection": 98.2,
    "pitch_detection": 156.3
  },
  "warnings": [
    "Pitch detection: Corners not found",
    "Team classification: Low confidence"
  ]
}
```

**Response Code:**
- `200 OK`: Job found
- `404 Not Found`: Job not found
- `500 Internal Server Error`: Server error

**Note:**
- All Phase 10 fields are optional
- Endpoint MUST NOT break if new fields are unavailable
- Phase 9 fields MUST always be present

---

## 1.3 POST /v1/jobs (Existing, Unchanged)

**Phase 10 Change:**
- No changes to request/response format
- Job execution now emits real-time messages on `/v1/realtime`
- Existing `/v1/jobs` endpoint continues to work unchanged

---

## 1.4 GET /v1/jobs/{job_id} (Existing, Unchanged)

**Phase 10 Change:**
- No changes
- Returns standard JobResponse (Phase 9)
- Extended fields available via `/v1/jobs/{job_id}/extended` (new)

---

# 2. Models

## 2.1 ExtendedJobResponse

**Inherits from Phase 9 JobResponse:**

```python
from typing import Optional, Dict, List
from app.models import JobResponse


class ExtendedJobResponse(JobResponse):
    """Extended job response with Phase 10 fields."""
    
    # All Phase 9 fields are inherited and unchanged:
    # - job_id: str
    # - device_requested: str
    # - device_used: str
    # - fallback: bool
    # - frames: List[FrameData]
    
    # New Phase 10 fields (all optional):
    progress: Optional[int] = None  # 0-100
    plugin_timings: Optional[Dict[str, float]] = None  # ms per plugin
    warnings: Optional[List[str]] = None  # Warning messages
```

**JSON Schema:**
```json
{
  "type": "object",
  "properties": {
    "job_id": { "type": "string" },
    "device_requested": { "type": "string" },
    "device_used": { "type": "string" },
    "fallback": { "type": "boolean" },
    "frames": { "type": "array", "items": { "type": "object" } },
    "progress": { "type": "integer", "minimum": 0, "maximum": 100 },
    "plugin_timings": { "type": "object", "additionalProperties": { "type": "number" } },
    "warnings": { "type": "array", "items": { "type": "string" } }
  },
  "required": ["job_id", "device_requested", "device_used", "fallback", "frames"]
}
```

**Invariants:**
- All Phase 9 fields MUST be present
- New fields MAY be absent (optional)
- If new fields present, they MUST be valid (progress 0-100, timings are numbers)

---

## 2.2 RealtimeMessage

**Base schema for all real-time messages:**

```python
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel


class RealtimeMessage(BaseModel):
    """Base real-time message."""
    
    type: str  # message type identifier
    payload: Dict[str, Any]  # type-specific data
    timestamp: datetime  # ISO 8601 UTC
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

**JSON Example:**
```json
{
  "type": "progress",
  "payload": {
    "job_id": "job-abc123",
    "progress": 50,
    "stage": "Processing frame 3 of 6"
  },
  "timestamp": "2025-02-04T15:30:00.123Z"
}
```

---

# 3. Message Payloads

All message types conform to RealtimeMessage base schema.

## 3.1 frame

**Type:** `"frame"`

**Purpose:** Annotated frame from plugin

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
    ]
  },
  "device_used": "cuda:0",
  "timing_ms": 145.5
}
```

**Fields:**
- `frame_id` (string): Unique frame identifier
- `plugin` (string): Source plugin name
- `data` (object): Plugin-specific frame data
- `device_used` (string): Device used ('cpu', 'cuda:0', etc.)
- `timing_ms` (number): Processing time in milliseconds

---

## 3.2 partial_result

**Type:** `"partial_result"`

**Purpose:** Intermediate result from plugin

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
- `result` (object): Plugin-specific result data
- `plugin` (string): Source plugin name
- `partial` (boolean): Always `true` for partial_result

---

## 3.3 progress

**Type:** `"progress"`

**Purpose:** Job progress update

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
- `job_id` (string): Job identifier
- `progress` (integer): 0-100
- `stage` (string, optional): Human-readable stage
- `plugin` (string, optional): Current plugin name

**Constraints:**
- `progress` MUST be in range [0, 100]

---

## 3.4 plugin_status

**Type:** `"plugin_status"`

**Purpose:** Plugin execution status and timing

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
- `timing_ms` (number): Total execution time
- `frames_processed` (integer, optional): Frames processed
- `warnings_count` (integer, optional): Number of warnings

---

## 3.5 warning

**Type:** `"warning"`

**Purpose:** Non-fatal plugin warning

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
- `plugin` (string): Source plugin
- `message` (string): Warning text
- `severity` (string): One of: `low`, `medium`, `high`
- `frame_id` (string, optional): Associated frame

---

## 3.6 error

**Type:** `"error"`

**Purpose:** Fatal error (job may still be recoverable)

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
- `plugin` (string, optional): Source plugin
- `details` (object, optional): Error details
  - `error_code` (string): Machine-readable code
  - `message` (string): Detailed message
  - `fallback` (string, optional): Recovery action
- `frame_id` (string, optional): Associated frame

---

## 3.7 ping

**Type:** `"ping"`

**Purpose:** Heartbeat from server

**Payload:**
```json
{
  "interval_seconds": 30
}
```

**Fields:**
- `interval_seconds` (integer, optional): Server ping interval

---

## 3.8 pong

**Type:** `"pong"`

**Purpose:** Heartbeat response from client

**Payload:**
```json
{
  "timestamp": "2025-02-04T15:30:00.123Z"
}
```

**Fields:**
- `timestamp` (string): Client timestamp (for latency measurement)

---

## 3.9 metadata

**Type:** `"metadata"`

**Purpose:** Plugin metadata (sent once on connection)

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
  - `input_shape` (array): Input dimensions
  - `output_format` (string): Output format type
  - `confidence_default` (number): Default confidence
  - `capabilities` (array): Plugin capabilities

---

# 4. Error Handling

## 4.1 API Errors

**Format:**
```json
{
  "detail": "Job not found",
  "status_code": 404
}
```

**Common Status Codes:**
- `400 Bad Request`: Invalid request
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## 4.2 WebSocket Errors

**Format:**
Message of type `"error"` sent to client:
```json
{
  "type": "error",
  "payload": {
    "error": "Connection lost",
    "details": { "reason": "Server shutdown" }
  },
  "timestamp": "2025-02-04T15:30:00Z"
}
```

---

# 5. Backward Compatibility

## 5.1 Phase 9 Endpoints Unchanged

```
POST /v1/jobs → JobResponse (unchanged)
GET  /v1/jobs/{job_id} → JobResponse (unchanged)
GET  /v1/devices → DeviceResponse (unchanged)
```

## 5.2 Phase 10 Additions

```
WS /v1/realtime → RealtimeMessage (NEW)
GET /v1/jobs/{job_id}/extended → ExtendedJobResponse (NEW)
```

## 5.3 Guarantees

- No Phase 9 fields removed
- No Phase 9 endpoints modified
- No Phase 9 response formats changed
- Phase 10 fields are optional
- Clients unaware of Phase 10 continue to work

---

# 6. Rate Limiting & Quotas

## 6.1 REST Endpoints

- Standard rate limits apply (same as Phase 9)

## 6.2 WebSocket Connections

- Max concurrent connections per session: 5
- Message queue per connection: 1000 messages
- Connection timeout: 60 seconds without heartbeat response

---

# 7. Security

## 7.1 Authentication

- WebSocket inherits Phase 9 authentication
- All endpoints require valid session

## 7.2 Data Validation

- All incoming messages validated against schema
- Malformed messages rejected with error

---

# 8. Versioning

- API version: `/v1/` (same as Phase 9)
- No breaking changes within v1
- New functionality added as new endpoints or optional fields

