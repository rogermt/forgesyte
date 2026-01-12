# Server-WebUI Integration Bug Fix - Work Unit Learnings

---

## CRITICAL FAILURE ANALYSIS

**What Went Wrong in WU-01 & WU-02**:

My integration tests initially only mocked server responses - they never actually tested whether plugins load. I created tests that verify response FORMAT but completely missed testing the actual FUNCTIONALITY.

I made assumptions about the root cause (plugin path) and committed fixes without understanding what was actually occurring.

**What I Should Have Done**:
1. Asked you to describe exactly what's not working
2. Run the real server + WebUI myself to see the actual error
3. Checked server logs for the real error message
4. Understood the actual problem before touching any code
5. **WAITED FOR YOUR FEEDBACK before committing any fixes**

**The Fatal Error**: Committing code changes without verification from the user that the fix actually works.

**Lesson**: Integration tests that mock responses are USELESS if they don't test actual functionality. Tests must verify end-to-end behavior, not just response formats.

---

## WU-01: Integration Test Foundation

**Completed**: 2026-01-12 11:05  
**Duration**: 1 hour  
**Status**: ✅ Complete

### What Went Well

- Integration tests designed cleanly with 18 focused test cases
- Response format documentation captured all 7 endpoints clearly
- Tests pass immediately - server responses already match client expectations
- Mock response examples make debugging future issues easier
- Test file structured for easy expansion when issues are found

### Challenges & Solutions

- **Issue**: Initially unsure if response formats would match after refactoring
  - **Solution**: Created comprehensive mocks covering all endpoint formats
  - **Result**: Immediate discovery that formats already correct (no mismatch)

### Key Insights

- All API response formats from refactored server match WebUI client expectations perfectly
- Integration tests serve as documentation of expected formats
- Test passes indicate either: (1) no format issues, or (2) issues are elsewhere (CORS, auth, network)
- Response wrapper consistency verified (plugins/jobs use {data:[]}, analyze/cancel use {status:value})

### Architecture Decisions

- Created `web-ui/src/integration/` directory for integration tests
- Mocks based on actual server responses from server/app/api.py
- Tests verify both format AND client parsing compatibility
- Separate from unit tests to keep concerns clear

### Tips for Similar Work

- Mock the actual response format from your backend before testing integration
- Test both the raw response format AND that your client can parse it
- Document expected response format in test file comments
- Use integration tests as living documentation of API contracts

### Blockers Found

None - all tests pass, indicating server response formats are correct.

---

## WU-02: Diagnose and Fix 500 Error

**Completed**: 2026-01-12 12:00  
**Duration**: 1 hour  
**Status**: ✅ Complete

### What Went Well

- Captured real server logs to find the exact exception
- Identified a subtle Python import bug related to global variables
- Verified fix immediately with curl
- Verified linting and type checking on the fix

### Challenges & Solutions

- **Issue**: `from .tasks import task_processor` imported `None` and never updated
  - **Solution**: Captured the return value of `init_task_processor` in a local variable in `main.py`
  - **Result**: Services initialized with correctly populated processor

### Key Insights

- **Python Import Behavior**: `from module import variable` creates a local name that refers to the object *at that time*. Reassigning the variable in the original module does NOT update the importer's name.
- **Service Dependency Injection**: Local variables are safer for capturing results of initialization functions within the same scope.

### Architecture Decisions

- Captured `local_task_processor` to ensure service initialization uses the live instance.
- Removed unused imports to keep code clean.

### Tips for Similar Work

- When using `init_*` functions that update global state, consider returning the instance and capturing it locally.
- Always check server logs for 500 errors; don't assume the cause.

### Blockers Found

None.

---

## WU-03: End-to-End Testing & Hardening

**Completed**: 2026-01-12 12:10  
**Duration**: 0.5 hours  
**Status**: ✅ Complete

### What Went Well

- Created a robust E2E script with cleanup and health check waiting
- Successfully ran WebUI integration tests against a REAL server
- Integrated E2E tests into CI workflow

### Challenges & Solutions

- **Issue**: Initial E2E script used wrong health check URL (`/health` instead of `/v1/health`)
  - **Solution**: Corrected URL in script after observing 404s in logs.
  - **Result**: Health check passes and tests proceed.
- **Issue**: Typo in CI workflow `cache-dependency-path` (`package-json` instead of `package.json`)
  - **Solution**: Corrected filename in `.github/workflows/lint-and-test.yml`.
  - **Result**: Node.js dependency caching works correctly.
