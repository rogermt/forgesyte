# Server-WebUI Integration Fix Plan

**Issue**: Web UI receives 500 errors when fetching plugins list  
**Current Status**: WU-01 & WU-02 Complete. WU-03 (E2E Testing) Next.  
**Root Cause**: Server initialization bug (imported global variable not updating). Fixed in WU-02.

## Work Breakdown

### WU-01: Integration Test Foundation (Completed)
**Goal**: Create test infrastructure to detect server/WebUI mismatches locally
**Status**: ✅ Complete (2026-01-12)
**Outcome**: 
- Integration tests pass (18/18)
- Confirmed server response formats match WebUI client expectations

---

### WU-02: Diagnose and Fix 500 Error (Completed)
**Goal**: Identify the exact exception causing the 500 error and fix it.
**Status**: ✅ Complete (2026-01-12)
**Outcome**:
- **Root Cause Identified**: Python import behavior caused `task_processor` to remain `None` in `main.py` despite initialization.
- **Fix Applied**: Updated `main.py` to use local variable from `init_task_processor` return value.
- **Verified**: `curl /v1/plugins` returns 200 OK.

---

### WU-03: End-to-End Testing & Hardening (Next Up)
**Goal**: Verify real server + WebUI work together and prevent regression.

**Tasks**:
1. Create `e2e.test.sh` script:
   - Start server in background.
   - Wait for health check.
   - Run WebUI integration tests against REAL server (not mocks).

2. Run full test sequence:
   - Server tests: `pytest`
   - WebUI tests: `npm test`
   - E2E tests: `./e2e.test.sh`

**Acceptance**: E2E tests pass with real server.

**Commits**:
```bash
test: Add e2e test script and verify server-webui integration (WU-03)
```

---

### WU-04: Update CI and Documentation (Completed)
**Goal**: Ensure CI catches integration issues early.
**Status**: ✅ Complete (2026-01-12)
**Outcome**: CI now includes WebUI and E2E jobs.

---

## Phase 2: WebUI Test Stability (Completed)

### WU-05: Fix Hook Testing Infrastructure (Completed)
**Goal**: Resolve 17 failures in `useWebSocket.test.ts`.
**Status**: ✅ Complete (2026-01-12)
**Outcome**: All hook tests passing after improving WebSocket mock and timer handling.

---

### WU-06: Resolve DOM Selection and Ambiguity (Completed)
**Goal**: Fix query errors and styling assertions.
**Status**: ✅ Complete (2026-01-12)
**Outcome**: Switched to `getByRole` and `data-testid` for reliable DOM targeting.

---

### WU-07: Fix Act Warnings and Lifecycle Cleanup (Completed)
**Goal**: Eliminate all "not wrapped in act(...)" warnings.
**Status**: ✅ Complete (2026-01-12)
**Outcome**: Corrected async `act` usage across all test files.

---

### WU-08: Final Verification & CI Hardening (Completed)
**Goal**: Final local and CI pass.
**Status**: ✅ Complete (2026-01-12)
**Outcome**: 100% test pass rate achieved locally and verified via E2E script.

