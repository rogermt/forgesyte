# Phase 11 Implementation Plan

**Deterministic execution plan for Plugin Stability & Crash-Proof Execution.**

---

## Overview

Phase 11 transforms plugins from "might crash the server" to "impossible to crash the server."

**Deliverable:** A plugin system that is:
- ✅ Crash-proof (no plugin exception reaches FastAPI)
- ✅ Observable (every plugin has queryable health state)
- ✅ Recoverable (failed plugins don't block server restart)
- ✅ Governed (strict developer contract enforced)

**Timeline:** 8 commits across 4 weeks

---

## Phase 11 Structure

### 11a – Foundation (Commits 1-2)
- Scaffold modules
- Wire health API

### 11b – Sandbox & Registry (Commits 3-4)
- Implement PluginRegistry
- Implement PluginSandboxRunner

### 11c – Integration (Commits 5-6)
- Wire ToolRunner to sandbox
- Implement error tracking

### 11d – Hardening (Commits 7-8)
- Add timeout/memory guards
- Enforce developer contract
- Final test sweep

---

## Commit 1: Scaffold Plugin Stability Modules

**Branch:** `feature/phase-11-governance`

**Message:** `chore(phase-11): scaffold plugin loader, sandbox, lifecycle, health modules`

**Create directories:**

```
server/app/plugins/
├── loader/
│   ├── __init__.py
│   ├── plugin_loader.py
│   ├── plugin_registry.py
│   ├── dependency_checker.py
│   └── plugin_errors.py
├── sandbox/
│   ├── __init__.py
│   ├── sandbox_runner.py
│   ├── timeout.py
│   └── memory_guard.py
├── lifecycle/
│   ├── __init__.py
│   ├── lifecycle_state.py
│   └── lifecycle_manager.py
├── health/
│   ├── __init__.py
│   ├── health_router.py
│   └── health_model.py
└── __init__.py
```

**Create files:**

- All files start with `pass` or minimal stubs
- Imports only (no implementation)
- Allows RED tests to run

**Verification:**

```bash
cd server && python -m pytest tests/ -q
# Tests should fail (RED)
```

---

## Commit 2: Wire Plugin Health API into FastAPI

**Message:** `feat(phase-11): mount plugin health endpoints in main app`

**Implement:**

- `server/app/plugins/health/health_model.py` – `PluginHealthResponse`
- `server/app/plugins/health/health_router.py` – API endpoints
- `server/app/main.py` patch – include router

**Endpoints:**

```
GET /v1/plugins
    → Returns list[PluginHealthResponse]

GET /v1/plugins/{name}/health
    → Returns PluginHealthResponse
```

**Tests expected to fail:**

```bash
cd server && pytest tests/test_plugin_health_api/ -v
# Tests call endpoints, get NotImplementedError (RED)
```

---

## Commit 3: Implement PluginRegistry

**Message:** `feat(phase-11): implement PluginRegistry with lifecycle tracking`

**Implement:**

- `server/app/plugins/loader/plugin_registry.py` – Full implementation
- `server/app/plugins/lifecycle/lifecycle_state.py` – Enum
- `server/app/plugins/lifecycle/lifecycle_manager.py` – State manager

**Code from PHASE_11_CONCRETE_IMPLEMENTATION.md**

**Verification:**

```bash
cd server && pytest tests/test_plugin_loader/ -v
# Tests should start passing (GREEN)
```

---

## Commit 4: Implement PluginSandboxRunner

**Message:** `feat(phase-11): implement sandbox runner with exception isolation`

**Implement:**

- `server/app/plugins/sandbox/sandbox_runner.py` – Full implementation

**Code from PHASE_11_CONCRETE_IMPLEMENTATION.md**

**Tests:**

```bash
cd server && pytest tests/test_plugin_sandbox/ -v
# Tests verify sandbox never raises (GREEN)
```

**Verify sandbox isolation:**

```python
from app.plugins.sandbox.sandbox_runner import run_plugin_sandboxed

def bad_plugin():
    1 / 0

result = run_plugin_sandboxed(bad_plugin)
assert result.ok is False
assert result.error_type == "ZeroDivisionError"
```

---

## Commit 5: Wire ToolRunner to Sandbox

**Message:** `feat(phase-11): integrate sandbox runner with ToolRunner for crash-proof execution`

**Patch:**

- `server/app/tools/runner.py` – Patch `run_tool()` method

**Code from PHASE_11_CONCRETE_IMPLEMENTATION.md**

**Integration test:**

```bash
cd server && pytest tests/integration/test_tool_runner_sandbox.py -v
# Verify tool failures don't crash server
```

**Verification:**

```python
# Run a failing plugin through ToolRunner
response = tool_runner.run_tool(
    plugin_id="bad_plugin",
    tool_name="run",
    args={},
)

assert response["ok"] is False
assert response["error_type"] == "SomeError"
# Server is still running
```

---

## Commit 6: Add Error Tracking & Metrics

**Message:** `feat(phase-11): add plugin execution metrics and error tracking`

**Implement:**

- Extend `PluginRegistry` with `record_success()`, `record_error()`
- Update `PluginHealthResponse` with `success_count`, `error_count`, `uptime_seconds`
- Update `health_router.py` to return full metrics

**Tests:**

```bash
cd server && pytest tests/test_plugin_metrics/ -v
# Verify metrics are tracked and exposed
```

**Verify health response includes metrics:**

```python
response = client.get("/v1/plugins/ocr/health")
assert response.status_code == 200
body = response.json()
assert "success_count" in body
assert "error_count" in body
assert "uptime_seconds" in body
```

---

## Commit 7: Add Timeout & Memory Guards

**Message:** `feat(phase-11): add timeout and memory guards to sandbox runner`

**Implement:**

- `server/app/plugins/sandbox/timeout.py` – Timeout wrapper
- `server/app/plugins/sandbox/memory_guard.py` – Memory limit wrapper
- Update `sandbox_runner.py` to use guards

**Pattern:**

```python
def run_plugin_sandboxed_with_timeout(
    fn: Callable,
    *args,
    timeout_seconds: float = 30.0,
    max_memory_mb: float = 512.0,
    **kwargs,
) -> PluginSandboxResult:
    """Run with timeout and memory limits."""
    ...
```

**Tests:**

```bash
cd server && pytest tests/test_plugin_sandbox/test_timeout.py -v
cd server && pytest tests/test_plugin_sandbox/test_memory_guard.py -v
# Verify timeouts and memory limits are enforced
```

---

## Commit 8: Enforce Developer Contract & Final Tests

**Message:** `feat(phase-11): enforce developer contract and complete test coverage`

**Implement:**

- Add pre-commit hook for `pytest` enforcement
- Finalize PR template with Phase 11 checklist
- Add CI check for "no plugin execution without sandbox"
- Full integration test suite

**Pre-commit hook:**

```yaml
- id: server-tests-phase-11
  name: "Phase 11: Server tests must pass"
  entry: bash -c 'cd server && uv run pytest -q --tb=line'
  language: system
  pass_filenames: false
```

**CI check (GitHub Actions):**

```yaml
- name: "Phase 11: Verify all plugin calls use sandbox"
  run: |
    cd server
    # Check for any plugin.run() without run_plugin_sandboxed()
    grep -r "plugin\.run(" --include="*.py" && exit 1 || true
```

**Final verification:**

```bash
cd server

# All tests pass
pytest -v

# All integration tests pass
pytest tests/integration/ -v

# Health API is working
curl http://localhost:8000/v1/plugins
curl http://localhost:8000/v1/plugins/ocr/health

# Server stays running even with bad plugin
# (manual testing)
```

---

## Parallel Work (Can run while commits are in progress)

### Documentation

- ✅ PHASE_11_ARCHITECTURE.md (already done)
- ✅ PHASE_11_RED_TESTS.md (already done)
- ✅ PHASE_11_CONCRETE_IMPLEMENTATION.md (already done)
- ✅ PHASE_11_DEVELOPER_CONTRACT.md (already done)

### Tests (RED first)

Write all RED tests in parallel with implementation:

- `tests/test_plugin_health_api/` – RED in commit 2, GREEN in commit 3-4
- `tests/test_plugin_sandbox/` – RED in commit 2, GREEN in commit 4
- `tests/test_plugin_metrics/` – RED in commit 2, GREEN in commit 6

---

## Daily Checklist

Each day during Phase 11:

### Morning

```bash
git checkout feature/phase-11-governance
git pull origin feature/phase-11-governance

cd server && uv run pytest -v
# Verify no regressions
```

### During Day

```bash
# Write RED tests
# Implement code to make tests GREEN
# Run tests frequently

cd server && pytest -v --tb=short
```

### Before Commit

```bash
# Run full test suite
cd server && uv run pytest -v

# Run linting
cd server && uv run ruff check --fix app/

# Run type check
cd server && uv run mypy app/ --no-site-packages

# Verify no regressions
cd web-ui && npm run type-check && npm run lint

# If all pass → commit
git add -A
git commit -m "..."
git push
```

---

## Risk Mitigation

### Risk: Breaking existing ToolRunner

**Mitigation:**
- All existing ToolRunner tests must pass
- Patch ToolRunner backwards-compatibly
- No breaking changes to plugin interface

### Risk: Plugin state not properly initialized

**Mitigation:**
- Every plugin gets a state on load
- Registry is thread-safe
- Tests verify state transitions

### Risk: Health API endpoints crash

**Mitigation:**
- Health API never accesses plugin code
- All state is in PluginRegistry
- Health API has comprehensive error handling

### Risk: Sandbox overhead too high

**Mitigation:**
- Sandbox is ~1-2ms overhead per call
- Should not impact performance
- Performance tests verify latency

---

## Success Criteria

Phase 11 is complete when:

✅ **All 8 commits merged to main**

✅ **All RED tests pass** (17 tests from PHASE_11_RED_TESTS.md)

✅ **No plugin crash regressions**
- Run load test with intentionally broken plugins
- Verify server stays running

✅ **Health API is observable**
- `/v1/plugins` shows all plugin states
- `/v1/plugins/{name}/health` shows detailed state
- Failed plugins are visible

✅ **Developer contract is enforced**
- Pre-commit hook blocks commits without tests
- CI blocks merges with test failures
- PR template has Phase 11 checklist

✅ **No Phase 9/10 regressions**
- All UI controls still work
- All realtime messaging still works
- All video tracker functionality still works

✅ **Performance acceptable**
- Tool execution time increase < 5% from sandbox overhead
- Server startup time < 10s with 10+ plugins

---

## Timeline

| Week | Commits | Focus |
|------|---------|-------|
| 1 | 1-2 | Scaffolding, API wiring |
| 2 | 3-4 | Registry, Sandbox implementation |
| 3 | 5-6 | ToolRunner integration, Metrics |
| 4 | 7-8 | Guards, Contract enforcement, Final tests |

---

## PR Template

Create a PR for each commit:

```md
## Phase 11: [Commit Title]

**Objective:** [What this commit does]

**Changes:**
- [File 1]
- [File 2]

**Tests:**
- All existing tests pass
- [N] new tests added
- All new tests pass

**Verification:**
- [ ] Ran `cd server && uv run pytest` locally
- [ ] All server tests pass
- [ ] No Phase 9/10 regressions
- [ ] Health API endpoints work (if applicable)

**Related:** Phase 11 Kickoff

Closes #[issue number if exists]
```

---

## Conclusion

Phase 11 is a transformation from "plugins might crash the server" to **"impossible for plugins to crash the server."**

This plan is **deterministic**: follow it exactly, and you get a crash-proof system.

**Execute it methodically. Trust the process. Build the foundation right.**

---

## Appendix: Troubleshooting

### Tests fail: "Module not found"

```bash
cd server && uv pip install -e .
# Reinstall package in dev mode
```

### Tests pass locally but fail in CI

```bash
# Check CI environment
# Usually: missing dependencies or different Python version

# Run locally in Docker to match CI
docker run -it python:3.9 bash
```

### Performance regression detected

```bash
# Run benchmark
cd server && pytest tests/benchmark/ -v

# Compare with baseline
# If regression > 5%, optimize sandbox overhead
```

### Plugin state not updating

```bash
# Check thread locking in PluginRegistry
# Verify all access protected by self._lock

# Add debug logging
registry.mark_failed(name, reason)
# Should appear in logs
```

### Health API returns 500

```bash
# Check for unhandled exceptions in health_router.py
# Should only raise HTTPException with 404

# Add try/except around all registry access
try:
    status = registry.get_status(name)
except KeyError:
    raise HTTPException(status_code=404)
```

---

**This plan is binding. Follow it exactly.**
