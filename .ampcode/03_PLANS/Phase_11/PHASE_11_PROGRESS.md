# Phase 11 Progress Tracker

**Plugin Stability & Crash-Proof Execution**

Status: 🔵 SPECIFICATION COMPLETE | ⏳ IMPLEMENTATION PENDING

---

## Overview

Phase 11 transforms the plugin system from "might crash the server" to "impossible to crash the server."

- **Specification Status:** ✅ COMPLETE (12 docs, 6,000+ lines)
- **Implementation Status:** ⏳ NOT STARTED
- **Timeline:** 8 commits across 4 weeks
- **Success Criteria:** 7 objective items

---

## Specification Documents (✅ COMPLETE)

### Foundation Documents
- [x] PHASE_11_KICKOFF.md – First 5 commits, scaffolding
- [x] PHASE_11_ARCHITECTURE.md – System design, components, data flow
- [x] PHASE_11_RED_TESTS.md – 17 RED test cases (pre-implementation)

### Implementation Documents
- [x] PHASE_11_CONCRETE_IMPLEMENTATION.md – Production code ready
- [x] PHASE_11_PLUGIN_LOADER_V2.md – Full PluginLoader v2 implementation
- [x] PHASE_11_VIDEOTRACKER_STABILITY.md – Hardening patch

### Governance Documents
- [x] PHASE_11_DEVELOPER_CONTRACT.md – 10 binding rules
- [x] PHASE_11_IMPLEMENTATION_PLAN.md – 8-commit timeline
- [x] PHASE_11_PR_TEMPLATE.md – Markdown template
- [x] PHASE_11_COMPLETION_CRITERIA.md – Definition of done

### Active Documents
- [x] .github/pull_request_template.md – GitHub automation
- [x] scripts/audit_plugins.py – Governance scanner

---

## Implementation Status

### Commit 1: Scaffold Plugin Stability Modules

**Status:** ⏳ PENDING

**Expected Output:**
- Directory structure created
- All modules with `pass` stubs
- Imports wired

**Verification:**
```bash
cd server && python -m pytest tests/ -q
# Expected: Tests RED (failing)
```

**Checklist:**
- [ ] Create `server/app/plugins/loader/` module
- [ ] Create `server/app/plugins/sandbox/` module
- [ ] Create `server/app/plugins/lifecycle/` module
- [ ] Create `server/app/plugins/health/` module
- [ ] All files have stubs (no implementation)
- [ ] Imports resolve

---

### Commit 2: Wire Plugin Health API into FastAPI

**Status:** ⏳ PENDING

**Expected Output:**
- `/v1/plugins` endpoint wired
- `/v1/plugins/{name}/health` endpoint wired
- Router included in main app

**Verification:**
```bash
cd server && pytest tests/test_plugin_health_api/ -v
# Expected: Tests RED (endpoints not implemented)
```

**Checklist:**
- [ ] PluginHealthResponse model created
- [ ] PluginHealthRouter created
- [ ] Router included in main app
- [ ] Endpoints callable (return NotImplementedError)
- [ ] Tests fail as expected (RED)

---

### Commit 3: Implement PluginRegistry

**Status:** ⏳ PENDING

**Expected Output:**
- PluginRegistry with thread-safe state tracking
- PluginLifecycleManager working
- All state transitions implemented

**Verification:**
```bash
cd server && pytest tests/test_plugin_loader/test_import_failures.py -v
# Expected: Tests GREEN
```

**Checklist:**
- [ ] PluginRegistry class implemented (from PHASE_11_CONCRETE_IMPLEMENTATION.md)
- [ ] Thread-safe with locks
- [ ] All methods: register, mark_failed, mark_unavailable, get_status, list_all, list_available
- [ ] LifecycleManager integrated
- [ ] Tests pass

---

### Commit 4: Implement PluginSandboxRunner

**Status:** ⏳ PENDING

**Expected Output:**
- Sandbox runner catches all exceptions
- Returns structured error objects
- Never raises to caller

**Verification:**
```bash
cd server && pytest tests/test_plugin_sandbox/ -v
# Expected: All sandbox tests GREEN
```

**Checklist:**
- [ ] PluginSandboxResult class implemented
- [ ] run_plugin_sandboxed() function implemented (from PHASE_11_CONCRETE_IMPLEMENTATION.md)
- [ ] Exception handling complete
- [ ] Error types captured
- [ ] Tests pass

---

