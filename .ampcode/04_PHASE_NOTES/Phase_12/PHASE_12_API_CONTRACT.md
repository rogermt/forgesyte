# Phase 12 — API Contract

Phase 12 does NOT introduce new API endpoints.  
Instead, it strengthens the guarantees of existing endpoints by enforcing
execution-path governance and structured error envelopes.

---

# 1. Affected Endpoints

## POST /v1/analyze
Execution behavior changes, but the API surface does not.

### Request
- image: bytes (required)
- options: dict (optional)

### Phase 12 Requirements
- Input MUST be validated.
- Invalid input MUST produce a structured error envelope.

### Response (Success)
```json
{
  "result": { "...": "plugin output" },
  "execution_time_ms": 125,
  "plugin": "ocr"
}
```

### Response (Error)
```json
{
  "error": {
    "type": "ValidationError",
    "message": "human readable message",
    "details": { "field": "reason" },
    "plugin": "ocr",
    "timestamp": "2026-02-06T02:35:00Z"
  }
}
```

---

# 2. Error Envelope Contract

All errors MUST follow this structure:

```json
{
  "error": {
    "type": "ValidationError | ExecutionError | PluginError | InternalError",
    "message": "string",
    "details": { "...": "..." },
    "plugin": "string | null",
    "timestamp": "ISO8601"
  }
}
```

- No raw tracebacks.
- No unstructured strings.
- No HTTP 500 with stack traces.

---

# 3. Execution Metadata Contract

ToolRunner MUST attach execution metadata:

```json
{
  "execution_time_ms": 125,
  "plugin": "ocr"
}
```

---

# 4. Backward Compatibility

- No Phase 11 API fields are removed.
- No Phase 11 behavior is broken.
- All Phase 11 clients remain compatible.

---

# 5. Phase 12 API Invariants

- Structured errors only.
- Validated input only.
- Validated output only.
- Registry metrics MUST update after execution.
- Execution timing MUST be included.
