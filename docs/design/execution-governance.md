# Execution Governance Architecture

This document defines the execution governance system for the repository.
It is the **single source of truth** for how plugins are executed, validated, monitored, and exposed via API.

---

## 1. Overview

The execution layer provides a **safe, deterministic, and governed** pipeline for running plugins.
It ensures:

- A single execution path (ToolRunner)
- Strict lifecycle state management
- Input/output validation
- Structured error envelopes
- Job lifecycle tracking
- Mechanical enforcement via scanner + CI

Execution governance prevents ambiguity, drift, and silent failures.

---

## 2. Execution Architecture

```
API → AnalysisExecutionService → JobExecutionService → PluginExecutionService → ToolRunner → Plugin
```

Each layer has a single responsibility:

| Component | Responsibility |
|-----------|----------------|
| **API** | Request/response, auth, error mapping |
| **AnalysisExecutionService** | Sync + async orchestration |
| **JobExecutionService** | Job lifecycle + storage |
| **PluginExecutionService** | Delegation to ToolRunner |
| **ToolRunner** | Validation, execution, metrics, error envelope |
| **Plugin** | Business logic |

---

## 3. Plugin Lifecycle States

Plugins use the **Phase 11 lifecycle states**, unchanged:

```
LOADED
INITIALIZED   ← success
RUNNING
FAILED        ← failure
UNAVAILABLE
```

### Rules:
- ToolRunner sets `INITIALIZED` on success.
- ToolRunner sets `FAILED` on error.
- No other states are permitted.
- `SUCCESS` and `ERROR` are **metrics**, not lifecycle states.

---

## 4. Job Lifecycle

Jobs represent execution requests.

```
PENDING → RUNNING → SUCCESS / FAILED
```

### Rules:
- Jobs are created by `create_job()`
- Jobs are executed by `run_job()`
- Jobs store:
  - plugin
  - payload
  - status
  - result or error
  - timestamps

---

## 5. Validation Rules

### Input Validation
- `image` must be present and non-empty
- `mime_type` must be present and non-empty

### Output Validation
- Plugin output must be a dict
- Invalid output triggers a validation error envelope

---

## 6. Error Envelope

All exceptions are wrapped in a structured envelope:

```json
{
  "error": {
    "type": "ValidationError | PluginError | ExecutionError",
    "message": "Human-readable message",
    "details": {},
    "plugin": "plugin_name",
    "timestamp": "UTC ISO8601"
  },
  "_internal": {
    "traceback": "stringified traceback"
  }
}
```

API exposes only the `error` section.

---

## 7. Mechanical Scanner Rules

The scanner enforces:

1. **No direct `plugin.run()`** outside ToolRunner
2. ToolRunner.run() must contain:
   - a `finally` block
   - a call to `update_execution_metrics()` inside that finally
3. Only valid lifecycle states may be used
4. No SUCCESS/ERROR lifecycle states
5. No bypass of validation or error envelope

Scanner failures block CI.

---

## 8. CI Enforcement

CI runs:

1. Mechanical scanner
2. Phase 11 tests
3. Execution tests

Any failure blocks merge.

---

## 9. Developer Responsibilities

### When adding a plugin:
- Register it in the registry
- Ensure it returns a dict
- Do not call plugin.run() directly

### When adding execution features:
- Use existing services
- Never bypass ToolRunner
- Update tests accordingly

### When debugging:
- Check job state
- Check registry metrics
- Check error envelope
- Run scanner

---

## 10. File Locations

```
server/app/services/execution/
server/app/plugins/runtime/tool_runner.py
server/app/api/routes/analysis_execution.py
server/tests/execution/
scripts/scan_execution_violations.py
.github/workflows/execution-ci.yml
docs/execution-governance.md
```

---

This document governs the execution subsystem and must remain authoritative.
