# Issue #22: Review and Standardize Mock Data - Work Unit Plan

## Overview
Break down GitHub Issue #22 into small, atomic work units (1-2 hours each) to systematically fix mock data across the codebase to match actual API contracts.

## Work Units

### WU-1: Create Golden Fixtures Infrastructure
**Duration**: 1 hour  
**Goal**: Establish golden fixtures directory and capture real API responses

**Acceptance Criteria**:
- [ ] Create `fixtures/` directory at project root
- [ ] Create `fixtures/api-responses.json` with real server API responses
- [ ] Document fixture schema in `fixtures/README.md`
- [ ] Add entry to `.gitignore` if needed
- [ ] Capture actual responses for:
  - `/v1/jobs` (list jobs)
  - `/v1/jobs/{id}` (single job)
  - WebSocket frame results

**Deliverables**:
- Fixture files with documented schema
- README explaining fixture usage
- No code changes yet

---

### WU-2: Create Mock Factory for Web UI (TypeScript)
**Duration**: 1.5 hours  
**Goal**: Build factory functions that generate mocks from actual API schema

**Acceptance Criteria**:
- [ ] Create `web-ui/src/test-utils/factories.ts`
- [ ] Implement `createMockJob()` factory (from JobResponse schema)
- [ ] Implement `createMockPlugin()` factory (from Plugin schema)
- [ ] Implement `createMockFrameResult()` factory
- [ ] All factories accept `overrides` for test-specific customization
- [ ] Factories use exact field names from server models
- [ ] Type-safe: factories are typed with actual interfaces
- [ ] Add JSDoc with usage examples

**Deliverables**:
- `factories.ts` with 3+ mock factories
- Tests for factories themselves

---

### WU-3: Update Web UI Tests - JobList Component
**Duration**: 1.5 hours  
**Goal**: Migrate JobList tests from hand-written mocks to factories

**Acceptance Criteria**:
- [ ] Update all mocks in `JobList.test.tsx` to use `createMockJob()`
- [ ] Verify test data matches server API format:
  - `job_id` (not `id`)
  - `status: "queued" | "running" | "done" | "error" | "not_found"`
  - `completed_at` (not `updated_at`)
  - `progress` field included
- [ ] All 21 JobList tests pass
- [ ] No hand-written mock objects remain
- [ ] Comment linking test to API endpoint (`/v1/jobs`)

**Deliverables**:
- Updated `JobList.test.tsx`
- Tests passing with 100% coverage maintained

---

### WU-4: Update Web UI Tests - Other Components
**Duration**: 1.5 hours  
**Goal**: Fix remaining Web UI tests (App, ResultsPanel, useWebSocket)

**Acceptance Criteria**:
- [ ] Update `App.test.tsx` to use mock factories
- [ ] Update `ResultsPanel.test.tsx` to use mock factories
- [ ] Update `useWebSocket.test.ts` to use frame result factory
- [ ] All tests pass
- [ ] Each test has comment linking to API endpoint
- [ ] Coverage maintained at 80%+

**Deliverables**:
- Updated test files
- All tests passing

---

### WU-5: Add Integration Test - API Contract Verification
**Duration**: 2 hours  
**Goal**: Create server-side integration test that verifies API responses match documented schema

**Acceptance Criteria**:
- [ ] Create `server/tests/integration/test_api_contracts.py`
- [ ] Test `/v1/jobs` endpoint response shape
- [ ] Test `/v1/jobs/{id}` endpoint response shape
- [ ] Test `/v1/plugins` endpoint response shape
- [ ] Verify all field names match JobResponse/PluginMetadata models
- [ ] Verify enum values match defined JobStatus/PluginStatus
- [ ] Verify required vs optional fields
- [ ] Test passes when running against real server
- [ ] Run as part of CI pipeline

**Deliverables**:
- Integration test file with 3+ contract tests
- All tests passing

---

### WU-6: Create Fixture Synchronization Script
**Duration**: 1 hour  
**Goal**: Automated script to update fixtures when API changes

**Acceptance Criteria**:
- [ ] Create `scripts/sync-fixtures.sh`
- [ ] Script starts test server
- [ ] Script calls real API endpoints
- [ ] Script captures responses to `fixtures/api-responses.json`
- [ ] Script validates responses match schema
- [ ] Can be run manually: `./scripts/sync-fixtures.sh`
- [ ] Documented in `README.md` and `CONTRIBUTING.md`

