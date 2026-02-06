# Phase 12 Execution Flow Diagram

## High-Level Architecture

```
HTTP Client
    │
    ▼
POST /v1/analyze-execution (execution.py)
    │
    ▼
AnalysisExecutionService (analysis_execution_service.py)
    │
    ▼
JobExecutionService (job_execution_service.py)
    PENDING → RUNNING → SUCCESS/FAILED
    │
    ▼
PluginExecutionService (plugin_execution_service.py)
    │
    ▼
ToolRunner (tool_runner.py)
    ├─ validate_input() (execution_validation.py)
    ├─ plugin.run() [ONLY PLACE]
    ├─ validate_output() (execution_validation.py)
    ├─ error envelope (error_envelope.py)
    └─ finally: registry.update_execution_metrics()
    │
    ▼
PluginRegistry (plugin_registry.py)
    success_count, error_count, execution times, lifecycle state
```

## File-to-Component Mapping

| Component | File | Responsibility |
|-----------|------|----------------|
| API Route | `server/app/api/routes/execution.py` | HTTP handling |
| Analysis Service | `server/app/services/execution/analysis_execution_service.py` | Orchestration |
| Job Service | `server/app/services/execution/job_execution_service.py` | Job lifecycle |
| Plugin Service | `server/app/services/execution/plugin_execution_service.py` | ToolRunner wrapper |
| ToolRunner | `server/app/plugins/runtime/tool_runner.py` | Execution, validation, metrics |
| Validation | `server/app/core/validation/execution_validation.py` | Input/output validation |
| Error Envelope | `server/app/core/errors/error_envelope.py` | Structured errors |
| Registry | `server/app/plugins/loader/plugin_registry.py` | Metrics & state |

## Plugin Lifecycle States

```
LOADED ───► INITIALIZED (success) ───► RUNNING ───► FAILED ───► UNAVAILABLE
              │                         │
              │                         │
              └─────────────────────────┘
```

## Job Lifecycle

```
create_job() ──► PENDING ──► run_job() ──► RUNNING
                                           │       │
                              success ◄─────┘       └─────► failure
                                           │                   │
                                           ▼                   ▼
                                        SUCCESS              FAILED
```

## Validation Flow

```
Input Payload
    │
    ▼
validate_input()
    │
    ├─ Invalid ──► InputValidationError ──► error_envelope.py
    │
    └─ Valid ──► plugin.run()
                    │
                    ▼
            validate_output()
                    │
                    ├─ Invalid ──► OutputValidationError ──► error_envelope.py
                    │
                    └─ Valid ──► Result
```

## Error Envelope Structure

```python
{
  "error": {
    "type": "ValidationError | PluginError | ExecutionError",
    "message": "<human-readable>",
    "details": {},
    "plugin": "<plugin_name>|null",
    "timestamp": "<UTC ISO8601>"
  },
  "_internal": {
    "traceback": "<stringified traceback>"
  }
}
```

## Test Files

```
server/tests/execution/
  test_toolrunner_lifecycle_states.py   # INITIALIZED/FAILED states
  test_toolrunner_validation.py         # input/output validation
  test_registry_metrics.py              # metrics update
  test_plugin_execution_service.py      # ToolRunner delegation
  test_job_execution_service.py        # job lifecycle
  test_api_execution_route.py          # /v1/analyze-execution
  test_no_direct_plugin_run.py          # scanner test
```

## Scanner

```
scripts/scan_execution_violations.py
```

## CI Pipeline

```
.github/workflows/execution-ci.yml
  1. Run scanner
  2. Run Phase 11 tests
  3. Run execution tests
```

## Invariants

1. **Single Execution Path:** All plugin execution → ToolRunner.run()
2. **No Direct plugin.run():** Forbidden outside tool_runner.py
3. **Lifecycle States:** Only LOADED, INITIALIZED, RUNNING, FAILED, UNAVAILABLE
4. **Error Handling:** All exceptions → structured error envelope
5. **Metrics:** Every execution → registry.update_execution_metrics()
