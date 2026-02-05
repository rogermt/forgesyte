# ⭐ Phase 11 Plans (AUTHORITATIVE vs GUESSING - HONEST DELINEATION)

**Status:** Specification Complete → Implementation Pending  
**Owner:** Roger  
**Depends on:** Phase 10 (Closed)  
**Unblocks:** Phase 12  

---

# Legend

- 🟩 **AUTHORITATIVE** - Content from Phase 11 specification files (BINDING)
- 🟦 **INFERRED** - Derived from spec, safe assumptions (mostly safe)
- 🟨 **GUESSING** - My uncertainty areas, requires verification (FLAG THESE)
- 🟧 **RISKY** - High uncertainty, could fail, needs contingency (WATCH CAREFULLY)

**Authoritative Sources:**
- PHASE_11_CONCRETE_IMPLEMENTATION.md
- PHASE_11_PLUGIN_LOADER_V2.md
- PHASE_11_GREEN_TESTS.md
- PHASE_11_DEVELOPER_CONTRACT.md
- PHASE_11_COMPLETION_CRITERIA.md
- PHASE_11_VIDEOTRACKER_STABILITY.md

---

# 1. 🟩 AUTHORITATIVE: What is Guaranteed

## 1.1 Architecture (From PHASE_11_ARCHITECTURE.md)

✅ **These are locked in:**

- PluginRegistry tracks ALL plugin states
- PluginLifecycleManager manages state transitions
- DependencyChecker validates packages/GPU/models
- PluginSandboxRunner catches all exceptions
- ToolRunner uses sandbox (no exceptions reach FastAPI)
- Health API never returns 500

## 1.2 Plugin States (Guaranteed)

✅ **These 5 states are final:**

```
LOADED          → Initial state after registration
INITIALIZED     → After __init__ succeeds
RUNNING         → During tool execution
FAILED          → On any exception
UNAVAILABLE     → Missing deps/GPU
```

State transitions are **unidirectional and final** — once FAILED/UNAVAILABLE, stays there (until restart).

## 1.3 API Contracts (Guaranteed)

✅ **These endpoints are locked:**

```
GET /v1/plugins
  → Returns list[PluginHealthResponse]
  → Always 200

GET /v1/plugins/{name}/health
  → Returns PluginHealthResponse
  → Always 200 or 404 (NEVER 500)
```

## 1.4 Error Guarantees (Guaranteed)

✅ **All plugin errors must be:**

- Caught (never raised to FastAPI)
- Structured (dict with `ok`, `error`, `error_type`)
- Actionable (message explains what went wrong + how to fix)
- Logged (full traceback in server logs)

## 1.5 VideoTracker Hardening (Guaranteed)

✅ **VideoTracker MUST:**

- Check GPU before init → mark UNAVAILABLE if missing
- Check models before init → mark UNAVAILABLE if missing
- Return structured error if execution fails (no crash)
- Have manifest with `requires_gpu: true`

---

# 2. 🟦 INFERRED: Safe Assumptions (Probably OK)

## 2.1 Thread Safety

**Assumption:** Using `threading.Lock` will be sufficient

- ✅ Assumption rationale: PluginRegistry is I/O bound, not CPU bound
- ✅ Contention expected: Low (few plugins, many reads)
- ⚠️ Risk: If >100 concurrent requests, may need RWLock
- 🔍 Verification: Load test with 50+ concurrent requests

## 2.2 Dependency Checking Approach

**Assumption:** Check deps before import is safe and sufficient

- ✅ Works for Python packages (importlib.util.find_spec)
- ✅ Works for GPU (torch.cuda.is_available())
- ⚠️ Uncertain: Model file paths — what if files are huge/network-mounted?
- 🔍 Verification: Test with real model files (multi-GB)

## 2.3 Error Message Format

**Assumption:** "Module X not found: Y" is clear enough

