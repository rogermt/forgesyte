# Server-WebUI Integration Fix Plan

**Issue**: Web UI receives 500 errors after Python refactoring  
**Root Cause**: API response format mismatch between refactored server and Web UI client  
**Effort**: 3-4 work units, ~4-5 hours

## Work Breakdown

### WU-01: Integration Test Foundation (1.5 hours)
**Goal**: Create test infrastructure to detect server/WebUI mismatches locally

**Tasks**:
1. Create `web-ui/src/integration/server-api.integration.test.ts`
   - Mock server responses based on actual refactored server
   - Test all 7 API endpoints: plugins, jobs (list/get/cancel), analyze, health
   - Use real client (no mocking client)

2. Capture actual server responses:
   - Start server locally
   - Make real calls
   - Document response format for each endpoint

3. Update WebUI client if response format differs:
   - Check wrapper presence (`{data}` vs bare object)
   - Verify field names match (job_id vs id)
   - Handle optional fields

**Acceptance**: Integration tests run, document current vs expected responses

**Commits**: 
```bash
feat: Create server-api integration test suite (WU-01)
```

---

### WU-02: Fix API Response Formats (2 hours)
**Goal**: Ensure server responses match WebUI client expectations

**Tasks**:
1. For each endpoint in `server/app/api.py`:
   - Check actual response format
   - Compare to `web-ui/src/api/client.ts` expectations
   - Update server or client to match

2. Key endpoints to verify:
   - `GET /v1/plugins` → `{ plugins: [...] }`
   - `GET /v1/jobs` → `{ jobs: [...] }`
   - `GET /v1/jobs/:id` → `{ job: {...} }` OR bare object
   - `POST /v1/analyze` → `{ job_id, status }`
   - `DELETE /v1/jobs/:id` → `{ status, job_id }`
   - `GET /v1/health` → `{ status, plugins_loaded, version }`

3. Run integration tests:
   - All 7 endpoints must return correct format
   - No 500 errors
   - Client can parse response correctly

**Acceptance**: Integration tests pass (all endpoints return expected format)

**Commits**:
```bash
fix: Ensure API responses match WebUI client expectations (WU-02)
```

---

### WU-03: End-to-End Testing (1.5 hours)
**Goal**: Verify real server + WebUI work together

**Tasks**:
1. Create `e2e.test.sh` script:
   - Start server in background
   - Start web-ui dev server
   - Run WebUI integration tests against real server
   - Verify no 500 errors

2. Run full test sequence:
   - Server tests: `cd server && pytest --cov=app --cov-fail-under=80`
   - WebUI tests: `cd web-ui && npm test`
   - E2E tests: `./e2e.test.sh`

3. Document results:
   - All tests pass
   - No integration issues

**Acceptance**: E2E tests pass with real server/WebUI

**Commits**:
```bash
test: Add e2e test script and verify server-webui integration (WU-03)
```

---

### WU-04: Update CI and Documentation (1 hour)
**Goal**: Ensure CI catches integration issues early

**Tasks**:
1. Update `.github/workflows/lint-and-test.yml`:
   - Add step to run `npm test` in web-ui
   - Add E2E test step (optional, may be slow)
   - Ensure both pass before merge

2. Update `AGENTS.md`:
   - Add "Run integration tests" to mandatory workflow
   - Include: `npm run test` in web-ui/
   - Before committing, verify both server and webui tests pass

3. Document:
   - Why integration testing is critical
   - How to run tests locally
   - What to do if one fails

**Acceptance**: CI updated, AGENTS.md updated, documentation clear

**Commits**:
```bash
ci: Add web-ui tests to workflow (WU-04)
docs: Update AGENTS.md with integration testing requirement (WU-04)
```

---

## Local Testing Command Sequence

**Before committing ANY changes:**

```bash
# Terminal 1: Server tests
cd /home/rogermt/forgesyte/server
uv sync
cd ..
uv run pre-commit run --all-files
cd server
PYTHONPATH=. uv run mypy app/ --no-site-packages
uv run pytest --cov=app --cov-fail-under=80 --cov-report=term-missing

# Terminal 2: WebUI tests
cd /home/rogermt/forgesyte/web-ui
npm install  # if needed
npm test

# Terminal 3: E2E (only after both pass)
# Start server
cd /home/rogermt/forgesyte/server
uv run uvicorn app.main:app --reload

# Terminal 4: Run e2e
cd /home/rogermt/forgesyte/web-ui
npm run test:e2e
```

## Success Metrics

✅ Server tests pass (80%+ coverage)  
✅ WebUI unit tests pass  
✅ Integration tests reveal no 500 errors  
✅ E2E tests pass with real server  
✅ CI enforces all tests before merge  
✅ AGENTS.md enforces integration testing before commits  

## Commit Strategy

**Branch**: Create `fix/server-webui-integration`

```bash
# WU-01: Integration test foundation
git add web-ui/src/integration/
git commit -m "feat: Create server-api integration test suite (WU-01)"
git push origin fix/server-webui-integration

# WU-02: Fix response formats
git add server/app/
git commit -m "fix: Ensure API responses match WebUI client expectations (WU-02)"
git push origin fix/server-webui-integration

# WU-03: E2E testing
git add e2e.test.sh
git commit -m "test: Add e2e test script and verify server-webui integration (WU-03)"
git push origin fix/server-webui-integration

# WU-04: CI and docs
git add .github/workflows/ AGENTS.md
git commit -m "ci/docs: Add web-ui tests to CI workflow and update AGENTS.md (WU-04)"
git push origin fix/server-webui-integration

# Final merge
git checkout main
git pull origin main
git merge fix/server-webui-integration
git push origin main
```

## Risk Mitigation

- **Small commits**: Each WU is independently reviewable
- **Tests first**: Integration tests reveal issues before fixes
- **Rollback easy**: If issues found, revert single commits
- **CI gate**: Enforces all tests pass before merge

## Dependencies

- None (can work independently)
- No blockers identified

## Next Steps

1. Review this plan
2. Approve or request changes
3. Start WU-01 when ready
4. Run FULL test sequence (server + webui) before each commit
