# Issue: Server-WebUI Integration - 500 Response Bug

**Status**: Open  
**Severity**: Critical  
**Impact**: Web UI cannot communicate with refactored server  

## Problem

After Python refactoring (refactor/python-standards merge), web UI receives 500 responses when calling server endpoints. This indicates:

1. **API response format mismatch** - WebUI expects one format, server returns another
2. **Missing integration tests** - No tests verify server/webui compatibility
3. **Response wrapper inconsistencies** - Some endpoints use `{wrapper: data}`, others don't

## Root Cause Analysis

The refactored server (WU-03 onwards) changed API endpoint implementations and response formats:

### WebUI Client Expectations
- `getPlugins()` - expects `{ plugins: [] }`
- `listJobs()` - expects `{ jobs: [] }`
- `getJob(id)` - expects `{ job: {} }` OR bare object
- `analyzeImage()` - expects `{ job_id: string, status: string }`
- `health()` - expects `{ status, plugins_loaded, version }`

### Refactored Server Responses
Need to verify actual response format from:
- `server/app/api.py` - REST endpoints
- `server/app/services/` - Service layer responses

## Evidence

**Pre-refactoring**: Web UI worked (endpoints unchanged)  
**Post-refactoring**: Web UI gets 500 errors (endpoints refactored with new response logic)

## Solution Plan

### Phase 1: Integration Testing (WU-1)
- Create `web-ui/src/integration/server-api.integration.test.ts`
- Mock actual server responses
- Test each API endpoint against refactored server

### Phase 2: Fix Response Formats (WU-2)
- Identify response format mismatches
- Update server endpoints if needed
- Verify tests pass

### Phase 3: E2E Testing (WU-3)
- Start actual server + web UI
- Run real integration tests
- Verify 200 responses for all endpoints

## Current Test Coverage

**Web UI Unit Tests**: ✅ Present
- `client.test.ts` - API client (mocked)
- `App.integration.test.tsx` - React (mocked WebSocket)
- `useWebSocket.test.ts` - WebSocket hook

**Missing**: Real server integration
- No test actually calls running server
- All mocks prevent discovering response format issues
- CI doesn't test server + web UI together

## Acceptance Criteria

- [ ] Server API responses match WebUI client expectations
- [ ] Integration tests pass (mocked server responses)
- [ ] E2E tests pass (real server + web UI)
- [ ] No 500 errors when WebUI calls server
- [ ] AGENTS.md updated with "run full integration test suite" requirement
- [ ] CI workflow includes both server and web-ui tests
