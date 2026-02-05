Clarifying Questions for Phase 11 Plans
Based on my review of the Phase notes and current plan docs, here are questions that would strengthen clarity:

1. VideoTracker GPU Detection Specificity
Current state: "Check GPU before init → mark UNAVAILABLE if missing"

Question: Should we distinguish between:

No GPU hardware at all (truly unavailable)
GPU present but driver broken (could fail at runtime)
CUDA toolkit missing but fixable?
This affects error messaging quality.

2. Lock Timeout Behavior Under Contention
Current assumption: RWLock sufficient for 10-50 req/sec

Question: When lock acquisition times out (your contingency):

Should Health API return 503 (temporarily unavailable)?
Or retry with exponential backoff?
Or mark plugin UNAVAILABLE?
This clarifies what "lock timeout" actually does.

3. Silent Init Failures Detection
Mentioned in 🟨 GUESSING (3.1): Plugin's __init__ catches exception internally

Question: Do we require a validate() hook AFTER __init__ succeeds?

If yes: Should this be part of the manifest?
If no: How do we detect "init succeeded but plugin is broken"?
Affects Commit 6 requirements.

4. Error Message Specificity for Dependency Chains
Current approach: "Module X not found"

Question: Should we do a chain inspection for indirect failures?

Example: import yolo succeeds, but import yolo.models fails due to missing CUDA
Should we report "CUDA missing" or "yolo initialization failed"?
Affects DependencyChecker complexity.

5. Auto-Recovery vs Manual Restart Justification
Current decision: Manual restart only (no auto-recovery)

Question: Is this because:

Restarting might hide deeper issues?
Auto-recovery could mask corrupt state?
Simpler for Phase 11, defer to Phase 12?
Affects user experience expectations.

6. Concurrent Access Pattern Reality Check
Assumption: < 50 requests/second to plugin APIs

Question: Are we counting:

ALL API calls (health checks + tool runs)?
Just tool execution requests?

Affects lock strategy sufficiency.

7. Phase 11 Pre-Commit Hook Authority
Current state: "DO NOT ALTER per user instruction"

Question: Does this mean:

Don't change the WHAT the hook checks (tests, lint, types)?
Don't change the HOW it checks it (order, commands)?
Or both?
Affects whether we can optimize hook performance.# ⭐ Phase 11 Plans (AUTHORITATIVE - NO GUESSING)

**Status:** Specification Complete → Implementation Pending  
**Owner:** Roger  
**Depends on:** Phase 10 (Closed)  
**Unblocks:** Phase 12  

---

## Authoritative Sources

| Document | Purpose |
|----------|---------|
| PHASE_11_KICKOFF.md | First 5 commits, scaffolding |
| PHASE_11_ARCHITECTURE.md | System design, components, data flow |
| PHASE_11_RED_TESTS.md | 17 RED test cases |
| PHASE_11_CONCRETE_IMPLEMENTATION.md | Production code |
| PHASE_11_PLUGIN_LOADER_V2.md | Full PluginLoader v2 |
| PHASE_11_GREEN_TESTS.md | Post-implementation tests |
| PHASE_11_DEVELOPER_CONTRACT.md | 10 binding rules |
| PHASE_11_IMPLEMENTATION_PLAN.md | 8-commit timeline |
| PHASE_11_COMPLETION_CRITERIA.md | Definition of done |
| PHASE_11_VIDEOTRACKER_STABILITY.md | Hardening patch |
| PHASE_11_NOTES_01.md | Authoritative decisions |
| PHASE_11_NOTES_02.md | Governance model |

---

## Part 1: Strict Requirements (Non-Negotiable)

### 1.1 Sandbox Execution

All plugin execution MUST go through the sandbox wrapper. No plugin may crash the server.

```python
# MUST use sandbox for all plugin calls
from app.plugins.sandbox.sandbox_runner import run_plugin_sandboxed

result = run_plugin_sandboxed(plugin.run, **args)
```

### 1.2 Lifecycle State Machine (5 States Required)

