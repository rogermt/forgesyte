# Phase 11 Developer Contract

**Governance rules for plugin stability and crash-proof execution.**

This document is binding. Every commit must satisfy these rules.

---

## Core Principle

**No plugin failure crashes the server.**

All plugin execution is sandboxed. All plugin state is visible. All errors are recoverable.

---

## Rule 1: Server Tests MUST Run Before Every Commit

**Binding rule.** Non-negotiable.

### Command

```bash
cd server && uv run pytest --cov=app --cov-report=term-missing -v
```

### Verification

Before committing:

```bash
# Run server tests
cd server && uv run pytest -q

# If any test fails, FIX IT. Do not commit.
# If all pass, proceed to commit.
```

### Enforcement

- **Pre-commit hook** – Runs `pytest` before every commit
- **CI/CD** – PR cannot merge if tests fail
- **Review** – PRs without test confirmation are rejected

### Consequence

If you commit without running tests:

- Pre-commit hook blocks commit
- CI blocks merge
- PR is closed with comment: "Please run server tests locally before pushing"

---

## Rule 2: All Plugin Execution Goes Through Sandbox

**Binding rule.** No exceptions.

### Pattern

Every plugin function call **must** use `run_plugin_sandboxed()`:

```python
from app.plugins.sandbox.sandbox_runner import run_plugin_sandboxed

result = run_plugin_sandboxed(plugin.run, *args, **kwargs)

if not result.ok:
    registry.mark_failed(plugin_name, result.error)
```

### Exceptions

**There are no exceptions.** If you think you found one, you're wrong.

Even "trusted" plugins get sandboxed. Especially those.

### Code Review

Any code that calls a plugin function **without** `run_plugin_sandboxed()` is rejected.

```python
# ✗ REJECTED
plugin.run(args)

# ✓ ACCEPTED
result = run_plugin_sandboxed(plugin.run, args)
```

---

## Rule 3: Plugin Registry State Must Be Updated on Every Outcome

**Binding rule.** Every execution path updates registry state.

### Pattern

```python
# Load plugin
if error:
    registry.mark_failed(name, reason)
else:
    registry.register(name)

# Run plugin
registry.mark_running(name)
result = run_plugin_sandboxed(...)

if result.ok:
    registry.record_success(name)
else:
    registry.mark_failed(name, result.error)
    registry.record_error(name)
```

### Code Review

If a code path doesn't update registry state, PR is rejected.

```python
# ✗ REJECTED - no state update on error
result = run_plugin_sandboxed(...)
if not result.ok:
    return error_response  # Missing registry.mark_failed()

# ✓ ACCEPTED - state updated
result = run_plugin_sandboxed(...)
if not result.ok:
    registry.mark_failed(name, result.error)
    return error_response
```

---

## Rule 4: Health API Endpoints Must Never Return 500

**Binding rule.** Health API is the source of truth. It must be reliable.

### Guarantee

- `GET /v1/plugins` → Always 200
- `GET /v1/plugins/{name}/health` → Always 200 or 404
- No unhandled exceptions
- No internal server errors

### Code Review

Any exception in `health_router.py` is a blocker. PR is rejected and sent back for fixes.

```python
# ✓ ACCEPTED - HTTPException with 404
if not registry.has(name):
    raise HTTPException(status_code=404, detail="Plugin not found")

# ✗ REJECTED - unhandled exception
status = registry.get_status(name)  # Could raise KeyError
return status
```

---

## Rule 5: All Plugin Errors Must Have Actionable Reason Strings

**Binding rule.** Error messages must be useful.

### Pattern

```python
# ✗ REJECTED - vague
registry.mark_failed(name, "Error")

# ✓ ACCEPTED - actionable
registry.mark_failed(
    name,
    "ImportError: No module named 'torch' (GPU plugin requires PyTorch)"
)
```

### Why

System operators must be able to:

1. Understand what failed
2. Fix it without looking at code
3. Know if it's temporary (FAILED) or permanent (UNAVAILABLE)

### Code Review

Vague error messages are rejected. Re-submit with clear, actionable messages.

---

## Rule 6: FAILED ≠ UNAVAILABLE

**Binding rule.** These states mean different things.

### FAILED

**Transient error.** Plugin loaded but crashed during execution.

- Example: network timeout during tool run
- Example: bad input to plugin
- Example: out of memory during execution
- Recovery: server restart might help; admin intervention likely needed

### UNAVAILABLE

**Permanent issue.** Plugin cannot be loaded.

- Example: missing GPU when plugin requires GPU
- Example: dependency not installed (`pip install torch`)
- Example: model file not found
- Recovery: install dependencies; then restart server

### Code Review

If you use the wrong state, PR is rejected.

```python
# ✗ REJECTED - wrong state for missing dependency
registry.mark_failed(name, "Missing torch")

# ✓ ACCEPTED - correct state for missing dependency
registry.mark_unavailable(name, "Missing torch (install with: pip install torch)")
```

