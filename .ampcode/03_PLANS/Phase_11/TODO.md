er# Phase 11 Implementa or filenames?tion - Complete Plan

## Commit 6 - Error Tracking & Metrics
**Status: ✅ COMPLETE**

### Tasks:
- [x] 1. Add `execution_time_ms` field to `PluginSandboxResult`
- [x] 2. Add `execution_time_ms` field to `PluginHealthResponse` model
- [x] 3. Track execution time in `run_plugin_sandboxed()`
- [x] 4. Update `PluginMetadata` to store execution times
- [x] 5. Add `avg_execution_time_ms` to health response (calculated from last 10 runs)
- [x] 6. Update `plugin_registry.py` to track execution metrics
- [x] 7. Write tests for execution time tracking (24 tests pass)

### Files Modified:
- `server/app/plugins/sandbox/sandbox_runner.py`
- `server/app/plugins/health/health_model.py`
- `server/app/plugins/loader/plugin_registry.py`
- `server/app/services/plugin_management_service.py`
- `server/tests/plugins/test_tool_runner_sandbox.py`

---

## Commit 7 - Timeout/Memory Guards
**Status: ✅ COMPLETE**

### Tasks:
- [x] 1. Implement `timeout.py`:
  - [x] `TimeoutGuardResult` dataclass with timeout tracking
  - [x] `run_with_timeout()` function with ThreadPoolExecutor
  - [x] `run_sandboxed_with_timeout()` convenience function
  - [x] Default timeout: 60 seconds

- [x] 2. Implement `memory_guard.py`:
  - [x] `MemoryGuardResult` dataclass with memory tracking
  - [x] `get_memory_usage_bytes()` using psutil
  - [x] `run_with_memory_guard()` function
  - [x] Default limit: 1 GB (1024 MB)

- [x] 3. Integrate guards into sandbox runner:

  - [x] `run_with_guards()` convenience function (in separate timeout.py module)
- [x] 4. Update `sandbox/__init__.py` exports

- [x] 5. Write tests for timeout and memory guards (24 tests pass)

### Files Modified:
- `server/app/plugins/sandbox/timeout.py`
- `server/app/plugins/sandbox/memory_guard.py`
- `server/app/plugins/sandbox/sandbox_runner.py`
- `server/app/plugins/sandbox/__init__.py`

---

## Commit 8 - Enforce Governance
**Status: ⏳ PENDING**

### Tasks:
- [ ] 1. Run all server tests
  ```bash
  cd server && uv run pytest -v
  ```

- [ ] 2. Run linting
  ```bash
  cd server && uv run ruff check --fix app/
  ```

- [ ] 3. Run type checking
  ```bash
  cd server && uv run mypy app/ --no-site-packages
  ```

- [ ] 4. Run pre-commit hooks
  ```bash
  uv run pre-commit run --all-files
  ```

- [ ] 5. Update this TODO.md with verification results

- [ ] 6. Update PHASE_11_PROGRESS.md to mark all commits complete

### Files to Modify:
- `.ampcode/03_PLANS/Phase_11/TODO.md`
- `.ampcode/03_PLANS/Phase_11/PHASE_11_PROGRESS.md`

---

## Verification Checklist (All Commits)

### Pre-Verification:
- [ ] All tests pass locally
- [ ] No linting errors
- [ ] No type errors
- [ ] Pre-commit hooks pass

### Post-Verification:
- [ ] Sandbox runner catches all exception types
- [ ] Registry tracks success/error counts
- [ ] Execution time is tracked
- [ ] Timeout guard works
- [ ] Memory guard works
- [ ] Health API returns complete responses

---

## Notes

### Error Types to Handle:
- ImportError (missing dependencies)
- RuntimeError (plugin runtime errors)
- ValueError (invalid arguments)
- MemoryError (memory exhausted)
- TimeoutError (execution timeout)
- Generic Exception (catch-all)

### Metrics to Track:
- success_count: Number of successful executions
- error_count: Number of failed executions
- uptime_seconds: Seconds since plugin was loaded
- last_used: Timestamp of last execution
- execution_time_ms: Last execution time in milliseconds
- avg_execution_time_ms: Average execution time (last 10 runs)

### Default Limits:
- Timeout: 60 seconds
- Memory: 1024 MB (1 GB)

