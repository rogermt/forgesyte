# Phase 11 Manual QA Checklist

## Plugin Execution Safety
- [ ] Trigger a plugin that raises an exception → server stays alive
- [ ] Response contains structured error (no traceback)
- [ ] ToolRunner never calls plugin.run() directly

## Lifecycle State Machine
- [ ] GET /v1/plugins shows only: LOADED, INITIALIZED, RUNNING, FAILED, UNAVAILABLE
- [ ] FAILED plugins include a reason
- [ ] UNAVAILABLE plugins include a reason
- [ ] No plugin stuck in None or empty state

## Health API
- [ ] GET /v1/plugins → 200
- [ ] GET /v1/plugins/{name}/health → 200
- [ ] GET /v1/plugins/does_not_exist/health → 404
- [ ] Never returns 500

## Registry Thread Safety
- [ ] Run 200 concurrent health checks → no deadlocks
- [ ] No "dictionary changed size" errors
- [ ] No inconsistent plugin states

## VideoTracker Stability
- [ ] Run VideoTracker on machine without GPU → structured error
- [ ] No crash, no traceback
- [ ] State becomes UNAVAILABLE or FAILED appropriately

## Pre-Commit Governance
- [ ] Break a test → commit is blocked
- [ ] Fix test → commit succeeds

## Regression
- [ ] Phase 9 tests pass
- [ ] Phase 10 tests pass

---

## Test Results Summary

**Date Completed:** _________  
**Tester:** _________  

### Passing
- [ ] Plugin Execution Safety: **0/3** ✓
- [ ] Lifecycle State Machine: **0/4** ✓
- [ ] Health API: **0/4** ✓
- [ ] Registry Thread Safety: **0/3** ✓
- [ ] VideoTracker Stability: **0/3** ✓
- [ ] Pre-Commit Governance: **0/2** ✓
- [ ] Regression: **0/2** ✓

### Issues Found
```
(None yet)
```

### Sign-Off
Phase 11 QA Status: **PENDING**
