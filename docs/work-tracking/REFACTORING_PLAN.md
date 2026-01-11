# Post-Migration Refactoring & Code Quality Plan

**Status**: In Progress
**Priority**: Before adding new features
**Goal**: Improve test coverage, code quality, maintainability

---

## Phase 1: Fix Failing Tests (0-1 hour)

**Status**: ✅ COMPLETE

**Current**: 311 passing, 0 failing

**Fixed Tests** (Gemini Integration):
- ✅ test_gemini_cli_tools_list_returns_all_plugins
- ✅ test_gemini_cli_tools_have_required_metadata  
- ✅ test_gemini_cli_tools_have_input_output_types
- ✅ test_gemini_cli_full_workflow_sequence

**Issue Fixed**: Tests were expecting old MCPTool format (id, title, inputs, outputs), but tools/list returns new MCP format (name, description, inputSchema). Updated all assertions to match new format.

**Work Done**:
- [x] Update test assertions to match new tools/list response format
- [x] Verify all 311 tests pass

---

## Phase 2: Type Safety & Imports (2-3 hours)

**Current Issues**:
- Missing type stubs for pydantic, fastapi, numpy, PIL, httpx, pytesseract
- websocket_manager has untyped functions
- Plugin implementations lack type hints

### WU-02a: Add Type Stub Packages (0.5 hours)
- [ ] Add missing type stub packages to `requirements-lint.txt`
- [ ] Test mypy with new stubs

### WU-02b: Type Hints for websocket_manager (1 hour)
- [ ] Add type hints to all functions in websocket_manager.py
- [ ] Run mypy to validate

### WU-02c: Type Hints for Plugin Base Classes (1 hour)
- [ ] Add comprehensive type hints to plugin interfaces
- [ ] Document type annotation patterns for future plugins

### WU-02d: Final Type Check (0.5 hours)
- [ ] Run `mypy server/app/ --no-site-packages` - target 100%
- [ ] Fix any remaining type errors

---

## Phase 3: Test Coverage Analysis (4-5 hours)

**Current Backend (server/)**: 65.40% (311 passing tests)
**Current Frontend (web-ui/)**: Not measured yet

**Priority Areas** (coverage gaps by module):
1. websocket_manager.py: 31.43% (48.57% gap) - CRITICAL
2. tasks.py: 42.27% (37.73% gap) - HIGH
3. api.py: 47.22% (32.78% gap) - HIGH
4. main.py: 49.47% (30.53% gap) - HIGH
5. auth.py: 52.50% (27.50% gap) - MEDIUM
6. plugin_loader.py: 57.48% (22.52% gap) - MEDIUM

### WU-03a: WebSocket & Streaming Tests (1.5 hours)
- [ ] Add tests for WebSocket connect/disconnect scenarios
- [ ] Test stream message handling and edge cases
- [ ] Target: websocket_manager.py → 80%+

### WU-03b: Task Processor Tests (1 hour)
- [ ] Add tests for task lifecycle (creation, processing, completion)
- [ ] Test error handling in task execution
- [ ] Target: tasks.py → 80%+

### WU-03c: API Endpoint Tests (1 hour)
- [ ] Add tests for API endpoints (job retrieval, status checks, errors)
- [ ] Test parameter validation and error responses
- [ ] Target: api.py → 80%+

### WU-03d: Frontend (web-ui) Coverage Setup (0.5 hours)
- [ ] Install @vitest/coverage-v8 in web-ui/
- [ ] Update vitest.config.ts with coverage threshold
- [ ] Run `npm run test:coverage` 
- [ ] Identify files <80% coverage
- [ ] Document current coverage baseline
- **Note**: Currently no coverage provider installed, needs setup

### WU-03e: Final Backend Coverage Check (1 hour)
- [ ] Run full coverage suite: `pytest --cov=app --cov-report=term-missing`
- [ ] Fix remaining gaps
- [ ] Ensure all modules ≥80%

---

## Phase 4: Code Organization & Clarity (3 hours)

**Current Strengths**:
- ✅ Clear separation of concerns (models, adapters, handlers, routes)
- ✅ Good docstrings on major functions
- ✅ Consistent naming conventions

