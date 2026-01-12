# Project Learnings & Work Unit Documentation

**Last Updated**: 2026-01-12 11:00  
**Current Project**: Server-WebUI Integration Bug Fix  
**Status**: Starting WU-01  

---

## WU-1: Integration Test Foundation

**Status**: 🟡 In Progress  
**Started**: 2026-01-12  
**Estimated Duration**: 1.5 hours  
**Target Completion**: Create integration test infrastructure

### Objectives
- Create `web-ui/src/integration/server-api.integration.test.ts`
- Mock actual server response formats (not just API client)
- Test all 7 API endpoints against expected server responses
- Document response format for each endpoint (actual vs expected)
- No test failures - all tests should pass or be clearly documented

### Key Tasks
1. Capture server endpoint responses
2. Create integration tests for each endpoint
3. Verify response format matches WebUI client expectations
4. Document any mismatches found

### Current Progress
- [x] Review existing WebUI test structure
- [x] Identified 7 key endpoints to test
- [x] Analyzed client.ts expectations
- [ ] Create integration test file
- [ ] Mock server responses
- [ ] Run tests

---

## Previous Work: Python Standards Refactoring (Complete ✅)

### Key Learnings from Full Refactoring Project

#### Lessons from Workflow Errors & Coverage (WU-Fix)

**What Went Well**:
- Rapid diagnosis of test failures
- Targeted fixes using proper async mocking (AsyncMock for httpx)
- Coverage boost from 68% to 80.82% via 5 new service test files
- All standards maintained in new code

**Critical Learnings**:
1. **Tests are code consumers** - When APIs change (JobStore signature), ALL dependent tests must be updated
2. **Async mocking requires AsyncMock** - Standard MagicMock cannot be awaited; httpx.AsyncClient needs AsyncMock
3. **Logging tests need caplog.records** - caplog.text doesn't include `extra` context dict; use `caplog.records` to verify structured logging
4. **Coverage is enforced locally** - CI requires 80%; local must match or tests pass locally but fail in CI

**Blockers Discovered**:
- None - all issues fixed and merged

---

#### Critical Insight: Local ≠ CI Without Matching Configuration

**The Core Problem**:
Local test runs used different configuration than CI:
- Local: No coverage threshold enforcement
- CI: `--fail-under=80` enforced strictly
- Result: Tests passed locally (68%) but failed in CI

**The Solution (Documented in AGENTS.md)**:
```bash
# Local test must run exact same command as CI:
cd server
uv sync
cd ..
uv run pre-commit run --all-files  # black, ruff, mypy
cd server
PYTHONPATH=. uv run mypy app/ --no-site-packages
uv run pytest --cov=app --cov-report=term-missing
uv run coverage report --fail-under=80  # MUST PASS
```

This ensures local environment matches CI exactly before pushing.

---

#### Architecture Patterns from Refactoring

**Service Layer Pattern** (Applied 13 times):
```python
# 1. Define Protocol (interface)
class PluginRegistry(Protocol):
    def list_plugins(self) -> list[dict]: ...

# 2. Create Service
class PluginManagementService:
    def __init__(self, registry: PluginRegistry): ...
    def list_all(self) -> list[dict]: ...

# 3. Dependency Injection in FastAPI
async def get_plugins(
    service: PluginManagementService = Depends(...)
) -> dict:
    return {"plugins": service.list_all()}
```

**Benefits**: Testable (mock registry), decoupled (swappable implementations), maintainable

**Structured Logging Pattern** (Applied throughout):
```python
logger.info("operation", extra={"context": value, "id": id})
```

Not just text messages - semantic context for production debugging.

**Type Hints Everywhere**:
100% coverage on new/refactored code prevents silent failures.

---

#### Standards Applied in Python Refactoring

✅ **Separation of Concerns** - Service layer extracted from endpoints  
✅ **Protocol-Based Design** - All key abstractions use Protocol  
✅ **Retry Pattern** - Tenacity for external calls (ImageAcquisitionService)  
✅ **Structured Logging** - extra={} dict on all operations  
✅ **Specific Exceptions** - No generic catches  
✅ **Type Hints** - 100% coverage  
✅ **Docstrings** - Google-style with Args/Returns/Raises  
✅ **Path Management** - pathlib.Path throughout  
✅ **Health Checks** - /health endpoint implemented  
✅ **Input Validation** - Pydantic constraints  

---

## Current Issue: Server-WebUI Integration (Active 🔴)

### Problem Statement
After Python refactoring, WebUI receives 500 errors when calling server. Root cause: **API response format mismatch**.

### Evidence
- **Pre-refactoring**: WebUI worked
- **Post-refactoring**: Server endpoints changed response format
- **Example**: `getPlugins()` expects `{plugins: []}`, server may return different format

### Why Local Tests Didn't Catch This
1. **WebUI tests mock everything** - No real server calls
2. **Server tests don't include WebUI** - CI runs server tests, then webui tests separately
3. **No E2E testing** - CI doesn't verify server + webui work together

### Solution Plan
4 work units with integration testing at every level:
- WU-01: Create integration test infrastructure
- WU-02: Fix any response format mismatches
- WU-03: E2E testing (real server + webui)
- WU-04: Update CI to enforce integration testing

### Key Acceptance Criteria
✅ Integration tests reveal ALL format mismatches  
✅ No 500 errors when WebUI calls server  
✅ CI enforces both server AND webui tests  
✅ AGENTS.md requires full integration testing before commits  

---

## Tips for Future Work

**Before Committing ANY Changes**:
1. Run server test sequence (pre-commit + mypy + pytest + coverage)
2. Run webui test sequence (npm test)
3. Document any failures clearly
4. Do NOT commit if tests fail

**When Creating Integration Tests**:
1. Test REAL interfaces, not mocks
2. Capture actual server responses
3. Verify client can parse responses
4. Document expected vs actual format

**When Fixing Server Responses**:
1. Check WebUI client expectations first
2. Update server if format differs
3. Verify integration tests pass
4. Run E2E test with real server

**For Code Review**:
1. Verify both server and webui tests pass
2. Check coverage didn't drop
3. Ensure no integration issues
4. Run integration tests locally

---

## References

- **Bug Report**: `/docs/issues/SERVER_WEBUI_INTEGRATION_BUG.md`
- **Fix Plan**: `/docs/work-tracking/SERVER_WEBUI_INTEGRATION_PLAN.md`
- **AGENTS.md**: Updated with CI-matching workflow
- **Workflow File**: `.github/workflows/lint-and-test.yml` (defines CI checks)