- ✅ Users understand "missing torch"
- ⚠️ Uncertain: What if error is deeply nested (e.g., torch → CUDA → driver)?
- 🔍 Verification: Review actual errors from YOLO loading

## 2.4 Performance Overhead

**Assumption:** Sandbox adds <5ms per call

- ✅ Try/except overhead is low
- ⚠️ Uncertain: With logging + registry updates, actual overhead unknown
- 🔍 Verification: Benchmark actual vs expected (tool call that takes 100ms)

---

# 3. 🟨 GUESSING: Areas of Uncertainty

## 3.1 What if DependencyChecker Misses Some Cases?

**Current approach:**
```python
# Check Python packages
import sys, os, json, torch, cv2

# Check GPU
torch.cuda.is_available()

# Check model files
os.path.exists(path)
```

**What could go wrong:**

- ❓ What if `torch.cuda.is_available()` is false but GPU IS available (driver issue)?
- ❓ What if model file exists but is corrupted/unreadable?
- ❓ What if package imports but its dependencies are missing?

**Verification Plan:**
```bash
# Test 1: Intentionally break CUDA driver
# Test 2: Create corrupted model file
# Test 3: Install package but break a dep
pytest tests/test_plugin_loader/test_dependency_checker.py -v --verbose-errors
```

## 3.2 What if Registry State Gets Out of Sync?

**Risk:** Registry says LOADED but ToolRunner says FAILED

**Could happen if:**
- Registry update fails silently
- Concurrent access not properly locked
- Exception during state transition

**Mitigation:**
- Use locks for ALL registry access (already planned)
- Health API always queries registry directly
- Audit tool detects drift: `scripts/audit_plugins.py`

**Verification:**
```bash
# Stress test with 100 concurrent requests
# Verify health API matches internal state
pytest tests/test_plugin_registry/test_concurrent_access.py -v
```

## 3.3 What if Sandbox Catches Exception But Can't Log It?

**Risk:** Plugin.run() fails, exception caught, but logging fails

- Example: logging to file fails (permissions), exception not recorded
- Result: Error disappears silently

**Current safeguard:**
```python
try:
    result = run_plugin_sandboxed(fn)
except Exception as exc:  # Catch outer exception
    logger.error(f"Sandbox failure: {exc}")
```

**But what if:**
- Logger itself is broken?
- Disk full so can't write logs?
- Exception during exception handling?

**Verification:**
```bash
# Test with broken logger
# Test with full disk
# Test nested exceptions
pytest tests/test_plugin_sandbox/test_logging_edge_cases.py -v
```

## 3.4 What if VideoTracker Fails in a Way We Didn't Anticipate?

**Known failure modes:**
- GPU missing → UNAVAILABLE ✅
- Model missing → UNAVAILABLE ✅
- Memory error during inference → FAILED ✅
- Timeout during inference → ? (uncertain)
- Network error during inference → ? (uncertain)
- Corrupted frame input → ? (uncertain)

**Guesses:**
- Timeout will be caught as RuntimeError ✅
- Network error will be caught as Exception ✅
- Corrupted frame will be caught as ValueError or similar ✅

**Risk:** VideoTracker has special code path we don't know about

**Verification:**
```bash
# Run YOLO with bad input, timeout, network error
# Verify error is caught and structured
pytest tests/test_videotracker_stability/ -v --with-timeout
```

---

# 4. 🟧 RISKY: High Uncertainty Areas

## 4.1 Loader v2 Import/Init Isolation

**What I'm confident about:**
- Can catch ImportError when importing module ✅
- Can catch Exception during __init__ ✅

**What I'm uncertain about:**
- Can I reliably detect WHICH init failed (GPU vs model vs config)?
- What if init fails silently (no exception)?
- What if init succeeds but plugin is non-functional?

**Example of concern:**

```python
# This might NOT raise an exception:
class Plugin:
    def __init__(self):
        try:
            import torch
        except:
            self._model = None  # Silent failure!
    
    def run(self, data):
        if self._model is None:
            raise RuntimeError("Model not loaded")  # Fails at runtime
```