**Deliverables**:
- Sync script
- Documentation

---

### WU-7: Update Server Tests - conftest.py Mocks
**Duration**: 1.5 hours  
**Goal**: Review and fix server-side mock fixtures

**Acceptance Criteria**:
- [ ] Review `MockPluginRegistry` - verify matches Protocol
- [ ] Review `MockJobStore` - verify matches actual JobStore behavior
- [ ] Review `MockTaskProcessor` - verify matches actual behavior
- [ ] Add comments documenting what each mock verifies
- [ ] All server tests still pass
- [ ] Mark which server tests have API contract guarantees

**Deliverables**:
- Updated conftest.py with documented mocks
- Tests passing

---

### WU-8: Documentation - Update CONTRIBUTING.md
**Duration**: 1 hour  
**Goal**: Document mock best practices for contributors

**Acceptance Criteria**:
- [ ] Add "Testing Strategy" section to CONTRIBUTING.md
- [ ] Include link to mock factories location
- [ ] Include fixture synchronization instructions
- [ ] Add checklist: "When adding tests, use factories not hand-written mocks"
- [ ] Document how to run integration tests
- [ ] Link to AGENTS.md mock section

**Deliverables**:
- Updated CONTRIBUTING.md
- Clear contributor guidelines

---

### WU-9: Documentation - Create Test Guide (new file)
**Duration**: 1.5 hours  
**Goal**: Comprehensive guide for testing with proper mocks

**Acceptance Criteria**:
- [ ] Create `docs/TESTING.md`
- [ ] Section: "Mock Data Best Practices"
- [ ] Section: "API Contract Testing"
- [ ] Section: "Golden Fixtures"
- [ ] Examples: Using factories
- [ ] Examples: Integration tests
- [ ] Troubleshooting: "Tests pass but code fails"

**Deliverables**:
- `docs/TESTING.md` with comprehensive examples

---

### WU-10: Audit & Verification
**Duration**: 1 hour  
**Goal**: Final audit that all mocks match API contracts

**Acceptance Criteria**:
- [ ] Run all tests: `npm test` and `pytest`
- [ ] All 100+ tests pass
- [ ] Coverage maintained at 80%+
- [ ] Integration tests verify API contracts
- [ ] No hand-written mocks found (grep for anti-patterns)
- [ ] All fixtures up-to-date with current API
- [ ] Documentation complete and linked

**Deliverables**:
- Test results showing 100% pass
- Audit checklist completed

---

## Recommended Execution Order

```
WU-1: Golden Fixtures Infrastructure (1 hour)
  ↓
WU-2: Mock Factory (1.5 hours)
  ↓
WU-3: JobList Tests (1.5 hours)
  ↓
WU-4: Other Web UI Tests (1.5 hours)
  ↓
WU-5: Integration Tests (2 hours)
  ↓
WU-6: Fixture Sync Script (1 hour)
  ↓
WU-7: Server Test Mocks (1.5 hours)
  ↓
WU-8: CONTRIBUTING.md (1 hour)
  ↓
WU-9: Testing Guide (1.5 hours)
  ↓
WU-10: Audit & Verification (1 hour)

Total: ~13.5 hours (about 7 small threads at 2 hours each)
```

## Success Metrics

- ✅ All tests pass
- ✅ 100% mock data matches server API schema
- ✅ Zero hand-written mocks remain
- ✅ Integration tests verify contracts
- ✅ Documentation updated (AGENTS.md, CONTRIBUTING.md, TESTING.md)
- ✅ Contributors can't add mismatched mocks (blocked by factories requirement)

## Notes

- Each WU is designed as a commit
- Earlier WUs unblock later ones
- Can run parallel: WU-3 and WU-4 can run in parallel after WU-2
- Testing gates each step (must verify tests pass before moving forward)
- Documentation updates in WU-8/9 won't affect code functionality

## Blockers & Dependencies

- **WU-1 blocks**: WU-2, WU-3, WU-4, WU-6 (need fixtures first)
- **WU-2 blocks**: WU-3, WU-4 (need factories)
- **WU-5 blocks**: WU-10 (integration test verification)
- **No blockers for**: WU-7, WU-8, WU-9 (can work in parallel with code changes)
