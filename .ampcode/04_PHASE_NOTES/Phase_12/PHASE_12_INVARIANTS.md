# Phase 12 — Execution Invariants

## Execution Path
- All plugin execution MUST go through ToolRunner.
- No direct calls to plugin.run() are permitted.
- Execution time MUST be measured.
- Exceptions MUST be converted to structured errors.
- No traceback may leak to the client.

## Registry Updates
- success_count increments on success.
- error_count increments on failure.
- last_execution_time_ms updated.
- avg_execution_time_ms updated.
- last_used timestamp updated.

## Input Validation
- Image bytes MUST be non-empty.
- MIME type MUST be valid.
- Payload MUST decode correctly.

## Output Validation
- Plugin output MUST be a dict or structured object.
- Plugin MUST NOT return None.
- Empty dict only allowed if explicitly intended.

## Observability
- Execution logs MUST be emitted.
- Error logs MUST be emitted.
- Timing logs MUST be emitted.

## Lifecycle
- RUNNING → SUCCESS
- RUNNING → ERROR → FAILED
- RUNNING → ERROR → UNAVAILABLE