### WU-04a: MCP Module Reorganization (1 hour)
- [ ] Consolidate related MCP code (mcp_*, mcp_handlers, mcp_routes, mcp_adapter)
- [ ] Create `server/app/mcp/` subdirectory structure
- [ ] Move files: protocol.py, handlers.py, routes.py, adapter.py
- [ ] Update imports across codebase

### WU-04b: Plugin System Documentation (0.5 hours)
- [ ] Document plugin interface (base class contract)
- [ ] Create plugin development checklist
- [ ] Document plugin registry pattern usage

### WU-04c: WebSocket & Streaming Docs (0.5 hours)
- [ ] Document WebSocket message types and flow
- [ ] Clarify stream format for real-time analysis
- [ ] Add streaming protocol helpers/examples

### WU-04d: Authentication & Authorization Review (1 hour)
- [ ] Review auth.py for consistency
- [ ] Document API key validation flow
- [ ] Clarify validation separation (auth.py vs routes)

---

## Phase 5: Documentation Improvements (1 hour)

**Current**: Good README, ARCHITECTURE.md exists

### WU-05a: Core Documentation Updates (1 hour)
- [ ] Update ARCHITECTURE.md with post-migration structure
- [ ] Add API endpoint documentation (auto-generated from FastAPI)
- [ ] Document MCP protocol implementation
- [ ] Create TESTING.md (how to run tests, coverage targets)
- [ ] Update PLUGIN_DEVELOPMENT.md with type hints and examples

---

## Phase 6: Performance & Observability (1.5 hours)

### WU-06a: Logging & Performance Review (1.5 hours)
- [ ] Review logging (is everything necessary logged?)
- [ ] Check for n+1 queries or inefficient loops
- [ ] Verify caching is effective (manifest caching)
- [ ] Add performance metrics to slow operations
- [ ] Document structured logging patterns

---

## Coverage Philosophy

**Important**: Coverage % is a guideline, not a quality metric. We aim for **meaningful** coverage:
- ✅ **Good coverage**: Tests validate logic, error handling, edge cases
- ❌ **Artificial coverage**: Tests created only to hit % targets with no real assertions

**Our 80% target** means:
- Mission-critical paths (MCP, WebSocket, task processing) require tests
- Error scenarios must be tested (auth failures, malformed requests, etc.)
- Edge cases validated (empty inputs, large data, concurrent operations)
- NOT: Every single line covered just for metrics

We'll avoid inflating numbers with hollow tests. Phase 3 focuses on **valuable** coverage.

---

## Success Criteria

- ✅ All 311+ tests passing
- ✅ 100% mypy compliance (or documented exceptions)
- ✅ 80%+ code coverage (backend + frontend)
- ✅ No ruff violations
- ✅ Clear, documented code organization
- ✅ Updated architecture documentation

---

## Estimated Timeline

| Phase | Work Units | Hours | Status |
|-------|-----------|-------|--------|
| Phase 1: Fix Tests | - | 0.25 | ✅ DONE |
| Phase 2: Type Safety | WU-02a,b,c,d | 3 | TODO |
| Phase 3: Coverage | WU-03a,b,c,d,e | 5 | TODO |
| Phase 4: Organization | WU-04a,b,c,d | 3 | TODO |
| Phase 5: Documentation | WU-05a | 1 | TODO |
| Phase 6: Performance | WU-06a | 1.5 | TODO |
| **Total** | **14 units** | **13.75** | **IN PROGRESS** |

**Breakdown by Work Unit Duration**:
- Small units: 0.5 hours (WU-02a, 03d, 04b, 04c)
- Medium units: 1 hour (WU-02b, 02c, 03b, 03c, 05a, 06a)
- Large units: 1.5 hours (WU-03a)
- XL units: 1 hour (WU-02d, 03e, 04a)

---

## Priority Order

1. **Phase 1** (tests) - Unblock other phases
2. **Phase 2** (types) - Build confidence in codebase
3. **Phase 3** (coverage) - Identify gaps
4. **Phase 4** (org) - Improve maintainability
5. **Phase 5** (docs) - Share knowledge
6. **Phase 6** (perf) - Optimize before scaling
