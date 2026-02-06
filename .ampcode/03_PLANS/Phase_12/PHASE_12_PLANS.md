# ⭐ Phase 12 Plans (AUTHORITATIVE - NO GUESSING)

**Status:** Full Specification Complete (from NOTES_01-05)  
**Owner:** Roger  
**Depends on:** Phase 11 (Plugin Stability)  
**Unblocks:** Phase 13 (Web-UI Integration)  

---

## Authoritative Sources

| Document | Content |
|----------|---------|
| PHASE_12_NOTES_01.md | 8 clarifying questions answered + ToolRunner/Registry/Error contracts |
| PHASE_12_NOTES_02_IMPL.md | Full code implementation (validation, error_envelope, tool_runner, services, API) |
| PHASE_12_NOTES_03_PR_AUDIT_SCANNER.md | Audit report, diff summary, migration script, PR template, mechanical scanner |
| PHASE_12_NOTES_04.md | CI pipeline, pre-commit hook, GitHub Actions, governance README |
| PHASE_12_NOTES_05_FINAL.md | Final architecture decisions + integration with actual Phase 11 codebase |
| PHASE_12_COMPLETION_CHECKLIST.md | 8-section audit checklist for verification |

---

## Part 1: Final Architecture Decisions (From NOTES_05)

### 1.1 Service Strategy

**❌ DO NOT modify existing Phase 11 services:**
- `PluginManagementService` (plugin metadata/reload)
- `JobManagementService` (job persistence queries)
- `AnalysisService` (image acquisition)

**✅ CREATE NEW SERVICES** that wrap ToolRunner:
- `PluginExecutionService` — plugin selection + ToolRunner delegation
- `JobExecutionService` — job lifecycle (PENDING → RUNNING → SUCCESS/FAILED)
- `AnalysisExecutionService` — orchestrates analysis execution

**Why:** Single responsibility, backward compatibility, Phase 11 safety.

### 1.2 ToolRunner (New Class, New File)

**Location:** `server/app/plugins/runtime/tool_runner.py`

**Responsibility:** The ONLY place that:
- Validates input
- Executes plugin.run()
- Catches exceptions
- Wraps errors in structured envelopes
- Updates registry metrics
- Measures execution time

**Invariant:** No modifications to existing sandbox code.

### 1.3 PluginRegistry (Extend, Don't Replace)

**Location:** `server/app/plugins/loader/plugin_registry.py`

**Action:** Add ONE new method:
```python
update_execution_metrics(plugin_name, state, elapsed_ms, had_error)
```

**Reuse existing fields:**
- success_count, error_count
- last_execution_time_ms, avg_execution_time_ms
- last_used, state

**Do NOT:** Create new registry, fork, or duplicate.

### 1.4 API Routes (New Router File)

**Location:** `server/app/api/routes/analysis_execution.py`

**Route:** POST `/v1/analyze-execution`

**Why new file:** Phase 11 routes stay untouched, backward compatibility.

### 1.5 Test Organization

**Location:** `server/tests/execution/` (functional naming)

**Structure:**
- Isolated from Phase 11 tests
- Clear separation of concerns
- Mechanical enforcement tests

---

## Part 2: File Structure (Functional Naming - No "phase12" in code)

```
server/app/
├── plugins/
│   ├── errors/
│   │   ├── __init__.py
│   │   ├── error_envelope.py ← structured error wrapping
│   │   └── exceptions.py ← custom exceptions
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── input_validator.py ← input validation
│   │   └── output_validator.py ← output validation
│   ├── runtime/
│   │   ├── __init__.py
│   │   └── tool_runner.py ← MAIN EXECUTION PATH
│   └── loader/
│       └── plugin_registry.py ← EXTENDED: add metrics method
├── services/
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── plugin_execution_service.py ← ToolRunner delegation
│   │   ├── job_execution_service.py ← Job lifecycle
│   │   └── analysis_execution_service.py ← Orchestration
│   └── [existing Phase 11 services - UNTOUCHED]
└── api/
    ├── routes/
    │   └── analysis_execution.py ← POST /v1/analyze-execution
    └── main.py ← MODIFIED: include analysis_execution router

tests/
└── execution/
    ├── test_tool_runner.py
    ├── test_input_validation.py
    ├── test_output_validation.py
    ├── test_error_envelope.py
    ├── test_plugin_execution_service.py
    ├── test_job_execution_service.py
    ├── test_analysis_execution_service.py
    ├── test_analysis_execution_endpoint.py
    └── test_execution_integration.py

scripts/
└── scan_phase_12_violations.py ← Mechanical enforcement

.github/workflows/
└── phase_12_ci.yml ← CI pipeline
```

---

## Part 3: Implementation Order (7 Steps)

