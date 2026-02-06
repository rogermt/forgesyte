# Phase 12 — Developer Contract

This contract defines the non-negotiable rules developers MUST follow during
Phase 12. These rules ensure deterministic, observable, and safe plugin
execution.

---

## 1. Execution Path Rules

1. All plugin execution MUST go through ToolRunner.
2. No direct calls to plugin.run() are permitted anywhere in the codebase.
3. Execution MUST be wrapped in a try/except block inside ToolRunner.
4. Execution MUST measure timing for every plugin invocation.
5. Execution MUST produce structured success or structured error envelopes.

---

## 2. Input Validation Rules

1. Image bytes MUST be non-empty.
2. MIME type MUST be validated.
3. Payload MUST decode correctly.
4. Invalid input MUST produce a structured error envelope.

---

## 3. Output Validation Rules

1. Plugin output MUST be a dict or structured object.
2. Plugin output MUST NOT be None.
3. Empty dict is only allowed if explicitly intended by plugin design.
4. Invalid output MUST be treated as an execution error.

---

## 4. Registry Update Rules

1. success_count MUST increment on success.
2. error_count MUST increment on failure.
3. last_execution_time_ms MUST update.
4. avg_execution_time_ms MUST update.
5. last_used MUST update.
6. lifecycle state MUST reflect SUCCESS, FAILED, or UNAVAILABLE.

---

## 5. Observability Rules

1. Execution logs MUST be emitted.
2. Error logs MUST be emitted.
3. Timing logs MUST be emitted.
4. No raw tracebacks may appear in logs or API responses.

---

## 6. Lifecycle Rules

1. RUNNING MUST be entered before plugin.run().
2. SUCCESS MUST be entered on valid output.
3. ERROR MUST be entered on exception or invalid output.
4. FAILED or UNAVAILABLE MUST be assigned based on error classification.

---

## 7. Forbidden Actions

1. Direct plugin.run() calls.
2. Returning raw exceptions or tracebacks.
3. Skipping registry updates.
4. Returning unvalidated plugin output.
5. Bypassing ToolRunner for any reason.

---

## 8. Compliance

All PRs MUST use the Phase 12 PR template and MUST satisfy all invariants before
merge. No exceptions.
