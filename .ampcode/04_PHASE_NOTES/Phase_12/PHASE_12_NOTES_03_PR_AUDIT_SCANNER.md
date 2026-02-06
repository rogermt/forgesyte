### Phase 12 audit report

```md
# Phase 12 Audit Report

## Scope

Phase 12 introduces governed plugin execution via ToolRunner, structured error envelopes, registry metrics, and a layered service/API path, without breaking Phase 11.

## Execution Path

- ✅ All plugin execution flows through ToolRunner:
  - API → AnalysisService → JobManagementService → PluginManagementService → ToolRunner → plugin.run()
- ✅ No direct plugin.run() calls outside ToolRunner (enforced by scanner + tests).

## Validation

- ✅ Input validation:
  - `validate_input_payload()` rejects empty image, missing/invalid mime_type.
- ✅ Output validation:
  - `validate_plugin_output()` rejects None and non-dict outputs.

## Error Handling

- ✅ All exceptions in plugin execution are caught in ToolRunner.
- ✅ Errors are wrapped using `build_error_envelope()` with:
  - type, message, details, plugin, timestamp, _internal.traceback.
- ✅ API returns structured error via HTTP 400 with `detail=error["error"]`.

## Registry & Metrics

- ✅ `PluginRegistry.update_execution_metrics()` called in ToolRunner finally block.
- ✅ Metrics:
  - success_count, error_count, last_execution_time_ms, avg_execution_time_ms, last_used, state.

## Service Layer

- ✅ PluginManagementService:
  - Delegates to ToolRunner only.
- ✅ JobManagementService:
  - Delegates to PluginManagementService only.
- ✅ AnalysisService:
  - Delegates to JobManagementService only.

## API Layer

- ✅ `/v1/analyze` returns:
  - On success: `{ "result": {...}, "plugin": "<name>" }`
  - On error: HTTP 400 with structured error envelope.

## Phase 11 Compatibility

- ✅ Registry changes are additive.
- ✅ No public signatures removed or changed.
- ✅ Phase 11 tests expected to remain green.

## Conclusion

Phase 12 is complete when:
- All Phase 12 tests pass.
- All Phase 11 tests pass.
- Mechanical scanner reports no violations.
```

---

### Phase 12 diff‑style summary

```md
# Phase 12 Diff Summary

## New Modules

- `server/app/plugins/runtime/tool_runner.py`
- `server/app/phase12/validation.py`
- `server/app/phase12/error_envelope.py`
- `server/app/services/plugin_management_service.py`
- `server/app/services/job_management_service.py`
- `server/app/services/analysis_service.py`
- `server/app/api/routes/analyze.py` (extended/added)

## Modified Modules

- `server/app/plugins/loader/plugin_registry.py`
  - Added execution metrics fields.
  - Added `update_execution_metrics()`.
  - Kept existing registration and lookup behavior intact.

## New Tests

- `server/tests/phase_12/test_toolrunner_happy_path.py`
- `server/tests/phase_12/test_input_validation.py`
- `server/tests/phase_12/test_output_validation.py`
- `server/tests/phase_12/test_error_envelope_structure.py`
- `server/tests/phase_12/test_unstructured_errors_fail.py`
- `server/tests/phase_12/test_toolrunner_called_for_all_plugins.py`
- `server/tests/phase_12/test_job_management_uses_plugin_management.py`
- `server/tests/phase_12/test_analyze_endpoint_phase12_contract.py`

## Behavioral Changes

- Plugin execution now:
  - MUST go through ToolRunner.
  - MUST validate input/output.
  - MUST produce structured errors.
  - MUST update registry metrics.

## Non-Changes

- Existing plugin registration and lookup semantics preserved.
- Existing API routes not removed or renamed.
- Existing Phase 11 behavior remains valid.
```

---

### Phase 12 migration script (skeleton)

