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
└── execution-ci.yml ← CI pipeline
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

**Test:** `tests/execution/test_tool_runner.py`

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
- `tests/execution/test_plugin_execution_service.py`
- `tests/execution/test_job_execution_service.py`
- `tests/execution/test_analysis_execution_service.py`

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

### Step 7: Documentation + Diagrams

**Purpose:** Codify the execution governance system so it's impossible for future contributors to misunderstand or drift.

---

## 1. Execution Governance Documentation

### File: `docs/design/execution-governance.md`

This document becomes the **single source of truth** for the execution subsystem.

### Sections to include:

#### A. Overview
- What the execution layer does
- Why governance exists
- High‑level flow diagram

#### B. Plugin Execution Architecture
- ToolRunner
- PluginExecutionService
- JobExecutionService
- AnalysisExecutionService
- API routes

#### C. Lifecycle States
- LOADED
- INITIALIZED
- RUNNING
- FAILED
- UNAVAILABLE

#### D. Job Lifecycle
- PENDING → RUNNING → SUCCESS/FAILED

#### E. Validation Rules
- Input validation
- Output validation

#### F. Error Envelope Format
- Structured error wrapping
- Error types and classification

#### G. Scanner Rules
- No direct plugin.run
- ToolRunner invariants
- Valid lifecycle states only

#### H. CI Pipeline
- Scanner
- Phase 11 tests
- Execution tests

#### I. Developer Responsibilities
- How to add a plugin
- How to add a new execution endpoint
- How to debug execution failures

#### J. File Locations
- All key file paths organized by function

---

## 2. Architecture Diagrams

### File: `docs/design/execution-architecture.drawio`

Include diagrams for:

#### A. Execution Flow Diagram
```
API → AnalysisExecutionService → JobExecutionService → PluginExecutionService → ToolRunner → Plugin
```

#### B. Job Lifecycle Diagram
```
PENDING → RUNNING → SUCCESS/FAILED
```

#### C. Registry State Diagram
```
LOADED → INITIALIZED / FAILED / UNAVAILABLE
```

#### D. Error Envelope Flow
```
Exception → Envelope → API → Client
```

#### E. Scanner Enforcement Diagram
```
Developer → Code → Scanner → CI → Merge
```

### Alternative: ASCII Diagrams

```
+--------+        +---------------------------+        +---------------------------+
| Client |  HTTP  |        API Route          |        |  AnalysisExecutionService |
|        +------->|   /v1/analyze-execution   +------->+  (sync + async orchestration)
+--------+        +---------------------------+        +---------------------------+
                                                           |
                                                           v
                                                +---------------------------+
                                                |    JobExecutionService    |
                                                | PENDING→RUNNING→SUCCESS/  |
                                                |           FAILED          |
                                                +---------------------------+
                                                           |
                                                           v
                                                +---------------------------+
                                                |  PluginExecutionService   |
                                                |  delegates to ToolRunner  |
                                                +---------------------------+
                                                           |
                                                           v
                                                +---------------------------+
                                                |        ToolRunner         |
                                                | validation + metrics +    |
                                                |  lifecycle + envelopes    |
                                                +---------------------------+
                                                           |
                                                           v
                                                +---------------------------+
                                                |          Plugin           |
                                                |        .run(payload)      |
                                                +---------------------------+


                          +---------------------------------------------+
                          |             Plugin Registry                 |
                          |  state, success/error counts, timings,     |
                          |  last_used, etc. (updated by ToolRunner)   |
                          +---------------------------------------------+


+---------------------------+                 +---------------------------+
|   Mechanical Scanner      |                 |   Execution Governance    |
| scripts/scan_execution_   |  enforces       |           CI              |
| violations.py             +---------------->+ .github/workflows/       |
| - no direct plugin.run    |                 |   execution-ci.yml        |
| - ToolRunner invariants   |                 | - scanner + tests on PR   |
+---------------------------+                 +---------------------------+
```

---

## 3. Developer Onboarding Guide

### File: `docs/execution-onboarding.md`

Include:

#### A. Core Mental Model
All plugin execution must follow this exact path:
```
API → AnalysisExecutionService → JobExecutionService → PluginExecutionService → ToolRunner → Plugin
```

**Never call plugin.run() directly. Always go through ToolRunner.**

#### B. Running Tests
```bash
# Run all tests
pytest server/tests -v

# Run execution governance tests
pytest server/tests/execution -v
```

#### C. Running the Mechanical Scanner
```bash
python scripts/scan_execution_violations.py
```

#### D. Where Things Live
| Area | Path |
|------|------|
| Execution services | `server/app/services/execution/` |
| ToolRunner | `server/app/plugins/runtime/tool_runner.py` |
| Execution API | `server/app/api/routes/analysis_execution.py` |
| Execution tests | `server/tests/execution/` |
| Scanner | `scripts/scan_execution_violations.py` |
| CI workflow | `.github/workflows/execution-ci.yml` |
| Governance docs | `docs/design/execution-governance.md` |

