# Phase 12 — Execution Path Diagram

## ASCII Diagram (Authoritative)

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

## High-Level Execution Flow

Web‑UI  
→ AnalysisService  
→ JobManagementService  
→ PluginManagementService  
→ ToolRunner  
→ plugin.run()  
→ Registry.update()  
→ Response

## Phase 12 Invariants Represented

- ToolRunner is the ONLY execution entry point.
- No direct plugin.run() calls.
- All errors are structured.
- Registry metrics MUST update after execution.
- Execution timing MUST be measured.
