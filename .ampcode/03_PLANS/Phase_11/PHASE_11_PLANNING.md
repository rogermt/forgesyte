going to # Phase 11 Planning Document

**Phase:** Plugin Stability & Crash-Proof Execution  
**Status:** PLANNING COMPLETE → READY FOR IMPLEMENTATION  
**Created:** 2026-02-15  
**Owner:** Roger  

---

## Executive Summary

Phase 11 transforms the plugin system from "might crash the server" to "impossible to crash the server." This is achieved through:

1. **Plugin Loader v2** - Safe import/init with error isolation
2. **Sandbox Runner** - Exception wrapping for all plugin executions
3. **Lifecycle Management** - Observable plugin states (LOADED, INITIALIZED, RUNNING, FAILED, UNAVAILABLE)
4. **Health API** - Queryable plugin status via HTTP endpoints
5. **Dependency Checking** - GPU/deps validation before loading

---

## Phase Dependencies

### Required From Phase 10 (Already Complete)
- ✅ Real-time WebSocket infrastructure (`server/app/realtime/`)
- ✅ ExtendedJobResponse model (`server/app/extended_job.py`)
- ✅ Plugin InspectorService (`server/app/plugins/inspector/inspector_service.py`)
- ✅ ProgressBar and PluginInspector components
- ✅ RealtimeContext state management
- ✅ ConnectionManager for multiple clients

### Required For Phase 12 (Unblocked By Phase 11)
- Plugin orchestration system
- Multi-plugin workflow manager
- Advanced scheduling/queuing

---

## Core Deliverables

### 1. Plugin Loader v2

**Purpose:** Safe plugin loading with complete error isolation

**Components:**
```
server/app/plugins/loader/
├── __init__.py
├── plugin_loader.py       # Main loader class
├── plugin_registry.py     # Plugin metadata + state tracking
├── dependency_checker.py  # GPU/deps validation
└── plugin_errors.py      # Structured error types
```

**Key Behaviors:**
- Import failures → FAILED state (not crash)
- Init failures → FAILED state (not crash)
- Missing GPU → UNAVAILABLE state
- Missing packages → UNAVAILABLE state
- Missing models → UNAVAILABLE state

### 2. Plugin Sandbox Runner

**Purpose:** Wrap all plugin function calls in exception isolation

**Location:** `server/app/plugins/sandbox/sandbox_runner.py`

**Guarantees:**
- Never raises exceptions to caller
- Returns structured result: `{ok: bool, result: Any, error: str, error_type: str}`
- Logs full traceback for debugging
- Preserves function arguments/kwargs

### 3. Plugin Lifecycle Management

**Purpose:** Track observable plugin states through execution

**States:**
```
LOADED       → Initial state after registration
INITIALIZED  → After __init__ succeeds
RUNNING      → During tool execution
FAILED       → On any exception
UNAVAILABLE  → Missing deps/GPU/models
```

**Key Property:** States are UNIDIRECTIONAL and FINAL
- Once FAILED or UNAVAILABLE, stays there until restart
- No cycling back to LOADED from FAILED

### 4. Plugin Health API

**Purpose:** Queryable plugin status for operators

**Endpoints:**
```
GET /v1/plugins
    → Returns list of all plugins with health status

GET /v1/plugins/{name}/health
    → Returns detailed health for specific plugin
```

**Response Model:**
```python
class PluginHealthResponse(BaseModel):
    name: str
    state: PluginLifecycleState  # LOADED, INITIALIZED, RUNNING, FAILED, UNAVAILABLE
    reason: Optional[str]        # Error message if FAILED/UNAVAILABLE
    version: Optional[str]
    uptime_seconds: Optional[float]
    last_used: Optional[datetime]
    success_count: int = 0
    error_count: int = 0
```

**Guarantees:**
- Never returns 500 (only 200 or 404)
- Failed plugins are visible, not hidden
- All fields populated for queryable state

### 5. VideoTracker Hardening

**Purpose:** Ensure VideoTracker fails gracefully under all conditions

**Requirements:**
- Manifest includes `requires_gpu: true`
- Manifest includes `dependencies` list
- Manifest includes `models` dict
- Missing GPU → UNAVAILABLE (not crash)
- Missing models → UNAVAILABLE (not crash)
- Runtime errors → structured error response

---

## Implementation Plan

### Phase 11a — Foundation (Commits 1-2)

**Commit 1: Scaffold Plugin Stability Modules**
- Create directory structure
- All files start as stubs with `pass`
- Import wiring complete

**Commit 2: Wire Plugin Health API**
- Implement health_model.py
- Implement health_router.py
- Mount in main.py

### Phase 11b — Sandbox & Registry (Commits 3-4)

**Commit 3: Implement PluginRegistry**
- Full PluginRegistry implementation
- Lifecycle state tracking
- Thread-safe with locks