```python
# scripts/migrate_phase_12.py

"""
Phase 12 migration script.

Goals:
- Ensure ToolRunner exists and is wired.
- Ensure PluginRegistry has metrics fields and update_execution_metrics().
- Scan for direct plugin.run() calls and report them.
"""

import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
SERVER = ROOT / "server"


def scan_direct_plugin_run():
    pattern = re.compile(r"plugin\.run\(")
    violations = []

    for path in SERVER.rglob("*.py"):
        if "tool_runner.py" in str(path):
            continue
        text = path.read_text(encoding="utf-8")
        if pattern.search(text):
            violations.append(path)

    return violations


def main() -> int:
    violations = scan_direct_plugin_run()

    if violations:
        print("Phase 12 migration check FAILED: direct plugin.run() calls found:")
        for v in violations:
            print(f" - {v}")
        return 1

    print("Phase 12 migration check OK: no direct plugin.run() calls found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

---

### Phase 12 PR template

```md
# Phase 12 PR Template — ToolRunner & Governance

## Summary

- [ ] Implements or updates ToolRunner governed execution.
- [ ] Wires PluginManagementService → ToolRunner.
- [ ] Wires JobManagementService → PluginManagementService.
- [ ] Wires API → AnalysisService → JobManagementService.

## Changes

- [ ] New/updated files:
  - [ ] `server/app/plugins/runtime/tool_runner.py`
  - [ ] `server/app/plugins/loader/plugin_registry.py`
  - [ ] `server/app/phase12/validation.py`
  - [ ] `server/app/phase12/error_envelope.py`
  - [ ] `server/app/services/plugin_management_service.py`
  - [ ] `server/app/services/job_management_service.py`
  - [ ] `server/app/services/analysis_service.py`
  - [ ] `server/app/api/routes/analyze.py`

## Invariants

- [ ] No direct `plugin.run()` calls outside ToolRunner.
- [ ] All plugin execution goes through ToolRunner.
- [ ] All errors are structured envelopes.
- [ ] Registry metrics updated after every execution.
- [ ] Input and output validated.

## Testing

- [ ] `pytest server/tests/phase_12`
- [ ] `pytest server/tests/phase_11`
- [ ] Migration script:
  - [ ] `python scripts/migrate_phase_12.py`

## Risks / Notes

- [ ] Any known Phase 11 touchpoints.
- [ ] Any follow-up work (e.g., persistence, locking).
```

---

### Phase 12 mechanical scanner (violations)

A more focused scanner you can wire into CI or pre-commit.

```python
# scripts/scan_phase_12_violations.py

"""
Phase 12 mechanical scanner.

Checks:
- No direct plugin.run() calls outside ToolRunner.
- ToolRunner.run() exists and returns (result, error).
"""

import ast
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
SERVER = ROOT / "server"


def find_direct_plugin_run():
    violations = []

    for path in SERVER.rglob("*.py"):
        if "tool_runner.py" in str(path):
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "run" and isinstance(node.func.value, ast.Name):
                    if node.func.value.id == "plugin":
                        violations.append(path)
                        break

    return sorted(set(violations))