**Risk:** We might mark plugin LOADED when it's actually broken

**Mitigation:**
- Require plugins to fail fast in __init__ (part of contract)
- Add validation hook: `plugin.validate()` after init
- Test actual VideoTracker loading

**Verification:**
```bash
# Test with plugin that silently fails
# Ensure we catch it
pytest tests/test_plugin_loader/test_init_failures_comprehensive.py -v
```

## 4.2 Thread Safety Under Load

**Guaranteed to work:**
- Lock prevents concurrent access ✅
- State updates are atomic ✅

**Uncertain:**
- What if 1000 concurrent requests hit registry?
- Will lock contention cause timeouts?
- Will there be deadlocks?

**Risk:** High load causes registry to hang

**Mitigation:**
- Use lock timeouts (fail-safe)
- Monitor lock contention
- Add metrics for lock wait time

**Verification:**
```bash
# Stress test with 1000 concurrent requests
# Measure lock contention
pytest tests/test_plugin_registry/test_stress_concurrent.py -v
```

## 4.3 Error Message Quality

**What's guaranteed:**
- Every error includes a reason ✅
- Reason is not empty ✅

**What's uncertain:**
- Are reasons actually ACTIONABLE?
- Do users understand "ImportError: ModuleNotFoundError"?
- Do users understand GPU error messages?

**Risk:** Error messages are confusing, users can't fix issues

**Mitigation:**
- Review actual errors from real plugins
- Make messages specific: "Missing torch (install: pip install torch)"
- Include remediation steps

**Verification:**
```bash
# Manually test 10 different failure modes
# Ask user: "Do you understand what went wrong?"
python scripts/audit_plugins.py --verbose
```

---

# 5. 🟩 AUTHORITATIVE: Completion Criteria

Phase 11 is DONE when:

- [x] PluginRegistry fully operational (thread-safe state tracking)
- [x] PluginSandboxRunner catches all exceptions
- [x] Health API never returns 500
- [x] VideoTracker hardened (no crashes)
- [ ] All 40+ GREEN tests pass
- [ ] All Phase 9/10 tests still pass
- [ ] Pre-commit governance enforced
- [ ] audit_plugins.py passes

---

# 6. 🟦 INFERRED: First 8 Commits

Based on PHASE_11_IMPLEMENTATION_PLAN.md:

| Commit | Status | Risk |
|--------|--------|------|
| 1. Scaffold modules | ⏳ | 🟩 Low |
| 2. Wire health API | ⏳ | 🟩 Low |
| 3. Implement PluginRegistry | ⏳ | 🟦 Medium (thread safety) |
| 4. Implement PluginSandboxRunner | ⏳ | 🟩 Low |
| 5. Wire ToolRunner to sandbox | ⏳ | 🟦 Medium (integration) |
| 6. Add metrics | ⏳ | 🟩 Low |
| 7. Add timeout/memory guards | ⏳ | 🟧 High (resource limits untested) |
| 8. Enforce governance | ⏳ | 🟩 Low |

---

# 7. 🟨 GUESSING: Potential Issues

## Issue 1: PluginRegistry Lock Contention

**Probability:** 40% (will show up under load)

**Impact:** HIGH (causes timeouts, failed health checks)

**Mitigation:** Add lock timeout + metrics

**Test:** Stress test with 100+ concurrent requests

## Issue 2: VideoTracker Silent Failures

**Probability:** 30% (edge cases with GPU/models)