| State | Meaning |
|-------|---------|
| LOADED | Initial state after registration |
| INITIALIZED | After `__init__` succeeds |
| RUNNING | During tool execution |
| FAILED | On any exception |
| UNAVAILABLE | Missing deps/GPU/models |

State transitions are unidirectional and final.

### 1.3 Health API Contract

```
GET /v1/plugins         → 200 (list of all plugins)
GET /v1/plugins/{name}/health → 200 or 404 (never 500)
```

### 1.4 Pre-Commit Enforcement

Before EVERY commit:
```bash
cd server && uv run pytest -v
```

### 1.5 PluginRegistry Thread Safety

Registry operations MUST be thread-safe. Lock type is RWLock (see Section 2).

---


| Registry Lock Type | RWLock (Reader-Writer Lock) |
| Reads | Use reader lock |
| Writes | Use writer lock |

```python
from threading import RWLock

class PluginRegistry:
    def __init__(self):
        self._lock = RWLock()
    
    def get_status(self, name: str) -> PluginHealthResponse:
        with self._lock.reader_lock():
            # read-only operations
    
    def mark_failed(self, name: str, reason: str) -> None:
        with self._lock.writer_lock():
            # write operations
```

### 2.2 Dependency Checking

| Check Type | Method |
|------------|--------|
| GPU/CUDA | Both `torch.cuda.is_available()` AND `nvidia-smi` (fail-safe) |
| Model Files | Read first 16 bytes (detect corruption) |
| Python Packages | `importlib.util.find_spec()` |

### 2.3 Runtime Guards

| Guard | Value |
|-------|-------|
| Timeout | 60 seconds (default) |
| Memory Limit | 1 GB (default) |
| Configuration | Global defaults + per-plugin overrides allowed |

### 2.4 Lifecycle & Recovery

| Setting | Value |
|---------|-------|
| States | 5 (LOADED, INITIALIZED, RUNNING, FAILED, UNAVAILABLE) |
| Auto-Recovery | NO - require manual restart |
| Validation Hook | REQUIRED - `plugin.validate()` after `__init__` |

### 2.5 VideoTracker Hardening

| Check | Behavior |
|-------|----------|
| Missing GPU | Mark UNAVAILABLE |
| Missing Models | Mark UNAVAILABLE |
| Runtime Error | Return structured error, no crash |
| Manifest | Must include `requires_gpu: true` |

---

## Part 3: Implementation Plan (8 Commits)

### Commit 1: Scaffold Plugin Stability Modules
- Create `server/app/plugins/loader/` module
- Create `server/app/plugins/sandbox/` module
- Create `server/app/plugins/lifecycle/` module
- Create `server/app/plugins/health/` module
- All files with `pass` stubs

### Commit 2: Wire Plugin Health API
- `health_model.py` - PluginHealthResponse
- `health_router.py` - `/v1/plugins` and `/v1/plugins/{name}/health`
- Mount in `main.py`

### Commit 3: Implement PluginRegistry
- RWLock-based thread safety
- All state transitions
- DependencyChecker with dual GPU check

### Commit 4: Implement PluginSandboxRunner
- Exception isolation
- Structured result objects
- Never raises to caller

### Commit 5: Wire ToolRunner to Sandbox
- `ToolRunner.run()` wrapped in sandbox
- Registry state updated on all paths
- Success/error counts tracked

### Commit 6: Add Error Tracking & Metrics
- success_count, error_count
- uptime_seconds
- last_used timestamp
- Health API returns full metrics

### Commit 7: Add Timeout & Memory Guards
- timeout.py module (60s default)
- memory_guard.py module (1GB default)
- Guards prevent hanging/OOM

### Commit 8: Enforce Developer Contract
- Pre-commit hook configured
- PR template updated
- Final test sweep
- No Phase 9/10 regressions

---

## Part 4: Test Requirements (40+ Tests)

### Required Test Suites