**Commit 4: Implement PluginSandboxRunner**
- Exception isolation
- Structured result objects
- Comprehensive tests

### Phase 11c — Integration (Commits 5-6)

**Commit 5: Wire ToolRunner to Sandbox**
- Patch run_tool() method
- Update registry on all paths
- Success/error tracking

**Commit 6: Add Error Tracking & Metrics**
- success_count tracking
- error_count tracking
- uptime_seconds calculation

### Phase 11d — Hardening (Commits 7-8)

**Commit 7: Add Timeout & Memory Guards**
- Timeout wrapper
- Memory limit wrapper

**Commit 8: Enforce Developer Contract**
- Pre-commit hook for tests
- Final test sweep
- PR template updates

---

## Testing Strategy

### RED Tests (Written First)
- Import failure tests (3 tests)
- Init failure tests (2 tests)
- Dependency checking tests (6 tests)
- Health API tests (8 tests)
- Sandbox runner tests (6 tests)
- ToolRunner integration tests (4 tests)
- VideoTracker stability tests (4 tests)

**Total: 33+ RED tests**

### GREEN Tests (Post-Implementation)
All RED tests must pass post-implementation

### Regression Tests
- All Phase 9 tests must pass (16 tests)
- All Phase 10 tests must pass (31 tests)

---

## Success Criteria

Phase 11 is complete when:

- [ ] PluginRegistry fully operational (thread-safe state tracking)
- [ ] PluginSandboxRunner catches all exceptions
- [ ] Health API never returns 500
- [ ] VideoTracker hardened (no crashes)
- [ ] All 33+ RED tests pass (GREEN)
- [ ] All Phase 9/10 tests still pass
- [ ] Pre-commit governance enforced
- [ ] audit_plugins.py passes

---

## Risk Assessment

### High Risk Areas

1. **Thread Safety Under Load**
   - Risk: Registry lock contention under 100+ concurrent requests
   - Mitigation: Add lock timeout + metrics
   - Contingency: RWLock or reduced lock scope

2. **Timeout/Memory Guards Performance**
   - Risk: Guards add >10ms overhead per call
   - Mitigation: Benchmark guards, make optional per-plugin
   - Contingency: Skip guards for fast plugins

### Medium Risk Areas

1. **Dependency Detection Completeness**
   - Risk: Missing edge cases (corrupted files, network mounts)
   - Mitigation: Comprehensive tests with real failure modes
   - Contingency: Fallback to try-import approach

2. **Error Message Clarity**
   - Risk: Users can't understand error messages
   - Mitigation: Review real errors, add remediation steps
   - Contingency: User testing with actual plugin failures

---

## Developer Contract Summary

All commits must satisfy:

1. ✅ Server tests before commit (`pytest`)
2. ✅ All plugin execution through sandbox
3. ✅ Registry state updated on every outcome
4. ✅ Health API never returns 500
5. ✅ Actionable error messages
6. ✅ FAILED ≠ UNAVAILABLE (correct state usage)
7. ✅ Thread safety (locks on shared state)
8. ✅ RED tests written before implementation
9. ✅ No plugin crashes server
10. ✅ Complete health response

---

## File Structure

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
└── health/
    ├── __init__.py
    ├── health_router.py
    └── health_model.py

server/tests/
├── test_plugin_loader/
├── test_plugin_sandbox/
├── test_plugin_lifecycle/
├── test_plugin_health_api/
└── test_videotracker_stability/
```

---

## Timeline

| Week | Phase | Focus |
|------|-------|-------|
| 1 | 11a | Scaffolding, API wiring |
| 2 | 11b | Registry, Sandbox implementation |
| 3 | 11c | ToolRunner integration, Metrics |
| 4 | 11d | Guards, Contract enforcement, Final tests |

---

## Next Steps

1. ✅ Complete Phase 11 planning (this document)
2. ⏳ Implement Commit 1: Scaffold modules
3. ⏳ Implement Commit 2: Wire health API
4. ⏳ Implement Commits 3-8: Per implementation plan
5. ⏳ Verify all criteria met
6. ⏳ Merge to main
7. ⏳ Kick off Phase 12

---

## References

- [Phase 11 Architecture](.ampcode/04_PHASE_NOTES/Phase_11/PHASE_11_ARCHITECTURE.md)
- [Phase 11 Implementation Plan](.ampcode/04_PHASE_NOTES/Phase_11/PHASE_11_IMPLEMENTATION_PLAN.md)
- [Phase 11 Concrete Implementation](.ampcode/04_PHASE_NOTES/Phase_11/PHASE_11_CONCRETE_IMPLEMENTATION.md)
- [Phase 11 Developer Contract](.ampcode/04_PHASE_NOTES/Phase_11/PHASE_11_DEVELOPER_CONTRACT.md)
- [Phase 11 Completion Criteria](.ampcode/04_PHASE_NOTES/Phase_11/PHASE_11_COMPLETION_CRITERIA.md)

re 