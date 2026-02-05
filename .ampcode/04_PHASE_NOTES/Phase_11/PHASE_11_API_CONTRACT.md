# Phase 11 API Contract — `/v1/plugins`

**Canonical Shape After Phase 11**

## Endpoint

```
GET /v1/plugins
```

## Response (Phase 11 Authoritative)

Returns **list of dicts** (NOT wrapped in `{ plugins: [...] }`):

```json
[
  {
    "name": "ocr",
    "state": "INITIALIZED",
    "description": "OCR analysis plugin",
    "version": "1.0.0",
    "reason": null,
    "uptime_seconds": 123.45,
    "last_used": "2026-02-05T16:58:32.432Z",
    "success_count": 42,
    "error_count": 0,
    "last_execution_time_ms": 150.5,
    "avg_execution_time_ms": 145.2
  },
  {
    "name": "videotracker",
    "state": "UNAVAILABLE",
    "description": "Video tracking (GPU required)",
    "version": "2.0.0",
    "reason": "CUDA not found on this machine",
    "uptime_seconds": null,
    "last_used": null,
    "success_count": 0,
    "error_count": 1,
    "last_execution_time_ms": null,
    "avg_execution_time_ms": null
  }
]
```

## Contract Rules (Enforcement)

✅ **MUST:**
- Return HTTP 200 (even if plugins FAILED or UNAVAILABLE)
- Return list of dicts (not plugin objects)
- Include all fields above for every plugin
- Use ISO 8601 timestamps for dates
- Use snake_case field names
- Return stable JSON shape

❌ **MUST NOT:**
- Return `{ "plugins": [...] }` wrapper (Phase 11 flattened this)
- Return plugin objects with `.metadata()` methods
- Call `.metadata()` on anything
- Return HTTP 500 for any plugin state
- Return null values for required fields (use provided defaults)

## For Web-UI Consumers

Plugin list is **stable JSON**. Consume as:

```typescript
// ✅ Correct (Phase 11)
plugins.forEach(p => {
  console.log(p.name);        // "ocr"
  console.log(p.state);       // "INITIALIZED"
  console.log(p.description); // "OCR analysis plugin"
  console.log(p.reason);      // null or "error reason"
});

// ❌ Wrong (pre-Phase 11)
plugins.forEach(p => {
  p.metadata();               // Does not exist!
  p.id;                       // Wrong field
  p.get_status();             // Wrong method
});
```

## Tests That Lock This Contract

**File:** `server/tests/integration/test_phase11_api_contract.py`

Tests verify:
1. ✅ Returns HTTP 200
2. ✅ Returns list (not dict wrapper)
3. ✅ Each item is a dict (not object)
4. ✅ All required fields present
5. ✅ Field types match schema
6. ✅ No `.metadata()` anywhere
7. ✅ Works for FAILED/UNAVAILABLE plugins

Any regression fails immediately.

## Backward Compatibility

Pre-Phase 11 expected:
```json
{
  "plugins": [ { ... }, { ... } ],
  "count": 2
}
```

Phase 11 simplified to:
```json
[ { ... }, { ... } ]
```

**Web-UI MUST update** to consume flat list, not `response.json().plugins`.