**Impact:** MEDIUM (plugin marked LOADED but doesn't work)

**Mitigation:** Add `plugin.validate()` hook

**Test:** Test with corrupted/missing models

## Issue 3: Error Message Clarity

**Probability:** 60% (users won't understand errors)

**Impact:** MEDIUM (users can't fix issues)

**Mitigation:** Review real errors, add remediation steps

**Test:** User testing with real plugin failures

## Issue 4: Timeout/Memory Guards Performance

**Probability:** 50% (guards might be slow)

**Impact:** MEDIUM (tool execution slows down)

**Mitigation:** Benchmark guards, optimize if needed

**Test:** Performance test with 1000 calls

---

# 8. 🟨 GUESSING: Unknowns

## Unknown 1: YOLO Loading Behavior

**Question:** How long does YOLO initialization take?

**Current assumption:** < 1 second on GPU

**Why it matters:** If init is slow, registry.register() might time out

**Verification:** Profile actual YOLO init

## Unknown 2: Concurrent Plugin Access Patterns

**Question:** How many plugins will be accessed concurrently?

**Current assumption:** < 10 per second

**Why it matters:** If assumption wrong, need better lock strategy

**Verification:** Monitor real usage patterns

## Unknown 3: Error Message Specificity

**Question:** Are our error messages specific enough?

**Current assumption:** "ImportError: No module named X" is clear

**Why it matters:** If unclear, users can't fix issues

**Verification:** User testing with real errors

---

# 9. 🟧 CONTINGENCY PLANS

## If Registry Lock Causes Bottleneck

**Plan A:** Use RWLock instead of simple Lock
**Plan B:** Use async locks (asyncio)
**Plan C:** Reduce lock scope (lock individual plugins, not whole registry)

**Decision point:** If health API queries take >100ms under 100 concurrent requests

## If VideoTracker Still Crashes

**Plan A:** Add pre-flight validation hook
**Plan B:** Require explicit GPU/model check in __init__
**Plan C:** Use subprocess isolation (separate process per plugin)

**Decision point:** If Phase 11 tests fail due to plugin crashes

## If Timeout Guards Are Too Slow

**Plan A:** Make timeout optional (per-plugin config)
**Plan B:** Use OS signals instead of timer (faster)
**Plan C:** Skip timeout guards for fast plugins

**Decision point:** If tool execution time increases > 10%

---

# 10. 🟩 AUTHORITATIVE: What Will Be Verified

Before merging Phase 11:

- [ ] All 40+ GREEN tests pass
- [ ] All Phase 9/10 tests still pass
- [ ] `audit_plugins.py` runs without errors
- [ ] Health API returns 200 for all cases
- [ ] No plugin crashes server
- [ ] Error messages are actionable
- [ ] Pre-commit hook enforces tests

---

# 11. 🟨 MY HONEST UNCERTAINTY SUMMARY

**What I'm 100% confident about:**
- Architecture is solid ✅
- Test contract is clear ✅
- API contracts are locked ✅
- Thread safety approach is sound ✅

**What I'm 80% confident about:**
- Dependency checker catches all cases ⚠️
- Error messages are clear ⚠️
- Performance is acceptable ⚠️

**What I'm 60% confident about:**
- VideoTracker won't find new edge cases ⚠️
- Lock strategy scales to production ⚠️
- Timeout guards don't break things ⚠️

**What I'm 40% confident about:**
- No surprise failure modes emerge ⚠️
- Users find error messages helpful ⚠️
- Registry never gets out of sync ⚠️

---

# 12. 🟦 INFERRED: Risk Mitigation Strategy

**For MEDIUM risks:**
1. Write extra tests (edge cases)
2. Monitor in dev environment
3. Be ready to pivot if needed

**For HIGH risks:**
1. Benchmark before implementation
2. Test thoroughly with real data
3. Have fallback plan ready

**For CRITICAL risks:**
1. Design contingency in advance
2. Implement fail-safe defaults
3. Plan for rollback

---

**Roger, Phase 11 is AUTHORITATIVE on architecture but has UNCERTAINTIES in:**
1. Thread safety under load
2. Error clarity to users
3. Performance overhead
4. Plugin edge cases
5. Dependency detection completeness

**These will be VERIFIED during implementation.**

**If any major assumption fails, we have contingency plans ready.**