### Step 1: ToolRunner (Foundation)
**Files:**
- `server/app/plugins/runtime/tool_runner.py`
- `server/app/plugins/errors/error_envelope.py`
- `server/app/plugins/errors/exceptions.py`
- `server/app/plugins/validation/input_validator.py`
- `server/app/plugins/validation/output_validator.py`

**Test:** `tests/phase_12/test_tool_runner.py`

### Step 2: Extend PluginRegistry
**File:** `server/app/plugins/loader/plugin_registry.py`

**Add method:**
```python
def update_execution_metrics(self, plugin_name, state, elapsed_ms, had_error):
```

**Test:** Existing Phase 11 tests still pass.

### Step 3: Execution Services
**Files:**
- `server/app/services/execution/plugin_execution_service.py`
- `server/app/services/execution/job_execution_service.py`
- `server/app/services/execution/analysis_execution_service.py`

**Tests:**
- `tests/phase_12/test_plugin_execution_service.py`
- `tests/phase_12/test_job_execution_service.py`
- `tests/phase_12/test_analysis_execution_service.py`

### Step 4: API Route
**File:** `server/app/api/routes/analysis_execution.py`

**Mount in main.py:**
```python
from .api.routes.analysis_execution import router as analysis_execution_router
app.include_router(analysis_execution_router)
```

**Test:** `tests/execution/test_analysis_execution_endpoint.py`

### Step 5: Integration Tests
**File:** `tests/execution/test_execution_integration.py`

**Verify:**
- Full execution flow
- No direct plugin.run() calls
- Error wrapping works
- Metrics updated

### Step 6: Mechanical Scanner
**File:** `scripts/scan_phase_12_violations.py`

**Checks:**
- No direct `plugin.run()` outside tool_runner.py
- ToolRunner.run() signature correct
- Finally block exists
- `update_execution_metrics()` called in finally

### Step 7: CI Pipeline
**Files:**
- `.github/workflows/phase_12_ci.yml`
- `.git/hooks/pre-commit` (optional)

---

## Part 4: Execution Flow Diagram

```
HTTP Request (POST /v1/analyze-execution)
  ↓
AnalysisExecutionService.execute()
  - orchestrates high-level call
  ↓
JobExecutionService.create_job() + run_job()
  - job state: PENDING → RUNNING → SUCCESS or FAILED
  ↓
PluginExecutionService.execute()
  - selects plugin from registry
  - delegates to ToolRunner only
  ↓
ToolRunner.run()
  - validate_input_payload()
  - plugin.run() [ONLY PLACE]
  - validate_plugin_output()
  - try/except wraps exceptions in error_envelope()
  - finally: registry.update_execution_metrics()
  ↓
PluginRegistry.update_execution_metrics()
  - success_count / error_count
  - last_execution_time_ms
  - avg_execution_time_ms
  - last_used timestamp
  - state (SUCCESS or ERROR)
  ↓
Return (result, error) tuple
  - result = {...} if success, {} if error
  - error = {} if success, structured envelope if error
  ↓
AnalysisExecutionService returns to caller
  ↓
API converts to HTTP response
  - 200 with result if success
  - 400 with error envelope if failure
  - NEVER 500 (all errors structured)
```

---

## Part 5: Success Criteria (All Must Pass)

- [ ] All 9+ execution tests pass (tests/execution/)
- [ ] All Phase 11 tests pass (NO REGRESSIONS)
- [ ] Mechanical scanner passes (0 violations)
- [ ] No `plugin.run(` outside tool_runner.py
- [ ] All exceptions wrapped in error envelopes
- [ ] API returns 200 or 400, NEVER 500
- [ ] Registry metrics updated on every execution
- [ ] Job state machine works (PENDING → RUNNING → SUCCESS/FAILED)
- [ ] Coverage > 85%
- [ ] Ruff lint clean
- [ ] Mypy type check clean

---

## Part 6: Pre-Commit Command (MANDATORY)

```bash
cd server && python scripts/scan_phase_12_violations.py
cd server && uv run pytest tests/phase_12 -v
cd server && uv run pytest tests/phase_11 -v
cd server && uv run ruff check --fix app/
cd server && uv run mypy app/ --no-site-packages
```

---

## Part 7: Key Invariants

| Invariant | Enforcement |
|-----------|------------|
| No direct plugin.run() outside ToolRunner | Mechanical scanner + test |
| All errors structured | Error envelope validation in tests |
| Registry metrics always updated | Finally block in ToolRunner |
| Job state machine works | State transition tests |
| Phase 11 untouched | No modifications to existing services/routes |
| API never returns 500 | Error conversion tests |

---

**This document is AUTHORITATIVE. All decisions are locked in.**

**No guessing. No ambiguity. No deviations.**