#### E. Adding or Modifying a Plugin
1. Implement `.run(payload: dict) -> dict`
2. Register the plugin in the registry
3. Do NOT call `plugin.run()` directly
4. Let ToolRunner handle validation, metrics, lifecycle, error envelopes

#### F. Adding or Modifying Execution Behavior
- Use `AnalysisExecutionService` for API-facing orchestration
- Use `JobExecutionService` for job lifecycle
- Use `PluginExecutionService` to reach ToolRunner
- Never bypass ToolRunner

#### G. Debugging Execution Issues
1. Check job state (PENDING/RUNNING/SUCCESS/FAILED)
2. Check error envelope (type, message, plugin, details)
3. Check registry metrics (success_count, error_count, timings)
4. Run scanner + tests

#### H. Before Opening a PR
```bash
python scripts/scan_execution_violations.py
pytest server/tests -v
pytest server/tests/execution -v
```

---

## 4. Phase 12 Wrap-Up Document

### File: `docs/phase12-wrap-up.md`

#### A. What Phase 12 Achieved
- Repaired execution architecture
- Restored ToolRunner invariants
- Corrected lifecycle state usage
- Added input/output validation
- Added structured error envelopes
- Added job lifecycle system
- Added synchronous + async execution paths
- Added execution API routes
- Added mechanical scanner
- Added CI enforcement
- Added documentation + diagrams

#### B. Key Guarantees Now Enforced
- Single execution path (ToolRunner)
- No direct plugin.run() calls
- Lifecycle states are correct and enforced
- Metrics always updated
- Validation always applied
- Errors always wrapped
- Jobs always tracked
- Scanner prevents regressions
- CI blocks violations

#### C. What Changed in the Repo
- New execution services
- New API routes
- New tests
- New scanner
- New CI workflow
- New documentation
- New diagrams

#### D. Developer Guidance
- How to add plugins
- How to add execution features
- How to run scanner
- How to interpret job states
- How to debug execution failures

#### E. Future Enhancements (Optional)
- Async worker queue
- Persistent job storage
- Plugin sandboxing
- Plugin timeouts
- Resource limits

---

## 5. Repository Audit Checklist

### File: `docs/repo-audit-checklist.md`

#### A. Directory Structure
- [ ] No phase‑named folders
- [ ] Execution code lives in functional directories
- [ ] Tests live under `server/tests/execution/`
- [ ] Documentation lives under `docs/`

#### B. Execution Architecture
- [ ] ToolRunner is the only caller of plugin.run()
- [ ] PluginExecutionService delegates correctly
- [ ] JobExecutionService manages lifecycle correctly
- [ ] AnalysisExecutionService exposes sync + async paths
- [ ] API routes match service methods

#### C. Lifecycle States
- [ ] Only LOADED, INITIALIZED, RUNNING, FAILED, UNAVAILABLE
- [ ] No SUCCESS/ERROR lifecycle states
- [ ] Registry updates state correctly

#### D. Validation + Error Envelope
- [ ] Input validation always runs
- [ ] Output validation always runs
- [ ] Error envelope always wraps exceptions
- [ ] API never returns raw exceptions

#### E. Scanner
- [ ] Scanner exists
- [ ] Scanner enforces all invariants
- [ ] Scanner passes locally
- [ ] Scanner blocks regressions

#### F. CI Pipeline
- [ ] CI workflow exists
- [ ] Scanner runs first
- [ ] Phase 11 tests run
- [ ] Execution tests run
- [ ] CI fails on violations

#### G. Documentation
- [ ] Execution governance doc exists
- [ ] Architecture diagrams exist
- [ ] Onboarding guide exists
- [ ] README updated

#### H. Developer Experience
- [ ] Running tests is easy
- [ ] Running scanner is easy
- [ ] Adding plugins is documented
- [ ] Adding execution features is documented

---

## 6. Update README.md

Update root `README.md` with:

- Link to execution governance docs (`docs/design/execution-governance.md`)
- Link to architecture diagrams (`docs/design/execution-architecture.drawio`)
- Link to onboarding guide (`docs/execution-onboarding.md`)
- Link to CI workflow (`.github/workflows/execution-ci.yml`)
- Quickstart for running scanner + tests

---

## 7. Commands to Verify Documentation

```bash
# Verify documentation files exist
ls -la docs/design/execution-governance.md
ls -la docs/design/execution-architecture.drawio
ls -la docs/execution-onboarding.md
ls -la docs/phase12-wrap-up.md
ls -la docs/repo-audit-checklist.md

# Run all verification
python scripts/scan_execution_violations.py
pytest server/tests/execution -v
pytest server/tests -v
```

---

## 8. Documentation Files Summary

| File | Purpose | Status |
|------|---------|--------|
| `docs/design/execution-governance.md` | Single source of truth | Create |
| `docs/design/execution-architecture.drawio` | Architecture diagrams | Create |
| `docs/execution-onboarding.md` | Developer quickstart | Create |
| `docs/phase12-wrap-up.md` | Phase 12 summary | Create |
| `docs/repo-audit-checklist.md` | Audit checklist | Create |
| `README.md` | Links to all docs | Update |

---

**This completes Step 7: Documentation + Diagrams.**

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