---

## Rule 7: Thread Safety Is Mandatory

**Binding rule.** Plugin registry is accessed from multiple threads.

### Pattern

All access to registry state **must** be protected:

```python
from threading import Lock

class Registry:
    def __init__(self):
        self._lock = Lock()
    
    def mark_failed(self, name: str, reason: str):
        with self._lock:
            # Update state
```

### Code Review

Any access to shared state without locking is rejected.

```python
# ✗ REJECTED - no locking
self._plugins[name] = ...

# ✓ ACCEPTED - locked
with self._lock:
    self._plugins[name] = ...
```

---

## Rule 8: Plugin Tests Must Be RED Before Implementation

**Binding rule.** Tests define the contract.

### Workflow

1. Write RED tests (tests fail because code doesn't exist)
2. Run tests → verify they fail
3. Implement code to make tests GREEN
4. Run tests → verify they pass
5. Commit

### Code Review

If you implement code without RED tests first, PR is rejected.

```
"Please add RED tests first. Tests should fail before implementation."
```

---

## Rule 9: No Plugin Can Crash the Server

**Binding rule.** This is non-negotiable.

### Guarantee

The server must remain running even if:

- Plugin import fails
- Plugin init fails
- Plugin tool raises exception
- Plugin uses infinite memory
- Plugin uses infinite CPU
- Plugin segfaults (if possible)

### Testing

Every plugin must have tests that verify:

```python
def test_plugin_never_crashes_server():
    """Verify that plugin failure doesn't crash server."""
    result = run_plugin_sandboxed(broken_plugin.run, bad_input)
    assert result.ok is False
    assert server_is_still_running()
```

### Code Review

Any code that could crash the server is rejected immediately.

---

## Rule 10: Health API Response Must Be Complete

**Binding rule.** Every health response must have required fields.

### Pattern

```python
PluginHealthResponse(
    name=plugin_name,  # Required
    state=state,  # Required
    description=description,  # Optional
    reason=reason_if_failed,  # Optional
    version=version,  # Optional
    uptime_seconds=uptime,  # Optional
    success_count=count,  # Required
    error_count=count,  # Required
)
```

### Code Review

Missing required fields = PR rejected.

---

## Enforcement Mechanism

### Pre-Commit Hook

```yaml
# .pre-commit-config.yaml
- id: server-tests-phase-11
  name: "Phase 11: Server tests must pass"
  entry: bash -c 'cd server && uv run pytest -q --tb=line'
  language: system
  pass_filenames: false
  stages: [commit]
```

### CI/CD

```yaml
# .github/workflows/ci.yml
- name: "Phase 11: Run server tests"
  run: cd server && uv run pytest --cov=app -v
  
- name: "Block merge if tests fail"
  if: failure()
  run: exit 1
```

### PR Template

```md
## Phase 11 Compliance Checklist

- [ ] Ran `cd server && uv run pytest` locally
- [ ] All server tests pass
- [ ] Plugin execution goes through sandbox
- [ ] Registry state updated on all outcomes
- [ ] Health API endpoints return correct status codes
- [ ] Error messages are actionable
- [ ] Thread safety verified
- [ ] RED tests written before implementation
```

### Code Review Automation

Use GitHub Actions to auto-reject PRs that:

```
1. Have server test failures
2. Add plugin calls without sandbox
3. Add HTTP endpoints that can raise unhandled exceptions
4. Have vague error messages
5. Don't update registry state
```

---

## Summary

| Rule | Level | Enforcement |
|------|-------|-------------|
| Server tests before commit | Binding | Pre-commit hook + CI |
| All execution through sandbox | Binding | Code review |
| Registry state on every outcome | Binding | Code review |
| Health API never 500 | Binding | CI tests |
| Actionable error messages | Binding | Code review |
| FAILED ≠ UNAVAILABLE | Binding | Code review |
| Thread safety | Binding | Code review |
| RED tests first | Binding | Code review |
| No plugin crashes server | Binding | Test coverage |
| Complete health response | Binding | Code review |

---

## Deviation Protocol

If you need to deviate from any rule:

1. **Document** why in the PR description
2. **Get approval** from the project lead
3. **Add a test** that verifies the deviation
4. **Update this document** to reflect the exception

No deviations without documentation and approval.

---

## For Project Leads

Use this checklist for every Phase 11 PR:

- [ ] All RED tests present and failing
- [ ] All implementation tests passing
- [ ] No plugin execution without sandbox
- [ ] Registry state updated on all paths
- [ ] Health API endpoints verified
- [ ] Error messages are clear
- [ ] Thread safety verified
- [ ] Server tests pass locally and in CI
- [ ] No phase 9/10 regressions

If any check fails, request changes.

---

**This contract is binding as of Phase 11 kickoff.**

All future plugin work must satisfy these rules.

**No exceptions.**
