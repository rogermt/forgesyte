# Phase 12 — Plugin Execution Flow

## ASCII Flow Diagram

```
+----------------------+
|   Input Validation   |
+----------+-----------+
           |
           v
+----------------------+
|   ToolRunner.run()   |
+----------+-----------+
           |
           v
+----------------------+
|  try/except wrapper  |
+----------+-----------+
           |
           v
+----------------------+
|  plugin.run() call   |
+----------+-----------+
           |
     +-----+------+
     |            |
     v            v
+---------+   +-----------+
| SUCCESS |   |  ERROR    |
+----+----+   +-----+-----+
     |              |
     v              v
+------------------------+
|   Registry.update()    |
+-----------+------------+
            |
            v
+------------------------+
|   Structured Response  |
+------------------------+
```

## Step-by-Step Flow

1. Validate input.
2. Invoke ToolRunner.run().
3. Wrap plugin.run() in try/except.
4. Measure execution time.
5. Validate output.
6. Update registry metrics.
7. Return structured success or structured error.

## Phase 12 Invariants

- Input MUST be validated before execution.
- Output MUST be validated before returning.
- Registry MUST update after every execution.
- All errors MUST be structured.
- ToolRunner is the ONLY legal execution entry point.
