# Phase 12 — ToolRunner Lifecycle

## ASCII State Machine

```
          +-------+
          | IDLE  |
          +---+---+
              |
              | ToolRunner.run()
              v
        +-----+------+
        |  RUNNING   |
        +--+-----+---+
           |     |
     valid |     | error or invalid output
           |     |
           v     v
   +-------+--+  +--------+
   | SUCCESS  |  | ERROR  |
   +-----+----+  +---+----+
         |           |
         |           |
         v           v
     +---+---+   +---+------------------+
     | IDLE  |   | FAILED / UNAVAILABLE |
     +-------+   +----------+-----------+
                            |
                            v
                          +---+
                          |IDLE|
                          +---+
```

## States

- **IDLE** — Not executing.
- **RUNNING** — Executing plugin.run().
- **SUCCESS** — Valid output.
- **ERROR** — Exception or invalid output.
- **FAILED** — Persistent error.
- **UNAVAILABLE** — Temporary/environmental error.

## Phase 12 Invariants

- All execution MUST pass through RUNNING.
- SUCCESS, FAILED, UNAVAILABLE are terminal outcomes.
- Registry MUST update based on final state.
- No raw exceptions may escape ToolRunner.
