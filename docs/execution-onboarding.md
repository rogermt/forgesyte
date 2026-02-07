# Execution Layer Onboarding — Quickstart

This is the **short, practical guide** for working on the execution subsystem.

If you're touching plugins, execution services, or the execution API, start here.

---

## 1. Core Mental Model

All plugin execution must follow this path:

> Client → API → AnalysisExecutionService → JobExecutionService → PluginExecutionService → ToolRunner → Plugin

You **never** call `plugin.run()` directly.  
You **always** go through ToolRunner.

---

## 2. How to Run Tests

From the repo root:

```bash
# Run all tests
pytest server/tests -v

# Run execution governance tests only
pytest server/tests/execution -v
```

All execution changes must keep both suites green.

---

## 3. How to Run the Mechanical Scanner

The scanner enforces execution invariants (no direct plugin.run, correct lifecycle states, ToolRunner invariants).

```bash
python scripts/scan_execution_violations.py
```

- If it prints `Execution scanner OK` → you're good.  
- If it prints violations → fix them before committing.

CI will run this on every PR and push to `main`.

---

## 4. Where Things Live

| Area | Path |
|------|------|
| Execution services | `server/app/services/execution/` |
| ToolRunner | `server/app/plugins/runtime/tool_runner.py` |
| Execution API routes | `server/app/api/routes/analysis_execution.py` |
| Execution tests | `server/tests/execution/` |
| Scanner | `scripts/scan_execution_violations.py` |
| CI workflow | `.github/workflows/execution-ci.yml` |
| Execution governance docs | `docs/design/execution-governance.md` |

---

## 5. Adding or Changing a Plugin

1. Implement a `.run(payload: dict) -> dict` method.
2. Register the plugin in the plugin registry.
3. Do **not** call `plugin.run()` directly anywhere.
4. Let ToolRunner handle:
   - validation
   - metrics
   - lifecycle state updates
   - error envelopes

If you need new behavior, add it to services or ToolRunner, not around them.

---

## 6. Adding or Changing Execution Behavior

Typical changes:

- New API endpoint
- New job type
- New orchestration logic

**Rules:**

- Use `AnalysisExecutionService` for API-facing orchestration.
- Use `JobExecutionService` for job lifecycle.
- Use `PluginExecutionService` to reach ToolRunner.
- Never bypass ToolRunner.
- Add or update tests in `server/tests/execution/`.
- Run:
  ```bash
  python scripts/scan_execution_violations.py
  pytest server/tests/execution -v
  ```

---

## 7. Debugging Execution Issues

When something goes wrong:

### Check the job:
- Use job endpoints (`/v1/analyze-execution/jobs/...`)
- Inspect status: PENDING / RUNNING / SUCCESS / FAILED

### Check the error envelope:
- API returns a structured `error` object
- Look at `type`, `message`, `details`, `plugin`

### Check registry metrics:
- success_count / error_count
- last_execution_time_ms
- state (INITIALIZED / FAILED)

### Run scanner + tests:
```bash
python scripts/scan_execution_violations.py
pytest server/tests/execution -v
```

---

## 8. Before Opening a PR

Run all of this from the repo root:

```bash
python scripts/scan_execution_violations.py
pytest server/tests -v
pytest server/tests/execution -v
```

If any of these fail, fix them before pushing.

---

## 9. Where to Read More

- **Execution Governance:**  
  `docs/design/execution-governance.md`

- **Phase 12 Wrap-Up:**  
  `docs/phase12-wrap-up.md`

- **Repo Audit Checklist:**  
  `docs/repo-audit-checklist.md`

These documents define the **rules of the system**.  
This quickstart is how you work inside those rules without friction.