### Commit 5: Wire ToolRunner to Sandbox

**Status:** ⏳ PENDING

**Expected Output:**
- ToolRunner.run() uses sandbox
- Registry state updated on all paths
- Success/error counts tracked

**Verification:**
```bash
cd server && pytest tests/test_tool_runner/test_sandbox_integration.py -v
# Expected: All integration tests GREEN
```

**Checklist:**
- [ ] ToolRunner imports sandbox runner
- [ ] ToolRunner.run() wrapped in sandbox
- [ ] Registry.mark_failed() called on errors
- [ ] Registry.record_success() called on success
- [ ] Registry.record_error() called on failure
- [ ] Tests pass

---

### Commit 6: Add Error Tracking & Metrics

**Status:** ⏳ PENDING

**Expected Output:**
- Plugin execution metrics tracked
- Health API returns full metrics
- Success/error counts exposed

**Verification:**
```bash
cd server && pytest tests/test_plugin_metrics/ -v
# Expected: All metrics tests GREEN
```

**Checklist:**
- [ ] success_count tracking added to PluginMetadata
- [ ] error_count tracking added to PluginMetadata
- [ ] uptime_seconds calculation added
- [ ] last_used timestamp updated
- [ ] PluginHealthResponse includes all metrics
- [ ] Health API returns metrics

---

### Commit 7: Add Timeout & Memory Guards

**Status:** ⏳ PENDING

**Expected Output:**
- Timeout wrapper for sandbox
- Memory limit wrapper for sandbox
- Guards prevent hanging/OOM

**Verification:**
```bash
cd server && pytest tests/test_plugin_sandbox/test_timeout.py -v
cd server && pytest tests/test_plugin_sandbox/test_memory_guard.py -v
# Expected: All guard tests GREEN
```

**Checklist:**
- [ ] timeout.py module implemented
- [ ] memory_guard.py module implemented
- [ ] run_plugin_sandboxed_with_guards() function created
- [ ] Timeout handling tested
- [ ] Memory limits tested
- [ ] Tests pass

---

### Commit 8: Enforce Developer Contract & Final Tests

**Status:** ⏳ PENDING

**Expected Output:**
- Pre-commit hook enforces tests
- All Phase 11 tests pass
- No Phase 9/10 regressions

**Verification:**
```bash
cd server && pytest tests/test_plugin_loader/ \
                    tests/test_plugin_health_api/ \
                    tests/test_plugin_sandbox/ \
                    tests/test_tool_runner/ \
                    tests/test_videotracker_stability/ -v

cd web-ui && npm run test -- --run
# Expected: All tests GREEN (40+ Phase 11, 16 Phase 9, 31 Phase 10)
```

**Checklist:**
- [ ] Pre-commit hook configured
- [ ] PR template updated
- [ ] CI checks updated
- [ ] All Phase 11 tests pass
- [ ] All Phase 9 tests pass
- [ ] All Phase 10 tests pass
- [ ] No regressions

---

## Completion Criteria Status

| Criterion | Status | Evidence |
|-----------|--------|----------|
| 1. Loader v2 operational | ⏳ PENDING | Will pass Commit 3 tests |
| 2. Sandbox enforced | ⏳ PENDING | Will pass Commit 5 tests |
| 3. Health API stable | ⏳ PENDING | Will pass Commit 2 tests |
| 4. VideoTracker hardened | ⏳ PENDING | Will pass Commit 6 tests |
| 5. RED tests GREEN | ⏳ PENDING | Will pass Commit 8 tests |
| 6. No regressions | ⏳ PENDING | Will pass Commit 8 tests |
| 7. Governance enforced | ⏳ PENDING | Will pass Commit 8 tests |

---

## Daily Checklist (When Implementing)

### Before Starting Day
- [ ] Pull latest from main
- [ ] Verify no conflicts with other work
- [ ] Check Phase 10/9 tests still pass

### During Day
- [ ] Write RED tests first (if new features)
- [ ] Implement code
- [ ] Run tests frequently
- [ ] Check for lint/type issues

### Before Commit
```bash
cd server && uv run pytest -v
cd server && uv run ruff check --fix app/
cd server && uv run mypy app/ --no-site-packages
cd web-ui && npm run type-check && npm run lint
```

- [ ] All tests pass
- [ ] All lint passes
- [ ] All types pass
- [ ] No Phase 9/10 regressions
- [ ] Commit message clear

---

## Testing Progress

