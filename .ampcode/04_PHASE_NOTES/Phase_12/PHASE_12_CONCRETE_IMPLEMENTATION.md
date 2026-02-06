# Phase 12 — Concrete Implementation Plan

This document defines the concrete, step-by-step implementation tasks required
to satisfy Phase 12 invariants.

---

# 1. ToolRunner Implementation

## 1.1 Add Execution Wrapper
- Wrap plugin.run() in try/except.
- Start timing before invocation.
- Stop timing after invocation.
- Convert exceptions into structured error envelopes.

## 1.2 Add Input Validation
- Reject empty image bytes.
- Reject invalid MIME types.
- Reject undecodable payloads.

## 1.3 Add Output Validation
- Ensure plugin output is a dict or structured object.
- Reject None.
- Reject invalid schema.

---

# 2. Registry Integration

## 2.1 Add Metric Updates
- success_count++
- error_count++
- last_execution_time_ms
- avg_execution_time_ms
- last_used timestamp

## 2.2 Add Lifecycle Updates
- SUCCESS on valid output.
- ERROR on exception or invalid output.
- FAILED or UNAVAILABLE based on classification.

---

# 3. PluginManagementService Integration

## 3.1 Enforce ToolRunner Usage
- Replace any direct plugin.run() calls.
- Ensure all execution flows through ToolRunner.run().

---

# 4. JobManagementService Integration

## 4.1 Execution Path Enforcement
- Ensure job execution delegates to PluginManagementService.
- Ensure no job-level execution bypasses ToolRunner.

---

# 5. Error Envelope Implementation

## 5.1 Structured Error Format
- type
- message
- details
- plugin_name
- timestamp

## 5.2 Replace Raw Exceptions
- No tracebacks.
- No unstructured error strings.

---

# 6. Logging Implementation

## 6.1 Execution Logs
- plugin name
- execution time
- success/failure

## 6.2 Error Logs
- structured error envelope

## 6.3 Timing Logs
- execution duration in ms

---

# 7. Test Implementation

## 7.1 RED Tests (Provided)
- Execution path fails initially
- ToolRunner not invoked
- Direct plugin.run() detection
- Registry metrics missing
- Unstructured errors
- Invalid plugin output
- Input validation missing

## 7.2 GREEN Tests
- Implement features until all RED tests pass.

---

# 8. Documentation Updates

- Update execution-path diagram.
- Update ToolRunner lifecycle.
- Update plugin execution flow.