| Suite | Count | Location |
|-------|-------|----------|
| Import Failures | 3 | tests/test_plugin_loader/ |
| Init Failures | 2 | tests/test_plugin_loader/ |
| Dependency Checking | 6 | tests/test_plugin_loader/ |
| Health API | 8 | tests/test_plugin_health_api/ |
| Sandbox Runner | 6 | tests/test_plugin_sandbox/ |
| ToolRunner Integration | 4 | tests/test_tool_runner/ |
| VideoTracker Stability | 4 | tests/test_videotracker_stability/ |
| Metrics | 3+ | tests/test_plugin_metrics/ |
| Timeout/Memory Guards | 4+ | tests/test_plugin_sandbox/ |

### Regression Requirements
- Phase 9 tests: 16/16 must pass
- Phase 10 tests: 31/31 must pass

---

## Part 5: Governance Model (From PHASE_11_NOTES_02.md)

### Strict (Non-Negotiable)
- Sandbox execution
- Lifecycle states
- Health API contract
- Pre-commit server tests
- PluginRegistry thread safety
- VideoTracker stability

### Flexible (Engineering Judgment)
- Lock type (RWLock recommended, Lock acceptable)
- GPU checks (dual recommended, torch-only acceptable)
- Model validation (read bytes recommended, exists acceptable)
- plugin.validate() hook (recommended, optional)
- Timeout/memory defaults (60s/1GB recommended)
- Commit granularity (8 or fewer)
- TDD workflow (recommended)

---

## Part 6: Completion Criteria

Phase 11 is DONE when ALL of:

- [ ] PluginRegistry fully operational (RWLock, thread-safe)
- [ ] PluginSandboxRunner catches all exceptions
- [ ] Health API never returns 500 (only 200/404)
- [ ] VideoTracker hardened (no crashes)
- [ ] All 40+ Phase 11 tests pass
- [ ] All Phase 9 tests pass (16/16)
- [ ] All Phase 10 tests pass (31/31)
- [ ] Pre-commit governance enforced
- [ ] audit_plugins.py passes

---

## Part 7: File Structure

```
server/app/plugins/
├── loader/
│   ├── __init__.py
│   ├── plugin_loader.py
│   ├── plugin_registry.py ← use RWLock!
│   ├── dependency_checker.py ← dual GPU check!
│   └── plugin_errors.py
├── sandbox/
│   ├── __init__.py
│   ├── sandbox_runner.py
│   ├── timeout.py ← 60s default
│   └── memory_guard.py ← 1GB default
├── lifecycle/
│   ├── __init__.py
│   ├── lifecycle_state.py
│   └── lifecycle_manager.py
└── health/
    ├── __init__.py
    ├── health_model.py
    └── health_router.py

tests/
├── test_plugin_loader/
├── test_plugin_health_api/
├── test_plugin_sandbox/
├── test_tool_runner/
└── test_videotracker_stability/
```

---

## Part 8: Pre-Commit Command (MANDATORY)

Before EVERY commit:

```bash
cd server && uv run pytest -v
cd server && uv run ruff check --fix app/
cd server && uv run mypy app/ --no-site-packages
cd web-ui && npm run type-check && npm run lint
```

---

## Links

- [Architecture](.ampcode/04_PHASE_NOTES/Phase_11/PHASE_11_ARCHITECTURE.md)
- [Implementation Plan](.ampcode/04_PHASE_NOTES/Phase_11/PHASE_11_IMPLEMENTATION_PLAN.md)
- [Concrete Implementation](.ampcode/04_PHASE_NOTES/Phase_11/PHASE_11_CONCRETE_IMPLEMENTATION.md)
- [Developer Contract](.ampcode/04_PHASE_NOTES/Phase_11/PHASE_11_DEVELOPER_CONTRACT.md)
- [Completion Criteria](.ampcode/04_PHASE_NOTES/Phase_11/PHASE_11_COMPLETION_CRITERIA.md)
- [Authoritative Decisions](.ampcode/04_PHASE_NOTES/Phase_11/PHASE_11_NOTES_01.md)
- [Governance Model](.ampcode/04_PHASE_NOTES/Phase_11/PHASE_11_NOTES_02.md)

---

**This document is AUTHORITATIVE. All decisions are locked in.**

**No guessing. No ambiguity. No deviations.**