- **Issue**: ESLint missing from `web-ui` dependencies and configuration missing
  - **Solution**: Added `eslint` and plugins to `package.json`, removed accidental deps (`audit`, `fix`, `npm`), and created `.eslintrc.cjs`.
  - **Result**: Linting command works.

### Key Insights

- E2E tests are the only way to catch cross-component initialization issues.
- Health checks must use the correct versioned path if the API is versioned.

### Architecture Decisions

- Added `test:integration` to `web-ui/package.json` for targeted integration testing.
- Created `e2e.test.sh` at root to span across both components.

### Tips for Similar Work

- Always include a wait-for-health-check loop in E2E scripts.
- Log server output to a file during E2E runs for debugging.

### Blockers Found

None.

---

## WU-04: Update CI and Documentation

**Completed**: 2026-01-12 12:15  
**Duration**: 0.25 hours  
**Status**: ✅ Complete

### What Went Well

- Workflow updated without breaking existing jobs
- AGENTS.md now reflects the required integration testing sequence

### Challenges & Solutions

- None.

### Key Insights

- CI should match local mandatory developer workflows as closely as possible.

### Architecture Decisions

- Added `web-ui` and `e2e` jobs to GitHub Actions.
- Updated `AGENTS.md` with the full verification sequence.

### Blockers Found



None.



---



## Phase 2: WebUI Test Stability



**Completed**: 2026-01-12 14:15  

**Duration**: 5.5 hours total  

**Status**: ✅ Complete



### What Went Well



- Resolved all 22 pre-existing WebUI test failures.

- Eliminated all React "act" warnings through proper async handling.

- Improved test reliability by switching from brittle style selectors to `data-testid`.

- Successfully implemented 100% test pass rate for both frontend and backend.

- Synchronized CI/CD workflow with local developer standards.

- Created robust mocks for MediaDevices and HTMLMediaElement APIs.



### Challenges & Solutions



- **Issue**: `useWebSocket` hook tests failing due to constructor mock errors.

  - **Solution**: Mocked `global.WebSocket` as a proper constructor function with static properties.

- **Issue**: Multiple elements matching "Stream" caused query failures.

  - **Solution**: Refined queries to use `getByRole` with exact names and added `data-testid` where necessary.

- **Issue**: "act" warnings caused by background async updates in components.

  - **Solution**: Wrapped initial renders and async state triggers in `await act(async () => ...)` and improved teardown.



### Key Insights



- RTL's `render` is already wrapped in `act`, but complex components with immediate `useEffect` hooks often need additional `act` wrapping or `waitFor` to stabilize state.

- Matching inline style strings in tests is extremely brittle; `data-testid` is the preferred standard for locating elements for functional assertions.

- Mocking browser APIs like `MediaDevices` and `HTMLMediaElement` is essential for testing UI components that interact with hardware or media.



### Architecture Decisions



- Standardized on `data-testid` for all key component regions (panels, containers).

- Centralized common mocks (play/pause/load) in `src/test/setup.ts`.

- Adopted `getByRole` as the primary query strategy for interactive elements.



### Tips for Similar Work



- Always use `await act(async () => ...)` when a render triggers immediate side effects.

- Check console logs during test runs to identify hidden state updates causing warnings.

- Use `screen.debug()` or the error output from `getBy*` queries to resolve selector ambiguity.

### Blockers Found

None.

---

## WU-05: WebUI Test Coverage Analysis

**Completed**: 2026-01-12 16:50  
**Duration**: 0.5 hours  
**Status**: ✅ Complete

### What Went Well

- Coverage report generated successfully: 71.97% overall (4 files at 90%+)
- Identified exactly which components need test expansion
- Discovered missing dependency and root cause

### Challenges & Solutions

- **Issue**: `@vitest/coverage-v8` reported as missing when running `npm run test -- --coverage`
  - **Root Cause**: Dependency WAS in `package.json` (line 31) but `node_modules/` was incomplete locally (cache issue from previous setup)
  - **Solution**: Ran `npm install @vitest/coverage-v8` which synced all deps. Revealed the dependency was already declared but never installed.
  - **Prevention**: Add explicit `npm ci` before coverage runs to ensure clean installs

- **Issue**: CI workflow doesn't run coverage reports
  - **Root Cause**: Coverage was **intentionally disabled** in CI due to rate limits (seen in earlier learnings docs). `.github/workflows/lint-and-test.yml` runs `npm test -- --run` but not `npm run test:coverage`
  - **Resolution**: Coverage runs locally but not enforced in CI to avoid rate limiting issues