### Phase 11 Tests (40+ total)

**Test Suite Status:**

| Suite | Count | Status |
|-------|-------|--------|
| Import Failures | 3 | ⏳ PENDING |
| Init Failures | 2 | ⏳ PENDING |
| Dependency Checking | 6 | ⏳ PENDING |
| Health API | 8 | ⏳ PENDING |
| Sandbox Runner | 6 | ⏳ PENDING |
| ToolRunner Integration | 4 | ⏳ PENDING |
| VideoTracker Stability | 4 | ⏳ PENDING |
| Metrics | 3+ | ⏳ PENDING |
| Timeout/Memory Guards | 4+ | ⏳ PENDING |

**Total: 40+ tests**

### Regression Tests

| Suite | Count | Status |
|-------|-------|--------|
| Phase 9 UI Controls | 16 | ✅ PASSING |
| Phase 10 Realtime | 31 | ✅ PASSING |

---

## Implementation Notes

### Key Files to Create/Modify

```
server/app/plugins/
├── __init__.py
├── loader/
│   ├── __init__.py
│   ├── plugin_loader.py ← Commit 3
│   ├── plugin_registry.py ← Commit 3
│   ├── dependency_checker.py ← Commit 3
│   └── plugin_errors.py ← Commit 1
├── sandbox/
│   ├── __init__.py
│   ├── sandbox_runner.py ← Commit 4
│   ├── timeout.py ← Commit 7
│   └── memory_guard.py ← Commit 7
├── lifecycle/
│   ├── __init__.py
│   ├── lifecycle_state.py ← Commit 1
│   └── lifecycle_manager.py ← Commit 3
└── health/
    ├── __init__.py
    ├── health_model.py ← Commit 2
    └── health_router.py ← Commit 2

server/app/main.py ← Patches in Commits 2, 5, 8
server/app/tools/runner.py ← Patch in Commit 5

tests/
├── test_plugin_loader/ ← RED in Commit 1, GREEN in Commit 3
├── test_plugin_health_api/ ← RED in Commit 2, GREEN in Commit 2
├── test_plugin_sandbox/ ← RED in Commit 2, GREEN in Commit 4
├── test_tool_runner/ ← RED in Commit 2, GREEN in Commit 5
└── test_videotracker_stability/ ← RED in Commit 2, GREEN in Commit 6

.github/pull_request_template.md ← Updated for Phase 11
scripts/audit_plugins.py ← Governance tool
```

---

## Known Issues / Blockers

None currently. All specification complete and ready for implementation.

---

## Rollout Plan

1. **Week 1-2:** Implement Commits 1-3 (Scaffold, Router, Registry)
2. **Week 2-3:** Implement Commits 4-6 (Sandbox, Integration, Metrics)
3. **Week 3-4:** Implement Commits 7-8 (Guards, Enforcement)
4. **End of Week 4:** Merge to main, deploy Phase 11

---

## Success Metrics

### At Completion

✅ **40+ Phase 11 tests pass**

✅ **0 Phase 9/10 test failures**

✅ **No plugin crashes under any condition**

✅ **Health API always returns 200 or 404**

✅ **All error messages actionable**

✅ **Pre-commit hook enforces governance**

---

## Links

- [Phase 11 Completion Criteria](.ampcode/04_PHASE_NOTES/Phase_11/PHASE_11_COMPLETION_CRITERIA.md)
- [Phase 11 Implementation Plan](.ampcode/04_PHASE_NOTES/Phase_11/PHASE_11_IMPLEMENTATION_PLAN.md)
- [Phase 11 Concrete Implementation](.ampcode/04_PHASE_NOTES/Phase_11/PHASE_11_CONCRETE_IMPLEMENTATION.md)
- [Phase 11 Developer Contract](.ampcode/04_PHASE_NOTES/Phase_11/PHASE_11_DEVELOPER_CONTRACT.md)

---

## Next Steps

1. ✅ **Complete Phase 11 specification** (DONE)
2. ⏳ **Implement Commit 1:** Scaffold modules
3. ⏳ **Implement Commit 2:** Wire health API
4. ⏳ **Implement Commits 3-8:** Per implementation plan
5. ⏳ **Verify all criteria met**
6. ⏳ **Merge to main**
7. ⏳ **Kick off Phase 12**

---

**Status Updated:** 2026-02-15

**Last Modified By:** Phase 11 Setup

**Next Review:** When implementation starts
