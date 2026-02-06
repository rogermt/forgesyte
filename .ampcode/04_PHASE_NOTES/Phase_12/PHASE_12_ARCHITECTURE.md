# Phase 12 — Architecture

Phase 12 introduces execution-path governance.  
This architecture document defines the structural boundaries, components, and
data flows required to enforce deterministic plugin execution.

---

# 1. Architectural Goals

1. Enforce a single execution path for all plugins.
2. Centralize execution logic inside ToolRunner.
3. Ensure deterministic lifecycle transitions.
4. Ensure structured error handling.
5. Ensure registry metrics update consistently.
6. Ensure input/output validation is mandatory.
7. Ensure observability across the entire execution pipeline.

---

# 2. Components Involved

## 2.1 AnalysisService
- Validates incoming requests.
- Rejects invalid input early.
- Delegates execution to JobManagementService.

## 2.2 JobManagementService
- Creates/updates job records.
- Delegates plugin execution to PluginManagementService.

## 2.3 PluginManagementService
- Selects plugin(s) for execution.
- MUST route execution through ToolRunner.
- No direct plugin.run() calls.

## 2.4 ToolRunner (Phase 12 Core)
- Validates input.
- Wraps plugin.run() in try/except.
- Measures execution time.
- Validates output.
- Produces structured success/error envelopes.
- Updates registry metrics.
- Updates lifecycle state.

## 2.5 Registry
- Stores plugin metadata and metrics.
- Updated after every execution.

---

# 3. Execution Path

```
+------------------+
|     Web‑UI       |
+---------+--------+
          |
          v
+------------------+
| AnalysisService  |
+---------+--------+
          |
          v
+------------------------+
| JobManagementService   |
+-----------+------------+
            |
            v
+----------------------------+
| PluginManagementService    |
+-------------+--------------+
              |
              v
+----------------------------+
|        ToolRunner          |
|  (single execution path)   |
+-------------+--------------+
              |
              v
+----------------------------+
|       plugin.run()         |
+-------------+--------------+
              |
              v
+----------------------------+
|      Registry.update()     |
+-------------+--------------+
              |
              v
+----------------------------+
|         Response           |
+----------------------------+
```

---

# 4. Phase 12 Architectural Invariants

- ToolRunner is the ONLY execution entry point.
- No direct plugin.run() calls exist.
- All errors are structured.
- Registry metrics MUST update after execution.
- Execution timing MUST be measured.
- Lifecycle transitions MUST follow the defined state machine.

---

# 5. Architectural Boundaries

- No business logic in AnalysisService.
- No execution logic in JobManagementService.
- No plugin invocation in PluginManagementService.
- All execution logic centralized in ToolRunner.
