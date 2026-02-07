# Execution Layer — Developer Quickstart

This guide gives developers the minimum they need to work safely and confidently inside the execution subsystem.

---

## 1. Core Mental Model

All plugin execution must follow this exact path:

```
API → AnalysisExecutionService → JobExecutionService → PluginExecutionService → ToolRunner → Plugin
```

**Never call `plugin.run()` directly.**
**Always go through ToolRunner.**

---

## 2. Running Tests

From the repo root:

### Run all tests
```bash
pytest server/tests -v
```

### Run execution governance tests
```bash
pytest server/tests/execution -v
```

All execution changes must keep both suites green.

---

## 3. Running the Mechanical Scanner

The scanner enforces execution invariants:

```bash
python scripts/scan_execution_violations.py
```

- If it prints **Execution scanner OK**, you're good.
- If it prints violations, fix them before committing.

CI will run this automatically on every PR and push to `main`.

---

## 4. Where Things Live

| Area | Path |
|------|------|
| Execution services | `server/app/services/execution/` |
| ToolRunner | `server/app/plugins/runtime/tool_runner.py` |
| Execution API | `server/app/api_routes/routes/execution.py` |
| Execution tests | `server/tests/execution/` |
| Scanner | `scripts/scan_execution_violations.py` |
| CI workflow | `.github/workflows/execution-ci.yml` |
| Governance docs | `docs/design/execution-governance.md` |

---

## 5. Adding or Modifying a Plugin

1. Implement `.run(payload: dict) -> dict`
2. Register the plugin in the registry
3. Do **not** call `plugin.run()` directly
4. Let ToolRunner handle:
   - validation
   - metrics
   - lifecycle state updates
   - error envelopes

If you need new behavior, add it to services or ToolRunner, not around them.

---

## 6. Adding or Modifying Execution Behavior

Typical changes:

- New API endpoint
- New job type
- New orchestration logic

**Rules:**

- Use `AnalysisExecutionService` for API-facing orchestration
- Use `JobExecutionService` for job lifecycle
- Use `PluginExecutionService` to reach ToolRunner
- Never bypass ToolRunner
- Add/update tests in `server/tests/execution/`
- Run scanner + tests before committing

---

## 7. Debugging Execution Issues

When something breaks:

### Check job state
Use job endpoints to inspect:
- PENDING
- RUNNING
- SUCCESS
- FAILED

### Check error envelope
API returns structured errors:
- type
- message
- plugin
- details

### Check registry metrics
- success_count
- error_count
- last_execution_time_ms
- state

### Run scanner + tests
```bash
python scripts/scan_execution_violations.py
pytest server/tests/execution -v
```

---

## 8. Before Opening a PR

Run all of this:

```bash
python scripts/scan_execution_violations.py
pytest server/tests -v
pytest server/tests/execution -v
```

If anything fails, fix it before pushing.

---

## 9. Where to Learn More

- **Execution Governance:**
  `docs/design/execution-governance.md`

- **Phase 12 Wrap‑Up:**
  `docs/phase12-wrap-up.md`

- **Repo Audit Checklist:**
  `docs/repo-audit-checklist.md`

This quickstart is the "how," those documents are the "why."

---

## 10. ASCII Architecture Reference

```
+--------+        +---------------------------+        +---------------------------+
| Client |  HTTP  |        API Route          |        |  AnalysisExecutionService |
|        +------->|   /v1/analyze-execution   +------->+  (sync + async orchestration)
+--------+        +---------------------------+        +---------------------------+
                                                            |
                                                            v
                                                 +---------------------------+
                                                 |    JobExecutionService    |
                                                 | PENDING→RUNNING→SUCCESS/  |
                                                 |           FAILED          |
                                                 +---------------------------+
                                                            |
                                                            v
                                                 +---------------------------+
                                                 |  PluginExecutionService   |
                                                 |  delegates to ToolRunner  |
                                                 +---------------------------+
                                                            |
                                                            v
                                                 +---------------------------+
                                                 |        ToolRunner         |
                                                 | validation + metrics +    |
                                                 |  lifecycle + envelopes    |
                                                 +---------------------------+
                                                            |
                                                            v
                                                 +---------------------------+
                                                 |          Plugin           |
                                                 |        .run(payload)      |
                                                 +---------------------------+


                           +---------------------------------------------+
                           |             Plugin Registry                 |
                           |  state, success/error counts, timings,     |
                           |  last_used, etc. (updated by ToolRunner)   |
                           +---------------------------------------------+


+---------------------------+                 +---------------------------+
|   Mechanical Scanner      |                 |   Execution Governance    |
| scripts/scan_execution_   |  enforces       |           CI              |
| violations.py             +---------------->+ .github/workflows/       |
| - no direct plugin.run    |                 |   execution-ci.yml        |
| - ToolRunner invariants   |                 | - scanner + tests on PR   |
+---------------------------+                 +---------------------------+
```
