### PHASE 10 TOOLRUNNER EXECUTION MODEL  
**File:** `PHASE_10_TOOLRUNNER_EXECUTION_MODEL.md`

```md
# Phase 10 — ToolRunner Execution Model

This document defines how ToolRunner executes plugins in real time, measures
timings, and integrates with the realtime channel.

---

# 1. Responsibilities

ToolRunner is responsible for:
- Executing plugins for a given job
- Measuring execution time
- Capturing warnings
- Emitting RealtimeMessage objects
- Remaining non-blocking for the realtime channel

---

# 2. Execution Flow

For each plugin:

1. Fetch plugin configuration + metadata.
2. Start timing (monotonic clock).
3. Execute plugin:
   - `result = plugin.run(job_context)`
4. Stop timing.
5. Forward:
   - result
   - timing
   - warnings (if any)
   to InspectorService + Realtime pipeline.

---

# 3. Concurrency Model

Phase 10 default (authoritative):

- Plugins MAY be executed sequentially or concurrently.
- ToolRunner MUST NOT block the realtime channel:
  - Use background tasks / async execution where available.
- Ordering of plugin messages is best-effort, not guaranteed.

---

# 4. Integration Points

## 4.1 InspectorService

After each plugin run:

- `inspector.record_timing(plugin_name, timing_ms)`
- `inspector.record_warnings(plugin_name, warnings)`

## 4.2 RealtimeMessage Emission

ToolRunner MUST emit:

- `partial_result` (optional, plugin-specific)
- `plugin_status` (timing + status)
- `warning` (for each warning)

---

# 5. Error Handling

If plugin raises an exception:

- Capture exception
- Emit `error` RealtimeMessage with details
- Optionally mark plugin as failed in InspectorService
- MUST NOT crash the server process

---

# 6. Completion Criteria

ToolRunner is complete when:
- Plugins execute correctly
- Timings are measured and emitted
- Warnings are captured and emitted
- Errors do not crash the system
- No Phase 9 invariants are broken
```

---

### PHASE 10 REALTIME ERROR HANDLING SPEC  
**File:** `PHASE_10_REALTIME_ERROR_HANDLING_SPEC.md`

```md
# Phase 10 — Realtime Error Handling Spec

This document defines how errors are handled and propagated in the realtime
channel.

---

# 1. Error Sources

Errors may originate from:
- Plugin execution
- Network issues
- Serialization issues
- Internal server failures

---

# 2. Error Message Schema

Realtime `error` message:

```json
{
  "type": "error",
  "payload": {
    "error": "string",
    "details": {
      "plugin": "optional string",
      "job_id": "optional string",
      "trace_id": "optional string"
    }
  },
  "timestamp": "ISO8601"
}
```

---

# 3. Plugin Errors

If a plugin raises an exception:

- ToolRunner catches it.
- InspectorService may record it.
- Server emits `error` message with:
  - `plugin` name
  - high-level error message
- Job MAY continue or terminate, depending on severity (implementation choice).

---

# 4. Network / Connection Errors

If WebSocket/SSE connection fails:

- Server:
  - Logs error
  - Cleans up connection
- Client:
  - Transitions to DISCONNECTED → RECONNECTING
  - Uses backoff strategy

No `error` message is required for network-level disconnects.

---

# 5. Serialization Errors

If a message cannot be serialized:

- Server MUST NOT crash.
- Message is dropped.
- Optional: log error with trace_id.

---

# 6. UI Behavior (Contract-Level)

On receiving `error` message:

- UI MUST:
  - Show an error banner or equivalent
  - NOT crash
  - Allow user to restart job or reconnect

---

# 7. Completion Criteria

Realtime error handling is complete when:
- Plugin errors are surfaced via `error` messages
- Network errors trigger reconnection, not crashes
- Serialization errors are non-fatal
- UI responds gracefully to `error` messages
```

---

### PHASE 10 PLUGIN METADATA SCHEMA  
**File:** `PHASE_10_PLUGIN_METADATA_SCHEMA.md`

```md
# Phase 10 — Plugin Metadata Schema

This document defines the metadata structure for plugins used by the
InspectorService and realtime UI.

---

# 1. PluginMetadata (Backend)

Python shape:

```py
class PluginMetadata(BaseModel):
    name: str
    version: Optional[str]
    description: Optional[str]
    author: Optional[str]
    tags: Optional[List[str]]
    enabled: bool = True
```

---

# 2. Metadata Storage

InspectorService MUST maintain:

```py
plugins: Dict[str, PluginMetadata]
```

Keyed by `name`.

---

# 3. Metadata Exposure

InspectorService MUST expose:

- `get_metadata() -> Dict[str, PluginMetadata]`

This may be used by:
- Realtime endpoint (optional)
- Future `/v1/plugins` endpoint (optional)
- PluginInspector UI (via separate API or embedded in messages)

---

# 4. Optional Realtime Metadata Message

Phase 10 MAY (optional) emit:

```json
{
  "type": "plugin_metadata",
  "payload": {
    "plugins": [
      {
        "name": "ocr",
        "version": "1.0.0",
        "description": "Optical character recognition",
        "tags": ["vision", "text"],
        "enabled": true
      }
    ]
  },
  "timestamp": "ISO8601"
}
```

This is NOT required by the Developer Contract, but allowed.

---

# 5. Frontend Shape

TypeScript shape:

```ts
type PluginMetadata = {
  name: string;
  version?: string;
  description?: string;
  author?: string;
  tags?: string[];
  enabled: boolean;
};
```

---

# 6. Invariants

- Metadata is additive; it MUST NOT affect Phase 9 behavior.
- Missing metadata MUST NOT break execution.
- Plugin names MUST be stable identifiers across messages.

---

# 7. Completion Criteria

Plugin metadata is complete when:
- Metadata is stored per plugin
- Metadata can be retrieved
- Optional realtime metadata messages can be emitted
- No Phase 9 invariants are broken
```

---