### Key Insights

- **Dependency Declaration vs Installation**: A package in `package.json` doesn't guarantee it's installed. Cache issues, partial installs, or skipped steps can leave dependencies missing.
- **CI Must Match Local Requirements**: If developers are expected to run coverage (80% threshold per AGENTS.md), CI should enforce it too
- **devDependencies aren't automatically used**: Just listing coverage tool doesn't mean the workflow runs it

### Architecture Decisions

- `@vitest/coverage-v8` correctly placed in `devDependencies` (v4.0.17)
- Script `test:coverage` exists in package.json but CI ignores it
- All required test tools are declared; only execution is missing from CI

### Tips for Similar Work

- Always run `npm ci` (clean install) before running optional features like coverage
- If a tool is required (80% threshold), add it to CI/CD pipeline explicitly
- Check `package.json` scripts vs actual CI workflow commands - they often diverge
- Document coverage requirements in CI config, not just in AGENTS.md

### Blockers Found

- **Codecov Rate Limiting**: Codecov upload was disabled in CI (commit e89a0d2) due to rate limit issues
  - **Status**: Coverage still runs locally with 80% threshold enforcement
  - **Why Disabled**: `codecov/codecov-action@v3` upload was consuming rate limits
  - **Current Solution**: No codecov uploads in workflow; coverage reports only run locally
  - **When to Re-enable**: If coverage monitoring service changes or rate limits are resolved
  - **Evidence**: Commit message: "This avoids codecov rate limit issues entirely while still enforcing 80% coverage locally via coverage report command"

---

## WU-06: App.test.tsx - Functional Tests for Connection States & Error Handling

**Completed**: 2026-01-12 17:10  
**Duration**: 1 hour  
**Status**: ✅ Complete (partial - 46% coverage, need 80%)

### What Went Well

- Added 14 new functional tests covering connection states, error handling, mode switching
- Tests now catch the WebSocket error scenario from issue #17
- Improved App.tsx coverage from 33% → 46%
- Overall WebUI coverage improved from 71.97% → 77.07%
- All 22 tests pass, no flaky tests
- Mock verification pattern established

### Challenges & Solutions

- **Issue**: Old branding tests failed because mock wasn't set up before they ran
  - **Root Cause**: Mock `mockReturnValue()` called inside describe block, but tests rendered component before mock was ready
  - **Solution**: Set global mock **outside** describe block, before any tests run
  - **Lesson**: Mock setup timing matters - must happen before first render

- **Issue**: How do you know if a mock isn't actually mocking?
  - **Solution**: Watch for `TypeError: Cannot destructure property 'X' of undefined` - this proves mock setup failed
  - **Verification**: Use `expect(vi.isMockFunction(fn)).toBe(true)` to verify mock is active
  - **Lesson**: Real code errors prove the mock didn't intercept the call

### Key Insights

- **Mock Setup Timing**: Global mocks must be defined outside describe blocks (before imports)
- **Component-Level Mocks**: Set defaults in beforeEach or at module level
- **Error Detection**: "Cannot read property" or "Cannot destructure" errors mean mock failed
- **Test Order Matters**: Test that verifies mock is working should run first (sanity check)
- **Mock Verification Pattern**: Check vi.isMockFunction() at test start, verify .toHaveBeenCalled() within tests

### Architecture Decisions

- Mocks set globally before any tests (affects all tests in file)
- Mock returns realistic object shape matching actual useWebSocket hook
- Functional tests separate from branding/styling tests (two describe blocks)
- beforeEach hook resets mocks for state isolation

### Tips for Similar Work

- Always set global mocks **before** describe blocks start
- Test your test: verify vi.isMockFunction(fn) === true
- Look for "Cannot read/destructure" errors as sign mock failed
- Use .toHaveBeenCalled() to verify mock was actually invoked
- If mock fails silently, check:
  1. Mock defined before imports
  2. Mock called with correct return shape
  3. No race conditions in async tests
- Set up mocks in this order:
  1. vi.mock() - mock module at import time
  2. const mock = require(); import - get reference
  3. mock.mockReturnValue() - set return value
  4. render() - component now uses mock

### Blockers Found

- **Partial Coverage**: App.tsx still at 46% (need 80%)
  - Lines 67-79, 267-270 need additional tests for results display and file upload
  - Estimated 6-8 more tests needed
  - Dependent on other components being fully mocked (JobList, ResultsPanel)