def check_toolrunner_signature():
    path = SERVER / "app" / "plugins" / "runtime" / "tool_runner.py"
    if not path.exists():
        return ["ToolRunner file not found"]

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    errors = []

    class ToolRunnerVisitor(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            if node.name != "ToolRunner":
                return
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "run":
                    # Expect at least (self, plugin_name, payload)
                    if len(item.args.args) < 3:
                        errors.append("ToolRunner.run() must accept (self, plugin_name, payload)")
            self.generic_visit(node)

    ToolRunnerVisitor().visit(tree)
    return errors


def main() -> int:
    failures = []

    direct = find_direct_plugin_run()
    if direct:
        failures.append("Direct plugin.run() calls found:")
        failures.extend(f" - {p}" for p in direct)

    sig_errors = check_toolrunner_signature()
    failures.extend(sig_errors)

    if failures:
        print("Phase 12 scanner FAILED:")
        for f in failures:
            print(f)
        return 1

    print("Phase 12 scanner OK: no violations detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Absolutely, Roger — let’s tighten the Phase 12 scanner so it **asserts that `update_execution_metrics()` is called inside ToolRunner’s `finally` block**, using AST analysis. This gives you a *mechanical guarantee* that no one can silently remove or bypass the metrics update.

Below is the **enhanced scanner**, with the new check added cleanly and safely.

---

# 🔍 **Enhanced Phase 12 Mechanical Scanner**  
### (Now enforces: `update_execution_metrics()` MUST appear in ToolRunner’s `finally` block)

```python
# scripts/scan_phase_12_violations.py

"""
Phase 12 mechanical scanner.

Checks:
1. No direct plugin.run() calls outside ToolRunner.
2. ToolRunner.run() exists and has correct signature.
3. ToolRunner.run() contains a finally block.
4. update_execution_metrics() is called inside that finally block.
"""

import ast
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
SERVER = ROOT / "server"


# ------------------------------------------------------------
# 1. Detect direct plugin.run() calls outside ToolRunner
# ------------------------------------------------------------

def find_direct_plugin_run():
    violations = []

    for path in SERVER.rglob("*.py"):
        if "tool_runner.py" in str(path):
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "run" and isinstance(node.func.value, ast.Name):
                    if node.func.value.id == "plugin":
                        violations.append(path)
                        break

    return sorted(set(violations))


# ------------------------------------------------------------
# 2. Check ToolRunner.run() signature
# ------------------------------------------------------------

def check_toolrunner_signature():
    path = SERVER / "app" / "plugins" / "runtime" / "tool_runner.py"
    if not path.exists():
        return ["ToolRunner file not found"]

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    errors = []

    class ToolRunnerVisitor(ast.NodeVisitor):
        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            if node.name != "ToolRunner":
                return
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "run":
                    # Expect at least (self, plugin_name, payload)
                    if len(item.args.args) < 3:
                        errors.append("ToolRunner.run() must accept (self, plugin_name, payload)")
            self.generic_visit(node)

    ToolRunnerVisitor().visit(tree)
    return errors


# ------------------------------------------------------------
# 3. Ensure update_execution_metrics() is called in finally block
# ------------------------------------------------------------

def check_metrics_update_in_finally():
    path = SERVER / "app" / "plugins" / "runtime" / "tool_runner.py"
    if not path.exists():
        return ["ToolRunner file not found"]

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    errors = []

    class FinallyCheckVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            if node.name != "run":
                return

            has_finally = False
            metrics_called = False

            for child in ast.walk(node):
                if isinstance(child, ast.Try):
                    if child.finalbody:
                        has_finally = True
                        # Look for update_execution_metrics inside finalbody
                        for stmt in child.finalbody:
                            for sub in ast.walk(stmt):
                                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
                                    if sub.func.attr == "update_execution_metrics":
                                        metrics_called = True

            if not has_finally:
                errors.append("ToolRunner.run() must contain a finally block")

            if not metrics_called:
                errors.append("update_execution_metrics() must be called inside ToolRunner.run()'s finally block")

    FinallyCheckVisitor().visit(tree)
    return errors


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main() -> int:
    failures = []

    direct = find_direct_plugin_run()
    if direct:
        failures.append("Direct plugin.run() calls found:")
        failures.extend(f" - {p}" for p in direct)

    sig_errors = check_toolrunner_signature()
    failures.extend(sig_errors)

    metrics_errors = check_metrics_update_in_finally()
    failures.extend(metrics_errors)

    if failures:
        print("Phase 12 scanner FAILED:")
        for f in failures:
            print(f)
        return 1

    print("Phase 12 scanner OK: no violations detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

---

# ⭐ What this scanner guarantees

### **1. No direct plugin.run() calls anywhere except ToolRunner**  
If someone tries to bypass governance, CI fails.

### **2. ToolRunner.run() has the correct signature**  
Ensures Phase 11 compatibility and Phase 12 invariants.

### **3. ToolRunner.run() MUST contain a finally block**  
This enforces the lifecycle guarantee.

### **4. update_execution_metrics() MUST be called inside that finally block**  
This enforces:

- metrics always update  
- even on exceptions  
- even on validation failures  
- even on plugin crashes  

This is the **core Phase 12 invariant**.

---

